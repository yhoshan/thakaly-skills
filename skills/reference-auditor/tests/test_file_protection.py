import csv
import importlib.util
import pathlib
import tempfile
import unittest

p = pathlib.Path(__file__).resolve().parents[1] / "skill.py"
spec = importlib.util.spec_from_file_location("csv_tool", p)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

class TestFileProtection(unittest.TestCase):
    def test_never_overwrite_input_or_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = root / "source.csv"
            rows = {key: "مثال" for key in tool.REQUIRED}
            with source.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(tool.REQUIRED))
                writer.writeheader()
                writer.writerow(rows)
            original = source.read_bytes()
            with self.assertRaises((ValueError, FileExistsError)):
                tool.run(str(source), str(source))
            self.assertEqual(source.read_bytes(), original)
            with self.assertRaises((ValueError, FileExistsError)):
                tool.run(str(source), str(root / "." / "source.csv"))
            self.assertEqual(source.read_bytes(), original)
            target = root / "report.csv"
            target.write_text("existing report", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                tool.run(str(source), str(target))
            self.assertEqual(target.read_text(encoding="utf-8"), "existing report")
            target.unlink()
            tool.run(str(source), str(target))
            self.assertTrue(target.exists())
            self.assertEqual(source.read_bytes(), original)

if __name__ == "__main__":
    unittest.main()
