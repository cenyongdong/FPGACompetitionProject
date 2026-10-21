"""Fetch only the two approved OctoNet stage-A files from a pinned official revision."""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

REPO = "hku-aiot/OctoNet"
REVISION = "47a68995d135344c43356840e9e14cc630f62c35"
FILES = (
    ("node_1/1_wifi_1_1_sit_1_20240519162409.pickle", 12743058,
     "0421bca51134f2fd16aa72bd63a1424d7a468acab76d139bb0b3194258aa0bf3"),
    ("node_1/1_heartrate_1_1_sit_1_20240519162409.pickle", 4134,
     "d5958c03d844a5f833a94022e3ef51b927cc77fb1cc5bf798f87a458596b469b"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--proxy", default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    metadata = root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    manifest_path = metadata / "stage-a-download.json"
    if manifest_path.exists():
        raise RuntimeError("Preserve the existing manifest; inspect it before any further transfer")
    if sum(size for _, size, _ in FILES) > 100 * 1024**2:
        raise RuntimeError("Stage-A approved byte budget exceeded")
    for remote, _, _ in FILES:
        target = root / "raw" / remote
        if target.exists() or target.with_suffix(target.suffix + ".part").exists():
            raise RuntimeError(f"Preserve existing or partial artifact: {target}")
    proxy = {"http": args.proxy, "https": args.proxy} if args.proxy else {}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxy))
    manifest = dict(schema=1, repository=REPO, revision=REVISION, stage="A",
                    stage_a_limit_bytes=100 * 1024**2, total_limit_bytes=500 * 1024**2,
                    selection="node 1, scene 1, user 1, sit, trial 1, 20240519162409",
                    metadata_source="official resolve HEAD X-Repo-Commit/X-Linked-Size/X-Linked-ETag",
                    tls_certificate_verification=True, records=[], complete=False)

    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save()
    for remote, expected_size, expected_sha in FILES:
        target = root / "raw" / remote
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".part")
        record = dict(remote_path=remote, local_path=str(target), expected_bytes=expected_size,
                      official_sha256=expected_sha, received_bytes=0, verified=False)
        manifest["records"].append(record)
        save()
        start = time.monotonic()
        digest = hashlib.sha256()
        url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{remote}"
        print(f"Downloading {remote}: {expected_size} bytes", flush=True)
        try:
            with opener.open(url, timeout=30) as response, partial.open("xb") as out:
                if response.status != 200 or not response.url.startswith("https://"):
                    raise RuntimeError("Unexpected transfer status or insecure redirect")
                while chunk := response.read(256 * 1024):
                    record["received_bytes"] += len(chunk)
                    if record["received_bytes"] > expected_size:
                        raise RuntimeError("Response exceeds approved file size")
                    out.write(chunk)
                    digest.update(chunk)
            record["local_sha256"] = digest.hexdigest()
            if record["received_bytes"] != expected_size or digest.hexdigest() != expected_sha:
                raise RuntimeError("Downloaded size or official content SHA256 mismatch")
            partial.rename(target)
            record.update(verified=True, seconds=time.monotonic() - start)
            save()
            print(f"Verified {target.name}", flush=True)
        except Exception as error:
            record.update(error=f"{type(error).__name__}: {error}", seconds=time.monotonic() - start)
            save()
            raise
    manifest["complete"] = True
    manifest["received_bytes"] = sum(r["received_bytes"] for r in manifest["records"])
    save()
    print(json.dumps({"manifest": str(manifest_path), "received_bytes": manifest["received_bytes"]}))


if __name__ == "__main__":
    main()
