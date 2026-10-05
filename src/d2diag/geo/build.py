"""Build ``places.tsv.gz`` from the GeoNames dumps (spec 2026-10-06-logs-at-scale §2).

Thin CLI: ``tools/build_places.py``. The output is deterministic: the same cached inputs
always give a byte-identical file (rows sorted, gzip mtime 0, header dated from the
dump itself rather than the wall clock).

File format (UTF-8, tab-separated, gzip):

* ``# key: value`` header comments (source, licence, dump date);
* ``#country<TAB>CC<TAB>Name`` lines, the country-name map;
* one header row ``name lat lon cc admin1_name admin2_name population``;
* one row per place, lat/lon at 5 decimals.
"""
from __future__ import annotations

import gzip
import io
import os
import urllib.request
import zipfile

BASE_URL = "https://download.geonames.org/export/dump/"
INPUTS = ("cities1000.zip", "admin1CodesASCII.txt", "admin2Codes.txt", "countryInfo.txt")
COLUMNS = ("name", "lat", "lon", "cc", "admin1_name", "admin2_name", "population")
DEFAULT_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "d2diag-geonames")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "places.tsv.gz")
# Historical, abandoned or destroyed places never name a live drive.
_SKIP_FEATURES = {"PPLH", "PPLQ", "PPLW", "PPLCH"}


def download(cache_dir: str = DEFAULT_CACHE, base_url: str = BASE_URL) -> None:
    """Fetch any missing input into ``cache_dir``; present files are kept as they are."""
    os.makedirs(cache_dir, exist_ok=True)
    for name in INPUTS:
        path = os.path.join(cache_dir, name)
        if os.path.exists(path):
            continue
        req = urllib.request.Request(base_url + name, headers={"User-Agent": "discovery2-diag build_places"})
        tmp = path + ".part"
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                fh.write(chunk)
        os.replace(tmp, path)


def _clean(text: str) -> str:
    return text.replace("\t", " ").replace("\n", " ").strip()


def _read_lines(path: str):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                yield line.split("\t")


def build(cache_dir: str = DEFAULT_CACHE, out_path: str = DEFAULT_OUT) -> dict:
    """Write ``out_path`` from the cached dumps; returns {rows, bytes, date}."""
    admin1 = {f[0]: _clean(f[1]) for f in _read_lines(os.path.join(cache_dir, "admin1CodesASCII.txt"))}
    admin2 = {f[0]: _clean(f[1]) for f in _read_lines(os.path.join(cache_dir, "admin2Codes.txt"))}
    countries = {f[0]: _clean(f[4]) for f in _read_lines(os.path.join(cache_dir, "countryInfo.txt")) if len(f) > 4}

    rows = []
    with zipfile.ZipFile(os.path.join(cache_dir, "cities1000.zip")) as zf:
        info = zf.getinfo("cities1000.txt")
        date = "%04d-%02d-%02d" % info.date_time[:3]
        with zf.open(info) as raw:
            for line in io.TextIOWrapper(raw, encoding="utf-8"):
                f = line.rstrip("\n").split("\t")
                if len(f) < 15 or f[7] in _SKIP_FEATURES:
                    continue
                name, cc = _clean(f[1]), f[8]
                if not name:
                    continue
                lat, lon = float(f[4]), float(f[5])
                a1 = admin1.get(f"{cc}.{f[10]}", "") if f[10] else ""
                a2 = admin2.get(f"{cc}.{f[10]}.{f[11]}", "") if f[11] else ""
                try:
                    pop = int(f[14] or 0)
                except ValueError:
                    pop = 0
                rows.append((name, f"{lat:.5f}", f"{lon:.5f}", cc, a1, a2, str(pop)))
    rows = sorted(set(rows), key=lambda r: (r[3], r[0], r[1], r[2], r[4], r[5], r[6]))

    out = io.StringIO()
    out.write("# source: GeoNames cities1000 + admin1/admin2 codes + countryInfo "
              "(https://download.geonames.org/export/dump/)\n")
    out.write("# licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), (c) GeoNames\n")
    out.write(f"# date: {date}\n")
    out.write("# built-by: tools/build_places.py (do not hand-edit)\n")
    used = sorted({r[3] for r in rows} | set(countries))
    for cc in used:
        if cc in countries:
            out.write(f"#country\t{cc}\t{countries[cc]}\n")
    out.write("\t".join(COLUMNS) + "\n")
    for r in rows:
        out.write("\t".join(r) + "\n")
    data = out.getvalue().encode("utf-8")

    tmp = out_path + ".tmp"
    with open(tmp, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, compresslevel=9, mtime=0) as gz:
            gz.write(data)
    os.replace(tmp, out_path)
    return {"rows": len(rows), "bytes": os.path.getsize(out_path), "date": date}
