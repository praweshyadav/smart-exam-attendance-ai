import datetime
from backend.database.database import get_connection


def create_notification(title: str, message: str, notif_type: str = "info"):
    """
    Create a notification in the database.
    """
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO notifications (title, message, type, is_read, created_at)
                VALUES (?, ?, ?, 0, ?)
                """,
                (title, message, notif_type, datetime.datetime.now())
            )
            connection.commit()
    except Exception as e:
        print(f"Warning: Failed to create notification: {e}")


def get_notifications(limit: int = 20):
    with get_connection() as connection:
        unread_count = connection.execute(
            "SELECT COUNT(*) AS c FROM notifications WHERE is_read = 0"
        ).fetchone()["c"]

        rows = connection.execute(
            """
            SELECT id, title, message, type, is_read, created_at
            FROM notifications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return {
        "unread_count": unread_count,
        "notifications": [dict(r) for r in rows],
    }


def mark_notification_read(notif_id: int):
    with get_connection() as connection:
        connection.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notif_id,)
        )
        connection.commit()
    return True


def mark_all_notifications_read():
    with get_connection() as connection:
        connection.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
        connection.commit()
    return True
