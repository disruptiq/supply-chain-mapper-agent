#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from src.walker import RepoWalker
from src.parsers.npm_parser import NpmParser
from src.parsers.python_parser import PythonParser
from src.parsers.go_parser import GoParser
from src.parsers.dockerfile_parser import DockerfileParser
from src.parsers.rust_parser import RustParser
from src.parsers.java_parser import JavaParser
from src.parsers.ruby_parser import RubyParser
from src.parsers.php_parser import PhpParser
from src.parsers.dotnet_parser import DotNetParser
from src.parsers.yaml_parser import YamlParser
from src.parsers.lockfile_parser import LockfileParser
from src.parsers.swift_parser import SwiftParser
from src.parsers.r_parser import RParser
from src.parsers.makefile_parser import MakefileParser
from src.risk_heuristics import RiskHeuristics
from src.output import OutputFormatter
from src.config import ConfigManager
from src.logger import get_logger
from src.progress import ProgressIndicator
from src.sbom_generator import SBOMGenerator
from src.vulnerability_checker import VulnerabilityChecker
from src.cve_checker import CVEChecker

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
    parser = argparse.ArgumentParser(
        description="Supply Chain Risk Mapper - Scan repositories for dependency risks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py .                                    # Scan current directory
  python main.py repo-to-scan --output report.json    # Custom output file
  python main.py /path/to/repo --format csv          # CSV output
  python main.py repo --verbose --log scan.log       # Verbose with logging
        """
    )
    parser.add_argument("path", type=str, help="Path to the repository to scan")
    parser.add_argument("--output", "-o", type=str, default="output.json",
                       help="Output file for the scan report (default: mapper_report.json)")
    parser.add_argument("--format", "-f", choices=['json', 'csv', 'xml'], default='json',
                       help="Output format (default: json)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--include-binaries", action="store_true", help="Include binary detection in scan")
    parser.add_argument("--config", "-c", type=str, help="Path to config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--log", type=str, help="Log file path")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    parser.add_argument("--check-vulns", action="store_true", help="Check dependencies for known vulnerabilities")
    parser.add_argument("--check-cves", action="store_true", help="Check dependencies for CVEs using NVD")
    parser.add_argument("--no-sbom", action="store_true", help="Skip SBOM generation")

    args = parser.parse_args()

    # Initialize logger
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = get_logger(level=log_level, log_file=args.log, enable_colors=not args.no_color)

    # Validate input path
    scan_path = Path(args.path).resolve()
    if not scan_path.exists():
        logger.error(f"Path does not exist: {scan_path}")
        sys.exit(1)

    if not scan_path.is_dir():
        logger.error(f"Path is not a directory: {scan_path}")
        sys.exit(1)

    logger.info(f"Scanning repository: {scan_path}")

    # Set output file based on format if not specified
    if args.output == "mapper_report.json" and args.format != 'json':
        args.output = f"mapper_report.{args.format}"

    logger.info(f"Output report to: {args.output}")

    try:
        # Initialize config manager
        config_manager = ConfigManager(args.config)
        config = config_manager.get_config()

        # Override config with CLI arguments
        if args.include_binaries:
            config['include_binaries'] = True

        # Initialize progress indicator
        progress = ProgressIndicator(description="Processing manifests")
        if not args.quiet:
            progress.update(0, "Initializing scanner...")

        walker = RepoWalker(str(scan_path), ignore_patterns=config.get('paths_to_ignore', []))
        walk_result = walker.walk()
        found_manifests = walk_result["manifests_found"]

        if not args.quiet:
            progress.set_total(len(found_manifests))
            progress.update(0, f"Found {len(found_manifests)} manifests")

        logger.info(f"Found {len(found_manifests)} manifest files")

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
        yaml_parser = YamlParser()
        lockfile_parser = LockfileParser()
        swift_parser = SwiftParser()
        r_parser = RParser()
        makefile_parser = MakefileParser()

        all_dependencies = []
        processed_count = 0

        for manifest_path in found_manifests:
            full_path = os.path.join(str(scan_path), manifest_path)

            if not args.quiet:
                progress.update()

            try:
                # Route to appropriate parser based on file type
                if os.path.basename(manifest_path) == "package.json":
                    parsed_deps = npm_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} npm dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "package-ts.json":
                    # Use the npm parser for TypeScript package files as they have the same format
                    parsed_deps = npm_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} npm dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "tsconfig.json":
                    # tsconfig.json doesn't contain dependencies, so we skip it
                    logger.debug(f"Skipping tsconfig.json: {manifest_path}")
                    processed_count += 1
                    continue
                elif os.path.basename(manifest_path) in ["requirements.txt", "pyproject.toml", "setup.py"]:
                    parsed_deps = python_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} python dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) in ["go.mod", "go.sum"]:
                    parsed_deps = go_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} go dependencies from {manifest_path}")
                elif "dockerfile" in os.path.basename(manifest_path).lower():
                    parsed_deps = dockerfile_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} docker dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "Cargo.toml":
                    parsed_deps = rust_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} rust dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "pom.xml":
                    parsed_deps = java_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} java dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) in ["Gemfile", "Gemfile.lock"]:
                    parsed_deps = ruby_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} ruby dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) in ["composer.json", "composer.lock"]:
                    parsed_deps = php_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} php dependencies from {manifest_path}")
                elif os.path.basename(manifest_path).endswith(".csproj") or os.path.basename(manifest_path) == "packages.lock.json":
                    parsed_deps = dotnet_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} dotnet dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
                    parsed_deps = lockfile_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} lockfile dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "Package.swift":
                    parsed_deps = swift_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} swift dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "DESCRIPTION":
                    parsed_deps = r_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} r dependencies from {manifest_path}")
                elif manifest_path.endswith('.yml') or manifest_path.endswith('.yaml'):
                    parsed_deps = yaml_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} yaml dependencies from {manifest_path}")
                elif os.path.basename(manifest_path) == "Makefile" or manifest_path.endswith('.mk'):
                    parsed_deps = makefile_parser.parse(full_path)
                    all_dependencies.extend(parsed_deps)
                    logger.debug(f"Parsed {len(parsed_deps)} makefile dependencies from {manifest_path}")
                else:
                    logger.info(f"No parser available for: {manifest_path}")

            except Exception as e:
                logger.error(f"Failed to parse {manifest_path}: {e}")
                if args.verbose:
                    logger.exception("Parser error details:")

            processed_count += 1

        if not args.quiet:
            progress.update(new_description="Analyzing risk signals...")

        logger.info(f"Parsed {len(all_dependencies)} total dependencies")

        # Analyze dependencies for risk signals
        risk_analyzer = RiskHeuristics()
        commit_hash = get_git_commit_hash(str(scan_path))
        risk_signals = risk_analyzer.analyze(all_dependencies, str(scan_path))

        logger.info(f"Identified {len(risk_signals)} risk signals")

        # Check vulnerabilities if requested
        vulnerabilities = []
        if args.check_vulns:
            if not args.quiet:
                progress.update(new_description="Checking vulnerabilities...")
            vuln_checker = VulnerabilityChecker()
            vulnerabilities = vuln_checker.check_vulnerabilities(all_dependencies)
            logger.info(f"Found {len(vulnerabilities)} vulnerabilities")

        # Check CVEs if requested
        cves = []
        if args.check_cves:
            if not args.quiet:
                progress.update(new_description="Checking CVEs...")
            cve_checker = CVEChecker()
            cves = cve_checker.check_cves(all_dependencies)
            logger.info(f"Found {len(cves)} CVEs")

        # Generate SBOM by default (unless disabled)
        if not args.no_sbom:
            if not args.quiet:
                progress.update(new_description="Generating SBOM...")
            sbom_generator = SBOMGenerator()
            sbom = sbom_generator.generate_cyclonedx(all_dependencies, str(scan_path), commit_hash)
            sbom_filename = "sbom.json"
            sbom_generator.save_sbom(sbom, sbom_filename)
            logger.success(f"SBOM saved to: {sbom_filename}")

        # Generate final report
        output_formatter = OutputFormatter(enable_colors=not args.no_color)
        final_report = output_formatter.generate_report(
            repo_path=str(scan_path),
            dependencies=all_dependencies,
            signals=risk_signals,
            commit_hash=commit_hash,
            vulnerabilities=vulnerabilities,
            cves=cves
        )

        # Save the report
        if not args.quiet:
            progress.update(new_description=f"Saving {args.format.upper()} report...")

        success = output_formatter.save_report(final_report, args.output)

        if not args.quiet:
            progress.finish("Scan completed successfully!")

        if success:
            logger.success(f"Report saved to: {args.output}")
            if not args.quiet:
                output_formatter.print_summary(final_report)
        else:
            logger.error(f"Could not save report to {args.output}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        if not args.quiet:
            progress.finish("Scan cancelled")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during scan: {e}")
        if args.verbose:
            logger.exception("Error details:")
        if not args.quiet:
            progress.finish("Scan failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
