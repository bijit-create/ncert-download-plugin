# NCERT textbook PDF coding (observed 2026-10-12)

Source: https://ncert.nic.in/textbook.php. The class/subject/book arrays are inline JS in the page itself (function `change1`), no separate JS file. Each book option has value `textbook.php?<bookcode>=0-<N>`, where N is the chapter count the site declares. A second inline script (the sidebar renderer) generates the chapter list, extras and links.

## URL scheme
`https://ncert.nic.in/textbook/pdf/<bookcode><suffix>.<ext>`

- `<bookcode>` = class letter + medium letter(s) + subject code + book number.
  - Class letter: a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10 (k=11, l=12).
  - Medium: e=English, h=Hindi, u=Urdu. Other languages use two letters: as, bn, bd, dg, gj, kn, ks, mt, ml, mn, np, or, pn, sn, tm, tl (Telugu), sk, mr, ko, si. Class 1 also uses `amr`, `asi` etc. for the same languages.
  - Subject code (2 letters; varies by book, not fixed per subject): mm (Math Mela / Math-Mela, cl 3-5), ev (Our Wondrous World, cl 3-5), gp (Ganita Prakash, cl 6-8), mh (Ganita Manjari cl 9; Mathematics cl 10), cu (Curiosity, Science 6-8), sc (Science 9-10), es (Exploring Society India and Beyond, SST 6-8), st (Understanding Society, SST 9), ss (class 10 SST, see below).
  - Book number: 1 for single books; 1/2 for Part I/II (Math 7, 8, 9; SST 7, 8, 9). Class 10 SST uses 1-4 as four separate books, not parts.
- Suffixes (from the sidebar JS):
  - `01`..`NN` chapter (two digits, no gaps seen)
  - `ps` prelims (front matter, cover, contents)
  - `dd` whole-book **zip** (`.zip`, everything else `.pdf`)
  - `an` answers, `a1`/`a2` appendices, `ax` annexure, `tn` teacher notes, `sm` supplementary material, `gl` glossary, `rf` references, `bt` brain teasers, `ex` exercise, `sk` shabd kosh, `in` index, `qa` prashn abhyas, `pr` persist, `lp` lekhak parichay, `er` errata, `mg`, `pp`, `rc` (labels not shown on site), `wc` warm-up/cool-down, `cc.jpg` cover image, `c1/c2.PNG`.
  - Which extras a book gets is hard-coded per book code in the JS. Of the 79 in-scope books only these exist on the server: ps and dd for all; gl for class 6-8 SST (12 books; not gues1); an for class 9 Science Hindi, class 10 Science EN/HI, class 10 Math EN/HI; a1 for class 10 Math EN/HI/UR and class 10 SST (Geo) EN/HI; a2 for class 10 Math EN/HI/UR. Of these, a2 (all three class 10 Math books) and an for jumh1 exist but are not linked on the site; flagged in the CSV notes.
- Class 10 SST books: jess1/jhss1/juss1 Contemporary India (geography), jess2.. Understanding Economic Development, jess3.. India and the Contemporary World II (history), jess4.. Democratic Politics (civics). CSV subject codes: SST_GEO, SST_ECO, SST_HIST, SST_CIV.

## Server behaviour
- HEAD works with a normal browser UA and with no UA. No redirects, no auth, no blocking seen. 404 returns a 6-byte body. Content-Type is application/pdf or application/zip; there are no soft 200s.
- A single HEAD in the first test returned an empty reply once; a retry succeeded. The script retries 4 times with back-off.
- Last-Modified is the only date signal on the site. The site shows no edition/reprint year (that is inside the prelims PDF). Upload dates: class 3-9 books are 2024-07 to 2026-10; class 9 files were modified as recently as 2026-10-09 (books are still being revised). Class 10 English/Hindi are 2026-03; class 10 Urdu is 2017/2020.
- Page text still says textbooks are "rationalised" (2022-23), but this paragraph is commented out in the HTML. A generic `Rationalised.pdf` link is shown for older books.

## Quirks
- juss3 (class 10 Urdu, India and the Contemporary World II): site declares 5 chapters, server has 8 (ch 6-8 are 83-114 MB each, dated 2017). Check before downloading.
- Class 7 SST Telugu Part-II: site option links Marathi's code `gmres2`. The real Telugu Part-II is `gtles2` (live, not linked).
- Many titles are transliterated Latin (Ganit Mela, Hamara Adhbhut Sansar, Riyazi Mela, Khayal); Hindi/Urdu titles are not in Devanagari/Nastaliq on this page.
- Class labels for "Social Science" in class 9 are `iest1`, `iest2` (SST Part I and II, EN only).

## Media coverage (classes 3-10, Math / Science-EVS / SST, English-Hindi-Urdu)
All books exist in EN, HI and UR (probed, same chapter counts) for: class 3 Math and EVS; class 4 Math and EVS; class 5 Math and EVS; class 6 Math, Science, SST; class 7 Math Part I (all three), Science, SST Part I and II (Urdu SST Part I and II present); class 8 Science; class 10 Math, Science, SST (all four books).

Missing in a medium (site does not list; probing the derived code gave 404 for ch01, ps and dd):
- Class 7 Math Part II: Urdu missing (gugp2).
- Class 8 Math Part II: Urdu missing (hugp2).
- Class 8 SST Part II: Hindi and Urdu missing (hhes2, hues2); English only.
- Class 9 Math Part II (iemh2): Hindi and Urdu missing (ihmh2, iumh2).
- Class 9 Science: Urdu missing (iusc1).
- Class 9 SST Part I and II: Hindi and Urdu missing (ihst1/2, iust1/2); English only.
- Class 10 Science Urdu and Class 10 SST Urdu are the old edition (2017/2020).
- Class 9 Hindi Science is "Anveshan" (ihsc1) and has an `an` answers file; English "Exploration" (iesc1) has none.

## Languages
- The site lists Hindi, English, Urdu plus 20+ other languages for the new NCF books (Assamese, Bengali, Bodo, Dogri, Gujarati, Kannada, Kashmiri, Konkani, Maithili, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit, Santhali, Sindhi, Tamil, Telugu).
- **Telugu is offered** (correction to the brief): all new-NCF Math, EVS, Science and SST books in classes 3-8 exist in Telugu on the server (medium code `tl`, e.g. `ctlmm1`, `ftlgp1`, `gtlcu1`, `htles1`). Class 9 and 10 have no Telugu. Candidate list: `ncert_candidates_telugu.csv` (HEAD-verified, not downloaded).
- For classes 3-8 Math, EVS, Science, SST, the other-language books mirror the English structure and chapter counts.

## Files in this directory
- `ncert_candidates.csv` (982 rows, HEAD-verified existing items for EN/HI/UR)
- `ncert_candidates_telugu.csv` (230 rows)
- `probe_log.csv` (all probes, incl. 404s)
- `site_books.json` (parsed dropdown: class, subject, title, code, declared chapters, all languages and subjects)
- `site_extras.json` (site-declared extras per book code), scripts `parse_site.py`, `parse_extras.py`, `probe.py`, `build_csv.py`, `telugu.py`

## Addendum: other Indian-language media (probed 2026-10-12, HEAD only, 4 parallel)
Output: `ncert_candidates_more_langs.csv` (1,368 rows; language = ISO pa/ta/or/bn/mr/gu). Same code pattern as before: class letter + medium code + subject code + book number (e.g. `fpngp1` = class 6, Punjabi, Ganita Prakash).

Medium codes (site's own): pn = Punjabi, tm = Tamil, or = Odia, bn = Bengali, mr = Marathi, gj = Gujarati. Others seen: as Assamese, bd Bodo, dg Dogri, kn Kannada, ks Kashmiri, ko Konkani, mt Maithili, ml Malayalam, mn Manipuri, np Nepali, sn Santhali, si Sindhi, sk Sanskrit, tl Telugu. (Telugu = tl, Marathi = mr; the earlier "gmres2" is a real Marathi Part-II code.)

Coverage: all of these media exist only for classes 3-8 (Math, EVS in 3-5, Math/Science/SST in 6-8). For classes 9 and 10 every derived code for the six languages (Math, Science, SST, all parts and all four class 10 SST books) returned 404 for ch01, prelims and zip. The same 14 other media exist for the same classes 3-8 books (ch01 probe on all English-derived codes; none for classes 9-10).

Quirks:
- Punjabi class 4 EVS code is `dpev1` (site-listed; the derived `dpnev1` is 404).
- Tamil class 7 SST Part II `gtmes2` is listed on the site but returns 404 for chapters, prelims and zip.
- Tamil class 7 Math Part I `gtmgp1` has 7 chapters on the server (site says 8; ch08 is 404).
- Marathi class 5 Math `emrmm1` has no chapter 12 but has chapters 1-11 and 13-16 (15 files, declared 15).
- Part-I SST class 7 has 13 chapters for Punjabi, Bengali and Marathi (site says 12).
- Whole-book zip missing: Tamil class 5 Math (`etmmm1`), Bengali class 6 SST (`fbnes1`), Marathi class 8 Science (`hmrcu1`, also no prelims). Gujarati class 7 Science (`ggjcu1`) has no prelims.
- Class 8 SST Part II (`hXXes2`) does not exist in any of the six languages (nor in Hindi/Urdu).
