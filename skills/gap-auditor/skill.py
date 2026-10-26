import csv,sys,collections
REQUIRED={'title','topic','method'}
def analyze(rows):
 counts=collections.Counter((r['topic'].strip(),r['method'].strip()) for r in rows)
 topics=sorted({r['topic'].strip() for r in rows if r['topic'].strip()});methods=sorted({r['method'].strip() for r in rows if r['method'].strip()})
 return [{'topic':t,'method':m,'studies_in_sample':counts[(t,m)],'status':'NO_ENTRY_IN_SAMPLE' if counts[(t,m)]==0 else 'COVERED_IN_SAMPLE'} for t in topics for m in methods]

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
