# Legacy Scripts (Deprecated)

⚠️ **DEPRECATED**: These scripts are from version 1.0 and are kept for backward compatibility only.

## Migration Notice

**Please use the new modular structure instead:**

```bash
# OLD (deprecated)
python legacy/pipeline_2.py

# NEW (recommended)
python scripts/run_pipeline.py
```

## What's in This Folder

These are the original v1.0 scripts before the refactoring:

- `pipeline_2.py` - Old pipeline orchestrator → Use `scripts/run_pipeline.py`
- `git_upload.py` - Old git upload script → Now `src/git/uploader.py`
- `d_whisperx.py` - Old model downloader → Now `src/transcription/model_downloader.py`
- `download_automation_3.py` - Old download script → Integrated into `src/pipeline.py`
- `transcribe.py` - Old transcription script → Moved to `scripts/transcribe.py`
- `run_1.slurm` - Old SLURM template → Moved to `config/run.slurm`

## Why Keep Legacy Scripts?

These scripts are kept to:
1. **Maintain backward compatibility** for users still on v1.0
2. **Provide reference** during migration
3. **Enable gradual migration** without breaking existing workflows

## Migration Guide

See the main repository's `MIGRATION.md` for detailed migration instructions.

### Quick Migration Steps

1. **Update your workflow** to use the new entry point:
   ```bash
   python scripts/run_pipeline.py
   ```

2. **Update configuration** in `src/config.py` instead of editing `legacy/pipeline_2.py`

3. **Use new modular classes** for custom integrations:
   ```python
   from src.pipeline import TranscriptionPipeline
   from src.config import get_config
   
   pipeline = TranscriptionPipeline()
   pipeline.run()
   ```

## Deprecation Timeline

- **v2.0** (Current): Legacy scripts work, marked deprecated
- **v2.1** (Planned): Add runtime deprecation warnings
- **v3.0** (Future): Remove legacy scripts entirely

## Still Need Help?

- See `../MIGRATION.md` for detailed migration guide
- See `../QUICKSTART.md` for new setup instructions
- See `../README.md` for complete documentation

---

**Last Updated**: December 2024  
**Status**: ⚠️ Deprecated - Use new structure in `src/`, `scripts/`, and `config/`
