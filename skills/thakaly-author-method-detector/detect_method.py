#!/usr/bin/env python3
"""Conservative lexical evidence extraction; not historical attribution verification."""
import argparse
import json
import re
from pathlib import Path

PATTERNS = {
 'preference':[r'و?أولى\s+(?:(?:هذه|تلك)\s+)?(?:الأقوال|القول|القراءتين)(?:\s+(?:في\s+ذلك|عندي|بالصواب))*',r'و?أولى\s+القراءتين(?:\s+في\s+ذلك)?\s+بالصواب',r'والقول\s+الذي\s+هو\s+عندي\s+أولى\s+بالصواب',r'والأولى\s+(?:عندي|بالصواب|بالحق|من\s+ذلك)',r'والصحيح\s+(?:عندي|أن|هو)',r'والراجح\s+(?:عندي|أن|هو)',r'والذي\s+أختاره'],
 'reasoning':[r'وإنما\s+قلنا',r'وذلك\s+(?:أن|لأن)',r'والدليل\s+(?:على\s+ذلك|عليه)',r'لأن',r'إذ\s+إن',r'لصحة\s+(?:معناه|الخبر|ذلك|ما\s+ذكرنا)',r'(?:و)?ما\s+يدل\s+على\s+صحة\s+ما\s+قلنا'],
 'objection':[r'فإن\s+قيل',r'فإن\s+قال\s+(?:لنا\s+)?قائل',r'قد\s+يقال'],
 'response':[r'فالجواب',r'قيل\s+له',r'فيقال\s+له',r'(?<!\w)قلنا(?!\w)'],
 'consensus_reference':[r'لإجماع\s+(?:الجميع|جميعهم|جميع\s+أهل\s+العلم|الحجة(?:\s+من\s+أهل\s+التأويل)?)',r'قد\s+أجمع\s+(?:علماء\s+الأمة|أهل\s+العلم)',r'بإجماع',r'أجمعوا',r'لا\s+خلاف\s+بين',r'(?:الجميع|جميعهم)\s+من\s+الحجة\s+مجمعون',r'(?:الحجة|أهل\s+التأويل)\s+مجمعون'],
}
REPORT = re.compile(r'(?:قال|ذكر|حكى|روى|نقل)\s+[^.!؟\n:،]{1,85}?[:،]|(?:حدثنا|أخبرنا|عن)\s+')
AUTHOR_RESTART = re.compile(r'قال\s+أبو\s+جعفر\s*[:،]|قال\s+المؤلف\s*[:،]')
OBJECTION = re.compile(r'فإن\s+قيل|فإن\s+قال\s+(?:لنا\s+)?قائل|قد\s+يقال')

def _quoted(prefix):
 return prefix.count('«') > prefix.count('»') or prefix.count('“') > prefix.count('”')

def _segment_lines(raw):
 for line in re.finditer(r'[^\n]+', raw):
  body=line.group(); offset=line.start()
  for part in re.finditer(r'[^.!؟]+(?:[.!؟]|$)',body):
   if part.group().strip():
    yield part.group(),offset+part.start(),body,line.start()

def extract(doc):
 if not isinstance(doc,dict) or not isinstance(doc.get('text'),str) or not doc['text'].strip():
  raise ValueError('Input must have nonempty text string')
 source=doc.get('source',{})
 if not isinstance(source,dict):raise ValueError('source must be object')
 raw=doc['text']; found=[]
 for segment,offset,line,line_offset in _segment_lines(raw):
  hits=[]
  for category,patterns in PATTERNS.items():
   for pattern in patterns:
    for hit in re.finditer(pattern,segment):
     hits.append((category,hit.start(),hit.end(),hit.group()))
  dedup=[]
  for item in sorted(hits,key=lambda h:(h[1],-(h[2]-h[1]),h[0])):
   if any(x[0]==item[0] and x[1]<=item[1]<x[2] for x in dedup):continue
   dedup.append(item)
  for category,start,end,trigger in dedup:
   if category=='response' and trigger=='قلنا':
    if not OBJECTION.search(line[:offset-line_offset+start]):continue
    if re.search(r'(?:إنما|صحة\s+ما|معنى\s+ما|دليل\s+ما)\s*$',segment[:start]):continue
   if category=='response' and re.fullmatch(r'قيل\s+له', trigger):
    if not OBJECTION.search(line[:offset-line_offset+start]):continue
   if category=='response' and not OBJECTION.search(line[:offset-line_offset+start]):
    response_without_objection=True
   else:response_without_objection=False
   before=segment[:start]
   restarts=[m for m in AUTHOR_RESTART.finditer(before) if not _quoted(before[:m.start()])]
   local=before[restarts[-1].end():] if restarts else before
   mediated=bool(REPORT.search(local))
   in_quotes=_quoted(before)
   warnings=[]
   if mediated:warnings.append('preceded_by_transmission_in_same_segment')
   if in_quotes:warnings.append('inside_quotation_marks')
   if category=='consensus_reference':warnings.append('wording_is_not_evidence_of_actual_consensus')
   if response_without_objection:warnings.append('response_requires_objection_context')
   absolute_start=offset+start; absolute_end=offset+end
   found.append({'category':category,'trigger':trigger,'evidence':segment.strip(),
     'start':absolute_start,'end':absolute_end,'source_location':source.get('location'),
     'assessment':'review_required' if warnings else 'candidate','warnings':warnings,
     'attribution_status':'not_verified'})
 found.sort(key=lambda x:(x['start'],x['category']))
 return {'skill':'thakaly-author-method-detector','version':'0.5.0','source':source,'items':found,
  'counts':{cat:sum(item['category']==cat for item in found) for cat in PATTERNS},
  'limitations':['Text-pattern extraction only: not a verification of authorial attribution, consensus or methodological consistency.',
   'Author-restart and reported-speech flags are heuristic and can fail in long mixed quotations.',
   'Results require comparison with original edition and surrounding context before scholarly adoption.', 'A lexical match does not establish speaker identity, argument validity, or whether a methodology is recurrent.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('-o','--output');args=p.parse_args()
 result=extract(json.loads(Path(args.input).read_text(encoding='utf-8')))
 output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if args.output:Path(args.output).write_text(output,encoding='utf-8')
 else:print(output)
if __name__=='__main__':main()
