# AI Engineer Journey

Senior Java Backend Engineer at Charles Schwab 
transitioning to AI Engineering.

## Goal
AI Engineer in 6 months — March to September 2026

## Stack
- GCP (Vertex AI, Cloud Run, Cloud SQL)
- Python, FastAPI
- Claude API, Gemini API
- pgvector, LangChain

## Progress
- [x] Week 1 Day 1 — First Claude API call ← you'll tick this tonight

## Setup & Security

### Installation
```bash
pip install -r requirements.txt
```

### Environment Variables
For security, API keys are stored in environment variables:

1. Create a `.env` file (already gitignored)
2. Add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Security Note
- ⚠️ **Never commit API keys to Git**
- Use environment variables for all sensitive data
- The `.env` file is automatically ignored by Git