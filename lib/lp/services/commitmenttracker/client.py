# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "CommitmentTrackerClient",
    "get_commitment_tracker_client",
]

import json
import logging
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from lp.services.config import config


class CommitmentTrackerClient:
    """Thin HTTP client for sending release payloads to CT."""

    CT_MAX_RETRIES = 5

    def __init__(
        self,
        base_url: str,
        release_endpoint: str = "/release",
        api_key: Optional[str] = None,
        timeout: int = 5,
        http_proxy: Optional[str] = None,
        ca_certificates_path: Optional[str] = None,
    ):
        if not base_url:
            raise ValueError("CommitmentTrackerClient base_url is required")

        self.endpoint = (
            f"{base_url.rstrip('/')}/{release_endpoint.lstrip('/')}"
        )
        self.timeout = timeout
        self.logger = logging.getLogger()
        self.session = self._make_session(
            api_key, http_proxy, ca_certificates_path
        )

    def _make_session(
        self,
        api_key: Optional[str],
        http_proxy: Optional[str],
        ca_certificates_path: Optional[str],
    ) -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        if http_proxy:
            session.proxies = {"http": http_proxy, "https": http_proxy}
        if ca_certificates_path:
            session.verify = ca_certificates_path
        if api_key:
            session.headers.update({"x-api-key": api_key})
        session.headers.update({"Content-Type": "application/json"})
        return session

    def send_payloads_with_results(
        self, payloads: Iterable[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """Send payloads and return (success_count, failure_errors)."""
        total = 0
        sent = 0
        failure_errors: List[str] = []
        for payload in payloads:
            total += 1
            summary = self._payload_summary(payload)
            try:
                self._post_with_retries(payload, summary)
                sent += 1
            except Exception:
                failure_errors.append(summary)
        self.logger.info("[CT] posted %d/%d payloads", sent, total)
        return sent, failure_errors

    def _post_with_retries(
        self,
        payload: Dict[str, Any],
        summary: str,
    ):
        delay = 1.0
        last_error: Optional[Exception] = None
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(self.CT_MAX_RETRIES):
            try:
                resp = self.session.post(
                    self.endpoint, data=body, timeout=self.timeout
                )
                if 200 <= resp.status_code < 300:
                    return
                if resp.status_code == 409:
                    # Idempotent conflict; treat as success.
                    self.logger.info(
                        "[CT] received 409 (idempotent); "
                        "treating as success. %s",
                        summary,
                    )
                    return
                last_error = Exception(
                    f"CT POST failed: status={resp.status_code} "
                    f"body={resp.text} payload={summary}"
                )
            except requests.RequestException as exc:
                last_error = Exception(f"{exc} payload={summary}")

            if attempt < self.CT_MAX_RETRIES - 1:
                time.sleep(delay)
                delay = min(delay * 2, 30.0)

        if last_error:
            raise last_error
        raise Exception("CT POST failed for unknown reasons")

    def _payload_summary(self, payload: Dict[str, Any]) -> str:
        """Best-effort small summary for logging without dumping payload."""
        try:
            release = payload.get("release", {}) or {}
            props = release.get("properties", {}) or {}
            return (
                f"type={props.get('type') or '?'} "
                f"sha256={props.get('sha256') or '?'} "
                f"name={props.get('name') or '?'} "
                f"version={props.get('version') or '?'} "
                f"base={props.get('archive_base') or '?'} "
                f"archive={props.get('archive_reference') or '?'} "
                f"series={props.get('archive_series') or '?'} "
                f"component={props.get('archive_component') or '?'} "
                f"pocket={props.get('archive_pocket') or '?'}"
            )
        except Exception:
            return "unparsable-payload"


def get_commitment_tracker_client() -> CommitmentTrackerClient:
    """Build a client from config; callers should ensure config exists."""
    ct_config = getattr(config, "commitment_tracker", None)
    base_url = getattr(ct_config, "base_url", None)
    release_endpoint = getattr(ct_config, "release_endpoint", "/release")

    def _clean_url(url: Optional[str]) -> Optional[str]:
        if not url or url == "none":
            return None
        return url.rstrip("/")

    base_url = _clean_url(base_url)

    if not base_url:
        raise ValueError("Commitment Tracker base_url is required")

    api_key = getattr(ct_config, "api_key", None)
    timeout = getattr(ct_config, "timeout", 5)
    http_proxy = getattr(config.launchpad, "http_proxy", None)
    ca_certificates_path = getattr(
        config.launchpad, "ca_certificates_path", None
    )
    return CommitmentTrackerClient(
        base_url=base_url,
        release_endpoint=release_endpoint,
        api_key=api_key,
        timeout=timeout,
        http_proxy=http_proxy,
        ca_certificates_path=ca_certificates_path,
    )
