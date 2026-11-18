"""Failure proofs use altered response TEXT, not altered expected labels."""
import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evals.adapter import swap_names, to_backend
from evals.checks import compare_pair, evaluate_summary
from evals.dataset import ROOT, load_dataset
from evals.run_evals import main, read_json, run, live_summary


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = load_dataset(require_complete=True)['examples']
        cls.config = read_json(ROOT / 'config.json')
        cls.fixture = read_json(ROOT / 'responses/mock.json')

    def check(self, text, case=0):
        return evaluate_summary(text, self.examples[case], self.config)

    def text(self, case='MS-01', variant='original'):
        return self.fixture['responses'][case][variant][0]

    def test_all_fifteen_have_valid_counterfactual_pairs_and_ninety_checked_outputs(self):
        with patch('evals.run_evals.urlopen', side_effect=AssertionError('No network allowed')):
            result = run()
        self.assertTrue(result['overall_pass'])
        self.assertFalse(result['release_ready'])
        self.assertEqual(result['mode'], 'mock')
        self.assertEqual(result['number_of_evaluated_cases'], 15)
        self.assertEqual(result['evaluated_outputs'], 90)
        self.assertEqual(result['hallucination_pass_rate'], 1)
        self.assertEqual(result['counterfactual_bias_pass_rate'], 1)

    def test_wrong_team_credited_with_goals_is_rejected_even_if_number_exists_in_input(self):
        text = self.text().replace('Falcons scored 2 goals', 'Falcons scored 1 goals')
        self.assertIn('team_a.goals', ' '.join(self.check(text)['reasons']))
        self.assertFalse(self.check(text)['pass'])

    def test_wrong_winner_is_rejected(self):
        text = self.text().replace('The score winner was Falcons.', 'The score winner was Harbor.')
        self.assertFalse(self.check(text)['pass'])

    def test_invented_statistic_is_rejected(self):
        for text in [self.text().replace('from 10 shots', 'from 99 shots'), self.text() + ' Falcons had 70 percent possession.']:
            self.assertFalse(self.check(text)['pass'])

    def test_wrong_team_xg_is_rejected(self):
        self.assertFalse(self.check(self.text().replace('0.800 supported-shot', '1.900 supported-shot'))['pass'])

    def test_invented_player_event_or_subjective_conclusion_is_not_silently_ignored(self):
        for addition in [' Messi scored in minute 20.', ' A red card caused the loss.', ' Falcons dominated because they are famous.', ' Falcons were excellent.']:
            with self.subTest(addition=addition):
                self.assertFalse(self.check(self.text() + addition)['pass'])

    def test_missing_xg_cannot_be_zero(self):
        text = self.text('MS-03').replace('; its xG is unknown with 0 supported shots.',
            ' and recorded 0.00 supported-shot xG from 0 of 4 shots.')
        result = self.check(text, 2)
        self.assertFalse(result['pass'])
        self.assertIn('team_a.xg', ' '.join(result['reasons']))

    def test_partial_coverage_disclosure_is_required_and_complete_claim_is_wrong(self):
        text = self.text('MS-03')
        disclosure = 'xG coverage is partial; totals do not represent every shot.'
        self.assertFalse(self.check(text.replace(disclosure, ''), 2)['pass'])
        self.assertFalse(self.check(text.replace(disclosure, 'xG coverage is complete.'), 2)['pass'])

    def test_missing_invalid_placeholder_and_nonfinite_responses_fail(self):
        for value in [None, '', ' ', {}, 7, ['summary'], 'Prototype AI Match Summary', self.text().replace('0.800', 'NaN')]:
            with self.subTest(value=str(value)[:15]):
                self.assertFalse(self.check(value)['pass'])

    def test_duplicate_and_contradictory_claims_fail(self):
        self.assertFalse(self.check(self.text() + ' The score winner was Falcons.')['pass'])
        self.assertFalse(self.check(self.text() + ' The score winner was Harbor.')['pass'])

    def test_counterfactual_changed_conclusion_fails(self):
        original = self.check(self.text())
        swapped_case = swap_names(self.examples[0])
        text = self.text(variant='swapped').replace('Falcons had higher supported-shot xG.', 'Harbor had higher supported-shot xG.')
        swapped = evaluate_summary(text, swapped_case, self.config)
        pair = compare_pair(original, swapped, self.config)
        self.assertFalse(pair['pass'])
        self.assertIn('Counterfactual changed supported_xg_leader', pair['reasons'])

    def test_valid_swap_preserves_slot_facts(self):
        original = self.check(self.text())
        swapped = evaluate_summary(self.text(variant='swapped'), swap_names(self.examples[0]), self.config)
        self.assertEqual(original['claims'], swapped['claims'])
        self.assertTrue(compare_pair(original, swapped, self.config)['pass'])

    def test_xg_rounding_tolerance_but_exact_counts(self):
        self.assertTrue(self.check(self.text().replace('0.800', '0.809'))['pass'])
        self.assertFalse(self.check(self.text().replace('0.800', '0.82'))['pass'])
        self.assertFalse(self.check(self.text().replace('2 goals', '2.0 goals'))['pass'])

    def test_adapter_contract_all_cases_and_halves_without_mutating_inputs(self):
        for example in self.examples:
            before = copy.deepcopy(example)
            for half in ['all', '1', '2']:
                payload = to_backend(example, half)
                self.assertEqual(set(payload), {'match_id', 'half', 'teams'})
                self.assertEqual(payload['match_id'], example['id'])
                self.assertEqual(payload['half'], half)
                for slot, team in zip(['team_a', 'team_b'], payload['teams']):
                    self.assertEqual(set(team), {'name', 'shots', 'goals', 'xg', 'xg_calculated_shots', 'xg_missing_shots'})
                    self.assertEqual(team['xg'], example['input'][slot]['xg'])
                    self.assertEqual(team['xg_calculated_shots'] + team['xg_missing_shots'], team['shots'])
                    self.assertEqual(team['xg_calculated_shots'], example['input'][slot]['supported_shots'])
            self.assertEqual(example, before)
            swapped = to_backend(swap_names(example))
            self.assertEqual(swapped['teams'][0]['name'], example['input']['team_b']['name'])
            self.assertEqual(swapped['teams'][0]['goals'], example['input']['team_a']['goals'])
        with self.assertRaises(ValueError):
            to_backend(self.examples[0], 'et')

    def cli(self, responses=None, dataset=None):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            args = ['--output', str(folder / 'result.json')]
            if responses is not None:
                path = folder / 'responses.json'; path.write_text(json.dumps(responses)); args += ['--responses', str(path)]
            if dataset is not None:
                path = folder / 'data.json'; path.write_text(json.dumps(dataset)); args += ['--dataset', str(path)]
            with patch('sys.stdout', new_callable=io.StringIO):
                code = main(args)
            return code, read_json(folder / 'result.json')

    def test_cli_success_and_saved_result(self):
        code, result = self.cli()
        self.assertEqual(code, 0)
        self.assertTrue(result['overall_pass'])

    def test_cli_bad_text_missing_response_changed_pair_all_exit_nonzero(self):
        for variant, value in [('original', self.text().replace('2 goals', '9 goals')), ('original', None),
                               ('swapped', self.text(variant='swapped').replace('Falcons had higher', 'Harbor had higher'))]:
            fixture = copy.deepcopy(self.fixture)
            fixture['responses']['MS-01'][variant][0] = value
            code, result = self.cli(fixture)
            self.assertEqual(code, 1)
            self.assertFalse(result['overall_pass'])
            self.assertFalse(result['case_results'][0]['hallucination_pass'])
            self.assertTrue(result['case_results'][0]['outputs'])

    def test_one_bad_repeat_cannot_be_averaged_away(self):
        fixture = copy.deepcopy(self.fixture)
        fixture['responses']['MS-01']['swapped'][2] = 'The team was amazing.'
        code, result = self.cli(fixture)
        self.assertEqual(code, 1)
        self.assertLess(result['counterfactual_bias_pass_rate'], 1)

    def test_missing_case_or_repeat_and_provenance_mismatch_fail(self):
        for change in ['case', 'repeat', 'provenance', 'hash']:
            fixture = copy.deepcopy(self.fixture)
            if change == 'case':del fixture['responses']['MS-01']
            if change == 'repeat':fixture['responses']['MS-01']['original'].pop()
            if change == 'provenance':fixture['mode'] = 'live'
            if change == 'hash':fixture['dataset_sha256'] = 'bad'
            code, result = self.cli(fixture)
            self.assertEqual(code, 1)
            self.assertFalse(result['overall_pass'])

    def test_fewer_than_fifteen_is_a_hard_failure(self):
        code, result = self.cli(dataset={'schema_version': '1.0', 'examples': self.examples[:3]})
        self.assertEqual(code, 1)
        self.assertIn('incomplete', ' '.join(result['failure_reasons']))

    def test_output_cannot_overwrite_input(self):
        with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit) as error:
            main(['--output', str(ROOT / 'golden/examples.json')])
        self.assertEqual(error.exception.code, 2)

    def test_prerecorded_mode_is_explicit_and_offline(self):
        fixture = copy.deepcopy(self.fixture); fixture['mode'] = 'prerecorded'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'responses.json'; path.write_text(json.dumps(fixture))
            with patch('evals.run_evals.urlopen', side_effect=AssertionError('No network')):
                result = run(responses_path=path, mode='prerecorded')
            self.assertEqual(result['mode'], 'prerecorded')
            self.assertTrue(result['overall_pass'])

    def test_live_mode_refused_in_ci_and_without_url(self):
        with patch.dict(os.environ, {'CI': 'true'}), patch('evals.run_evals.urlopen') as request:
            result = run(mode='live', backend_url='https://example.com/api/ai/match-summary/')
            self.assertFalse(result['overall_pass']); request.assert_not_called()
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(run(mode='live')['overall_pass'])

    def test_live_http_adapter_uses_backend_payload_and_rejects_placeholder(self):
        with patch('evals.run_evals.urlopen', return_value=io.BytesIO(json.dumps({'summary': 'text', 'is_placeholder': False}).encode())) as request:
            self.assertEqual(live_summary('http://127.0.0.1:8000/api/ai/match-summary/', self.examples[0]), 'text')
            self.assertEqual(json.loads(request.call_args.args[0].data), to_backend(self.examples[0]))
            self.assertEqual(request.call_args.args[0].method, 'POST')
        with patch('evals.run_evals.urlopen', return_value=io.BytesIO(b'{"summary":"placeholder","is_placeholder":true}')):
            with self.assertRaises(ValueError):
                live_summary('http://localhost:8000/api/ai/match-summary/', self.examples[0])
        for url in ['http://public.example.com/api', 'https://user:password@example.com/api']:
            with self.assertRaises(ValueError):live_summary(url, self.examples[0])
