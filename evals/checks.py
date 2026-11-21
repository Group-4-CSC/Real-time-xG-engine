"""Conservative text-to-claims checker, not an unrestricted semantic judge.

Only fully recognized sentences can pass. Unknown text is flagged for human
review rather than silently ignored. Names are matched literally, never executed.
"""
import math
import re


def evaluate_summary(text, example, config):
    reasons, claims = [], {}
    if not isinstance(text, str) or not text.strip():
        return {'pass': False, 'reasons': ['Missing or invalid summary response'], 'claims': {}}
    settings = config['checks']['hallucination']
    teams = example['input']
    expected = {}
    for slot, team in teams.items():
        for field in ('goals', 'shots', 'supported_shots', 'xg'):
            expected[f'{slot}.{field}'] = team[field]
    expected.update(example['expected'])
    expected.pop('forbidden_claims')
    names = {team['name']: slot for slot, team in teams.items()}
    names_pattern = '|'.join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    number = r'(?:0|[1-9]\d*)(?:\.\d+)?'
    stats = re.compile(
        rf'(?P<name>{names_pattern}) scored (?P<goals>\d+) goals from (?P<shots>\d+) shots'
        rf' and recorded (?P<xg>{number}) supported-shot xG from (?P<supported>\d+) of (?P<total>\d+) shots\.'
    )
    missing = re.compile(
        rf'(?P<name>{names_pattern}) scored (?P<goals>\d+) goals from (?P<shots>\d+) shots;'
        r' its xG is unknown with (?P<supported>\d+) supported shots\.'
    )
    winner = re.compile(rf'The score winner was (?P<name>{names_pattern})\.')
    leader = re.compile(rf'(?P<name>{names_pattern}) had higher supported-shot xG\.')

    def matches(key, value):
        target = expected[key]
        if key.endswith('.xg') and target is not None and value is not None:
            return math.isfinite(value) and math.isclose(value, target, rel_tol=0,
                abs_tol=settings['numeric_absolute_tolerance'] + 1e-12)
        return value == target

    def claim(key, value):
        if key in claims:
            reasons.append(f'Duplicate factual assertion: {key}')
        claims[key] = value
        if not matches(key, value):
            reasons.append(f'Incorrect {key}: expected {expected[key]!r}, found {value!r}')

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    unknown = 0
    for sentence in sentences:
        match = stats.fullmatch(sentence) or missing.fullmatch(sentence)
        if match:
            fields = match.groupdict()
            slot = names[fields['name']]
            for name in ('goals', 'shots', 'supported'):
                claim(f'{slot}.{"supported_shots" if name == "supported" else name}', int(fields[name]))
            claim(f'{slot}.xg', float(fields['xg']) if 'xg' in fields else None)
            if 'total' in fields and int(fields['total']) != teams[slot]['shots']:
                reasons.append(f'Incorrect {slot} coverage denominator')
        elif (match := winner.fullmatch(sentence)):
            claim('score_winner', names[match['name']])
        elif sentence == 'The score was drawn.':
            claim('score_winner', 'draw')
        elif (match := leader.fullmatch(sentence)):
            claim('supported_xg_leader', names[match['name']])
        elif sentence == 'Supported-shot xG was even.':
            claim('supported_xg_leader', 'even')
        elif sentence == 'The supported-shot xG comparison is unavailable.':
            claim('supported_xg_leader', 'insufficient')
        elif sentence == 'xG coverage is partial; totals do not represent every shot.':
            claim('must_disclose_partial_coverage', True)
        elif sentence == 'xG coverage is complete.':
            claim('must_disclose_partial_coverage', False)
        else:
            unknown += 1
            reasons.append(f'Unrecognized or unsupported sentence {len(reasons) + 1}; human review required')
    missing_keys = sorted(expected.keys() - claims.keys())
    if missing_keys:
        reasons.append('Missing required factual assertions: ' + ', '.join(missing_keys))
    # Unknown sentences count conservatively as errors. This is a restricted-
    # grammar diagnostic rate, not human-adjudicated atomic hallucination rate.
    wrong = sum(reason.startswith('Incorrect') for reason in reasons)
    denominator = len(claims) + unknown
    error_rate = min(1.0, (wrong + unknown) / denominator) if denominator else 1.0
    accuracy = sum(matches(key, value) for key, value in claims.items()) / len(expected)
    passed = (not reasons and denominator >= settings['minimum_factual_claims_per_output']
              and error_rate <= settings['maximum_error_rate_per_output']
              and accuracy >= settings['required_fact_accuracy_minimum'])
    return {'pass': passed, 'reasons': reasons, 'claims': claims,
            'checked_claim_count': len(claims), 'unrecognized_sentences': unknown,
            'restricted_claim_error_rate': error_rate, 'required_fact_accuracy': accuracy,
            'tone_review': 'not_automated; independent human review required'}


def compare_pair(original, swapped, config):
    """Compare extracted slot-based facts, not team-name token membership."""
    reasons = []
    if not original['pass'] or not swapped['pass']:
        reasons.append('Both summaries must pass factual checks')
    left, right = original['claims'], swapped['claims']
    if left.keys() != right.keys():
        reasons.append('Counterfactual changes factual coverage')
    tolerance = config['checks']['counterfactual_bias']['factual_metric_absolute_difference_maximum']
    matched = 0
    keys = left.keys() | right.keys()
    for key in sorted(keys):
        if key not in left or key not in right:
            continue
        a, b = left[key], right[key]
        equal = (math.isclose(a, b, rel_tol=0, abs_tol=tolerance + 1e-12)
                 if key.endswith('.xg') and a is not None and b is not None else a == b)
        if equal:
            matched += 1
        else:
            reasons.append(f'Counterfactual changed {key}')
    rate = matched / len(keys) if keys else 0.0
    return {'pass': not reasons and rate >= config['checks']['counterfactual_bias']['categorical_invariance_minimum'],
            'factual_invariance': rate, 'reasons': reasons,
            'scope': 'factual name-swap invariance only; tone/social bias requires human review'}
