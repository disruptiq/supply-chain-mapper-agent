import os
import xml.etree.ElementTree as ET

class JavaParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        if os.path.basename(manifest_path) == "pom.xml":
            dependencies.extend(self._parse_pom_xml(manifest_path))
        return dependencies

    def _parse_pom_xml(self, manifest_path):
        deps = []
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            # Handle namespaces - Maven POMs use namespaces
            namespace = {'m': 'http://maven.apache.org/POM/4.0.0'}
            
            # Find all dependency elements
            dependencies_list = root.findall(".//m:dependency", namespace)
            
            for dep in dependencies_list:
                # Get the group ID, artifact ID, and version
                group_id_elem = dep.find("m:groupId", namespace)
                artifact_id_elem = dep.find("m:artifactId", namespace)
                version_elem = dep.find("m:version", namespace)
                scope_elem = dep.find("m:scope", namespace)
                
                if group_id_elem is not None and artifact_id_elem is not None:
                    group_id = group_id_elem.text
                    artifact_id = artifact_id_elem.text
                    version = version_elem.text if version_elem is not None else "*"
                    scope = scope_elem.text if scope_elem is not None else "compile"
                    
                    # Maven coordinates: groupId:artifactId:version
                    dep_name = f"{group_id}:{artifact_id}"
                    
                    dep_record = {
                        "ecosystem": "java",
                        "manifest_path": os.path.relpath(manifest_path),
                        "dependency": {
                            "name": dep_name,
                            "version": version,
                            "source": "maven_central",  # or jcenter, or other repository
                            "resolved": None
                        },
                        "metadata": {
                            "dev_dependency": scope in ["test", "provided", "runtime"],
                            "line_number": None,  # XML parsing doesn't provide line numbers easily
                            "script_section": False
                        }
                    }
                    deps.append(dep_record)
                    
        except ET.ParseError as e:
            print(f"Error parsing XML in {manifest_path}: {e}")
        except Exception as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
        
        return deps