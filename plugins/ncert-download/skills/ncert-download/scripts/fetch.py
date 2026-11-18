"""Download and verify one shard of the NCERT list. Never prints PDF text.

python -I fetch.py <dl_list.csv> <shard> <Textbook_Corpus dir> <results.jsonl> [workers]
Per file: stream to .part, check size, %PDF header, open with pymupdf, page count, sha256,
printed page number (folio) per page from the text layer. One JSON line per file in results.
Re-running skips files already recorded as ok whose sha256 still matches.
"""
import csv, hashlib, json, os, sys, time, datetime, threading
from concurrent.futures import ThreadPoolExecutor
import ssl
import requests
import pymupdf
from requests.adapters import HTTPAdapter


class SystemCA(HTTPAdapter):
    """Trust the operating system's certificate store: certifi alone lacks NCERT's intermediate certificate."""
    def init_poolmanager(self, *a, **k):
        k["ssl_context"] = ssl.create_default_context()
        return super().init_poolmanager(*a, **k)


HTTP = requests.Session()
HTTP.mount("https://", SystemCA())

lst, shard, root, out = sys.argv[1:5]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 2
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
DIGITS = {}
for base in (0x0660, 0x06F0, 0x0966, 0x0AE6, 0x0C66):
    for i in range(10):
        DIGITS[chr(base + i)] = str(i)
lock = threading.Lock()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def folio(page):
    """Printed page number: a 1-3 digit word in the top or bottom 9% of the page, nearest the edge."""
    H = page.rect.height
    best = None
    for x0, y0, x1, y1, w, *_ in page.get_text("words"):
        t = "".join(DIGITS.get(ch, ch) for ch in w.strip())
        if not (t.isdigit() and 1 <= len(t) <= 3):
            continue
        d = min(y0, H - y1)
        if d > 0.09 * H:
            continue
        if best is None or d < best[0]:
            best = (d, int(t))
    return best[1] if best else None


def verify(path):
    with open(path, "rb") as f:
        head = f.read(5)
    r = {"header_ok": head == b"%PDF-"}
    doc = pymupdf.open(path)
    r["pages"] = doc.page_count
    fol = [folio(p) for p in doc]
    doc.close()
    offs = [f - (i + 1) for i, f in enumerate(fol) if f is not None]
    r["folios"] = fol
    r["folio_found"] = len(offs)
    if offs:
        mode = max(set(offs), key=offs.count)
        r["offset"] = mode
        r["offset_agree"] = round(offs.count(mode) / len(offs), 2)
        r["first_printed"] = 1 + mode
        r["last_printed"] = doc_pages = r["pages"] + mode
    return r


def done_ok():
    ok = {}
    if os.path.exists(out):
        for line in open(out, encoding="utf-8"):
            j = json.loads(line)
            if j.get("status") == "ok":
                ok[j["local_path"]] = j["sha256"]
    return ok


def work(row, prev):
    dest = os.path.join(root, row["local_path"])
    res = {k: row[k] for k in ("set", "shard", "chapter_key", "language", "url", "local_path", "expected_size", "last_modified", "book_code")}
    if row["local_path"] in prev and os.path.exists(dest) and sha256(dest) == prev[row["local_path"]]:
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    err = None
    for attempt in range(4):
        try:
            with HTTP.get(row["url"], headers=UA, stream=True, timeout=(20, 120)) as resp:
                resp.raise_for_status()
                with open(tmp, "wb") as f:
                    for b in resp.iter_content(1 << 16):
                        f.write(b)
            size = os.path.getsize(tmp)
            if str(size) != row["expected_size"]:
                raise IOError(f"size {size} != expected {row['expected_size']}")
            os.replace(tmp, dest)
            err = None
            break
        except Exception as e:
            err = f"{type(e).__name__}: {e}"[:300]
            time.sleep(5 * (attempt + 1))
    if err:
        if os.path.exists(tmp):
            os.remove(tmp)
        res.update(status="download_failed", error=err)
        return res
    res["size_bytes"] = os.path.getsize(dest)
    res["sha256"] = sha256(dest)
    try:
        res.update(verify(dest))
        res["status"] = "ok" if res["header_ok"] and res["pages"] > 0 else "verify_failed"
    except Exception as e:
        res.update(status="verify_failed", error=f"{type(e).__name__}: {e}"[:300])
    res["downloaded_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    time.sleep(0.5)
    return res


rows = [r for r in csv.DictReader(open(lst, encoding="utf-8")) if r["shard"] == shard]
prev = done_ok()
counts = {}
with ThreadPoolExecutor(workers) as ex, open(out, "a", encoding="utf-8") as fo:
    for res in ex.map(lambda r: work(r, prev), rows):
        if res is None:
            counts["skipped_already_ok"] = counts.get("skipped_already_ok", 0) + 1
            continue
        with lock:
            fo.write(json.dumps(res, ensure_ascii=False) + "\n")
            fo.flush()
        counts[res["status"]] = counts.get(res["status"], 0) + 1
        if res["status"] != "ok":
            print("FAIL", res["chapter_key"], res["language"], res.get("error"), flush=True)
print("SHARD", shard, "rows", len(rows), counts, flush=True)
