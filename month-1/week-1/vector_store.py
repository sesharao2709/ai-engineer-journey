import os
import vertexai
import psycopg2
from vertexai.language_models import TextEmbeddingModel
from dotenv import load_dotenv

load_dotenv()

# Initialize Vertex AI
vertexai.init(
    project=os.getenv("GCP_PROJECT_ID"),
    location="us-central1"
)

embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# ── DATABASE SETUP ─────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )

def setup_database():
    """Create the vector table — run once"""
    conn = get_connection()
    cursor = conn.cursor()

    # Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create documents table
    # Notice: embedding column is just a new data type
    # Everything else is standard SQL you already know
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          SERIAL PRIMARY KEY,
            content     TEXT NOT NULL,
            source      VARCHAR(255),
            chunk_index INTEGER,
            embedding   vector(768),
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS chunk_index INTEGER
    """)

    # Create index for fast similarity search
    # cursor.execute("""
    #     CREATE INDEX IF NOT EXISTS documents_embedding_idx
    #     ON documents
    #     USING ivfflat (embedding vector_cosine_ops)
    #     WITH (lists = 100);
    # """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database setup complete")

# ── INGESTION ──────────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """Convert text to vector using Vertex AI"""
    embeddings = embedding_model.get_embeddings([text])
    return embeddings[0].values

def store_document(content: str, source: str):
    embedding = embed_text(content)

    conn = get_connection()
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute("""
        SELECT id FROM documents 
        WHERE source = %s AND content = %s
    """, (source, content))

    if cursor.fetchone():
        print(f"⚠️  Already exists: '{content[:50]}...' — skipping")
        cursor.close()
        conn.close()
        return

    cursor.execute("""
        INSERT INTO documents (content, source, embedding)
        VALUES (%s, %s, %s)
    """, (content, source, embedding))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Stored: '{content[:50]}...'")



# def store_document(content: str, source: str):
#     """Store a document chunk with its embedding"""
#     # Generate embedding
#     embedding = embed_text(content)

#     # Store in pgvector — just a regular INSERT
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO documents (content, source, embedding)
#         VALUES (%s, %s, %s)
#     """, (content, source, embedding))
#     conn.commit()
#     cursor.close()
#     conn.close()
#     print(f"✅ Stored: '{content[:50]}...'")

# ── RETRIEVAL ──────────────────────────────────────────────────────

# def search_similar(query: str, top_k: int = 3) -> list[dict]:
#     """Find most similar documents to a query"""
#     # Embed the query
#     query_embedding = embed_text(query)

#     # Search — cosine similarity
#     # <=> operator means cosine distance in pgvector
#     # 1 - distance = similarity score
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT
#             content,
#             source,
#             1 - (embedding <=> %s::vector) as similarity
#         FROM documents
#         ORDER BY embedding <=> %s::vector
#         LIMIT %s
#     """, (query_embedding, query_embedding, top_k))

#     results = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     return [
#         {
#             "content": row[0],
#             "source": row[1],
#             "similarity": round(row[2], 4)
#         }
#         for row in results
#     ]

def search_similar(query: str, top_k: int = 3) -> list[dict]:
    query_embedding = embed_text(query)

    conn = get_connection()
    cursor = conn.cursor()

    # Sequential scan — reliable for small datasets
    cursor.execute("SET enable_indexscan = off;")

    cursor.execute("""
        SELECT
            content,
            source,
            1 - (embedding <=> %s::vector) as similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_embedding, query_embedding, top_k))

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

# ── MAIN — Run experiments ─────────────────────────────────────────

if __name__ == "__main__":

    # STEP 1 — Setup database
    print("Setting up database...")
    setup_database()

    # STEP 2 — Store sample Schwab-style compliance documents
    print("\nIngesting documents...")

    documents = [
        {
            "content": "Margin calls occur when the value of securities in a margin account falls below the broker's required minimum value. The investor must either deposit more funds or sell securities to meet the margin call within 24 hours.",
            "source": "schwab_margin_policy.pdf"
        },
        {
            "content": "Pattern day traders must maintain a minimum equity of $25,000 in their margin account on any day that the customer day trades. If the account falls below this requirement, the customer will not be permitted to day trade.",
            "source": "schwab_trading_rules.pdf"
        },
        {
            "content": "Portfolio rebalancing is the process of realigning the weightings of a portfolio of assets. It involves periodically buying or selling assets to maintain an original or desired level of asset allocation or risk.",
            "source": "schwab_investment_guide.pdf"
        },
        {
            "content": "A stop-loss order is designed to limit an investor's loss on a security position. Setting a stop-loss order for 10% below the price at which you bought the stock will limit your loss to 10%.",
            "source": "schwab_order_types.pdf"
        },
        {
            "content": "Wire transfer requests must be submitted before 4:00 PM ET to be processed same day. International wire transfers require additional verification and may take 2-3 business days to complete.",
            "source": "schwab_transfer_policy.pdf"
        },
    ]

    for doc in documents:
        store_document(doc["content"], doc["source"])

    # STEP 3 — Search with different queries
    print("\n" + "="*60)
    print("SEMANTIC SEARCH EXPERIMENTS")
    print("="*60)

    queries = [
        "What happens when my account value drops?",
        "How much money do I need for day trading?",
        "How do I send money internationally?",
        "What is portfolio rebalancing?",
    ]

    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)
        results = search_similar(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"  Result {i} (similarity: {result['similarity']})")
            print(f"  Source: {result['source']}")
            print(f"  Content: {result['content'][:100]}...")
            
# DEBUG — show ALL results with scores for a query
def search_all(query: str):
    """Show all documents ranked by similarity — for debugging"""
    query_embedding = embed_text(query)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            content,
            source,
            1 - (embedding <=> %s::vector) as similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
    """, (query_embedding, query_embedding))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\n🔍 ALL results for: '{query}'")
    print("-" * 50)
    for row in results:
        print(f"  {round(row[2], 4)} → {row[1]}")
        print(f"           {row[0][:80]}...")

# Add at bottom of main block:
print("\n\n=== DEBUG — ALL SIMILARITY SCORES ===")
search_all("What happens when my account value drops?")
search_all("How do I send money internationally?")
search_all("What is portfolio rebalancing?")
