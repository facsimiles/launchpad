# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from lazr.lifecycle.interfaces import IObjectCreatedEvent

from lp.answers.interfaces.question import IQuestion
from lp.services.metrics import send_metrics
from lp.services.webapp.authorization import check_permission


def send_metrics_question_created(
    question: IQuestion, event: IObjectCreatedEvent
):
    """Create metrics to aggregate number of questions asked."""
    is_legitimate = check_permission(
        "launchpad.AnyLegitimatePerson", question.owner
    )
    send_metrics(
        "question.count",
        labels={
            "is_legitimate": is_legitimate,
        },
    )
