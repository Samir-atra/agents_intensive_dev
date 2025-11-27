# Code Broker: AI-Powered Code Assessment Agent 🤖

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![ADK](https://img.shields.io/badge/Google-ADK-4285F4?logo=google)](https://google.github.io/adk-docs/)

> **Agents Intensive Capstone Project** - A multi-agent system for comprehensive code analysis and quality assessment

## 🎯 What is Code Broker?

Code Broker is an intelligent multi-agent system built with Google's ADK that automatically analyzes code files, directories, or GitHub repositories and generates detailed assessment reports with actionable improvement recommendations.

## ✨ Key Features

- 🔍 **Multi-Source Analysis**: Files, directories, or GitHub repositories
- 📊 **Comprehensive Scoring**: Correctness, security, style, and maintainability metrics
- 🤖 **5-Agent System**: Parallel processing with specialized AI agents
- 📝 **Beautiful Reports**: Markdown and HTML formatted assessment reports
- ⚡ **Fast & Reliable**: Async processing with retry mechanisms
- 🎨 **Pylint Integration**: Automated Python code quality analysis

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/Samir-atra/agents_intensive_dev.git
cd agents_intensive_dev
pip install -r requirements.txt

# Configure environment (add your GOOGLE_API_KEY and GITHUB_TOKEN)
cp .env.example .env

# Run the notebook
jupyter notebook notebooks/code_broker.ipynb
```

## 📂 Project Structure

```
agents_intensive_dev/
├── notebooks/
│   └── code_broker.ipynb          # Main executable notebook
├── reports/                        # Generated assessment reports
├── src/                            # Source code modules
├── Docs/                           # Documentation
├── KAGGLE_WRITEUP.md              # Detailed competition writeup
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🏗️ Architecture

Code Broker uses a **hierarchical multi-agent architecture**:

- **Report Generator** (Orchestrator): Coordinates the entire workflow
- **Sequential Pipeline Agent**: Manages assessment flow
- **Parallel Assessment Agent**: Runs 3 agents concurrently:
  - Correctness Assessor
  - Style Assessor  
  - Description Generator
- **Improvement Recommender**: Synthesizes findings into actionable recommendations

## 📖 Documentation

For a detailed writeup including architecture, design decisions, and technical details, see:
**[KAGGLE_WRITEUP.md](KAGGLE_WRITEUP.md)**

## 🎓 Competition

This project was created for the **Agents Intensive Capstone Project** on Kaggle:
https://www.kaggle.com/competitions/agents-intensive-capstone-project

## 👨‍💻 Author

**Samer Atra** - [GitHub](https://github.com/Samir-atra)

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

⭐ **Star this repo if you find it useful!**
