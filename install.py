#!/usr/bin/env python3
"""Install the standalone app over BUSY Bar's official local API. No extra packages."""
import argparse,getpass,gzip,io,json,shutil,sys,urllib.request,urllib.error
from pathlib import Path
APP='app.kungfu.endless'
def package_bytes(folder):
 """Expand the compact download into the gzip format required by BUSY Bar."""
 compact=folder/'Karate.tar.xz'
 if compact.exists():
  import lzma
  print('Preparing the compact game package (lossless; all sounds and animations retained)...')
  output=io.BytesIO()
  with lzma.open(compact,'rb') as source, gzip.GzipFile(fileobj=output,mode='wb',compresslevel=6,mtime=0) as target:
   shutil.copyfileobj(source,target,1024*1024)
  return output.getvalue()
 package=folder/'Karate.tgz'
 if not package.exists():raise RuntimeError('Keep Karate.tar.xz or Karate.tgz beside this installer.')
 return package.read_bytes()

def main():
 p=argparse.ArgumentParser(description='Install Karate on BUSY Bar')
 p.add_argument('--host',default='10.0.4.20',help='USB or Wi-Fi device address')
 p.add_argument('--wifi',action='store_true',help='Prompt privately for the device Wi-Fi API password')
 p.add_argument('--check',action='store_true',help='Only check connection and native app support')
 p.add_argument('--launch',action='store_true',help='Launch after installation')
 args=p.parse_args();base=args.host.rstrip('/')
 if not base.startswith(('http://','https://')):base='http://'+base
 base=(base[:-4] if base.endswith('/api') else base)+'/api/'
 headers={}
 if args.wifi:headers['X-API-Token']=getpass.getpass('BUSY Bar Wi-Fi API password: ')
 def call(path,data=None,timeout=10):
  h=dict(headers)
  if data is not None:h['Content-Type']='application/octet-stream'
  req=urllib.request.Request(base+path,data=data,headers=h,method='GET' if data is None else 'POST')
  # Local hardware must not be sent to a system HTTP proxy.
  with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=timeout) as r:
   raw=r.read();return json.loads(raw) if raw else {}
 try:
  firmware=call('status/firmware');print('BUSY Bar connected. Firmware:',json.dumps(firmware))
  try:call('apps/list')
  except urllib.error.HTTPError as e:
   if e.code==404:raise RuntimeError('This firmware does not expose native JavaScript apps. Update using the official BUSY app, then try again.') from e
   raise
  if args.check:print('Native app API is available.');return
  package=package_bytes(Path(__file__).resolve().parent)
  print('Uploading game and audio. This can take several minutes; keep BUSY Bar connected...')
  staged=call('apps/stage',package,600)
  if staged.get('staged',{}).get('id')!=APP:raise RuntimeError('Device returned an unexpected staged app ID; nothing installed.')
  key=staged.get('install_key')
  if not isinstance(key,int):raise RuntimeError('Device did not return an installation key.')
  print('Installing files on BUSY Bar. Large audio libraries can take several minutes... ',flush=True)
  call('apps/install?install_key='+str(key),b'',900)
  print('Installed. Select Karate in the BUSY Bar Apps menu. It runs without your computer.')
  if args.launch:call('apps/launch?app_id='+APP,b'');print('Game launched.')
 except (urllib.error.URLError,TimeoutError,RuntimeError,OSError,ValueError) as e:
  print('Installation could not finish:',str(e),file=sys.stderr)
  print('Check USB connection, or use --host DEVICE_IP --wifi. No firmware has been flashed.',file=sys.stderr)
  sys.exit(1)
if __name__=='__main__':main()
