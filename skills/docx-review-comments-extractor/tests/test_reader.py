import importlib.util
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'inspect_docx.py'
spec=importlib.util.spec_from_file_location('reader',SCRIPT);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
MODE=reader.MODE
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
SACRED='إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ ﴿قُلْ هُوَ اللَّهُ أَحَدٌ﴾'
def pack(path,body,comments=None,extras=None):
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('word/document.xml',f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>')
        if comments is not None:z.writestr('word/comments.xml',f'<w:comments xmlns:w="{W}">{comments}</w:comments>')
        for n,v in (extras or {}).items():z.writestr(n,v)
def run(text):return '<w:r><w:t>'+text+'</w:t></w:r>'
class ReaderTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.p=self.d/'sample.docx'
    def tearDown(self):self.tmp.cleanup()
    def fixture(self):
        body='<w:p><w:bookmarkStart w:id="4" w:name="دليل"/><w:commentRangeStart w:id="8"/>'
        body+='<w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>'+SACRED+'</w:t></w:r>'
        body+='<w:bookmarkEnd w:id="4"/><w:commentRangeEnd w:id="8"/><w:r><w:commentReference w:id="8"/></w:r></w:p>'
        pack(self.p,body,'<w:comment w:id="8" w:author="مراجع"><w:p>'+run('راجع المصدر')+'</w:p></w:comment>')
    def test_expected_result_and_original_bytes(self):
        self.fixture();before=self.p.read_bytes();r=reader.inspect(self.p,MODE)
        self.assertEqual(r['count'],1);self.assertEqual(self.p.read_bytes(),before);self.assertTrue(r['source_unchanged'])
        item=r['items'][0]
        if MODE=='comments':self.assertEqual(item['text'],'راجع المصدر');self.assertEqual(item['anchors'][0]['text'],SACRED)
        else:self.assertEqual(item['text'],SACRED)
    def test_empty_document(self):
        pack(self.p,'<w:p/>');self.assertEqual(reader.inspect(self.p,MODE)['count'],0)
    def test_corrupt_zip(self):
        self.p.write_bytes(b'not zip')
        with self.assertRaises(zipfile.BadZipFile):reader.inspect(self.p,MODE)
    def test_invalid_xml(self):
        pack(self.p,'<w:p>')
        with self.assertRaises(reader.ET.ParseError):reader.inspect(self.p,MODE)
    def test_wrong_extension(self):
        p=self.d/'file.doc';p.write_bytes(b'x')
        with self.assertRaises(ValueError):reader.inspect(p,MODE)
    def test_macro_bearing_rejected(self):
        pack(self.p,'',extras={'word/vbaProject.bin':b'fake'})
        with self.assertRaises(ValueError):reader.inspect(self.p,MODE)
    def test_same_output_rejected(self):
        self.fixture();before=self.p.read_bytes();r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(self.p)],capture_output=True)
        self.assertEqual(r.returncode,2);self.assertEqual(self.p.read_bytes(),before)
    def test_existing_report_not_overwritten(self):
        self.fixture();out=self.d/'out.json';out.write_text('keep')
        r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(out)],capture_output=True)
        self.assertEqual(r.returncode,2);self.assertEqual(out.read_text(),'keep')
    def test_cli_json(self):
        self.fixture();out=self.d/'report.json';r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(out)],capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['count'],1)
    def test_missing_source(self):
        with self.assertRaises(OSError):reader.inspect(self.p,MODE)
    def test_cli_csv(self):
        self.fixture();out=self.d/'report.csv';r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(out)],capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr)
        with out.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['part'],'word/document.xml');self.assertEqual(rows[0]['paragraph'],'1')
        self.assertEqual(rows[0]['text'],'راجع المصدر' if MODE=='comments' else SACRED)
    def test_empty_csv_has_scope_notice(self):
        pack(self.p,'<w:p/>');out=self.d/'empty.csv';r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(out)],capture_output=True)
        self.assertEqual(r.returncode,0)
        with out.open(encoding='utf-8-sig',newline='') as f:row=next(csv.DictReader(f))
        self.assertEqual(row['status'],'no-items');self.assertTrue(row['limitations'])
    def test_csv_formula_like_text_is_not_executable(self):
        text='=1+1'
        body='<w:p><w:bookmarkStart w:id="1" w:name="x"/><w:commentRangeStart w:id="1"/><w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>'+text+'</w:t></w:r><w:bookmarkEnd w:id="1"/><w:commentRangeEnd w:id="1"/></w:p>'
        pack(self.p,body,'<w:comment w:id="1"><w:p>'+run(text)+'</w:p></w:comment>')
        out=self.d/'formulas.csv';r=subprocess.run([sys.executable,str(SCRIPT),str(self.p),'--out',str(out)],capture_output=True)
        self.assertEqual(r.returncode,0)
        with out.open(encoding='utf-8-sig',newline='') as f:row=next(csv.DictReader(f))
        self.assertEqual(row['text'],"'=1+1");self.assertIn('text',row['escaped_fields']);self.assertEqual(reader.inspect(self.p,MODE)['items'][0]['text'],text)
    def test_deleted_text_not_silently_counted(self):
        self.fixture()
        pack(self.p,'<w:p><w:del>'+run('محذوف')+'</w:del></w:p>')
        r=reader.inspect(self.p,MODE);self.assertEqual(r['count'],0);self.assertTrue(r['warnings'])
    def test_header_story(self):
        header=f'<w:hdr xmlns:w="{W}"><w:p><w:bookmarkStart w:id="1" w:name="header"/><w:r><w:rPr><w:highlight w:val="green"/></w:rPr><w:t>رأس</w:t></w:r><w:bookmarkEnd w:id="1"/></w:p></w:hdr>'
        pack(self.p,'',extras={'word/header1.xml':header});r=reader.inspect(self.p,MODE)
        self.assertIn('word/header1.xml',r['parts']);self.assertEqual(r['count'],0 if MODE=='comments' else 1)
    def test_mode_specific_boundaries(self):
        if MODE=='bookmarks':
            pack(self.p,'<w:p><w:bookmarkStart w:id="1" w:name="ع"/>'+run('أ')+'</w:p><w:p>'+run('ب')+'<w:bookmarkEnd w:id="1"/></w:p>')
            self.assertEqual(reader.inspect(self.p,MODE)['items'][0]['text'],'أ\nب')
        elif MODE=='comments':
            pack(self.p,'<w:p><w:r><w:commentReference w:id="5"/></w:r></w:p>','<w:comment w:id="5"><w:p>'+run('أ')+'</w:p><w:p>'+run('ب')+'</w:p></w:comment>')
            item=reader.inspect(self.p,MODE)['items'][0];self.assertEqual(item['text'],'أ\nب');self.assertEqual(item['status'],'anchored')
        else:
            pack(self.p,'<w:p><w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>أ</w:t><w:tab/></w:r><w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>ب</w:t></w:r>'+run('ج')+'<w:r><w:rPr><w:highlight w:val="none"/></w:rPr><w:t>د</w:t></w:r></w:p>')
            r=reader.inspect(self.p,MODE);self.assertEqual(r['count'],1);self.assertEqual(r['items'][0]['text'],'أ\tب')
    def test_mode_specific_incomplete_data(self):
        if MODE=='bookmarks':
            pack(self.p,'<w:p><w:bookmarkStart w:id="1" w:name="ع"/>'+run('أ')+'</w:p>');r=reader.inspect(self.p,MODE)
            self.assertEqual(r['items'][0]['status'],'missing-end');self.assertIsNone(r['items'][0]['text']);self.assertTrue(r['warnings'])
        elif MODE=='comments':
            pack(self.p,'<w:p><w:r><w:commentReference w:id="8"/></w:r></w:p>');r=reader.inspect(self.p,MODE)
            self.assertEqual(r['count'],0);self.assertTrue(r['warnings'])
        else:
            pack(self.p,'<w:p><w:r><w:rPr><w:shd w:fill="FFFF00"/></w:rPr><w:t>ليس تمييزًا صريحًا</w:t></w:r></w:p>');r=reader.inspect(self.p,MODE)
            self.assertEqual(r['count'],0);self.assertTrue(any('Inherited' in x for x in r['limitations']))
    def test_wrong_namespace_not_false_success(self):
        with zipfile.ZipFile(self.p,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml','<document/>')
        with self.assertRaises(ValueError):reader.inspect(self.p,MODE)
if __name__=='__main__':unittest.main()
