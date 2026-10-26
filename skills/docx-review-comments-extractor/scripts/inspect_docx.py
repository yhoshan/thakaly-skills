"""Independent, read-only OOXML reader. Python standard library only."""
import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MAX_XML = 40 * 1024 * 1024
MAX_TOTAL = 160 * 1024 * 1024

def xml_part(z, name):
    info = z.getinfo(name)
    if info.file_size > MAX_XML:
        raise ValueError('XML part exceeds 40 MiB: ' + name)
    data = z.read(name)
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entities are not supported')
    return ET.fromstring(data)

def story(root, part):
    chunks, marks, spans, warnings = [], [], [], []
    offset, paragraph = 0, 0
    def add(text, color=None):
        nonlocal offset
        if color and text:
            if spans and spans[-1]['end'] == offset and spans[-1]['color'] == color and spans[-1]['paragraph'] == paragraph:
                spans[-1]['text'] += text
                spans[-1]['end'] += len(text)
            else:
                spans.append(dict(part=part, paragraph=paragraph, start=offset, end=offset+len(text), color=color, text=text))
        chunks.append(text)
        offset += len(text)
    def walk(el, color=None):
        nonlocal paragraph
        tag = el.tag
        if tag in (W+'del', W+'moveFrom'):
            warnings.append('Deleted/moved-from revision omitted from visible-text view: '+part)
            return
        if tag in (W+'ins', W+'moveTo'):
            warnings.append('Inserted/moved-to revision included without accepting changes: '+part)
        if tag == W+'altChunk':
            warnings.append('Embedded altChunk content was not read: '+part)
        if tag == W+'p': paragraph += 1
        if tag == W+'r':
            h = el.find(W+'rPr/'+W+'highlight')
            color = h.get(W+'val') if h is not None else None
            if color == 'none': color = None
        if tag in {W+x for x in ('bookmarkStart','bookmarkEnd','commentRangeStart','commentRangeEnd','commentReference')}:
            marks.append(dict(kind=tag[len(W):],id=el.get(W+'id'),name=el.get(W+'name'),offset=offset,paragraph=paragraph,part=part))
        if tag == W+'t': add(el.text or '', color)
        elif tag == W+'tab': add('\t', color)
        elif tag in (W+'br',W+'cr'): add('\n', color)
        elif tag == W+'noBreakHyphen': add('\u2011', color)
        elif tag == W+'softHyphen': add('\u00ad', color)
        for child in el: walk(child,color)
        if tag == W+'p': add('\n')
    walk(root)
    return ''.join(chunks),marks,spans,warnings

def ranges(text, marks, prefix, warnings):
    starts = {}; result=[]
    for m in marks:
        if m['kind'] == prefix+'Start':
            if m['id'] in starts:
                warnings.append('Duplicate start ID '+str(m['id'])+' in '+m['part'])
                result.append(dict(**starts.pop(m['id']),status='duplicate-start',text=None,end=None))
            starts[m['id']] = m
        elif m['kind'] == prefix+'End':
            first = starts.pop(m['id'],None)
            if first is None:
                warnings.append('Orphan end ID '+str(m['id'])+' in '+m['part'])
                result.append(dict(**m,status='orphan-end',text=None,end=m['offset']))
            else:
                result.append(dict(**first,status='ok',end=m['offset'],text=text[first['offset']:m['offset']]))
    for m in starts.values():
        result.append(dict(**m,status='missing-end',text=None,end=None))
        warnings.append('Missing end ID '+str(m['id'])+' in '+m['part'])
    return result

def inspect(path, mode):
    path=Path(path)
    if path.suffix.lower() != '.docx': raise ValueError('Only .docx is supported; no .doc, .docm or PDF')
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    warnings=[]; items=[]; all_marks=[]; anchor_ranges=[];parts=[]
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)): raise ValueError('Duplicate ZIP members are ambiguous')
        if sum(x.file_size for x in z.infolist() if x.filename.endswith('.xml'))>MAX_TOTAL: raise ValueError('XML total exceeds 160 MiB')
        if any(n.lower().endswith('vbaproject.bin') for n in names): raise ValueError('Macro-bearing package rejected')
        if '[Content_Types].xml' not in names or 'word/document.xml' not in names: raise ValueError('Not a supported Word document package')
        xml_part(z,'[Content_Types].xml')
        parts=sorted(n for n in names if re.fullmatch(r'word/(?:document|footnotes|endnotes|header\d*|footer\d*)\.xml',n))
        for part in parts:
            root=xml_part(z,part)
            if not root.tag.startswith(W): raise ValueError('Unsupported Word XML namespace: '+part)
            text,marks,spans,warn=story(root,part);warnings.extend(warn);all_marks.extend(marks)
            if mode=='bookmarks': items.extend(ranges(text,marks,'bookmark',warnings))
            elif mode=='highlights': items.extend(spans)
            elif mode=='comments': anchor_ranges.extend(ranges(text,marks,'commentRange',warnings))
            else: raise ValueError('Unknown mode')
        if mode=='comments':
            ids=set()
            if 'word/comments.xml' in names:
                root=xml_part(z,'word/comments.xml')
                if root.tag!=W+'comments': raise ValueError('Unsupported comments namespace')
                parts.append('word/comments.xml')
                for c in root.findall(W+'comment'):
                    cid=c.get(W+'id');text,_,_,warn=story(c,'word/comments.xml');warnings.extend(warn)
                    if cid in ids:warnings.append('Duplicate comment ID '+str(cid))
                    ids.add(cid)
                    scopes=[x for x in anchor_ranges if x['id']==cid]
                    refs=[x for x in all_marks if x['kind']=='commentReference' and x['id']==cid]
                    items.append(dict(id=cid,author=c.get(W+'author'),initials=c.get(W+'initials'),date=c.get(W+'date'),text=text[:-1] if text.endswith('\n') else text,anchors=scopes,references=refs,status='anchored' if scopes or refs else 'unanchored'))
            for m in all_marks:
                if m['kind'].startswith('comment') and m['id'] not in ids:warnings.append('Anchor references missing comment ID '+str(m['id']))
            if any('commentsExtended' in n or 'commentsExtensible' in n or 'people.xml' in n for n in names):warnings.append('Modern comment threading/resolution metadata is not interpreted')
    after=hashlib.sha256(path.read_bytes()).hexdigest()
    if before!=after:raise ValueError('Input changed during inspection; result discarded')
    limits=['Offsets are zero-based Unicode code points in extracted story text, not Word page numbers or UTF-16 offsets.','Paragraph indices are per XML story, including table cells and text boxes.','Field instructions, images, embedded objects and deleted text are not rendered.']
    if mode=='highlights':limits.append('Only explicit w:highlight is extracted. Inherited style highlights, shading and font color are not inferred.')
    return dict(skill_mode=mode,input_name=path.name,source_sha256=before,source_unchanged=True,parts=parts,count=len(items),items=items,warnings=sorted(set(warnings)),limitations=limits)

def csv_records(result):
    records=[]
    for item in result['items']:
        scopes=item.get('anchors') or item.get('references') or [item]
        for scope in scopes:
            records.append(dict(mode=result['skill_mode'],source=result['input_name'],sha256=result['source_sha256'],part=scope.get('part','word/comments.xml'),paragraph=scope.get('paragraph',''),start=scope.get('offset',scope.get('start','')),end=scope.get('end',''),id=item.get('id',''),name=item.get('name',''),color=item.get('color',''),author=item.get('author',''),date=item.get('date',''),status=item.get('status','ok'),text=item.get('text',''),anchor_text=scope.get('text','') if result['skill_mode']=='comments' else '',warnings='; '.join(result['warnings']),limitations='; '.join(result['limitations'])))
    return records

def main(mode):
    parser=argparse.ArgumentParser(description='Read-only Word '+mode+' inventory')
    parser.add_argument('input');parser.add_argument('--out',required=True,help='New .csv or .json output; existing files are refused')
    args=parser.parse_args()
    try:
        source=Path(args.input).resolve();out=Path(args.out).resolve()
        if source==out or (out.exists() and source.exists() and out.samefile(source)):raise ValueError('Output must differ from input')
        if out.exists():raise ValueError('Output already exists; choose a new report path')
        if out.suffix.lower() not in {'.csv','.json'}:raise ValueError('Output extension must be .csv or .json')
        result=inspect(source,mode)
        if out.suffix.lower()=='.json':
            with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        else:
            records=csv_records(result)
            fields=['mode','source','sha256','part','paragraph','start','end','id','name','color','author','date','status','text','anchor_text','warnings','limitations','escaped_fields']
            # A summary row keeps limitations visible even when no items exist.
            if not records:records=[dict(mode=mode,source=result['input_name'],sha256=result['source_sha256'],status='no-items',warnings='; '.join(result['warnings']),limitations='; '.join(result['limitations']))]
            with out.open('x',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
                for rec in records:
                    escaped=[]
                    for k,v in rec.items():
                        if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')):
                            rec[k]="'"+v;escaped.append(k)
                    rec['escaped_fields']=';'.join(escaped);writer.writerow(rec)
        print(json.dumps({'count':result['count'],'warnings':len(result['warnings']),'output':str(out)},ensure_ascii=True))
        return 0
    except (ValueError,OSError,zipfile.BadZipFile,ET.ParseError,KeyError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2

MODE = 'comments'
if __name__ == "__main__":
    raise SystemExit(main(MODE))
