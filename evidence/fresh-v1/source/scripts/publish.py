"""Rebuild the compact publication ledger from audited, immutable runs."""
import argparse, json, hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
specs=[('development-v2','development-v2-analysis-v2','development-v2-audit'),('order-diagnostic-v1','order-diagnostic-v1-analysis','order-diagnostic-v1-audit'),('fresh-v1','fresh-v1-analysis','fresh-v1-audit')]
ledger=[]
for run,analysis,audit in specs:
    p=Path('evidence')/run
    for f,h in json.loads((p/'hashes.json').read_text()).items():
        with (p/f).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==h
    r=json.loads((Path('evidence')/analysis/'report.json').read_text());au=json.loads((Path('evidence')/audit/'report.json').read_text())
    rows=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
    assert sum(x['kind']=='generation' for x in rows)==au['checked_generations']
    assert sum(x['kind']=='update' for x in rows)==au['checked_updates']
    assert all(x['match'] for x in au['probes']) and au['invariants']['base_unchanged'] and au['invariants']['reset_max_logit_delta']==0
    generations=[x for x in rows if x['kind'] in ['generation','recall']];updates=[x for x in rows if x['kind']=='update']
    w=json.loads((p/'workload.json').read_text())
    ledger.append(dict(run=run,manifest=json.loads((p/'manifest.json').read_text()),status=r['status'],tables=r['tables'],candidate_trajectories=r['candidate_trajectories'],audit=dict(seconds=au['seconds'],probes=len(au['probes'])),cost=dict(updates=len(updates),generations=len(generations),update_seconds=sum(x['seconds'] for x in updates),generation_seconds=sum(x['seconds'] for x in generations),input_tokens=sum(x['input_tokens'] for x in updates),loss_tokens=sum(x['loss_tokens'] for x in updates),prompt_tokens=sum(x['prompt_tokens'] for x in generations),completion_tokens=sum(x['completion_tokens'] for x in generations),adapter_bytes=sum(x['bytes'] for x in rows if x['kind']=='checkpoint')),lesson_bytes={k:len(v.encode()) for k,v in w['lessons'].items()},policy_bytes=[len(json.dumps(x,separators=(',',':')).encode()) for x in w['policies']],executable=r['executable']))
totals={k:sum(x['cost'][k] for x in ledger) for k in ledger[0]['cost']}
totals['audit_seconds']=sum(x['audit']['seconds'] for x in ledger);totals['audit_probes']=sum(x['audit']['probes'] for x in ledger)
(out/'ledger.json').write_text(json.dumps(dict(runs=ledger,investigation_totals=totals,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
text='| Fresh method | Updates | Initial | Correction 1 | Correction 2 | 96-use total | Acquisition s | Use s |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
f=ledger[-1]
for t in f['candidate_trajectories']:
    cells=[r for r in f['tables'] if r['arm']==t['arm'] and r['step']==t['step']];cells.sort(key=lambda r:r['version'])
    text+=f"| {t['arm']} | {t['step']} | "+' | '.join(str(r['correct'])+'/32' for r in cells)+f" | {t['correct']}/96 | {t['acquisition_seconds']:.2f} | {t['use_seconds']:.2f} |\n"
text+='| executable | 0 | 32/32 | 32/32 | 32/32 | 96/96 | supplied implementation | '+f"{f['executable']['seconds']:.4f}"+' |\n'
(out/'fresh-table.md').write_text(text);print(text);print(json.dumps(totals,indent=2))
