import argparse
import re
from pathlib import Path

PATTERN = re.compile(r"(?<=[ء-ي])\s*,\s*(?=[ء-ي])")

def audit(text):
    return [match.start() for match in PATTERN.finditer(text)]

def propose(text):
    return PATTERN.sub("، ", text)

def main():
    parser = argparse.ArgumentParser(description="فحص الفواصل الإنجليزية في نص عربي")
    parser.add_argument("input")
    parser.add_argument("--out")
    args = parser.parse_args()
    path = Path(args.input)
    text = path.read_text(encoding="utf-8-sig")
    print("مواضع للمراجعة:", audit(text))
    if args.out:
        target = Path(args.out)
        if target.resolve() == path.resolve():
            parser.error("لا يجوز الكتابة فوق الملف الأصلي")
        if target.exists():
            parser.error("ملف المخرجات موجود")
        target.write_text(propose(text), encoding="utf-8")

if __name__ == "__main__":
    main()
