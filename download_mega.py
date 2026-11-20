import base64,struct,json,concurrent.futures
from pathlib import Path
import requests
from Crypto.Cipher import AES
from Crypto.Util import Counter
import download_pets as d

def b64(s):return base64.urlsafe_b64decode(s+'='*((-len(s))%4))
def run(pair):
 i,row=pair
 ident=f"{row['STT']}-{d.slug(row['Tên nhân vật'])}"
 try:
  handle,key=row['Link tải chính (Mega)'].split('/file/')[1].split('#')
  k=struct.unpack('>8I',b64(key)); aeskey=struct.pack('>4I',*(k[n]^k[n+4] for n in range(4)))
  meta=requests.post('https://g.api.mega.co.nz/cs',params={'id':i+1},json=[{'a':'g','g':1,'p':handle}],timeout=40).json()[0]
  if not isinstance(meta,dict) or 'g' not in meta: raise ValueError(f'Mega unavailable: {meta}')
  encrypted=requests.get(meta['g'],timeout=120); encrypted.raise_for_status()
  ctr=Counter.new(128,initial_value=((k[4]<<32)|k[5])<<64)
  raw=AES.new(aeskey,AES.MODE_CTR,counter=ctr).decrypt(encrypted.content)
  path=d.ROOT/'archives'/(ident+'.zip'); path.write_bytes(raw)
  copy=dict(row); copy['Link dự phòng (Drive)']='https://drive.google.com/file/d/mega-local/view'
  rec=d.fetch((i,copy)); rec['drive']=''; rec['mega']=row['Link tải chính (Mega)']
  print(ident,rec['status'],flush=True)
 except Exception as e:
  print(ident,str(e),flush=True)
  rec={'row':i+2,'id':ident,'name':row['Tên nhân vật'],'status':'failed','error':str(e),'mega':row['Link tải chính (Mega)']}
 return rec
if __name__=='__main__':
 tasks=[(i,r) for i,r in enumerate(d.rows) if not r['Link dự phòng (Drive)']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(run,tasks))
 (d.ROOT/'reports'/'mega-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
