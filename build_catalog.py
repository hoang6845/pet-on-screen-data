import argparse,json,collections,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote,urlparse
ROOT=Path(__file__).resolve().parent

def build(base):
 records={}
 for line in (ROOT/'reports/downloads.jsonl').read_text(encoding='utf-8').splitlines():
  r=json.loads(line)
  if r['row'] not in records or r['status']=='ok':records[r['row']]=r
 mega=ROOT/'reports/mega-results.json'
 if mega.exists():
  for r in json.loads(mega.read_text(encoding='utf-8')):
   if r['status']=='ok':records[r['row']]=r
 template=ET.parse(ROOT/'standard-actions.xml').getroot()
 mapping={'walk':'Walk','run':'Run','sit':'Sit','climb':'ClimbWall','top':'ClimbCeiling','drag':'Pinched','fall':'Falling','drop':'Falling'}
 pets=[]; skipped=[]
 def url(path):return base.rstrip('/')+'/'+quote(path,safe='/')
 for r in sorted(records.values(),key=lambda r:r['row']):
  if r['status']!='ok':continue
  files=r['files']; images=[f for f in files if Path(f['path']).suffix in ['.png','.webp','.gif']]
  # Separate image subdirectories so costumes/variants are not mixed together.
  groups=collections.defaultdict(dict)
  for f in images:groups[str(Path(f['original']).parent)][Path(f['original']).name.lower()]=f['path']
  variants=[(folder,fs) for folder,fs in groups.items() if 'shime1.png' in fs]
  if not variants:
   skipped.append({'id':r['id'],'reason':'No standard shime1.png; static preview only; manual animation mapping required'})
   if not images:continue
   variants=[('unmapped',{'shime1.png':images[0]['path']})]
  xmls=[f for f in files if f['path'].endswith('.xml') and Path(f['original']).name.lower()=='actions.xml']
  for index,(folder,fs) in enumerate(variants):
   actions=template; mapping_source='standard-actions.xml'
   if xmls:
    try:actions=ET.parse(ROOT/xmls[0]['path']).getroot(); mapping_source=xmls[0]['path']
    except ET.ParseError:pass
   item={'id':r['id']+(f'-v{index+1}' if len(variants)>1 else ''),'name':r['name']+(f' ({index+1})' if len(variants)>1 else ''),'type':r['category'],'category':r['category'],'series':r['series'],'thumbnail':url(fs['shime1.png']),'is_lock':False,'source_url':r['source'],'animation_mapping':mapping_source}
   for target,source in mapping.items():
    action=next((a for a in actions.iter() if a.tag.split('}')[-1]=='Action' and a.get('Name')==source),None)
    if action is None:continue
    names=[Path(n.get('Image','').replace('\\','/')).name.lower() for n in action.iter() if n.tag.split('}')[-1]=='Pose']
    if names and all(n in fs for n in names):item[target]={'frames':[url(fs[n]) for n in names]}
   if 'walk' not in item:
    skipped.append({'id':item['id'],'reason':'No complete Walk sequence; exported as static preview'})
    item['walk']={'frames':[item['thumbnail']]}
    item['animation_mapping']='static-preview-needs-review'
   pets.append(item)
 categories=[{'type':c,'name':c} for c in dict.fromkeys(p['type'] for p in pets)]
 out=ROOT/'publish';out.mkdir(exist_ok=True)
 for name,data in [('data_pet_moving_v3.json',pets),('pet_type.json',categories),('data_pet.json',[])]:
  (out/name).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 config={'data_pet_moving_v3':url('publish/data_pet_moving_v3.json'),'pet_type':url('publish/pet_type.json'),'data_pet':'[]'}
 (ROOT/'remote-config-values.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
 summary={'source_rows':1081,'processed_rows':len(records),'downloaded_rows':sum(r['status']=='ok' for r in records.values()),'failed_rows':[r for r in records.values() if r['status']!='ok'],'pets_exported':len(pets),'manual_mapping':skipped,'base_url':base,'catalog_bytes':(out/'data_pet_moving_v3.json').stat().st_size}
 (ROOT/'reports/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'manifest.json').write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in summary.items() if k not in ['failed_rows','manual_mapping']},ensure_ascii=False))
 print('Failed downloads:',len(summary['failed_rows']),'Manual mapping:',len(skipped))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base-url',required=True);a=p.parse_args()
 if not a.base_url.startswith('https://'):p.error('base URL must use HTTPS')
 build(a.base_url)
