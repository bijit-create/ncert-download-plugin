import json, csv, re, time, threading, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
BASE='https://ncert.nic.in/textbook/pdf/'
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
sem=threading.Semaphore(6)
cache={}
def fetch(url, tries=4):
    if url in cache: return cache[url]
    last=None
    for a in range(tries):
        with sem:
            time.sleep(0.12)
            try:
                req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':UA})
                try:
                    r=urllib.request.urlopen(req,timeout=30); st=r.status; h=r.headers
                except urllib.error.HTTPError as e:
                    st=e.code; h=e.headers
                if st in (403,405,501):
                    req=urllib.request.Request(url,headers={'User-Agent':UA,'Range':'bytes=0-0'})
                    try:
                        r=urllib.request.urlopen(req,timeout=30); st=r.status; h=r.headers; r.read(2)
                    except urllib.error.HTTPError as e:
                        st=e.code; h=e.headers
                    cr=h.get('Content-Range','')
                    size=int(cr.split('/')[-1]) if '/' in cr and cr.split('/')[-1].isdigit() else h.get('Content-Length','')
                else:
                    size=h.get('Content-Length','')
                res=dict(status=st,size=size,lm=h.get('Last-Modified',''),ct=h.get('Content-Type',''),loc=h.get('Location',''))
                if st>=500: raise Exception('5xx %s'%st)
                cache[url]=res; return res
            except Exception as ex:
                last=str(ex); time.sleep(1.5*(a+1))
    res=dict(status='ERR',size='',lm='',ct='',loc='',err=last); cache[url]=res; return res
def exists(res): return res['status'] in (200,206)

EXTRA=['ps','dd','an','a1','a2','ax','tn','sm','gl','rf','bt','ex','in','mg','er','pp']
def probe_book(code,nch):
    out=[]
    miss=0; n=1
    while True:
        u='%s%s%02d.pdf'%(BASE,code,n); r=fetch(u)
        out.append(('chapter',n,u,r))
        if exists(r): miss=0
        else:
            miss+=1
        n+=1
        if n>nch and miss>=3: break
        if n>45: break
    for s in EXTRA:
        ext='zip' if s=='dd' else 'pdf'
        u='%s%s%s.%s'%(BASE,code,s,ext); r=fetch(u)
        out.append((s,None,u,r))
    return out
if __name__=='__main__':
    rows=json.load(open('site_books.json',encoding='utf-8'))
    sel=[r for r in rows if 3<=r['cls']<=10 and r['subject'] in('Mathematics','Science','Social Science','The World Around Us') and r['code'][1] in 'ehu' ]
    # dedupe by code
    seen={}; 
    for r in sel: seen.setdefault(r['code'],r)
    sel=list(seen.values()); print(len(sel),'books in scope',flush=True)
    listed=set(r['code'] for r in rows)
    results={}
    def work(r): 
        return r['code'],probe_book(r['code'],r['nch'])
    with ThreadPoolExecutor(6) as ex:
        for code,out in ex.map(work,sel):
            results[code]=out; print(code,sum(1 for o in out if exists(o[3])),flush=True)
    # unlisted twin media
    stems={}
    for r in sel: stems.setdefault((r['code'][0],r['code'][2:]),r)
    twins=[]
    for (c,rest),r in stems.items():
        for m in 'ehu':
            code=c+m+rest
            if code not in listed: twins.append((code,r))
    print(len(twins),'twin probes',flush=True)
    tw={}
    def tw_work(t):
        code,r=t
        res=[]
        for suf,ext in (('01','pdf'),('ps','pdf'),('dd','zip')):
            res.append((suf,fetch('%s%s%s.%s'%(BASE,code,suf,ext))))
        return code,res
    with ThreadPoolExecutor(6) as ex:
        for code,res in ex.map(tw_work,twins): tw[code]=res
    ser={k:[(a,b,c,d) for a,b,c,d in v] for k,v in results.items()}
    json.dump(dict(results=ser,twins={k:v for k,v in tw.items()},sel=sel),open('probe_raw.json','w'))
    print('done')
