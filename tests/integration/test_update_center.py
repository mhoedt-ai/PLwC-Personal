from __future__ import annotations

import base64
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from plwc_gateway.installation.update_center import (
    PERSONAL_MANIFEST_URL,
    _verify_rsa_sha256_pkcs1v15,
    load_trusted_release_keys,
    rsa_public_key_id,
    MAX_MANIFEST_BYTES,
    UpdateCenter,
    UpdateConfirmationRequired,
    UpdateContractError,
    UpdateFetchError,
    UpdateSecurityError,
    _validate_release_manifest,
    canonical_manifest_bytes,
    parse_manifest_json,
    verify_release_manifest,
)


ARTIFACT = base64.b64decode("UEx3QyByMjYgc2lnbmVkIGFydGlmYWN0IGZpeHR1cmUNCg==")
TEST_KEY_ID = "r26-test-only"
TEST_TRUSTED_KEYS = {
    TEST_KEY_ID: {
        "exponent": 65537,
        "modulus": int(
            "bcfdcd2ad3b67e0462a79e20eb80ef769d999408ca5c34599c4ceaf1f23aba10"
            "1dbd83d78cb3a752cf65bfea5dc9cc1e5505de817663ddfeffa1949fe6795baa1"
            "be20307e758c26cb7c4ff8c4b1c2d67526319fcc9fa89602428dbca2985b742af"
            "33c2ab3115606aa1525787e6f803181410b1ee46ee5768f6fa87afcaed7d3495e"
            "c3c45e854d405c3ea09a0dd37f9ff6f47d9d7fca08af982f2856fca345b0544e"
            "46f2ac6e80d801a357fc5f1ea0cd000ad19ff013c015a456feacde5118c280e55"
            "d917c0c9a4fc0a3fbfcb82fae6172ef4f1446cf76f3d022c29124f35537718118"
            "697086500f2a926306a4fc34ba254a1c47059cab9aa6ade547cae354ded",
            16,
        ),
    }
}
SIGNATURE = (
    "ErUDfAto4HwdjTpZnQtdsbsSSs9j3ZuB7QCjEaEbpWHoB4N+OE4LK0+wAV6y6p3A"
    "t3GTWPaJLrdtoG9bN1dMxBj7Pa3Vi7Tq4fmLShOT2pkGsL8FkN2XhcV8K/nFzVeG"
    "xMR5EYsinBzoQMhdYayQ765DmYKH/UGVAxr2dEhoGxbyleMLSTCeWqZYYo32W7/jM"
    "ko8SYSjQatVlJ3dfqgZyIsd7j/+BqWTu0696nVU2RimVN2whDIStsDQKFDOB3zlij"
    "cRtqNJSTi/8L8nLsv8YMP4ie8NYwIFs3b74oEc4lhQ3Jp9f6mYGjVbo+HdeqDq/9"
    "p/wAMFyqw0kp2kTo70rQ=="
)
MANIFEST_URL = "https://updates.example.invalid/plwc-release-manifest.json"
ARTIFACT_URL = "https://updates.example.invalid/PLwC-Setup-1.0.0-installer-r26.exe"


def legacy_signed_manifest() -> dict[str, object]:
    digest = "9817cccdef34917e8d281154355cb32dad2bd9e7d6a09d20897296b4cf98ca2b"
    return {
        "schema_version": "1.0.0",
        "product": {"name": "PLwC", "version": "1.0.0", "installer_revision": "installer-r26"},
        "release": {
            "published_at": "2026-09-03T10:00:00+00:00",
            "update_kind": "recommended",
            "notes": {"de": "Sichere Testfreigabe.", "en": "Secure test release."},
        },
        "components": [
            {
                "id": "gateway",
                "version": "1.0.0",
                "compatibility": {"minimum": "1.0.0", "maximum_exclusive": "1.1.0"},
            },
            {
                "id": "browser_extension",
                "version": "1.0.1",
                "compatibility": {"minimum": "1.0.0", "maximum_exclusive": "1.1.0"},
            },
        ],
        "artifacts": [
            {
                "id": "windows_installer",
                "kind": "windows_installer",
                "file_name": "PLwC-Setup-1.0.0-installer-r26.exe",
                "url": ARTIFACT_URL,
                "size": len(ARTIFACT),
                "sha256": digest,
                "build_identity": {
                    "schema_version": 1,
                    "build_id": f"plwc@1.0.0/installer-r26#sha256:{digest}",
                    "product_version": "1.0.0",
                    "installer_revision": "installer-r26",
                    "sha256": digest,
                },
            }
        ],
        "signature": {
            "algorithm": "rsa-sha256-pkcs1v15",
            "key_id": TEST_KEY_ID,
            "value_base64": SIGNATURE,
        },
    }


LEGACY_VECTOR = legacy_signed_manifest()
LEGACY_KEYS = copy.deepcopy(TEST_TRUSTED_KEYS)

# Independent signing implementation; key exists only in test process memory.
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

_TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=3072)
_TEST_PUBLIC = _TEST_PRIVATE_KEY.public_key().public_numbers()
import hashlib
TEST_KEY_ID = "plwc-personal-rsa-" + hashlib.sha256(_TEST_PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).hexdigest()
TEST_TRUSTED_KEYS = {TEST_KEY_ID: {"exponent": _TEST_PUBLIC.e, "modulus": _TEST_PUBLIC.n}}
MANIFEST_URL = PERSONAL_MANIFEST_URL
ARTIFACT_URL = "https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.1.0/PLwC-Setup-1.1.0-installer-r26.exe"


def resign(manifest: dict) -> dict:
    manifest["signature"] = {"algorithm": "rsa-sha256-pkcs1v15", "key_id": TEST_KEY_ID,
        "value_base64": base64.b64encode(_TEST_PRIVATE_KEY.sign(
            canonical_manifest_bytes(manifest), padding.PKCS1v15(), hashes.SHA256())).decode()}
    return manifest


def signed_manifest() -> dict:
    result = copy.deepcopy(LEGACY_VECTOR)
    result["product"]["name"] = "PLwC Personal"
    result["product"]["version"] = "1.1.0"
    result["release"].update(manifest_sequence=1, status="active")
    result["artifacts"][0].update(url=ARTIFACT_URL, file_name="PLwC-Setup-1.1.0-installer-r26.exe")
    result["artifacts"][0]["build_identity"]["product_version"] = "1.1.0"
    return resign(result)


def manifest_bytes(manifest: dict[str, object] | None = None) -> bytes:
    return json.dumps(manifest or signed_manifest(), ensure_ascii=False, sort_keys=True).encode("utf-8")


class FixtureFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.offline = False
        self.artifact = ARTIFACT
        self.manifest = manifest_bytes()

    def __call__(self, url: str, maximum_bytes: int) -> bytes:
        self.calls.append(url)
        if self.offline:
            raise UpdateFetchError("offline fixture")
        payload = self.manifest if url == MANIFEST_URL else self.artifact
        assert len(payload) <= maximum_bytes
        return payload


def test_signed_manifest_verifies_and_canonical_form_excludes_only_signature() -> None:
    manifest = parse_manifest_json(manifest_bytes())
    verified = verify_release_manifest(manifest, TEST_TRUSTED_KEYS)

    assert verified["product"]["installer_revision"] == "installer-r26"
    assert len(verified["components"]) == 2
    assert b'"signature"' not in canonical_manifest_bytes(verified)
    legacy_key = next(iter(LEGACY_KEYS.values()))
    assert _verify_rsa_sha256_pkcs1v15(canonical_manifest_bytes(LEGACY_VECTOR), base64.b64decode(SIGNATURE), **legacy_key)
    assert rsa_public_key_id(_TEST_PUBLIC.n, _TEST_PUBLIC.e) == TEST_KEY_ID


def test_tampered_or_untrusted_manifest_is_rejected() -> None:
    tampered = signed_manifest()
    tampered["release"]["update_kind"] = "required"

    with pytest.raises(UpdateSecurityError, match="signature verification failed"):
        verify_release_manifest(tampered, TEST_TRUSTED_KEYS)
    with pytest.raises(UpdateSecurityError, match="untrusted key"):
        verify_release_manifest(signed_manifest(), {})


def test_personal_center_rejects_signed_legacy_product_and_cached_plan(tmp_path: Path) -> None:
    fetcher = FixtureFetcher()
    state_root = tmp_path / "state"
    update_root = state_root / "updates"
    update_root.mkdir(parents=True)
    (update_root / "last-valid-manifest.json").write_text(json.dumps(LEGACY_VECTOR))
    (update_root / "status.json").write_text(json.dumps({"release": {"product": {"name": "PLwC"}}}))
    fetcher.manifest = json.dumps(LEGACY_VECTOR).encode()

    personal = UpdateCenter(
        state_root=state_root,
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        expected_product_name="PLwC Personal",
        fetch_bytes=fetcher,
    )
    assert personal.snapshot()["state"] == "rejected"
    assert personal.snapshot()["cached_release_available"] is False
    with pytest.raises(UpdateSecurityError, match="different product"):
        personal.plan_download("windows_installer")
    rejected = personal.check()
    assert rejected["state"] == "rejected"
    assert rejected["cached_release_available"] is False


def test_manifest_rejects_unsafe_or_mismatched_installer_revision() -> None:
    unsafe = signed_manifest()
    unsafe["product"]["installer_revision"] = "../installer-r27"
    with pytest.raises(UpdateContractError, match="installer revision"):
        _validate_release_manifest(unsafe)

    mismatch = signed_manifest()
    mismatch["artifacts"][0]["build_identity"]["installer_revision"] = "installer-r27"
    with pytest.raises(UpdateSecurityError, match="revisions do not match"):
        _validate_release_manifest(mismatch)


def test_duplicate_json_members_and_non_https_artifacts_fail_closed() -> None:
    with pytest.raises(Exception, match="Duplicate JSON member"):
        parse_manifest_json(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    unsafe = copy.deepcopy(signed_manifest())
    unsafe["artifacts"][0]["url"] = "http://updates.example.invalid/setup.exe"
    with pytest.raises(UpdateSecurityError):
        verify_release_manifest(unsafe, TEST_TRUSTED_KEYS)


def test_check_is_interval_limited_and_offline_keeps_last_verified_result(tmp_path: Path) -> None:
    now = [datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)]
    fetcher = FixtureFetcher()
    center = UpdateCenter(
        state_root=tmp_path / "state",
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        fetch_bytes=fetcher,
        clock=lambda: now[0],
    )

    current = center.check()
    assert current["state"] == "update_available"
    assert current["update_kind"] == "recommended"
    assert current["integrity_verified"] is True
    assert current["check_due"] is False
    assert fetcher.calls == [MANIFEST_URL]

    assert center.check()["state"] == "update_available"
    assert fetcher.calls == [MANIFEST_URL]

    now[0] += timedelta(hours=7)
    fetcher.offline = True
    offline = center.check()
    assert offline["state"] == "offline"
    assert offline["cached_release_available"] is True
    assert offline["last_valid_at"] == current["last_valid_at"]
    assert offline["last_checked_at"] != offline["last_valid_at"]


def test_tampered_live_manifest_never_replaces_verified_cache(tmp_path: Path) -> None:
    fetcher = FixtureFetcher()
    center = UpdateCenter(
        state_root=tmp_path / "state",
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        fetch_bytes=fetcher,
    )
    center.check(force=True)
    cached_before = center.manifest_path.read_bytes()
    tampered = signed_manifest()
    tampered["product"]["installer_revision"] = "installer-r99"
    fetcher.manifest = manifest_bytes(tampered)

    rejected = center.check(force=True)

    assert rejected["state"] == "rejected"
    assert rejected["integrity_verified"] is False
    assert rejected["cached_release_available"] is True
    assert center.manifest_path.read_bytes() == cached_before


def test_download_and_install_require_separate_confirmation_and_reverify_hash(tmp_path: Path) -> None:
    fetcher = FixtureFetcher()
    state_root = tmp_path / "state"
    center = UpdateCenter(
        state_root=state_root,
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        fetch_bytes=fetcher,
    )
    center.check(force=True)
    plan = center.plan_download("windows_installer")

    with pytest.raises(UpdateConfirmationRequired, match="download"):
        center.download(plan["plan_id"], confirmed=False)
    assert fetcher.calls == [MANIFEST_URL]

    downloaded = center.download(plan["plan_id"], confirmed=True)
    assert downloaded["state"] == "download_verified"
    assert Path(downloaded["artifact_path"]).read_bytes() == ARTIFACT

    runner_calls: list[Path] = []
    with pytest.raises(UpdateConfirmationRequired, match="installation"):
        center.install(plan["plan_id"], confirmed=False, runner=lambda path: 0)
    assert runner_calls == []

    completed = center.install(
        plan["plan_id"],
        confirmed=True,
        runner=lambda path: runner_calls.append(path) or 0,
    )
    assert completed["state"] == "installer_completed"
    assert completed["build_identity_verified"] is True
    assert runner_calls == [Path(downloaded["artifact_path"])]


@pytest.mark.parametrize("artifact", [b"x" * len(ARTIFACT), ARTIFACT[:-1]])
def test_wrong_hash_or_interrupted_download_is_rejected_and_not_installed(
    tmp_path: Path,
    artifact: bytes,
) -> None:
    fetcher = FixtureFetcher()
    center = UpdateCenter(
        state_root=tmp_path / "state",
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        fetch_bytes=fetcher,
    )
    center.check(force=True)
    plan = center.plan_download("windows_installer")
    fetcher.artifact = artifact

    with pytest.raises(UpdateSecurityError, match="size|hash"):
        center.download(plan["plan_id"], confirmed=True)

    assert not list(center.download_root.glob("*.exe"))
    assert not list(center.download_root.glob("*.part"))


def test_failed_installer_surfaces_matching_revision_rollback_report(tmp_path: Path) -> None:
    fetcher = FixtureFetcher()
    state_root = tmp_path / "state"
    center = UpdateCenter(
        state_root=state_root,
        logs_root=tmp_path / "configured-logs",
        manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS,
        fetch_bytes=fetcher,
    )
    center.check(force=True)
    plan = center.plan_download("windows_installer")
    center.download(plan["plan_id"], confirmed=True)
    rollback_report = tmp_path / "configured-logs" / "setup" / "r26-installer-rollback.json"
    rollback_report.parent.mkdir(parents=True)

    def failed_install(_path: Path) -> int:
        rollback_report.write_text('{"rollback":"completed"}\n', encoding="utf-8")
        return 1603

    failed = center.install(plan["plan_id"], confirmed=True, runner=failed_install)

    assert failed["ok"] is False
    assert failed["state"] == "installer_failed"
    assert failed["return_code"] == 1603
    assert failed["postflight_delegated_to"] == "installer-r26"
    assert failed["rollback_report"] == str(rollback_report)

    stale = center.install(plan["plan_id"], confirmed=True, runner=lambda _path: 1603)
    assert stale["rollback_report"] is None


def center_fixture(tmp_path: Path, fetcher: FixtureFetcher | None = None, **kwargs):
    fetcher = fetcher or FixtureFetcher()
    return UpdateCenter(state_root=tmp_path / "state", manifest_url=MANIFEST_URL,
        trusted_keys=TEST_TRUSTED_KEYS, fetch_bytes=fetcher, **kwargs), fetcher


@pytest.mark.parametrize("location", [(), ("product",), ("release",), ("release","notes"),
    ("components",0), ("components",0,"compatibility"), ("artifacts",0),
    ("artifacts",0,"build_identity"), ("signature",)])
def test_unknown_members_rejected_by_schema_and_runtime(location) -> None:
    from jsonschema import Draft202012Validator
    manifest = signed_manifest()
    target = manifest
    for key in location: target = target[key]
    target["unexpected"] = "fixture"
    schema = json.loads((Path(__file__).parents[2]/"config/release-manifest.schema.json").read_text())
    assert list(Draft202012Validator(schema).iter_errors(manifest))
    with pytest.raises(UpdateContractError, match="unknown fields"):
        _validate_release_manifest(manifest)


@pytest.mark.parametrize("field,value", [("sequence",True),("sequence",1.0),("sequence",0),
    ("sequence",-1),("sequence","1"),("status",[]),("status","missing"),("kind",{}),
    ("identity_schema",True),("hash","A"*64),("version"," 1.1.0 "),("size",True),
    ("date","2026-09-03"),("date","2026-99-01T10:00:00Z")])
def test_strict_types_formats_and_nonfinite_numbers(field,value) -> None:
    manifest = signed_manifest()
    if field=='sequence':manifest['release']['manifest_sequence']=value
    elif field=='status':manifest['release']['status']=value
    elif field=='kind':manifest['release']['update_kind']=value
    elif field=='date':manifest['release']['published_at']=value
    elif field=='identity_schema':manifest['artifacts'][0]['build_identity']['schema_version']=value
    elif field=='hash':manifest['artifacts'][0]['sha256']=value
    elif field=='size':manifest['artifacts'][0]['size']=value
    elif field=='version':manifest['product']['version']=value
    with pytest.raises(UpdateContractError):_validate_release_manifest(manifest)


@pytest.mark.parametrize('raw',[b'{"n":NaN}',b'{"n":Infinity}',b'{"n":-Infinity}'])
def test_parser_rejects_nonfinite_json(raw) -> None:
    with pytest.raises(UpdateContractError):parse_manifest_json(raw)


@pytest.mark.parametrize('url', ['http://github.com/setup.exe','https://example.invalid/setup.exe',
    'https://github.com/mhoedt-ai/PLwC-Personal/releases/latest/setup.exe',
    ARTIFACT_URL+'?token=fixture',ARTIFACT_URL.replace('/v1.1.0/','/v1.0.0/'),
    ARTIFACT_URL.replace('github.com','user:pass@github.com'),ARTIFACT_URL+'#fragment'])
def test_immutable_artifact_source_enforced(url) -> None:
    manifest=signed_manifest();manifest['artifacts'][0]['url']=url
    with pytest.raises(UpdateSecurityError):_validate_release_manifest(manifest)


def test_independent_canonical_unicode_vector() -> None:
    assert canonical_manifest_bytes({'z':{'b':2,'a':'Ä'},'signature':{'anything':True},'a':1}) == b'{"a":1,"z":{"a":"\xc3\x84","b":2}}'


def test_product_and_artifact_versions_must_match() -> None:
    manifest=signed_manifest();manifest['artifacts'][0]['build_identity']['product_version']='1.2.0'
    with pytest.raises(UpdateSecurityError,match='versions do not match'):_validate_release_manifest(manifest)


@pytest.mark.parametrize('url', [PERSONAL_MANIFEST_URL,
    'https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.0.0/plwc-personal-release-manifest.json',
    'https://release-assets.githubusercontent.com/approved-transport?signature=fixture',
    'https://objects.githubusercontent.com/approved-transport'])
def test_github_manifest_redirect_chain_remains_usable(url):
    from plwc_gateway.installation.update_center import _validate_manifest_redirect
    _validate_manifest_redirect(url)


@pytest.mark.parametrize('url', ['http://release-assets.githubusercontent.com/asset',
    'https://example.invalid/manifest.json',
    'https://github.com/foreign/repository/releases/download/v1.0.0/plwc-personal-release-manifest.json',
    'https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.0.0/other.json',
    'https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.0.0/plwc-personal-release-manifest.json?token=fixture'])
def test_manifest_redirect_cannot_move_trust_to_another_source(url):
    from plwc_gateway.installation.update_center import _validate_manifest_redirect
    with pytest.raises(UpdateSecurityError):_validate_manifest_redirect(url)


@pytest.mark.parametrize('offset',['+00:60','+24:00','-01:99'])
def test_timestamp_rejects_normalized_invalid_timezone_offset(offset):
    manifest=signed_manifest();manifest['release']['published_at']='2026-10-02T12:00:00'+offset
    with pytest.raises(UpdateContractError):_validate_release_manifest(manifest)


def test_higher_withdrawal_blocks_stale_download_without_fetching_exe(tmp_path) -> None:
    center,fetcher=center_fixture(tmp_path);center.check(force=True)
    plan=center.plan_download('windows_installer')
    withdrawn=signed_manifest();withdrawn['release'].update(manifest_sequence=2,status='withdrawn');withdrawn['artifacts']=[]
    fetcher.manifest=manifest_bytes(resign(withdrawn))
    with pytest.raises(UpdateSecurityError):center.download(plan['plan_id'],confirmed=True)
    assert ARTIFACT_URL not in fetcher.calls
    assert json.loads(center.highwater_path.read_text())['release']['manifest_sequence']==2
    fetcher.manifest=manifest_bytes()
    assert center.check(force=True)['state']=='rejected'
    assert json.loads(center.highwater_path.read_text())['release']['manifest_sequence']==2


def test_same_sequence_changed_content_and_restart_cannot_replay(tmp_path) -> None:
    center,fetcher=center_fixture(tmp_path);center.check(force=True)
    before=center.manifest_path.read_bytes()
    changed=signed_manifest();changed['release']['notes']['en']='different signed content'
    fetcher.manifest=manifest_bytes(resign(changed))
    restarted,_=center_fixture(tmp_path,fetcher)
    assert restarted.check(force=True)['state']=='rejected'
    assert center.manifest_path.read_bytes()==before
    assert restarted.plan_download('windows_installer')['artifact']['sha256']==signed_manifest()['artifacts'][0]['sha256']


@pytest.mark.parametrize('fault',['missing','corrupt'])
def test_sequence_state_loss_fails_closed(tmp_path,fault) -> None:
    center,_=center_fixture(tmp_path);center.check(force=True)
    if fault=='missing':center.highwater_path.unlink()
    else:center.highwater_path.write_text('{}')
    assert center.check(force=True)['state']=='rejected'
    with pytest.raises(UpdateContractError):center.plan_download('windows_installer')


def test_offline_download_and_start_require_live_verification(tmp_path) -> None:
    center,fetcher=center_fixture(tmp_path);center.check(force=True);plan=center.plan_download('windows_installer')
    fetcher.offline=True
    with pytest.raises(UpdateSecurityError):center.download(plan['plan_id'],confirmed=True)
    assert not center.download_root.exists()
    fetcher.offline=False;center.download(plan['plan_id'],confirmed=True);fetcher.offline=True
    calls=[]
    with pytest.raises(UpdateSecurityError):center.install(plan['plan_id'],confirmed=True,runner=lambda p:calls.append(p) or 0)
    assert calls==[]


def test_withdrawal_after_download_prevents_real_launcher(tmp_path) -> None:
    center,fetcher=center_fixture(tmp_path);center.check(force=True);plan=center.plan_download('windows_installer')
    center.download(plan['plan_id'],confirmed=True)
    withdrawn=signed_manifest();withdrawn['release'].update(manifest_sequence=2,status='withdrawn')
    fetcher.manifest=manifest_bytes(resign(withdrawn));calls=[]
    with pytest.raises(UpdateSecurityError):center.install(plan['plan_id'],confirmed=True,runner=lambda p:calls.append(p) or 0)
    assert not calls


def test_withdrawal_during_file_verification_still_prevents_launcher(tmp_path,monkeypatch):
    center,fetcher=center_fixture(tmp_path);center.check(force=True)
    plan=center.plan_download('windows_installer');center.download(plan['plan_id'],confirmed=True)
    verify=center._verify_downloaded_artifact
    def verify_then_withdraw(path,artifact):
        verify(path,artifact)
        withdrawn=signed_manifest();withdrawn['release'].update(manifest_sequence=2,status='withdrawn')
        fetcher.manifest=manifest_bytes(resign(withdrawn))
    monkeypatch.setattr(center,'_verify_downloaded_artifact',verify_then_withdraw)
    calls=[]
    with pytest.raises(UpdateSecurityError):center.install(plan['plan_id'],confirmed=True,runner=lambda p:calls.append(p) or 0)
    assert calls==[]


def test_unwritable_highwater_never_authorizes_download(tmp_path,monkeypatch):
    center,fetcher=center_fixture(tmp_path);center.check(force=True)
    plan=center.plan_download('windows_installer');write=center._atomic_write_json
    before=center.highwater_path.read_bytes()
    def protected(path,payload):
        if path==center.highwater_path:raise PermissionError('synthetic read-only state')
        write(path,payload)
    monkeypatch.setattr(center,'_atomic_write_json',protected)
    assert center.check(force=True)['state']=='rejected'
    with pytest.raises(UpdateSecurityError):center.download(plan['plan_id'],confirmed=True)
    assert center.highwater_path.read_bytes()==before
    assert ARTIFACT_URL not in fetcher.calls and not center.download_root.exists()


@pytest.mark.parametrize('action',['download','install'])
def test_download_junction_cannot_write_or_launch_outside_owned_state(tmp_path,action):
    import subprocess
    center,fetcher=center_fixture(tmp_path);center.check(force=True)
    plan=center.plan_download('windows_installer')
    outside=tmp_path/'outside';outside.mkdir();canary=outside/'keep.txt';canary.write_bytes(b'keep unchanged')
    fake_exe=outside/plan['artifact']['file_name'];fake_exe.write_bytes(ARTIFACT)
    subprocess.run(['cmd','/c','mklink','/J',str(center.download_root),str(outside)],check=True,capture_output=True)
    calls=[]
    with pytest.raises(UpdateSecurityError,match='Reparse'):
        if action=='download':center.download(plan['plan_id'],confirmed=True)
        else:center.install(plan['plan_id'],confirmed=True,runner=lambda p:calls.append(p) or 0)
    assert calls==[] and canary.read_bytes()==b'keep unchanged' and fake_exe.read_bytes()==ARTIFACT
    assert ARTIFACT_URL not in fetcher.calls


def test_two_update_instances_cannot_regress_highest_signed_sequence(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    center,_=center_fixture(tmp_path);center.check(force=True)
    second,_=center_fixture(tmp_path)
    newer=signed_manifest();newer['release'].update(manifest_sequence=3,status='withdrawn');newer=resign(newer)
    older=signed_manifest();older['release']['manifest_sequence']=2;older=resign(older)
    def accept(instance,manifest):
        try:instance._accept_verified(manifest);return True
        except UpdateSecurityError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=[pool.submit(accept,instance,manifest) for instance,manifest in ((center,newer),(second,older))]
        assert results[0].result() is True
        results[1].result()
    assert json.loads(center.highwater_path.read_text())['release']['manifest_sequence']==3
    assert center._load_verified_manifest()['release']['status']=='withdrawn'


def test_same_version_repair_is_explicit_and_exact(tmp_path) -> None:
    center,_=center_fixture(tmp_path,installed_version='1.1.0',installed_artifact_sha256=hashlib.sha256(ARTIFACT).hexdigest())
    center.check(force=True)
    with pytest.raises(UpdateSecurityError,match='repair'):center.plan_download('windows_installer')
    plan=center.plan_download('windows_installer',repair=True)
    assert center.download(plan['plan_id'],confirmed=True)['ok']
    wrong,_=center_fixture(tmp_path,installed_version='1.1.0',installed_artifact_sha256='0'*64)
    with pytest.raises(UpdateSecurityError):wrong.plan_download('windows_installer',repair=True)
    newer,_=center_fixture(tmp_path,installed_version='1.2.0')
    with pytest.raises(UpdateSecurityError,match='downgrade'):newer.plan_download('windows_installer',repair=True)


def test_public_pin_matches_independent_spki_and_rejects_unknown_fields(tmp_path) -> None:
    pin={'schema_version':'1.0.0','keys':[{'algorithm':'rsa-sha256-pkcs1v15','key_id':TEST_KEY_ID,
        'modulus_hex':format(_TEST_PUBLIC.n,'x'),'exponent':65537}]}
    path=tmp_path/'trust.json';path.write_text(json.dumps(pin))
    assert load_trusted_release_keys(path)==TEST_TRUSTED_KEYS
    pin['keys'][0]['key_id']='plwc-personal-rsa-'+'0'*64;path.write_text(json.dumps(pin))
    with pytest.raises(UpdateSecurityError):load_trusted_release_keys(path)
    pin['keys'][0]['key_id']=TEST_KEY_ID;pin['keys'][0]['private_key']='fixture';path.write_text(json.dumps(pin))
    with pytest.raises(UpdateContractError):load_trusted_release_keys(path)
