from datetime import datetime,timedelta,timezone
from pathlib import Path
import tempfile
import unittest
from validation_runs import new_gate,scoped_validation_status,implementation_digest

SHA='a'*64
START=datetime(2026,10,21,tzinfo=timezone.utc)


def receipt(gate,day):
    time=START+timedelta(days=day,hours=1)
    return {'receipt_version':2,**{k:gate[k] for k in ['gate_id','phase','environment','implementation_sha256']},
            'started_at':time.isoformat(),'recorded_at':(time+timedelta(minutes=1)).isoformat(),'healthy':True}


class GateIsolationTests(unittest.TestCase):
    def test_old_day_one_and_operational_receipts_cannot_count_for_7f(self):
        gate=new_gate('7F',SHA,'local',as_of=START)
        old=receipt(gate,0);old.pop('gate_id');old['receipt_version']=1
        six=new_gate('6R',SHA,'local',as_of=START)
        other=new_gate('7F',SHA,'local',as_of=START)
        status=scoped_validation_status(gate,[old,receipt(six,0),receipt(other,0)],SHA,as_of=START+timedelta(days=1))
        self.assertEqual(status['accepted_receipts'],0)
        self.assertEqual(status['consecutive_healthy_days'],0)
        self.assertFalse(status['validation_window_passed'])

    def test_seven_real_distinct_dates_and_only_matching_gate_can_pass(self):
        gate=new_gate('7F',SHA,'local',as_of=START)
        values=[receipt(gate,i) for i in range(7)]
        values.append(receipt(gate,6))
        status=scoped_validation_status(gate,values,SHA,as_of=START+timedelta(days=6,hours=5))
        self.assertEqual(status['consecutive_healthy_days'],7)
        self.assertTrue(status['validation_window_passed'])
        changed=scoped_validation_status(gate,values,'b'*64,as_of=START+timedelta(days=7))
        self.assertTrue(changed['reset_required']);self.assertFalse(changed['validation_window_passed'])

    def test_prestart_and_other_environment_receipts_are_excluded(self):
        gate=new_gate('7F',SHA,'local',as_of=START)
        before=receipt(gate,0);before['started_at']=(START-timedelta(seconds=1)).isoformat()
        hosted=receipt(gate,0);hosted['environment']='github-actions'
        status=scoped_validation_status(gate,[before,hosted],SHA,as_of=START+timedelta(days=1))
        self.assertEqual(status['accepted_receipts'],0)

    def test_invalid_current_receipt_cannot_hide_behind_seven_good_days(self):
        gate=new_gate('7F',SHA,'local',as_of=START)
        values=[receipt(gate,i) for i in range(7)]
        broken=receipt(gate,6);broken['recorded_at']='invalid'
        status=scoped_validation_status(gate,[*values,broken],SHA,as_of=START+timedelta(days=7))
        self.assertFalse(status['validation_window_passed'])
        self.assertEqual(status['invalid_current_receipts'],1)

    def test_operational_receipts_never_satisfy_a_release_window(self):
        gate=new_gate('6R',SHA,'local',as_of=START)
        status=scoped_validation_status(gate,[receipt(gate,i) for i in range(8)],SHA,as_of=START+timedelta(days=8))
        self.assertEqual(status['accepted_receipts'],8)
        self.assertFalse(status['validation_window_passed']);self.assertEqual(status['consecutive_healthy_days'],0)

    def test_fingerprint_covers_nested_fixtures_and_launcher_but_not_live_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'tests/fixtures/releases').mkdir(parents=True);(root/'data').mkdir()
            fixture=root/'tests/fixtures/releases/frozen.json';fixture.write_bytes(b'first')
            (root/'ScrapeLaptops.bat').write_bytes(b'python runner.py\r\n')
            first=implementation_digest(root)
            (root/'data/current.json').write_bytes(b'observation')
            self.assertEqual(first,implementation_digest(root))
            fixture.write_bytes(b'second')
            second=implementation_digest(root);self.assertNotEqual(first,second)
            (root/'ScrapeLaptops.bat').write_bytes(b'python changed.py\r\n')
            self.assertNotEqual(second,implementation_digest(root))
