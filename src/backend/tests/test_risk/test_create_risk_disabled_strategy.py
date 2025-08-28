import datetime

from django.test import TestCase

from services.web.risk.handlers.risk import RiskHandler
from services.web.risk.models import Risk
from services.web.strategy_v2.constants import StrategyStatusChoices
from services.web.strategy_v2.models import Strategy


class TestCreateRiskWithStrategyStatus(TestCase):
    def setUp(self):
        # Common timestamps
        self.now_ms = int(datetime.datetime.now().timestamp() * 1000)

    def test_skip_when_strategy_disabled(self):
        # Prepare a disabled strategy
        Strategy.objects.create(strategy_id=101, status=StrategyStatusChoices.DISABLED.value)

        event = {
            "strategy_id": 101,
            "raw_event_id": "raw-001",
            "event_time": self.now_ms,
            "event_data": {},
            "event_evidence": "[]",
        }

        created, risk = RiskHandler().create_risk(event)

        self.assertFalse(created)
        self.assertIsNone(risk)
        self.assertEqual(Risk.objects.count(), 0)

    def test_create_when_strategy_running(self):
        # Prepare a running strategy
        Strategy.objects.create(strategy_id=102, status=StrategyStatusChoices.RUNNING.value)

        event = {
            "strategy_id": 102,
            "raw_event_id": "raw-002",
            "event_time": self.now_ms,
            "event_data": {},
            "event_evidence": "[]",
        }

        created, risk = RiskHandler().create_risk(event)

        self.assertTrue(created)
        self.assertIsNotNone(risk)
        self.assertEqual(Risk.objects.filter(strategy_id=102, raw_event_id="raw-002").count(), 1)

    def test_existing_risk_not_updated_when_disabled(self):
        # Strategy disabled
        strategy = Strategy.objects.create(strategy_id=103, status=StrategyStatusChoices.DISABLED.value)

        # Create an existing risk for the same strategy/raw_event_id
        existing = Risk.objects.create(
            strategy=strategy,
            raw_event_id="raw-003",
            event_time=datetime.datetime.fromtimestamp(self.now_ms / 1000),
            event_end_time=datetime.datetime.fromtimestamp(self.now_ms / 1000),
            event_data={},
            event_type=[],
        )

        later_ms = self.now_ms + 60_000
        event = {
            "strategy_id": 103,
            "raw_event_id": "raw-003",
            "event_time": later_ms,
            "event_data": {},
            "event_evidence": "[]",
        }

        created, risk = RiskHandler().create_risk(event)

        # Should skip and not touch the existing risk
        self.assertFalse(created)
        self.assertIsNone(risk)

        existing.refresh_from_db()
        self.assertEqual(int(existing.event_end_time.timestamp()), int(self.now_ms / 1000))
