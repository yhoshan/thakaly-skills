import re

def audit(text):
    return [m.start() for m in re.finditer(r'(?<=[ء-ي]),(?=[ء-ي])', text)]

def propose(text):
    return re.sub(r'(?<=[ء-ي]),(?=[ء-ي])', '،', text)
