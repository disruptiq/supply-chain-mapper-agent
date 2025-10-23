import re
import base64
import json
import os
from pathlib import Path

class RiskHeuristics:
    def __init__(self):
        self.heuristics = [
            self._detect_install_scripts,
            self._detect_obfuscated_code,
            self._detect_git_dependencies,
            self._detect_unpinned_versions,
            self._detect_container_risks,
            self._detect_ci_actions
        ]

    def analyze(self, dependencies, repo_path):
        """
        Analyze dependencies and manifests for potential supply chain risks
        """
        all_signals = []
        
        # Analyze each dependency individually
        for dep in dependencies:
            manifest_path = os.path.join(repo_path, dep["manifest_path"])
            signals = self._analyze_dependency(dep, manifest_path)
            all_signals.extend(signals)
            
            # Also add risk scores to the dependency itself
            if signals:
                dep["risk_score"] = self._calculate_risk_score(signals)
                dep["signals"] = signals
            else:
                dep["risk_score"] = 0.0
                dep["signals"] = []
        
        return all_signals

    def _analyze_dependency(self, dep, manifest_path):
        """
        Analyze a single dependency for risks
        """
        signals = []
        
        for heuristic in self.heuristics:
            try:
                heuristic_signals = heuristic(dep, manifest_path)
                signals.extend(heuristic_signals)
            except Exception as e:
                print(f"Error running heuristic {heuristic.__name__} on {dep.get('manifest_path', 'unknown')}: {e}")
        
        return signals

    def _detect_install_scripts(self, dep, manifest_path):
        """
        Detect suspicious install/postinstall scripts in package.json
        """
        signals = []
        manifest_file = os.path.basename(manifest_path)
        
        if manifest_file == "package.json":
            try:
                with open(manifest_path, "r") as f:
                    package_data = json.load(f)
                
                if "scripts" in package_data:
                    for script_name, script_command in package_data["scripts"].items():
                        if any(keyword in script_name.lower() for keyword in ["install", "postinstall", "preinstall", "prepare"]):
                            # Check for suspicious patterns
                            suspicious_patterns = [
                                (r'curl.*\|.*sh', "Download and execute via pipe to shell"),
                                (r'wget.*\|.*sh', "Download and execute via pipe to shell"),
                                (r'bash.*-c', "Direct bash execution"),
                                (r'python.*-c', "Direct Python execution"),
                                (r'node.*-e', "Direct Node execution"),
                                (r'download', "Contains download keyword"),
                                (r'exec\(', "Contains exec function"),
                                (r'eval\(', "Contains eval function")
                            ]
                            
                            for pattern, description in suspicious_patterns:
                                if re.search(pattern, script_command, re.IGNORECASE):
                                    signals.append({
                                        "type": "postinstall_script",
                                        "file": manifest_path,
                                        "line": None,  # Hard to get exact line from JSON
                                        "detail": f"{script_name} script contains '{description}': {script_command}",
                                        "severity": "high" if any(danger in pattern for danger in ['curl.*\|', 'wget.*\|', 'bash.*-c', 'python.*-c']) else "medium"
                                    })
                                    break  # Only report the first match to avoid duplicates
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return signals

    def _detect_obfuscated_code(self, dep, manifest_path):
        """
        Detect obfuscated or encoded code in manifests and related files
        """
        signals = []
        
        # Check the manifest file for long base64 strings or encoded content
        try:
            with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Look for long base64-like strings
            base64_pattern = r'[A-Za-z0-9+/]{50,}={0,2}'
            matches = re.findall(base64_pattern, content)
            if matches:
                signals.append({
                    "type": "obfuscated_code",
                    "file": manifest_path,
                    "line": None,
                    "detail": f"Found {len(matches)} potential obfuscated base64 strings",
                    "severity": "high"
                })
            
            # Look for potential eval usage in JavaScript/Node files
            if manifest_path.endswith(('.js', '.json')):
                eval_matches = re.findall(r'eval\(|atob\(|btoa\(|String\.fromCharCode\(|unescape\(', content)
                if eval_matches:
                    signals.append({
                        "type": "obfuscated_code",
                        "file": manifest_path,
                        "line": None,
                        "detail": f"Found {len(eval_matches)} potential obfuscation functions",
                        "severity": "medium"
                    })
        except Exception:
            pass  # If we can't read the file, skip checking
        
        return signals

    def _detect_git_dependencies(self, dep, manifest_path):
        """
        Detect git dependencies in manifests
        """
        signals = []
        
        manifest_file = os.path.basename(manifest_path)
        dep_name = dep.get("dependency", {}).get("name", "")
        dep_version = dep.get("dependency", {}).get("version", "")
        
        # Check if version string indicates a git dependency
        git_sources = ["git+", "git@", "github.com", "gitlab.com", "bitbucket.org"]
        if any(source in str(dep_version).lower() for source in git_sources) or \
           any(source in str(dep_name).lower() for source in git_sources):
            signals.append({
                "type": "git_dependency",
                "file": manifest_path,
                "line": dep.get("metadata", {}).get("line_number"),
                "detail": f"Dependency '{dep_name}' uses git source: {dep_version}",
                "severity": "medium"
            })
        
        # For package.json specifically, we can look for git dependencies in the file content
        if manifest_file == "package.json":
            try:
                with open(manifest_path, "r") as f:
                    package_data = json.load(f)
                
                for dep_type in ["dependencies", "devDependencies"]:
                    if dep_type in package_data:
                        for name, version in package_data[dep_type].items():
                            if any(source in str(version).lower() for source in git_sources):
                                signals.append({
                                    "type": "git_dependency", 
                                    "file": manifest_path,
                                    "line": None,
                                    "detail": f"'{name}' uses git source: {version}",
                                    "severity": "medium"
                                })
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # For go.mod files, git dependencies are common in Go ecosystem
        elif manifest_file == "go.mod":
            # This would be detected in the parsing phase, but we'll double check
            pass
        
        return signals

    def _detect_unpinned_versions(self, dep, manifest_path):
        """
        Detect unpinned versions (using *, latest, etc.)
        """
        signals = []
        dep_version = dep.get("dependency", {}).get("version", "")
        
        # Check for unpinned or overly permissive versions
        unpinned_patterns = [
            (r'^\*', "wildcard version"),
            (r'latest', "latest version"),
            (r'^\d+\.\d+\.x', "major.minor.x pattern"),
            (r'^\d+\.x\.x', "major.x.x pattern"),
            (r'^.*x.*', "contains 'x' for wildcard"),
            (r'^>', "unbounded upper version"),
            (r'^<', "unbounded lower version")
        ]
        
        for pattern, description in unpinned_patterns:
            if re.search(pattern, str(dep_version), re.IGNORECASE):
                signals.append({
                    "type": "unpinned_version",
                    "file": dep.get("manifest_path"),
                    "line": dep.get("metadata", {}).get("line_number"),
                    "detail": f"Dependency '{dep.get('dependency', {}).get('name', '')}' has unpinned version '{dep_version}' ({description})",
                    "severity": "medium" if pattern == r'^>' or pattern == r'^<' else "high"
                })
                break  # Only report the first match to avoid duplicates
        
        return signals

    def _detect_container_risks(self, dep, manifest_path):
        """
        Detect risky patterns in Dockerfiles
        """
        signals = []
        
        if dep.get("ecosystem") == "docker":
            dep_version = dep.get("dependency", {}).get("version", "")
            
            # Check if using 'latest' tag which is risky
            if dep_version.lower() == "latest":
                signals.append({
                    "type": "unpinned_base_image",
                    "file": dep.get("manifest_path"),
                    "line": dep.get("metadata", {}).get("line_number"),
                    "detail": f"Base image '{dep.get('dependency', {}).get('name', '')}' uses 'latest' tag",
                    "severity": "high"
                })
            
            # Check Dockerfile content for risky RUN commands
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r") as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line.upper().startswith("RUN "):
                            run_cmd = line[4:]  # Remove "RUN " prefix
                            
                            # Check for risky patterns
                            if re.search(r'curl.*\|.*sh|wget.*\|.*sh', run_cmd, re.IGNORECASE):
                                signals.append({
                                    "type": "container_risk",
                                    "file": manifest_path,
                                    "line": line_num,
                                    "detail": f"RUN command downloads and executes script: {run_cmd}",
                                    "severity": "high"
                                })
                            elif re.search(r'bash.*-c.*\|.*', run_cmd, re.IGNORECASE):
                                signals.append({
                                    "type": "container_risk",
                                    "file": manifest_path,
                                    "line": line_num,
                                    "detail": f"RUN command executes piped shell commands: {run_cmd}",
                                    "severity": "medium"
                                })
                except Exception:
                    pass
        
        return signals

    def _detect_ci_actions(self, dep, manifest_path):
        """
        Detect unpinned CI/CD actions in workflow files
        """
        signals = []
        
        # This would be more relevant for workflow files like .github/workflows/*.yml
        # For now, we'll just check if we're analyzing a workflow file
        if ".github/workflows/" in manifest_path and (manifest_path.endswith(".yml") or manifest_path.endswith(".yaml")):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Look for GitHub Actions with unpinned references
                unpinned_actions = re.findall(r'uses:\s*["\']?([^"\n\'/]+/[^"\n\'/]+)(?:@.*)?["\']?', content)
                
                for action in unpinned_actions:
                    # Check if the action has a pinned version
                    if "@" not in action or any(unpinned in action.lower() for unpinned in ["@main", "@master", "@develop", "@latest"]):
                        signals.append({
                            "type": "unpinned_ci_action",
                            "file": manifest_path,
                            "line": None,  # Would need more complex parsing to get line numbers
                            "detail": f"GitHub Action '{action}' does not use pinned version reference",
                            "severity": "high"
                        })
            except Exception:
                pass  # If we can't read the file, skip checking
        
        return signals

    def _calculate_risk_score(self, signals):
        """
        Calculate a risk score based on the severity of detected signals
        """
        severity_weights = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0
        }
        
        score = 0.0
        for signal in signals:
            severity = signal.get("severity", "medium").lower()
            weight = severity_weights.get(severity, 0.5)
            score += weight
        
        # Normalize the score to be between 0 and 1
        return min(1.0, score / len(signals)) if signals else 0.0