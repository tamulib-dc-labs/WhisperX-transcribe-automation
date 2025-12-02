import subprocess
import os
import datetime
import sys
import argparse

def git_standard_pipeline(
    source_data_folder,   # Where your files are NOW
    git_repo_folder,      # Where we will download the repo to (OUTSIDE working directory)
    target_owner,
    repo_name,
    auth_username,
    token,
    branch_prefix="upload"
):
    """
    Standard Git pipeline for uploading files to GitHub
    
    Args:
        source_data_folder: Path to the folder containing files to upload
        git_repo_folder: Path where git repo will be cloned/maintained (should be OUTSIDE working directory)
        target_owner: GitHub repository owner
        repo_name: GitHub repository name
        auth_username: GitHub username for authentication
        token: GitHub personal access token
        branch_prefix: Prefix for the branch name (default: "upload")
    """
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
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(git_repo_folder), exist_ok=True)
            # We clone directly into the target folder
            subprocess.run(["git", "clone", remote_url, git_repo_folder], check=True)
            
            # Disable credential helper for this repo so it MUST use the token in the URL
            # Use check=False to ignore error if credential.helper is not set
            subprocess.run(["git", "config", "--local", "--unset", "credential.helper"], 
                         cwd=git_repo_folder, check=False)
        
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
        print("Copying from Source -> Git Repo (additions/updates only)...")
        
        # We use 'rsync' because it's built into Linux clusters and handles 
        # merging folders safely without deleting existing files in the destination.
        # -a: Archive mode (keeps permissions/dates)
        # -v: Verbose
        # --ignore-existing: Skip files that already exist in destination
        # --exclude '.git': Critical to not corrupt the git folder
        # NOTE: This will only ADD new files and UPDATE changed files, never DELETE
        cmd_rsync = [
            "rsync", "-av", 
            "--exclude", ".git",
            f"{source_data_folder}/",  # Trailing slash ensures contents are copied
            f"{git_repo_folder}/"
        ]
        subprocess.run(cmd_rsync, check=True)

        # --- STEP 4: Git Add, Commit, Push ---
        print("Staging changes (new and modified files only)...")
        # Only add new and modified files, don't stage deletions
        run(["git", "add", "--all", "--ignore-removal"], cwd=git_repo_folder)
        
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
# MAIN - Parse command line arguments
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload files to GitHub repository via standard Git pipeline"
    )
    
    # Required arguments
    parser.add_argument("--source-path", required=True, 
                       help="Path to the folder containing files to upload")
    parser.add_argument("--repo-path", required=True,
                       help="Path where git repo will be cloned/maintained (should be OUTSIDE working directory)")
    parser.add_argument("--owner", required=True,
                       help="GitHub repository owner")
    parser.add_argument("--repo-name", required=True,
                       help="GitHub repository name")
    parser.add_argument("--username", required=True,
                       help="GitHub username for authentication")
    parser.add_argument("--token", required=True,
                       help="GitHub personal access token")
    
    # Optional arguments
    parser.add_argument("--branch-prefix", default="upload",
                       help="Prefix for the branch name (default: upload)")
    
    args = parser.parse_args()

    git_standard_pipeline(
        source_data_folder=args.source_path,
        git_repo_folder=args.repo_path,
        target_owner=args.owner,
        repo_name=args.repo_name,
        auth_username=args.username,
        token=args.token,
        branch_prefix=args.branch_prefix
    )