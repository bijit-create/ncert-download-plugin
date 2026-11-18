"""Merge download results into Textbook_Corpus: manifest.csv, alignment.csv, checksums.csv,
check.json for chapter folders that hold en.pdf plus another language, and a Drive staging tree.

python -I postprocess.py <dl_dir> <Textbook_Corpus dir>
Idempotent: rows with source=ncert.nic.in are rebuilt from the results on every run.
"""
import csv, glob, hashlib, json, os, sys, collections

dl, root = sys.argv[1:3]
LANGS = ["en", "hi", "gu", "te", "ur", "pa", "ta", "or", "bn", "mr", "kn", "und"]
LANG_NAME = {"en": "English", "hi": "Hindi", "gu": "Gujarati", "te": "Telugu", "ur": "Urdu", "pa": "Punjabi",
             "ta": "Tamil", "or": "Odia", "bn": "Bengali", "mr": "Marathi", "kn": "Kannada"}
G10_SS_BOOK = {"": "GEO", "P2": "ECO", "P3": "HIST", "P4": "CIV"}

lst = {r["local_path"]: r for f in glob.glob(f"{dl}/dl_list*.csv") for r in csv.DictReader(open(f, encoding="utf-8"))}
def folio_fit(j):
    """Printed page = pdf index + offset. Trust the modal offset only when enough pages carry it;
    isolated digits (chapter numbers, figure labels) are ignored as outliers."""
    fol = j.get("folios") or []
    offs = [f - (i + 1) for i, f in enumerate(fol) if f is not None]
    j["folio_ok"] = False
    if offs:
        mode = max(set(offs), key=offs.count)
        support = offs.count(mode)
        j["folio_support"] = support
        if support >= max(3, 0.4 * j["pages"]):
            j.update(folio_ok=True, offset=mode, first_printed=1 + mode, last_printed=j["pages"] + mode)
    if not j["folio_ok"]:
        for k in ("offset", "first_printed", "last_printed"):
            j.pop(k, None)


res = {}
for f in sorted(glob.glob(f"{dl}/results_*.jsonl")):
    for line in open(f, encoding="utf-8"):
        j = json.loads(line)
        if j["local_path"] in res and res[j["local_path"]]["status"] == "ok" and j["status"] != "ok":
            continue
        if j["status"] == "ok":
            folio_fit(j)
        res[j["local_path"]] = j

# ---------- manifest.csv ----------
mpath = f"{root}/manifest.csv"
mrows = list(csv.DictReader(open(mpath, encoding="utf-8-sig")))
mf = list(mrows[0].keys())
for extra in ("source", "url", "sha256", "local_path"):
    if extra not in mf:
        mf.append(extra)
for r in mrows:
    r.setdefault("source", "drive")
    for extra in ("url", "sha256", "local_path"):
        r.setdefault(extra, "")
mrows = [r for r in mrows if r["source"] != "ncert.nic.in"]
new_ok = []
for lp, j in sorted(res.items()):
    L = lst[lp]
    yr = j["last_modified"][12:16]
    notes = [f"ncert.nic.in Last-Modified {yr}; site shows no reprint year"]
    if L["set"] in ("B", "E"):
        notes.insert(0, "local working copy; byte size equals the Drive file, not for upload")
    if L.get("fix_note"):
        notes.insert(0, L["fix_note"])
    mislab = L.get("fix_note", "").startswith("MISLABELLED")
    if j["status"] == "ok":
        notes.append(f"pages {j['pages']}")
        if j["folio_ok"]:
            notes.append(f"printed pp {j['first_printed']}-{j['last_printed']} (folio on {j['folio_support']}/{j['pages']} pages)")
        else:
            notes.append("printed page numbers not readable from the text layer; read them from page images")
        if not mislab:
            new_ok.append((L, j))
    else:
        notes.append(j.get("error", ""))
    if L["grade"] == "10" and L["subject"] == "SS":
        notes.append(f"book {L['book_code']} ({G10_SS_BOOK[L['part']]})")
    mrows.append(dict(chapter_key=L["chapter_key"], board="NCERT", subject=L["subject"], grade=L["grade"], edition="2026",
                      part=L["part"], chapter=L["chapter"], language=L["language"],
                      title=f"{L['book_title']} ch{L['chapter']} ({L['url'].rsplit('/', 1)[1]})", drive_id="",
                      size_bytes=j.get("size_bytes", ""), drive_path="",
                      status="mislabelled" if mislab else (("local_copy" if L["set"] in ("B", "E") else "ok") if j["status"] == "ok" else j["status"]), notes="; ".join(notes), owner="",
                      source="ncert.nic.in", url=L["url"], sha256=j.get("sha256", ""), local_path=lp))
with open(mpath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=mf)
    w.writeheader()
    w.writerows(mrows)

# ---------- alignment.csv ----------
apath = f"{root}/alignment.csv"
arows = list(csv.DictReader(open(apath, encoding="utf-8-sig")))
fixed = ["chapter_key", "board", "subject", "grade", "edition", "part", "chapter"]
af = fixed + LANGS + [f"ed_{l}" for l in LANGS] + ["n_langs"] + [f"has_en_{l}" for l in LANGS if l not in ("en", "und")] + ["note"]
byk = {r["chapter_key"]: r for r in arows}
for r in arows:  # drop earlier local: entries so reruns stay clean
    for l in LANGS:
        if r.get(l, "").startswith("local:"):
            r[l] = ""
            r[f"ed_{l}"] = ""
for L, j in new_ok:
    k = L["chapter_key"]
    if k not in byk:
        byk[k] = {c: "" for c in af}
        byk[k].update(chapter_key=k, board="NCERT", subject=L["subject"], grade=L["grade"], edition="2026",
                      part=L["part"], chapter=L["chapter"])
        if L["grade"] == "10" and L["subject"] == "SS":
            byk[k]["note"] = f"G10 SS book {G10_SS_BOOK[L['part']]} ({L['book_code'][:-1]}*); part label = NCERT book number"
        arows.append(byk[k])
    r = byk[k]
    if not r.get(L["language"]):
        r[L["language"]] = "local:" + L["local_path"]
        r[f"ed_{L['language']}"] = "NA"
for r in arows:
    for c in af:
        r.setdefault(c, "")
    present = [l for l in LANGS if r[l]]
    r["n_langs"] = len(present)
    for l in LANGS:
        if l not in ("en", "und"):
            r[f"has_en_{l}"] = int(bool(r["en"] and r[l]))
arows.sort(key=lambda r: (r["board"], r["subject"], int(r["grade"] or 0), r["part"], r["chapter"]))
with open(apath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=af)
    w.writeheader()
    w.writerows(arows)

# ---------- checksums.csv ----------
cpath = f"{root}/checksums.csv"
cf = ["chapter_key", "language", "drive_id", "size_bytes", "md5", "sha256", "pages", "downloaded_at", "source", "url",
      "local_path", "first_printed", "last_printed", "folio_found"]
old = {(r["local_path"]): r for r in csv.DictReader(open(cpath, encoding="utf-8-sig"))} if os.path.exists(cpath) else {}
crow = {}
for L, j in new_ok:
    lp = L["local_path"]
    if lp in old and old[lp]["sha256"] == j["sha256"] and old[lp]["md5"]:
        md5 = old[lp]["md5"]
    else:
        h = hashlib.md5()
        with open(os.path.join(root, lp), "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        md5 = h.hexdigest()
    crow[lp] = dict(chapter_key=L["chapter_key"], language=L["language"], drive_id="", size_bytes=j["size_bytes"], md5=md5,
                    sha256=j["sha256"], pages=j["pages"], downloaded_at=j["downloaded_at"], source="ncert.nic.in",
                    url=L["url"], local_path=lp, first_printed=j.get("first_printed", ""),
                    last_printed=j.get("last_printed", ""), folio_found=j.get("folio_support", 0) if j["folio_ok"] else 0)
for lp, r in old.items():
    if r.get("source") != "ncert.nic.in":
        crow.setdefault(lp, r)
with open(cpath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cf)
    w.writeheader()
    w.writerows(sorted(crow.values(), key=lambda r: r["local_path"]))

# ---------- check.json where en.pdf and a target are both local ----------
by_folder = collections.defaultdict(dict)
for L, j in new_ok:
    by_folder[os.path.dirname(L["local_path"])][L["language"]] = j
checks = []
for folder, langs in sorted(by_folder.items()):
    if "en" not in langs:
        continue
    en = langs["en"]
    out = {"chapter_key": en["chapter_key"], "pairs": {}}
    for lang, t in langs.items():
        if lang == "en":
            continue
        c = {"pages_en": en["pages"], "pages_target": t["pages"]}
        if not en["folio_ok"] or not t["folio_ok"]:
            c["result"] = "needs_image_folios"
            c["reason"] = "no folio in the text layer of " + ", ".join(x for x, y in (("en", en), (lang, t)) if not y["folio_ok"])
        else:
            const = True
            pe = set(range(en["first_printed"], en["last_printed"] + 1))
            pt = list(range(t["first_printed"], t["last_printed"] + 1))
            subset = set(pt) <= pe
            c.update(first_printed=t["first_printed"], last_printed=t["last_printed"],
                     en_first=en["first_printed"], en_last=en["last_printed"],
                     leading_en=max(0, t["first_printed"] - en["first_printed"]),
                     trailing_en=max(0, en["last_printed"] - t["last_printed"]),
                     offsets_constant=const, target_subset_of_en=subset,
                     result="pass" if (const and subset) else "fail")
        out["pairs"][lang] = c
        checks.append((en["chapter_key"], lang, c["result"], c.get("trailing_en", ""), c["pages_en"], c["pages_target"]))
    json.dump(out, open(os.path.join(root, folder, "check.json"), "w", encoding="utf-8"), indent=1)

# ---------- Drive staging (hard links, no extra disk) ----------
G10_SS_TITLE = {"P2": "Economics (Understanding Economic Development)", "P3": "History (India and the Contemporary World-II)",
                "P4": "Political Science (Democratic Politics)"}


def drive_folder(g, s, p, lang):
    """Folder (relative to Grade_<g>/<Language>) matching the existing NCERTs Drive layout.
    Existing folders are reused by name; new ones copy the English sibling's name (':' dropped for Windows)."""
    tag = f"_{p}" if p else ""
    if lang == "gu":  # only G6 SS chapters are new; the book sits in .../Social Science/SS_GJ_BOOK
        return "Gujarati_NCERT/Social Science/SS_GJ_Chapters", tag
    if g == 10 and s == "SS":
        return f"SOCIAL SCIENCE - {G10_SS_TITLE[p]}", "_" + G10_SS_BOOK[p]
    if g == 9 and s == "MATH":
        return ("MATHS (Ganita Manjari Part - II)" if p else "MATHS"), tag
    if g == 9 and s == "SS":
        return ("SOCIAL SCIENCE (Understanding Society Part - II)" if p else "SOCIAL SCIENCE"), tag
    if s == "MATH":
        return ("Mathematics" + (f" (Ganita Prakash Part - {'I' * int(p[1])})" if p else "")), tag
    if s == "SS":
        return ("Social Science" + (f" - Exploring Society India and Beyond Part {'I' * int(p[1])}" if p else "")), tag
    return {"SCIENCE": "Science", "EVS": "EVS"}[s], tag


stage = os.path.join(root, "_drive_staging", "NCERTs")
want = set()
relinked = 0
SUBJ_FOLDER = {"MATH": "Mathematics", "SCIENCE": "Science", "EVS": "EVS", "SS": "Social Science"}
SUBJ_CODE = {"MATH": "MATH", "SCIENCE": "SCIENCE", "EVS": "EVS", "SS": "SOCIALSCIENCE"}
staged = 0
for L, j in new_ok:
    if L["set"] in ("B", "E"):
        continue  # already on Drive
    g, s, p = int(L["grade"]), L["subject"], L["part"]
    sub, tag = drive_folder(g, s, p, L["language"])
    yr = j["last_modified"][12:16]
    name = f"NCERT_G{g:02d}_{SUBJ_CODE[s]}_{L['language'].upper()}_{yr}{tag}_CH{L['chapter']}.pdf"
    d = os.path.join(stage, f"Grade_{g}", LANG_NAME[L["language"]], *sub.split("/"))
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name)
    want.add(os.path.normcase(os.path.abspath(dst)))
    src = os.path.join(root, L["local_path"])
    if os.path.exists(dst) and not os.path.samefile(src, dst):
        os.remove(dst)  # link left from before a renumbering; points at another chapter
        relinked += 1
    if not os.path.exists(dst):
        os.link(src, dst)
    staged += 1

stale = []
for dp, dn, fn in os.walk(stage):
    for f in fn:
        q = os.path.join(dp, f)
        if os.path.normcase(os.path.abspath(q)) not in want:
            try:
                os.remove(q)  # stale hard link from an earlier run; the corpus file is untouched
                stale.append(q)
            except OSError as e:
                print("could not remove stale link", q, e)
for dp, dn, fn in sorted(os.walk(stage), key=lambda x: -len(x[0])):
    if not os.listdir(dp):
        try:
            os.rmdir(dp)
        except OSError:
            pass
print("stale links removed", len(stale), "| relinked", relinked)
st = collections.Counter(j["status"] for j in res.values())
print("results", len(res), dict(st), "| manifest rows", len(mrows), "| alignment rows", len(arows), "| staged", staged)
print("checks", collections.Counter(c[2] for c in checks))
for c in checks:
    print("CHECK", *c)
