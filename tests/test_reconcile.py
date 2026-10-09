import hashlib
import json
import unittest
from unittest.mock import patch
import reconcile


class Imports(unittest.TestCase):
    def fixture(self):
        artifact = b'{"signed":"fixture"}'
        descriptor = {'schema': 'knowledge-project/1', 'artifact': {
            'path': 'knowledge/artifact.json', 'sha256': hashlib.sha256(artifact).hexdigest(), 'address': 'a' * 64}}
        entry = {'schema': 'knowledge-core-entry/1', 'github': 'example/project', 'revision': 'b' * 40}
        def reader(repo, rev, path):
            return json.dumps(descriptor).encode() if path == 'knowledge.json' else artifact
        return entry, descriptor, reader

    def test_descriptor_resolves_artifact_without_catalog_copy(self):
        entry, _, reader = self.fixture()
        data, address = reconcile.resolve(entry, reader)
        self.assertEqual(data, b'{"signed":"fixture"}')
        self.assertEqual(address, 'a' * 64)

    def test_bad_hash_prevents_any_cache_write(self):
        entry, descriptor, reader = self.fixture()
        descriptor['artifact']['sha256'] = '0' * 64
        with patch('reconcile.subprocess.run') as put:
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                reconcile.reconcile([entry], '/unused', ['knowledge'], '/unused', reader)
            put.assert_not_called()

    def test_paths_and_mutable_revisions_rejected_before_network(self):
        for path in ['../secret', '/absolute', 'a/../b']:
            with self.assertRaises(ValueError):
                reconcile.safe_path(path)
        with self.assertRaisesRegex(ValueError, 'immutable'):
            reconcile.fetch('example/project', 'main', 'knowledge.json')


if __name__ == '__main__':
    unittest.main()
