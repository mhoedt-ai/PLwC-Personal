"""Plan or perform one explicitly approved, byte-preserving private image promotion."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from finalize_runtime_image_manifest import inspect_remote_image
from verify_runtime_images import VerificationError

COMPONENTS=('document-worker','node-runner','python-runner')
DIGEST=re.compile(r'^sha256:[0-9a-f]{64}$')


def promotion_plan(component: str, digest: str) -> dict:
    if component not in COMPONENTS or not DIGEST.fullmatch(digest):
        raise VerificationError('Unknown promotion subject')
    source=f'ghcr.io/mhoedt-ai/plwc-personal-private-staging-{component}@{digest}'
    target=f'ghcr.io/mhoedt-ai/plwc-personal-{component}:1.0.0'
    argv=['docker','buildx','imagetools','create','--prefer-index=false','--tag',target,source]
    plan={'component':component,'digest':digest,'source':source,'target':target,'argv':argv,
        'required_action':'private_image_promotion','requires_separate_product_owner_approval':True}
    plan['plan_id']=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return plan


def package_visibility(repository: str, *, runner=subprocess.run) -> str:
    name=repository.rsplit('/',1)[1]
    result=runner(['gh','api',f'/users/mhoedt-ai/packages/container/{name}'],capture_output=True,check=True)
    data=json.loads(result.stdout)
    if data.get('name')!=name or data.get('package_type')!='container' or data.get('visibility') not in {'private','public'}:
        raise VerificationError('Package identity or visibility is unknown')
    return data['visibility']


def promote(plan: dict, approval: dict, *, runner=subprocess.run, inspector=inspect_remote_image, visibility=package_visibility) -> dict:
    expected=promotion_plan(plan.get('component',''),plan.get('digest',''))
    if plan!=expected:raise VerificationError('Promotion plan changed')
    if approval.get('action')!='private_image_promotion' or approval.get('plan_id')!=plan['plan_id'] or approval.get('approved') is not True or not approval.get('approved_by'):
        raise VerificationError('Exact promotion has no separate owner approval')
    source_repo=plan['source'].split('@')[0];target_repo=plan['target'].rsplit(':',1)[0]
    if visibility(source_repo)!='private' or visibility(target_repo)!='private':
        raise VerificationError('Both promotion packages must remain private')
    before=inspector(plan['source'],runner=runner)
    if before['digest']!=plan['digest'] or 'sha256:'+before['raw_sha256']!=plan['digest']:
        raise VerificationError('Source bytes do not match approved digest')
    runner(plan['argv'],check=True,capture_output=True)
    target=f"{target_repo}@{plan['digest']}"
    after=inspector(target,runner=runner)
    tagged=inspector(plan['target'],runner=runner)
    fields=['digest','raw_sha256','config_digest','media_type','download_bytes','layers']
    if any(before.get(key)!=after.get(key) for key in fields):
        raise VerificationError('Promotion changed manifest config or layer bytes')
    if any(before.get(key)!=tagged.get(key) for key in fields):
        raise VerificationError('Promoted tag does not name the approved bytes')
    if visibility(source_repo)!='private' or visibility(target_repo)!='private':
        raise VerificationError('Package visibility changed during promotion')
    return {'status':'pass','plan_id':plan['plan_id'],'source':plan['source'],'target':target,
        'raw_sha256':after['raw_sha256'],'config_digest':after['config_digest'],'layers':after['layers']}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--component',choices=COMPONENTS,required=True);p.add_argument('--digest',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--approval',type=Path)
    args=p.parse_args();plan=promotion_plan(args.component,args.digest)
    if args.execute:
        if args.approval is None:p.error('--execute requires the exact separately approved record')
        result=promote(plan,json.loads(args.approval.read_text(encoding='utf-8')))
    else:result=plan
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
