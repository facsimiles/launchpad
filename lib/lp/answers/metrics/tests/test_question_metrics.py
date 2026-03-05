from lp.services.statsd.tests import StatsMixin
from lp.testing import TestCaseWithFactory
from lp.testing.layers import DatabaseFunctionalLayer


class TestQuestionStats(TestCaseWithFactory, StatsMixin):
    """Tests that metrics are sent when a question is asked."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.setUpStats()

    def test_question_count_metric_owner_legitimate(self):
        # When a new question is asked, a metric should be sent to statsd with
        # the "question.count" name and label with the is_legitimate boolean
        self.pushConfig(
            "launchpad", min_legitimate_karma=5, min_legitimate_account_age=5
        )
        # Karma set to 1000 to make them legitimate
        legitimate_user = self.factory.makePerson(karma=1000)
        self.factory.makeQuestion(owner=legitimate_user)
        # Check that question.count metric was called
        question_calls = [
            call
            for call in self.stats_client.incr.call_args_list
            if "question.count" in str(call)
        ]
        # Assert that question.count was called once and that the user was
        # legitimate
        self.assertEqual(1, len(question_calls))
        self.assertEqual(
            (("question.count,env=test,is_legitimate=True",)),
            question_calls[0][0],
        )

    def test_question_count_metric_owner_illegitimate(self):
        # When a new question is asked, a metric should be sent to statsd with
        # the "question.count" name and label with the is_legitimate boolean
        self.pushConfig(
            "launchpad", min_legitimate_karma=5, min_legitimate_account_age=5
        )
        # Karma set to 0 to make them illegitimate
        illegitimate_user = self.factory.makePerson(karma=0)
        self.factory.makeQuestion(owner=illegitimate_user)
        # Check that question.count metric was called
        question_calls = [
            call
            for call in self.stats_client.incr.call_args_list
            if "question.count" in str(call)
        ]

        # Assert that question.count was called once and that the user was
        # illegitimate
        self.assertEqual(1, len(question_calls))
        self.assertEqual(
            (("question.count,env=test,is_legitimate=False",)),
            question_calls[0][0],
        )
