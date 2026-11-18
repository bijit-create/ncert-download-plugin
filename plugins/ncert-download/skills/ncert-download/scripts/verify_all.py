"""Re-check every listed file on disk: exists, size = site size, sha256 = recorded, %PDF header, opens."""
import csv, glob, hashlib, json, os, sys
import pymupdf
root = sys.argv[1]
lst = [r for f in glob.glob("dl_list*.csv") for r in csv.DictReader(open(f, encoding="utf-8"))]
rec = {}
for f in glob.glob("results_*.jsonl"):
    for l in open(f, encoding="utf-8"):
        j = json.loads(l)
        if j["status"] == "ok":
            rec.setdefault(j["local_path"], set()).add(j["sha256"])
bad = []
for r in lst:
    p = os.path.join(root, r["local_path"])
    if not os.path.exists(p):
        bad.append((r["local_path"], "missing")); continue
    if str(os.path.getsize(p)) != r["expected_size"]:
        bad.append((r["local_path"], "size")); continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if h not in rec.get(r["local_path"], ()):
        bad.append((r["local_path"], "sha not recorded")); continue
    if len(rec[r["local_path"]]) > 1:
        bad.append((r["local_path"], f"{len(rec[r['local_path']])} different hashes recorded"))
    with open(p, "rb") as fh:
        if fh.read(5) != b"%PDF-":
            bad.append((r["local_path"], "header")); continue
    try:
        pymupdf.open(p).close()
    except Exception as e:
        bad.append((r["local_path"], f"open {e}"))
print("listed", len(lst), "bad", len(bad))
for b in bad[:40]:
    print("BAD", *b)
