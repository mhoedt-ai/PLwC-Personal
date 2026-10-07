import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';

const root='/usr/share/doc/plwc';
mkdirSync(root,{recursive:true});
const packages=execFileSync('dpkg-query',['-W','-f=${Package}\t${Version}\n'],{encoding:'utf8'}).trim().split('\n').map(line=>{
  const [name,version]=line.split('\t');
  const path=`/usr/share/doc/${name}/copyright`;
  return {ecosystem:'debian',name,version,license_path:existsSync(path)?path:null};
});
packages.push({ecosystem:'node-runtime',name:'node',version:process.version,
  license_paths:['/usr/local/LICENSE','/usr/local/share/doc/node/LICENSE'].filter(existsSync)});
if (existsSync('/usr/share/doc/docker-node/LICENSE-MIT.txt')) {
  packages.push({ecosystem:'official-image-script',name:'docker-node entrypoint',
    source_revision:'81f419144a1251854c6d9afb09eaa39928e724e8',
    license_paths:['/usr/share/doc/docker-node/LICENSE-MIT.txt','/usr/share/doc/docker-node/SOURCE-NOTICE.md']});
}
if (existsSync('/usr/share/doc/debian-generator/DEBUERREOTYPE-LICENSE-MIT.txt')) {
  packages.push({ecosystem:'base-generator-notice',name:'debuerreotype and copied Docker material',version:'0.17',
    license_paths:['DEBUERREOTYPE-LICENSE-MIT.txt','DOCKER-LICENSE-APACHE-2.0.txt','DOCKER-NOTICE.txt','SOURCE-NOTICE.md']
      .map(name=>`/usr/share/doc/debian-generator/${name}`)});
}
packages.sort((a,b)=>`${a.ecosystem}/${a.name}`.localeCompare(`${b.ecosystem}/${b.name}`,'en'));
writeFileSync(`${root}/runtime-license-locations.json`,JSON.stringify({schema_version:'1.0.0',packages,
  review_status:'requires_exact_artifact_license_and_corresponding_source_review'},null,2)+'\n');
writeFileSync(`${root}/THIRD_PARTY_NOTICES.txt`,'Third-party components retain their independent rights.\n'+
  'Exact versions and installed notices: runtime-license-locations.json.\n'+
  'Debian licenses: /usr/share/doc/<package>/copyright and /usr/share/common-licenses/.\n'+
  'Release acceptance requires reviewed complete notices and corresponding source archives.\n'+
  'This machine inventory alone does not establish redistribution permission.\n');
