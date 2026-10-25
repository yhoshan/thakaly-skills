import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detect_method import extract
class Improvements(unittest.TestCase):
 def run_case(self,t):return extract({'text':t})
 def test_consensus_expression(self):
  d=self.run_case('وإنما قلنا ذلك؛ لإجماع الجميع على كذا.')
  self.assertEqual(d['counts']['consensus_reference'],1)
  self.assertIn('wording_is_not_evidence_of_actual_consensus',d['items'][-1]['warnings'])
 def test_innama_qolna_reasoning_not_response(self):
  d=self.run_case('وإنما قلنا ذلك أولى؛ لأن العبارة محتملة.')
  self.assertEqual(d['counts']['response'],0)
  self.assertGreaterEqual(d['counts']['reasoning'],1)
 def test_author_restart_clears_isnad(self):
  d=self.run_case('حدثنا فلان عن فلان، قال: كذا.\nقال أبو جعفر: وأولى الأقوال في ذلك الصواب.')
  it=next(x for x in d['items'] if x['category']=='preference')
  self.assertNotIn('preceded_by_transmission_in_same_segment',it['warnings'])
 def test_reported_quote_warning(self):
  d=self.run_case('قال بعض أهل العلم: «والصحيح عندي أن القول كذا».')
  it=d['items'][0]
  self.assertIn('inside_quotation_marks',it['warnings'])
 def test_unexplained_response_not_confident(self):
  d=self.run_case('قلنا إن المسألة محل نظر.')
  self.assertEqual(d['counts']['response'],0)  # No objection: bare قلنا is not a response
 def test_offsets_on_real_multiline(self):
  s='حدثنا فلان.\nقال أبو جعفر: وأولى الأقوال كذا.\nوإنما قلنا ذلك؛ لإجماع الجميع.'
  d=self.run_case(s)
  self.assertTrue(all(s[x['start']:x['end']]==x['trigger'] for x in d['items']))
 def test_consensus_is_not_validation(self):
  d=self.run_case('لإجماع الجميع على الأمر.')
  self.assertEqual(d['items'][0]['assessment'],'review_required')
if __name__=='__main__':unittest.main()
