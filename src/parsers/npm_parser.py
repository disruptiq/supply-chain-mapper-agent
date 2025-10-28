import json
import os

class NpmParser:
    def __init__(self):
        pass

    def parse(self, manifest_path):
        dependencies = []
        try:
            with open(manifest_path, "r") as f:
                content = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading or parsing {manifest_path}: {e}")
            return dependencies

        # Helper to extract and normalize dependencies
        def extract_deps(deps_dict, dev_dependency=False):
            if not deps_dict:
                return
            for name, version in deps_dict.items():
                # Basic normalization for now, can be expanded
                dep_record = {
                    "ecosystem": "npm",
                    "manifest_path": os.path.relpath(manifest_path),
                    "dependency": {
                        "name": name,
                        "version": version,
                        "source": "registry", # Default to registry, can be refined later
                        "resolved": None # Will be filled by lockfile parsing later
                    },
                    "metadata": {
                        "dev_dependency": dev_dependency,
                        "line_number": None, # Difficult to get accurately from JSON load
                        "script_section": False,
                        "license": content.get("license")
                    }
                }
                dependencies.append(dep_record)

        extract_deps(content.get("dependencies"), dev_dependency=False)
        extract_deps(content.get("devDependencies"), dev_dependency=True)
        extract_deps(content.get("peerDependencies"), dev_dependency=False)
        extract_deps(content.get("optionalDependencies"), dev_dependency=False)

        # Check for script sections (e.g., postinstall)
        scripts = content.get("scripts", {})
        for script_name, script_command in scripts.items():
            if "install" in script_name or "post" in script_name or "pre" in script_name:
                # This is a simplistic check. More sophisticated analysis will be in risk_heuristics.py
                # For now, just flag that a script section exists
                for dep_record in dependencies:
                    # This associates script_section with all dependencies, which is not ideal
                    # A better approach would be to associate it with the manifest itself or specific scripts
                    # For now, we'll just set it to True if any script is found
                    dep_record["metadata"]["script_section"] = True
                break

        return dependencies
