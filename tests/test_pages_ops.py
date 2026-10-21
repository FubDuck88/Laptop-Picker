from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pages_ops import prepare,finish,receipt_seen,delivery_verified,schedule_overdue
from datetime import datetime


def state():
    return {'public':None,'maintenance':{'tag':'maintenance-test','archive_sha256':'a'*64},
            'publication_inhibited':True,'notification':{'issue':5,'receipt_confirmed':False},
            'active_attempt':{'run_id':'old'},'last_schedule':None}


class DeploymentGuardsTests(unittest.TestCase):
    def github(self,value):
        github=Mock();github.state.return_value=(deepcopy(value),'state-version')
        return github

    def test_cutover_requires_owner_receipt_and_daily_requires_cutover(self):
        github=self.github(state());github.api.return_value=[]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'receipt'):prepare(github,'cutover',tmp)
            with self.assertRaisesRegex(ValueError,'inhibited'):prepare(github,'daily',tmp)
            with self.assertRaisesRegex(ValueError,'Unknown'):prepare(github,'unexpected',tmp)
        github.save.assert_not_called()

    def test_receipt_is_explicit_and_from_named_owner(self):
        github=Mock()
        for login,body,expected in [('github-actions[bot]','received',False),('FubDuck88','please verify',False),('FubDuck88','received',True)]:
            github.api.return_value=[{'user':{'login':login},'body':body}]
            self.assertEqual(receipt_seen(github,state()),expected)

    def test_notification_alone_cannot_unlock_cutover_without_recovery_proof(self):
        value=state();value['notification']['receipt_confirmed']=True
        github=self.github(value)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'recovery drill'):prepare(github,'cutover',tmp)
        github.save.assert_not_called()

    def test_verified_recipient_delivery_is_distinct_from_issue_creation(self):
        value=state()
        self.assertFalse(delivery_verified(value))
        proof={'recipient':'FubDuck88','issue':5,'method':'authenticated_repository_notifications_api',
               'evidence_sha256':'a'*64}
        value['notification']['delivery_verified']=proof
        self.assertTrue(delivery_verified(value))
        proof['recipient']='someone-else'
        self.assertFalse(delivery_verified(value))

    def test_stale_completion_and_recovery_cannot_overwrite_current_state(self):
        github=self.github(state())
        with patch.dict(os.environ,{'GITHUB_RUN_ID':'new','OP_MODE':'drill'}):
            with self.assertRaisesRegex(ValueError,'Stale'):finish(github,'.','verified')
            with self.assertRaisesRegex(ValueError,'Stale'):prepare(github,'recover','.',expected_run='older')
        github.save.assert_not_called()

    def test_drill_is_not_a_public_release_or_scheduled_success(self):
        value=state();value['active_attempt']['run_id']='new'
        github=self.github(value)
        with patch.dict(os.environ,{'GITHUB_RUN_ID':'new','OP_MODE':'drill'}):finish(github,'.','drill-restored')
        saved=github.save.call_args.args[0]
        self.assertIsNone(saved['public']);self.assertIsNone(saved['last_schedule'])
        self.assertTrue(saved['publication_inhibited'])
        self.assertTrue(saved['recovery_drill']['passed'])

    def test_unproven_recovery_keeps_guard_for_automatic_recovery_workflow(self):
        value=state();value['active_attempt']['run_id']='new'
        github=self.github(value)
        with patch.dict(os.environ,{'GITHUB_RUN_ID':'new','OP_MODE':'drill'}):finish(github,'.','recovery-unproven')
        self.assertEqual(github.save.call_args.args[0]['active_attempt']['run_id'],'new')

    def test_only_actual_schedule_event_creates_scheduled_proof(self):
        for event in ['workflow_dispatch','schedule']:
            value=state();value['active_attempt']['run_id']='new'
            github=self.github(value)
            with tempfile.TemporaryDirectory() as tmp:
                Path(tmp,'public-pin.json').write_text(json.dumps({'release_sha256':'b'*64}))
                with patch.dict(os.environ,{'GITHUB_RUN_ID':'new','OP_MODE':'daily','GITHUB_EVENT_NAME':event}):
                    finish(github,tmp,'verified')
            saved=github.save.call_args.args[0]
            self.assertEqual(saved['last_schedule'] is not None,event=='schedule')

    def test_watchdog_waits_for_first_actual_due_date_and_grace_period(self):
        value=state();value['public']={'release_sha256':'b'*64}
        value['cutover_at']='2026-10-21T12:00:00+00:00'
        self.assertFalse(schedule_overdue(value,as_of=datetime.fromisoformat('2026-10-21T13:00:00+00:00')))
        self.assertFalse(schedule_overdue(value,as_of=datetime.fromisoformat('2026-10-22T01:36:00+00:00')))
        self.assertTrue(schedule_overdue(value,as_of=datetime.fromisoformat('2026-10-22T01:37:00+00:00')))
        value['last_schedule']={'passed':True,'recorded_at':'2026-10-22T00:10:00+00:00'}
        self.assertFalse(schedule_overdue(value,as_of=datetime.fromisoformat('2026-10-22T01:37:00+00:00')))

    def test_controlled_timeout_recovery_preserves_pretest_schedule_state(self):
        value=state();value['public']={'release_sha256':'b'*64};value['publication_inhibited']=False
        value['active_attempt']={'run_id':'old','mode':'timeout-drill','prior_publication_inhibited':False}
        github=self.github(value)
        with patch.dict(os.environ,{'GITHUB_RUN_ID':'recovery','OP_MODE':'recover','RECOVER_RUN':'old'}):
            finish(github,'.','recovered')
        saved=github.save.call_args.args[0]
        self.assertFalse(saved['publication_inhibited'])
        self.assertTrue(saved['timeout_recovery_drill']['passed'])
