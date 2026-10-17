#!/usr/bin/env python3
"""Conservative read-only documentation and Git-status audit; standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

EXCLUDE = {'.git', '.venv', 'venv', 'node_modules', 'dist', 'build', 'vendor', '__pycache__', '.tox', '.next', 'private', 'secrets', 'keys'}
CANDIDATES = {'CURRENT.md', 'NEXT.md', 'README.md', 'ARCHITECTURE.md', 'CONTRIBUTING.md', 'STATUS.md', 'PROJECT.md', 'AGENTS.md'}
MAX_DOCS = 150
MAX_BYTES = 128_000

def audit(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('root must be a directory')
    git_status = None
    try:
        p = subprocess.run(['git', '-C', str(root), 'status', '--short'],
                           capture_output=True, text=True, timeout=4, check=False)
        if p.returncode == 0:
            git_status = p.stdout.splitlines()[:100]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    found = []
    for folder, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDE and not d.startswith('.')]
        for name in sorted(files):
            if name not in CANDIDATES and not (name.endswith('.md') and len(Path(folder).relative_to(root).parts) < 3):
                continue
            f = Path(folder) / name
            if f.is_symlink():
                continue
            try:
                if f.stat().st_size > MAX_BYTES:
                    continue
                raw = f.read_text(encoding='utf-8', errors='replace')
            except (OSError, UnicodeError):
                continue
            headings = re.findall(r'^#{1,3}\s+(.+)$', raw, flags=re.M)
            stale = re.findall(r'(?im)\b(archived|deprecated|superseded|historical|do not use)\b', raw)
            found.append({'path': f.relative_to(root).as_posix(), 'heading_count': len(headings),
                          'stale_marker_count': len(stale), 'bytes': len(raw.encode('utf-8'))})
            if len(found) >= MAX_DOCS:
                break
        if len(found) >= MAX_DOCS:
            break
    return {'root': str(root), 'git_status': git_status,
            'dirty': bool(git_status) if git_status is not None else None,
            'docs_scanned': len(found), 'candidate_docs': found,
            'audit_limit_reached': len(found) >= MAX_DOCS, 'read_only': True}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', nargs='?', default='.')
    args = p.parse_args()
    try:
        print(json.dumps(audit(args.root), indent=2))
    except (ValueError, OSError) as exc:
        print(f'audit failed: {exc}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
