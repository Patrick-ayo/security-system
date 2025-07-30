@echo off
echo Pushing to GitHub...
echo.
echo Please enter your GitHub credentials when prompted:
echo Username: Patrick-ayo
echo Password: Use your Personal Access Token (not your GitHub password)
echo.
git push -u origin main --force
echo.
echo Push completed!
pause 