from datetime import datetime, timezone
import unittest

from validation_runs import local_validation_status


def receipt(day, *, healthy=True, code='current', hour='00', environment='local'):
    return {'receipt_version':1,'recorded_at':f'2026-10-{day:02}T{hour}:30:00Z','healthy':healthy,
            'implementation_sha256':code,'environment':environment}


class ValidationRunTests(unittest.TestCase):
    def test_same_day_reruns_are_one_day_and_seven_actual_days_pass(self):
        now = datetime(2026,10,20,12,tzinfo=timezone.utc)
        one = local_validation_status([receipt(20),receipt(20,hour='01')],'current',as_of=now)
        self.assertEqual(one['consecutive_healthy_days'],1)
        self.assertFalse(one['local_seven_day_gate_passed'])
        seven = local_validation_status([receipt(d) for d in range(14,21)],'current',as_of=now)
        self.assertTrue(seven['local_seven_day_gate_passed'])
        self.assertEqual(seven['hosted_operation'],'not_assessed_by_local_runner')

    def test_gaps_failures_old_code_and_old_results_do_not_pass(self):
        now = datetime(2026,10,20,12,tzinfo=timezone.utc)
        values = [receipt(d) for d in range(14,21)]
        values.append(receipt(20,healthy=False,hour='01'))
        self.assertEqual(local_validation_status(values,'current',as_of=now)['consecutive_healthy_days'],0)
        values = [receipt(18),receipt(20),receipt(19,code='old')]
        self.assertEqual(local_validation_status(values,'current',as_of=now)['consecutive_healthy_days'],1)
        self.assertEqual(local_validation_status([receipt(17)],'current',as_of=now)['consecutive_healthy_days'],0)

    def test_malaysia_day_rollover_future_receipts_and_hosted_runs(self):
        now = datetime(2026,10,21,0,tzinfo=timezone.utc)
        values = [receipt(20,hour='15'),receipt(20,hour='16'),receipt(21,hour='23'),receipt(19,environment='github-actions')]
        status = local_validation_status(values,'current',as_of=now)
        self.assertEqual(status['consecutive_healthy_days'],2)
        self.assertEqual(status['invalid_receipts'],1)
        self.assertFalse(status['local_seven_day_gate_passed'])
