import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any


class SBOMGenerator:
    def __init__(self):
        pass

    def generate_cyclonedx(self, dependencies: List[Dict[str, Any]], repo_path: str, commit_hash: str) -> Dict[str, Any]:
        """Generate CycloneDX SBOM"""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{str(uuid.uuid4())}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tools": [{
                    "vendor": "DisruptiQ",
                    "name": "Supply Chain Risk Mapper",
                    "version": "1.0.0"
                }],
                "component": {
                    "type": "application",
                    "name": os.path.basename(repo_path),
                    "version": commit_hash[:8] if commit_hash != "unknown" else "latest"
                }
            },
            "components": []
        }

        seen = set()
        for dep in dependencies:
            name = dep["dependency"]["name"]
            version = dep["dependency"]["version"]
            key = (name, version)

            if key in seen:
                continue
            seen.add(key)

            component = {
                "type": "library",
                "name": name,
                "version": version,
                "purl": self._generate_purl(dep)
            }

            # Add license if available
            if "license" in dep.get("metadata", {}):
                component["licenses"] = [{
                    "license": {
                        "id": dep["metadata"]["license"]
                    }
                }]

            # Add hashes if integrity is available
            if "integrity" in dep.get("metadata", {}):
                integrity = dep["metadata"]["integrity"]
                if integrity.startswith("sha256-"):
                    component["hashes"] = [{
                        "alg": "SHA-256",
                        "content": integrity[7:]  # Remove sha256- prefix
                    }]
                elif integrity.startswith("sha512-"):
                    component["hashes"] = [{
                        "alg": "SHA-512",
                        "content": integrity[7:]
                    }]

            # Add properties
            component["properties"] = [
                {
                    "name": "ecosystem",
                    "value": dep["ecosystem"]
                },
                {
                    "name": "dev_dependency",
                    "value": str(dep.get("metadata", {}).get("dev_dependency", False))
                }
            ]

            sbom["components"].append(component)

        return sbom

    def _generate_purl(self, dep: Dict[str, Any]) -> str:
        """Generate Package URL"""
        ecosystem = dep["ecosystem"]
        name = dep["dependency"]["name"]
        version = dep["dependency"]["version"]

        # Clean version for PURL (remove ranges, keep simple)
        clean_version = version.replace("^", "").replace("~", "").replace(">", "").replace("<", "").replace("=", "").strip()

        if ecosystem == "npm":
            return f"pkg:npm/{name}@{clean_version}"
        elif ecosystem == "pypi" or ecosystem == "python":
            return f"pkg:pypi/{name}@{clean_version}"
        elif ecosystem == "cargo" or ecosystem == "rust":
            return f"pkg:cargo/{name}@{clean_version}"
        elif ecosystem == "maven" or ecosystem == "java":
            return f"pkg:maven/{name}@{clean_version}"
        elif ecosystem == "docker":
            return f"pkg:docker/{name}@{clean_version}"
        elif ecosystem == "swift":
            return f"pkg:swift/{name}@{clean_version}"
        elif ecosystem == "go" or ecosystem == "golang":
            return f"pkg:golang/{name}@{clean_version}"
        elif ecosystem == "composer" or ecosystem == "php":
            return f"pkg:composer/{name}@{clean_version}"
        elif ecosystem == "nuget" or ecosystem == "dotnet":
            return f"pkg:nuget/{name}@{clean_version}"
        elif ecosystem == "rubygems" or ecosystem == "ruby":
            return f"pkg:gem/{name}@{clean_version}"
        else:
            return f"pkg:generic/{ecosystem}/{name}@{clean_version}"

    def save_sbom(self, sbom: Dict[str, Any], output_path: str):
        """Save SBOM to file"""
        with open(output_path, "w") as f:
            json.dump(sbom, f, indent=2)
