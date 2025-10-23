import json
import os
import csv
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class OutputFormatter:
    def __init__(self, enable_colors: bool = True):
        self.enable_colors = enable_colors

    def generate_report(self, repo_path, dependencies, signals, commit_hash="unknown"):
        """
        Generate the final JSON report according to the specification
        """
        ecosystems_detected = list(set(dep["ecosystem"] for dep in dependencies))
        
        report = {
            "repo": {
                "path": os.path.abspath(repo_path),
                "commit_hash": commit_hash,
                "scan_date": datetime.utcnow().isoformat() + "Z"
            },
            "scan_summary": {
                "total_manifests": len(set(dep["manifest_path"] for dep in dependencies)),
                "ecosystems_detected": ecosystems_detected,
                "total_dependencies": len(dependencies),
                "total_signals": len(signals)
            },
            "dependencies": dependencies
        }
        
        return report

    def save_report(self, report, output_path):
        """
        Save the report to a file with automatic format detection
        """
        output_path = Path(output_path)

        if output_path.suffix.lower() == '.json':
            return self._save_json(report, output_path)
        elif output_path.suffix.lower() == '.csv':
            return self._save_csv(report, output_path)
        elif output_path.suffix.lower() == '.xml':
            return self._save_xml(report, output_path)
        else:
            # Default to JSON
            return self._save_json(report, output_path)

    def _save_json(self, report, output_path):
        """Save report as JSON"""
        try:
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON report to {output_path}: {e}")
            return False

    def _save_csv(self, report, output_path):
        """Save report as CSV"""
        try:
            with open(output_path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    'Ecosystem', 'Manifest_Path', 'Name', 'Version', 'Source',
                    'Dev_Dependency', 'Line_Number', 'Script_Section',
                    'Risk_Score', 'Signals_Count'
                ])

                # Write data
                for dep in report.get('dependencies', []):
                    dependency = dep.get('dependency', {})
                    metadata = dep.get('metadata', {})
                    signals = dep.get('signals', [])

                    writer.writerow([
                        dep.get('ecosystem', ''),
                        dep.get('manifest_path', ''),
                        dependency.get('name', ''),
                        dependency.get('version', ''),
                        dependency.get('source', ''),
                        metadata.get('dev_dependency', False),
                        metadata.get('line_number', ''),
                        metadata.get('script_section', False),
                        dep.get('risk_score', 0),
                        len(signals)
                    ])

            return True
        except Exception as e:
            print(f"Error saving CSV report to {output_path}: {e}")
            return False

    def _save_xml(self, report, output_path):
        """Save report as XML"""
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom

            root = Element('SupplyChainReport')

            # Repo info
            repo = SubElement(root, 'Repository')
            repo_info = report.get('repo', {})
            SubElement(repo, 'Path').text = repo_info.get('path', '')
            SubElement(repo, 'CommitHash').text = repo_info.get('commit_hash', '')
            SubElement(repo, 'ScanDate').text = repo_info.get('scan_date', '')

            # Scan summary
            summary = SubElement(root, 'ScanSummary')
            scan_summary = report.get('scan_summary', {})
            SubElement(summary, 'TotalManifests').text = str(scan_summary.get('total_manifests', 0))
            SubElement(summary, 'TotalDependencies').text = str(scan_summary.get('total_dependencies', 0))
            SubElement(summary, 'TotalSignals').text = str(scan_summary.get('total_signals', 0))

            ecosystems = SubElement(summary, 'EcosystemsDetected')
            for ecosystem in scan_summary.get('ecosystems_detected', []):
                SubElement(ecosystems, 'Ecosystem').text = ecosystem

            # Dependencies
            dependencies_elem = SubElement(root, 'Dependencies')
            for dep in report.get('dependencies', []):
                dep_elem = SubElement(dependencies_elem, 'Dependency')

                SubElement(dep_elem, 'Ecosystem').text = dep.get('ecosystem', '')
                SubElement(dep_elem, 'ManifestPath').text = dep.get('manifest_path', '')

                dependency = dep.get('dependency', {})
                dep_info = SubElement(dep_elem, 'DependencyInfo')
                SubElement(dep_info, 'Name').text = dependency.get('name', '')
                SubElement(dep_info, 'Version').text = dependency.get('version', '')
                SubElement(dep_info, 'Source').text = dependency.get('source', '')

                metadata = dep.get('metadata', {})
                meta_elem = SubElement(dep_elem, 'Metadata')
                SubElement(meta_elem, 'DevDependency').text = str(metadata.get('dev_dependency', False))
                SubElement(meta_elem, 'LineNumber').text = str(metadata.get('line_number', ''))
                SubElement(meta_elem, 'ScriptSection').text = str(metadata.get('script_section', False))

                SubElement(dep_elem, 'RiskScore').text = str(dep.get('risk_score', 0))

                signals_elem = SubElement(dep_elem, 'Signals')
                for signal in dep.get('signals', []):
                    signal_elem = SubElement(signals_elem, 'Signal')
                    SubElement(signal_elem, 'Type').text = signal.get('type', '')
                    SubElement(signal_elem, 'File').text = signal.get('file', '')
                    SubElement(signal_elem, 'Line').text = str(signal.get('line', ''))
                    SubElement(signal_elem, 'Detail').text = signal.get('detail', '')
                    SubElement(signal_elem, 'Severity').text = signal.get('severity', '')

            # Pretty print XML
            rough_string = tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            with open(output_path, "w", encoding='utf-8') as f:
                f.write(pretty_xml)

            return True
        except Exception as e:
            print(f"Error saving XML report to {output_path}: {e}")
            return False

    def print_summary(self, report):
        """
        Print a summary of the scan results to stdout with colors
        """
        def colorize(text, color_code):
            if self.enable_colors:
                return f"\033[{color_code}m{text}\033[0m"
            return text

        # Color codes: 32=green, 33=yellow, 31=red, 36=cyan, 35=magenta
        print(f"\n{colorize('Scan Summary:', '1;36')}")
        print(f"|- Repository: {colorize(report['repo']['path'], '32')}")
        print(f"|- Commit: {colorize(report['repo']['commit_hash'], '33')}")
        print(f"|- Scan Date: {colorize(report['repo']['scan_date'], '36')}")
        print(f"|- Total Dependencies: {colorize(str(report['scan_summary']['total_dependencies']), '1;32')}")
        print(f"|- Total Manifests: {colorize(str(report['scan_summary']['total_manifests']), '32')}")
        print(f"|- Ecosystems Detected: {colorize(', '.join(report['scan_summary']['ecosystems_detected']), '35')}")
        print(f"\\- Total Risk Signals: {colorize(str(report['scan_summary']['total_signals']), '1;31')}")

        # Breakdown by ecosystem with colors
        print(f"\n{colorize('Dependencies by Ecosystem:', '1;36')}")
        for i, ecosystem in enumerate(report['scan_summary']['ecosystems_detected']):
            count = len([dep for dep in report['dependencies'] if dep['ecosystem'] == ecosystem])
            prefix = "|-" if i < len(report['scan_summary']['ecosystems_detected']) - 1 else "\\-"
            print(f"  {prefix} {colorize(ecosystem, '35')}: {colorize(str(count), '32')} dependencies")

        # Show top risk signals if any
        if report['scan_summary']['total_signals'] > 0:
            print(f"\n{colorize('Top Risk Signals:', '1;33')}")
            # Group signals by severity
            signals = []
            for dep in report['dependencies']:
                signals.extend(dep.get('signals', []))

            severity_counts = {}
            for signal in signals:
                severity = signal.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            severity_colors = {'critical': '1;31', 'high': '31', 'medium': '33', 'low': '32'}
            for severity, count in severity_counts.items():
                color = severity_colors.get(severity.lower(), '37')
                print(f"  |- {colorize(severity.title(), color)}: {colorize(str(count), '1;31')} signals")