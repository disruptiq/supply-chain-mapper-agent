import os
import json
import yaml
from typing import Optional, Dict, Any
import requests


class LicenseDetector:
    def __init__(self):
        # Simple license compatibility mapping
        self.incompatible_licenses = {
            'GPL-2.0', 'GPL-3.0', 'LGPL-2.1', 'LGPL-3.0', 'AGPL-3.0'
        }
        self.permissive_licenses = {
            'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'ISC'
        }

    def detect_license(self, manifest_path: str, dependency_name: str, ecosystem: str) -> Optional[str]:
        """Detect license from manifest file"""
        filename = os.path.basename(manifest_path)

        try:
            if filename == "package.json" and ecosystem == "npm":
                return self._detect_npm_license(manifest_path, dependency_name)
            elif filename == "Cargo.toml" and ecosystem == "rust":
                return self._detect_cargo_license(manifest_path, dependency_name)
            elif filename == "DESCRIPTION" and ecosystem == "r":
                return self._detect_r_license(manifest_path, dependency_name)
            # Add more as needed
        except Exception as e:
            print(f"Error detecting license for {dependency_name}: {e}")

        return None

    def _detect_npm_license(self, manifest_path: str, dependency_name: str) -> Optional[str]:
        with open(manifest_path, "r") as f:
            data = json.load(f)
        return data.get("license")

    def _detect_cargo_license(self, manifest_path: str, dependency_name: str) -> Optional[str]:
        # For Cargo.toml, license is usually in the package section
        # For dependencies, we'd need to check Cargo.lock or query crates.io
        # Simplified: assume it's in the manifest
        try:
            with open(manifest_path, "r") as f:
                content = f.read()
            # Look for license in [package] section
            import re
            license_match = re.search(r'license\s*=\s*"([^"]+)"', content)
            if license_match:
                return license_match.group(1)
        except:
            pass
        return None

    def _detect_r_license(self, manifest_path: str, dependency_name: str) -> Optional[str]:
        with open(manifest_path, "r") as f:
            content = f.read()
        # Look for License field
        for line in content.split('\n'):
            if line.startswith('License:'):
                return line.split(':', 1)[1].strip()
        return None

    def check_license_compliance(self, license: str, project_license: str = "MIT") -> Dict[str, Any]:
        """Check if dependency license is compatible with project license"""
        if not license:
            return {"compatible": False, "reason": "Unknown license", "severity": "high"}

        # Simple compatibility check
        if project_license in self.permissive_licenses:
            # Permissive project can use most licenses
            if license in self.incompatible_licenses:
                return {"compatible": False, "reason": f"Copyleft license {license} incompatible with {project_license}", "severity": "high"}
            else:
                return {"compatible": True, "reason": "Compatible", "severity": "low"}

        return {"compatible": True, "reason": "Compatibility not checked", "severity": "medium"}
