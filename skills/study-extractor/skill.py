import csv,sys
REQUIRED={'title','author','year','method','findings','source_locator'}
def analyze(rows):
 return [{'title':r['title'],'missing_fields':' | '.join(k for k in sorted(REQUIRED) if not r[k].strip()),'verification':'REVIEW' if any(not r[k].strip() for k in REQUIRED) else 'PRESENT_UNVERIFIED'} for r in rows]

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
