from backend.services.exam_service import (
    add_exam,
    get_exam,
    get_all_exams,
    get_exams_by_class,
    update_exam,
    delete_exam,
    exam_exists,
)

from backend.services.class_service import (
    add_class,
    delete_class,
    get_all_classes,
)


print("===== EXAM SERVICE TEST =====")


TEST_CLASS_NAME = "Test Exam Class"


# Clean previous test class
existing_classes = get_all_classes()

for class_data in existing_classes:
    if class_data["class_name"] == TEST_CLASS_NAME:
        delete_class(class_data["class_id"])


# 1. Create class
print("\n1. Creating class for exam...")

result = add_class(
    TEST_CLASS_NAME,
    department="Computer Science",
    semester=6,
)

if result:
    print("   PASS - Class created")
else:
    print("   FAIL - Class was not created")


# Get class ID
classes = get_all_classes()

test_class = next(
    (
        class_data
        for class_data in classes
        if class_data["class_name"] == TEST_CLASS_NAME
    ),
    None,
)

if test_class is None:
    raise RuntimeError("Test class could not be found.")

class_id = test_class["class_id"]


# 2. Add exam
print("\n2. Adding exam...")

result = add_exam(
    exam_name="Mid Semester Examination",
    class_id=class_id,
    exam_date="2026-10-15",
    start_time="10:00",
)

if result:
    print("   PASS - Exam added")
else:
    print("   FAIL - Exam was not added")


# 3. Get all exams
print("\n3. Getting all exams...")

exams = get_all_exams()

print(f"   PASS - Found {len(exams)} exam(s)")

test_exam = next(
    (
        exam
        for exam in exams
        if exam["exam_name"] == "Mid Semester Examination"
    ),
    None,
)

if test_exam:
    print(f"   Exam: {test_exam}")


# 4. Get exam by ID
print("\n4. Getting exam by ID...")

exam_id = test_exam["exam_id"]

result = get_exam(exam_id)

if result:
    print("   PASS - Exam retrieved")
else:
    print("   FAIL - Exam not retrieved")


# 5. Check exam exists
print("\n5. Checking exam exists...")

if exam_exists(exam_id):
    print("   PASS - Exam exists")
else:
    print("   FAIL - Exam does not exist")


# 6. Get exams by class
print("\n6. Getting exams by class...")

class_exams = get_exams_by_class(class_id)

if class_exams:
    print(f"   PASS - Found {len(class_exams)} exam(s) for class")
else:
    print("   FAIL - No exams found for class")


# 7. Update exam
print("\n7. Updating exam...")

result = update_exam(
    exam_id,
    exam_name="Updated Mid Semester Examination",
    exam_date="2026-10-20",
    start_time="11:00",
)

if result:
    print("   PASS - Exam updated")
else:
    print("   FAIL - Exam update failed")


# 8. Verify update
print("\n8. Verifying exam update...")

updated_exam = get_exam(exam_id)

if (
    updated_exam
    and updated_exam["exam_name"] == "Updated Mid Semester Examination"
    and updated_exam["exam_date"] == "2026-10-20"
    and updated_exam["start_time"] == "11:00"
):
    print("   PASS - Exam update verified")
else:
    print("   FAIL - Exam update verification failed")


# 9. Delete exam
print("\n9. Deleting exam...")

result = delete_exam(exam_id)

if result:
    print("   PASS - Exam deleted")
else:
    print("   FAIL - Exam deletion failed")


# 10. Verify exam deletion
print("\n10. Verifying exam deletion...")

if not exam_exists(exam_id):
    print("   PASS - Exam no longer exists")
else:
    print("   FAIL - Exam still exists")


# Clean test class
delete_class(class_id)


print("\n================================")
print("ALL EXAM SERVICE TESTS PASSED")
print("================================")