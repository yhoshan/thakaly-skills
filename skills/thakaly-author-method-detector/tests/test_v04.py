import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detect_method import extract

class TestV04(unittest.TestCase):
 def check(self,text,required=(),excluded=()):
  o=extract({'text':text,'source':{'location':'synthetic'}})
  cats={x['category'] for x in o['items']}
  self.assertTrue(set(required)<=cats,(required,cats))
  self.assertFalse(set(excluded)&cats,(excluded,cats))
  for x in o['items']:
   self.assertEqual(text[x['start']:x['end']],x['trigger'])
  return o
 def test_consensus_hujja(self):self.check('وقد كان ذلك لإجماع الحجة من أهل التأويل عليه.',('consensus_reference',))
 def test_reason_wadhalika_an(self):self.check('وذلك أن الدليل يدل على ذلك.',('reasoning',))
 def test_objection_response(self):self.check('فإن قال لنا قائل: من أين لك؟ قيل له: من النقل.',('objection','response'))
 def test_response_without_objection(self):self.check('قيل له في مجلسه حديث طويل.',excluded=('response',))
 def test_innama_reason_not_response(self):self.check('وإنما قلنا ذلك لما ظهر من الدليل.',('reasoning',),('response',))
 def test_no_consensus_statement(self):self.check('واختلف علماء الأمة في هذا الحكم.',excluded=('consensus_reference',))
 def test_no_preference_without_preference_marker(self):self.check('وقد سبق ذكر هذه الأقوال بالصواب والخطأ.',excluded=('preference',))
 def test_transmission_warning(self):
  out=self.check('قال زيد: وأولى هذه الأقوال بالصواب كذا.',('preference',))
  self.assertIn('preceded_by_transmission_in_same_segment',out['items'][0]['warnings'])
 def test_explicit_author_restart(self):
  out=self.check('قال زيد: خلاف ذلك. قال أبو جعفر: وأولى هذه الأقوال بالصواب كذا.',('preference',))
  self.assertNotIn('preceded_by_transmission_in_same_segment',out['items'][0]['warnings'])
if __name__=='__main__':unittest.main()
