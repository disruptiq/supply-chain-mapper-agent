import requests
import json
from typing import List, Dict, Any, Optional
import time


class CVEChecker:
    def __init__(self):
        self.nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.cache = {}  # Simple in-memory cache
        self.last_request_time = 0
        self.rate_limit_delay = 1  # Initial delay: 1 second between requests
        self.max_delay = 10  # Maximum delay: 10 seconds

    def check_cves(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check dependencies for CVEs"""
        cves = []

        for dep in dependencies:
            cve_list = self._check_single_dependency(dep)
            if cve_list:
                cves.extend(cve_list)

        return cves

    def _check_single_dependency(self, dep: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Check a single dependency for CVEs"""
        ecosystem = dep["ecosystem"]
        name = dep["dependency"]["name"]
        version = dep["dependency"]["version"]

        # Always use keyword search for reliability
        query = f"{name} {version}"

        cache_key = f"{ecosystem}/{name}/{version}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        params = {
            "keywordSearch": query,
            "resultsPerPage": 5  # Limit results
        }

        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

        def process_response(data):
            """Process the API response data into CVE records"""
            # Reset delay on successful request
            if self.rate_limit_delay > 1:
                self.rate_limit_delay = max(1, self.rate_limit_delay // 2)

            cve_records = []
            if "vulnerabilities" in data:
                for vuln in data["vulnerabilities"]:
                    cve = vuln["cve"]
                    cve_record = {
                        "dependency": dep,
                        "cve": {
                            "id": cve.get("id", ""),
                            "description": self._get_description(cve),
                            "severity": self._get_severity(cve),
                            "references": cve.get("references", []),
                            "published": cve.get("published", ""),
                            "lastModified": cve.get("lastModified", "")
                        }
                    }
                    cve_records.append(cve_record)

            self.cache[cache_key] = cve_records if cve_records else None
            return cve_records

        try:
            response = requests.get(self.nvd_api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return process_response(data)

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited, increase delay
                self.rate_limit_delay = min(self.max_delay, self.rate_limit_delay * 2)
                print(f"Rate limited, increasing delay to {self.rate_limit_delay} seconds")
                # Sleep extra and retry once
                time.sleep(self.rate_limit_delay)
                try:
                    response = requests.get(self.nvd_api_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    return process_response(data)
                except Exception:
                    pass  # Fall through to error handling
            print(f"Error checking CVEs for {name}: {e}")
            self.cache[cache_key] = None
            return None
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error checking CVEs for {name}: {e}")
            self.cache[cache_key] = None
            return None



    def _get_description(self, cve: Dict[str, Any]) -> str:
        """Extract description from CVE data"""
        descriptions = cve.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                return desc.get("value", "")
        return ""

    def _get_severity(self, cve: Dict[str, Any]) -> str:
        """Extract severity from CVE data"""
        metrics = cve.get("metrics", {})
        # Check cvssMetricV31 first, then v30, v2
        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics:
                base_score = metrics[version][0]["cvssData"].get("baseScore", 0)
                if base_score >= 9.0:
                    return "CRITICAL"
                elif base_score >= 7.0:
                    return "HIGH"
                elif base_score >= 4.0:
                    return "MEDIUM"
                elif base_score >= 0.1:
                    return "LOW"
                else:
                    return "NONE"
        return "UNKNOWN"
