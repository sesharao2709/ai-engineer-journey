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
- [x] Day 2 — Understood tokens, system prompts, parameters ✅
      KEY INSIGHT: Model doesn't know internal company data
      THIS is exactly why RAG exists — to inject your 
      private data into the model's context at query time

## Day 3 Observations:

1. How many dimensions does each embedding have?
   → Text: 'What is a margin call?'
    Vector length: 768
    we are using we are using text-embedding-004 model from Google Vertex AI
    the we are using text-embedding-004 produces 768-dimensional embeddings.
    When you run the script successfully, this will output 768, showing that each text embedding is represented as a vector with 768 numerical values (dimensions).

    Each dimension captures different semantic aspects of the input text, and the 768 dimensions together create a rich representation that allows the model to understand semantic similarity between different pieces of text.

2. Which sentence scored highest similarity to "What is a margin call?"
   → Explain what a margin call means scored 0.9787 score which is highest
   similar financial sentences score higher

3. Which sentence scored lowest and why?
   → What is the weather today which scored 0.2378 is the lowest 
   irrelevant sentences

4. What does this tell you about how RAG finds relevant documents?
   → RAG uses semantic similarity (not keyword matching) to find relevant docs
   It converts both the user query AND all stored documents into embeddings
   Then calculates similarity scores between query embedding and document embeddings
   Documents with highest similarity scores get retrieved and added to LLM context
   This is why "margin call" and "explain margin call" score so high (0.9787)
   while "weather" scores low (0.2378) - the vectors capture MEANING, not just words


## Day 4 Observations:

1. Duplicate ingestion is a real production problem
   → Always check before inserting
   → ivfflat index needs 1000+ docs to work reliably

2. Vague queries produce ambiguous results
   → "What happens when account drops?" → 0.43 (unclear)
   → "What is a margin call?" → 0.85+ (precise)
   → Solution: Query rewriting in production

3. Similarity thresholds matter
   → Below 0.5 = uncertain, better to return nothing
   → Above 0.8 = high confidence match
   → In finance: wrong answer is worse than no answer

4. The database itself gives you hints
   → "ivfflat index created with little data" warning
   → Always read system messages — they tell the truth
```

---

## What's Coming Tomorrow — Day 5

This is the one you've been building toward:
```
Day 1 → Claude API          ✅
Day 2 → LLM understanding   ✅
Day 3 → Embeddings          ✅
Day 4 → Vector database     ✅
Day 5 → Connect ALL of it   ← tomorrow
```

Tomorrow you build the complete RAG loop:
```
User question
     ↓
Embed the question
     ↓
Search your pgvector database
     ↓
Retrieve relevant chunks
     ↓
Feed to Claude with context
     ↓
Grounded answer with citations

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