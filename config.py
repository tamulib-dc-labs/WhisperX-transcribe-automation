"""
Configuration loader for WhisperX Automation Pipeline

This module provides a centralized configuration system that loads settings from:
1. config.yaml file (primary source)
2. Environment variables (overrides)
3. Default values (fallback)

Usage:
    from config import load_config
    
    config = load_config()
    hf_home = config['paths']['hf_home']
    github_token = config['credentials']['github_token']
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Singleton instance
_config_instance = None

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to config.yaml file. If None, searches current directory.
        
    Returns:
        Dictionary containing all configuration values
        
    Raises:
        FileNotFoundError: If config.yaml is not found
        yaml.YAMLError: If config.yaml is malformed
    """
    global _config_instance
    
    # Return cached instance if already loaded
    if _config_instance is not None:
        return _config_instance
    
    # Find config file
    if config_path is None:
        # Search in current directory and script directory
        search_paths = [
            Path.cwd() / "config.yaml",
            Path(__file__).parent / "config.yaml",
        ]
        
        config_path = None
        for path in search_paths:
            if path.exists():
                config_path = path
                break
        
        if config_path is None:
            raise FileNotFoundError(
                "config.yaml not found. Please create config.yaml from config.example.yaml"
            )
    else:
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    # Cache and return
    _config_instance = config
    return config


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Environment variables are checked in the format: SECTION_KEY
    For example: PATHS_HF_HOME, CREDENTIALS_GITHUB_TOKEN
    """
    # Paths overrides
    if 'paths' in config:
        config['paths']['hf_home'] = os.getenv('HF_HOME', config['paths'].get('hf_home'))
        config['paths']['nltk_data'] = os.getenv('NLTK_DATA', config['paths'].get('nltk_data'))
        config['paths']['torch_home'] = os.getenv('TORCH_HOME', config['paths'].get('torch_home'))
    
    # Credentials overrides (for security)
    if 'credentials' in config:
        config['credentials']['github_token'] = os.getenv('GITHUB_TOKEN', config['credentials'].get('github_token'))
        config['credentials']['smb_password'] = os.getenv('SMB_PASSWORD', config['credentials'].get('smb_password'))
    
    return config


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get a specific configuration value using dot notation.
    
    Args:
        key_path: Dot-separated path to config value (e.g., 'paths.hf_home')
        default: Default value if key not found
        
    Returns:
        Configuration value or default
        
    Example:
        hf_home = get_config_value('paths.hf_home')
        batch_size = get_config_value('whisperx.batch_size', 16)
    """
    config = load_config()
    
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def reload_config():
    """Force reload of configuration (clears cache)"""
    global _config_instance
    _config_instance = None
    return load_config()
