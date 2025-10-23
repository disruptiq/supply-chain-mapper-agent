import os
import pathspec

class RepoWalker:
    # Define known manifest and lockfile patterns
    MANIFEST_PATTERNS = {
        "javascript": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "typescript": ["package-ts.json", "tsconfig.json"],
        "python": ["requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "java": ["pom.xml", "build.gradle", "gradle.lockfile"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "php": ["composer.json", "composer.lock"],
        "dotnet": ["*.csproj", "packages.lock.json"],
        "container": ["Dockerfile", "docker-compose.yml"],
        "ci_cd": [".github/workflows/*.yml", ".gitlab-ci.yml"],
        "git": [".gitmodules"],
        "other": ["setup.py", "setup.cfg", "Makefile"]
    }

    def __init__(self, repo_path, ignore_patterns=None):
        self.repo_path = os.path.abspath(repo_path)
        self.ignore_patterns = ignore_patterns if ignore_patterns is not None else []
        # Add default ignore patterns if none provided
        if not self.ignore_patterns:
            self.ignore_patterns = [
                "node_modules/",
                "vendor/",
                ".git/",
                "__pycache__/",
                "*.log",
                "dist/",
                "build/",
                ".venv/",
                "venv/"
            ]
        self.manifests_found = []

    def _load_gitignore(self):
        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                gitignore_lines = f.readlines()
                # Add our custom ignore patterns to gitignore spec
                all_patterns = [line.strip() for line in gitignore_lines if line.strip() and not line.startswith('#')]
                all_patterns.extend(self.ignore_patterns)
                return pathspec.PathSpec.from_lines("gitwildmatch", all_patterns)
        else:
            # If no .gitignore, just use our custom ignore patterns
            return pathspec.PathSpec.from_lines("gitwildmatch", self.ignore_patterns)

    def walk(self):
        gitignore_spec = self._load_gitignore()
        
        for root, dirs, files in os.walk(self.repo_path):
            # Filter out ignored directories
            if gitignore_spec:
                # Create a list of directories to prune
                prune_dirs = []
                for d in dirs:
                    relative_path = os.path.relpath(os.path.join(root, d), self.repo_path)
                    # Add trailing slash to match directory patterns
                    if gitignore_spec.match_file(relative_path + os.sep):
                        prune_dirs.append(d)
                
                # Modify dirs in-place to prevent os.walk from entering ignored directories
                for d in prune_dirs:
                    dirs.remove(d)

            for file in files:
                relative_file_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                
                # Check against combined gitignore and custom ignore patterns
                if gitignore_spec and gitignore_spec.match_file(relative_file_path):
                    continue

                # Check if the file matches any manifest pattern
                for ecosystem, patterns in self.MANIFEST_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.startswith("*"): # Handle patterns like *.csproj
                            if file.endswith(pattern[1:]):
                                self.manifests_found.append(relative_file_path)
                                break
                        elif pattern.find("*") != -1: # Handle glob patterns like .github/workflows/*.yml
                            # For glob patterns, we'll use pathspec
                            pathspec_pattern = pathspec.PathSpec.from_lines('gitwildmatch', [pattern])
                            if pathspec_pattern.match_file(relative_file_path):
                                self.manifests_found.append(relative_file_path)
                                break
                        elif file == pattern:
                            self.manifests_found.append(relative_file_path)
                            break
                    else:
                        continue
                    break # Break from inner loop if manifest found

                # Special handling for Dockerfiles with different naming
                if "dockerfile" in os.path.basename(relative_file_path).lower():
                    if relative_file_path not in self.manifests_found:
                        self.manifests_found.append(relative_file_path)

        return {"repo_path": self.repo_path, "manifests_found": sorted(list(set(self.manifests_found)))}