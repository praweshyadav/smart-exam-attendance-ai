from backend.services.verification_session_service import (
    VerificationSessionService,
)


def test_create_session():
    service = VerificationSessionService()

    session_id = service.create_session()

    assert session_id is not None
    assert service.session_exists(session_id)
    assert service.get_session_count() == 1

    service.close_all_sessions()

    print("PASS: create_session")


def test_multiple_sessions_are_independent():
    service = VerificationSessionService()

    session_a = service.create_session()
    session_b = service.create_session()

    assert session_a != session_b

    assert service.session_exists(session_a)
    assert service.session_exists(session_b)

    assert service.get_session_count() == 2

    service.close_all_sessions()

    assert service.get_session_count() == 0

    print("PASS: multiple_sessions_are_independent")


def test_process_invalid_session():
    service = VerificationSessionService()

    try:
        service.process_frame(
            "invalid-session",
            None,
        )

        assert False

    except ValueError as error:
        assert str(error) == (
            "Verification session does not exist."
        )

    service.close_all_sessions()

    print("PASS: process_invalid_session")


def test_reset_invalid_session():
    service = VerificationSessionService()

    try:
        service.reset_session(
            "invalid-session"
        )

        assert False

    except ValueError as error:
        assert str(error) == (
            "Verification session does not exist."
        )

    service.close_all_sessions()

    print("PASS: reset_invalid_session")


def test_close_session():
    service = VerificationSessionService()

    session_id = service.create_session()

    assert service.session_exists(session_id)

    closed = service.close_session(
        session_id
    )

    assert closed is True
    assert not service.session_exists(session_id)
    assert service.get_session_count() == 0

    print("PASS: close_session")


def test_close_nonexistent_session():
    service = VerificationSessionService()

    closed = service.close_session(
        "invalid-session"
    )

    assert closed is False
    assert service.get_session_count() == 0

    print("PASS: close_nonexistent_session")


def test_close_all_sessions():
    service = VerificationSessionService()

    service.create_session()
    service.create_session()
    service.create_session()

    assert service.get_session_count() == 3

    service.close_all_sessions()

    assert service.get_session_count() == 0

    print("PASS: close_all_sessions")


if __name__ == "__main__":
    test_create_session()
    test_multiple_sessions_are_independent()
    test_process_invalid_session()
    test_reset_invalid_session()
    test_close_session()
    test_close_nonexistent_session()
    test_close_all_sessions()

    print()
    print("ALL TESTS PASSED")