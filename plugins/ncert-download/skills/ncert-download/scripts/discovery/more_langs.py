import json,csv,collections,threading
import probe
from probe import fetch,BASE,exists
probe.sem=threading.Semaphore(4)
from concurrent.futures import ThreadPoolExecutor
probe.EXTRA=['ps','dd','an','a1','a2','ax','tn','sm','gl']
rows=json.load(open('site_books.json',encoding='utf-8'))
listed={r['code']:r for r in rows}
SCOPE=('Mathematics','Science','Social Science','The World Around Us')
en=[r for r in rows if 3<=r['cls']<=10 and r['subject'] in SCOPE and r['code'][1]=='e']
seen={}
for r in en: seen.setdefault(r['code'],r)
en=list(seen.values())
LANGS={'pn':('pa','Punjabi'),'tm':('ta','Tamil'),'or':('or','Odia'),'bn':('bn','Bengali'),'mr':('mr','Marathi'),'gj':('gu','Gujarati'),'kn':('kn','Kannada')}
# Optional: python more_langs.py kn  -> probe only these ISO codes and write ncert_candidates_kn.csv
import sys
PICK=sys.argv[1:]
if PICK: LANGS={m:v for m,v in LANGS.items() if v[0] in PICK}
OUT='ncert_candidates_%s.csv'%'_'.join(PICK) if PICK else 'ncert_candidates_more_langs.csv'
OTHER={'as':'Assamese','bd':'Bodo','dg':'Dogri','ks':'Kashmiri','ko':'Konkani','mt':'Maithili','ml':'Malayalam','mn':'Manipuri','np':'Nepali','sn':'Santhali','si':'Sindhi','sk':'Sanskrit','tl':'Telugu'}
SUB={'Mathematics':'MATH','Science':'SCI','The World Around Us':'EVS','Social Science':'SST'}
def subj(r):
    if r['subject']=='Social Science' and r['cls']==10: return {'1':'SST_GEO','2':'SST_ECO','3':'SST_HIST','4':'SST_CIV'}[r['code'][-1]]
    return SUB[r['subject']]
tasks=[(r,m,r['code'][0]+m+r['code'][2:]) for r in en for m in LANGS]
def w(t):
    r,m,code=t
    a=fetch('%s%s01.pdf'%(BASE,code))
    if not exists(a):
        b=fetch('%s%sps.pdf'%(BASE,code)); c=fetch('%s%sdd.zip'%(BASE,code))
        return t,None,(a['status'],b['status'],c['status'])
    return t,probe.probe_book(code,r['nch']),None
res=[]
with ThreadPoolExecutor(4) as ex:
    for x in ex.map(w,tasks): res.append(x)
# other languages: ch01 only
oth=collections.defaultdict(list)
def w2(t):
    r,m,code=t
    return t,exists(fetch('%s%s01.pdf'%(BASE,code)))
ot=[] if PICK else [(r,m,r['code'][0]+m+r['code'][2:]) for r in en for m in OTHER]
with ThreadPoolExecutor(4) as ex:
    for t,ok in ex.map(w2,ot):
        if ok: oth[t[1]].append((t[0]['cls'],t[2], t[2] in listed))
# stems with parts
stemnums=collections.defaultdict(set)
for r in en: stemnums[(r['code'][0]+r['code'][2:-1],r['subject'])].add(r['code'][-1])
ROMAN={'1':'I','2':'II'}
out=[]; absent=[]
for t,o,miss in res:
    r,m,code=t; iso,name=LANGS[m]
    if o is None: absent.append((r['cls'],subj(r),iso,code,miss)); continue
    part=ROMAN[r['code'][-1]] if r['cls']!=10 and len(stemnums[(r['code'][0]+r['code'][2:-1],r['subject'])])>1 else ''
    title=listed[code]['title'].strip() if code in listed else r['title'].strip()+' (%s)'%name
    for kind,n,u,rs in o:
        if rs['status']!=200: continue
        it={'chapter':'chapter','ps':'prelims','dd':'zip','an':'answers'}.get(kind,'other')
        notes=[]
        if code not in listed: notes.append('not listed on site; found by probe')
        if kind=='chapter' and n>r['nch']: notes.append('beyond site-declared chapter count (%d)'%r['nch'])
        if kind not in('chapter','ps','dd','an'): notes.append(kind)
        out.append(dict(grade=r['cls'],subject=subj(r),language=iso,book_code=code,book_title=title,part=part,item_type=it,chapter=n if kind=='chapter' else '',url=u,http_status=200,size_bytes=rs['size'],last_modified=rs['lm'],notes='; '.join(notes)))
cols=['grade','subject','language','book_code','book_title','part','item_type','chapter','url','http_status','size_bytes','last_modified','notes']
out.sort(key=lambda x:(x['language'],x['grade'],x['subject'],x['book_code'],{'prelims':0,'chapter':1,'answers':2,'other':3,'zip':4}[x['item_type']],x['chapter'] if x['chapter']!='' else 0))
with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
    wr=csv.DictWriter(f,cols); wr.writeheader(); wr.writerows(out)
json.dump(dict(absent=absent,oth={k:v for k,v in oth.items()}),open(OUT.replace('.csv','_meta.json'),'w'))
print(len(out),'rows')
# tables
agg=collections.defaultdict(lambda:[0,0,0,0])
for x in out:
    k=(x['language'],x['grade'],x['subject'])
    if x['item_type']=='chapter': agg[k][0]+=1; agg[k][1]+=int(x['size_bytes'])
    if x['item_type']=='zip': agg[k][2]+=1; agg[k][3]+=int(x['size_bytes'])
for k in sorted(agg): print(k,agg[k][0],round(agg[k][1]/1e6),'zip',agg[k][2],round(agg[k][3]/1e6))
print('ABSENT')
for a in absent: print(a)
print('OTHER')
for m,v in oth.items(): print(m,OTHER[m],sorted(set((c,code,l) for c,code,l in v)))
