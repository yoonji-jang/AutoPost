@echo off
cd /d "%~dp0"
"C:\Users\jjyjj\.local\bin\claude.exe" -p "/write-daily-post" --permission-mode bypassPermissions >> "%~dp0write_daily_post.log" 2>&1
