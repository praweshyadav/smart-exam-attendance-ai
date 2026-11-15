from backend.database.database import initialize_database
from backend.services.student_service import (
    add_student,
    get_student,
    get_all_students,
    update_student,
    delete_student,
    student_exists,
    set_face_registered,
)


def main():
    print("\n===== STUDENT SERVICE TEST =====\n")

    # Make sure database exists
    initialize_database()

    test_student_id = "TEST001"
    test_student_name = "Test Student"

    # Clean previous test data if it exists
    if student_exists(test_student_id):
        delete_student(test_student_id)

    # 1. ADD
    print("1. Adding student...")
    result = add_student(test_student_id, test_student_name)

    assert result is True
    print("   PASS - Student added")

    # 2. GET
    print("2. Getting student...")
    student = get_student(test_student_id)

    assert student is not None
    assert student["student_id"] == test_student_id
    assert student["student_name"] == test_student_name

    print("   PASS - Student retrieved")
    print(f"   Student: {student}")

    # 3. EXISTS
    print("3. Checking student exists...")
    assert student_exists(test_student_id) is True

    print("   PASS - Student exists")

    # 4. GET ALL
    print("4. Getting all students...")
    students = get_all_students()

    assert any(
        student["student_id"] == test_student_id
        for student in students
    )

    print(f"   PASS - Found {len(students)} student(s)")

    # 5. UPDATE
    print("5. Updating student...")

    result = update_student(
        test_student_id,
        student_name="Updated Test Student"
    )

    assert result is True

    updated_student = get_student(test_student_id)

    assert updated_student["student_name"] == "Updated Test Student"

    print("   PASS - Student updated")

    # 6. FACE REGISTRATION STATUS
    print("6. Updating face registration status...")

    result = set_face_registered(test_student_id, True)

    assert result is True

    student = get_student(test_student_id)

    assert student["face_registered"] == 1

    print("   PASS - Face registration status updated")

    # 7. DELETE
    print("7. Deleting student...")

    result = delete_student(test_student_id)

    assert result is True
    assert student_exists(test_student_id) is False

    print("   PASS - Student deleted")

    print("\n================================")
    print("ALL STUDENT SERVICE TESTS PASSED")
    print("================================\n")


if __name__ == "__main__":
    main()