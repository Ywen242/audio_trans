@echo off
cd /d E:\test_audio
git add .
git commit -m "Automatic commit"
git pull origin master --allow-unrelated-histories
git push origin master
