#!/usr/bin/env python3
"""Validate handoff evidence; never launch a service or promote from diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def positive_number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value > 0)


def promotion_errors(proof):
    """A negative guardrail, not a replacement for the owning experiment audit."""
    errors = []
    if proof.get('role') != 'candidate':
        errors.append('control replay is not a candidate')
    if proof.get('evidence_class') != 'matched-treatment-ab':
        errors.append('diagnostic or historical evidence cannot promote')
    if proof.get('percentile') != 'p95':
        errors.append('P95 must not be replaced with P50')
    flags = ('runtime_only', 'activation_all_ranks', 'paired_same_environment',
             'warm_state_controlled', 'quality_complete',
             'source_fingerprints_match', 'prefix_cache_isolated',
             'comparison_registered', 'tail_risk_reviewed')
    for flag in flags:
        if proof.get(flag) is not True:
            errors.append('missing gate: ' + flag)
    if not proof.get('baseline_id'):
        errors.append('missing denominator ID')
    if proof.get('generalization_claim'):
        for flag in ('policy_frozen_before_holdout', 'unseen_content', 'unseen_shapes'):
            if proof.get(flag) is not True:
                errors.append('missing generalization gate: ' + flag)
    matrix = proof.get('matrix', [])
    expected = {(c, r) for c in (1, 5, 8, 16) for r in (1, 2, 3)}
    keys = [(row.get('c'), row.get('r')) for row in matrix]
    if len(keys) != 12 or set(keys) != expected:
        errors.append('incomplete or duplicated repetition matrix')
        return errors
    for c in (1, 5, 8, 16):
        rows = [row for row in matrix if row['c'] == c]
        for metric, bound in (('ttft', 0.60), ('tpot', 0.80)):
            b = [row.get('baseline_' + metric) for row in rows]
            a = [row.get('candidate_' + metric) for row in rows]
            if not all(positive_number(v) for v in b + a):
                errors.append('invalid latency: ' + metric)
            elif statistics.median(a) / statistics.median(b) > bound:
                errors.append('latency target missed: c' + str(c) + '/' + metric)
    return errors


def validate_packet(repo, verify_artifacts=False):
    repo = Path(repo)
    root = repo / 'docs/handovers/qwen35-mtp-off'
    packet = json.loads((root / 'evidence.json').read_text())
    lessons = json.loads((root / 'lessons.json').read_text())
    require(packet['schema'] == 'qwen35-handoff/v1', 'unknown handoff schema')
    require(lessons['schema'] == 'qwen35-experience-lessons/v1', 'unknown lesson schema')
    target = packet['target']
    for key in ('mtp', 'speculation', 'quantization', 'retraining'):
        require(target[key] is False, 'forbidden target change: ' + key)
    require(target['dtype'] == 'BF16' and target['tp'] == 4 and target['dp'] == 1,
            'dtype/topology drift')
    require(target['ttft_max_ratio'] == 0.60 and target['tpot_max_ratio'] == 0.80,
            'latency gate changed')
    require(target['concurrencies'] == [1, 5, 8, 16] and target['repetitions'] == 3,
            'matrix contract changed')
    require(target['quality_rows'] == 357 and target['material_quality_regressions_allowed'] == 0,
            'quality scope changed')
    require(packet['performance_status'] == 'not-achieved', 'snapshot cannot claim a release')
    require(packet['runtime_snapshot_is_lease'] is False, 'snapshot is not a resource lease')
    require(packet['t15']['experiment_complete'] is False, 'T15 completion is not evidenced')
    evidence = {e['id']: e for e in packet['evidence']}
    require(len(evidence) == len(packet['evidence']), 'duplicate evidence ID')
    for item in evidence.values():
        require(re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None, 'invalid checksum')
        require(bool(item['scope']), 'missing evidence boundary')
        if verify_artifacts:
            require(Path(item['path']).is_file(), 'artifact missing: ' + item['id'])
            require(file_hash(item['path']) == item['sha256'], 'artifact drift: ' + item['id'])
    records = {row['id']: row for row in packet['records']}
    require(len(records) == len(packet['records']), 'duplicate record ID')
    for row in records.values():
        require(row['evidence_id'] in evidence, 'record without evidence')
        for key in ('ttft_p95_ms', 'tpot_p95_ms'):
            require(positive_number(row[key]), 'invalid P95')
        if verify_artifacts:
            raw = json.loads(Path(evidence[row['evidence_id']]['path']).read_text())
            for short, long in (('ttft_p95_ms', 'ttft_ms'), ('tpot_p95_ms', 'tpot_ms')):
                require(row[short] == raw[long]['p95'], 'reported percentile mismatch')
            require(row['completed'] == raw['completed'] and row['errors'] == raw['errors'],
                    'reported sample count mismatch')
    for key in ('t14-r1', 't14-r2'):
        require(records[key]['role'] == 'control', 'T14 must not become a candidate')
    require(packet['dataset_nonempty_answers'] == 0, 'oracle scope changed without audit')
    ids = set()
    allowed = {'existing-skill-update', 'new-narrow-skill', 'registry-metadata',
               'example-repository-pattern', 'eval-or-verification-case',
               'tool-adapter-note', 'runtime-product-boundary-rule',
               'git-checkpoint-policy', 'audit-correction', 'do-not-ingest'}
    for lesson in lessons['lessons']:
        require(lesson['id'] not in ids, 'duplicate lesson')
        ids.add(lesson['id'])
        require(lesson['classification'] in allowed, 'invalid ingestion destination class')
        for field in ('trigger', 'different_action', 'destination', 'verification', 'scope'):
            require(bool(lesson.get(field)), 'incomplete ingestion: ' + field)
        dest = Path(lesson['destination'])
        require(not dest.is_absolute() and '..' not in dest.parts, 'unsafe destination')
        require((repo / dest).is_file(), 'missing lesson destination: ' + str(dest))
        require(lesson['evidence_ids'] and all(e in evidence for e in lesson['evidence_ids']),
                'lesson without traceable evidence')
    readme = (root / 'README.md').read_text()
    for n, section in enumerate(('Status', 'North Star', 'Current Focus', 'Recent Progress',
                                  'Current Action', 'Next Actions', 'Validation Commands',
                                  'Do Not Do', 'Recovery / Resume Commands')):
        require('## ' + str(n) + '. ' + section in readme, 'missing resume section')
    if verify_artifacts:
        audit = json.loads(Path(evidence['E-P95-AUDIT']['path']).read_text())
        for ref in audit['raw_files']:
            require(file_hash(ref['path']) == ref['sha256'], 'historical raw evidence drift')
        manifest = json.loads(Path(evidence['E-PRESERVATION']['path']).read_text())
        backup = Path(manifest['backup_root'])
        require(file_hash(backup / 'delivery-uncommitted.patch') == packet['patch_sha256'],
                'private recovery patch drift')
        for item in manifest['untracked_files']:
            if 'sha256' in item:
                require(file_hash(backup / 'untracked' / item['path']) == item['sha256'],
                        'private untracked backup drift')
    return {'lessons': len(ids), 'evidence_files': len(evidence),
            'artifact_verification': verify_artifacts, 'performance_accepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--verify-artifacts', action='store_true')
    args = parser.parse_args()
    try:
        result = validate_packet(args.repo, args.verify_artifacts)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, 'FAIL: ' + str(exc) + '\n')
    print('PASS: ' + json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
