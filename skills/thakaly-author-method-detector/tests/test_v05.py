import unittest
from detect_method import extract

class ContextRegressionV05(unittest.TestCase):
 def categories(self,s):
  out=extract({'text':s});return {x['category'] for x in out['items']}
 def test_consensus_plural(self):
  self.assertIn('consensus_reference',self.categories('فإن الجميع من الحجة مجمعون على هذا.'))
 def test_consensus_not_from_arbitrary_plural(self):
  self.assertNotIn('consensus_reference',self.categories('فإن الجميع من الطلاب مجمعون على الموعد.'))
 def test_reason_lisihha(self):
  self.assertIn('reasoning',self.categories('وهذا الاختيار لصحة معناه.'))
 def test_reason_ma_yadullu(self):
  self.assertIn('reasoning',self.categories('وما يدل على صحة ما قلنا في ذلك قوله تعالى.'))
 def test_qolna_no_objection(self):
  self.assertNotIn('response',self.categories('وما يدل على صحة ما قلنا في ذلك الآية التالية.'))
 def test_qolna_after_objection(self):
  self.assertIn('response',self.categories('فإن قيل: ما الحجة؟ قلنا: الدليل هو النص.'))
 def test_quotation_requires_review(self):
  out=extract({'text':'قال أحدهم: «وأولى هذه الأقوال بالصواب قول كذا»'})
  self.assertTrue(all(x['assessment']=='review_required' for x in out['items']))
 def test_offsets_valid(self):
  s='فإن الجميع من الحجة مجمعون. وما يدل على صحة ما قلنا بيان المعنى.'
  out=extract({'text':s})
  self.assertTrue(all(s[x['start']:x['end']]==x['trigger'] for x in out['items']))
if __name__=='__main__':unittest.main()
