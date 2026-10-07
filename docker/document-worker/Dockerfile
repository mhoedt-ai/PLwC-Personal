FROM python:3.12.14-slim-trixie@sha256:2fe5997d249a808b8eeea52c58a1dbffbba28754dc11699ef5c029f2d818ce79

# Build the MIME database without shipping its XML compiler or system libxml2.
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf '%s\n' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260928T000000Z trixie main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260928T000000Z trixie-updates main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260928T000000Z trixie-security main' \
        > /etc/apt/sources.list \
    && apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install -y --no-install-recommends \
        libc6=2.41-12+deb13u4 \
        libc-bin=2.41-12+deb13u4 \
        shared-mime-info=2.4-5+b2 \
    && test -s /usr/share/mime/mime.cache \
    && test -s /usr/share/mime/globs2 \
    && test -s /usr/share/mime/magic

FROM python:3.12.14-slim-trixie@sha256:2fe5997d249a808b8eeea52c58a1dbffbba28754dc11699ef5c029f2d818ce79

ARG SOURCE_DATE_EPOCH="0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/plwc-document-worker \
    PIP_NO_INDEX=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

WORKDIR /opt/plwc-document-worker

RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && printf '%s\n' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260928T000000Z trixie main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20260928T000000Z trixie-updates main' \
        'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20260928T000000Z trixie-security main' \
        > /etc/apt/sources.list \
    && apt-get update -o APT::Update::Error-Mode=any \
    && apt-get install -y --no-install-recommends \
        fonts-dejavu-core=2.37-8 \
        libc6=2.41-12+deb13u4 \
        libc-bin=2.41-12+deb13u4 \
        libcairo2=1.18.4-1+b1 \
        libffi8=3.4.8-2 \
        libpcre2-8-0=10.46-1~deb13u2 \
    && rm -rf \
        /var/lib/apt/lists/* \
        /var/cache/apt/* \
        /var/cache/ldconfig/* \
        /var/log/apt/* \
        /var/log/alternatives.log \
        /var/log/dpkg.log

COPY --from=0 /usr/share/mime/ /usr/share/mime/
COPY --from=0 /usr/share/doc/shared-mime-info/copyright /usr/share/doc/shared-mime-info/copyright

COPY requirements-doc-worker.txt requirements-doc-worker.txt
COPY requirements-doc-worker.lock requirements-doc-worker.lock
COPY wheelhouse/ /opt/plwc-wheelhouse/
COPY worker/ /opt/plwc-document-worker/

# The lock file must contain pinned versions and hashes generated from the
# offline wheelhouse. This intentionally fails if hashes or wheels are missing.
RUN python -m pip install --no-index --find-links=/opt/plwc-wheelhouse --require-hashes -r requirements-doc-worker.lock

# The vendored odfpy wheel omits its upstream license files. Preserve the
# notices from the SHA-256-verified 1.4.1 source distribution beside the
# installed package; the source files also carry LGPL and OASIS notices.
COPY notices/odfpy-1.4.1/ /usr/share/doc/odfpy/
RUN cp /usr/share/common-licenses/LGPL-2.1 /usr/share/doc/odfpy/LGPL-2.1.txt \
    && test -s /usr/share/doc/odfpy/APACHE-LICENSE-2.0.txt \
    && test -s /usr/share/doc/odfpy/GPL-LICENSE-2.txt \
    && test -s /usr/share/doc/odfpy/LGPL-2.1.txt \
    && test -s /usr/share/doc/odfpy/README.md \
    && test -s /usr/share/doc/odfpy/CC-BY-SA-3.0.txt \
    && test -s /usr/share/doc/odfpy/THUMBNAIL-NOTICE.txt \
    && test -s /usr/share/doc/odfpy/OASIS-ODF-1.2-NOTICE.txt \
    && test -s /usr/share/doc/odfpy/FILE-LICENSES.json \
    && test -s /usr/share/doc/odfpy/LGPL-REPLACEMENT.md

# Retain full grants omitted by individual wheels and copied-file notices.
COPY notices/python-reviewed-subset/ /usr/share/doc/plwc-python-notices/
RUN test -s /usr/share/doc/plwc-python-notices/PYTHON-PACKAGE-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-python-notices/SOURCE-NOTICE.md

COPY notices/timezone-reviewed-subset/ /usr/share/doc/plwc-timezone-notices/
RUN test -s /usr/share/doc/plwc-timezone-notices/TIMEZONE-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-timezone-notices/SOURCE-NOTICE.md

COPY notices/reportlab-reviewed/ /usr/share/doc/plwc-reportlab-notices/
RUN test -s /usr/share/doc/plwc-reportlab-notices/REPORTLAB-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-reportlab-notices/SOURCE-NOTICE.md

COPY notices/pandas-reviewed/ /usr/share/doc/plwc-pandas-notices/
RUN test -s /usr/share/doc/plwc-pandas-notices/PANDAS-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-pandas-notices/SOURCE-NOTICE.md

COPY notices/pillow-reviewed/ /usr/share/doc/plwc-pillow-notices/
RUN test -s /usr/share/doc/plwc-pillow-notices/PILLOW-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-pillow-notices/SOURCE-NOTICE.md

COPY notices/numpy-reviewed/ /usr/share/doc/plwc-numpy-notices/
RUN test -s /usr/share/doc/plwc-numpy-notices/NUMPY-SUPPLEMENTAL-NOTICES.txt \
    && test -s /usr/share/doc/plwc-numpy-notices/SOURCE-NOTICE.md

# Preserve copied Python/ElementTree and individual native-header grants.
# This bounded notice supplement does not approve the whole lxml package.
COPY notices/lxml-retained-reviewed/ /usr/share/doc/plwc-lxml-notices/
RUN test -s /usr/share/doc/plwc-lxml-notices/LXML-RETAINED-FILE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/NATIVE-CORE-SOURCE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/GENERATED-TABLE-SOURCE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/GENERATED-CONFIG-SOURCE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/ADAPTED-AUTOCONF-SOURCE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/SYSTEM-HEADER-SOURCE-NOTICES.txt \
    && test -s /usr/share/doc/plwc-lxml-notices/SOURCE-NOTICE.md

RUN useradd --no-log-init --no-create-home --uid 10001 --shell /usr/sbin/nologin plwcworker \
    && chage -d 0 plwcworker \
    && rm -f /etc/shadow- /etc/gshadow- \
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

# Distribute only the corrected filesystem. The Python base's earlier layers
# otherwise retain replaced OpenSSL binaries and the removed Perl runtime.
FROM scratch
COPY --from=1 / /

ARG OCI_CREATED="1970-01-01T00:00:00Z"
ARG SOURCE_REVISION="unknown"
ARG SOURCE_DATE_EPOCH="0"

LABEL org.opencontainers.image.title="PLwC Personal Document Worker" \
      org.opencontainers.image.description="Offline governed document operations for PLwC" \
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
    PYTHONPATH=/opt/plwc-document-worker \
    PIP_NO_INDEX=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

USER 10001:10001

WORKDIR /work
ENTRYPOINT ["python", "-m", "plwc_document_worker"]
