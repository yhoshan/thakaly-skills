import unittest
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'skill.py'
spec = importlib.util.spec_from_file_location('test_module', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestActualResults(unittest.TestCase):
    def test_expected_results(self):
        a=[{'title':'بحث','author':'أ','year':'2024','method':'تحليلي','findings':'نتيجة','source_locator':'ص 1'},{'title':'آخر','author':'ب','year':'2025','method':'','findings':'نتيجة','source_locator':''}]
        r=m.analyze(a)
        self.assertEqual(r[0]['verification'],'PRESENT_UNVERIFIED')
        self.assertEqual(r[1]['verification'],'REVIEW')
        self.assertIn('source_locator',r[1]['missing_fields'])

if __name__ == '__main__':
    unittest.main()
