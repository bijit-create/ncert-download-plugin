"""Build the approved NCERT download list (set A: not on Drive; set C: Telugu G3-8).

python -I build_list.py <discovery_dir> <Textbook_Corpus dir> <out.csv>
Set A = EN/HI/UR chapter PDFs whose exact byte size matches no NCERT file in manifest.csv.
"""
import csv, sys, collections

disc, corpus, out = sys.argv[1:4]
SUBJ = {"MATH": "MATH", "SCI": "SCIENCE", "EVS": "EVS"}


def subject(s):
    return "SS" if s.startswith("SST") else SUBJ[s]


def part(r):
    """Part label used in chapter keys; matches the keys already in alignment.csv."""
    g, s, n = int(r["grade"]), subject(r["subject"]), r["book_code"][-1]
    if g in (7, 8) and s in ("MATH", "SS"):
        return "P" + n
    if g == 9 and s in ("MATH", "SS"):
        return "" if n == "1" else "P" + n  # Drive keys for G9 part I have no part
    if g == 10 and s == "SS":
        return "" if n == "1" else "P" + n  # Drive's unparted G10 SS keys are Contemporary India (jess1)
    return ""


sizes = {int(r["size_bytes"]) for r in csv.DictReader(open(f"{corpus}/manifest.csv", encoding="utf-8-sig"))
         if r["board"] == "NCERT" and r["size_bytes"]}
rows = []
CAND = sys.argv[4] if len(sys.argv) > 4 else "ncert_candidates_more_langs.csv"  # optional 4th arg: another candidates file
for fname, setname in ((CAND, "D"),):
    for r in csv.DictReader(open(f"{disc}/{fname}", encoding="utf-8-sig")):
        if r["item_type"] != "chapter" or r["http_status"] != "200":
            continue
        if (setname == "A" or r["language"].lower() == "gu") and int(r["size_bytes"]) in sizes:
            continue
        g, s, p, ch = int(r["grade"]), subject(r["subject"]), part(r), int(r["chapter"])
        lang = r["language"].lower()
        lang = {"tl": "te"}.get(lang, lang)
        key = f"NCERT-{s}-G{g:02d}-2026" + (f"-{p}" if p else "") + f"-CH{ch:02d}"
        folder = f"NCERT/{s}/G{g:02d}/2026/" + (f"{p.lower()}_" if p else "") + f"ch{ch:02d}"
        shard = lang.upper()
        rows.append(dict(set=setname, shard=shard, chapter_key=key, subject=s, grade=g, part=p, chapter=f"{ch:02d}",
                         language=lang, book_code=r["book_code"], book_title=r["book_title"], url=r["url"],
                         expected_size=r["size_bytes"], last_modified=r["last_modified"],
                         local_path=f"{folder}/{lang}.pdf"))
dup = [k for k, v in collections.Counter((r["chapter_key"], r["language"]) for r in rows).items() if v > 1]
assert not dup, dup
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
c = collections.Counter(r["shard"] for r in rows)
mb = collections.Counter()
for r in rows:
    mb[r["shard"]] += int(r["expected_size"])
for k in sorted(c):
    print(k, c[k], round(mb[k] / 1e6), "MB")
print("total", len(rows), round(sum(mb.values()) / 1e6), "MB")
