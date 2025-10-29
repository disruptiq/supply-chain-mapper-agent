import os
import re
import toml

class PythonParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        basename = os.path.basename(manifest_path)
        if basename == "requirements.txt":
            dependencies.extend(self._parse_requirements_txt(manifest_path))
        elif basename == "pyproject.toml":
            dependencies.extend(self._parse_pyproject_toml(manifest_path))
        elif basename == "setup.py":
            dependencies.extend(self._parse_setup_py(manifest_path))
        return dependencies

    def _parse_requirements_txt(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-r") or line.startswith("-f"):
                        continue

                    # Regex to capture package name and version. Handles ==, >=, <=, >, <, ~=
                    match = re.match(r"^([a-zA-Z0-9_.-]+)(?:([<>=~]+)([0-9a-zA-Z_.-]+))?", line)
                    if match:
                        name = match.group(1)
                        operator = match.group(2) if match.group(2) else "=="
                        version = match.group(3) if match.group(3) else "*"

                        # Reconstruct version string for consistency
                        version_string = f"{operator}{version}" if version != "*" else version

                        dep_record = {
                            "ecosystem": "python",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": name,
                                "version": version_string,
                                "source": "pypi",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": False, # requirements.txt doesn't distinguish dev deps easily
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps
        except FileNotFoundError:
            print(f"Error: requirements.txt not found at {manifest_path}")
        return deps

    def _parse_pyproject_toml(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
        except UnicodeDecodeError:
            print(f"Warning: {manifest_path} contains invalid UTF-8 characters, skipping")
            return deps

        # Handle dependencies from [project] section (PEP 621)
            project_section = data.get("project", {})
            dependencies_list = project_section.get("dependencies", [])
            optional_dependencies = project_section.get("optional-dependencies", {})
            
            # Parse main dependencies
            line_num = 1  # Note: TOML files don't have exact line numbers for dependencies, using 1 as placeholder
            for dep in dependencies_list:
                parsed_dep = self._parse_single_dependency(dep)
                if parsed_dep:
                    dep_record = {
                        "ecosystem": "python",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": parsed_dep["name"],
                            "version": parsed_dep["version"],
                            "source": "pypi",
                            "resolved": None
                        },
                        "metadata": {
                            "dev_dependency": False,
                            "line_number": line_num,
                            "script_section": False
                        }
                    }
                    deps.append(dep_record)
            
            # Parse optional dependencies (dev dependencies, etc.)
            for group_name, group_deps in optional_dependencies.items():
                is_dev = group_name.lower() in ["dev", "test", "testing", "dev-dependencies"]
                for dep in group_deps:
                    parsed_dep = self._parse_single_dependency(dep)
                    if parsed_dep:
                        dep_record = {
                            "ecosystem": "python",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": parsed_dep["name"],
                                "version": parsed_dep["version"],
                                "source": "pypi",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": is_dev,
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)
                        
            # Handle legacy setup.py style dependencies in [tool.poetry.dependencies] 
            poetry_section = data.get("tool", {}).get("poetry", {})
            if "dependencies" in poetry_section:
                poetry_deps = poetry_section["dependencies"]
                for name, version_info in poetry_deps.items():
                    # Check if this is a dev dependency (poetry has optional dependencies)
                    is_dev = name in poetry_section.get("group", {}).get("dev", {}).get("dependencies", {})
                    
                    # Handle version as string or dict
                    if isinstance(version_info, dict):
                        version = version_info.get("version", "*")
                        if version == "*":
                            # Check if there's a git source or other version info
                            if "git" in version_info:
                                source = f"git+{version_info['git']}"
                                version = version_info.get("rev", version_info.get("tag", version_info.get("branch", "*")))
                            elif "path" in version_info:
                                source = f"file://{version_info['path']}"
                                version = "*"
                            else:
                                version = str(version_info)
                        else:
                            source = "pypi"
                    else:
                        version = str(version_info)
                        source = "pypi"
                    
                    dep_record = {
                        "ecosystem": "python",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": name,
                            "version": version,
                            "source": source,
                            "resolved": None
                        },
                        "metadata": {
                            "dev_dependency": is_dev,
                            "line_number": line_num,
                            "script_section": False
                        }
                    }
                    deps.append(dep_record)
                    
        except (FileNotFoundError, toml.TOMLDecodeError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        return deps

    def _parse_single_dependency(self, dep_string):
        """Parse a single dependency string that may include version specifiers."""
        # Remove extra markers like ;python_version<"3.8"
        dep_without_marker = dep_string.split(";")[0].strip()
        
        # Parse package name and version - handles formats like: package, package>=1.0, package~=1.4.2
        match = re.match(r"^([a-zA-Z0-9_.-]+)(.*)", dep_without_marker)
        if match:
            name = match.group(1)
            version_part = match.group(2).strip()
            
            # If no version specified, use '*'
            if not version_part:
                version_part = "*"
                
            return {"name": name, "version": version_part}
        return None

    def _parse_setup_py(self, manifest_path):
        """Parse setup.py for dependencies"""
        deps = []
        try:
            with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find setup() call and extract dependency arguments
            setup_match = re.search(r'setup\s*\(', content, re.DOTALL)
            if not setup_match:
                return deps

            # Extract the setup call content
            setup_start = setup_match.start()
            paren_count = 0
            end_pos = setup_start

            for i, char in enumerate(content[setup_start:], setup_start):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        end_pos = i + 1
                        break

            setup_content = content[setup_start:end_pos]

            # Extract dependency lists
            dependency_fields = ['install_requires', 'setup_requires', 'tests_require', 'extras_require']

            for field in dependency_fields:
                # Find the field assignment
                field_pattern = rf'{field}\s*=\s*(\[.*?\]|\(.*?\)|[\'\"](.*?)[\'\"])'
                matches = re.findall(field_pattern, setup_content, re.DOTALL)

                for match in matches:
                    dep_list_str = match[0] if isinstance(match, tuple) else match
                    if dep_list_str.startswith('[') or dep_list_str.startswith('('):
                        # It's a list or tuple
                        dep_strings = self._extract_list_items(dep_list_str)
                    else:
                        # It's a single string
                        dep_strings = [dep_list_str]

                    is_dev = field in ['tests_require', 'extras_require']

                    for dep_str in dep_strings:
                        dep_str = dep_str.strip().strip('\'"')
                        if dep_str and not dep_str.startswith('#'):
                            parsed_dep = self._parse_single_dependency(dep_str)
                            if parsed_dep:
                                dep_record = {
                                    "ecosystem": "python",
                                    "manifest_path": os.path.relpath(manifest_path),
                                    "dependency": {
                                        "name": parsed_dep["name"],
                                        "version": parsed_dep["version"],
                                        "source": "pypi",
                                        "resolved": None
                                    },
                                    "metadata": {
                                        "dev_dependency": is_dev,
                                        "line_number": self._find_line_number(content, dep_str),
                                        "script_section": False
                                    }
                                }
                                deps.append(dep_record)

        except Exception as e:
            print(f"Error parsing setup.py {manifest_path}: {e}")

        return deps

    def _extract_list_items(self, list_str):
        """Extract items from a Python list/tuple string"""
        items = []
        current_item = ""
        in_string = False
        string_char = None
        brace_count = 0

        i = 0
        while i < len(list_str):
            char = list_str[i]

            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_item += char
                elif char in ['[', '(']:
                    brace_count += 1
                elif char in [']', ')']:
                    brace_count -= 1
                    if brace_count == 0:
                        break
                elif char == ',' and brace_count == 1:
                    if current_item.strip():
                        items.append(current_item.strip())
                    current_item = ""
                else:
                    current_item += char
            else:
                current_item += char
                if char == string_char and (i == 0 or list_str[i-1] != '\\'):
                    in_string = False

            i += 1

        if current_item.strip():
            items.append(current_item.strip())

        return items

    def _find_line_number(self, content, target):
        """Find approximate line number for a target string"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if target in line:
                return i
        return 0
