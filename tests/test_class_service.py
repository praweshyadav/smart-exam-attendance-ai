from backend.database.database import initialize_database
from backend.services.class_service import (
    add_class,
    get_class,
    get_all_classes,
    update_class,
    delete_class,
    class_exists,
    get_students_by_class,
)
from backend.services.student_service import (
    add_student,
    delete_student,
)


def main():
    print("\n===== CLASS SERVICE TEST =====\n")

    initialize_database()

    test_class_name = "TEST CLASS"
    test_department = "Computer Science"
    test_semester = 6

    # Remove old test class if it exists
    classes = get_all_classes()

    for class_data in classes:
        if class_data["class_name"] == test_class_name:
            delete_class(class_data["class_id"])

    # 1. ADD CLASS
    print("1. Adding class...")

    result = add_class(
        test_class_name,
        test_department,
        test_semester
    )

    assert result is True
    print("   PASS - Class added")

    # Get class ID
    classes = get_all_classes()

    test_class = next(
        item
        for item in classes
        if item["class_name"] == test_class_name
    )

    class_id = test_class["class_id"]

    # 2. GET CLASS
    print("2. Getting class...")

    class_data = get_class(class_id)

    assert class_data is not None
    assert class_data["class_name"] == test_class_name

    print("   PASS - Class retrieved")
    print(f"   Class: {class_data}")

    # 3. CHECK EXISTS
    print("3. Checking class exists...")

    assert class_exists(class_id) is True

    print("   PASS - Class exists")

    # 4. UPDATE
    print("4. Updating class...")

    result = update_class(
        class_id,
        class_name="UPDATED TEST CLASS"
    )

    assert result is True

    updated_class = get_class(class_id)

    assert updated_class["class_name"] == "UPDATED TEST CLASS"

    print("   PASS - Class updated")

    # 5. ADD STUDENT TO CLASS
    print("5. Adding test student to class...")

    test_student_id = "CLASS_TEST_001"

    if add_student(
        test_student_id,
        "Class Test Student",
        class_id
    ) is False:
        pass

    students = get_students_by_class(class_id)

    assert any(
        student["student_id"] == test_student_id
        for student in students
    )

    print("   PASS - Student found in class")

    # 6. DELETE STUDENT
    print("6. Cleaning test student...")

    delete_student(test_student_id)

    print("   PASS - Test student removed")

    # 7. DELETE CLASS
    print("7. Deleting class...")

    result = delete_class(class_id)

    assert result is True
    assert class_exists(class_id) is False

    print("   PASS - Class deleted")

    print("\n==============================")
    print("ALL CLASS SERVICE TESTS PASSED")
    print("==============================\n")


if __name__ == "__main__":
    main()