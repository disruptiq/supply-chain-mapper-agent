import os
import xml.etree.ElementTree as ET

class DotNetParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        filename = os.path.basename(manifest_path)
        if filename.endswith('.csproj'):
            dependencies.extend(self._parse_csproj(manifest_path))
        elif filename == 'packages.lock.json':
            dependencies.extend(self._parse_packages_lock_json(manifest_path))
        return dependencies

    def _parse_csproj(self, manifest_path):
        deps = []
        seen_deps = set()  # To avoid duplicates
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            # Find all PackageReference elements
            package_refs = root.findall(".//PackageReference")
            
            for ref in package_refs:
                # Get the Include attribute (package name) and Version attribute
                package_name = ref.get('Include')
                version = ref.get('Version')
                
                if package_name:
                    # Skip if we've already seen this dependency
                    dep_key = (package_name.lower(), version)
                    if dep_key in seen_deps:
                        continue
                    seen_deps.add(dep_key)
                    
                    # Determine if it's a development dependency
                    # In .NET, this might be indicated by PrivateAssets attribute
                    private_assets = ref.get('PrivateAssets', '').lower()
                    is_dev = 'all' in private_assets or 'test' in private_assets
                    
                    dep_record = {
                        "ecosystem": "dotnet",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": package_name,
                            "version": version if version else "*",
                            "source": ".net_nuget",
                            "resolved": None
                        },
                        "metadata": {
                            "dev_dependency": is_dev,
                            "line_number": None,  # XML parsing doesn't easily provide line numbers
                            "script_section": False
                        }
                    }
                    deps.append(dep_record)
                    
        except ET.ParseError as e:
            print(f"Error parsing XML in {manifest_path}: {e}")
        except Exception as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        
        return deps

    def _parse_packages_lock_json(self, manifest_path):
        # packages.lock.json provides locked versions but let's just return empty for now
        # The main .csproj file contains the important dependency information
        return []