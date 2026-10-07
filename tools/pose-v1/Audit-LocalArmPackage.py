"""Read original ARM .deb archives; never extract or execute their payloads."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile


def ar_members(path):
    with path.open("rb") as stream:
        if stream.read(8) != b"!<arch>\n":
            raise ValueError("Not an ar archive")
        while True:
            header = stream.read(60)
            if not header:
                return
            if len(header) != 60 or header[58:60] != b"`\n":
                raise ValueError("Invalid ar header")
            size = int(header[48:58].strip())
            data = stream.read(size)
            if len(data) != size:
                raise ValueError("Truncated ar member")
            if size % 2:
                stream.read(1)
            yield header[:16].decode("ascii").strip().rstrip("/"), data


def review(path):
    result = {"source": str(path.resolve()), "size": path.stat().st_size,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "selected_files": [], "payload_executed": False}
    for archive_name, content in ar_members(path):
        if not archive_name.startswith(("data.tar", "control.tar")):
            continue
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as archive:
            for member in archive:
                name = member.name
                selected = ("hostbackend" in name.lower() or "cuda" in name.lower()
                            or "matmul" in name.lower()
                            or (archive_name.startswith("control.tar")
                                and name.strip("./") == "control"))
                if not selected:
                    continue
                entry = {"archive": archive_name, "path": name,
                         "size": member.size, "link": member.linkname}
                if member.isfile():
                    data = archive.extractfile(member).read()
                    entry["sha256"] = hashlib.sha256(data).hexdigest()
                    if name.endswith(".cmake") or name.strip("./") == "control":
                        entry["text"] = data.decode("utf-8", errors="replace")
                    if ".so" in name:
                        entry["literal_counts"] = {
                            token: data.count(token.encode("ascii"))
                            for token in ("Matmul", "TopK", "Gather", "ScatterND",
                                          "icraft::xir::MatmulNode")}
                        entry["matching_printable_strings"] = sorted(set(
                            s.decode("ascii") for s in re.findall(rb"[ -~]{6,}", data)
                            if any(token in s for token in
                                   (b"Matmul", b"TopK", b"ScatterND"))))[:60]
                result["selected_files"].append(entry)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packages", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve existing audit; output already exists")
    result = {"scope": "Static original archive review only; binary strings are not a runtime support test",
              "packages": [review(path) for path in args.packages]}
    args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print("Static package audit saved:", args.output)


if __name__ == "__main__":
    main()
