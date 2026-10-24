import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_attribution import audit

BASE={'id':'test','source_title':'الرسالة','source_location':'باب خبر الواحد',
'source_excerpt':'قال الشافعي: إن الخبر حجة','attributed_to':'الشافعي','attribution_formula':'قال الشافعي',
'attribution_mode':'direct','transmission_nature':'verbatim','text_layer':'متن','quote':'إن الخبر حجة'}
class TestCues(unittest.TestCase):
 def test_direct_prose(self):
  self.assertEqual(audit(BASE)['status'],'structurally_consistent')
 def test_false_direct_chain(self):
  d={**BASE,'source_excerpt':'أخبرنا مالك عن زيد بن أسلم عن عطاء','attribution_formula':'أخبرنا مالك عن زيد بن أسلم', 'quote':'عطاء'}
  self.assertIn('possible_mediated_attribution_mislabeled_direct',[x['code'] for x in audit(d)['issues']])
 def test_false_direct_uncertain(self):
  d={**BASE,'source_excerpt':'وقد سمعت من يصل هذا الحديث ولا يحضرني ذكر من وصله','quote':'هذا الحديث'}
  self.assertIn('possible_uncertain_attribution_mislabeled_direct',[x['code'] for x in audit(d)['issues']])
 def test_no_guarantee_with_no_cues(self):
  self.assertIn('no validation',audit(BASE)['verification_limit'])
if __name__=='__main__':unittest.main()
