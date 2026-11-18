---
name: ncert-download
description: Download NCERT textbook chapter PDFs from ncert.nic.in for classes 3-10 (Maths, Science, EVS, Social Science) in English, Hindi, Urdu, Telugu, Punjabi, Tamil, Odia, Bengali, Marathi, Gujarati or Kannada, check each file, and lay them out in folders for translation. Use when someone asks to download NCERT books or chapters, add a language to the textbook set, re-run failed NCERT downloads, or check downloaded NCERT PDFs.
---

# NCERT chapter download

All scripts are in `scripts/` next to this file. They need Python 3 with `requests` and `pymupdf`
(`pip install requests pymupdf`). Run them one stage after another. Each stage writes files that the next one reads.

The download folder is called the **corpus folder** below. Chapters are saved as
`NCERT/<SUBJECT>/G<grade>/2026/[p2_]ch<NN>/<lang>.pdf`, for example `NCERT/MATH/G06/2026/ch03/ta.pdf`.

## 1. Find what exists on NCERT's server (`scripts/discovery/`)

The results of the last check are already included, so you can usually skip this step:
- `site_books.json` lists every book on ncert.nic.in/textbook.php, with its code and chapter count.
- `ncert_candidates.csv` (English, Hindi, Urdu), `ncert_candidates_telugu.csv` and
  `ncert_candidates_more_langs.csv` (Punjabi, Tamil, Odia, Bengali, Marathi, Gujarati) list every chapter
  file with its link, size and date.
- `NCERT_CODING.md` explains NCERT's file names (class letter + language code + subject + book number)
  and lists the gaps found on the server.

To check again, or to add a language, run these from inside `scripts/discovery/`:
- `python probe.py` checks English, Hindi and Urdu books.
- `python more_langs.py` checks the other languages. You can pass ISO codes to check only those, for example
  `python more_langs.py kn` writes `ncert_candidates_kn.csv`. The supported codes are pa, ta, or, bn, mr, gu and kn.
  To add another language, put its NCERT code in `LANGS` in `more_langs.py`. The codes are listed in `NCERT_CODING.md`.

These only send HEAD requests (asking whether a file exists) and download nothing.

## 2. Build the download list

```
python -I scripts/build_list.py      scripts/discovery <corpus> runs/dl_list.csv        # English/Hindi/Urdu + Telugu
python -I scripts/build_list_more.py scripts/discovery <corpus> runs/dl_list_more.csv   # other languages
python -I scripts/build_list_more.py scripts/discovery <corpus> runs/dl_list_kn.csv ncert_candidates_kn.csv
```
These scripts skip any chapter that is already in `<corpus>/manifest.csv` with the same byte size. For a new
corpus folder, first make a `manifest.csv` with only the header `board,size_bytes,source`.
`build_list_en.py` and `build_list_higu.py` make English, Hindi and Gujarati working copies of files the corpus already has.
Each list row has a `shard`: the language code in capitals (TA, KN, ...), or for Telugu and Urdu, `TE_G03-05`-style groups.

## 3. Download and check

```
python -I scripts/fetch.py runs/dl_list_more.csv TA <corpus> runs/results_more_TA.jsonl 2
```
Arguments: the list, the shard, the corpus folder, the results file and the number of parallel downloads.
Keep parallel downloads at 2, because NCERT's server drops connections when there are more.
The script writes each file to `.part` first, then checks the size against the list, the `%PDF` start bytes,
that the file opens and its page count, and reads the printed page numbers. It writes one JSON line per file.
**If some files fail (most failures are dropped connections), run the same command again.** Files that already
passed are skipped.

Run `python -I scripts/verify_all.py <corpus>` from inside `runs/` to check every listed file on disk again.

## 4. Merge into the corpus and set up translation folders

- `python -I scripts/postprocess.py runs <corpus>` updates `manifest.csv`, `alignment.csv` (which languages each
  chapter has) and `checksums.csv`, and writes a `check.json` in every chapter folder that has English plus another language.
  It only works on a corpus whose `manifest.csv` and `alignment.csv` already have rows. Skip it for a fresh folder:
  the PDFs and the results files are complete without it.
- `python -I scripts/stage_translation.py <corpus>` (run from inside `runs/`) builds
  `<corpus>/_drive_staging/Translation/Grade_<n>/<Language>/<Subject>/` with Drive-style file names, such as
  `NCERT_G06_MATH_TA_2025_CH03.pdf`. It uses hard links, so files are not stored twice.

## Known gaps on NCERT's server
- The other languages have books only for classes 3-8. Classes 9-10 return 404.
- Class 8 Social Science Part II does not exist in any language except English.
- More gaps, book by book, are listed at the end of `NCERT_CODING.md`.
