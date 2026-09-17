import argparse, json, time, subprocess, os, fcntl
from pathlib import Path
import mlx.core as mx
from runtime import Runtime,resource,sha
from workload import score,interpreter
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.run);out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
lock=open('/tmp/evidence-use-under-revision.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
assert not [x for x in ps.splitlines() if 'python' in x and 'scripts/experiment.py' in x and '/bin/zsh ' not in x]
for f,h in json.loads((p/'hashes.json').read_text()).items():assert sha(p/f)==h
mx.set_memory_limit(32*1024**3);mx.set_cache_limit(2*1024**3)
meta=json.loads((p/'manifest.json').read_text());rt=Runtime(meta['args']['seed']);resource();rows=[json.loads(x) for x in (p/'events.jsonl').read_text().splitlines()]
checked=0
for r in rows:
    if r['kind']=='generation':
        assert len(rt.encode(r['prompt']))==r['prompt_tokens']
        ids=r['ids'];decoded=rt.tokenizer.decode(ids[:-1] if r['ended'] else ids)
        assert decoded==r['raw'] and len(ids)==r['completion_tokens']
        assert interpreter(r['prompt'])==r['target'];assert score(decoded,r['target'])['complete']==r['complete'];checked+=1
    elif r['kind']=='update':
        prefix=rt.encode(r['prompt']);y=rt.target(prefix,r['target']);assert len(y)==r['loss_tokens'];assert len(prefix)+len(y)-1==r['input_tokens']
probes=[]
for ck in [r for r in rows if r['kind']=='checkpoint']:
    rt.restore(list(mx.load(str(p/ck['file'])).items()))
    matches=[r for r in rows if r['kind']=='generation' and r['arm']==ck['arm'] and r['step']==ck['step']]
    chosen={}
    for r in matches:
        key=(r['version'],r['fresh'],r['changed'],r['complete'])
        chosen.setdefault(key,r)
    for r in chosen.values():
        assert time.monotonic()-start<600
        actual=rt.generate(rt.encode(r['prompt']),limit=48)
        probes.append(dict(arm=ck['arm'],step=ck['step'],case=r['case'],version=r['version'],match=actual['raw']==r['raw'],raw=actual['raw'],seconds=actual['seconds']))
        assert actual['raw']==r['raw'],probes[-1]
report=dict(checked_generations=checked,checked_updates=sum(r['kind']=='update' for r in rows),probes=probes,invariants=rt.invariants(),seconds=time.monotonic()-start,peak_mlx_bytes=mx.get_peak_memory(),source_sha=sha(__file__))
(out/'report.json').write_text(json.dumps(report,indent=2));print('Audit passed:',checked,'generations;',len(probes),'reload probes')
