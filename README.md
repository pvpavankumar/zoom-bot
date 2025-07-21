# 🤖 Zoom Interview Bot

An intelligent AI-powered assistant that provides real-time guidance during Zoom interviews. Features advanced audio processing, AI conversation analysis, and automatic startup validation.

## ✨ Key Features

- 🎤 **Modern Audio Stack** - SoundDevice-based audio processing (no PyAudio dependency)
- 🗣️ **Real-time Speech Recognition** - Google Speech API with voice activity detection
- 🤖 **AI-Powered Analysis** - OpenAI GPT-4 for conversation insights and interview guidance
- 🔄 **Distributed Processing** - Celery + Redis for multi-room handling
- 🧪 **Automatic Validation** - Integrated startup tests ensure system readiness
- 🌐 **REST API** - FastAPI-based interface with health monitoring
- 🔐 **Secure Integration** - JWT authentication and encrypted communications

## 🏗️ Project Structure

```
📁 ZoomInterviewBot/
├── 📄 .env                          # Your configuration
├── 📄 requirements.txt               # Dependencies
├── 📄 start_bot_windows.bat         # Easy Windows startup
├──  src/                         # Core application
│   ├── 📄 main.py                  # Entry point with validation
│   ├── 📁 api/                     # REST API (FastAPI)
│   ├── 📁 audio/                   # Audio processing
│   ├──  ai/                      # AI analysis & suggestions
│   ├── � core/                    # Bot management
│   ├── 📁 tasks/                   # Background processing
│   └── � zoom/                    # Zoom integration
├── 📁 tests/                       # Test suite
│   ├── 📄 startup_validator.py     # Startup validation
│   └── 📄 test_*.py                # Component tests
├── 📄 demo_live_test.py            # Safe demo testing
├── � live_test.py                 # Real meeting testing
└── � fix_auth_comprehensive.py    # Auth troubleshooting
```
## 💻 Commands

### Basic Usage
```bash
# Start the bot with validation
python -m src.main

# Run demo (safe, no real meeting)
python demo_live_test.py

# Test with real Zoom meeting
python live_test.py <meeting_id> observer
```

### Testing & Troubleshooting
```bash
# Validate startup systems only
python tests\startup_validator.py

# Fix Zoom authentication issues
python fix_auth_comprehensive.py

# Run comprehensive tests
python tests\run_all_tests.py
```

### Logs & Monitoring
```bash
# View logs
type logs\zoom_bot.log

# Check API health
curl http://localhost:8000/health
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your API keys:
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_secret  
OPENAI_API_KEY=your_openai_key
```

### 3. Start the Bot
```bash
# Windows (Recommended)
start_bot_windows.bat

# Or manual start
python -m src.main
```

### 4. Test Everything Works
```bash
# Run demo (no real meeting needed)
python demo_live_test.py

# Test with real Zoom meeting
python live_test.py <meeting_id> observer
```

## 🧪 Built-in Validation

The bot automatically validates all systems on startup:

✅ **Python Environment** - Version and virtual environment  
✅ **Project Structure** - Required files and directories  
✅ **Configuration** - API keys and settings  
✅ **Dependencies** - All required packages  
✅ **Redis Connection** - Task queue (if available)  
✅ **Audio System** - Microphone and sound devices  

**Example startup output:**
```
🧪 STARTUP VALIDATION CHECKS
==================================================
🔍 Validating Python Environment...
✅ Python Environment validation passed
🔍 Validating Configuration...  
✅ Configuration validation passed
🔍 Validating Dependencies...
   ✅ Found 92 installed packages
✅ Dependencies validation passed

🎉 ALL VALIDATIONS PASSED! Bot ready for operation.
```

## ⚙️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI + Uvicorn | REST API and async processing |
| **Task Queue** | Celery + Redis | Background processing |
| **Audio** | SoundDevice | Cross-platform audio capture |
| **Speech** | Google Speech API | Real-time transcription |
| **AI** | OpenAI GPT-4 | Conversation analysis |
| **Platform** | Zoom SDK | Meeting integration |
| **Validation** | Custom testing | Startup health checks |

## � System Requirements

- **Python 3.8+**
- **Microphone access**
- **Internet connection**
- **Zoom account with API access**
- **OpenAI API key**

## 🆘 Troubleshooting

### Common Issues

**❌ "Access token expired"**
```bash
python fix_auth_comprehensive.py
```

**❌ Audio not working**
- Check microphone permissions
- Run: `python -c "import sounddevice; print(sounddevice.query_devices())"`

**❌ Bot not starting**
- Check logs: `type logs\zoom_bot.log`
- Validate setup: `python tests\startup_validator.py`

### Support
- Check logs in `logs/zoom_bot.log`
- Run validation: `python tests\startup_validator.py`
- Test components: `python demo_live_test.py`

---

**🎯 Ready to enhance your Zoom interviews with AI assistance!**
