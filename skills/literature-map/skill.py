import csv,sys,collections
REQUIRED={'title','year','topic','method'}
def analyze(rows):
 count=collections.Counter((r['topic'].strip(),r['method'].strip(),r['year'].strip()) for r in rows)
 return [{'topic':a,'method':b,'year':c,'studies_count':n} for (a,b,c),n in sorted(count.items())]

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
