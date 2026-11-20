import json,concurrent.futures
from pathlib import Path
from urllib.parse import unquote
from PIL import Image
r=Path(__file__).resolve().parent
pets=json.loads((r/'publish/data_pet_moving_v3.json').read_text(encoding='utf-8'))
assert len({p['id'] for p in pets})==len(pets)
paths=set()
for p in pets:
 assert p['thumbnail'].startswith('https://') and p['walk']['frames']
 urls=[p['thumbnail']]+[u for v in p.values() if isinstance(v,dict) for u in v.get('frames',[])]
 for u in urls:paths.add('assets/'+unquote(u.split('/assets/',1)[1]))
cachefile=r/'reports/validated-images.json'
cache=set(json.loads(cachefile.read_text()) if cachefile.exists() else [])
validated=set()
def check(relative):
 path=r/relative
 assert path.is_file(),relative
 assert path.stat().st_size<48*1024*1024,relative
 if relative not in cache:
  with Image.open(path) as im:im.verify()
 return relative
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
 for n,relative in enumerate(pool.map(check,sorted(paths)),1):
  validated.add(relative)
  if n%1000==0:
   cachefile.write_text(json.dumps(sorted(cache|validated)))
   print(f'Validated images {n}/{len(paths)}',flush=True)
cachefile.write_text(json.dumps(sorted(cache|validated)))
report={'pets':len(pets),'referenced_images':len(paths),'unique_ids':True,'readable_images':True,'catalog_bytes':(r/'publish/data_pet_moving_v3.json').stat().st_size,'template_urls':any('/OWNER/REPO/' in p['thumbnail'] for p in pets)}
assert report['catalog_bytes']<12*1024*1024
(r/'reports/validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
