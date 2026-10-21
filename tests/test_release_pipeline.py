"""Failure recovery, truthful history, freshness, and atomic activation."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from catalog_v2 import SourceResult
from release_pipeline import (activate_release, build_release, collection_lock, freshness, load_release,
                              publish_release, validate_release)
from test_catalog_v2 import record, source


def result(day=20, *, source_id='test_store', price='3999.00', rows=1):
    values = []
    for i in range(rows):
        value = record()
        value['offer'].update(observed_at=f'2026-10-{day:02}T00:15:00Z', price_myr=price, variant_id=str(i))
        for group in ('configuration', 'offer'):
            for proof in value[group]['evidence'].values():
                proof['observed_at'] = value['offer']['observed_at']
        value['offer']['evidence']['price']['raw_value'] = price
        values.append(value)
    return source(values, source_id=source_id, started_at=f'2026-10-{day:02}T00:00:00Z', finished_at=f'2026-10-{day:02}T00:30:00Z')


def release(day=20, previous=None, results=None):
    return build_release([result(day)] if results is None else results, previous,
                         generated_at=f'2026-10-{day:02}T00:31:00Z')[0]


class ReleasePipelineTests(unittest.TestCase):
    def test_price_changes_append_actual_history_and_replays_do_not_duplicate(self):
        first = release()
        second = release(21, first, [result(21, price='3799.00')])
        replay = release(21, second, [result(21, price='3799.00')])
        self.assertEqual(len(replay['history']['receipts']), 2)
        self.assertEqual(replay['catalog']['offers'][0]['price_sen'], 379900)
        self.assertEqual(first['catalog']['offers'][0]['id'], replay['catalog']['offers'][0]['id'])
        self.assertEqual({r['observation']['observed_at'] for r in replay['history']['receipts']}, {'2026-10-20T00:15:00Z', '2026-10-21T00:15:00Z'})
        validate_release(replay)

    def test_failed_partial_empty_and_deferred_sources_retain_good_data(self):
        first = release()
        failures = [SourceResult('test_store', state, error='Offline', started_at='2026-10-23T00:00:00Z', finished_at='2026-10-23T00:30:00Z') for state in ('failed', 'partial')]
        failures += [result(23, rows=0), SourceResult('test_store', 'not_run', mode='deferred', error='Not qualified')]
        for failure in failures:
            with self.subTest(state=failure.status):
                saved = release(23, first, [failure])
                self.assertEqual(saved['catalog']['offers'], first['catalog']['offers'])
                self.assertEqual(saved['history']['receipts'], first['history']['receipts'])
                self.assertEqual(saved['source_decisions'][0]['state'], 'retained')
                self.assertEqual(saved['attempts'][0]['status'], failure.status)
                self.assertEqual(next(iter(saved['freshness'].values()))['state'], 'stale')

    def test_partial_failure_does_not_block_a_different_successful_source(self):
        first = release(results=[result(source_id='a'), result(source_id='b')])
        failure = SourceResult('a', 'failed', error='Offline', started_at='2026-10-21T00:00:00Z', finished_at='2026-10-21T00:30:00Z')
        saved = release(21, first, [failure, result(21, source_id='b', price='3500.00')])
        offers = {o['source_id']: o for o in saved['catalog']['offers']}
        self.assertEqual(offers['a']['observed_at'], '2026-10-20T00:15:00Z')
        self.assertEqual(offers['b']['price_sen'], 350000)
        self.assertEqual(len(saved['history']['receipts']), 3)

    def test_sudden_count_drop_and_older_observations_do_not_replace_source(self):
        first = release(results=[result(rows=3)])
        dropped = release(21, first, [result(21, rows=1)])
        self.assertEqual(len(dropped['catalog']['offers']), 3)
        newer = release(22)
        backwards = release(23, newer, [result(21)])
        self.assertEqual(backwards['catalog']['offers'], newer['catalog']['offers'])

    def test_changed_hardware_does_not_move_the_old_price_to_a_new_configuration(self):
        first = release()
        updated = result(21)
        updated.records[0]['configuration']['memory'] = {'capacity_gb': 32, 'label': '32GB DDR5'}
        updated.records[0]['configuration']['evidence']['memory']['raw_value'] = '32GB DDR5'
        second = release(21, first, [updated])
        self.assertEqual(len(second['history']['configurations']), 2)
        self.assertNotEqual(first['catalog']['offers'][0]['id'], second['catalog']['offers'][0]['id'])

    def test_freshness_boundaries_and_history_retention_do_not_fabricate_observations(self):
        offer = {'observed_at': '2026-10-20T00:00:00Z'}
        self.assertEqual(freshness(offer, '2026-10-21T23:59:59Z')['state'], 'fresh')
        self.assertEqual(freshness(offer, '2026-10-22T00:00:00Z')['state'], 'stale')
        self.assertFalse(freshness(offer, '2026-10-27T00:00:00Z')['show_by_default'])
        first = release()
        expired = build_release([], first, generated_at='2027-02-01T00:00:00Z')[0]
        self.assertEqual(expired['history']['receipts'], [])
        self.assertEqual(expired['catalog']['offers'], first['catalog']['offers'])
        self.assertFalse(next(iter(expired['freshness'].values()))['show_by_default'])

    def test_corrupt_history_or_freshness_cannot_publish(self):
        first = release()
        for change in ('price', 'freshness', 'outside_run'):
            bad = deepcopy(first)
            if change == 'price': bad['history']['receipts'][0]['observation']['price_sen'] += 1
            if change == 'freshness': next(iter(bad['freshness'].values()))['state'] = 'stale'
            if change == 'outside_run': bad['history']['receipts'][0]['observation']['observed_at'] = '2026-10-19T00:00:00Z'
            with self.subTest(change=change), self.assertRaises((ValueError, KeyError)):
                validate_release(bad)

    def test_atomic_pointer_failure_leaves_last_good_release_active(self):
        with tempfile.TemporaryDirectory() as directory:
            first = release()
            publish_release(first, directory)
            pointer = (Path(directory) / 'current.json').read_bytes()
            import os
            replace = os.replace
            def fail_pointer(source_path, destination):
                if Path(destination).name == 'current.json':
                    raise OSError('Simulated interruption')
                return replace(source_path, destination)
            with patch('release_pipeline.os.replace', side_effect=fail_pointer), self.assertRaises(OSError):
                publish_release(release(21, first), directory)
            self.assertEqual((Path(directory) / 'current.json').read_bytes(), pointer)
            self.assertEqual(load_release(directory), first)

    def test_size_gate_and_missing_history_receipts_preserve_the_active_release(self):
        with tempfile.TemporaryDirectory() as directory:
            first = release()
            publish_release(first, directory)
            with patch('release_pipeline.MAX_RELEASE_BYTES', 1), self.assertRaises(ValueError):
                publish_release(release(21, first), directory)
            self.assertEqual(load_release(directory), first)
        broken = deepcopy(first)
        broken['history'] = {'configurations': {}, 'runs': {}, 'receipts': []}
        with self.assertRaises(ValueError): validate_release(broken)

    def test_lock_refuses_overlap_without_deleting_another_runs_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            with collection_lock(directory):
                with self.assertRaises(FileExistsError):
                    with collection_lock(directory):
                        self.fail('Concurrent collection was allowed')
                self.assertTrue((Path(directory) / '.collection.lock').exists())
            self.assertFalse((Path(directory) / '.collection.lock').exists())

    def test_cold_start_failure_and_tampered_pointer_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            failed = release(results=[SourceResult('test_store', 'failed', error='Offline', started_at='2026-10-20T00:00:00Z', finished_at='2026-10-20T00:30:00Z')])
            with self.assertRaises(ValueError): publish_release(failed, directory)
            self.assertFalse((Path(directory) / 'current.json').exists())
            pointer = publish_release(release(), directory)
            (Path(directory) / pointer['path']).write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError): load_release(directory)

    def test_previous_release_is_retained_and_rollback_preserves_observation_times(self):
        with tempfile.TemporaryDirectory() as directory:
            first = release()
            publish_release(first, directory)
            second = release(21, first)
            retained = publish_release(second, directory)
            third = release(22, second)
            publish_release(third, directory)
            self.assertEqual(len(list((Path(directory) / 'releases').glob('*.json'))), 2)
            activate_release(directory, retained['path'])
            self.assertEqual(load_release(directory), second)
            self.assertEqual(load_release(directory)['catalog']['offers'][0]['observed_at'], '2026-10-21T00:15:00Z')
            with self.assertRaises(ValueError): activate_release(directory, '../outside.json')

    def test_daily_command_returns_failure_but_preserves_and_reports_good_data(self):
        from tools.run_daily import main
        with tempfile.TemporaryDirectory() as directory:
            args = ['--data-dir', directory, '--diagnostics-dir', str(Path(directory) / 'diagnostics')]
            with patch('tools.run_daily.collect_sources', return_value=[result(source_id='allit')]):
                self.assertEqual(main(args), 0)
            first = load_release(directory)
            failure = SourceResult('allit', 'failed', error='Offline', started_at='2026-10-20T00:00:00Z', finished_at='2026-10-20T00:30:00Z')
            with patch('tools.run_daily.collect_sources', return_value=[failure]):
                self.assertEqual(main(args), 1)
            self.assertEqual(load_release(directory)['catalog']['offers'], first['catalog']['offers'])
            self.assertTrue((Path(directory) / 'diagnostics/run.json').exists())


if __name__ == '__main__':
    unittest.main()
