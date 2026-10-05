# Discovery 2 diagnostics web viewer — container image.
#
# Runs the stdlib HTTP + React dashboard LIVE (there is no demo mode, ADR-0011). With no
# cable attached it shows "No connection" plus the two committed demo logs, the fault
# dictionary, docs, coverage and system map; nothing is recorded without a car. The React UI is prebuilt and committed to src/d2diag/web/static, so
# no Node is needed at runtime; the only runtime dependency is pyserial.
#
# The app runs straight from the source tree (tools/dashboard.py prepends ./src to sys.path),
# so we install only the dependency and copy the repo — no wheel build needed.
FROM python:3.12-slim

WORKDIR /app

# Unbuffered stdout/stderr so the startup banner and any print() reach `docker logs`
# immediately (Python block-buffers stdout when it is not a TTY, which otherwise hides
# the banner behind a never-flushed buffer).
ENV PYTHONUNBUFFERED=1

# Dependency layer first, for build-cache reuse across source changes.
RUN pip install --no-cache-dir "pyserial>=3.5"

COPY . /app

EXPOSE 8080

# /snapshot is a no-auth, no-hardware 200 (slim has no curl, so use Python).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/snapshot', timeout=3).status == 200 else 1)"

# Live, bound on all interfaces for Traefik. NOT --allow-shutdown (would let the web UI
# power off the host). --replay loops the committed synthetic sniff log so the admin Decode
# tab has a feed (no car data in it). The OSM geocoder is on (the default
# https://nominatim.openstreetmap.org; ≤1 request/s, cached in logs/geocache.json).
CMD ["python", "tools/dashboard.py", "--host", "0.0.0.0", "--port", "8080", \
     "--replay", "src/d2diag/vehicles/lr_d2/demo/sniff-demo.txt", \
     "--geocoder", "https://nominatim.openstreetmap.org"]
