import re, json
src = open('textbook.html', encoding='utf-8', errors='replace').read()
i0 = src.index('function change1'); i1 = src.index('</script>', i0); js = src[i0:i1]
js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
js = re.sub(r'(?m)^\s*//.*$', '', js)
rows=[]; cur=None; texts={}
for line in js.splitlines():
    m = re.search(r'tclass\.value==(\d+)\)\s*&&\s*\(document\.test\.tsubject\.options\[sind\]\.text=="([^"]*)"\)', line)
    if m:
        cur=(int(m.group(1)),m.group(2)); texts={}; continue
    m = re.search(r'tbook\.options\[(\d+)\]\.text="([^"]*)"', line)
    if m and cur: texts[int(m.group(1))]=m.group(2)
    m = re.search(r'tbook\.options\[(\d+)\]\.value="textbook\.php\?([A-Za-z0-9_]+)=(\d+)-(\d+)"', line)
    if m and cur:
        idx=int(m.group(1))
        rows.append(dict(cls=cur[0],subject=cur[1],title=texts.get(idx,''),code=m.group(2),ch0=int(m.group(3)),nch=int(m.group(4))))
    elif 'tbook.options' in line and '.value=' in line and cur:
        print('UNPARSED',cur,line.strip())
json.dump(rows,open('site_books.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(rows))
from collections import Counter
print(Counter((r['cls']) for r in rows))
for r in rows:
    if 3<=r['cls']<=10: print(r['cls'],r['subject'],'|',r['title'],'|',r['code'],r['nch'])
