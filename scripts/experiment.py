import argparse, collections, fcntl, json, os, shutil, subprocess, time, traceback
from pathlib import Path
import mlx.core as mx
from runtime import Runtime, resource, sha, digest
from workload import *

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--seed',type=int,default=731);ap.add_argument('--steps',type=int,default=256);ap.add_argument('--arms',nargs='+',default=['stable','varied']);ap.add_argument('--pilot',action='store_true');ap.add_argument('--shuffle',action='store_true');ap.add_argument('--rebind',action='store_true');a=ap.parse_args()
assert a.steps<=256 and set(a.arms)<= {'stable','varied'}
out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
start=time.monotonic();events=(out/'events.jsonl').open('w');status='failed'
def write(kind,**kw):
    events.write(json.dumps(dict(kind=kind,**kw))+'\n');events.flush()
def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2))
def guard():
    if time.monotonic()-start>1800: raise TimeoutError('30 minute invocation budget')
    if mx.get_peak_memory()>32*1024**3:raise MemoryError('32GiB MLX budget')
    ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
    others=[x for x in ps.splitlines() if ('python' in x.lower()) and any(k in x for k in ['scripts/experiment','scripts/maintenance_','scripts/state_support','scripts/acquire','scripts/mlx_']) and int(x.strip().split()[0])not in {os.getpid(),os.getppid()} and ' /bin/zsh ' not in x]
    if others:raise RuntimeError('Competing model job: '+str(others))
try:
    lock=open('/tmp/evidence-use-under-revision.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    save('manifest.json',dict(args=vars(a),git=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),dirty=subprocess.check_output(['git','status','--porcelain'],text=True),started=time.time(),resource_limit_bytes=32*1024**3))
    (out/'processes-before.txt').write_text(subprocess.check_output(['ps','-axo','pid,etime,command'],text=True))
    for folder in ['scripts','protocol','notes']:
        shutil.copytree(folder,out/'source'/folder,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy('uv.lock',out/'source/uv.lock')
    guard();mx.set_memory_limit(32*1024**3);mx.set_cache_limit(2*1024**3)
    save('model.json',resource());rt=Runtime(seed=a.seed);initial=rt.snapshot()
    save('initial.json',dict(adapter_digest=digest(initial),base_hash=rt.base_hash))
    bank=cases(a.seed,rebind=a.rebind);p0=policy(a.seed)
    save('workload.json',dict(cases=bank,policies=[revised(p0,v) for v in range(3)],histories={arm:history(a.seed,arm) for arm in a.arms},lessons={arm:lesson(a.seed,arm) for arm in a.arms}))
    def evaluate(arm,step,extra='',subset=None):
        for v in range(3):
            for c in (bank if subset is None else subset):
                guard();p=revised(p0,v);target=oracle(c,p);text=prompt(c,p,extra);ids=rt.encode(text)
                r=rt.generate(ids,limit=48)
                write('generation',arm=arm,step=step,version=v,case=c['id'],fresh=c['fresh'],target=target,prompt=text,changed=v>0 and oracle(c,revised(p0,v-1))!=target,**r,**score(r['raw'],target))
        print('evaluated',arm,step,flush=True)
    # Exact executable behavior and evidence bytes are independently recorded.
    for v in range(3):
        for c in bank:
            p=revised(p0,v);t=time.perf_counter();result=interpreter(evidence(c,p));sec=time.perf_counter()-t
            write('executable',version=v,case=c['id'],target=oracle(c,p),result=result,seconds=sec,evidence_bytes=len(evidence(c,p).encode()),complete=result==oracle(c,p))
    evaluate('base',0)
    for arm in a.arms:evaluate('lesson-'+arm,0,lesson(a.seed,arm))
    if not a.pilot:
        for arm in a.arms:
            rt.restore(initial);opt=rt.optimizer();hist=history(a.seed,arm)
            order=list(range(len(hist)))
            if a.shuffle: random.Random(a.seed+872).shuffle(order)
            save(arm+'-order.json',order)
            for i in range(a.steps):
                guard();h=hist[order[i]];text=prompt(h['case'],h['policy']);ids=rt.encode(text);target=json.dumps(h['target']);y=rt.target(ids,target)
                r=rt.step(ids,y,opt);write('update',arm=arm,step=i+1,history_index=order[i],prompt=text,target=target,**r)
                if (i+1)%32==0:print('update',arm,i+1,'loss',r['loss'],flush=True)
                if i+1 in [128,a.steps]:
                    st=rt.snapshot();fn=f'{arm}-{i+1}.safetensors';mx.save_safetensors(str(out/fn),dict(st))
                    write('checkpoint',arm=arm,step=i+1,file=fn,sha256=sha(out/fn),bytes=(out/fn).stat().st_size,changed=digest(st)!=digest(initial),invariants=rt.invariants())
                    evaluate(arm,i+1)
                    # Actual training-case fit distinguishes failure to fit from fresh transfer.
                    for h in hist[:8]:
                        ids=rt.encode(prompt(h['case'],h['policy']));r=rt.generate(ids,limit=48)
                        write('recall',arm=arm,step=i+1,case=h['case']['id'],target=h['target'],**r,**score(r['raw'],h['target']))
            del opt
    save('invariants.json',rt.invariants());status='complete'
except BaseException as e:
    write('error',error=repr(e),traceback=traceback.format_exc());raise
finally:
    events.close();save('status.json',dict(status=status,seconds=time.monotonic()-start,peak_mlx_bytes=mx.get_peak_memory()))
    save('hashes.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='hashes.json'})
