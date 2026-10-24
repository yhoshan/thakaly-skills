import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detect_method import extract
class TestDetector(unittest.TestCase):
 def check(self,text):return extract({'text':text,'source':{'title':'شواهد مصطنعة للاختبار','location':'تجربة'}})
 def test_preference(self):
  x=self.check('والأولى عندي حمل اللفظ على العموم.')
  self.assertEqual(x['counts']['preference'],1);self.assertEqual(x['items'][0]['assessment'],'candidate')
 def test_attribution_warning(self):
  x=self.check('قال بعض أهل العلم: والصحيح عندي حمله على المعنى الآخر.')
  self.assertIn('preceded_by_transmission_in_same_segment',x['items'][0]['warnings'])
 def test_quote_warning(self):
  x=self.check('ورد في النقل: «والراجح عندي أن المقصود كذا».')
  self.assertIn('inside_quotation_marks',x['items'][0]['warnings'])
 def test_objection_response(self):
  x=self.check('فإن قيل: كيف ذلك؟ قلنا: لأن الدليل ظاهر.')
  self.assertEqual(x['counts']['objection'],1);self.assertEqual(x['counts']['response'],1);self.assertEqual(x['counts']['reasoning'],1)
 def test_consensus_caution(self):
  x=self.check('أجمعوا على هذا الحكم.');self.assertEqual(x['items'][0]['assessment'],'review_required')
 def test_exact_evidence_offsets(self):
  s='تمهيد.\nوالصحيح عندي أن هذا أولى.'
  x=self.check(s);it=x['items'][0];self.assertEqual(s[it['start']:it['end']],it['trigger'])
 def test_no_invention(self):
  x=extract({'text':'والأولى عندي هذا.'})
  self.assertNotIn('title',x['source']);self.assertIsNone(x['items'][0]['source_location'])
 def test_negative(self):self.assertEqual(self.check('في هذا الفصل تفاصيل متعددة.')['items'],[])
 def test_input_validation(self):
  with self.assertRaises(ValueError):extract({'text':''})
 def test_multiple(self):
  x=self.check('والصحيح عندي كذا.\nوالأولى عندي كذا.')
  self.assertEqual(x['counts']['preference'],2)
if __name__=='__main__':unittest.main()
