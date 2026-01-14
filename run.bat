@echo off
REM Grandma's Recipe Network - Windows Startup Script
REM This script starts all components of the recipe network

echo Starting Grandma's Recipe Network...

REM Start the network in a separate window
echo Starting network...
start "Recipe Network" cmd /c "openagents network start ."

REM Wait a moment for network to initialize
timeout /t 5 /nobreak >nul

REM Start the Recorder agent (ASR)
echo Starting Recorder agent...
start "Recorder Agent" cmd /c "openagents agent start agents/recorder.yaml"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start the Polisher agent (LLM)
echo Starting Polisher agent...
start "Polisher Agent" cmd /c "set OPENAI_API_KEY=your-api-key && openagents agent start agents/polisher.yaml"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start the Card Maker agent
echo Starting Card Maker agent...
start "Card Maker Agent" cmd /c "python agents/card_maker.py"

echo All agents started! Access Studio at http://localhost:8700/studio/
echo Note: Close this window to stop all components.
pause