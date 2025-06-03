#!/bin/bash

cd ~/Ostrova_Bot || exit
echo "[INFO] Pulling latest changes from GitHub..."
git reset --hard HEAD
git pull origin main

# Перезапуск сервера через systemd
echo "[INFO] Restarting service..."
sudo systemctl restart ostrova-bot.service
