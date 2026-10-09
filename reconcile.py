#!/usr/bin/env python3
"""Resolve pinned GitHub project descriptors and populate a Knowledge cache."""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

MAX_BYTES = 4 * 1024 * 1024


def safe_path(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or str(p) != value:
        raise ValueError('expected normalized repository-relative path')
    return value


def fetch(repository, revision, path):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('expected GitHub owner/repository')
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('imports require a full immutable Git revision')
    url = f'https://raw.githubusercontent.com/{repository}/{revision}/{safe_path(path)}'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('import exceeds 4 MiB')
    return data


def resolve(entry, reader=fetch):
    if entry['schema'] != 'knowledge-core-entry/1':
        raise ValueError('unsupported entry schema')
    descriptor = json.loads(reader(entry['github'], entry['revision'], entry.get('descriptor', 'knowledge.json')))
    if descriptor['schema'] != 'knowledge-project/1':
        raise ValueError('unsupported project schema')
    artifact = descriptor['artifact']
    data = reader(entry['github'], entry['revision'], safe_path(artifact['path']))
    if hashlib.sha256(data).hexdigest() != artifact['sha256']:
        raise ValueError('artifact byte hash mismatch')
    if not re.fullmatch(r'[0-9a-f]{64}', artifact['address']):
        raise ValueError('invalid artifact address')
    return data, artifact['address']


def reconcile(entries, cache, command, receipt_path, reader=fetch):
    # Resolve and validate every import before making any cache insertion.
    resolved = [resolve(entry, reader) for entry in entries]
    with tempfile.TemporaryDirectory(prefix='knowledge-core-') as folder:
        prepared = []
        for index, (data, address) in enumerate(resolved):
            path = Path(folder) / f'{index}.json'
            path.write_bytes(data)
            summary = json.loads(subprocess.check_output(command + ['inspect', '--input', str(path)]))
            if summary['address'] != address or not summary['signature_valid']:
                raise ValueError('Knowledge signature/address verification failed')
            prepared.append((path, address, summary))
        records = []
        for path, address, summary in prepared:
            subprocess.run(command + ['--cache', str(cache), 'put', '--input', str(path)], check=True, stdout=subprocess.DEVNULL)
            records.append({'address': address, 'completeness': summary['completeness'], 'reusable': summary['reusable']})
    receipt = {'schema': 'knowledge-core-state/1', 'imports': entries, 'objects': records,
               'mode': 'additive', 'checking': 'signatures_and_artifact_content_checked; external_sources_not_realized; tests_not_rerun'}
    Path(receipt_path).write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entries', type=Path, default=Path(__file__).parent / 'entries')
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--knowledge', default='knowledge', help='Knowledge executable, optionally with arguments')
    parser.add_argument('--receipt', type=Path, default=Path('cache-state.json'))
    args = parser.parse_args()
    entries = [json.loads(p.read_text()) for p in sorted(args.entries.glob('*.json'))]
    if not entries:
        parser.error('no catalog entries found')
    reconcile(entries, args.cache, shlex.split(args.knowledge), args.receipt)


if __name__ == '__main__':
    main()
