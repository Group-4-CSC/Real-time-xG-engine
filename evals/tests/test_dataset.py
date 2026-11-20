import copy
import json
import tempfile
import unittest
from pathlib import Path

from evals.dataset import ROOT, load_dataset, validate_dataset


class GoldenDatasetTests(unittest.TestCase):
    def setUp(self):
        self.data = load_dataset()

    def test_complete_golden_set_loads(self):
        self.assertEqual(len(self.data['examples']), 15)
        self.assertEqual(self.data['examples'][2]['expected']['supported_xg_leader'], 'insufficient')

    def test_coverage_plan_has_fifteen_populated_slots(self):
        plan = json.loads((ROOT / 'golden/coverage-plan.json').read_text())
        self.assertEqual(plan['target_original_examples'], 15)
        self.assertEqual(len({c['id'] for c in plan['cases']}), 15)
        self.assertEqual(sum(c['status'] == 'populated_pending_jason_review' for c in plan['cases']), 15)
        self.assertEqual(len(load_dataset(require_complete=True)['examples']), 15)

    def test_missing_field_and_unknown_field_are_rejected(self):
        for mode in ('missing', 'extra'):
            data = copy.deepcopy(self.data)
            team = data['examples'][0]['input']['team_a']
            if mode == 'missing':
                del team['goals']
            else:
                team['possession'] = 90
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_dataset(data)

    def test_invalid_numbers_and_counts_are_rejected(self):
        for field, value in [('goals', -1), ('shots', True), ('supported_shots', 99), ('xg', float('inf')), ('xg', -1), ('xg', 11)]:
            data = copy.deepcopy(self.data)
            data['examples'][0]['input']['team_a'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_dataset(data)

    def test_duplicate_ids_and_team_names_are_rejected(self):
        data = copy.deepcopy(self.data)
        data['examples'].append(copy.deepcopy(data['examples'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_dataset(data)
        data = copy.deepcopy(self.data)
        data['examples'][0]['input']['team_b']['name'] = 'Falcons'
        with self.assertRaisesRegex(ValueError, 'names must differ'):
            validate_dataset(data)

    def test_contradictory_expected_facts_are_rejected(self):
        for field, value in [('score_winner', 'team_b'), ('supported_xg_leader', 'team_a'), ('must_disclose_partial_coverage', True)]:
            data = copy.deepcopy(self.data)
            data['examples'][0]['expected'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'contradict'):
                validate_dataset(data)

    def test_missing_xg_is_not_numeric_zero(self):
        data = copy.deepcopy(self.data)
        data['examples'][2]['input']['team_a']['xg'] = 0
        with self.assertRaisesRegex(ValueError, 'missing xG'):
            validate_dataset(data)

    def test_file_loader_rejects_malformed_json_and_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.json'
            for text in ['{', json.dumps(self.data).replace('0.8', 'NaN', 1)]:
                path.write_text(text)
                with self.subTest(text=text[:10]), self.assertRaises(ValueError):
                    load_dataset(path)

    def test_counterfactual_preserves_metrics_and_gold_slots(self):
        for example in self.data['examples']:
            swapped = copy.deepcopy(example)
            a, b = swapped['input']['team_a'], swapped['input']['team_b']
            a['name'], b['name'] = b['name'], a['name']
            # Fixture validation only; this does not claim generated-text fairness.
            validate_dataset({'schema_version': '1.0', 'examples': [swapped]})
            for slot in ['team_a', 'team_b']:
                for field in ['goals', 'shots', 'supported_shots', 'xg']:
                    self.assertEqual(swapped['input'][slot][field], example['input'][slot][field])
