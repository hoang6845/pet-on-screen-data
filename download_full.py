import csv,json,concurrent.futures
from pathlib import Path
import download_pets as d
import download_mega as m
root=d.ROOT/'full-animation';root.mkdir(exist_ok=True)
for name in ['archives','assets','reports']:(root/name).mkdir(exist_ok=True)
tasks=[]
for i,r in enumerate(d.rows):
 link=r['Bản full animation']
 if link:
  row=dict(r);row['Link dự phòng (Drive)']=link if 'drive.google.com' in link else '';row['Link tải chính (Mega)']=link if 'mega.nz' in link else '';tasks.append((i,row))
d.ROOT=root
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 results=list(pool.map(lambda pair:d.fetch(pair) if pair[1]['Link dự phòng (Drive)'] else m.run(pair),tasks))
(root/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('Full animation:',len(results),'success:',sum(r['status']=='ok' for r in results),flush=True)
