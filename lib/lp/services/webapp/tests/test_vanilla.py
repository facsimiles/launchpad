# Copyright 2009-2024 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for the vanilla base layout template."""

from lp.services.beautifulsoup import BeautifulSoup
from lp.services.webapp.publisher import canonical_url, rootObject
from lp.testing import BrowserTestCase, TestCaseWithFactory, login_person
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.pages import extract_text, find_tag_by_id
from lp.testing.views import create_initialized_view


class TestVanillaBaseLayout(TestCaseWithFactory):
    """Test the vanilla base layout template."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.context = rootObject

    def _makeView(self):
        user = self.factory.makeAdministrator()
        login_person(user)
        return create_initialized_view(
            self.context, "+vanilla-test", principal=user
        )

    def test_vanilla_layout_doctype(self):
        view = self._makeView()
        markup = view()
        self.assertTrue(markup.strip().startswith("<!DOCTYPE html>"))

    def test_vanilla_layout_html_element(self):
        view = self._makeView()
        content = BeautifulSoup(view())
        self.assertEqual("http://www.w3.org/1999/xhtml", content.html["xmlns"])
        html_tag = content.html
        self.assertEqual("en", html_tag["xml:lang"])
        self.assertEqual("en", html_tag["lang"])
        self.assertEqual("ltr", html_tag["dir"])

    def test_vanilla_layout_head_parts(self):
        # Verify the common head parts of the vanilla layout.
        view = self._makeView()
        content = BeautifulSoup(view())
        head = content.head
        # The page's title should match the view's page_title.
        self.assertIn("Vanilla Test", head.title.string)
        # The shortcut icon for the browser chrome is provided.
        link_tag = head.find("link", rel="shortcut icon")
        self.assertEqual(["shortcut", "icon"], link_tag["rel"])
        self.assertEqual("/@@/favicon.ico?v=2022", link_tag["href"])
        # The vanilla CSS should be loaded.
        vanilla_css = head.find(
            "link", href=lambda x: x and "vanilla/styles.css" in x
        )
        self.assertIsNotNone(vanilla_css)

    def test_vanilla_layout_body_parts(self):
        # Verify the common body parts of the vanilla layout.
        view = self._makeView()
        content = BeautifulSoup(view())
        # Check for skip link.
        skip_link = content.find("a", class_="p-link--skip")
        self.assertIsNotNone(skip_link)
        self.assertEqual("#main-content", skip_link["href"])
        # Check for main content area.
        main_content = find_tag_by_id(content, "main-content")
        self.assertIsNotNone(main_content)
        # Check that the test content is present.
        self.assertIn("Vanilla Layout Test", extract_text(content))

    def test_vanilla_layout_navigation(self):
        # Verify that navigation is present in the vanilla layout.
        view = self._makeView()
        content = BeautifulSoup(view())
        # Check for navigation element
        navigation_by_id = find_tag_by_id(content, "navigation")
        self.assertIsNotNone(navigation_by_id)
        navigation_by_class = content.find(class_="p-navigation")
        self.assertIsNotNone(navigation_by_class)
        # Check for account menu control in navigation
        account_menu_control = content.find(
            attrs={"aria-controls": "account-menu"}
        )
        self.assertIsNotNone(account_menu_control)

    def test_vanilla_layout_notifications_area(self):
        # Verify that the notifications area is present.
        view = self._makeView()
        content = BeautifulSoup(view())
        notifications_div = content.find("div", id="request-notifications")
        self.assertIsNotNone(notifications_div)

    def test_vanilla_layout_page_title(self):
        # Verify that the page title is set correctly.
        view = self._makeView()
        self.assertEqual("Vanilla Test", view.page_title)
        content = BeautifulSoup(view())
        self.assertIn("Vanilla Test", content.head.title.string)


class TestVanillaBaseLayoutBrowser(BrowserTestCase):
    """Browser tests for the vanilla base layout template."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.admin_user = self.factory.makeAdministrator()

    def test_vanilla_test_page_accessible(self):
        # Verify that the vanilla test page is accessible.
        url = canonical_url(rootObject, view_name="+vanilla-test")
        browser = self.getUserBrowser(url, user=self.admin_user)
        self.assertEqual(200, browser.responseStatusCode)
        self.assertIn("Vanilla Layout Test", browser.contents)

    def test_vanilla_test_page_uses_vanilla_css(self):
        # Verify that the vanilla CSS is loaded.
        url = canonical_url(rootObject, view_name="+vanilla-test")
        browser = self.getUserBrowser(url, user=self.admin_user)
        self.assertIn("vanilla/styles.css", browser.contents)

    def test_vanilla_test_page_has_main_content(self):
        # Verify that the main content area is present.
        url = canonical_url(rootObject, view_name="+vanilla-test")
        browser = self.getUserBrowser(url, user=self.admin_user)
        self.assertIn('id="main-content"', browser.contents)
        self.assertIn("Vanilla Layout Test", browser.contents)

    def test_vanilla_test_page_notifications(self):
        # Verify that notifications can be triggered.
        url = (
            canonical_url(rootObject, view_name="+vanilla-test")
            + "?notification_type=info&notification_message=Hello"
        )
        browser = self.getUserBrowser(url, user=self.admin_user)
        self.assertIn("Hello", browser.contents)
        self.assertIn("p-notification--information", browser.contents)
