FROM node:22.23.3-trixie-slim@sha256:b26b04c123d9ff8ab646ceb18b9d75a1173acf64b9a401094b906d27b29338d4

# Minimal Node 22 LTS sandbox image for plwc_sandbox_run(lang="node").
# The sandbox executes node directly. Package managers from the upstream image
# are deliberately removed because dependency installation is forbidden here.
# Non-root uid/gid 65532 is enforced at runtime via --user 65532:65532.
RUN dpkg-query -s libc6 | grep -qx 'Version: 2.41-12+deb13u4' \
    && dpkg-query -s libc-bin | grep -qx 'Version: 2.41-12+deb13u4' \
    && rm -rf \
        /usr/local/lib/node_modules/corepack \
        /usr/local/lib/node_modules/npm \
        /opt/yarn-v1.22.22 \
    && rm -f \
        /usr/local/bin/corepack \
        /usr/local/bin/npm \
        /usr/local/bin/npx \
        /usr/local/bin/yarn \
        /usr/local/bin/yarnpkg \
    && dpkg --purge --force-remove-essential --force-depends perl-base \
    && test ! -e /usr/bin/perl \
    && ! dpkg-query -W perl-base \
    && rm -f /var/log/dpkg.log

COPY plwc-licenses/ /usr/share/doc/plwc/
COPY notices/docker-node/ /usr/share/doc/docker-node/
COPY notices/debian-generator/ /usr/share/doc/debian-generator/
COPY plwc-notices.mjs /tmp/plwc-notices.mjs
RUN node /tmp/plwc-notices.mjs && rm /tmp/plwc-notices.mjs

# Copy the cleaned filesystem into a new image. Deletions in a later layer
# otherwise still distribute npm documentation and removed interpreters.
FROM scratch
COPY --from=0 / /

ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG SOURCE_REVISION="unknown"
ARG SOURCE_DATE_EPOCH="0"

LABEL org.opencontainers.image.title="PLwC Personal Node Runner" \
      org.opencontainers.image.description="Offline Node sandbox runtime for PLwC" \
      org.opencontainers.image.source="https://github.com/mhoedt-ai/PLwC-Personal" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="LicenseRef-PLwC-Personal-1.0" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}"

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    NODE_VERSION=22.23.3
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node"]
WORKDIR /work
