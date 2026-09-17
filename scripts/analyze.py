import argparse, collections, hashlib, json
from pathlib import Path
from workload import interpreter,score
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--output',required=True);a=ap.parse_args()
p=Path(a.run);out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
for f,h in json.loads((p/'hashes.json').read_text()).items():
    with (p/f).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==h,f
rows=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
assert json.loads((p/'status.json').read_text())['status']=='complete'
gens=[r for r in rows if r['kind']=='generation'];groups=collections.defaultdict(list)
for r in gens:
    target=interpreter(r['prompt']);assert target==r['target']
    s=score(r['raw'],target)
    assert all(r[k]==s[k] for k in s)
    groups[(r['arm'],r['step'],r['version'])].append(r)
tables=[];transitions=[]
for (arm,step,v),rs in groups.items():
    assert len(rs)==32 and len({r['case'] for r in rs})==32
    table=dict(arm=arm,step=step,version=v,n=len(rs),correct=sum(r['complete'] for r in rs))
    for name,predicate in [('fresh',lambda r:r['fresh']),('familiar',lambda r:not r['fresh']),('changed',lambda r:r['changed']),('unchanged',lambda r:not r['changed'])]:
        sub=[r for r in rs if predicate(r)];table[name]=dict(n=len(sub),correct=sum(r['complete'] for r in sub))
    table['field_correct']=[sum(r['fields'][i] for r in rs) for i in range(4)]
    table['valid']=sum(r['valid'] for r in rs);tables.append(table)
    if v:
        before={r['case']:r for r in groups[(arm,step,v-1)]}
        eligible=[r for r in rs if not r['changed'] and before[r['case']]['complete']]
        transitions.append(dict(arm=arm,step=step,version=v,previously_correct_unchanged=len(eligible),retained=sum(r['complete'] for r in eligible)))
costs=[]
for arm in sorted({r.get('arm') for r in rows if r.get('arm')}):
    rs=[r for r in rows if r.get('arm')==arm];updates=[r for r in rs if r['kind']=='update'];uses=[r for r in rs if r['kind']=='generation'];recall=[r for r in rs if r['kind']=='recall']
    costs.append(dict(arm=arm,updates=len(updates),update_seconds=sum(r['seconds'] for r in updates),input_tokens=sum(r['input_tokens'] for r in updates),loss_tokens=sum(r['loss_tokens'] for r in updates),generations=len(uses),generation_seconds=sum(r['seconds'] for r in uses),prompt_tokens=sum(r['prompt_tokens'] for r in uses),completion_tokens=sum(r['completion_tokens'] for r in uses),recall_calls=len(recall),recall_correct=sum(r['complete'] for r in recall),recall_seconds=sum(r['seconds'] for r in recall)))
report=dict(run=a.run,tables=tables,unchanged_retention=transitions,investigation_costs=costs,status=json.loads((p/'status.json').read_text()),executable=dict(n=sum(r['kind']=='executable' for r in rows),correct=sum(r.get('complete',False) for r in rows if r['kind']=='executable'),seconds=sum(r['seconds'] for r in rows if r['kind']=='executable')))
# Deployment: one acquisition plus the fixed 96-use correction sequence at one endpoint.
trajectories=[]
for arm,step in sorted({(r['arm'],r['step']) for r in gens}):
    uses=[r for r in gens if r['arm']==arm and r['step']==step]
    updates=[r for r in rows if r['kind']=='update' and r['arm']==arm and r['step']<=step]
    trajectories.append(dict(arm=arm,step=step,correct=sum(r['complete'] for r in uses),uses=len(uses),acquisition_updates=len(updates),acquisition_seconds=sum(r['seconds'] for r in updates),use_seconds=sum(r['seconds'] for r in uses),total_active_seconds=sum(r['seconds'] for r in uses+updates),prompt_tokens=sum(r['prompt_tokens'] for r in uses),completion_tokens=sum(r['completion_tokens'] for r in uses),training_input_tokens=sum(r['input_tokens'] for r in updates),training_loss_tokens=sum(r['loss_tokens'] for r in updates),maintenance_updates=0))
report['candidate_trajectories']=trajectories
report['correction_operations']=[dict(version=1,fields=['A.urgent_cap','A.lane']),dict(version=2,fields=['B.price','B.cap'])]
report['limitations']=['Investigator construction time not measured; lesson and executable construction supplied.', 'Native seconds are observed local costs, not isolated benchmark or dollars.', 'Early checkpoint evaluations, other arms, development, and audit are investigation costs, not candidate deployment costs.']
(out/'report.json').write_text(json.dumps(report,indent=2))
text='| Arm | Updates | Version | Complete | Fresh | Changed | Unchanged |\n|---|---:|---:|---:|---:|---:|---:|\n'
for r in tables:
    ratio=lambda key:f"{r[key]['correct']}/{r[key]['n']}"
    text+=f"| {r['arm']} | {r['step']} | {r['version']} | {r['correct']}/{r['n']} | {ratio('fresh')} | {ratio('changed')} | {ratio('unchanged')} |\n"
(out/'tables.md').write_text(text);print(text)
