#!/usr/bin/env bash
# Serve this site locally. The CV app lives at http://localhost:8000/cv/
# (http://localhost:8000/ is the separate landing page).
cd "$(dirname "$0")" && python3 -m http.server 8000
# python -m SimpleHTTPServer 8000
