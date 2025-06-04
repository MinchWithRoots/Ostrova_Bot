#!/bin/bash

cd ~/Ostrova_Bot || exit
echo "[INFO] Pulling latest changes from GitHub..."
git reset --hard HEAD
git pull origin main

# (опционально) Перезапуск бота
echo "[INFO] Restarting VK bot..."
pkill -f app.py
source venv/bin/activate
nohup python3 app.py > output.log 2>&1 &
