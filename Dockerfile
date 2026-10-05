# Ostler — the open vehicle platform: web viewer container image.
#
# Runs the stdlib HTTP + React dashboard LIVE (there is no demo mode, ADR-0011). With no
# cable attached it shows "No connection" plus the vehicle pack's committed demo logs, the
# fault dictionary, docs, coverage and system map; nothing is recorded without a car. The
# React UI is prebuilt and committed to src/openostler/web/static, so no Node is needed at
# runtime; the only runtime dependency is pyserial.
#
# The image installs the platform (this repo) plus one vehicle pack (ADR-0013, ADR-0015):
# the Land Rover Discovery 2 reference pack "d2diag" from its repo at PACK_REF.

# Meta stage: stamp the platform commit and build time (Settings → Version) from .git,
# then drop .git so it never reaches the final image.
FROM python:3.12-slim AS meta
COPY . /src
RUN python /src/tools/build_meta.py /src && rm -rf /src/.git

FROM python:3.12-slim

# The D2 pack's git ref (a branch, tag or commit), e.g. --build-arg PACK_REF=v0.1.0.
ARG PACK_REF=main
ARG PACK_REPO=https://github.com/JamesWrightDavid/discovery2-diag

WORKDIR /app

# Unbuffered stdout/stderr so the startup banner and any print() reach `docker logs`
# immediately (Python block-buffers stdout when it is not a TTY, which otherwise hides
# the banner behind a never-flushed buffer).
ENV PYTHONUNBUFFERED=1

# Dependency layer first, for build-cache reuse across source changes.
RUN pip install --no-cache-dir "pyserial>=3.5"

COPY --from=meta /src /app

# The platform, then the pack (--no-deps: the pack depends on "openostler", installed just
# above). The pack is a source checkout installed editable, not a git+ wheel: it serves
# its docs (references/, docs/) for the Docs tab from the checkout. git is needed only
# for the clone and is removed again.
RUN pip install --no-cache-dir . \
 && apt-get update && apt-get install -y --no-install-recommends git \
 && git clone --depth 1 --branch "${PACK_REF}" "${PACK_REPO}" /opt/d2-pack \
 && git -C /opt/d2-pack rev-parse HEAD > /opt/d2-pack/BUILD_COMMIT \
 && rm -rf /opt/d2-pack/.git \
 && pip install --no-cache-dir --no-deps -e /opt/d2-pack \
 && apt-get purge -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

EXPOSE 8080

# /snapshot is a no-auth, no-hardware 200 (slim has no curl, so use Python).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/snapshot', timeout=3).status == 200 else 1)"

# Live, bound on all interfaces for Traefik. NOT --allow-shutdown (would let the web UI
# power off the host). "--replay pack" loops the installed pack's synthetic demo sniff log
# so the admin Decode tab has a feed (no car data in it). The OSM geocoder is on (the
# default https://nominatim.openstreetmap.org; ≤1 request/s, cached in logs/geocache.json).
CMD ["python", "tools/dashboard.py", "--host", "0.0.0.0", "--port", "8080", \
     "--replay", "pack", \
     "--geocoder", "https://nominatim.openstreetmap.org"]
