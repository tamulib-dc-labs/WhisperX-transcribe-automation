import smbclient
import os
import pandas as pd
import argparse
import re
import sys
import yaml
from smbprotocol.exceptions import SMBResponseException

# --- SMB Helper Functions ---

def download_file_smb(remote_path, local_path):
    """
    Download a single file from Network Share using smbclient
    """
    try:
        # Create local directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Open remote file (read binary) and local file (write binary)
        with smbclient.open_file(remote_path, mode='rb') as remote_f:
            with open(local_path, 'wb') as local_f:
                local_f.write(remote_f.read())
        
        print(f"Downloaded: {local_path}")
        return True
    except Exception as e:
        print(f"Failed to download {remote_path}: {e}")
        return False

def download_folder_smb(remote_folder, local_folder):
    """
    Download all files from a Network Share folder recursively
    """
    try:
        # Ensure local folder exists
        os.makedirs(local_folder, exist_ok=True)

        # List all entries in the remote folder
        for entry in smbclient.scandir(remote_folder):
            remote_entry_path = os.path.join(remote_folder, entry.name)
            local_entry_path = os.path.join(local_folder, entry.name)

            if entry.is_file():
                download_file_smb(remote_entry_path, local_entry_path)
            
            elif entry.is_dir():
                download_folder_smb(remote_entry_path, local_entry_path)
        
        return True

    except SMBResponseException as e:
        print(f"Folder not found on Network: {remote_folder}")
        return False
    except Exception as e:
        print(f"Error processing folder {remote_folder}: {e}")
        return False

# --- Original Logic (Preserved) ---

def extract_folder_name(sheet_folder_name):
    match = re.match(r'(\d+)_(\d+)(?:-[a-zA-Z0-9]+)?', sheet_folder_name)
    
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    print(f"Warning: Could not parse folder name '{sheet_folder_name}', using as-is")
    return sheet_folder_name

def get_incomplete_folders_from_sheet(sheet_url, max_folders=None):
    try:
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
        
        df = pd.read_csv(csv_url)
        
        target_folders = [] 
        seen_folders = set() 
        
        for index, row in df.iterrows():
            if pd.isna(row.get('Done')) or str(row.get('Done', '')).strip() == '':
                if pd.notna(row.get('as')) and str(row.get('as', '')).strip():
                    sheet_folder = str(row['as']).strip()
                    clean_folder_name = extract_folder_name(sheet_folder)
                    
                    if clean_folder_name not in seen_folders:
                        target_folders.append(clean_folder_name)
                        seen_folders.add(clean_folder_name)
                        
                        print(f"Found folder to download: {clean_folder_name} (from sheet: {sheet_folder})")
                        
                        if max_folders and len(target_folders) >= max_folders:
                            print(f"Reached maximum of {max_folders} folders, stopping sheet processing")
                            break
        
        return target_folders
        
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return []

# --- Main Execution ---

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # Load config file
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    config = load_config(config_path)

    # Get all settings from config
    sheet_url = config["google_sheets"]["url"]
    local_path = os.path.abspath(config["paths"]["oral_input"])
    max_folders = config["google_sheets"].get("max_folders", None)

    smb_server = config["smb"]["server"]
    smb_share = config["smb"]["share"]
    smb_base_path = config["smb"].get("base_path", "")
    smb_username = config["smb"]["username"]
    smb_password = config["smb"]["password"]

    try:
        # 1. Authenticate with SMB Server using config
        print(f"Connecting to {smb_server}...")
        smbclient.register_session(smb_server, username=smb_username, password=smb_password)
        print("Successfully connected to Network Share")

        # 2. Get list from Google Sheet
        incomplete_folders = get_incomplete_folders_from_sheet(sheet_url, max_folders)

        if not incomplete_folders:
            print("No incomplete folders found.")
            return

        print(f"Found {len(incomplete_folders)} unique incomplete folders to download")

        # 3. Process Downloads
        successful_downloads = 0
        failed_downloads = 0
        skipped_folders = []

        for idx, folder_name in enumerate(incomplete_folders, 1):
            # Construct the full UNC path
            network_root = fr"\\{smb_server}\{smb_share}"

            if smb_base_path:
                full_remote_path = os.path.join(network_root, smb_base_path, folder_name)
            else:
                full_remote_path = os.path.join(network_root, folder_name)

            local_destination = os.path.join(local_path, folder_name)

            print(f"\n[{idx}/{len(incomplete_folders)}] Downloading: {full_remote_path}")

            success = download_folder_smb(full_remote_path, local_destination)

            if success:
                print(f"Completed: {folder_name}")
                successful_downloads += 1
            else:
                print(f"Skipped (not found): {folder_name}")
                failed_downloads += 1
                skipped_folders.append(folder_name)

        # 4. Summary
        print("\n" + "="*50)
        print("Download Summary:")
        print(f"Total processed: {len(incomplete_folders)}")
        print(f"Success: {successful_downloads}")
        print(f"Failed/Not Found: {failed_downloads}")

        if skipped_folders:
            print("\nFolders not found on Network:")
            for f in skipped_folders:
                print(f"  - {f}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()