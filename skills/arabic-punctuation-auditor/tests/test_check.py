import importlib.util
import pathlib
import unittest

source = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check.py"
spec = importlib.util.spec_from_file_location("comma_audit", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestArabicComma(unittest.TestCase):
    def test_arabic_comma(self):
        self.assertEqual(module.propose("قال,وقال"), "قال، وقال")

    def test_space(self):
        self.assertEqual(module.propose("قال , وقال"), "قال، وقال")

    def test_number(self):
        self.assertEqual(module.propose("1,200"), "1,200")

    def test_only_arabic(self):
        self.assertEqual(module.audit("hello, world"), [])

if __name__ == "__main__":
    unittest.main()
