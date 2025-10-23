import os
import re

class DockerfileParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        filename = os.path.basename(manifest_path).lower()
        if filename == "dockerfile" or "dockerfile" in filename:
            dependencies.extend(self._parse_dockerfile(manifest_path))
        return dependencies

    def _parse_dockerfile(self, manifest_path):
        deps = []
        try:
            with open(manifest_path, "r") as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Parse FROM instruction for base image
                if line.upper().startswith("FROM "):
                    # Handle multi-stage builds: FROM <image> [AS <name>]
                    from_match = re.match(r"FROM\s+([^:]+)(?::([^#\s]+))?\s*(?:AS\s+\w+)?", line, re.IGNORECASE)
                    if from_match:
                        image_name = from_match.group(1).strip()
                        tag = from_match.group(2)
                        
                        # If no tag is specified, it defaults to 'latest' which is risky
                        version = tag if tag else "latest"
                        
                        dep_record = {
                            "ecosystem": "docker",
                            "manifest_path": os.path.relpath(manifest_path),
                            "dependency": {
                                "name": image_name,
                                "version": version,
                                "source": "docker_registry",
                                "resolved": None
                            },
                            "metadata": {
                                "dev_dependency": False,
                                "line_number": line_num,
                                "script_section": False
                            }
                        }
                        deps.append(dep_record)
                
                # Also look for potential risky operations in RUN commands
                elif line.upper().startswith("RUN "):
                    # Check for risky patterns in RUN commands
                    run_cmd = line[4:].strip()  # Remove "RUN " prefix
                    
                    # Look for commands that might download and execute scripts
                    if re.search(r'curl.*\|.*sh|wget.*\|.*sh|bash.*-c', run_cmd, re.IGNORECASE):
                        # This is a potential risk, but we'll add it as metadata to the Dockerfile
                        # rather than as a separate dependency
                        pass  # Risk will be handled by risk_heuristics.py
        
        except FileNotFoundError:
            print(f"Error: Dockerfile not found at {manifest_path}")
        return deps