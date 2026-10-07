"""Local encrypted-key signing; no private key or passphrase is passed through CI."""
from __future__ import annotations
import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from plwc_gateway.installation.update_center import (canonical_manifest_bytes, parse_manifest_json,
    rsa_public_key_id, verify_release_manifest, UpdateSecurityError)


def external_key_path(path: Path) -> Path:
    path=path.absolute()
    if str(path).startswith(('\\\\','//')) or path.is_symlink():
        raise ValueError('Key custody requires a local disk outside project/build/installation')
    resolved=path.resolve(strict=False)
    if any(part.casefold() in {'build','dist','stage','output'} for part in resolved.parts):
        raise ValueError('Private key may not enter a build/output tree')
    forbidden=[ROOT,Path(os.environ.get('APPDATA','.') )/'PLwC',Path(os.environ.get('LOCALAPPDATA','.') )/'PLwC']
    if any(resolved==p.resolve() or p.resolve() in resolved.parents for p in forbidden):
        raise ValueError('Private key may not enter repository or installation')
    if os.name=='nt':
        import ctypes
        drive=resolved.drive+'\\'
        if ctypes.windll.kernel32.GetDriveTypeW(drive)!=3:
            raise ValueError('Key custody requires a local fixed disk')
    current=path.parent
    while current!=current.parent:
        if current.exists() and (current.is_symlink() or getattr(current.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('Key custody path may not traverse reparse points')
        current=current.parent
    return resolved


def public_pin(key) -> dict:
    numbers=key.public_key().public_numbers()
    if key.key_size!=3072 or numbers.e!=65537:raise ValueError('Personal key must be RSA3072/65537')
    return {'algorithm':'rsa-sha256-pkcs1v15','key_id':rsa_public_key_id(numbers.n,numbers.e),
        'modulus_hex':format(numbers.n,'x'),'exponent':numbers.e}


def owner_only(path: Path) -> None:
    if os.name=='nt':
        literal="'"+str(path).replace("'","''")+"'"
        code="$ErrorActionPreference='Stop'; $p="+literal+''';
        $a=[System.IO.File]::GetAccessControl($p);
        $sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User;
        $a.SetAccessRuleProtection($true,$false);
        foreach($r in $a.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])) {
            $a.RemoveAccessRuleSpecific($r)
        }
        $a.SetOwner($sid);
        $rule=[System.Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','Allow');
        $a.AddAccessRule($rule); [System.IO.File]::SetAccessControl($p,$a)'''
        encoded=base64.b64encode(code.encode('utf-16le')).decode('ascii')
        subprocess.run(['powershell','-NoProfile','-NonInteractive','-EncodedCommand',encoded],check=True,capture_output=True)
    else:path.chmod(0o600)


def verify_owner_only(path: Path) -> None:
    if os.name != 'nt':
        info=path.stat()
        if info.st_mode & 0o077 or info.st_uid != os.getuid():
            raise ValueError('Private key permissions are not owner-only')
        return
    # Read effective file ACL metadata; never print/read key bytes through the shell.
    literal_path="'"+str(path).replace("'","''")+"'"
    code = "$ErrorActionPreference='Stop'; $a=[System.IO.File]::GetAccessControl("+literal_path+''');
    $s=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value;
    $o=$a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;
    $allowed=@();
    foreach($r in $a.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier])) {
        if($r.AccessControlType -eq 'Allow') { $allowed+=$r.IdentityReference.Value }
    }
    [Console]::WriteLine($o); [Console]::WriteLine($s);
    [Console]::WriteLine($a.AreAccessRulesProtected.ToString());
    [Console]::WriteLine([string]::Join(',', $allowed))'''
    encoded=base64.b64encode(code.encode('utf-16le')).decode('ascii')
    output=subprocess.check_output(['powershell','-NoProfile','-NonInteractive','-EncodedCommand',encoded],text=True)
    fields=output.splitlines()
    if len(fields)!=4 or fields[0]!=fields[1] or fields[2]!='True' or fields[3]!=fields[1]:
        raise ValueError('Private key permissions are not owner-only')


def create_key(path: Path, passphrase: bytes) -> dict:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    path=external_key_path(path)
    if not passphrase:raise ValueError('Encrypted PKCS8 requires a passphrase')
    key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    encoded=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passphrase))
    # Create the empty file exclusively and restrict ACLs before writing any key bytes.
    with path.open('xb') as handle:
        owner_only(path)
        verify_owner_only(path)
        handle.write(encoded);handle.flush();os.fsync(handle.fileno())
    return public_pin(key)


def load_key(path: Path, passphrase: bytes):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    path=external_key_path(path)
    verify_owner_only(path)
    encoded=path.read_bytes()
    if not encoded.startswith(b'-----BEGIN '+b'ENCRYPTED PRIVATE KEY-----'):
        raise ValueError('Unencrypted private key is forbidden')
    key=load_pem_private_key(encoded,password=passphrase)
    public_pin(key)
    return key


def sign_manifest(manifest: dict, key) -> dict:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    pin=public_pin(key)
    result={**manifest,'signature':{'algorithm':pin['algorithm'],'key_id':pin['key_id'],'value_base64':''}}
    result['signature']['value_base64']=base64.b64encode(key.sign(canonical_manifest_bytes(result),
        padding.PKCS1v15(),hashes.SHA256())).decode('ascii')
    # Independent stdlib verifier and complete contract before a signed file is emitted.
    return verify_release_manifest(result,{pin['key_id']:{'modulus':int(pin['modulus_hex'],16),'exponent':pin['exponent']}})


def verify_recovery(original_path: Path, restored_path: Path, passphrase: bytes) -> dict:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    first=load_key(original_path,passphrase);restored=load_key(restored_path,passphrase)
    if public_pin(first)!=public_pin(restored):raise UpdateSecurityError('Recovered key identity differs')
    message=b'PLwC Personal recovery test; not a release manifest'
    signed=restored.sign(message,padding.PKCS1v15(),hashes.SHA256())
    first.public_key().verify(signed,message,padding.PKCS1v15(),hashes.SHA256())
    return {'status':'pass','key_id':public_pin(first)['key_id'],'recovery_message_verified':True}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['create-key','sign','verify-recovery'])
    p.add_argument('--key',type=Path,required=True);p.add_argument('--manifest',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--restored-key',type=Path)
    args=p.parse_args()
    password=getpass.getpass('Local encrypted-key passphrase: ').encode('utf-8')
    if args.action=='create-key':
        if password!=getpass.getpass('Repeat passphrase: ').encode('utf-8'):p.error('Passphrases differ')
        result={'schema_version':'1.0.0','keys':[create_key(args.key,password)]}
    elif args.action=='verify-recovery':
        if args.restored_key is None:p.error('Provide the separately restored encrypted key')
        result=verify_recovery(args.key,args.restored_key,password)
    else:
        if args.manifest is None or args.output is None:p.error('Sign requires manifest and new output')
        result=sign_manifest(parse_manifest_json(args.manifest.read_bytes()),load_key(args.key,password))
    if args.output is not None:
        with args.output.open('x',encoding='utf-8',newline='\n') as handle:json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
    else:print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
