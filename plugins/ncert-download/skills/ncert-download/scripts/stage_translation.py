"""Translation-folder staging = every downloaded file incl. English working copies, Drive layout, hard links.
python -I stage_translation.py <Textbook_Corpus dir>"""
import csv, glob, json, os, sys
root = sys.argv[1]
ROMAN = {"1": "I", "2": "II"}
G10_SS = {"": ("GEO", "Geography (Contemporary India-II)"), "P2": ("ECO", "Economics (Understanding Economic Development)"),
          "P3": ("HIST", "History (India and the Contemporary World-II)"), "P4": ("CIV", "Political Science (Democratic Politics)")}


def drive_folder(g, s, p, lang):
    """One consistent subject-folder name per book, same in every language."""
    if g == 10 and s == "SS":
        return f"Social Science - {G10_SS[p][1]}", "_" + G10_SS[p][0]
    part = ROMAN[p[1]] if p else ("I" if g == 9 and s in ("MATH", "SS") else "")
    tag = f"_{p}" if p else ""
    if s == "MATH":
        book = {7: "Ganita Prakash", 8: "Ganita Prakash", 9: "Ganita Manjari"}.get(g)
        return ("Mathematics" + (f" ({book} Part - {part})" if part else "")), tag
    if s == "SS":
        book = {7: "Exploring Society India and Beyond", 8: "Exploring Society India and Beyond", 9: "Understanding Society India and Beyond"}.get(g)
        return ("Social Science" + (f" ({book} Part - {part})" if part else "")), tag
    return {"SCIENCE": "Science", "EVS": "EVS"}[s], tag


LANG_NAME = {"en": "English", "hi": "Hindi", "gu": "Gujarati", "te": "Telugu", "pa": "Punjabi", "ta": "Tamil", "or": "Odia", "bn": "Bengali", "mr": "Marathi", "kn": "Kannada"}
SUBJ_CODE = {"MATH": "MATH", "SCIENCE": "SCIENCE", "EVS": "EVS", "SS": "SOCIALSCIENCE"}
lst = {r["local_path"]: r for f in glob.glob("dl_list*.csv") for r in csv.DictReader(open(f, encoding="utf-8"))}
res = {}
for f in glob.glob("results_*.jsonl"):
    for l in open(f, encoding="utf-8"):
        j = json.loads(l)
        if j["status"] == "ok": res[j["local_path"]] = j
stage = os.path.join(root, "_drive_staging", "Translation")
n = 0; by = {}
for lp, j in sorted(res.items()):
    L = lst[lp]
    if L.get("fix_note", "").startswith("MISLABELLED"): continue
    g, s, p, lang = int(L["grade"]), L["subject"], L["part"], L["language"]
    sub, tag = drive_folder(g, s, p, lang)
    yr = j["last_modified"][12:16]
    name = f"NCERT_G{g:02d}_{SUBJ_CODE[s]}_{lang.upper()}_{yr}{tag}_CH{L['chapter']}.pdf"
    d = os.path.join(stage, f"Grade_{g}", LANG_NAME[lang], *sub.split("/"))
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name)
    if os.path.exists(dst) and not os.path.samefile(os.path.join(root, lp), dst): os.remove(dst)
    if not os.path.exists(dst): os.link(os.path.join(root, lp), dst)
    n += 1; by[lang] = by.get(lang, 0) + 1
print("staged", n, by)
