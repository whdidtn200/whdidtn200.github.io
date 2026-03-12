#!/usr/bin/env bash
cd /Users/yanngsoo/blog
git add .
git commit -m "Auto-publish: $(date +'%Y-%m-%d %H:%M:%S')"
git push origin main
