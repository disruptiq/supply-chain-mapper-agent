import re
from typing import List, Dict, Any
from pathlib import Path


class MakefileParser:
    """Parser for Makefile dependencies (C/C++ projects)"""

    def __init__(self):
        # Patterns to extract dependencies
        self.lib_patterns = [
            re.compile(r'^LIBS\s*[:+]?=\s*(.+)', re.MULTILINE),
            re.compile(r'^LDLIBS\s*[:+]?=\s*(.+)', re.MULTILINE),
            re.compile(r'^LDFLAGS\s*[:+]?=\s*(.+)', re.MULTILINE),
        ]

        self.include_patterns = [
            re.compile(r'^CPPFLAGS\s*[:+]?=\s*(.+)', re.MULTILINE),
            re.compile(r'^CFLAGS\s*[:+]?=\s*(.+)', re.MULTILINE),
            re.compile(r'^CXXFLAGS\s*[:+]?=\s*(.+)', re.MULTILINE),
        ]

        self.pkg_config_patterns = [
            re.compile(r'`pkg-config\s+--libs\s+([^`]+)`', re.MULTILINE),
            re.compile(r'\$\(shell\s+pkg-config\s+--libs\s+([^)]+)\)', re.MULTILINE),
        ]

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Makefile for dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading Makefile {file_path}: {e}")
            return []

        dependencies = []

        # Extract library dependencies
        lib_deps = self._extract_libraries(content)
        for lib in lib_deps:
            dependencies.append({
                "ecosystem": "makefile",
                "manifest_path": file_path,
                "dependency": {
                    "name": lib,
                    "version": "*",
                    "source": "system",
                    "resolved": None
                },
                "metadata": {
                    "dev_dependency": False,
                    "line_number": self._find_line_number(content, lib),
                    "script_section": False
                }
            })

        # Extract pkg-config dependencies
        pkg_deps = self._extract_pkg_config(content)
        for pkg in pkg_deps:
            dependencies.append({
                "ecosystem": "makefile",
                "manifest_path": file_path,
                "dependency": {
                    "name": pkg,
                    "version": "*",
                    "source": "pkg-config",
                    "resolved": None
                },
                "metadata": {
                    "dev_dependency": False,
                    "line_number": self._find_line_number(content, pkg),
                    "script_section": False
                }
            })

        return dependencies

    def _extract_libraries(self, content: str) -> List[str]:
        """Extract library names from LIBS, LDLIBS, LDFLAGS variables"""
        libraries = set()

        for pattern in self.lib_patterns:
            matches = pattern.findall(content)
            for match in matches:
                # Split on whitespace and extract -l flags
                parts = match.split()
                for part in parts:
                    part = part.strip()
                    if part.startswith('-l'):
                        lib_name = part[2:]  # Remove -l prefix
                        if lib_name and not lib_name.startswith('$'):
                            libraries.add(lib_name)
                    elif part.startswith('-L'):
                        # Skip library paths
                        continue
                    elif part.startswith('-Wl,'):
                        # Skip linker options
                        continue
                    elif part == '-lm' or part == '-lc' or part == '-lgcc':
                        # Skip standard C libraries
                        continue
                    elif not part.startswith('-') and not part.startswith('$'):
                        # Might be a library name without -l
                        libraries.add(part)

        return list(libraries)

    def _extract_pkg_config(self, content: str) -> List[str]:
        """Extract pkg-config package names"""
        packages = set()

        for pattern in self.pkg_config_patterns:
            matches = pattern.findall(content)
            for match in matches:
                # Split on whitespace to get package names
                pkg_names = match.split()
                for pkg in pkg_names:
                    pkg = pkg.strip()
                    if pkg and not pkg.startswith('$'):
                        packages.add(pkg)

        return list(packages)

    def _find_line_number(self, content: str, target: str) -> int:
        """Find line number containing the target string"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if target in line:
                return i
        return 0
