@echo off
echo Starting ngrok tunnel for Zoom Interview Bot...
echo.
echo Make sure the bot is running on port 8000 first!
echo Bot URL: http://localhost:8000
echo.
echo ⚠️  IMPORTANT: ngrok must be installed first!
echo.
echo To install ngrok:
echo 1. Download from: https://ngrok.com/download
echo 2. Extract to a folder in your PATH
echo 3. Sign up and get auth token: https://dashboard.ngrok.com/get-started/your-authtoken
echo 4. Run: ngrok authtoken YOUR_TOKEN
echo.
echo Starting ngrok tunnel...
ngrok http 8000
echo.
echo Copy the HTTPS URL and update your Zoom app webhook URL
echo Format: https://your-ngrok-url.ngrok.io/webhook/zoom
pause
