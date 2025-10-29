import os
import json

class PhpParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        if os.path.basename(manifest_path) == "composer.json":
            dependencies.extend(self._parse_composer_json(manifest_path))
        elif os.path.basename(manifest_path) == "composer.lock":
            # For now, just parse the main composer.json file
            pass
        return dependencies

    def _parse_composer_json(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
            
            # Parse regular dependencies
            require_deps = data.get("require", {})
            for name, version in require_deps.items():
                dep_record = {
                    "ecosystem": "php",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "packagist.org",
                        "resolved": None
                    },
                    "metadata": {
                        "dev_dependency": False,
                        "line_number": None,  # JSON doesn't provide line numbers easily
                        "script_section": False
                    }
                }
                deps.append(dep_record)
            
            # Parse dev dependencies
            require_dev_deps = data.get("require-dev", {})
            for name, version in require_dev_deps.items():
                dep_record = {
                    "ecosystem": "php",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "packagist.org",
                        "resolved": None
                    },
                    "metadata": {
                        "dev_dependency": True,
                        "line_number": None,
                        "script_section": False
                    }
                }
                deps.append(dep_record)
            
            # Check for post-install scripts that might be risky
            scripts = data.get("scripts", {})
            post_install_scripts = []
            for script_name, script_content in scripts.items():
                if "post" in script_name.lower() or "install" in script_name.lower():
                    if isinstance(script_content, list):
                        post_install_scripts.extend(script_content)
                    else:
                        post_install_scripts.append(script_content)
                        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        
        return deps