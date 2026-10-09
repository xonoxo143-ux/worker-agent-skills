#!/usr/bin/env python3
"""Append/verify a small local hash-chained JSONL task log; no network or credentials."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

STAGES = {'SOURCED', 'CONTACTED', 'REPLIED', 'CONTRACTED', 'WORKING', 'DELIVERED', 'ACCEPTED', 'PAID', 'LOST', 'BLOCKED'}

def digest(evt):
    body = {k: v for k, v in evt.items() if k != 'sha256'}
    data = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def load_and_verify(path):
    prev = '0' * 64
    events = []
    if not path.exists():
        return events, prev
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        try:
            e = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'line {n}: invalid JSON: {exc}') from exc
        if not isinstance(e, dict) or e.get('prev_sha256') != prev or e.get('sha256') != digest(e):
            raise ValueError(f'line {n}: invalid hash chain')
        if e.get('seq') != n or e.get('stage') not in STAGES or not isinstance(e.get('task'), str):
            raise ValueError(f'line {n}: invalid event fields')
        events.append(e)
        prev = e['sha256']
    return events, prev

def append(path, task, stage, reference):
    if stage not in STAGES:
        raise ValueError('unsupported stage')
    if not task.strip() or len(task) > 128:
        raise ValueError('task required (max 128 characters)')
    if not reference.strip() or len(reference) > 250:
        raise ValueError('reference required (max 250 characters)')
    path.parent.mkdir(parents=True, exist_ok=True)
    events, prev = load_and_verify(path)
    if events and events[-1]['task'] == task and events[-1]['stage'] == stage and events[-1]['reference'] == reference:
        raise ValueError('duplicate of latest event')
    e = {'seq': len(events) + 1, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'task': task, 'stage': stage, 'reference': reference, 'prev_sha256': prev}
    e['sha256'] = digest(e)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as f:
        f.write(json.dumps(e, sort_keys=True, ensure_ascii=False) + '\n')
        f.flush()
        os.fsync(f.fileno())
    return e

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('append')
    a.add_argument('--path', type=Path, required=True)
    a.add_argument('--task', required=True)
    a.add_argument('--stage', required=True, choices=sorted(STAGES))
    a.add_argument('--reference', required=True)
    v = sub.add_parser('verify')
    v.add_argument('--path', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.cmd == 'append':
            result = {'ok': True, 'event': append(args.path, args.task, args.stage, args.reference)}
        else:
            events, last = load_and_verify(args.path)
            result = {'ok': True, 'count': len(events), 'head_sha256': last,
                      'stages': {s: sum(e['stage'] == s for e in events) for s in sorted(STAGES)}}
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
