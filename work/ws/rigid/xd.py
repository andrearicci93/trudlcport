import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/rigid')
import pcdis
img=pcdis.Img('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe')
if __name__=='__main__': pcdis.dis(img,int(sys.argv[1],16),int(sys.argv[2]))
