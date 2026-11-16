#!/usr/bin/env python3
"""Run all five original criteria through the live service, three trials each.

python run_eval.py --label before
python run_eval.py --label after

This extends the starter runner to measure appeals, log changes, JSON errors,
label coverage, and average score separation. It does not change the service.
Each submission has a fresh test creator ID to isolate these criteria from the
separate flood test. IDs are recorded; these tests do not validate identity.
"""
import argparse
import datetime as dt
import json
import math
import statistics
import uuid
from pathlib import Path

import requests
import scenarios

ROOT = Path(__file__).resolve().parent


class Client:
    def __init__(self, url, timeout):
        self.url = url.rstrip('/')
        self.timeout = timeout
        self.trace = []

    def call(self, method, route, body=None):
        record = {'method': method, 'route': route}
        if body is not None:
            record['request'] = body
        try:
            response = requests.request(method, self.url + route, json=body,
                                        timeout=self.timeout)
            record['status'] = response.status_code
            try:
                record['response'] = response.json()
                record['json'] = True
            except ValueError:
                record['response'] = response.text[:2000]
                record['json'] = False
        except requests.RequestException as exc:
            record.update(status=None, json=False, error=str(exc))
        self.trace.append(record)
        return record

    def submit(self, text):
        return self.call('POST', '/submit', {
            'text': text, 'creator_id': 'eval_' + uuid.uuid4().hex
        })

    def history(self, content_id):
        result = self.call('GET', '/log')
        payload = result.get('response')
        if result.get('status') != 200 or not isinstance(payload, dict):
            return None
        entries = payload.get('entries')
        if not isinstance(entries, list):
            return None
        # Retain only this submission in the evidence, while using the actual
        # unfiltered response for the history check.
        selected = [e for e in entries if e.get('content_id') == content_id]
        result['response'] = {'entries': selected}
        result['response_scope'] = 'Filtered locally to the tested content_id'
        return selected


def payload(result):
    value = result.get('response')
    return value if isinstance(value, dict) else {}


def accepted(result):
    p = payload(result)
    return (result.get('status') == 200 and p.get('guess') in {'human', 'ai', 'unsure'}
            and isinstance(p.get('content_id'), str))


def score(result):
    value = payload(result).get('confidence')
    return value if (accepted(result) and isinstance(value, (int, float))
                     and not isinstance(value, bool) and math.isfinite(value)
                     and 0 <= value <= 1) else None


def appeal_test(client):
    setup = client.submit(scenarios.APPEAL_TEXT)
    content_id = payload(setup).get('content_id')
    if not accepted(setup):
        return {'met': False, 'measure': '0/5; setup failed', 'cases': [],
                'setup_error': 'Could not obtain a valid submission ID'}

    cases = []
    original = client.history(content_id)
    original_decisions = [e for e in (original or []) if e.get('event') != 'appeal']
    specifications = [
        ('initial detailed explanation', content_id, scenarios.REASON_ONE, 200, False),
        ('duplicate explanation', content_id, scenarios.REASON_ONE, 200, True),
        ('short explanation', content_id, 'I wrote this myself.', 400, None),
        ('different detailed explanation', content_id, scenarios.REASON_TWO, 200, False),
        ('unknown content ID', 'missing_' + uuid.uuid4().hex, scenarios.REASON_ONE, 404, None),
    ]
    for name, target_id, reasoning, expected_status, duplicate in specifications:
        before = client.history(target_id)
        response = client.call('POST', '/appeal',
                               {'content_id': target_id, 'reasoning': reasoning})
        after = client.history(target_id)
        p = payload(response)
        ok = (response.get('status') == expected_status
              and response.get('json') is True
              and before is not None and after is not None)
        if expected_status == 200:
            ok = ok and p.get('status') == 'under_review' and p.get('duplicate') is duplicate
            if duplicate:
                ok = ok and after == before
            else:
                new = after[len(before):] if after is not None and before is not None else []
                ok = (ok and len(after) == len(before) + 1 and len(new) == 1
                      and new[0].get('event') == 'appeal'
                      and new[0].get('status') == 'under_review'
                      and new[0].get('reasoning') == reasoning
                      and new[0].get('content_id') == content_id)
        else:
            ok = ok and after == before and bool(p.get('error')) and bool(p.get('message'))
        if target_id == content_id and after is not None:
            ok = ok and [e for e in after if e.get('event') != 'appeal'] == original_decisions
        cases.append({'case': name, 'met': bool(ok), 'status': response.get('status'),
                      'before_entries': len(before) if before is not None else None,
                      'after_entries': len(after) if after is not None else None})
    count = sum(c['met'] for c in cases)
    return {'met': count == 5, 'measure': f'{count}/5', 'cases': cases}


def evaluate(number, client):
    if number == 1:
        results = [client.submit(t) for t in scenarios.HUMAN_TEXTS]
        valid = sum(accepted(r) for r in results)
        false_positives = sum(payload(r).get('guess') == 'ai' for r in results)
        return {'met': valid == 10 and false_positives == 0,
                'measure': f'{false_positives}/10 AI; {valid}/10 accepted',
                'false_positives': false_positives, 'accepted': valid}
    if number == 2:
        return appeal_test(client)
    if number == 3:
        cases = [
            ('missing text', {}, 400),
            ('blank text', {'text': ''}, 400),
            ('wrong type', {'text': 12345}, 400),
            ('short text', {'text': 'Short submission.'}, 400),
            ('long text', {'text': 'x' * 10001}, 413),
        ]
        checks = []
        for name, body, expected in cases:
            body = dict(body, creator_id='eval_' + uuid.uuid4().hex)
            result = client.call('POST', '/submit', body)
            p = payload(result)
            ok = (result.get('status') == expected and result.get('json') is True
                  and bool(p.get('error')) and bool(p.get('message')))
            checks.append({'case': name, 'met': bool(ok), 'status': result.get('status')})
        health = client.call('GET', '/health')
        alive = health.get('status') == 200 and payload(health).get('ok') is True
        count = sum(c['met'] for c in checks)
        return {'met': count == 5 and alive, 'measure': f'{count}/5; service alive={alive}',
                'cases': checks, 'service_alive': alive}
    if number == 4:
        results = [client.submit(t) for t in scenarios.COVERAGE_TEXTS]
        labels = sorted({payload(r).get('guess') for r in results if accepted(r)})
        valid = sum(accepted(r) for r in results)
        return {'met': valid == 6 and set(labels) == {'human', 'ai', 'unsure'},
                'measure': f'{len(labels)}/3 labels; {valid}/6 accepted', 'labels': labels}
    if number == 5:
        human = [score(client.submit(t)) for t in scenarios.HUMAN_TEXTS[:5]]
        ai = [score(client.submit(t)) for t in scenarios.AI_TEXTS]
        if any(v is None for v in human + ai):
            return {'met': False, 'measure': 'Incomplete scores',
                    'human_scores': human, 'ai_scores': ai}
        human_mean = statistics.mean(human)
        ai_mean = statistics.mean(ai)
        gap = ai_mean - human_mean
        return {'met': gap >= 0.25, 'measure': f'gap={gap:.5f}',
                'human_scores': human, 'ai_scores': ai,
                'human_mean': human_mean, 'ai_mean': ai_mean, 'gap': gap}
    raise ValueError('Unknown criterion')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=['before', 'after'], required=True)
    parser.add_argument('--url', default='http://127.0.0.1:5000')
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    problems = scenarios.validate()
    if problems:
        raise SystemExit('\n'.join(problems))
    try:
        response = requests.get(args.url.rstrip('/') + '/health', timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f'Start python app.py in the other terminal. {exc}')

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\nCriterion {scenario['criterion']}: {scenario['name']}", flush=True)
        trials = []
        for trial in range(1, 4):
            client = Client(args.url, args.timeout)
            result = evaluate(scenario['criterion'], client)
            result.update(trial=trial, evidence=client.trace)
            trials.append(result)
            print(f"  Trial {trial}: {result['measure']} — "
                  f"{'MET' if result['met'] else 'MISSED'}", flush=True)
        rows.append(dict(scenario, trials=trials,
                         verdict='MET' if all(t['met'] for t in trials) else 'MISSED'))

    directory = ROOT / 'results'
    directory.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    stem = f'run_{stamp}_{args.label}'
    data = {'produced_by': 'run_eval.py::main; run_eval.py::evaluate; run_eval.py::appeal_test',
            'label': args.label, 'trials_per_criterion': 3, 'rows': rows}
    (directory / (stem + '.json')).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = [f'# Run log — {args.label}', '',
             'Produced by `run_eval.py::main`, `evaluate`, and `appeal_test`.', '',
             'Samples are fixed in `scenarios.py`. Fresh creator IDs isolate requests',
             'from the separately tested per-creator flood limit. All trials use the',
             'same service configuration. Human excerpts come from one essay and',
             'include cited quotations. Score-spread topics and lengths are unmatched.', '',
             '| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |',
             '|---|---|---|---|---|---|']
    for row in rows:
        measures = ' | '.join(t['measure'] for t in row['trials'])
        lines.append(f"| {row['criterion']}. {row['name']} | {row['target']} | {measures} | {row['verdict']} |")
    for row in rows:
        lines += ['', f"## Criterion {row['criterion']}: {row['name']}"]
        for trial in row['trials']:
            lines += ['', f"### Trial {trial['trial']}", '', '```json',
                      json.dumps(trial, indent=2, ensure_ascii=False), '```']
    (directory / (stem + '.md')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\nSaved results/{stem}.md and results/{stem}.json', flush=True)
    print('MET/MISSED here measures the original targets; inspect the evidence before final verdicts.')


if __name__ == '__main__':
    main()
