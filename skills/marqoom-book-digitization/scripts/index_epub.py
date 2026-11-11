#!/usr/bin/env python3
"""Extract lexical candidates from EPUB. Attribution is NEVER asserted."""
import argparse,csv,hashlib,json,re,zipfile
from pathlib import Path
from bs4 import BeautifulSoup
DIACRITICS={chr(c) for c in range(0x064b,0x0660)}|{chr(c) for c in range(0x0610,0x061b)}|{'ـ'}
def normalized_with_offsets(text):
    chars=[];pos=[]
    for i,ch in enumerate(text):
        if ch in DIACRITICS:continue
        chars.append({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي'}.get(ch,ch));pos.append(i)
    return ''.join(chars),pos
def scope_of(n,scopes):
    names=[v['name'] for v in scopes if int(v['start'])<=n<=int(v['end'])]
    if len(names)>1:raise ValueError(f'Overlapping editorial scopes at P{n}')
    return names[0] if names else None
def run(epub,config,out):
    epub=Path(epub);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(Path(config).read_text(encoding='utf8'))
    patterns=[(ax['name'],re.compile(p)) for ax in cfg['axes'] for p in ax['patterns']]
    counts={};n=0;units=0;included=0
    with zipfile.ZipFile(epub) as z,(out/'candidates.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['record_id','category','scope','epub_unit','path','cue_original','excerpt_original','start_char','end_char','review_status'])
        files=sorted((int(m.group(1)),p) for p in z.namelist() if (m:=re.search(r'/P(\d+)\.xhtml$',p)))
        for index,path in files:
            units+=1;scope=scope_of(index,cfg['scopes'])
            if scope is None:continue
            included+=1
            soup=BeautifulSoup(z.read(path),'html.parser')
            txt=re.sub(r'\s+',' ',soup.get_text(' ',strip=True))
            normalized,positions=normalized_with_offsets(txt)
            for name,regex in patterns:
                for hit in regex.finditer(normalized):
                    if not positions:continue
                    lo=positions[hit.start()];hi=positions[hit.end()-1]+1;n+=1
                    counts[name]=counts.get(name,0)+1
                    w.writerow([f'IDX-{n:08d}',name,scope,f'P{index}',path,txt[lo:hi],txt[max(0,lo-180):min(len(txt),hi+260)],lo,hi,'lexical candidate; attribution unverified'])
    report={'file':epub.name,'sha256':hashlib.sha256(epub.read_bytes()).hexdigest(),'units_total':units,'units_in_scope':included,'excluded':units-included,'candidates':n,'counts':counts,'scientifically_verified':False}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(run(a.input,a.config,a.out),ensure_ascii=False))
