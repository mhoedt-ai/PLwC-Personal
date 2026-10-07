FROM python:3.12.14-slim-trixie@sha256:2fe5997d249a808b8eeea52c58a1dbffbba28754dc11699ef5c029f2d818ce79

ARG SOURCE_DATE_EPOCH="0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

# Perl is not a PLwC runtime dependency. Removing the incidental Debian
# essential package eliminates an otherwise executable, unused interpreter.
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf '%s\n' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260928T000000Z trixie main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260928T000000Z trixie-security main' \
        > /etc/apt/sources.list \
    && apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install -y --no-install-recommends \
        libc6=2.41-12+deb13u4 \
        libc-bin=2.41-12+deb13u4 \
    && rm -rf \
        /var/lib/apt/lists/* \
        /var/cache/apt/* \
        /var/cache/ldconfig/* \
        /var/log/apt/* \
        /var/log/alternatives.log \
        /var/log/dpkg.log \
    && dpkg --purge --force-remove-essential --force-depends perl-base \
    && test ! -e /usr/bin/perl \
    && ! dpkg-query -W perl-base \
    && rm -f /var/log/dpkg.log

COPY notices/pip-reviewed/ /usr/share/doc/plwc-pip-notices/
COPY filter-linux-pip.py /tmp/filter-linux-pip.py
RUN python /tmp/filter-linux-pip.py && rm /tmp/filter-linux-pip.py
RUN test -s /usr/share/doc/plwc-pip-notices/PIP-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-pip-notices/SOURCE-NOTICE.md
COPY plwc-licenses/ /usr/share/doc/plwc/
COPY notices/debian-generator/ /usr/share/doc/debian-generator/
COPY plwc-notices.py /tmp/plwc-notices.py
RUN python /tmp/plwc-notices.py && rm /tmp/plwc-notices.py

# Do not distribute superseded OpenSSL or removed Perl bytes from base layers.
FROM scratch
COPY --from=0 / /

ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG SOURCE_REVISION="unknown"
ARG SOURCE_DATE_EPOCH="0"

LABEL org.opencontainers.image.title="PLwC Personal Python Runner" \
      org.opencontainers.image.description="Offline Python sandbox runtime for PLwC" \
      org.opencontainers.image.source="https://github.com/mhoedt-ai/PLwC-Personal" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="LicenseRef-PLwC-Personal-1.0" \
      org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.revision="${SOURCE_REVISION}"

ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    LANG=C.UTF-8 \
    GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305 \
    PYTHON_VERSION=3.12.14 \
    PYTHON_SHA256=5c8462af5790baf43a321a1559dbe0db06d1be4300fb85fb53c40060668e548a \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

CMD ["python3"]
WORKDIR /work
