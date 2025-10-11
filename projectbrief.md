# VK MAX Telegram Bot - Project Brief

## Project Overview
**Name:** VK MAX Telegram Bot (TGMaxSummarizer)
**Type:** Telegram Bot for VK MAX Chat Analysis
**Purpose:** AI-powered chat summarization and analysis tool

## Core Functionality
- **VK MAX Integration:** Connects to VK MAX API to retrieve chat messages
- **AI Analysis:** Uses GigaChat AI for intelligent chat summarization
- **Telegram Interface:** Provides user-friendly bot interface for interaction
- **Database Management:** Stores chat data and analysis results
- **Multi-language Support:** Russian interface with comprehensive documentation

## Technical Stack
- **Language:** Python 3.x
- **Telegram Framework:** python-telegram-bot >= 22.0
- **VK Integration:** python-max-client
- **AI Service:** GigaChat API
- **Database:** SQLite (bot_database.db)
- **Process Management:** psutil for bot lifecycle management

## Key Components
1. **bot.py** - Main bot class and application setup
2. **handlers.py** - Command and message handlers (1052 lines)
3. **vk_integration.py** - VK MAX API integration (344 lines)
4. **chat_analyzer.py** - GigaChat AI analysis (256 lines)
5. **database.py** - Database operations (411 lines)
6. **keyboards.py** - Telegram keyboard layouts
7. **utils.py** - Utility functions (233 lines)
8. **config.py** - Configuration management

## Current Status
- **Development Phase:** Complete implementation
- **Database:** 1.1MB of existing data
- **Documentation:** Comprehensive README and setup guides
- **Security:** Token management and security guidelines
- **Deployment:** Ready for production with management scripts

## Project Structure
```
TGMaxSummarizer/
├── Core Bot Files
│   ├── bot.py (129 lines)
│   ├── handlers.py (1052 lines)
│   ├── keyboards.py (139 lines)
│   └── config.py (39 lines)
├── Integration Layer
│   ├── vk_integration.py (344 lines)
│   ├── chat_analyzer.py (256 lines)
│   └── database.py (411 lines)
├── Management Scripts
│   ├── start_bot.py (98 lines)
│   ├── quick_start.py (54 lines)
│   ├── status_bot.py (134 lines)
│   └── stop_bot.py (80 lines)
├── Documentation
│   ├── README.md (165 lines)
│   ├── HOW_TO_START.md (100 lines)
│   └── SECURITY.md (90 lines)
└── Configuration
    ├── requirements.txt
    ├── env_example_safe.txt
    └── .gitignore
```

## Business Value
- **Automation:** Reduces manual chat analysis time
- **Intelligence:** AI-powered insights from chat conversations
- **Accessibility:** Easy-to-use Telegram interface
- **Scalability:** Handles multiple chats and users
- **Integration:** Seamless VK MAX and AI service integration
