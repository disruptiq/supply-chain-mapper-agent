import os
import toml

class RustParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        if os.path.basename(manifest_path) == "Cargo.toml":
            dependencies.extend(self._parse_cargo_toml(manifest_path))
        return dependencies

    def _parse_cargo_toml(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r") as f:
                data = toml.load(f)
            
            # Extract dependencies from [dependencies] section
            dependencies = data.get("dependencies", {})
            dev_dependencies = data.get("dev-dependencies", {})
            
            for name, version_info in dependencies.items():
                version = self._extract_version(version_info)
                dep_record = {
                    "ecosystem": "rust",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "crates.io",
                        "resolved": None
                    },
                    "metadata": {
                        "dev_dependency": False,
                        "line_number": None,  # TOML doesn't provide line numbers easily
                        "script_section": False
                    }
                }
                deps.append(dep_record)
            
            # Process dev dependencies
            for name, version_info in dev_dependencies.items():
                version = self._extract_version(version_info)
                dep_record = {
                    "ecosystem": "rust",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "crates.io",
                        "resolved": None
                    },
                    "metadata": {
                        "dev_dependency": True,
                        "line_number": None,
                        "script_section": False
                    }
                }
                deps.append(dep_record)
                
        except Exception as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        
        return deps

    def _extract_version(self, version_info):
        """Extract version from various formats in Cargo.toml"""
        if isinstance(version_info, str):
            return version_info
        elif isinstance(version_info, dict):
            # Handle complex dependency specifications
            if "version" in version_info:
                return version_info["version"]
            elif "git" in version_info:
                # Git dependencies
                git_url = version_info["git"]
                if "rev" in version_info:
                    return f"git+{git_url}@{version_info['rev']}"
                elif "tag" in version_info:
                    return f"git+{git_url}@{version_info['tag']}"
                elif "branch" in version_info:
                    return f"git+{git_url}#{version_info['branch']}"
                else:
                    return f"git+{git_url}"
            elif "path" in version_info:
                # Local dependencies
                return f"local:{version_info['path']}"
            else:
                # Fallback to string representation
                return str(version_info)
        else:
            return str(version_info)