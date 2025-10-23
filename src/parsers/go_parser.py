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
            with open(manifest_path, "r") as f:
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
                    if len(parts) >= 3:
                        module_name = parts[1]
                        version = parts[2]
                        # Check if it's a replaced dependency
                        replaced = " => " in line
                        
                        dep_record = {
                            "ecosystem": "go",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": module_name,
                                "version": version,
                                "source": "goproxy" if not replaced else "replaced",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": False,  # Go doesn't distinguish dev vs prod deps
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)
                    continue
                elif line.startswith("replace ") and not line.startswith("replace ("):
                    # Single line replace statement
                    parts = line.split()
                    if len(parts) >= 5:
                        original_module = parts[1]
                        new_module = parts[3]
                        new_version = parts[4]
                        
                        dep_record = {
                            "ecosystem": "go",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": original_module,
                                "version": new_version,
                                "source": "replaced",
                                "resolved": f"replaced with {new_module}@{new_version}"
                            },
                            "metadata": {
                                "dev_dependency": False,
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)
                    continue
                    
                elif in_require_section or in_replace_section:
                    # Multi-line require or replace statement
                    line = line.strip()
                    if line and not line.startswith("//"):  # Skip comments
                        parts = line.split()
                        if len(parts) >= 2:
                            if in_replace_section and " => " in line:
                                # Parse replace statement: module => replacement version
                                parts = line.split(" => ")
                                if len(parts) == 2:
                                    original_module = parts[0].strip()
                                    replacement_parts = parts[1].strip().split()
                                    if len(replacement_parts) >= 2:
                                        new_module = replacement_parts[0]
                                        new_version = replacement_parts[1]
                                        
                                        dep_record = {
                                            "ecosystem": "go",
                                            "manifest_path": os.path.relpath(manifest_path),
                                            "dependency": {
                                                "name": original_module,
                                                "version": new_version,
                                                "source": "replaced",
                                                "resolved": f"replaced with {new_module}@{new_version}"
                                            },
                                            "metadata": {
                                                "dev_dependency": False,
                                                "line_number": line_num,
                                                "script_section": False
                                            }
                                        }
                                        deps.append(dep_record)
                            else:
                                # Regular module requirement
                                module_name = parts[0]
                                version = parts[1]
                                
                                dep_record = {
                                    "ecosystem": "go",
                                    "manifest_path": os.path.relpath(manifest_path),
                                    "dependency": {
                                        "name": module_name,
                                        "version": version,
                                        "source": "goproxy",
                                        "resolved": None
                                    },
                                    "metadata": {
                                        "dev_dependency": False,
                                        "line_number": line_num,
                                        "script_section": False
                                    }
                                }
                                deps.append(dep_record)

        except FileNotFoundError:
            print(f"Error: go.mod not found at {manifest_path}")
        return deps