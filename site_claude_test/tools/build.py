#!/usr/bin/env python3
# =============================================================================
#  build.py  —  the ONE command to rebuild the whole site after you edit anything.
#
#  It just runs the two builders for you:
#    - build_projects.py  -> the "Robots, etc." page + the homepage Featured box
#    - build_pubs.py      -> the "Pubs and Patents" page
#
#  Use it like this:
#    python3 tools/build.py            # rebuild everything
#    python3 tools/build.py --check    # don't change anything, just tell me if a page is stale
# =============================================================================
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["build_projects.py", "build_pubs.py"]   # run these in order

def main():
    args = sys.argv[1:]                 # pass through flags like --check
    rc = 0
    for script in SCRIPTS:
        result = subprocess.run([sys.executable, os.path.join(HERE, script)] + args)
        rc = rc or result.returncode    # if any builder reports a problem, so do we
    sys.exit(rc)

if __name__ == "__main__":
    main()
