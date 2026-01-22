# Copyright 2009-2024 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Vanilla layout test view."""

from lp.services.webapp.publisher import LaunchpadView


class VanillaTestView(LaunchpadView):
    """Test view for vanilla layout.

    This view is used for testing the vanilla base layout template.
    """

    use_vanilla_layout = True
    page_title = "Vanilla Test"

    def initialize(self):
        notification_type = self.request.form.get("notification_type")
        message = self.request.form.get(
            "notification_message", "This is a test notification."
        )
        if notification_type:
            if notification_type == "info":
                self.request.response.addInfoNotification(message)
            elif notification_type == "warning":
                self.request.response.addWarningNotification(message)
            elif notification_type == "error":
                self.request.response.addErrorNotification(message)
            elif notification_type == "debug":
                self.request.response.addDebugNotification(message)
