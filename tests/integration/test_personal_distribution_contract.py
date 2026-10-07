from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import export_personal_source as exporter
import build_runtime_images as builder
import promote_runtime_images as promotion
import audit_personal_publication_surface as auditor


def _file(root, name, data=b'public code'):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return exporter.file_record(root,name)


@pytest.mark.parametrize('path', ['../secret', '/absolute', 'a/../b', 'a\\b', 'C:/x',
    '.git/config', 'profiles/real.json', 'logs/private.txt', '.docker/config.json',
    '.env', 'NUL.txt', 'a/file.', 'a/file ', 'a//b', 'a/*'])
def test_source_filter_rejects_private_traversal_and_windows_aliases(path):
    with pytest.raises(exporter.PublicationError):exporter.safe_relative(path)


@pytest.mark.parametrize('fault', ['changed_hash','secret','private_path','duplicate','extra_field'])
def test_source_filter_checks_all_inputs_before_any_output(tmp_path, fault):
    root=tmp_path/'source';root.mkdir()
    records=[_file(root,'src/main.py')]
    if fault=='changed_hash':(root/'src/main.py').write_bytes(b'changed')
    elif fault=='secret':records.append(_file(root,'src/secret.txt', b'-----BEGIN '+b'PRIVATE KEY-----'))
    elif fault=='private_path':records.append(_file(root,'src/private.txt',b'C:/Users/RealOwner/private'))
    elif fault=='duplicate':records.append({**records[0],'target':'SRC/MAIN.PY'})
    else:records[0]['unknown']=True
    output=tmp_path/'filtered'
    with pytest.raises(exporter.PublicationError):
        exporter.copy_allowlisted_tree(root,output,records,private_roots=('C:/Users/RealOwner',))
    assert not output.exists()


@pytest.mark.parametrize('data',[b'gho_'+b'X'*36,b'AKIA'+b'A'*16,b'sk-'+b'X'*30,
    b'C:/Users/RealOwner/private',b'C:\\\\Users\\\\RealOwner\\\\private'])
def test_credential_and_escaped_private_path_scan(data):
    with pytest.raises(exporter.PublicationError):
        exporter.scan_forbidden_bytes(data,private_roots=('C:\\Users\\RealOwner',))


def test_verified_public_format_validator_is_not_key_material():
    data = (ROOT/'tests/fixtures/public-format-literals/jose-6.2.3-import.js').read_bytes()
    assert hashlib.sha256(data).hexdigest() == 'b4e122bd70624cdbca8ca2e002e85540ac6f20e2c5c72c2b4b93e8e8ba4f2f5d'
    exporter.scan_forbidden_bytes(data)
    exporter.scan_stream(io.BytesIO(data))


@pytest.mark.parametrize('extra', [b'\n', b'gho_'+b'X'*36, b'\n-----BEGIN '+b'PRIVATE KEY-----\nsecret'])
def test_public_format_validator_exemption_rejects_every_changed_file(extra):
    data = (ROOT/'tests/fixtures/public-format-literals/jose-6.2.3-import.js').read_bytes()+extra
    with pytest.raises(exporter.PublicationError, match='credential'):
        exporter.scan_forbidden_bytes(data)
    with pytest.raises(exporter.PublicationError, match='credential'):
        exporter.scan_stream(io.BytesIO(data))


def test_public_format_validator_does_not_exempt_private_paths():
    data = (ROOT/'tests/fixtures/public-format-literals/jose-6.2.3-import.js').read_bytes()
    with pytest.raises(exporter.PublicationError, match='private workspace'):
        exporter.scan_forbidden_bytes(data, private_roots=('importPKCS8',))


def test_source_filter_copies_only_explicit_bytes_without_history(tmp_path):
    root=tmp_path/'source';root.mkdir()
    record=_file(root,'src/main.py')
    (root/'.git').mkdir();(root/'.git/config').write_bytes(b'private history')
    result=exporter.copy_allowlisted_tree(root,tmp_path/'filtered',[record])
    assert result['history_included'] is False and result['publication_commit'] is None
    assert (tmp_path/'filtered/src/main.py').read_bytes()==b'public code'
    assert not (tmp_path/'filtered/.git').exists()


def test_source_filter_refuses_reparse_point(tmp_path):
    root=tmp_path/'source';root.mkdir();(root/'target.txt').write_bytes(b'public')
    link=root/'alias.txt'
    try:link.symlink_to(root/'target.txt')
    except OSError:
        # Windows developer mode may be unavailable; a junction exercises the same lstat gate.
        directory=root/'target';directory.mkdir();(directory/'file.txt').write_bytes(b'public')
        junction=root/'junction'
        subprocess.run(['cmd','/c','mklink','/J',str(junction),str(directory)],check=True,capture_output=True)
        with pytest.raises(exporter.PublicationError):exporter.checked_file(root,'junction/file.txt')
    else:
        with pytest.raises(exporter.PublicationError):exporter.checked_file(root,'alias.txt')


def _tar(files):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as handle:
        for name,data in files.items():
            member=tarfile.TarInfo(name);member.size=len(data);handle.addfile(member,io.BytesIO(data))
    return buffer.getvalue()


def _image(tmp_path, layers):
    names=[f'{i}/layer.tar' for i in range(len(layers))]
    files={'manifest.json':json.dumps([{'Layers':names}]).encode()}
    files.update({name:_tar(layer) for name,layer in zip(names,layers)})
    path=tmp_path/'image.tar';path.write_bytes(_tar(files));return path


def test_layer_scan_detects_secret_even_after_whiteout(tmp_path):
    image=_image(tmp_path,[{'tmp/key.pem':b'-----BEGIN '+b'PRIVATE KEY-----'}, {'tmp/.wh.key.pem':b''}])
    with pytest.raises(exporter.PublicationError,match='credential'):exporter.scan_image_archive(image)


@pytest.mark.parametrize('fault',['missing','changed','deleted'])
def test_final_image_grants_cannot_be_missing_changed_or_deleted(tmp_path, fault):
    name='usr/share/doc/plwc/LICENSE';required={name:b'approved license'}
    layers=[{name:b'approved license'}]
    if fault=='missing':layers=[{'usr/share/doc/other.txt':b'other'}]
    elif fault=='changed':layers.append({name:b'altered license'})
    else:layers.append({'usr/share/doc/plwc/.wh.LICENSE':b''})
    with pytest.raises(exporter.PublicationError):exporter.scan_image_archive(_image(tmp_path,layers),required_files=required)


def test_layer_scan_checks_every_layer_and_actual_grants(tmp_path):
    required={'usr/share/doc/plwc/LICENSE':b'approved'}
    result=exporter.scan_image_archive(_image(tmp_path,[{'etc/base.txt':b'base'},required]),required_files=required)
    assert result['layers_inspected']==2 and result['required_files_checked']==list(required)


@pytest.mark.parametrize('image_id',['document_worker','node_runner','python_runner'])
def test_actual_allowlisted_context_contains_exact_three_grants(tmp_path,image_id):
    image=next(x for x in json.loads((ROOT/'docker/runtime-image-sources.json').read_text())['images'] if x['id']==image_id)
    result=builder.prepare_image_context(image,tmp_path/'context')
    for name in auditor.PERSONAL_GRANTS:
        assert (tmp_path/'context/plwc-licenses'/name).read_bytes()==(ROOT/name).read_bytes()
    assert not any('/.git/' in x['path'] or 'node_modules' in x['path'] for x in result['files'])


@pytest.mark.parametrize('fault',['unexpected','reparse','credential'])
def test_context_filter_stops_before_builder_for_unsafe_source(tmp_path,monkeypatch,fault):
    root=tmp_path/'source';root.mkdir()
    _file(root,'docker/node-runner/Dockerfile',b'FROM pinned')
    for name in auditor.PERSONAL_GRANTS:_file(root,name,b'approved')
    _file(root,'docker/generate-runtime-notices.mjs',b'public')
    policy=json.loads((ROOT/'docker/runtime-context-files.json').read_text())
    # Supply every current allowlisted input before injecting the unsafe entry.
    # Otherwise a newly added notice masks the security assertion with ENOENT.
    for source in policy['images']['node_runner']['files'].values():
        if not (root/source).exists():_file(root,source,b'approved')
    _file(root,'docker/runtime-context-files.json',json.dumps(policy).encode())
    if fault=='unexpected':_file(root,'docker/node-runner/unknown.txt')
    elif fault=='credential':_file(root,'docker/node-runner/Dockerfile',b'-----BEGIN '+b'PRIVATE KEY-----')
    else:
        target=tmp_path/'target';target.mkdir()
        subprocess.run(['cmd','/c','mklink','/J',str(root/'docker/node-runner/junction'),str(target)],check=True,capture_output=True)
    monkeypatch.setattr(builder,'ROOT',root)
    with pytest.raises(exporter.PublicationError):builder.prepare_image_context({'id':'node_runner','context':'docker/node-runner'},tmp_path/'out')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('fault',['none','source','policy','image'])
def test_context_is_bound_to_actual_frozen_git_bytes(tmp_path,monkeypatch,fault):
    image={'id':'node_runner','context':'docker/node-runner'}
    inputs={'docker/runtime-context-files.json':b'{"schema_version":"1.0.0"}',
        'docker/runtime-image-sources.json':json.dumps({'images':[image]}).encode(),
        'docker/node-runner/Dockerfile':b'FROM exact frozen base'}
    for name,data in inputs.items():_file(tmp_path,name,data)
    report={'source_inputs':[{'path':'docker/node-runner/Dockerfile','target':'Dockerfile',
        'sha256':hashlib.sha256(inputs['docker/node-runner/Dockerfile']).hexdigest()}]}
    if fault=='source':report['source_inputs'][0]['sha256']='f'*64
    elif fault=='policy':(tmp_path/'docker/runtime-context-files.json').write_bytes(b'changed')
    elif fault=='image':image={**image,'foreign':'changed'}
    def read(argv,**kwargs):
        assert argv[:2]==['git','show'] and argv[2].startswith('a'*40+':')
        return subprocess.CompletedProcess(argv,0,stdout=inputs[argv[2].split(':',1)[1]],stderr=b'')
    monkeypatch.setattr(builder,'ROOT',tmp_path)
    if fault=='none':builder.verify_context_commit(image,report,'a'*40,runner=read)
    else:
        with pytest.raises(exporter.PublicationError):builder.verify_context_commit(image,report,'a'*40,runner=read)


def test_filtered_source_cannot_inherit_parent_development_git_identity(tmp_path,monkeypatch):
    source=tmp_path/'filtered-source';source.mkdir()
    monkeypatch.setattr(builder,'ROOT',source)
    monkeypatch.setattr(builder,'_git',lambda *_args:str(tmp_path))
    with pytest.raises(RuntimeError,match='parent development history'):builder._source_identity(False)


def _descriptor(digest):
    return {'digest':digest,'raw_sha256':digest[7:],'config_digest':'sha256:'+'b'*64,
        'media_type':'application/vnd.oci.image.manifest.v1+json','download_bytes':2560,
        'layers':[{'digest':'sha256:'+'c'*64,'size':2048}]}


@pytest.mark.parametrize('fault',['none','approval','public_source','public_target','digest','layer','tag'])
def test_private_promotion_has_exact_approval_and_preserves_bytes(fault):
    digest='sha256:'+'a'*64;plan=promotion.promotion_plan('node-runner',digest)
    approval={'action':'private_image_promotion','plan_id':plan['plan_id'],'approved':True,'approved_by':'synthetic-owner'}
    if fault=='approval':approval['plan_id']='changed'
    calls=[]
    def inspect(ref,**kwargs):
        result=_descriptor(digest)
        if fault=='digest' and 'staging' in ref:result['raw_sha256']='d'*64
        if fault=='layer' and 'staging' not in ref:result['layers']=[{'digest':'sha256:'+'e'*64,'size':2048}]
        if fault=='tag' and ref.endswith(':1.0.0'):result['digest']='sha256:'+'f'*64
        return result
    def visible(repo):
        if fault=='public_source' and 'staging' in repo:return 'public'
        if fault=='public_target' and 'staging' not in repo:return 'public'
        return 'private'
    def run(argv,**kwargs):calls.append(argv)
    if fault=='none':
        assert promotion.promote(plan,approval,runner=run,inspector=inspect,visibility=visible)['status']=='pass'
        assert calls==[plan['argv']] and '--prefer-index=false' in calls[0]
        assert 'build' not in calls[0]
    else:
        with pytest.raises(promotion.VerificationError):promotion.promote(plan,approval,runner=run,inspector=inspect,visibility=visible)
        if fault in {'approval','public_source','public_target','digest'}:assert calls==[]


def _snapshot(tmp_path,kind='source'):
    record=_file(tmp_path,'captured/public.txt',b'reviewed public metadata')
    content={'path':record['path'],'sha256':record['sha256']}
    required=auditor.SOURCE_SURFACES if kind=='source' else auditor.PACKAGE_SURFACES
    surfaces={name:[{'cursor':None,'next_cursor':None,'total_count':0,'items':[],'capture':content}] for name in required}
    surface='refs' if kind=='source' else 'versions'
    surfaces[surface][0].update(total_count=1,items=[{'id':'known','content':[content]}])
    subject='mhoedt-ai/PLwC-Personal' if kind=='source' else 'ghcr.io/mhoedt-ai/plwc-personal-node-runner'
    snapshot={'kind':kind,'subject':subject,'visibility':'private','publication_commit':'a'*40,
        'surfaces':surfaces,'writer_freeze':{'active':True,'publication_commit':'a'*40,'evidence':content}}
    approved={'subject':snapshot['subject'],'publication_commit':'a'*40,'reviewed_by':'synthetic-reviewer',
        'items':{surface+':known':[record['sha256']]}}
    return snapshot,approved


@pytest.mark.parametrize('kind',['source','package'])
@pytest.mark.parametrize('fault',['none','missing_surface','unknown_surface','unknown_item','unreadable','pagination','changed_content','freeze','commit','missing_capture','foreign_subject'])
def test_full_captured_surface_requires_complete_reviewed_bytes(tmp_path,kind,fault):
    snapshot,approved=_snapshot(tmp_path,kind)
    key='refs' if kind=='source' else 'versions'
    if fault=='missing_surface':snapshot['surfaces'].pop('attachments')
    elif fault=='unknown_surface':snapshot['surfaces']['unknown']=[]
    elif fault=='unknown_item':snapshot['surfaces'][key][0]['items'][0]['id']='unknown'
    elif fault=='unreadable':snapshot['surfaces'][key][0]['items'][0]['content']=[]
    elif fault=='pagination':snapshot['surfaces'][key][0]['next_cursor']='missing-page'
    elif fault=='changed_content':(tmp_path/'captured/public.txt').write_bytes(b'changed')
    elif fault=='freeze':snapshot['writer_freeze']['active']=False
    elif fault=='commit':snapshot['publication_commit']='b'*40
    elif fault=='missing_capture':snapshot['surfaces']['attachments'][0].pop('capture')
    elif fault=='foreign_subject':snapshot['subject']=approved['subject']='foreign/project'
    if fault=='none':
        result=auditor.audit_surface(snapshot,approved,tmp_path)
        assert result['status']=='captured_inventory_pass' and result['publication_authorized'] is False
        assert result['live_recollection_required_before_publication'] is True
    else:
        with pytest.raises((exporter.PublicationError,OSError)):auditor.audit_surface(snapshot,approved,tmp_path)


def test_pagination_accepts_complete_two_pages_and_rejects_unterminated_or_cyclic():
    pages=[{'cursor':None,'next_cursor':'two','total_count':2,'items':[{'id':'1'}],'capture':{}},
        {'cursor':'two','next_cursor':None,'total_count':2,'items':[{'id':'2'}],'capture':{}}]
    assert len(auditor.all_pages(pages))==2
    for changed in (pages[:1],[pages[0],{**pages[1],'next_cursor':'two'}],
        [pages[0],{**pages[1],'cursor':'wrong'}],[pages[0],{**pages[1],'total_count':3}]):
        with pytest.raises(exporter.PublicationError):auditor.all_pages(changed)


@pytest.mark.parametrize('fault',['none','untagged_private','unknown_referrer','missing_child'])
def test_package_graph_includes_untagged_versions_and_referrers(fault):
    versions=[{'id':1,'digest':'sha256:'+'a'*64,'tags':['1.0.0']}]
    graph={'sha256:'+'a'*64:{'children':['sha256:'+'b'*64],'referrers':['sha256:'+'c'*64]},
        'sha256:'+'b'*64:{'children':[],'referrers':[]},'sha256:'+'c'*64:{'children':[],'referrers':[]}}
    allowed=set(graph)
    if fault=='untagged_private':versions.append({'id':2,'digest':'sha256:'+'d'*64,'tags':[]})
    elif fault=='unknown_referrer':graph['sha256:'+'a'*64]['referrers'].append('sha256:'+'e'*64)
    elif fault=='missing_child':graph.pop('sha256:'+'b'*64)
    if fault=='none':auditor.verify_manifest_graph(versions,graph,allowed)
    else:
        with pytest.raises(exporter.PublicationError):auditor.verify_manifest_graph(versions,graph,allowed)


def test_package_graph_does_not_accept_a_non_digest_identity():
    with pytest.raises(exporter.PublicationError,match='invalid digest'):
        auditor.verify_manifest_graph([{'id':1,'digest':'mutable-tag','tags':[]}],
            {'mutable-tag':{'children':[],'referrers':[]}}, {'mutable-tag'})
