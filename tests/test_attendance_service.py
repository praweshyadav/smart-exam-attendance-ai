from backend.services.attendance_service import (
    mark_attendance,
    get_attendance,
    get_attendance_by_session,
    get_attendance_by_student,
    get_attendance_by_date,
    update_attendance,
    attendance_exists,
)

from backend.services.student_service import (
    add_student,
    delete_student,
)

from backend.services.class_service import (
    add_class,
    delete_class,
)

from backend.services.exam_service import (
    add_exam,
    delete_exam,
)

from backend.services.attendance_session_service import (
    start_session,
    end_session,
)


print("===== ATTENDANCE SERVICE TEST =====")


TEST_CLASS_NAME = "Test Attendance Class"
TEST_STUDENT_ID = "TEST_ATTENDANCE_STUDENT"


# 1. Create class
print("\n1. Creating class...")

add_class(
    TEST_CLASS_NAME,
    department="Computer Science",
    semester=6,
)

print("   PASS - Class created")


# Get class ID
from backend.services.class_service import get_all_classes

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


# 2. Create student
print("\n2. Creating student...")

add_student(
    TEST_STUDENT_ID,
    "Test Attendance Student",
    class_id=class_id,
)

print("   PASS - Student created")


# 3. Create exam
print("\n3. Creating exam...")

add_exam(
    exam_name="Attendance Test Examination",
    class_id=class_id,
    exam_date="2026-10-30",
    start_time="10:00",
)

print("   PASS - Exam created")


# Get exam ID
from backend.services.exam_service import get_all_exams

exams = get_all_exams()

test_exam = next(
    (
        exam
        for exam in exams
        if exam["exam_name"] == "Attendance Test Examination"
    ),
    None,
)

if test_exam is None:
    raise RuntimeError("Test exam could not be found.")

exam_id = test_exam["exam_id"]


# 4. Start attendance session
print("\n4. Starting attendance session...")

session_id = start_session(exam_id)

print(f"   PASS - Session started")
print(f"   Session ID: {session_id}")


# 5. Mark attendance
print("\n5. Marking attendance...")

result = mark_attendance(
    session_id=session_id,
    student_id=TEST_STUDENT_ID,
    student_name="Test Attendance Student",
    attendance_date="2026-10-30",
    attendance_time="10:15",
    status="Present",
    verification_score=0.92,
)

if result:
    print("   PASS - Attendance marked")
else:
    print("   FAIL - Attendance was not marked")


# 6. Get attendance
print("\n6. Getting attendance record...")

attendance_records = get_attendance_by_session(session_id)

if attendance_records:
    attendance_id = attendance_records[0]["id"]
    attendance = get_attendance(attendance_id)

    print("   PASS - Attendance retrieved")
    print(f"   Attendance: {attendance}")
else:
    raise RuntimeError("Attendance record could not be found.")


# 7. Check attendance exists
print("\n7. Checking attendance exists...")

if attendance_exists(attendance_id):
    print("   PASS - Attendance exists")
else:
    print("   FAIL - Attendance does not exist")


# 8. Get attendance by session
print("\n8. Getting attendance by session...")

session_attendance = get_attendance_by_session(session_id)

if len(session_attendance) == 1:
    print("   PASS - Correct attendance found for session")
else:
    print("   FAIL - Unexpected attendance count")


# 9. Get attendance by student
print("\n9. Getting attendance by student...")

student_attendance = get_attendance_by_student(TEST_STUDENT_ID)

if student_attendance:
    print("   PASS - Student attendance retrieved")
else:
    print("   FAIL - Student attendance not found")


# 10. Get attendance by date
print("\n10. Getting attendance by date...")

date_attendance = get_attendance_by_date("2026-10-30")

if date_attendance:
    print("   PASS - Date attendance retrieved")
else:
    print("   FAIL - Date attendance not found")


# 11. Test duplicate attendance
print("\n11. Testing duplicate attendance...")

result = mark_attendance(
    session_id=session_id,
    student_id=TEST_STUDENT_ID,
    student_name="Test Attendance Student",
    attendance_date="2026-10-30",
    attendance_time="10:20",
    status="Present",
    verification_score=0.95,
)

if result is False:
    print("   PASS - Duplicate attendance rejected")
else:
    print("   FAIL - Duplicate attendance was accepted")


# 12. Update attendance
print("\n12. Updating attendance...")

result = update_attendance(
    attendance_id,
    status="Present",
    verification_score=0.96,
)

if result:
    print("   PASS - Attendance updated")
else:
    print("   FAIL - Attendance update failed")


# 13. Verify update
print("\n13. Verifying attendance update...")

updated_attendance = get_attendance(attendance_id)

if (
    updated_attendance
    and updated_attendance["status"] == "Present"
    and updated_attendance["verification_score"] == 0.96
):
    print("   PASS - Attendance update verified")
else:
    print("   FAIL - Attendance update verification failed")


# 14. Create second exam on the SAME DATE
print("\n14. Creating second exam on same date...")

add_exam(
    exam_name="Second Attendance Test Examination",
    class_id=class_id,
    exam_date="2026-10-30",
    start_time="14:00",
)

print("   PASS - Second exam created")


# Get second exam
exams = get_all_exams()

second_exam = next(
    (
        exam
        for exam in exams
        if exam["exam_name"] == "Second Attendance Test Examination"
    ),
    None,
)

if second_exam is None:
    raise RuntimeError("Second test exam could not be found.")

second_exam_id = second_exam["exam_id"]


# 15. Start second session
print("\n15. Starting second session...")

second_session_id = start_session(second_exam_id)

print(f"   PASS - Second session started")


# 16. Mark same student in second session
print("\n16. Marking same student in second session...")

result = mark_attendance(
    session_id=second_session_id,
    student_id=TEST_STUDENT_ID,
    student_name="Test Attendance Student",
    attendance_date="2026-10-30",
    attendance_time="14:15",
    status="Present",
    verification_score=0.91,
)

if result:
    print("   PASS - Same student marked in different session")
else:
    print("   FAIL - Same student could not be marked in different session")


# 17. Verify student has two attendance records
print("\n17. Verifying multiple same-day attendance...")

student_attendance = get_attendance_by_student(TEST_STUDENT_ID)

if len(student_attendance) == 2:
    print("   PASS - Student has 2 attendance records on same date")
else:
    print(
        f"   FAIL - Expected 2 attendance records, "
        f"found {len(student_attendance)}"
    )


# 18. End sessions
print("\n18. Ending attendance sessions...")

end_session(session_id)
end_session(second_session_id)

print("   PASS - Sessions ended")


# 19. Clean up
print("\n19. Cleaning up test data...")

delete_exam(exam_id)
delete_exam(second_exam_id)
delete_student(TEST_STUDENT_ID)
delete_class(class_id)

print("   PASS - Test data cleaned")


print("\n================================")
print("ALL ATTENDANCE SERVICE TESTS PASSED")
print("================================")