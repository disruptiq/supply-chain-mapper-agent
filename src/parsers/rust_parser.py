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
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps

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

        # Handle dev-dependencies
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

        return deps

    def _extract_version(self, version_info):
        """Extract version string from various TOML formats"""
        if isinstance(version_info, str):
            return version_info
        elif isinstance(version_info, dict):
            # Handle version with features or other metadata
            return version_info.get("version", "*")
        else:
            return str(version_info)
