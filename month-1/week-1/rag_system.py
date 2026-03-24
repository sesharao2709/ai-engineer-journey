import os
import json
import vertexai
import psycopg2
import anthropic
from vertexai.language_models import TextEmbeddingModel
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── INITIALIZE ─────────────────────────────────────────────────────

vertexai.init(
    project=os.getenv("GCP_PROJECT_ID"),
    location="us-central1"
)

embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── DATABASE ───────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )

    # ── STEP 1: EMBED ──────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    embeddings = embedding_model.get_embeddings([text])
    return embeddings[0].values

# ── STEP 2: RETRIEVE ───────────────────────────────────────────────

def retrieve(query: str, top_k: int = 3,
             min_similarity: float = 0.4) -> list[dict]:
    """
    Search pgvector for most relevant chunks.
    If similarity below threshold — don't return it.
    In finance: no answer is better than wrong answer.
    """
    query_embedding = embed_text(query)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET enable_indexscan = off;")
    cursor.execute("""
        SELECT
            content,
            source,
            1 - (embedding <=> %s::vector) as similarity
        FROM documents
        WHERE 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_embedding, query_embedding,
          min_similarity, query_embedding, top_k))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "content": row[0],
            "source": row[1],
            "similarity": round(row[2], 4)
        }
        for row in results
    ]

# ── STEP 3: GENERATE ───────────────────────────────────────────────

def generate(question: str, chunks: list[dict]) -> dict:
    """
    Feed retrieved chunks to Claude as context.
    Strict rules prevent hallucination.
    """
    context = "\n\n".join([
        f"Source: {c['source']}\n"
        f"Relevance Score: {c['similarity']}\n"
        f"Content: {c['content']}"
        for c in chunks
    ])

    sources = list(set(c['source'] for c in chunks))

    response = claude.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system="""You are a compliance assistant at Charles Schwab.

STRICT RULES:
1. ONLY answer using the provided context
2. ALWAYS cite which source document your answer is from
3. If answer is NOT in context say exactly:
   "I don't have that information in my knowledge base."
4. NEVER make up financial information
5. Answer first, then list Sources at the bottom""",
        messages=[{
            "role": "user",
            "content": f"""Context:
{context}

Question: {question}

Answer using only the context above and cite your sources."""
        }]
    )

    return {
        "answer": response.content[0].text,
        "sources": sources,
        "chunks_used": len(chunks),
        "tokens_used": response.usage.input_tokens +
                       response.usage.output_tokens
    }

# ── STEP 4: AUDIT LOG ──────────────────────────────────────────────

def audit_log(question: str, result: dict):
    """
    Log EVERY interaction.
    Non-negotiable at Schwab — every AI response
    must be traceable for compliance purposes.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer_preview": result["answer"][:150],
        "sources": result["sources"],
        "chunks_used": result["chunks_used"],
        "tokens_used": result["tokens_used"]
    }

    with open("audit_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"📝 Audit logged at {entry['timestamp']}")

# ── COMPLETE RAG PIPELINE ──────────────────────────────────────────

def ask(question: str) -> str:
    """
    The complete RAG pipeline:
    Question → Embed → Retrieve → Generate → Log → Answer
    """
    print(f"\n{'='*60}")
    print(f"❓ Question: {question}")
    print(f"{'='*60}")

    # Step 1 — Retrieve
    print("🔍 Searching knowledge base...")
    chunks = retrieve(question, top_k=3, min_similarity=0.4)

    # No relevant chunks found — refuse to answer
    if not chunks:
        answer = "I don't have that information in my knowledge base."
        print(f"⚠️  No relevant chunks found above threshold")
        print(f"💬 Answer: {answer}")
        return answer

    print(f"✅ Found {len(chunks)} relevant chunks:")
    for c in chunks:
        print(f"   {c['similarity']} → {c['source']}")

    # Step 2 — Generate
    print("🤖 Generating grounded answer...")
    result = generate(question, chunks)

    # Step 3 — Audit log
    audit_log(question, result)

    # Step 4 — Display
    print(f"\n💬 Answer:")
    print(result["answer"])
    print(f"\n📚 Sources: {', '.join(result['sources'])}")
    print(f"🔢 Tokens used: {result['tokens_used']}")

    return result["answer"]

# ── RUN TESTS ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Schwab Compliance RAG System — Day 5")
    print("Testing complete pipeline...\n")

ask("What is the minimum deposit to open a margin account?")
ask("How long do international wire transfers take?")
ask("What documents do I need to open an account?")
ask("What is the early withdrawal penalty for an IRA?")
ask("What is the margin interest rate?")