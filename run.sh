#!/bin/bash

# Grandma's Recipe Network - Startup Script
# This script starts all components of the recipe network

echo "Starting Grandma's Recipe Network..."

# Start the network in the background
echo "Starting network..."
openagents network start . &

# Wait a moment for network to initialize
sleep 5

# Start the Recorder agent (ASR)
echo "Starting Recorder agent..."
openagents agent start agents/recorder.yaml &

# Wait a moment
sleep 3

# Start the Polisher agent (LLM)
echo "Starting Polisher agent..."
export OPENAI_API_KEY=${OPENAI_API_KEY:-"your-api-key-here"}
openagents agent start agents/polisher.yaml &

# Wait a moment
sleep 3

# Start the Card Maker agent
echo "Starting Card Maker agent..."
python agents/card_maker.py &

echo "All agents started! Access Studio at http://localhost:8700/studio/"
echo "Press Ctrl+C to stop all components."
echo

# Wait for all background jobs
wait