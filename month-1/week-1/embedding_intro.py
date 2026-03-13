import os
import vertexai
from vertexai.language_models import TextEmbeddingModel
from dotenv import load_dotenv

load_dotenv()

# Initialize Vertex AI
# Replace with your personal GCP project ID
vertexai.init(
    project=os.getenv("GCP_PROJECT_ID"),
    location="us-central1"
)

# Load the embedding model
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# ── EXPERIMENT 1 — Generate your first embedding ──────────────────

print("=== EXPERIMENT 1: Your First Embedding ===")
texts = ["What is a margin call?"]
embeddings = model.get_embeddings(texts)
vector = embeddings[0].values

print(f"Text: '{texts[0]}'")
print(f"Vector length: {len(vector)}")
print(f"First 5 numbers: {vector[:5]}")
print(f"Last 5 numbers: {vector[-5:]}")
print()

# ── EXPERIMENT 2 — Similar sentences ─────────────────────────────

print("=== EXPERIMENT 2: Similar vs Different Sentences ===")

sentences = [
    "What is a margin call?",                    # original
    "Explain what a margin call means",           # similar meaning
    "How does margin trading work?",              # related topic
    "What is the weather today?",                 # completely different
    "How much money is in my account?",           # financial but different
]

embeddings = model.get_embeddings(sentences)
vectors = [e.values for e in embeddings]

# Compare similarity between sentence 0 and all others
# We use dot product — higher number = more similar
def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))

base = vectors[0]
print(f"Base sentence: '{sentences[0]}'")
print()
print("Similarity scores:")
for i, (sentence, vector) in enumerate(zip(sentences, vectors)):
    score = dot_product(base, vector)
    print(f"  {score:.4f} → '{sentence}'")

print()
print("Higher score = more similar meaning")
print("Notice: similar financial sentences score higher")
print("Notice: weather question scores lowest")
