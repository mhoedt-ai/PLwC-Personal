from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import audit_personal_publication_surface as auditor
import export_personal_source as exporter
import sign_personal_release as signer
import verify_runtime_images as verifier
from plwc_gateway.installation.update_center import rsa_public_key_id, load_trusted_release_keys


@pytest.mark.parametrize('kind',['chrome','edge','mcpb','source'])
@pytest.mark.parametrize('fault',['none','missing','changed','duplicate','traversal','link_only','secret'])
def test_actual_archive_grants_are_complete_exact_texts(tmp_path,kind,fault):
    expected={name:(ROOT/name).read_bytes() for name in auditor.PERSONAL_GRANTS}
    entries=dict(expected)
    if fault=='missing':entries.pop('PERSONAL_USE_PERMISSION.md')
    elif fault=='changed':entries['LICENSE']=b'old Apache-only artifact'
    elif fault=='duplicate':entries['license']=entries['LICENSE']
    elif fault=='traversal':entries['../private.txt']=b'private'
    elif fault=='link_only':entries['OFFICIAL_REDISTRIBUTION_PERMISSION.md']=b'https://example.invalid/license'
    elif fault=='secret':entries['config/data.txt']=b'-----BEGIN '+b'PRIVATE KEY-----'
    archive=tmp_path/(kind+'.zip')
    with zipfile.ZipFile(archive,'w') as handle:
        for name,data in entries.items():handle.writestr(name,data)
    if fault=='none':assert auditor.verify_archive_grants(archive,expected)['status']=='pass'
    else:
        with pytest.raises(exporter.PublicationError):auditor.verify_archive_grants(archive,expected)


def _content(tmp_path,name,data):
    path=tmp_path/name;path.write_bytes(data)
    return {'path':name,'sha256':hashlib.sha256(data).hexdigest()}


def _licenses(tmp_path,license_name='MIT'):
    package={'name':'fixture-package','versionInfo':'3.2.1'}
    item={'name':package['name'],'version':package['versionInfo'],'license_concluded':license_name,
        'reviewed_by':'synthetic-reviewer','notice':_content(tmp_path,'notice.txt',b'full synthetic notice'),
        'source_required':'GPL' in license_name,'source':None,'lgpl_replacement':None}
    if item['source_required']:
        item['source']={'name':item['name'],'version':item['version'],'archive':_content(tmp_path,'source.tar',b'exact synthetic corresponding-source archive')}
    if 'LGPL' in license_name:
        item['lgpl_replacement']=_content(tmp_path,'replacement.txt',b'synthetic replacement instructions and test evidence')
    inventory={'schema_version':'1.0.0','source_sbom_sha256':'a'*64,'packages':[item]}
    return inventory,[package]


@pytest.mark.parametrize('license_name',['MIT','GPL-2.0-only','LGPL-2.1-or-later'])
def test_license_inventory_has_actual_notices_and_exact_source_rights(tmp_path,license_name):
    inventory,packages=_licenses(tmp_path,license_name)
    auditor.verify_dependency_licenses(inventory,packages,tmp_path)


@pytest.mark.parametrize('fault',['noassertion','missing_notice','changed_notice','unreviewed','missing_package',
    'empty_sbom','source_missing','source_wrong_version','gpl_waiver','lgpl_replacement','unknown_field'])
def test_unresolved_license_or_corresponding_source_blocks_candidate(tmp_path,fault):
    inventory,packages=_licenses(tmp_path,'LGPL-2.1-or-later');item=inventory['packages'][0]
    if fault=='noassertion':item['license_concluded']='NOASSERTION'
    elif fault=='missing_notice':(tmp_path/'notice.txt').unlink()
    elif fault=='changed_notice':(tmp_path/'notice.txt').write_bytes(b'changed')
    elif fault=='unreviewed':item['reviewed_by']=''
    elif fault=='missing_package':inventory['packages']=[]
    elif fault=='empty_sbom':packages=[]
    elif fault=='source_missing':item['source']=None
    elif fault=='source_wrong_version':item['source']['version']='3.2.0'
    elif fault=='gpl_waiver':item['source_required']=False;item['source']=None
    elif fault=='lgpl_replacement':item['lgpl_replacement']=None
    else:item['waiver']='approved'
    with pytest.raises((exporter.PublicationError,OSError)):auditor.verify_dependency_licenses(inventory,packages,tmp_path)


def test_release_verifier_binds_license_inventory_to_real_sbom(tmp_path):
    inventory,packages=_licenses(tmp_path)
    sbom=tmp_path/'sbom.json';sbom.write_text(json.dumps({'spdxVersion':'SPDX-2.3','packages':packages}))
    inventory['source_sbom_sha256']=hashlib.sha256(sbom.read_bytes()).hexdigest()
    path=tmp_path/'licenses.json';path.write_text(json.dumps(inventory))
    verifier._verify_licenses(path,sbom,tmp_path)
    inventory['source_sbom_sha256']='b'*64;path.write_text(json.dumps(inventory))
    with pytest.raises(verifier.VerificationError,match='actual SBOM'):verifier._verify_licenses(path,sbom,tmp_path)


@pytest.fixture(scope='module')
def key():return rsa.generate_private_key(public_exponent=65537,key_size=3072)


def test_public_pin_is_independently_bound_to_spki_der(key,tmp_path):
    expected=hashlib.sha256(key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
    pin=signer.public_pin(key)
    assert pin['key_id']=='plwc-personal-rsa-'+expected
    trust=tmp_path/'public-trust.json';trust.write_text(json.dumps({'schema_version':'1.0.0','keys':[pin]}))
    assert load_trusted_release_keys(trust)[pin['key_id']]['modulus']==key.public_key().public_numbers().n


def test_signer_rejects_legacy_key_size():
    with pytest.raises(ValueError,match='RSA3072'):signer.public_pin(rsa.generate_private_key(public_exponent=65537,key_size=2048))


def test_key_is_encrypted_external_owner_only_and_recoverable(tmp_path):
    # Ephemeral synthetic key in pytest's local temp directory, never a production trust anchor.
    original=tmp_path/'synthetic-key.pem';backup=tmp_path/'synthetic-restored.pem';password=b'ephemeral test only'
    pin=signer.create_key(original,password)
    assert original.read_bytes().startswith(b'-----BEGIN '+b'ENCRYPTED PRIVATE KEY-----')
    backup.touch();signer.owner_only(backup);backup.write_bytes(original.read_bytes())
    result=signer.verify_recovery(original,backup,password)
    assert result['status']=='pass' and result['key_id']==pin['key_id']
    with pytest.raises((ValueError,TypeError)):signer.load_key(original,b'wrong')
    with pytest.raises(FileExistsError):signer.create_key(original,password)


def test_key_path_cannot_enter_project_or_network():
    for path in (ROOT/'build/key.pem',Path('//private-host/share/key.pem')):
        with pytest.raises(ValueError):signer.external_key_path(path)


def test_key_with_broad_permissions_is_rejected_before_read(tmp_path,monkeypatch):
    path=tmp_path/'synthetic-key.pem';path.write_bytes(b'not a key')
    def bad_acl(_):raise ValueError('Private key permissions are not owner-only')
    monkeypatch.setattr(signer,'verify_owner_only',bad_acl)
    with pytest.raises(ValueError,match='owner-only'):signer.load_key(path,b'password')


def test_signer_uses_independent_manifest_verifier(key):
    import test_update_center as update_tests
    manifest=update_tests.signed_manifest()
    result=signer.sign_manifest(manifest,key)
    assert result['signature']['key_id']==signer.public_pin(key)['key_id']
    invalid=copy.deepcopy(manifest);invalid['release']['product']='Other Product'
    with pytest.raises(ValueError):signer.sign_manifest(invalid,key)
