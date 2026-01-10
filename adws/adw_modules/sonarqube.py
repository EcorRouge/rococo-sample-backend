"""SonarQube API integration for fetching code coverage data."""

import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from rococo.models import BaseModel

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    requests = None
    HTTPBasicAuth = None


@dataclass(kw_only=True)
class CoverageFile(BaseModel):
    """Coverage data for a single file."""

    path: str
    coverage_percentage: float
    uncovered_lines: List[int]
    lines_to_cover: int
    uncovered_conditions: int
    lines: int


@dataclass(kw_only=True)
class SonarQubeMetrics(BaseModel):
    """Overall project coverage metrics."""

    coverage: float
    lines_to_cover: int
    uncovered_lines: int
    conditions_to_cover: int
    uncovered_conditions: int


class SonarQubeClient:
    """Client for SonarQube REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        project_key: Optional[str] = None,
    ):
        """Initialize SonarQube client.

        Args:
            base_url: SonarQube server URL (defaults to SONARQUBE_URL env var)
            token: SonarQube authentication token (defaults to SONARQUBE_TOKEN env var)
            project_key: Project key (defaults to SONARQUBE_PROJECT_KEY env var)
        """
        if requests is None:
            raise ImportError(
                "requests library is required for SonarQube integration. "
                "Install with: pip install requests"
            )

        self.base_url = (base_url or os.getenv("SONARQUBE_URL", "")).rstrip("/")
        self.token = token or os.getenv("SONARQUBE_TOKEN")
        self.project_key = project_key or os.getenv(
            "SONARQUBE_PROJECT_KEY", "rococo-sample-backend"
        )
        self.logger = logging.getLogger(__name__)

        if not self.base_url:
            raise ValueError(
                "SonarQube base URL not provided. Set SONARQUBE_URL environment variable."
            )

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make a request to SonarQube API.

        Args:
            endpoint: API endpoint (e.g., '/api/measures/component')
            params: Query parameters

        Returns:
            JSON response as dict, or None if request failed
        """
        url = f"{self.base_url}{endpoint}"

        # Use token authentication if available
        auth = None
        if self.token:
            # SonarQube tokens can be used as basic auth with empty username
            auth = HTTPBasicAuth(self.token, "")

        try:
            response = requests.get(url, params=params, auth=auth, timeout=30)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.logger.error(
                    "SonarQube authentication failed. Check SONARQUBE_TOKEN."
                )
                return None
            elif response.status_code == 404:
                self.logger.warning(
                    f"SonarQube endpoint not found: {endpoint}. Project may not exist."
                )
                return None
            else:
                self.logger.error(
                    f"SonarQube API error: {response.status_code} - {response.text}"
                )
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error connecting to SonarQube: {e}")
            return None

    def get_project_metrics(self) -> Optional[SonarQubeMetrics]:
        """Get overall project coverage metrics.

        Returns:
            SonarQubeMetrics if successful, None otherwise
        """
        params = {
            "component": self.project_key,
            "metricKeys": "coverage,lines_to_cover,uncovered_lines,conditions_to_cover,uncovered_conditions",
        }

        data = self._make_request("/api/measures/component", params)
        if not data:
            return None

        try:
            component = data.get("component", {})
            measures = {m["metric"]: m["value"] for m in component.get("measures", [])}

            return SonarQubeMetrics(
                coverage=float(measures.get("coverage", 0)),
                lines_to_cover=int(measures.get("lines_to_cover", 0)),
                uncovered_lines=int(measures.get("uncovered_lines", 0)),
                conditions_to_cover=int(measures.get("conditions_to_cover", 0)),
                uncovered_conditions=int(measures.get("uncovered_conditions", 0)),
            )
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing SonarQube metrics: {e}")
            return None

    def get_file_coverage(self, file_key: str) -> Optional[CoverageFile]:
        """Get coverage data for a specific file.

        Args:
            file_key: SonarQube file key (e.g., 'rococo-sample-backend:common/models/person.py')

        Returns:
            CoverageFile if successful, None otherwise
        """
        params = {
            "component": file_key,
            "metricKeys": "coverage,lines_to_cover,uncovered_lines,conditions_to_cover,uncovered_conditions,lines",
        }

        data = self._make_request("/api/measures/component", params)
        if not data:
            return None

        try:
            component = data.get("component", {})
            measures = {m["metric"]: m["value"] for m in component.get("measures", [])}

            # Get uncovered lines
            uncovered_lines = []
            uncovered_lines_data = self._make_request(
                "/api/sources/lines",
                {"key": file_key, "from": 1, "to": 10000},
            )

            if uncovered_lines_data:
                sources = uncovered_lines_data.get("sources", [])
                uncovered_lines = [
                    line["line"]
                    for line in sources
                    if line.get("coverageStatus") == "UNCOVERED"
                ]

            # Extract file path from key (remove project prefix)
            path = file_key.replace(f"{self.project_key}:", "")

            return CoverageFile(
                path=path,
                coverage_percentage=float(measures.get("coverage", 0)),
                uncovered_lines=uncovered_lines,
                lines_to_cover=int(measures.get("lines_to_cover", 0)),
                uncovered_conditions=int(measures.get("uncovered_conditions", 0)),
                lines=int(measures.get("lines", 0)),
            )
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing file coverage: {e}")
            return None

    def get_all_files(self) -> List[str]:
        """Get list of all files in the project.

        Returns:
            List of file keys
        """
        params = {
            "component": self.project_key,
            "qualifiers": "FIL",
        }

        data = self._make_request("/api/components/tree", params)
        if not data:
            return []

        try:
            components = data.get("components", [])
            return [comp["key"] for comp in components]
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing file list: {e}")
            return []

    def get_uncovered_files(
        self, min_coverage: float = 100.0
    ) -> List[CoverageFile]:
        """Get all files with coverage less than min_coverage.

        Args:
            min_coverage: Minimum coverage threshold (default: 100.0 for 100%)

        Returns:
            List of CoverageFile objects for uncovered files
        """
        uncovered_files = []
        file_keys = self.get_all_files()

        self.logger.info(f"Checking coverage for {len(file_keys)} files...")

        for file_key in file_keys:
            coverage_file = self.get_file_coverage(file_key)
            if coverage_file and coverage_file.coverage_percentage < min_coverage:
                uncovered_files.append(coverage_file)

        self.logger.info(
            f"Found {len(uncovered_files)} files with coverage < {min_coverage}%"
        )
        return uncovered_files

    def get_coverage_summary(self) -> str:
        """Get a human-readable coverage summary.

        Returns:
            Formatted string with coverage information
        """
        metrics = self.get_project_metrics()
        if not metrics:
            return "Unable to fetch SonarQube coverage metrics."

        uncovered_files = self.get_uncovered_files()

        summary = f"""SonarQube Coverage Summary for {self.project_key}

Overall Coverage: {metrics.coverage:.2f}%
Lines to Cover: {metrics.lines_to_cover}
Uncovered Lines: {metrics.uncovered_lines}
Conditions to Cover: {metrics.conditions_to_cover}
Uncovered Conditions: {metrics.uncovered_conditions}

Files Needing Coverage ({len(uncovered_files)}):
"""

        for file in uncovered_files[:20]:  # Limit to first 20 for readability
            summary += f"  - {file.path}: {file.coverage_percentage:.1f}% coverage ({len(file.uncovered_lines)} uncovered lines)\n"

        if len(uncovered_files) > 20:
            summary += f"  ... and {len(uncovered_files) - 20} more files\n"

        return summary

    def get_uncovered_files_summary(self) -> str:
        """Get a summary of uncovered files formatted for Claude Code.

        Returns:
            JSON-formatted string with uncovered files and their uncovered lines
        """
        uncovered_files = self.get_uncovered_files()

        summary_data = {
            "total_uncovered_files": len(uncovered_files),
            "files": [
                {
                    "path": file.path,
                    "coverage_percentage": file.coverage_percentage,
                    "uncovered_lines": file.uncovered_lines[:50],  # Limit to first 50 lines
                    "total_uncovered_lines": len(file.uncovered_lines),
                    "lines_to_cover": file.lines_to_cover,
                }
                for file in uncovered_files
            ],
        }

        import json

        return json.dumps(summary_data, indent=2)

