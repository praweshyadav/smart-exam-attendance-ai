import numpy as np

from backend.ai.face_database import FaceDatabase


print("===== FACE DATABASE TEST =====")

database = FaceDatabase()

# Use a temporary in-memory dictionary so the real database
# file is not affected by this test.
database._database = {}

test_student_id = "TEST_FACE_001"

test_embedding = np.random.rand(512).astype(np.float32)
updated_embedding = np.random.rand(512).astype(np.float32)


print("1. Saving embedding...")

result = database.save_embedding(
    test_student_id,
    test_embedding
)

if not result:
    raise RuntimeError("Embedding was not saved.")

print("   PASS")


print("2. Checking embedding exists...")

if not database.embedding_exists(test_student_id):
    raise RuntimeError("Embedding does not exist.")

print("   PASS")


print("3. Getting embedding...")

stored_embedding = database.get_embedding(test_student_id)

if stored_embedding is None:
    raise RuntimeError("Embedding could not be retrieved.")

print("   PASS")


print("4. Checking embedding shape...")

print(f"   Shape: {stored_embedding.shape}")

if stored_embedding.shape != (512,):
    raise RuntimeError("Invalid embedding shape.")

print("   PASS")


print("5. Checking duplicate protection...")

result = database.save_embedding(
    test_student_id,
    test_embedding
)

if result:
    raise RuntimeError(
        "Duplicate embedding should not be saved."
    )

print("   PASS")


print("6. Updating embedding...")

result = database.update_embedding(
    test_student_id,
    updated_embedding
)

if not result:
    raise RuntimeError("Embedding was not updated.")

print("   PASS")


print("7. Verifying updated embedding...")

stored_embedding = database.get_embedding(test_student_id)

if not np.array_equal(
    stored_embedding,
    updated_embedding
):
    raise RuntimeError(
        "Updated embedding does not match."
    )

print("   PASS")


print("8. Checking database count...")

if database.count() != 1:
    raise RuntimeError("Database count is incorrect.")

print("   PASS")


print("9. Deleting embedding...")

result = database.delete_embedding(test_student_id)

if not result:
    raise RuntimeError("Embedding was not deleted.")

print("   PASS")


print("10. Verifying deletion...")

if database.embedding_exists(test_student_id):
    raise RuntimeError(
        "Embedding still exists after deletion."
    )

print("   PASS")


print("ALL FACE DATABASE TESTS PASSED")