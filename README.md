# WhisperX Transcribe Automation

## 1. Create Python Virtual Environment

Open a terminal in the project directory and run:

```powershell
python -m venv venv
```

Activate the virtual environment:
- On Windows:
  ```powershell
  .\venv\Scripts\activate
  ```
- On Linux/Mac:
  ```bash
  source venv/bin/activate
  ```

## 2. Install Dependencies

With the virtual environment activated, install required packages:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Directory Structure

You do **not** need to manually create any directories.

When you run the pipeline scripts, they will automatically create the following directories if they do not exist:
- `data/oral_input` (inside your project folder)
- `data/oral_output` (inside your project folder)
- `git_repo` (one level above your project folder)

## 4. Set Paths in Code

- The code is already set to use:
  - `data/oral_input` and `data/oral_output` for input/output data
  - `git_repo` outside the working directory for the Git repository
- No manual changes needed unless you want to customize paths.

## 5. Running the Pipeline

Run the main pipeline script:

```powershell
python pipeline_2.py
```

This script will:
- Prepare the environment
- Clear input/output folders
- Download data
- Run batch jobs
- Upload results to GitHub

## 6. Notes
- Make sure you have the required credentials (SMB password, GitHub token) ready when prompted.
- Review and update `config/config.yaml` if you need to change any configuration values.
- For any issues, check the log output in the terminal for troubleshooting.
