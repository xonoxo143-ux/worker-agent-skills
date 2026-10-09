import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

AUDIT = load(ROOT / 'skills/project-truth-keeper/scripts/audit_repo.py', 'audit_repo')
LEDGER = load(ROOT / 'skills/task-evidence-keeper/scripts/ledger.py', 'ledger')

class ReleaseTests(unittest.TestCase):
    def test_skill_format(self):
        for d in (ROOT / 'skills').iterdir():
            if d.is_dir():
                t = (d / 'SKILL.md').read_text()
                self.assertTrue(t.startswith('---\n'))
                self.assertIn('name: ' + d.name, t)
                self.assertIn('description: ', t)

    def test_read_only_audit_skips_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'CURRENT.md').write_text('# Current\nDeprecated old design\n')
            (root / '.env').write_text('TOKEN=never-expose')
            (root / 'private').mkdir()
            (root / 'private/STATUS.md').write_text('not-for-display')
            result = AUDIT.audit(root)
            self.assertEqual(result['docs_scanned'], 1)
            self.assertEqual(result['candidate_docs'][0]['stale_marker_count'], 1)
            self.assertNotIn('never-expose', json.dumps(result))
            self.assertNotIn('not-for-display', json.dumps(result))

    def test_ledger_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ledger.jsonl'
            LEDGER.append(p, 't1', 'SOURCED', 'public-post')
            LEDGER.append(p, 't1', 'CONTACTED', 'message-id')
            events, head = LEDGER.load_and_verify(p)
            self.assertEqual(len(events), 2)
            self.assertEqual(len(head), 64)
            with self.assertRaises(ValueError):
                LEDGER.append(p, 't1', 'CONTACTED', 'message-id')
            p.write_text(p.read_text().replace('message-id', 'fake-id'))
            with self.assertRaises(ValueError):
                LEDGER.load_and_verify(p)

if __name__ == '__main__':
    unittest.main()
