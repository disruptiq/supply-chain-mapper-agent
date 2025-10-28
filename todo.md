# Supply Chain Risk Mapper - Enhancement Roadmap

This document outlines planned improvements to make the scanner more comprehensive, accurate, and user-friendly.

## 🔴 High Priority (Core Functionality)

### 1. Vulnerability Database Integration
- [ ] Integrate with OSV.dev for vulnerability checking
- [ ] Add CVE database integration (NVD)
- [ ] Implement real-time security issue detection
- [ ] Add severity scoring and exploitability metrics
- [ ] Cache vulnerability data for offline mode

### 2. SBOM (Software Bill of Materials) Generation
- [ ] Generate CycloneDX format SBOMs
- [ ] Generate SPDX format SBOMs
- [ ] Include dependency trees and metadata
- [ ] Support NTIA/EU CRA compliance
- [ ] Add SBOM export functionality

## 🟡 Medium Priority (Enhanced Analysis)

### 3. License Scanning & Compliance
- [ ] Add license detection for dependencies
- [ ] Integrate SPDX license database
- [ ] Flag incompatible licenses
- [ ] Add license compliance checking
- [ ] Generate license reports

### 4. Advanced Risk Heuristics
- [ ] Analyze dependency depth and attack surface
- [ ] Detect unpinned versions and deprecated packages
- [ ] Score based on maintainer activity and download counts
- [ ] Add machine learning for anomaly detection
- [ ] Implement risk scoring algorithms

### 5. Expanded Parser Coverage
- [ ] Add Swift (Package.swift) parser
- [ ] Add Kotlin (build.gradle.kts) parser
- [ ] Add Scala (build.sbt) parser
- [ ] Add R (DESCRIPTION) parser
- [ ] Support additional lockfiles (poetry.lock, etc.)
- [ ] Handle monorepo structures

## 🟢 Low Priority (Integration & UX)

### 6. REST API Endpoints
- [ ] Add Flask/FastAPI server
- [ ] Implement programmatic scanning API
- [ ] Add CI/CD webhook support
- [ ] Support bulk repository scanning

### 7. Web Dashboard
- [ ] Create React/Vue frontend
- [ ] Add result visualization and heatmaps
- [ ] Implement historical trend analysis
- [ ] Add export capabilities (PDF, CSV)

### 8. Plugin Architecture
- [ ] Develop plugin system for custom parsers
- [ ] Allow custom risk rules
- [ ] Community-contributed ecosystem support

### 9. Incremental Scanning
- [ ] Implement result caching
- [ ] Add git diff-based rescanning
- [ ] Database storage for historical data

### 10. CI/CD Integration Templates
- [ ] Create GitHub Actions templates
- [ ] Add GitLab CI pipelines
- [ ] Implement Jenkins integration
- [ ] Add automated PR comments

## 💡 Additional Features

- [ ] Multi-threaded processing for large repos
- [ ] Container image scanning
- [ ] Dependency confusion detection
- [ ] Supply chain provenance verification
- [ ] Interactive HTML reports
- [ ] Notification system (Slack/Email)

## Implementation Notes

- Start with vulnerability integration and SBOM for immediate security value
- Prioritize parser expansions for broader ecosystem coverage
- Use plugin system for long-term extensibility
- Focus on compliance features for enterprise adoption</content>
</xai:function_call">Successfully created file /f:/disruptiq/supply-chain-mapper-agent/todo.md
