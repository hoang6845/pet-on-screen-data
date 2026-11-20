import csv,json,re,zipfile,hashlib,concurrent.futures,time,threading
from pathlib import Path
import gdown,requests
ROOT=Path(r'C:\EmojiBattery-PetData')
rows=list(csv.DictReader((ROOT/'source.csv').open(encoding='utf-8-sig')))
for d in ['archives','assets','reports']: (ROOT/d).mkdir(exist_ok=True)
lock=threading.Lock()
def slug(s):
 import unicodedata
 return re.sub('[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-') or 'pet'
def fetch(pair):
 i,row=pair; ident=f"{row['STT']}-{slug(row['Tên nhân vật'])}"
 rec={'row':i+2,'id':ident,'name':row['Tên nhân vật'],'category':row['Chủ đề'],'series':row['Series (chuẩn hoá)'],'source':row['Link bài viết'],'drive':row['Link dự phòng (Drive)'],'mega':row['Link tải chính (Mega)']}
 target=ROOT/'archives'/(ident+'.zip')
 try:
  if not rec['drive']: raise ValueError('Mega-only: requires separate download')
  match=re.search(r'/d/([^/]+)',rec['drive'])
  if not match: raise ValueError('Unsupported Drive URL')
  if not target.exists():
   tmp=target.with_suffix('.part')
   for attempt in range(3):
    try:
     response=requests.get('https://drive.google.com/uc',params={'export':'download','id':match[1]},timeout=60)
     response.raise_for_status()
     tmp.write_bytes(response.content)
     if not zipfile.is_zipfile(tmp):
      gdown.download(id=match[1],output=str(tmp),quiet=True,use_cookies=False)
     if not zipfile.is_zipfile(tmp): raise ValueError('Downloaded file is not ZIP')
     tmp.replace(target); break
    except Exception:
     if attempt==2: raise
     time.sleep(2*(attempt+1))
  files=[]
  with zipfile.ZipFile(target) as z:
   for member in z.infolist():
    if member.is_dir() or not member.filename.lower().endswith(('.png','.gif','.webp','.xml')): continue
    if '__MACOSX' in member.filename or Path(member.filename).name.startswith('._'): continue
    # Flatten safely into numbered files; retain original names in manifest.
    suffix=Path(member.filename).suffix.lower(); name=f'{len(files):04d}{suffix}'
    dest=ROOT/'assets'/ident/name; dest.parent.mkdir(exist_ok=True)
    data=z.read(member)
    if len(data)>30*1024*1024: raise ValueError('Oversized image')
    dest.write_bytes(data)
    files.append({'original':member.filename,'path':dest.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest()})
  if not any(x['path'].endswith(('.png','.gif','.webp')) for x in files): raise ValueError('No supported images in archive')
  rec.update(status='ok',files=files,archive=str(target.relative_to(ROOT)))
 except Exception as e: rec.update(status='failed',error=str(e)[:1200])
 with lock:
  with (ROOT/'reports'/'downloads.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
 return rec
if __name__=='__main__':
 done={}
 p=ROOT/'reports'/'downloads.jsonl'
 if p.exists():
  for l in p.read_text(encoding='utf-8').splitlines():
   r=json.loads(l)
   if r['status']=='ok':done[r['row']]=r
 tasks=[(i,r) for i,r in enumerate(rows) if i+2 not in done]
 print(f'Total {len(rows)}, already completed {len(done)}, pending {len(tasks)}',flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for n,r in enumerate(pool.map(fetch,tasks),1):
   done[r['row']]=r
   if n%20==0: print(f'Processed {n}/{len(tasks)}; successful {sum(x["status"]=="ok" for x in done.values())}',flush=True)
 (ROOT/'manifest.json').write_text(json.dumps(sorted(done.values(),key=lambda r:r['row']),ensure_ascii=False,indent=2),encoding='utf-8')
 print('Finished',flush=True)
