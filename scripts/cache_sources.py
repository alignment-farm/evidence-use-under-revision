import urllib.request, urllib.error, time, json, hashlib
from pathlib import Path
out=Path('.cache/arxiv');out.mkdir(parents=True,exist_ok=True)
manifest=Path('sources/papers/retrieval.json');manifest.parent.mkdir(parents=True,exist_ok=True)
urls=[('metadata.xml','https://export.arxiv.org/api/query?id_list=2303.11315,2410.10796,2509.13683'), *[(p+'.html','https://arxiv.org/html/'+p) for p in ['2303.11315v2','2410.10796v3','2509.13683v1']]]
ledger=[]
previous={x['url']:x for x in json.loads(manifest.read_text())} if manifest.exists() else {}
for name,url in urls:
    if (out/name).exists() and url in previous and hashlib.sha256((out/name).read_bytes()).hexdigest()==previous[url].get('sha256'):
        ledger.append(previous[url]);continue
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EvidenceUseUnderRevision/0.1 (independent bounded research; cached single-client requests)'}),timeout=45) as r:
            data=r.read(); (out/name).write_bytes(data)
            ledger.append(dict(url=url,file=name,cache_file=str(out/name),sha256=hashlib.sha256(data).hexdigest(),headers=dict(r.headers)))
    except urllib.error.HTTPError as e:
        ledger.append(dict(url=url,error=str(e),retry_after=e.headers.get('Retry-After')))
        if e.headers.get('Retry-After'):
            manifest.write_text(json.dumps(ledger,indent=2));break  # No further requests during server backoff.
    except Exception as e: ledger.append(dict(url=url,error=str(e)))
    manifest.write_text(json.dumps(ledger,indent=2))
    time.sleep(3.1)

manifest.write_text(json.dumps(ledger,indent=2))
