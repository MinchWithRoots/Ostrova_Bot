#!/bin/bash
cd ~/Ostrova_Bot || exit
git reset --hard HEAD
git pull origin main
pkill -f app.py
source venv/bin/activate
nohup python3 app.py > output.log 2>&1 &
