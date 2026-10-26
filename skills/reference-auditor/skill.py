import csv,sys,collections,re
REQUIRED={'title','author','year','source'}
def norm(s):
 return re.sub(r'\s+',' ',s.strip().casefold())
def analyze(rows):
 counts=collections.Counter((norm(r['title']),norm(r['author']),r['year'].strip()) for r in rows)
 return [{'title':r['title'],'author':r['author'],'year':r['year'],'missing_fields':' | '.join(k for k in sorted(REQUIRED) if not r[k].strip()),'possible_duplicate': 'YES' if counts[(norm(r['title']),norm(r['author']),r['year'].strip())]>1 else 'NO'} for r in rows]

def run(input_path,output_path):
 with open(input_path,encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or not REQUIRED.issubset(rd.fieldnames):
   raise ValueError('الحقول المطلوبة: '+', '.join(sorted(REQUIRED)))
  rows=list(rd)
 out=analyze(rows)
 with open(output_path,'w',encoding='utf-8-sig',newline='') as f:
  if not out:
   f.write('')
  else:
   wr=csv.DictWriter(f,fieldnames=out[0].keys());wr.writeheader();wr.writerows(out)
 return len(rows),len(out)
if __name__=='__main__':
 if len(sys.argv)!=3:
  raise SystemExit('Usage: python skill.py input.csv output.csv')
 print('input/output records:',run(sys.argv[1],sys.argv[2]))
