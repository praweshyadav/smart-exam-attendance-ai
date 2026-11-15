from fastapi import APIRouter, Depends, Query, HTTPException

from backend.api.dependencies import require_admin
from backend.services.dashboard_service import (
    get_dashboard_summary,
    get_attendance_trend,
    get_today_attendance,
    get_calendar_month,
    global_search,
)
from backend.services.activity_service import get_recent_activities
from backend.services.notification_service import (
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_admin)],
)


@router.get("/summary")
def read_dashboard_summary():
    """
    Returns actual counts and calculated attendance rate for StatCards.
    """
    return get_dashboard_summary()


@router.get("/attendance-trend")
def read_attendance_trend(days: int = Query(default=7, ge=7, le=60)):
    """
    Returns daily attendance trend excluding weekends and holidays.
    """
    return get_attendance_trend(days=days)


@router.get("/today-attendance")
def read_today_attendance():
    """
    Returns attendance metrics for today, or weekend/holiday indicator.
    """
    return get_today_attendance()


@router.get("/calendar")
def read_calendar(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
):
    """
    Returns days for monthly interactive calendar with attendance & holiday markers.
    """
    return get_calendar_month(year=year, month=month)


@router.get("/recent-activity")
def read_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    page: int = Query(default=1, ge=1),
):
    """
    Returns real database activity log.
    """
    return get_recent_activities(limit=limit, page=page)


@router.get("/notifications")
def read_notifications(limit: int = Query(default=20, ge=1, le=50)):
    """
    Returns real database notifications with unread count.
    """
    return get_notifications(limit=limit)


@router.put("/notifications/{notification_id}/read")
def update_notification_read(notification_id: int):
    """
    Marks a single notification as read.
    """
    mark_notification_read(notification_id)
    return {"status": "success", "message": "Notification marked as read."}


@router.put("/notifications/mark-all-read")
def update_all_notifications_read():
    """
    Marks all notifications as read.
    """
    mark_all_notifications_read()
    return {"status": "success", "message": "All notifications marked as read."}


@router.get("/search")
def search_records(q: str = Query(default="", min_length=1)):
    """
    Unified global search across Students, Classes, and Exams.
    """
    return global_search(query=q)


@router.get("/admin-profile")
def read_admin_profile(current_admin: dict = Depends(require_admin)):
    """
    Returns current authenticated admin profile.
    """
    return {
        "status": "success",
        "admin": {
            "name": current_admin.get("full_name") or current_admin.get("username"),
            "username": current_admin.get("username"),
            "role": "System Administrator" if current_admin.get("is_system_admin") else "Administrator",
            "is_system_admin": bool(current_admin.get("is_system_admin")),
            "email": f"{current_admin.get('username')}@smartattendance.edu",
            "department": "Academic Affairs",
            "avatar": None,
        }
    }
