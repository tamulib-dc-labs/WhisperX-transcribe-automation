def git_standard_pipeline(
    source_data_folder,   # Where your files are NOW
    git_repo_folder,      # Where we will download the repo to
    target_owner,
    repo_name,
    auth_username,
    token,
    branch_prefix="upload"
):
    # Construct URL with Token
    # This puts the token directly into the URL for authentication
    remote_url = f"https://{auth_username}:{token}@github.com/{target_owner}/{repo_name}.git"
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    new_branch = f"{branch_prefix}-{timestamp}"

    print(f"Starting Standard Pipeline")
    print(f"Source Data: {source_data_folder}")
    print(f"Git Repo Dir: {git_repo_folder}")

    def run(args, cwd):
        subprocess.run(args, cwd=cwd, check=True, text=True)

    try:
        # --- STEP 1: Setup the Git Repository ---
        if not os.path.exists(git_repo_folder):
            print("Cloning repository (First time setup)...")
            # We clone directly into the target folder
            subprocess.run(["git", "clone", remote_url, git_repo_folder], check=True)
            
            # Disable credential helper for this repo so it MUST use the token in the URL
            run(["git", "config", "--local", "--unset", "credential.helper"], cwd=git_repo_folder)
        
        else:
            print("Updating existing repository...")
            
            # Force Git to update the remote 'origin' URL to use the NEW token.
            # This fixes the "Authentication failed" error if the previous token expired.
            print("Refreshing remote credentials...")
            run(["git", "remote", "set-url", "origin", remote_url], cwd=git_repo_folder)

            run(["git", "checkout", "main"], cwd=git_repo_folder)
            run(["git", "pull", "origin", "main"], cwd=git_repo_folder)

        # --- STEP 2: Create New Branch ---
        print(f"Creating branch: {new_branch}")
        run(["git", "checkout", "-b", new_branch], cwd=git_repo_folder)

        # --- STEP 3: Copy Files ---
        print("SYNCING FILES...")
        print("Copying from Source -> Git Repo...")
        
        # We use 'rsync' because it's built into Linux clusters and handles 
        # merging folders safely without deleting existing files in the destination.
        # -a: Archive mode (keeps permissions/dates)
        # -v: Verbose
        # --exclude '.git': Critical to not corrupt the git folder
        cmd_rsync = [
            "rsync", "-av", 
            "--exclude", ".git",
            f"{source_data_folder}/",  # Trailing slash ensures contents are copied
            f"{git_repo_folder}/"
        ]
        subprocess.run(cmd_rsync, check=True)

        # --- STEP 4: Git Add, Commit, Push ---
        print("Staging changes...")
        run(["git", "add", "."], cwd=git_repo_folder)
        
        # Check if there are actually changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"], 
            cwd=git_repo_folder, capture_output=True, text=True
        ).stdout.strip()

        if not status:
            print("No new changes found after copying. Nothing to push.")
            return

        print("Committing...")
        run(["git", "commit", "-m", f"Upload via standard pipeline {timestamp}"], cwd=git_repo_folder)

        print(f"Pushing to {new_branch}...")
        # Since we updated the remote URL in Step 1, this push will use the correct token
        run(["git", "push", "-u", "origin", new_branch], cwd=git_repo_folder)

        print(f"SUCCESS! Pull Request URL: https://github.com/{target_owner}/{repo_name}/pull/new/{new_branch}")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")

# ==========================================
# CONFIGURATION
# ==========================================
import subprocess
import os
import datetime
import sys
import yaml

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    # Load config file
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    config = load_config(config_path)

    # 1. WHERE YOUR DATA IS (The Source)
    SOURCE_PATH = os.path.abspath(config["paths"]["oral_output"])

    # 2. WHERE THE GIT REPO SHOULD BE (The Destination)
    REPO_PATH = os.path.abspath(config["paths"]["git_repo"])

    # 3. GITHUB DETAILS
    TOKEN = config["git"]["token"]
    USER = config["git"]["username"]
    OWNER = config["git"]["owner"]
    REPO = config["git"]["repo"]

    git_standard_pipeline(
        source_data_folder=SOURCE_PATH,
        git_repo_folder=REPO_PATH,
        target_owner=OWNER,
        repo_name=REPO,
        auth_username=USER,
        token=TOKEN
    )