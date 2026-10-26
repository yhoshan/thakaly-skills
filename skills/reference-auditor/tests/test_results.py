import unittest
import importlib.util
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'skill.py'
spec = importlib.util.spec_from_file_location('test_module', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestActualResults(unittest.TestCase):
    def test_expected_results(self):
        a=[{'title':' عنوان   أ ','author':'باحث','year':'2024','source':'مجلة'},{'title':'عنوان أ','author':'باحث','year':'2024','source':''}]
        r=m.analyze(a)
        self.assertEqual([x['possible_duplicate'] for x in r],['YES','YES'])
        self.assertIn('source',r[1]['missing_fields'])

if __name__ == '__main__':
    unittest.main()
