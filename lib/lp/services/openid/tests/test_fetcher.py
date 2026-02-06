# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for OpenID fetcher proxy configuration."""

from textwrap import dedent
from urllib.request import HTTPSHandler, ProxyHandler, urlopen

from openid.fetchers import getDefaultFetcher

from lp.services.config import config
from lp.services.openid.fetcher import (
    WSGIFriendlyUrllib2Fetcher,
    set_default_openid_fetcher,
)
from lp.testing import TestCase
from lp.testing.layers import ZopelessLayer


class TestOpenIDFetcherProxy(TestCase):
    """Tests for OpenID fetcher proxy configuration."""

    layer = ZopelessLayer

    def test_fetcher_when_nothing_is_set(self):
        """Test fetcher when no proxy or test env is configured."""
        test_data = dedent(
            """
            [launchpad]
            enable_test_openid_provider: False
            """
        )
        config.push("test_no_proxy", test_data)
        self.addCleanup(config.pop, "test_no_proxy")

        set_default_openid_fetcher()
        fetcher = getDefaultFetcher().fetcher

        # Should be our custom fetcher
        self.assertIsInstance(fetcher, WSGIFriendlyUrllib2Fetcher)

        # Verify no custom opener is set - urlopen should be the default
        self.assertIs(fetcher.urlopen, urlopen)

    def test_fetcher_when_proxy_not_enabled_in_test_env(self):
        """Test fetcher when proxy is not enabled but test env is."""
        test_data = dedent(
            """
            [launchpad]
            enable_test_openid_provider: True
            """
        )
        config.push("test_no_proxy_with_test_env", test_data)
        self.addCleanup(config.pop, "test_no_proxy_with_test_env")

        set_default_openid_fetcher()
        fetcher = getDefaultFetcher().fetcher

        # Should be our custom fetcher
        self.assertIsInstance(fetcher, WSGIFriendlyUrllib2Fetcher)

        # Verify no proxy handler is configured
        opener = fetcher.urlopen.__self__
        proxy_handlers = [
            h for h in opener.handlers if isinstance(h, ProxyHandler)
        ]
        self.assertEqual(len(proxy_handlers), 0)

        # Verify HTTPS handler is configured for test environment
        https_handlers = [
            h for h in opener.handlers if isinstance(h, HTTPSHandler)
        ]
        self.assertEqual(len(https_handlers), 1)

    def test_fetcher_when_proxy_enabled_in_test_env(self):
        """Test fetcher when proxy is enabled in test environment."""
        proxy_url = "http://proxy.example.com:8080"

        test_data = dedent(
            f"""
            [launchpad]
            openid_http_proxy: {proxy_url}
            enable_test_openid_provider: True
            """
        )
        config.push("test_proxy_with_test_env", test_data)
        self.addCleanup(config.pop, "test_proxy_with_test_env")

        set_default_openid_fetcher()
        fetcher = getDefaultFetcher().fetcher

        # Should be our custom fetcher
        self.assertIsInstance(fetcher, WSGIFriendlyUrllib2Fetcher)

        # Verify proxy handler is configured in the opener
        opener = fetcher.urlopen.__self__
        proxy_handlers = [
            h for h in opener.handlers if isinstance(h, ProxyHandler)
        ]
        self.assertEqual(len(proxy_handlers), 1)
        self.assertEqual(proxy_handlers[0].proxies["http"], proxy_url)
        self.assertEqual(proxy_handlers[0].proxies["https"], proxy_url)

        # Verify HTTPS handler is configured
        https_handlers = [
            h for h in opener.handlers if isinstance(h, HTTPSHandler)
        ]
        self.assertEqual(len(https_handlers), 1)

    def test_fetcher_when_proxy_enabled_in_production(self):
        """Test fetcher when proxy is enabled in production."""
        proxy_url = "http://proxy.example.com:8080"
        test_data = dedent(
            f"""
            [launchpad]
            openid_http_proxy: {proxy_url}
            enable_test_openid_provider: False
            """
        )
        config.push("test_proxy_production", test_data)
        self.addCleanup(config.pop, "test_proxy_production")

        set_default_openid_fetcher()
        fetcher = getDefaultFetcher().fetcher

        self.assertIsInstance(fetcher, WSGIFriendlyUrllib2Fetcher)

        # Verify proxy handler is configured in the opener
        opener = fetcher.urlopen.__self__
        proxy_handlers = [
            h for h in opener.handlers if isinstance(h, ProxyHandler)
        ]
        self.assertEqual(len(proxy_handlers), 1)
        self.assertEqual(proxy_handlers[0].proxies["http"], proxy_url)
        self.assertEqual(proxy_handlers[0].proxies["https"], proxy_url)
