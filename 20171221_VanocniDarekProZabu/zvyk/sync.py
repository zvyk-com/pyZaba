# zvyk.sync =>

from json import loads
from uos import stat, listdir, remove, rename, mkdir
from gc import mem_free, collect
import socket

def SyncPathPrepare(path, root="/"):
  ps=path.split("/")
  ps=[ps[i] for i in range(len(ps)) if len(ps[i])>0]
  for i in range(len(ps)):
    path="/".join(ps[:i+1])
    if ps[i] not in listdir(root):
      mkdir(path)
    root=path
  return path

def SyncWget(mac, host, port, expSize, fn, targetPath="", tmpExt=".~", st=0, l=b'', lN=None):
  res = {'json':[], 'tags': [], 'size': 0}
  fpfn = targetPath+fn
  req = b'GET /sync/{}/{} HTTP/1.0\r\nHost: {}\r\n\r\n'.format(mac, fpfn, host)
  s = socket.socket(); s.connect(socket.getaddrinfo(host, port)[0][4]); s.send(req)
  while True:
    collect()
    if lN is not None: l=lN
    lN = s.readline() if st == 0 else s.read(512)
    if st == 0 and l == b'\r\n': st += 1; fT=open(fpfn+tmpExt,'wb+'); continue
    if st == 1 and l == b'\r\n' and not lN: st += 1
    if st == 0 and l[:4] == b'ESP:': [res['tags'].append(t) for t in [tg.strip() for tg in l.decode()[4:].split('#') if len(tg.strip())>0]]
    if st == 1:
      res['size'] += len(l)
      fT.write(l)
      if 'getListDir' in res['tags'] and 'json' in res['tags']: res['json'].append(l)
    if not lN: break
  fT.close(); s.close(); del s
  if 'getListDir' in res['tags'] and 'json' in res['tags']:
    remove(fpfn+tmpExt); print ('Removing {}'.format(fpfn+tmpExt))
    merge=''.join([j.decode() for j in res['json']])
    return loads(merge)
  if expSize > 0 and expSize == res['size']:
    if fn in listdir(targetPath[:-1]): remove(fpfn)
    rename(fpfn+tmpExt, fpfn); print (fpfn, '\033[1;32m%s\033[0m'%("Save done ;-D")); return True
  return False

def Sync(mac, host='esp.zvyk.com', port=80, force=[], forceAll=False): # returns bool-> if restart requested
  toSync = SyncWget(mac, host, port, 0, fn="getListDir")
  done=[]
  for l in toSync["fs"]:
    collect()
    #print (l, mem_free())
    p = l['path'] if 'path' in l else ""
    isYounger=isNewFile=(l['fn'] not in listdir(SyncPathPrepare(p)))
    if not isNewFile:
      lfn=stat(p+l['fn'])
      isYounger = True if lfn[9] < l['st_ctime2000'] else False
    #print (l, mem_free(),isYounger,isNewFile)
    if isNewFile or lfn[9] < l['st_ctime2000'] or l['fn'] in force or forceAll:
      print ('\033[1;36m%s\033[0m'%("SYNC REQUEST: "), l, " mem_free:", mem_free(), ' ', p+l['fn'], "\nisNew: ", isNewFile, "isYounger: ", isYounger, sep='')
      if SyncWget(mac, host, port, l['st_size'], l['fn'], p): done.append(l['fn'])
    else: print ("SYNC SKIP:", l)
  if done:
    print ('SYNC Added/Updated:', done, '\n\n\n\n')
    return True
  print('SYNC UP TO DATE')
  return False