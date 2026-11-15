import datetime
from backend.database.database import get_connection


def log_activity(activity_type: str, description: str, entity_type: str = None, entity_id: str = None):
    """
    Log an activity event into the database.
    """
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO activity_logs (activity_type, description, entity_type, entity_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (activity_type, description, entity_type, str(entity_id) if entity_id else None, datetime.datetime.now())
            )
            connection.commit()
    except Exception as e:
        print(f"Warning: Failed to log activity: {e}")


def get_recent_activities(limit: int = 10, page: int = 1):
    """
    Get recent activities ordered by newest first with pagination.
    """
    limit = max(1, min(limit, 100))
    offset = max(0, (page - 1) * limit)

    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) AS c FROM activity_logs").fetchone()["c"]
        rows = connection.execute(
            """
            SELECT id, activity_type, description, entity_type, entity_id, created_at
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ).fetchall()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "activities": [dict(r) for r in rows],
    }
