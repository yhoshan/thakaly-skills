import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detect_method import extract
class TestV03(unittest.TestCase):
 def cats(self,s):return extract({'text':s})['counts']
 def test_pref_aha(self):self.assertGreater(self.cats('قال أبو جعفر: وأولى هذه الأقوال بالصواب القول الأول.')['preference'],0)
 def test_pref_readings(self):self.assertGreater(self.cats('وأولى القراءتين في ذلك بالصواب قراءة الجمهور.')['preference'],0)
 def test_pref_own(self):self.assertGreater(self.cats('والقول الذي هو عندي أولى بالصواب ما تقدم.')['preference'],0)
 def test_consensus_all(self):self.assertGreater(self.cats('لإجماع جميعهم على ذلك.')['consensus_reference'],0)
 def test_consensus_scholars(self):self.assertGreater(self.cats('قد أجمع علماء الأمة على ذلك.')['consensus_reference'],0)
 def test_narrative_no_response(self):self.assertEqual(self.cats('وإنما قلنا ذلك لأنه قيل له في موضع آخر.')['response'],0)
 def test_distinct_reporting(self):
  a=extract({'text':'قال بعضهم: «والصحيح عندي كذا».','source':{'location':'موضع'}})['items']
  self.assertTrue(any('inside_quotation_marks' in x['warnings'] for x in a))
 def test_offset(self):
  s='قال أبو جعفر: وأولى هذه الأقوال بالصواب ما قلنا.\nقد أجمع علماء الأمة.'
  for x in extract({'text':s})['items']:self.assertEqual(s[x['start']:x['end']],x['trigger'])
 def test_unseen_preference(self):self.assertGreater(self.cats('أولى هذه الأقوال بالصواب عندي القول الثاني.')['preference'],0)
 def test_unseen_consensus(self):self.assertGreater(self.cats('لإجماع جميع أهل العلم على ذلك.')['consensus_reference'],0)
 def test_unseen_quoted(self):
  a=extract({'text':'حكى فلان: «وأولى القراءتين في ذلك بالصواب الأولى». '})['items']
  self.assertTrue(any(x['category']=='preference' and x['assessment']=='review_required' for x in a))
 def test_unseen_passive_quote(self):self.assertEqual(self.cats('قيل له ذلك، ثم رجع عن القول.')['response'],0)
