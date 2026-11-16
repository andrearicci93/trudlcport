# 0.22.55 (package P2a, small item A10): how many long-menu page keys does trumenu_quick_check's qb_page_names find now?
# The check menupages wants 28 and has failed since 0.22.45; this prints the real count and the keys (read only).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import trumenu_quick_check as q  # noqa: E402

names, keys = q.qb_page_names()
print('page keys: %d (unique %d)' % (len(keys), len(set(keys))))
print('keys: %s' % ', '.join(keys))
print('totest in keys: %s, quick in keys: %s' % ('totest' in keys, 'quick' in keys))
