import json
import yaml
import os
import re
from typing import List, Dict, Any


class LockfileParser:
    def __init__(self):
        pass

    def parse(self, manifest_path: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(manifest_path)

        if filename == "package-lock.json":
            return self._parse_package_lock(manifest_path)
        elif filename == "yarn.lock":
            return self._parse_yarn_lock(manifest_path)
        elif filename == "pnpm-lock.yaml":
            return self._parse_pnpm_lock(manifest_path)
        else:
            return []

    def _parse_package_lock(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return dependencies
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return dependencies

        def extract_from_lockfile_deps(deps_dict):
            if not deps_dict:
                return
            for name, dep_info in deps_dict.items():
                if isinstance(dep_info, dict):
                    version = dep_info.get("version", "")
                    resolved = dep_info.get("resolved", "")
                    integrity = dep_info.get("integrity", "")

                    dep_record = {
                        "ecosystem": "npm",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": name,
                            "version": version,
                            "source": "npm_registry",
                            "resolved": resolved
                        },
                        "metadata": {
                            "dev_dependency": False,  # Lockfiles don't distinguish dev/prod
                            "line_number": None,
                            "script_section": False,
                            "integrity": integrity,
                            "lockfile": True
                        }
                    }
                    dependencies.append(dep_record)

                    # Recurse into nested dependencies
                    if "dependencies" in dep_info:
                        extract_from_lockfile_deps(dep_info["dependencies"])

        extract_from_lockfile_deps(content.get("dependencies", {}))
        return dependencies

    def _parse_yarn_lock(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return dependencies
        except FileNotFoundError as e:
            print(f"Error reading {manifest_path}: {e}")
            return dependencies

        # Yarn lock format: each entry starts with "package@version:"
        # Then indented lines with version, resolved, integrity
        entries = re.split(r'\n(?=\w)', content)

        for entry in entries:
            lines = entry.strip().split('\n')
            if not lines:
                continue

            # First line: package@range
            package_line = lines[0].strip()
            if not package_line or ':' not in package_line:
                continue

            package_name = package_line.split('@')[0] if '@' in package_line else package_line.split(':')[0]

            version = ""
            resolved = ""
            integrity = ""

            for line in lines[1:]:
                line = line.strip()
                if line.startswith('version '):
                    version = line.split(' ', 1)[1].strip('"')
                elif line.startswith('resolved '):
                    resolved = line.split(' ', 1)[1].strip('"')
                elif line.startswith('integrity '):
                    integrity = line.split(' ', 1)[1].strip()

            if version:
                dep_record = {
                    "ecosystem": "npm",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": package_name,
                        "version": version,
                        "source": "npm_registry",
                        "resolved": resolved
                    },
                    "metadata": {
                        "dev_dependency": False,
                        "line_number": None,
                        "script_section": False,
                        "integrity": integrity,
                        "lockfile": True
                    }
                }
                dependencies.append(dep_record)

        return dependencies

    def _parse_pnpm_lock(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return dependencies
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return dependencies

        if not content:
            return dependencies

        # pnpm-lock.yaml structure varies by version
        # Look for snapshots or packages sections
        packages = content.get("packages", {})
        snapshots = content.get("snapshots", {})

        all_packages = {**packages, **snapshots}

        for package_path, package_info in all_packages.items():
            if isinstance(package_info, dict):
                # Extract name and version from path like /name/version
                parts = package_path.strip('/').split('/')
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[-1]  # Last part is version
                    resolved = package_info.get("resolution", {}).get("tarball", "")
                    integrity = package_info.get("integrity", "")

                    dep_record = {
                        "ecosystem": "npm",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": name,
                            "version": version,
                            "source": "npm_registry",
                            "resolved": resolved
                        },
                        "metadata": {
                            "dev_dependency": False,
                            "line_number": None,
                            "script_section": False,
                            "integrity": integrity,
                            "lockfile": True
                        }
                    }
                    dependencies.append(dep_record)

        return dependencies
