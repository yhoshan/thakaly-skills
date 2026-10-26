import unittest,importlib.util,pathlib,tempfile,csv
p=pathlib.Path(__file__).resolve().parents[1]/'skill.py'
spec=importlib.util.spec_from_file_location('skill_under_test',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestSkill(unittest.TestCase):
 def test_no_input(self):
  self.assertEqual(m.analyze([]),[])
 def test_missing_headers(self):
  with tempfile.TemporaryDirectory() as t:
   x=pathlib.Path(t)/'a.csv';y=pathlib.Path(t)/'b.csv';x.write_text('wrong\nvalue\n',encoding='utf-8')
   with self.assertRaises(ValueError):m.run(str(x),str(y))
 def test_sample(self):
  d=dict.fromkeys(m.REQUIRED,'مثال');d.update({'year':'2024','topic':'تفسير','method':'تحليلي','title':'عنوان 1','author':'باحث','source':'مجلة','source_locator':'p.1','findings':'نتيجة'})
  self.assertIsInstance(m.analyze([d]),list)
if __name__=='__main__':unittest.main()
