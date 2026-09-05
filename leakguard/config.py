"""Configuration file support for LeakGuard.

Supports pyproject.toml and .leakguard.toml configuration files.
"""

import tomllib
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from .confidence import Confidence


@dataclass
class LeakGuardConfig:
    """LeakGuard configuration."""
    
    fail_on: Confidence = Confidence.LIKELY
    ignore_patterns: List[str] = None
    safe_transfer_functions: List[str] = None
    
    def __post_init__(self):
        if self.ignore_patterns is None:
            self.ignore_patterns = []
        if self.safe_transfer_functions is None:
            self.safe_transfer_functions = []


def load_config(start_path: Path = None) -> LeakGuardConfig:
    """
    Load configuration from pyproject.toml or .leakguard.toml.
    
    Searches upward from start_path (or cwd) for config files.
    """
    if start_path is None:
        start_path = Path.cwd()
    
    # Try to find config file
    config_file = find_config_file(start_path)
    
    if config_file is None:
        # Return defaults
        return LeakGuardConfig()
    
    # Parse config file
    try:
        with open(config_file, 'rb') as f:
            data = tomllib.load(f)
        
        # Extract LeakGuard config
        if config_file.name == 'pyproject.toml':
            config_data = data.get('tool', {}).get('leakguard', {})
        else:
            config_data = data
        
        # Parse configuration
        fail_on_str = config_data.get('fail-on', 'likely')
        fail_on = Confidence.from_string(fail_on_str)
        
        ignore_patterns = config_data.get('ignore-patterns', [])
        safe_transfer_functions = config_data.get('safe-transfer-functions', [])
        
        return LeakGuardConfig(
            fail_on=fail_on,
            ignore_patterns=ignore_patterns,
            safe_transfer_functions=safe_transfer_functions
        )
    
    except Exception as e:
        # If config parsing fails, warn and return defaults
        print(f"Warning: Failed to parse config file {config_file}: {e}")
        return LeakGuardConfig()


def find_config_file(start_path: Path) -> Optional[Path]:
    """
    Search upward for pyproject.toml or .leakguard.toml.
    
    Returns the first config file found, or None.
    """
    current = start_path.resolve()
    
    while True:
        # Check for .leakguard.toml first (higher priority)
        leakguard_toml = current / '.leakguard.toml'
        if leakguard_toml.exists():
            return leakguard_toml
        
        # Check for pyproject.toml
        pyproject_toml = current / 'pyproject.toml'
        if pyproject_toml.exists():
            # Check if it contains [tool.leakguard] section
            try:
                with open(pyproject_toml, 'rb') as f:
                    data = tomllib.load(f)
                    if 'tool' in data and 'leakguard' in data['tool']:
                        return pyproject_toml
            except Exception:
                pass
        
        # Move up one directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent
