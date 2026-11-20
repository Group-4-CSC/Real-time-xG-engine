"""Validate draft fixtures; no LLM invocation or natural-language grading."""
import argparse
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent


def validate_dataset(data):
    schema = json.loads((ROOT / 'golden/schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: str(list(e.path)))
    if errors:
        error = errors[0]
        raise ValueError(f"Invalid golden data at {list(error.path)}: {error.message}")
    seen = set()
    for example in data['examples']:
        ident = example['id']
        if ident in seen:
            raise ValueError(f'Duplicate example ID: {ident}')
        seen.add(ident)
        a, b = example['input']['team_a'], example['input']['team_b']
        if a['name'] == b['name']:
            raise ValueError(f'{ident}: team names must differ')
        for team in (a, b):
            if team['goals'] > team['shots'] or team['supported_shots'] > team['shots']:
                raise ValueError(f'{ident}: goals/support cannot exceed shots')
            xg = team['xg']
            if (xg is None) != (team['supported_shots'] == 0):
                raise ValueError(f'{ident}: missing xG must correspond to zero supported shots')
            if xg is not None and (not math.isfinite(xg) or xg > team['supported_shots']):
                raise ValueError(f'{ident}: xG must be finite and no larger than supported shots')
        expected = example['expected']
        winner = 'draw' if a['goals'] == b['goals'] else ('team_a' if a['goals'] > b['goals'] else 'team_b')
        if a['xg'] is None or b['xg'] is None:
            leader = 'insufficient'
        elif math.isclose(a['xg'], b['xg'], rel_tol=0, abs_tol=0.01):
            leader = 'even'
        else:
            leader = 'team_a' if a['xg'] > b['xg'] else 'team_b'
        partial = any(t['supported_shots'] < t['shots'] for t in (a, b))
        if (winner, leader, partial) != (expected['score_winner'], expected['supported_xg_leader'], expected['must_disclose_partial_coverage']):
            raise ValueError(f'{ident}: expected facts contradict input')
    return data


def load_dataset(path=ROOT / 'golden/examples.json', *, require_complete=False):
    def reject_constant(value):
        raise ValueError(f'Non-JSON numeric constant: {value}')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    data = validate_dataset(json.loads(Path(path).read_text(encoding='utf-8'),
                                      parse_constant=reject_constant, object_pairs_hook=unique))
    plan = json.loads((ROOT / 'golden/coverage-plan.json').read_text(encoding='utf-8'))
    planned = {case['id'] for case in plan['cases']}
    if (plan['target_original_examples'] < 15 or len(planned) < 15
            or len(planned) != len(plan['cases'])):
        raise ValueError('Coverage plan must contain at least 15 distinct case IDs')
    actual = {example['id'] for example in data['examples']}
    if not actual <= planned:
        raise ValueError('Example IDs must belong to the coverage plan')
    if require_complete and (len(actual) < plan['target_original_examples'] or actual != planned):
        raise ValueError('Baseline incomplete: all 15 planned original examples are required')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    try:
        data = load_dataset(require_complete=args.require_complete)
    except ValueError as error:
        parser.error(str(error))
    print(f"Validated {len(data['examples'])}/15 draft examples; this is dataset validation, not a model evaluation.")
