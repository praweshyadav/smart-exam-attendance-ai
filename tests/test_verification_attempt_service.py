from backend.services.verification_attempt_service import (
    VerificationAttemptService,
)
from backend.services.student_service import (
    add_student,
    delete_student,
)


print("===== VERIFICATION ATTEMPT SERVICE TEST =====")


service = VerificationAttemptService()

TEST_STUDENT_ID = "TEST_STUDENT_001"


# -------------------------------------------------
# Test student setup
# -------------------------------------------------

print("0. Creating temporary test student...")

# Clean up in case an earlier interrupted test
# left the student behind.
delete_student(TEST_STUDENT_ID)

created = add_student(
    TEST_STUDENT_ID,
    "Test Student",
)

if not created:
    raise RuntimeError(
        "Temporary test student could not be created."
    )

print("   PASS")


# -------------------------------------------------
# Test 1: Record successful attempt
# -------------------------------------------------

print("1. Recording successful verification attempt...")

success_attempt_id = service.record_attempt(
    student_id=TEST_STUDENT_ID,
    result="Success",
    similarity=0.87,
    liveness_result="Verified",
    reason="Student verified successfully.",
)

print(
    f"   Attempt ID: {success_attempt_id}"
)

if not success_attempt_id:
    raise RuntimeError(
        "Successful attempt was not recorded."
    )

print("   PASS")


# -------------------------------------------------
# Test 2: Record failed attempt
# -------------------------------------------------

print("2. Recording failed verification attempt...")

failed_attempt_id = service.record_attempt(
    student_id=TEST_STUDENT_ID,
    result="Failed",
    similarity=0.31,
    liveness_result="Not Verified",
    reason="Face not recognized.",
)

print(
    f"   Attempt ID: {failed_attempt_id}"
)

if not failed_attempt_id:
    raise RuntimeError(
        "Failed attempt was not recorded."
    )

print("   PASS")


# -------------------------------------------------
# Test 3: Get one attempt
# -------------------------------------------------

print("3. Getting successful attempt...")

attempt = service.get_attempt(
    success_attempt_id
)

if attempt is None:
    raise RuntimeError(
        "Attempt could not be retrieved."
    )

print(
    f"   Student ID: {attempt['student_id']}"
)

print(
    f"   Result: {attempt['result']}"
)

print(
    f"   Similarity: {attempt['similarity']}"
)

print(
    f"   Liveness: {attempt['liveness_result']}"
)

if attempt["student_id"] != TEST_STUDENT_ID:
    raise RuntimeError(
        "Incorrect student ID."
    )

if attempt["result"] != "Success":
    raise RuntimeError(
        "Incorrect verification result."
    )

if attempt["similarity"] != 0.87:
    raise RuntimeError(
        "Incorrect similarity."
    )

if attempt["liveness_result"] != "Verified":
    raise RuntimeError(
        "Incorrect liveness result."
    )

print("   PASS")


# -------------------------------------------------
# Test 4: Check attempt exists
# -------------------------------------------------

print("4. Checking attempt exists...")

if not service.attempt_exists(
    success_attempt_id
):
    raise RuntimeError(
        "Attempt should exist."
    )

print("   PASS")


# -------------------------------------------------
# Test 5: Get all attempts
# -------------------------------------------------

print("5. Getting all attempts...")

attempts = service.get_all_attempts()

print(
    f"   Total attempts: {len(attempts)}"
)

if len(attempts) < 2:
    raise RuntimeError(
        "Expected at least two attempts."
    )

print("   PASS")


# -------------------------------------------------
# Test 6: Get attempts by student
# -------------------------------------------------

print("6. Getting attempts by student...")

student_attempts = (
    service.get_attempts_by_student(
        TEST_STUDENT_ID
    )
)

print(
    f"   Student attempts: "
    f"{len(student_attempts)}"
)

if len(student_attempts) != 2:
    raise RuntimeError(
        "Expected exactly two attempts "
        "for the test student."
    )

print("   PASS")


# -------------------------------------------------
# Test 7: Get attempts by result
# -------------------------------------------------

print("7. Getting successful attempts...")

successful_attempts = (
    service.get_attempts_by_result(
        "Success"
    )
)

print(
    f"   Successful attempts: "
    f"{len(successful_attempts)}"
)

if not any(
    attempt["id"] == success_attempt_id
    for attempt in successful_attempts
):
    raise RuntimeError(
        "Successful attempt was not found."
    )

print("   PASS")


# -------------------------------------------------
# Test 8: Get failed attempts
# -------------------------------------------------

print("8. Getting failed attempts...")

failed_attempts = (
    service.get_failed_attempts()
)

print(
    f"   Failed attempts: "
    f"{len(failed_attempts)}"
)

if not any(
    attempt["id"] == failed_attempt_id
    for attempt in failed_attempts
):
    raise RuntimeError(
        "Failed attempt was not found."
    )

print("   PASS")


# -------------------------------------------------
# Test 9: Invalid result
# -------------------------------------------------

print("9. Testing invalid verification result...")

try:

    service.record_attempt(
        student_id=TEST_STUDENT_ID,
        result="",
    )

    raise RuntimeError(
        "Empty result should raise ValueError."
    )

except ValueError as error:

    print(
        f"   Error: {error}"
    )

print("   PASS")


# -------------------------------------------------
# Test 10: Non-existing attempt
# -------------------------------------------------

print("10. Testing non-existing attempt...")

missing_attempt = service.get_attempt(
    999999
)

if missing_attempt is not None:
    raise RuntimeError(
        "Non-existing attempt should return None."
    )

if service.attempt_exists(999999):
    raise RuntimeError(
        "Non-existing attempt should not exist."
    )

print("   PASS")


# -------------------------------------------------
# Test 11: Delete successful attempt
# -------------------------------------------------

print("11. Deleting successful attempt...")

deleted = service.delete_attempt(
    success_attempt_id
)

if not deleted:
    raise RuntimeError(
        "Successful attempt was not deleted."
    )

if service.attempt_exists(
    success_attempt_id
):
    raise RuntimeError(
        "Deleted attempt should not exist."
    )

print("   PASS")


# -------------------------------------------------
# Test 12: Delete failed attempt
# -------------------------------------------------

print("12. Deleting failed attempt...")

deleted = service.delete_attempt(
    failed_attempt_id
)

if not deleted:
    raise RuntimeError(
        "Failed attempt was not deleted."
    )

if service.attempt_exists(
    failed_attempt_id
):
    raise RuntimeError(
        "Deleted attempt should not exist."
    )

print("   PASS")


# -------------------------------------------------
# Test 13: Delete non-existing attempt
# -------------------------------------------------

print("13. Testing deletion of non-existing attempt...")

deleted = service.delete_attempt(
    999999
)

if deleted:
    raise RuntimeError(
        "Deleting a non-existing attempt "
        "should return False."
    )

print("   PASS")


# -------------------------------------------------
# Cleanup
# -------------------------------------------------

print("14. Removing temporary test student...")

deleted_student = delete_student(
    TEST_STUDENT_ID
)

if not deleted_student:
    raise RuntimeError(
        "Temporary test student could not be deleted."
    )

print("   PASS")


print()
print("ALL VERIFICATION ATTEMPT SERVICE TESTS PASSED")