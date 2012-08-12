
import sys, os.path, localsettings
_lhp = os.path.abspath(localsettings.ROOT + '/..')
if _lhp not in sys.path:
    sys.path.append(_lhp)
del _lhp
