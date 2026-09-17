"""Controlled evidence use. Oracle and textual executable are independent paths."""
import copy, json, random

RULES='''Apply only the authoritative CURRENT policy to this request. Historical examples are not current rules.
Find the entity's plan in bindings. For urgent requests replace the ordinary cap by urgent_cap; otherwise use cap. Allocate the smallest of request, stock and the applicable cap. Fee is allocated units times price, plus surcharge only when urgent and not waived. If allocated units are zero, fee is zero and lane is NONE; otherwise use the plan lane. Leftover is stock minus allocated units.
Return only a JSON array [allocated_units, total_fee, lane, leftover_stock].'''
LESSON='''Retained procedural lesson: resolve the entity binding again every time. Select exactly one cap: urgent_cap replaces cap rather than being added or minimized with it. Bound allocation by BOTH request and stock. Waived removes only the surcharge, never the per-unit price. Apply the zero-allocation branch before choosing fee/lane. Recompute leftover from allocated units. Historical answers and plan values must never override CURRENT. Check all four fields.'''

def policy(seed,world=0):
    r=random.Random(seed+world*991)
    lanes=r.sample(['RED','BLUE','GREEN','GOLD'],2)
    return {p:dict(cap=4+i+world%3,urgent_cap=2+i+(world*2)%5,price=2+i+(world%3),surcharge=3+i,lane=lanes[i]) for i,p in enumerate(['A','B'])}

def revised(p,v):
    p=copy.deepcopy(p)
    if v>=1: p['A']['urgent_cap']+=4;p['A']['lane']='VIOLET'
    if v>=2: p['B']['price']+=2;p['B']['cap']+=3
    return p

def bindings(seed,fresh=False):
    return {f'E{seed}_{"new" if fresh else "old"}_{i}':['A','B'][i%2] for i in range(8)}

def cases(seed,train=False):
    r=random.Random(seed+(0 if train else 451))
    out=[]
    for fresh in ([False] if train else [False,True]):
        b=bindings(seed,fresh)
        for i,e in enumerate(b):
            for j in range(8 if train else 2):
                # Evaluation requests differ from training and include scarcity/zero/boundaries.
                stock=([0,2,6,11,3,9,5,14] if train else [0,3,8,13])[(i+j)% (8 if train else 4)]
                out.append(dict(id=f'{"train" if train else "eval"}:{e}:{j}',fresh=fresh,
                    request=dict(entity=e,request=r.choice([1,4,7,10] if train else [2,5,8,12]),stock=stock,urgent=bool((i//2+j)%2),waived=bool((i+j)%2)),bindings=b))
    return out

def oracle(c,p):
    q=c['request'];a=p[c['bindings'][q['entity']]]
    n=min(q['request'],q['stock'],a['urgent_cap'] if q['urgent'] else a['cap'])
    return [n,n*a['price']+(a['surcharge'] if q['urgent'] and not q['waived'] else 0) if n else 0,a['lane'] if n else 'NONE',q['stock']-n]

def evidence(c,p):
    return 'CURRENT='+json.dumps(dict(policy=p,bindings=c['bindings']),separators=(',',':'))+'\nREQUEST='+json.dumps(c['request'],separators=(',',':'))

def interpreter(text):
    # Consumes exact prompt evidence; does not call oracle or use hidden case labels.
    lines=text.splitlines();start=next(i for i,x in enumerate(lines) if x.startswith('CURRENT='));doc=json.loads(lines[start][8:])
    q=json.loads(next(x[8:] for x in lines[start+1:] if x.startswith('REQUEST=')))
    a=doc['policy'][doc['bindings'][q['entity']]]
    ceiling=a['cap']
    if q['urgent']: ceiling=a['urgent_cap']
    n=0
    while n<q['request'] and n<q['stock'] and n<ceiling: n+=1
    fee=0;lane='NONE'
    if n>0:
        lane=a['lane']
        for _ in range(n): fee+=a['price']
        if q['urgent']:
            if not q['waived']: fee+=a['surcharge']
    return [n,fee,lane,q['stock']-n]

def history(seed,arm):
    bank=cases(seed,True);out=[]
    for epoch in range(4):
        p=policy(seed,epoch if arm=='varied' else 0)
        for c in bank: out.append(dict(case=c,policy=p,target=oracle(c,p)))
    return out

def lesson(seed,arm):
    h=history(seed,arm)
    # Four historical worlds with cases spanning urgency, scarcity, waiver and zero.
    ix=[0,67,134,201]
    examples=['HISTORICAL worked example (values apply only inside this example):\n'+evidence(h[i]['case'],h[i]['policy']).replace('CURRENT=','HISTORICAL=')+'\nANSWER='+json.dumps(h[i]['target']) for i in ix]
    return LESSON+'\n'+'\n'.join(examples)+'\nEnd historical examples.\n'

def prompt(c,p,extra=''):return RULES+'\n'+extra+evidence(c,p)

def score(raw,target):
    try:
        value=json.loads(raw.strip())
        valid=isinstance(value,list) and len(value)==4 and all(type(value[i]) is int for i in [0,1,3]) and isinstance(value[2],str)
    except (ValueError,TypeError):value=None;valid=False
    fields=[bool(valid and value[i]==target[i]) for i in range(4)]
    return dict(complete=all(fields),valid=valid,fields=fields)

if __name__=='__main__':
    for seed in [731,947]:
        for train in [True,False]:
            for c in cases(seed,train):
                for v in range(3):
                    p=revised(policy(seed),v);y=oracle(c,p)
                    assert interpreter(evidence(c,p))==y
                    if not train:
                        for arm in ['stable','varied']:assert interpreter(prompt(c,p,lesson(seed,arm)))==y
                    assert score(json.dumps(y),y)['complete']
                    for k in range(4):
                        bad=y.copy();bad[k]=bad[k]+1 if isinstance(bad[k],int) else 'WRONG'
                        assert not score(json.dumps(bad),y)['complete']
    print('Oracle/interpreter agreement and all-field mutation rejection passed.')
