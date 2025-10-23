import argparse
import json
import os
import subprocess
from walker import RepoWalker
from parsers.npm_parser import NpmParser
from parsers.python_parser import PythonParser
from parsers.go_parser import GoParser
from parsers.dockerfile_parser import DockerfileParser
from parsers.rust_parser import RustParser
from parsers.java_parser import JavaParser
from parsers.ruby_parser import RubyParser
from parsers.php_parser import PhpParser
from parsers.dotnet_parser import DotNetParser
from risk_heuristics import RiskHeuristics
from output import OutputFormatter
from config import ConfigManager

def get_git_commit_hash(repo_path):
    """Get the current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            cwd=repo_path, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]  # Short hash
    except Exception:
        pass
    return "unknown"

def main():
    parser = argparse.ArgumentParser(description="Supply Chain Risk Mapper")
    parser.add_argument("--path", type=str, default=".", help="Path to the repository to scan")
    parser.add_argument("--output", type=str, default="mapper_report.json", help="Output file for the scan report")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--include-binaries", action="store_true", help="Include binary detection in scan")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()

    print(f"Scanning repository: {args.path}")
    print(f"Output report to: {args.output}")

    # Initialize config manager
    config_manager = ConfigManager(args.config)
    config = config_manager.get_config()
    
    # Override config with CLI arguments
    if args.include_binaries:
        config['include_binaries'] = True

    walker = RepoWalker(args.path, ignore_patterns=config.get('paths_to_ignore', []))
    found_manifests = walker.walk()["manifests_found"]

    # Initialize all parsers
    npm_parser = NpmParser()
    python_parser = PythonParser()
    go_parser = GoParser()
    dockerfile_parser = DockerfileParser()
    rust_parser = RustParser()
    java_parser = JavaParser()
    ruby_parser = RubyParser()
    php_parser = PhpParser()
    dotnet_parser = DotNetParser()

    all_dependencies = []

    for manifest_path in found_manifests:
        full_path = os.path.join(args.path, manifest_path)
        
        # Route to appropriate parser based on file type
        if os.path.basename(manifest_path) == "package.json":
            parsed_deps = npm_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) == "package-ts.json":
            # Use the npm parser for TypeScript package files as they have the same format
            parsed_deps = npm_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) == "tsconfig.json":
            # tsconfig.json doesn't contain dependencies, so we skip it
            continue
        elif os.path.basename(manifest_path) in ["requirements.txt", "pyproject.toml"]:
            parsed_deps = python_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) in ["go.mod", "go.sum"]:
            parsed_deps = go_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif "dockerfile" in os.path.basename(manifest_path).lower():
            parsed_deps = dockerfile_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) == "Cargo.toml":
            parsed_deps = rust_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) == "pom.xml":
            parsed_deps = java_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) in ["Gemfile", "Gemfile.lock"]:
            parsed_deps = ruby_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path) in ["composer.json", "composer.lock"]:
            parsed_deps = php_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)
        elif os.path.basename(manifest_path).endswith(".csproj") or os.path.basename(manifest_path) == "packages.lock.json":
            parsed_deps = dotnet_parser.parse(full_path)
            all_dependencies.extend(parsed_deps)

    # Analyze dependencies for risk signals
    risk_analyzer = RiskHeuristics()
    commit_hash = get_git_commit_hash(args.path)
    risk_signals = risk_analyzer.analyze(all_dependencies, args.path)

    # Generate final report
    output_formatter = OutputFormatter()
    final_report = output_formatter.generate_report(
        repo_path=args.path,
        dependencies=all_dependencies,
        signals=risk_signals,
        commit_hash=commit_hash
    )

    # Save the report
    success = output_formatter.save_report(final_report, args.output)

    if success:
        print(f"Scan completed successfully!")
        output_formatter.print_summary(final_report)
    else:
        print(f"Error: Could not save report to {args.output}")

if __name__ == "__main__":
    main()
