# grandma_cook_agent
外婆家菜谱实现方案

# Grandma's Recipe Network

"野生菜谱数字卡片" - 用3个轻量级Agent完成"语音 → 文字 → 美观卡片"一站式生成，30秒出图可发朋友圈。基础版纯Web分享，降低参赛门槛。

## Overview

This network converts voice recordings of recipes into beautiful digital cards with QR codes that link to the full recipe. It uses three specialized agents working in sequence to transform your grandmother's voice recipe into a shareable digital format. Supports both file uploads and real-time recording through Studio interface.

## Problem Solved

- Grandmother's recipes in dialect are not recorded in text
- Traditional archiving is not viewed or shared
- Manual layout and design is cumbersome

## Agents

| Agent | Type | Description |
|-------|------|-------------|
| `recorder` | Python (ASR) | Converts voice recordings to text using automatic speech recognition. Supports both file uploads and real-time recording via Studio interface using vosk/pyaudio |
| `simple-agent` | Python (LLM) | Standardizes text, converts vague measurements to specific quantities, formats as markdown |
| `card-maker` | Python | Generates PNG card with QR code linking to the full recipe |

## Quick Start

### 1. Install Dependencies

```bash
pip install pyaudio vosk pillow qrcode
```

### 2. Download Vosk Model (for real-time recording)

Download a Vosk model for Chinese (or your preferred language) from: https://alphacephei.com/vosk/models

Extract the model and set the environment variable:
```bash
export VOSK_MODEL_PATH=/path/to/vosk-model
```

### 3. Start the Network

```bash
openagents network start .
```

### 4. Access Studio

Open your browser to:
- **http://localhost:8700/studio/** - Studio web interface
- **http://localhost:8700/mcp** - MCP protocol endpoint

### 5. Launch the Agents

Start all three agents in separate terminals (make sure OPENAI_API_KEY is set):

**Recorder Agent (ASR):**
```bash
python agents/recorder.py
```

**Simple Agent (LLM):**
```bash
export OPENAI_API_KEY=your-api-key
python agents/simple_agent.py
```

**Card Maker Agent:**
```bash
python agents/card_maker.py
```

### 6. Use the Recipe Network

1. In Studio, go to the `recipe-uploads` channel
2. Upload a voice recording of a recipe OR trigger real-time recording via Studio interface
3. The Recorder agent will transcribe it (using vosk for real-time or Whisper for files)
4. The Simple agent will standardize the format
5. The Card Maker agent will generate a card with QR code
6. Find your card in the `recipe-cards` channel with a download link

## Configuration

- **Network Port:** 8700 (HTTP), 8600 (gRPC)
- **Studio:** http://localhost:8700/studio/
- **MCP:** http://localhost:8700/mcp
- **Channels:** `recipe-uploads`, `recipe-cards`

## Technical Implementation

- **Event Flow:** `recipe.audio.new` → `recipe.text` → `recipe.md.processed` → `recipe.card.generated` (file uploads)
- **Real-time Event Flow:** `recipe.audio.record` → `recipe.text` → `recipe.md.processed` → `recipe.card.generated` (real-time recording)
- **Shared Artifacts:** Stores recipe markdown and PNG cards
- **LLM Logs:** Tracks ASR and image generation usage
- **Protocols:** WebSocket (real-time) + HTTP (download cards)

## Next Steps

- Customize the card design in `agents/card_maker.py`
- Adjust the recipe formatting in `agents/simple_agent.py`
- Enhance the ASR capabilities in `agents/recorder.py`
- Add more sophisticated recipe parsing
- Integrate with image generation APIs for more beautiful cards