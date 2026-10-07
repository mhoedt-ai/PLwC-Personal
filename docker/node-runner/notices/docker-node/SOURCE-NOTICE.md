# Official docker-node entrypoint notice

`/usr/local/bin/docker-entrypoint.sh` is supplied by the official docker-node
repository, independently of the Node.js runtime distribution. The actual
entrypoint bytes were checked against source commit
`81f419144a1251854c6d9afb09eaa39928e724e8`:

https://github.com/nodejs/docker-node/blob/81f419144a1251854c6d9afb09eaa39928e724e8/docker-entrypoint.sh

`LICENSE-MIT.txt` is an exact copy of that commit's root `LICENSE`:

https://github.com/nodejs/docker-node/blob/81f419144a1251854c6d9afb09eaa39928e724e8/LICENSE

SHA-256: `782e17d54343aa3f6db60430015692b6540089b3ec5b78274981ada2d3c3c423`.
Copyright (c) 2015 Joyent, Inc. and Copyright (c) 2015 Node.js contributors
are retained in the complete MIT text. PLwC's own license does not restrict
the independent rights to this script. The separate Node.js runtime and
its embedded component notices remain at `/usr/local/LICENSE`.
