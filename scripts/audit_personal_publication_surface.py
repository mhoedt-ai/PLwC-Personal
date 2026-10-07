"""Audit captured publication surfaces. This never changes visibility or grants approval.

The collector/reviewer must supply every surface, all pages and actual content files.
A successful audit validates this captured inventory; it does not prove freshness or
replace the separate live inventory, owner review and writer freeze before publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from export_personal_source import PublicationError, checked_file, scan_forbidden_bytes, scan_stream

SOURCE_SURFACES = frozenset({
    'refs', 'commit_history', 'commit_messages', 'git_objects', 'lfs_objects',
    'releases', 'release_assets', 'actions_runs', 'actions_logs', 'actions_artifacts',
    'pull_requests', 'issues', 'discussions', 'wiki', 'pages', 'attachments',
    'settings', 'access_and_inherited_package_rights',
})
PACKAGE_SURFACES = frozenset({'versions', 'tags', 'manifest_graph', 'attachments',
    'settings', 'access_and_inherited_package_rights'})
PERSONAL_GRANTS = ('LICENSE', 'PERSONAL_USE_PERMISSION.md', 'OFFICIAL_REDISTRIBUTION_PERMISSION.md')


def all_pages(pages: list[dict]) -> list[dict]:
    """Require a contiguous, terminated cursor chain and a stable exact total."""
    if not isinstance(pages, list) or not pages:
        raise PublicationError('Missing pagination evidence, including for an empty surface')
    cursor = None
    seen_cursors = set()
    seen_ids = set()
    items = []
    total = pages[0].get('total_count')
    if type(total) is not int or total < 0:
        raise PublicationError('Surface total is unavailable')
    for index, page in enumerate(pages):
        if set(page) != {'cursor', 'next_cursor', 'total_count', 'items', 'capture'}:
            raise PublicationError('Unknown or missing pagination fields')
        if page['cursor'] != cursor or page['total_count'] != total:
            raise PublicationError('Pagination gap or inventory changed during collection')
        if not isinstance(page['items'], list):
            raise PublicationError('Unreadable page')
        for item in page['items']:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']:
                raise PublicationError('Surface item has no stable identity')
            if item['id'] in seen_ids:
                raise PublicationError('Duplicate surface item')
            seen_ids.add(item['id']); items.append(item)
        cursor = page['next_cursor']
        if cursor is None:
            if index != len(pages)-1:
                raise PublicationError('Pages after pagination terminated')
        elif not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
            raise PublicationError('Invalid or cyclic pagination')
        seen_cursors.add(cursor)
    if cursor is not None or len(items) != total:
        raise PublicationError('Incomplete pagination or total count')
    return items


def content_file(root: Path, record: dict, private_roots: tuple[str, ...]) -> str:
    if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
        raise PublicationError('Missing actual captured content')
    data = checked_file(root, record['path']).read_bytes()
    if not data:raise PublicationError('Captured evidence file is empty')
    digest = hashlib.sha256(data).hexdigest()
    if digest != record['sha256']:
        raise PublicationError('Captured content changed')
    scan_forbidden_bytes(data, private_roots=private_roots)
    return digest


def audit_surface(snapshot: dict, approved: dict, root: Path, *, private_roots=()) -> dict:
    """Bind all captured items and their bytes to the reviewed explicit inventory."""
    if set(snapshot) != {'kind', 'subject', 'visibility', 'publication_commit', 'surfaces', 'writer_freeze'}:
        raise PublicationError('Unknown or missing snapshot fields')
    kind = snapshot['kind']
    required = SOURCE_SURFACES if kind == 'source' else PACKAGE_SURFACES if kind == 'package' else None
    if required is None or set(snapshot['surfaces']) != required:
        raise PublicationError('Incomplete or unknown publication surfaces')
    subjects={'mhoedt-ai/PLwC-Personal'} if kind=='source' else {
        'ghcr.io/mhoedt-ai/plwc-personal-'+component for component in ('document-worker','node-runner','python-runner')}
    if snapshot['subject'] not in subjects:
        raise PublicationError('Publication subject is not the canonical Personal channel')
    if snapshot['visibility'] != 'private':
        raise PublicationError('Prepublication subject must still be private')
    if not re.fullmatch(r'[0-9a-f]{40}', str(snapshot['publication_commit'])):
        raise PublicationError('Actual publication commit is missing')
    if set(approved) != {'subject', 'publication_commit', 'reviewed_by', 'items'} or not isinstance(approved['reviewed_by'],str) or not approved['reviewed_by'].strip():
        raise PublicationError('Reviewed inventory is missing')
    if any(snapshot[field] != approved[field] for field in ('subject', 'publication_commit')):
        raise PublicationError('Reviewed inventory belongs to a different subject or commit')
    freeze = snapshot['writer_freeze']
    if not isinstance(freeze, dict) or set(freeze) != {'active', 'publication_commit', 'evidence'} or freeze['active'] is not True or freeze['publication_commit'] != snapshot['publication_commit']:
        raise PublicationError('Writer freeze is missing or bound to another commit')
    content_file(root, freeze['evidence'], private_roots)
    actual = {}
    for surface, pages in snapshot['surfaces'].items():
        for page in pages:
            content_file(root, page.get('capture'), private_roots)
        for item in all_pages(pages):
            if set(item) != {'id', 'content'} or not isinstance(item['content'], list) or not item['content']:
                raise PublicationError('Unreadable or incomplete surface item')
            identity = surface + ':' + item['id']
            digests = [content_file(root, record, private_roots) for record in item['content']]
            if len(set(digests)) != len(digests):
                raise PublicationError('Duplicated captured content cannot replace missing content')
            actual[identity] = digests
    if actual != approved['items']:
        raise PublicationError('Unknown, missing or changed publication item')
    inventory_sha = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'status': 'captured_inventory_pass', 'subject': snapshot['subject'],
        'publication_commit': snapshot['publication_commit'], 'items_checked': len(actual),
        'snapshot_sha256': inventory_sha, 'publication_authorized': False,
        'live_recollection_required_before_publication': True}


def verify_manifest_graph(versions: list[dict], manifests: dict[str, dict], approved_digests: set[str]) -> None:
    """Include tagged and untagged versions, nested manifests and referrers."""
    reachable = set()
    if any(not isinstance(digest,str) or not re.fullmatch('sha256:[0-9a-f]{64}',digest) for digest in approved_digests):
        raise PublicationError('Reviewed graph has an invalid digest')
    pending = []
    ids = set()
    for version in versions:
        if set(version) != {'id', 'digest', 'tags'} or type(version['id']) is not int or version['id']<1 or version['id'] in ids or not isinstance(version['tags'], list) or any(not isinstance(tag,str) or not tag for tag in version['tags']):
            raise PublicationError('Unknown or duplicate package version')
        ids.add(version['id']); pending.append(version['digest'])
    while pending:
        digest = pending.pop()
        if digest in reachable: continue
        if digest not in approved_digests or digest not in manifests:
            raise PublicationError('Unknown package version or manifest/referrer')
        node = manifests[digest]
        if set(node) != {'children', 'referrers'} or any(not isinstance(node[key], list) for key in node):
            raise PublicationError('Unreadable manifest graph')
        reachable.add(digest); pending.extend(node['children']); pending.extend(node['referrers'])
    if reachable != set(manifests) or reachable != approved_digests:
        raise PublicationError('Incomplete manifest graph or reviewed inventory')


def verify_archive_grants(archive: Path, expected: dict[str, bytes], *, prefix: str = '', private_roots=()) -> dict:
    """Read the actual ZIP/MCPB, including exact license text bytes, without extraction."""
    if set(expected) != set(PERSONAL_GRANTS):
        raise PublicationError('All three Personal grants are required')
    with zipfile.ZipFile(archive) as handle:
        names = handle.namelist()
        if len({name.casefold() for name in names}) != len(names):
            raise PublicationError('Duplicate/case-aliased archive entry')
        for item in handle.infolist():
            if item.filename.startswith(('/', '\\')) or '..' in item.filename.split('/') or '\\' in item.filename or ':' in item.filename:
                raise PublicationError('Unsafe artifact entry')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise PublicationError('Artifact symlink is forbidden')
            if not item.is_dir():
                with handle.open(item) as stream:scan_stream(stream,private_roots=private_roots)
        for name, data in expected.items():
            target = prefix + name
            if target not in names or handle.read(target) != data:
                raise PublicationError('Artifact grant is missing or differs from approved bytes')
    return {'status': 'pass', 'grants_checked': list(PERSONAL_GRANTS),
        'artifact_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}


def verify_dependency_licenses(inventory: dict, packages: list[dict], root: Path) -> None:
    """Require complete reviewed coverage; no unknown license or source-right waiver."""
    if set(inventory) != {'schema_version', 'source_sbom_sha256', 'packages'} or inventory['schema_version'] != '1.0.0':
        raise PublicationError('Reviewed license inventory is invalid')
    identities = {(item.get('name'), item.get('versionInfo')) for item in packages}
    if not identities or len(identities) != len(packages) or any(not all(identity) for identity in identities):
        raise PublicationError('Empty, duplicate or unidentified SBOM packages')
    covered = set()
    for item in inventory['packages']:
        if set(item) != {'name', 'version', 'license_concluded', 'reviewed_by', 'notice', 'source_required', 'source', 'lgpl_replacement'}:
            raise PublicationError('Incomplete license review')
        identity = (item['name'], item['version'])
        if identity not in identities or identity in covered:
            raise PublicationError('License inventory coverage differs from SBOM')
        covered.add(identity)
        license_name = item['license_concluded']
        if not isinstance(license_name, str) or not license_name.strip() or any(marker in license_name.upper() for marker in ('NOASSERTION', 'UNKNOWN', 'UNRESOLVED', 'NONE')) or not item['reviewed_by']:
            raise PublicationError('License rights are unresolved')
        content_file(root, item['notice'], ())
        if type(item['source_required']) is not bool:
            raise PublicationError('Corresponding-source decision is missing')
        # GPL-family packages always require exact corresponding-source evidence.
        if 'GPL' in license_name.upper() and item['source_required'] is not True:
            raise PublicationError('GPL corresponding source cannot be waived')
        if item['source_required']:
            source = item['source']
            if not isinstance(source, dict) or set(source) != {'name', 'version', 'archive'} or (source['name'], source['version']) != identity:
                raise PublicationError('Corresponding source is missing or belongs to another package version')
            content_file(root, source['archive'], ())
        elif item['source'] is not None:
            raise PublicationError('Unclassified source evidence')
        if 'LGPL' in license_name.upper():
            if not isinstance(item['lgpl_replacement'], dict):
                raise PublicationError('LGPL replacement instructions/evidence are missing')
            content_file(root, item['lgpl_replacement'], ())
        elif item['lgpl_replacement'] is not None:
            raise PublicationError('Unclassified LGPL evidence')
    if covered != identities:
        raise PublicationError('SBOM package has no reviewed license/source rights')


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--reviewed-inventory', type=Path, required=True)
    p.add_argument('--content-root', type=Path, required=True)
    args = p.parse_args()
    result = audit_surface(json.loads(args.snapshot.read_text(encoding='utf-8')),
        json.loads(args.reviewed_inventory.read_text(encoding='utf-8')), args.content_root)
    print(json.dumps(result, indent=2)); return 0


if __name__ == '__main__': raise SystemExit(main())
