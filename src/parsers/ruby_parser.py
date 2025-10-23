import os
import re

class RubyParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        filename = os.path.basename(manifest_path)
        if filename == "Gemfile" or filename == "Gemfile.lock":
            if filename == "Gemfile":
                dependencies.extend(self._parse_gemfile(manifest_path))
            elif filename == "Gemfile.lock":
                dependencies.extend(self._parse_gemfile_lock(manifest_path))
        return dependencies

    def _parse_gemfile(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r") as f:
                lines = f.readlines()
            
            in_group = False
            group_type = "default"  # Default dependency
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Handle group blocks (e.g., group :development, :test do)
                if line.startswith("group"):
                    in_group = True
                    if "development" in line or "test" in line:
                        group_type = "development"
                    else:
                        group_type = "default"
                    continue
                
                # End of group block
                if line == "end" and in_group:
                    in_group = False
                    group_type = "default"
                    continue
                
                # Parse gem declarations: gem 'name', 'version' or gem 'name', '~> 1.0'
                gem_match = re.match(r'^gem\s+[\'\"]([^\'\"]+)[\'\"](?:\s*,\s*[\'\"]([^\'\"]+)[\'\"])?', line)
                if gem_match:
                    name = gem_match.group(1)
                    version = gem_match.group(2) if gem_match.group(2) else "*"
                    
                    dep_record = {
                        "ecosystem": "ruby",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": name,
                            "version": version,
                            "source": "rubygems.org",
                            "resolved": None
                        },
                        "metadata": {
                            "dev_dependency": group_type == "development",
                            "line_number": line_num,
                            "script_section": False
                        }
                    }
                    deps.append(dep_record)
                    
        except Exception as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        
        return deps

    def _parse_gemfile_lock(self, manifest_path):
        # Gemfile.lock parsing is more complex and usually contains resolved versions
        # For now, we'll return empty as the Gemfile is the primary manifest
        return []