import unittest
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'skill.py'
spec = importlib.util.spec_from_file_location('test_module', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestActualResults(unittest.TestCase):
    def test_expected_results(self):
        a=[{'title':'أ','topic':'تفسير','method':'تحليلي','year':'2024'},{'title':'ب','topic':'تفسير','method':'تحليلي','year':'2024'},{'title':'ج','topic':'تفسير','method':'تحليلي','year':'2025'}]
        r=m.analyze(a)
        self.assertEqual([x['studies_count'] for x in r],[2,1])

if __name__ == '__main__':
    unittest.main()
