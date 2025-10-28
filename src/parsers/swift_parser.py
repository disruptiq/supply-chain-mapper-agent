import os
import json
from typing import List, Dict, Any


class SwiftParser:
    def __init__(self):
        pass

    def parse(self, manifest_path: str) -> List[Dict[str, Any]]:
        dependencies = []
        filename = os.path.basename(manifest_path)

        if filename == "Package.swift":
            dependencies.extend(self._parse_package_swift(manifest_path))

        return dependencies

    def _parse_package_swift(self, manifest_path: str) -> List[Dict[str, Any]]:
        deps = []
        try:
            with open(manifest_path, "r") as f:
                content = f.read()
        except FileNotFoundError as e:
            print(f"Error reading {manifest_path}: {e}")
            return deps

        # Package.swift is Swift code, look for dependencies array
        # This is a simple regex-based parser for common patterns
        import re

        # Look for .package(url: "url", from: "version") or similar
        package_pattern = r'\.package\(\s*url:\s*"([^"]+)"(?:\s*,\s*(?:from|upToNextMajor|exact):\s*"([^"]+)")?'
        matches = re.findall(package_pattern, content, re.IGNORECASE)

        for match in matches:
            url, version = match
            # Extract package name from URL
            if "/" in url:
                name = url.split("/")[-1].replace(".git", "")
            else:
                name = url

            dep_record = {
                "ecosystem": "swift",
                "manifest_path": os.path.relpath(manifest_path),
                "dependency": {
                    "name": name,
                    "version": version if version else "latest",
                    "source": "swift_package_manager",
                    "resolved": url
                },
                "metadata": {
                    "dev_dependency": False,
                    "line_number": None,
                    "script_section": False
                }
            }
            deps.append(dep_record)

        return deps
