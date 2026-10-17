import sys;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd
pat=b'\x00\x00\x80\xbf\x00\x00\x00\x00'
for f,s in fnd.allsecs():
    d=s['data']; n=d.count(pat)
    if n>=5 and 'dlc' in f: print(f,s['i'],s['id'],'type',s['type'],n,len(d))
