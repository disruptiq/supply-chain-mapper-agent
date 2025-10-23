import yaml
import os

class ConfigManager:
    def __init__(self, config_path=None):
        self.config = self._load_default_config()
        if config_path and os.path.exists(config_path):
            self.config = self._merge_configs(self.config, self._load_yaml_config(config_path))
        
    def _load_default_config(self):
        """Load default configuration"""
        return {
            "paths_to_ignore": [
                "node_modules/",
                "vendor/",
                ".git/",
                "__pycache__/",
                "*.log",
                "dist/",
                "build/",
                ".venv/",
                "venv/"
            ],
            "file_types": {
                "include": [],
                "exclude": [
                    "*.tmp",
                    "*.bak",
                    ".DS_Store"
                ]
            },
            "severity_thresholds": {
                "low": True,
                "medium": True,
                "high": True,
                "critical": True
            },
            "offline_mode": False,
            "include_binaries": False,
            "risk_heuristics": {
                "install_scripts": True,
                "obfuscated_code": True,
                "git_dependencies": True,
                "unpinned_versions": True,
                "binary_modules": True,
                "container_risks": True,
                "third_party_ci_actions": True
            }
        }
    
    def _load_yaml_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                return yaml_config or {}
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
            return {}
    
    def _merge_configs(self, default_config, yaml_config):
        """Merge default config with YAML config"""
        # Deep merge the configurations
        merged = default_config.copy()
        
        for key, value in yaml_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Recursively merge nested dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_config(self):
        """Get the current configuration"""
        return self.config
    
    def should_ignore_path(self, path):
        """Check if a path should be ignored based on configuration"""
        import fnmatch
        
        for pattern in self.config['paths_to_ignore']:
            if fnmatch.fnmatch(path, pattern) or pattern in path:
                return True
        return False