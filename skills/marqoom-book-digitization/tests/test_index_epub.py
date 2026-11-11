import json,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from index_epub import normalized_with_offsets,scope_of,run
class SkillTests(unittest.TestCase):
    def test_original_offsets(self):
        s='وَالْحَدِيثُ صَحِيحٌ';n,pos=normalized_with_offsets(s)
        self.assertEqual(n,'والحديث صحيح')
        self.assertEqual(s[pos[2]],'ل')
    def test_no_scope_overlap(self):
        with self.assertRaises(ValueError):
            scope_of(3,[{'name':'a','start':1,'end':4},{'name':'b','start':3,'end':5}])
    def test_only_allowed_scope(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);src=d/'test.epub';cfg=d/'config.json'
            with zipfile.ZipFile(src,'w') as z:
                z.writestr('OEBPS/xhtml/P2.xhtml','<html>وَالْحَدِيثُ صَحِيحٌ</html>')
                z.writestr('OEBPS/xhtml/P3.xhtml','<html>والحديث صحيح</html>')
            cfg.write_text(json.dumps({'scopes':[{'name':'النووي','start':2,'end':2}],'axes':[{'name':'حكم','patterns':['الحديث\\s+صحيح']}]},ensure_ascii=False),encoding='utf8')
            r=run(src,cfg,d/'out')
            self.assertEqual(r['candidates'],1)
            self.assertEqual(r['excluded'],1)
if __name__=='__main__':unittest.main()
