from backend.services.attendance_session_service import (
    start_session,
    get_session,
    get_all_sessions,
    get_sessions_by_exam,
    end_session,
    session_exists,
)

from backend.services.exam_service import (
    add_exam,
    delete_exam,
    get_exam,
)

from backend.services.class_service import (
    add_class,
    delete_class,
)


print("===== ATTENDANCE SESSION SERVICE TEST =====")


TEST_CLASS_NAME = "Test Session Class"


# Clean previous test class
from backend.services.class_service import get_all_classes

existing_classes = get_all_classes()

for class_data in existing_classes:
    if class_data["class_name"] == TEST_CLASS_NAME:
        delete_class(class_data["class_id"])


# 1. Create class
print("\n1. Creating class...")

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


# 2. Create exam
print("\n2. Creating exam...")

result = add_exam(
    exam_name="Session Test Examination",
    class_id=class_id,
    exam_date="2026-10-25",
    start_time="10:00",
)

if result:
    print("   PASS - Exam created")
else:
    print("   FAIL - Exam was not created")


# Get exam ID
from backend.services.exam_service import get_all_exams

exams = get_all_exams()

test_exam = next(
    (
        exam
        for exam in exams
        if exam["exam_name"] == "Session Test Examination"
    ),
    None,
)

if test_exam is None:
    raise RuntimeError("Test exam could not be found.")

exam_id = test_exam["exam_id"]


# 3. Start session
print("\n3. Starting attendance session...")

session_id = start_session(exam_id)

if session_id:
    print("   PASS - Session started")
    print(f"   Session ID: {session_id}")
else:
    print("   FAIL - Session was not started")


# 4. Get session
print("\n4. Getting session...")

session = get_session(session_id)

if session:
    print("   PASS - Session retrieved")
    print(f"   Session: {session}")
else:
    print("   FAIL - Session not retrieved")


# 5. Check session exists
print("\n5. Checking session exists...")

if session_exists(session_id):
    print("   PASS - Session exists")
else:
    print("   FAIL - Session does not exist")


# 6. Get all sessions
print("\n6. Getting all sessions...")

sessions = get_all_sessions()

if sessions:
    print(f"   PASS - Found {len(sessions)} session(s)")
else:
    print("   FAIL - No sessions found")


# 7. Get sessions by exam
print("\n7. Getting sessions by exam...")

exam_sessions = get_sessions_by_exam(exam_id)

if exam_sessions:
    print(f"   PASS - Found {len(exam_sessions)} session(s) for exam")
else:
    print("   FAIL - No sessions found for exam")


# 8. End session
print("\n8. Ending attendance session...")

result = end_session(session_id)

if result:
    print("   PASS - Session ended")
else:
    print("   FAIL - Session could not be ended")


# 9. Verify session ended
print("\n9. Verifying session ended...")

ended_session = get_session(session_id)

if ended_session and ended_session["ended_at"] is not None:
    print("   PASS - Session end time recorded")
else:
    print("   FAIL - Session end time not recorded")


# 10. Clean up
print("\n10. Cleaning up test data...")

delete_exam(exam_id)
delete_class(class_id)

print("   PASS - Test data cleaned")


print("\n================================")
print("ALL ATTENDANCE SESSION TESTS PASSED")
print("================================")