import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_attribution import run
class TestAttribution(unittest.TestCase):
 def base(self):
  return dict(id='t',source_title='كتاب افتراضي',source_location='ص 12',source_excerpt='قال المؤلف: هذا نص تجريبي.',attributed_to='المؤلف',attribution_formula='قال',attribution_mode='direct',transmission_nature='verbatim',text_layer='المتن',quote='هذا نص تجريبي.')
 def test_direct(self):
  r=run([self.base()])['results'][0]; self.assertEqual(r['status'],'structurally_consistent');self.assertTrue(r['quote_found_in_supplied_excerpt'])
 def test_mediated(self):
  d=self.base();d.update(source_title='كتاب ناقل افتراضي',source_excerpt='نقل فلان: هذا نص تجريبي.',attributed_to='شخص آخر',attribution_mode='mediated',attribution_formula='نقل',transmission_chain=['الناقل','المنسوب إليه'],chain_type='نقل علمي',claimed_direct=True)
  r=run([d])['results'][0];self.assertIn('unjustified_directness_claim',[x['code'] for x in r['issues']]);self.assertEqual(r['original_input']['source_title'],'كتاب ناقل افتراضي')
 def test_uncertain(self):
  d=self.base();d.update(attribution_mode='uncertain',attribution_formula='حُكي',reservation='نسبة غير جازمة',claimed_direct=True)
  r=run([d])['results'][0];self.assertIn('unjustified_directness_claim',[x['code'] for x in r['issues']]);self.assertEqual(r['original_input']['reservation'],'نسبة غير جازمة')
 def test_missing_reservation(self):
  d=self.base();d.update(attribution_mode='uncertain',reservation='')
  self.assertIn('missing_reservation',[x['code'] for x in run([d])['results'][0]['issues']])
if __name__=='__main__':unittest.main()
