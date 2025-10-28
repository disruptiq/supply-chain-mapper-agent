import os
from typing import List, Dict, Any


class RParser:
    def __init__(self):
        pass

    def parse(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        filename = os.path.basename(manifest_path)

        if filename == "DESCRIPTION":
            dependencies.extend(self._parse_description(manifest_path))

        return dependencies

    def _parse_description(self, manifest_path: str) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(manifest_path, "r") as f:
                content = f.read()
        except FileNotFoundError as e:
            print(f"Error reading {manifest_path}: {e}")
            return deps

        # DESCRIPTION file is in DCF (Debian Control File) format
        # Parse key-value pairs
        fields = {}
        current_key = None
        current_value = []

        for line in content.split('\n'):
            line = line.rstrip()
            if line.startswith(' ') or line.startswith('\t'):
                # Continuation line
                if current_value:
                    current_value[-1] += ' ' + line.strip()
            else:
                # New field
                if current_key:
                    fields[current_key] = '\n'.join(current_value)
                if ':' in line:
                    current_key, value = line.split(':', 1)
                    current_key = current_key.strip()
                    current_value = [value.strip()]
                else:
                    current_key = None

        if current_key:
            fields[current_key] = '\n'.join(current_value)

        # Extract dependencies from Depends, Imports, Suggests, etc.
        dep_fields = ['Depends', 'Imports', 'Suggests', 'Enhances', 'LinkingTo']

        for field in dep_fields:
            if field in fields:
                deps_list = fields[field].split(',')
                for dep in deps_list:
                    dep = dep.strip()
                    if dep and dep != 'R':
                        # Parse package name and version
                        # Format: package (>= version) or just package
                        if '(' in dep:
                            name = dep.split('(')[0].strip()
                            version_spec = dep.split('(')[1].split(')')[0].strip()
                        else:
                            name = dep
                            version_spec = ""

                        dep_record = {
                            "ecosystem": "r",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": name,
                                "version": version_spec if version_spec else "latest",
                                "source": "cran",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": field in ['Suggests', 'Enhances'],
                                "line_number": None,
                                "script_section": False,
                                "field": field
                            }
                        }
                        deps.append(dep_record)

        return deps
