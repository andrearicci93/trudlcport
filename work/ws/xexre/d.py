import sys
sys.path.insert(0,'/path/to/trudlcport/work/ws/xexre')
import x
va=int(sys.argv[1],16); n=int(sys.argv[2])
print("\n".join(x.dis(va,n)))
