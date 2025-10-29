import os
import re

class GoParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        if os.path.basename(manifest_path) == "go.mod":
            dependencies.extend(self._parse_go_mod(manifest_path))
        elif os.path.basename(manifest_path) == "go.sum":
            # go.sum is used for checksums but doesn't contain dependency definitions in the same way
            # We'll focus on go.mod for dependency information
            pass
        return dependencies

    def _parse_go_mod(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            in_require_section = False
            in_replace_section = False
            line_num = 0

            for i, line in enumerate(lines, 1):
                line_num = i
                line = line.strip()

                if line.startswith("require ("):
                    in_require_section = True
                    continue
                elif line == "require (":
                    in_require_section = True
                    continue
                elif line == ")":
                    in_require_section = False
                    in_replace_section = False
                    continue
                elif line.startswith("replace ("):
                    in_replace_section = True
                    continue
                elif line.startswith("require ") and not line.startswith("require ("):
                    # Single line require statement
                    parts = line.split()
                    if len(parts) >= 2:
                        module_path = parts[1]
                        version = parts[2] if len(parts) > 2 else "latest"

                        dep_record = {
                            "ecosystem": "go",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": module_path,
                                "version": version,
                                "source": "go",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": False,
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)

                elif in_require_section and not in_replace_section:
                    # Inside require block, parse module lines
                    if line and not line.startswith("#") and not line.startswith("//"):
                        parts = line.split()
                        if len(parts) >= 1:
                            module_path = parts[0]
                            version = parts[1] if len(parts) > 1 else "latest"

                            dep_record = {
                                "ecosystem": "go",
                                "manifest_path": os.path.relpath(manifest_path),
                                "dependency": {
                                    "name": module_path,
                                    "version": version,
                                    "source": "go",
                                    "resolved": None
                                },
                                "metadata": {
                                    "dev_dependency": False,
                                    "line_number": line_num,
                                    "script_section": False
                                }
                            }
                            deps.append(dep_record)

        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
        except FileNotFoundError:
            print(f"Error: go.mod not found at {manifest_path}")
        return deps
