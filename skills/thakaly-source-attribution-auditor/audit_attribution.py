#!/usr/bin/env python3
"""Thakaly TS-004 v0.2: structural checks + conservative attribution-cue alerts.
This is not an independent judgement of historical authenticity.
"""
import argparse, json, re
from pathlib import Path

REQUIRED = ('id','source_title','source_location','source_excerpt','attributed_to',
            'attribution_formula','attribution_mode','transmission_nature','text_layer','quote')
MODES = {'direct','mediated','uncertain'}
NATURES = {'verbatim','paraphrase','summary','unknown'}
CHAIN_CUES = re.compile(r'(?:^|[\s،:؛])(?:أخبرنا|حدثنا|حدثني|أخبرني|أنبأنا|روى|روينا|رُوي|روي|عن)(?=[\s،:؛])')
CHAIN_LINK = re.compile(r'(?:^|[\s،:؛])عن(?=[\s،:؛])')
UNCERTAIN_CUES = re.compile(r'(?:بلغني|بلغنا|فيما بلغني|لا يحضرني|لا أذكر|لا أدري|فيما أحسب|يُروى|يروى|قيل|حُكي|حكي)')

def audit(item):
    issues = []
    for field in REQUIRED:
        if not str(item.get(field, '')).strip():
            issues.append({'code':'missing_field','field':field})
    mode = item.get('attribution_mode')
    if mode not in MODES: issues.append({'code':'invalid_attribution_mode'})
    if item.get('transmission_nature') not in NATURES: issues.append({'code':'invalid_transmission_nature'})
    if mode == 'mediated' and not item.get('transmission_chain'): issues.append({'code':'missing_transmission_chain'})
    if mode == 'mediated' and not item.get('chain_type'): issues.append({'code':'missing_chain_type'})
    if mode in {'mediated','uncertain'} and item.get('claimed_direct'):
        issues.append({'code':'unjustified_directness_claim'})
    if mode == 'uncertain' and not item.get('reservation'): issues.append({'code':'missing_reservation'})
    q, excerpt = item.get('quote',''), item.get('source_excerpt','')
    match = bool(q and excerpt and q in excerpt)
    if item.get('transmission_nature') == 'verbatim' and not match:
        issues.append({'code':'verbatim_quote_not_in_supplied_excerpt'})
    if item.get('claimed_verified_original') and mode != 'direct':
        issues.append({'code':'unjustified_original_source_verification'})
    formula = str(item.get('attribution_formula') or '')
    opening = str(excerpt or '')[:180]
    chain_detected = bool(CHAIN_CUES.search(formula) or CHAIN_CUES.search(opening))
    uncertain_detected = bool(UNCERTAIN_CUES.search(formula) or UNCERTAIN_CUES.search(opening))
    if mode == 'direct' and chain_detected:
        issues.append({'code':'possible_mediated_attribution_mislabeled_direct',
                       'detail':'A transmission cue appears; reviewer must distinguish the author speaking from a report transmitted by the author.'})
    if mode == 'direct' and uncertain_detected:
        issues.append({'code':'possible_uncertain_attribution_mislabeled_direct',
                       'detail':'An uncertainty cue appears; human inspection required.'})
    return {'id':item.get('id'),'original_input':item,
            'quote_found_in_supplied_excerpt':match,
            'detected_cues':{'transmission':chain_detected,'uncertainty':uncertain_detected},
            'status':'needs_review' if issues else 'structurally_consistent','issues':issues,
            'verification_limit':'Heuristic cues and supplied data only; no validation of original text or authenticity'}

def run(data):
    if not isinstance(data,list): raise ValueError('Expected JSON array of attribution records')
    return {'skill':'thakaly-source-attribution-auditor','version':'0.2.0',
            'results':[audit(row) for row in data],
            'scope':'structural and heuristic cue alerts only, not independent historical attribution verification'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('-o','--output',required=True)
    args=p.parse_args()
    data=json.loads(Path(args.input).read_text(encoding='utf-8'))
    Path(args.output).write_text(json.dumps(run(data),ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
