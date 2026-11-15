import datetime
import os
import threading
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

# ==========================================
# MYSQL DATABASE CONFIGURATION
# ==========================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Gautam@12"),
    "database": os.getenv("DB_NAME", "7th"),
}


# ==========================================
# NORMALIZATION HELPERS
# ==========================================

def _normalize_value(val):
    if isinstance(val, datetime.timedelta):
        total_sec = int(val.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        if s == 0:
            return f"{h:02d}:{m:02d}"
        return f"{h:02d}:{m:02d}:{s:02d}"
    if isinstance(val, datetime.time):
        if val.second == 0:
            return val.strftime("%H:%M")
        return val.strftime("%H:%M:%S")
    if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return val


def _normalize_row(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return {k: _normalize_value(v) for k, v in row.items()}
    return row


class MySQLCursorWrapper:
    """
    Wraps mysql.connector cursor to automatically normalize
    date, time, and timedelta objects into clean string representations.
    """

    def __init__(self, raw_cursor):
        self._raw_cursor = raw_cursor

    def fetchone(self):
        row = self._raw_cursor.fetchone()
        return _normalize_row(row)

    def fetchall(self):
        rows = self._raw_cursor.fetchall()
        return [_normalize_row(r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._raw_cursor.fetchmany(size) if size else self._raw_cursor.fetchmany()
        return [_normalize_row(r) for r in rows]

    @property
    def lastrowid(self):
        return self._raw_cursor.lastrowid

    @property
    def rowcount(self):
        return self._raw_cursor.rowcount

    def close(self):
        try:
            self._raw_cursor.close()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._raw_cursor, name)


# ==========================================
# CONNECTION WRAPPER FOR MYSQL
# ==========================================

class MySQLConnectionWrapper:
    """
    Wraps mysql.connector connection to provide:
    - Context manager with auto commit/rollback and cleanup
    - connection.execute(query, params) returning wrapped buffered dict cursor
    - Automatic translation of '?' to '%s' parameter placeholders
    """

    def __init__(self, raw_conn):
        self._conn = raw_conn
        self._cursors = []

    def execute(self, query, params=None):
        if "?" in query:
            query = query.replace("?", "%s")

        raw_cursor = self._conn.cursor(dictionary=True, buffered=True)
        self._cursors.append(raw_cursor)

        if params is not None:
            if isinstance(params, list):
                params = tuple(params)
            raw_cursor.execute(query, params)
        else:
            raw_cursor.execute(query)

        return MySQLCursorWrapper(raw_cursor)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def cursor(self, *args, **kwargs):
        if "dictionary" not in kwargs:
            kwargs["dictionary"] = True
        if "buffered" not in kwargs:
            kwargs["buffered"] = True
        c = self._conn.cursor(*args, **kwargs)
        self._cursors.append(c)
        return MySQLCursorWrapper(c)

    def close(self):
        for c in self._cursors:
            try:
                c.close()
            except Exception:
                pass
        self._cursors.clear()
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:
                pass
        else:
            try:
                self.commit()
            except Exception:
                pass
        self.close()


# ==========================================
# DATABASE CONNECTION POOL
# ==========================================

_pool_lock = threading.Lock()
_pool = None


def get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                pool_config = DB_CONFIG.copy()
                pool_config["pool_name"] = "smart_exam_pool"
                pool_config["pool_size"] = int(os.getenv("DB_POOL_SIZE", "15"))
                pool_config["pool_reset_session"] = True
                _pool = MySQLConnectionPool(**pool_config)
    return _pool


def get_connection():
    """
    Retrieve and return a wrapped MySQL database connection from the connection pool.
    Falls back gracefully to a direct connection if the pool is exhausted.
    """
    try:
        raw_conn = get_pool().get_connection()
    except Exception:
        raw_conn = mysql.connector.connect(**DB_CONFIG)
    return MySQLConnectionWrapper(raw_conn)


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def initialize_database():
    """
    Ensure MySQL database exists and create all required tables.
    """
    db_name = DB_CONFIG.get("database", "7th")

    # Step 1: Ensure database exists
    server_config = DB_CONFIG.copy()
    server_config.pop("database", None)
    admin_conn = mysql.connector.connect(**server_config)
    admin_cur = admin_conn.cursor()
    admin_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    admin_cur.close()
    admin_conn.close()

    # Step 2: Create all required tables
    with get_connection() as connection:
        # 1. Classes Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                class_id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(255) NOT NULL UNIQUE,
                department VARCHAR(255),
                semester INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 2. Students Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(100) PRIMARY KEY,
                student_name VARCHAR(255) NOT NULL,
                class_id INT,
                face_registered TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                face_image LONGTEXT,
                face_embedding MEDIUMBLOB,
                FOREIGN KEY (class_id)
                    REFERENCES classes(class_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # 3. Exams Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                exam_id INT AUTO_INCREMENT PRIMARY KEY,
                exam_name VARCHAR(255) NOT NULL,
                class_id INT,
                exam_date DATE NOT NULL,
                start_time TIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id)
                    REFERENCES classes(class_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # 4. Exam Roster Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS exam_roster (
                roster_id INT AUTO_INCREMENT PRIMARY KEY,
                exam_id INT NOT NULL,
                student_id VARCHAR(100) NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_exam_student (exam_id, student_id),
                FOREIGN KEY (exam_id)
                    REFERENCES exams(exam_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # 5. Attendance Sessions Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                session_id INT AUTO_INCREMENT PRIMARY KEY,
                exam_id INT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                FOREIGN KEY (exam_id)
                    REFERENCES exams(exam_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # 6. Attendance Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT,
                student_id VARCHAR(100) NOT NULL,
                student_name VARCHAR(255) NOT NULL,
                attendance_date DATE NOT NULL,
                attendance_time TIME NOT NULL,
                status VARCHAR(50) NOT NULL,
                verification_score DOUBLE,
                face_image LONGTEXT,
                UNIQUE KEY unique_student_date (student_id, attendance_date),
                FOREIGN KEY (session_id)
                    REFERENCES attendance_sessions(session_id)
                    ON DELETE SET NULL,
                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # 7. Verification Attempts Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS verification_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result VARCHAR(100) NOT NULL,
                similarity DOUBLE,
                liveness_result VARCHAR(100),
                reason TEXT,
                face_image LONGTEXT,
                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # 8. Holidays Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id INT AUTO_INCREMENT PRIMARY KEY,
                holiday_date DATE NOT NULL UNIQUE,
                holiday_name VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 9. Activity Logs Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity_type VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                entity_type VARCHAR(50),
                entity_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 10. Notifications Table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'info',
                is_read TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 11. Users Table (Authentication & Authorization)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                full_name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                is_system_admin TINYINT NOT NULL DEFAULT 0,
                student_id VARCHAR(100) NULL UNIQUE,
                created_by VARCHAR(100) NULL,
                is_active TINYINT NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # 12. Revoked JWT Tokens Table (Logout invalidation)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti VARCHAR(64) PRIMARY KEY,
                expires_at DATETIME NOT NULL
            ) ENGINE=InnoDB
        """)

        # Ensure created_by column exists on attendance_sessions for session ownership checks
        try:
            col_row = connection.execute(
                """
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'attendance_sessions' AND COLUMN_NAME = 'created_by'
                """
            ).fetchone()
            if not col_row:
                connection.execute("ALTER TABLE attendance_sessions ADD COLUMN created_by VARCHAR(100) NULL")
        except Exception:
            pass

        # Performance Indexes
        def _ensure_index(table, idx_name, cols):
            try:
                row = connection.execute(
                    """
                    SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND INDEX_NAME = ?
                    """,
                    (table, idx_name)
                ).fetchone()
                if not row:
                    connection.execute(f"CREATE INDEX {idx_name} ON {table} ({cols})")
            except Exception:
                pass

        _ensure_index("attendance", "idx_att_date", "attendance_date")
        _ensure_index("attendance", "idx_att_sess_date", "session_id, attendance_date")
        _ensure_index("attendance", "idx_att_stu_date", "student_id, attendance_date")
        _ensure_index("attendance", "idx_att_sess_stu", "session_id, student_id")
        _ensure_index("verification_attempts", "idx_ver_attempts_ts", "timestamp")
        _ensure_index("verification_attempts", "idx_ver_attempts_stu_ts", "student_id, timestamp")
        _ensure_index("students", "idx_students_face_reg", "face_registered")
        _ensure_index("students", "idx_students_class_id", "class_id")
        _ensure_index("attendance_sessions", "idx_att_sess_ended", "ended_at")
        _ensure_index("attendance_sessions", "idx_sess_created_by", "created_by")
        _ensure_index("classes", "idx_classes_dept_sem", "department, semester")
        _ensure_index("holidays", "idx_holidays_date", "holiday_date")
        _ensure_index("activity_logs", "idx_act_logs_created", "created_at")
        _ensure_index("notifications", "idx_notif_read_created", "is_read, created_at")
        _ensure_index("users", "idx_users_role", "role")
        _ensure_index("users", "idx_users_uname_role", "username, role")
        _ensure_index("revoked_tokens", "idx_revoked_exp", "expires_at")

        # Seed default System Admin if none exists
        try:
            sys_admin = connection.execute(
                "SELECT id FROM users WHERE is_system_admin = 1 LIMIT 1"
            ).fetchone()
            if not sys_admin:
                from backend.core.config import (
                    SYSTEM_ADMIN_FULL_NAME,
                    SYSTEM_ADMIN_PASSWORD,
                    SYSTEM_ADMIN_USERNAME,
                )
                from backend.services.auth_service import hash_password

                existing_uname = connection.execute(
                    "SELECT id FROM users WHERE username = ? LIMIT 1",
                    (SYSTEM_ADMIN_USERNAME,),
                ).fetchone()
                if existing_uname:
                    connection.execute(
                        "UPDATE users SET role = 'admin', is_system_admin = 1 WHERE id = ?",
                        (existing_uname["id"],),
                    )
                else:
                    pw_hash = hash_password(SYSTEM_ADMIN_PASSWORD)
                    connection.execute(
                        """
                        INSERT INTO users (username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active)
                        VALUES (?, ?, ?, 'admin', 1, NULL, 'system', 1)
                        """,
                        (SYSTEM_ADMIN_USERNAME, SYSTEM_ADMIN_FULL_NAME, pw_hash),
                    )
        except Exception as seed_err:
            print(f"Warning: System admin seeding error: {seed_err}")

        # Step 3: Seed standard holidays if empty
        holiday_count = connection.execute("SELECT COUNT(*) AS c FROM holidays").fetchone()["c"]
        if holiday_count == 0:
            standard_holidays = [
                ("2026-01-01", "New Year's Day", "University New Year Holiday"),
                ("2026-01-26", "Republic Day", "National Holiday"),
                ("2026-03-04", "Holi", "Festival Holiday"),
                ("2026-08-15", "Independence Day", "National Holiday"),
                ("2026-10-02", "Gandhi Jayanti", "National Holiday"),
                ("2026-10-20", "Dussehra", "Festival Holiday"),
                ("2026-11-08", "Diwali", "Festival Holiday"),
                ("2026-12-25", "Christmas Day", "Winter Holiday"),
            ]
            for h_date, h_name, h_desc in standard_holidays:
                try:
                    connection.execute(
                        "INSERT IGNORE INTO holidays (holiday_date, holiday_name, description) VALUES (?, ?, ?)",
                        (h_date, h_name, h_desc)
                    )
                except Exception:
                    pass

        # Step 4: Backfill initial activity logs and notifications from existing data if empty
        act_count = connection.execute("SELECT COUNT(*) AS c FROM activity_logs").fetchone()["c"]
        if act_count == 0:
            # Backfill from students
            students = connection.execute("SELECT student_id, student_name, created_at FROM students ORDER BY created_at ASC").fetchall()
            for s in students:
                connection.execute(
                    "INSERT INTO activity_logs (activity_type, description, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("STUDENT_REGISTERED", f"Student registered: {s['student_name']} ({s['student_id']})", "student", s["student_id"], s.get("created_at") or datetime.datetime.now())
                )
            # Backfill from classes
            classes = connection.execute("SELECT class_id, class_name, department, created_at FROM classes ORDER BY created_at ASC").fetchall()
            for c in classes:
                connection.execute(
                    "INSERT INTO activity_logs (activity_type, description, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("CLASS_CREATED", f"Class added: {c['class_name']} ({c['department'] or 'General'})", "class", str(c["class_id"]), c.get("created_at") or datetime.datetime.now())
                )
            # Backfill from exams
            exams = connection.execute("SELECT exam_id, exam_name, created_at FROM exams ORDER BY created_at ASC").fetchall()
            for e in exams:
                connection.execute(
                    "INSERT INTO activity_logs (activity_type, description, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("EXAM_CREATED", f"Session/Exam created: {e['exam_name']}", "exam", str(e["exam_id"]), e.get("created_at") or datetime.datetime.now())
                )
            # Backfill recent attendance (latest 10)
            attendances = connection.execute("SELECT student_id, student_name, attendance_date, attendance_time FROM attendance ORDER BY attendance_date DESC, attendance_time DESC LIMIT 10").fetchall()
            for a in reversed(attendances):
                connection.execute(
                    "INSERT INTO activity_logs (activity_type, description, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    ("ATTENDANCE_MARKED", f"Attendance verified for {a['student_name']} ({a['student_id']})", "attendance", a["student_id"], f"{a['attendance_date']} {a['attendance_time']}")
                )

        notif_count = connection.execute("SELECT COUNT(*) AS c FROM notifications").fetchone()["c"]
        if notif_count == 0:
            initial_notifications = [
                ("System Ready", "Smart Exam Attendance v2 system initialized successfully with high-performance face recognition.", "success", 0),
                ("Attendance Logged", "Real-time attendance session recorded 6 present students for today's session.", "info", 0),
                ("Weekend Policy Active", "Weekend attendance lock is active. Saturdays and Sundays are designated academic holidays.", "warning", 0),
            ]
            for title, msg, n_type, is_read in initial_notifications:
                connection.execute(
                    "INSERT INTO notifications (title, message, type, is_read) VALUES (?, ?, ?, ?)",
                    (title, msg, n_type, is_read)
                )

    print("===================================")
    print("MySQL Database Initialized Successfully!")
    print(f"Database: {db_name}")
    print("Tables Created: 10")
    print("===================================")


if __name__ == "__main__":
    initialize_database()
