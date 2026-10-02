"""Fetch and unpack the two approved NVIDIA runtime components.

This changes only the project's .local/icraft-runtime directory. Run only after
approval of the downloads and paths described in REFERENCES.md, section I5.
Requires Python 3.8+; no third-party Python packages are used.
"""

import concurrent.futures
import hashlib
import json
import struct
import time
import urllib.request
import zipfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT / ".local" / "icraft-runtime" / "cuda-11.8.0"
BASE_URL = "https://developer.download.nvidia.com/compute/cuda/redist/"
MANIFEST_URL = BASE_URL + "redistrib_11.8.0.json"
COMPONENTS = {
    "libcublas": {
        "version": "11.11.3.6",
        "sha256": "67b0934a6359e4ee26fff823c356021589d392c4fd49ca12624f570edc08e2b9",
        "size": 420850025,
        "dlls": ["cublas64_11.dll", "cublasLt64_11.dll"],
    },
    "libcufft": {
        "version": "10.9.0.58",
        "sha256": "a4071a85e3983bf42ea7a2e9bebe3b0b3c9ac258668580adc32ee1c385f7556f",
        "size": 168982770,
        "dlls": ["cufft64_10.dll"],
    },
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_component(name, spec, official):
    if official["version"] != spec["version"]:
        raise RuntimeError("Official version changed: " + name)
    win = official["windows-x86_64"]
    if win["sha256"] != spec["sha256"] or int(win["size"]) != spec["size"]:
        raise RuntimeError("Official checksum/size differs from approved plan: " + name)
    relative = win["relative_path"]
    if not relative.startswith(name + "/windows-x86_64/") or not relative.endswith(".zip"):
        raise RuntimeError("Unexpected component URL: " + relative)
    url = BASE_URL + relative
    destination = ROOT / "downloads" / Path(relative).name
    if not destination.exists():
        partial = destination.with_suffix(".zip.part")
        if partial.exists():
            raise RuntimeError("Partial download already exists; inspect before retry: " + str(partial))
        received = 0
        last_notice = time.monotonic()
        print(name + ": download started", flush=True)
        with urllib.request.urlopen(url, timeout=60) as response, partial.open("xb") as out:
            while True:
                block = response.read(4 * 1024 * 1024)
                if not block:
                    break
                out.write(block)
                received += len(block)
                if time.monotonic() - last_notice >= 10:
                    print("{}: {:.1f}/{:.1f} MiB".format(name, received / 1048576, spec["size"] / 1048576), flush=True)
                    last_notice = time.monotonic()
        if partial.stat().st_size != spec["size"] or sha256_file(partial) != spec["sha256"]:
            raise RuntimeError("Download failed checksum/size validation: " + str(partial))
        partial.rename(destination)
    if destination.stat().st_size != spec["size"] or sha256_file(destination) != spec["sha256"]:
        raise RuntimeError("Cached ZIP failed checksum/size validation: " + str(destination))
    print(name + ": SHA-256 verified", flush=True)

    extracted = ROOT / "packages" / destination.stem
    if extracted.exists() and any(extracted.iterdir()):
        raise RuntimeError("Extraction directory already has contents; inspect before retry: " + str(extracted))
    extracted.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination) as archive:
        infos = archive.infolist()
        # Preserve the vendor directory structure; reject escaping ZIP paths.
        for member in infos:
            target = (extracted / member.filename).resolve()
            if extracted.resolve() not in target.parents and target != extracted.resolve():
                raise RuntimeError("Unsafe ZIP member: " + member.filename)
        archive.extractall(extracted)
    dll_records = []
    bin_dirs = set()
    for filename in spec["dlls"]:
        matches = list(extracted.rglob(filename))
        if len(matches) != 1:
            raise RuntimeError("Expected exactly one " + filename)
        path = matches[0]
        with path.open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise RuntimeError("Not a Windows DLL: " + str(path))
            stream.seek(0x3C)
            pe_offset = struct.unpack("<I", stream.read(4))[0]
            stream.seek(pe_offset)
            if stream.read(4) != b"PE\0\0" or struct.unpack("<H", stream.read(2))[0] != 0x8664:
                raise RuntimeError("Not a Windows x64 PE: " + str(path))
        dll_records.append({"name": filename, "path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size})
        bin_dirs.add(str(path.parent))
    licenses = [str(p) for p in extracted.rglob("*") if p.is_file() and any(word in p.name.lower() for word in ("license", "eula"))]
    if not licenses:
        raise RuntimeError("No vendor license file found: " + name)
    print(name + ": extracted; Windows x64 DLLs and license present", flush=True)
    return {
        "name": name, "version": spec["version"], "url": url,
        "zip_path": str(destination), "zip_sha256": spec["sha256"],
        "download_size": spec["size"], "extracted_root": str(extracted),
        "uncompressed_size": sum(info.file_size for info in infos),
        "bin_dirs": sorted(bin_dirs), "dlls": dll_records, "licenses": licenses,
    }


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "downloads").mkdir(exist_ok=True)
    (ROOT / "logs").mkdir(exist_ok=True)
    output_manifest = ROOT / "runtime-manifest.json"
    if output_manifest.exists():
        raise RuntimeError("Runtime manifest already exists; inspect instead of replacing it.")
    with urllib.request.urlopen(MANIFEST_URL, timeout=30) as response:
        raw_manifest = response.read()
    official = json.loads(raw_manifest)
    (ROOT / "redistrib_11.8.0.json").write_bytes(raw_manifest)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(download_component, name, spec, official[name]) for name, spec in COMPONENTS.items()]
        components = [future.result() for future in futures]
    manifest = {
        "schema_version": 1,
        "status": "prepared_pending_load_validation",
        "approval_date": "2026-10-01",
        "approval_scope": "Two official ZIPs, independent directory, launcher, DLL/help loading verification only",
        "cuda_distribution": "11.8.0",
        "icraft_version": "3.39.0",
        "icraft_bin": r"C:\Icraft\CLI v3.39.0\bin",
        "official_manifest_url": MANIFEST_URL,
        "official_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "components": components,
    }
    output_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Runtime manifest: " + str(output_manifest), flush=True)


if __name__ == "__main__":
    main()
