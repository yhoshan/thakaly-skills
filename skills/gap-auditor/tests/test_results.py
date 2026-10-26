import unittest
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'skill.py'
spec = importlib.util.spec_from_file_location('test_module', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestActualResults(unittest.TestCase):
    def test_expected_results(self):
        a=[{'title':'أ','topic':'تفسير','method':'تحليلي'},{'title':'ب','topic':'فقه','method':'مقارن'}]
        r=m.analyze(a)
        self.assertEqual(len(r),4)
        self.assertEqual(sum(x['status']=='NO_ENTRY_IN_SAMPLE' for x in r),2)

if __name__ == '__main__':
    unittest.main()
