"""Run actual summary-text checks offline by default; never call an LLM in CI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from evals.adapter import swap_names, to_backend
from evals.checks import compare_pair, evaluate_summary
from evals.dataset import ROOT, load_dataset


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def reject(value):
        raise ValueError(f'Invalid numeric constant: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique, parse_constant=reject)


def live_summary(url, example):
    """Use PR #58's HTTP contract; credentials, if any, stay in environment."""
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Backend URL cannot contain credentials, query, or fragment')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ValueError('Live mode requires HTTPS, or HTTP on loopback')
    request = Request(url, data=json.dumps(to_backend(example)).encode(),
                      headers={'Content-Type': 'application/json'}, method='POST')
    # No API/provider secret is copied into fixtures, logs, or result metadata.
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get('is_placeholder') is not False:
        raise ValueError('Backend returned a placeholder or missing contract flag')
    return payload.get('summary')


def run(dataset_path=ROOT / 'golden/examples.json', responses_path=ROOT / 'responses/mock.json',
        mode='mock', backend_url=None):
    config = read_json(ROOT / 'config.json')
    result = {
        'dataset_version': '1.0', 'dataset_sha256': None, 'mode': mode,
        'config_version': config['version'],
        'config_sha256': hashlib.sha256((ROOT / 'config.json').read_bytes()).hexdigest(),
        'checker_version': 'restricted-facts-v1',
        'number_of_evaluated_cases': 0, 'evaluated_outputs': 0,
        'hallucination_pass_rate': 0.0, 'counterfactual_bias_pass_rate': 0.0,
        'required_thresholds': config['checks'], 'case_results': [],
        'overall_pass': False, 'release_ready': False,
        'human_review_status': 'pending; Jason fixture review and independent tone review required',
        'scope': 'Restricted-language factual checks and name-swap invariance only; not proof of arbitrary-language factuality or absence of social bias',
        'failure_reasons': [],
    }
    try:
        dataset = load_dataset(dataset_path, require_complete=True)
        result['dataset_version'] = dataset['schema_version']
        result['dataset_sha256'] = hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest()
        examples = dataset['examples']
        minimum = max(15, config['minimum_reviewed_examples_for_baseline'])
        if len(examples) < minimum:
            raise ValueError(f'At least {minimum} original golden examples required')
        repeats = config['generation']['repeats_per_variant']
        if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats < 1:
            raise ValueError('Invalid repeat count')
        if mode == 'live':
            if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
                raise ValueError('Live mode is forbidden in CI')
            if not backend_url:
                raise ValueError('Live mode requires --backend-url for the PR #58 POST endpoint')
            result['provenance'] = 'Explicit live backend HTTP requests; backend model/version must be recorded separately'
        else:
            if mode not in ('mock', 'prerecorded'):
                raise ValueError('Unsupported response mode')
            fixture = read_json(responses_path)
            if fixture.get('mode') != mode:
                raise ValueError('Response provenance does not match selected mode')
            if fixture.get('dataset_sha256') != result['dataset_sha256']:
                raise ValueError('Response snapshot dataset hash mismatch; re-record against current data')
            result['provenance'] = fixture.get('provenance', 'User supplied response snapshot')
            result['response_sha256'] = hashlib.sha256(Path(responses_path).read_bytes()).hexdigest()
            responses = fixture['responses']
            if set(responses) != {example['id'] for example in examples}:
                raise ValueError('Response snapshot must contain exactly all golden case IDs')
        for example in examples:
            case = {'id': example['id'], 'outputs': [], 'pairs': []}
            for repeat in range(repeats):
                checked = []
                for variant, facts in (('original', example), ('swapped', swap_names(example))):
                    try:
                        if mode == 'live':
                            text = live_summary(backend_url, facts)
                        else:
                            variants = responses[example['id']]
                            if not isinstance(variants, dict) or set(variants) != {'original', 'swapped'}:
                                raise ValueError('Both original and swapped response arrays required')
                            values = variants[variant]
                            if not isinstance(values, list) or len(values) != repeats:
                                raise ValueError(f'Exactly {repeats} responses required per variant')
                            text = values[repeat]
                        check = evaluate_summary(text, facts, config)
                    except Exception as error:
                        # Never include transport exception text: URLs can contain secrets.
                        reason = str(error) if mode != 'live' and isinstance(error, ValueError) else type(error).__name__
                        check = {'pass': False, 'claims': {}, 'reasons': [f'Response unavailable/invalid: {reason}']}
                    checked.append(check)
                    case['outputs'].append({'variant': variant, 'repeat': repeat + 1, **check})
                case['pairs'].append({'repeat': repeat + 1, **compare_pair(*checked, config)})
            case['hallucination_pass'] = all(o['pass'] for o in case['outputs'])
            case['counterfactual_bias_pass'] = all(p['pass'] for p in case['pairs'])
            result['case_results'].append(case)
        result['number_of_evaluated_cases'] = len(examples)
        result['evaluated_outputs'] = sum(len(c['outputs']) for c in result['case_results'])
        result['hallucination_pass_rate'] = sum(c['hallucination_pass'] for c in result['case_results']) / len(examples)
        result['counterfactual_bias_pass_rate'] = sum(c['counterfactual_bias_pass'] for c in result['case_results']) / len(examples)
        result['overall_pass'] = (result['hallucination_pass_rate'] == 1.0 and result['counterfactual_bias_pass_rate'] == 1.0)
        if not result['overall_pass']:
            result['failure_reasons'].append('One or more cases failed factual or counterfactual checks; inspect case_results')
    except (ValueError, OSError, KeyError, TypeError) as error:
        result['failure_reasons'].append(str(error))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'golden/examples.json')
    parser.add_argument('--responses', type=Path, default=ROOT / 'responses/mock.json')
    parser.add_argument('--mode', choices=['mock', 'prerecorded', 'live'], default='mock')
    parser.add_argument('--backend-url')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/latest.json')
    args = parser.parse_args(argv)
    protected = [args.dataset, args.responses, ROOT / 'config.json', ROOT / 'golden/schema.json', ROOT / 'golden/coverage-plan.json']
    if any(args.output.resolve() == p.resolve() or (args.output.exists() and p.exists() and args.output.samefile(p)) for p in protected):
        parser.error('Output must not overwrite dataset, responses, schema, plan, or configuration')
    result = run(args.dataset, args.responses, args.mode, args.backend_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key not in ('case_results', 'required_thresholds')}, indent=2))
    return 0 if result['overall_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
