import numpy as np

from backend.ai.face_database import FaceDatabase
from backend.ai.face_matcher import FaceMatcher


print("===== FACE MATCHER TEST =====")


# Create isolated test database.
database = FaceDatabase()
database._database = {}


# Create test embeddings.
embedding_a = np.random.rand(512).astype(np.float32)
embedding_b = np.random.rand(512).astype(np.float32)


# Normalize embeddings.
embedding_a = embedding_a / np.linalg.norm(embedding_a)
embedding_b = embedding_b / np.linalg.norm(embedding_b)


print("1. Testing cosine similarity...")

similarity = FaceMatcher.cosine_similarity(
    embedding_a,
    embedding_a
)

print(f"   Similarity: {similarity:.6f}")

if not np.isclose(similarity, 1.0):
    raise RuntimeError(
        "Identical embeddings should have similarity 1.0."
    )

print("   PASS")


print("2. Testing embedding validation...")

try:
    FaceMatcher.cosine_similarity(
        np.random.rand(128),
        embedding_a
    )
except ValueError:
    print("   PASS")
else:
    raise RuntimeError(
        "Invalid embedding shape was not rejected."
    )


print("3. Testing empty database...")

matcher = FaceMatcher(
    database=database,
    threshold=0.45
)

result = matcher.find_best_match(
    embedding_a
)

if result["matched"]:
    raise RuntimeError(
        "Empty database should not produce a match."
    )

if result["student_id"] is not None:
    raise RuntimeError(
        "Empty database should return no student."
    )

print("   PASS")


print("4. Saving test student embedding...")

database.save_embedding(
    "TEST_STUDENT_001",
    embedding_a
)

print("   PASS")


print("5. Testing exact embedding match...")

result = matcher.find_best_match(
    embedding_a
)

print(f"   Result: {result}")

if not result["matched"]:
    raise RuntimeError(
        "Exact embedding should match."
    )

if result["student_id"] != "TEST_STUDENT_001":
    raise RuntimeError(
        "Incorrect student was matched."
    )

if not np.isclose(
    result["similarity"],
    1.0,
    atol=1e-5
):
    raise RuntimeError(
        "Exact match similarity should be approximately 1.0."
    )

print("   PASS")


print("6. Testing embedding below threshold...")

# Create a deliberately opposite embedding.
embedding_c = -embedding_a

result = matcher.find_best_match(
    embedding_c
)

print(f"   Result: {result}")

if result["matched"]:
    raise RuntimeError(
        "Embedding below the threshold should not match."
    )

if result["student_id"] is not None:
    raise RuntimeError(
        "Student ID should be None when there is no match."
    )

print("   PASS")


print("7. Testing threshold behavior...")

high_threshold_matcher = FaceMatcher(
    database=database,
    threshold=1.1
)

result = high_threshold_matcher.find_best_match(
    embedding_a
)

if result["matched"]:
    raise RuntimeError(
        "Similarity below threshold should not match."
    )

if result["student_id"] is not None:
    raise RuntimeError(
        "Student ID should be None when not matched."
    )

print("   PASS")


print("ALL FACE MATCHER TESTS PASSED")