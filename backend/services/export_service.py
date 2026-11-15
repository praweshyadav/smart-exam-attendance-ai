from pathlib import Path
import csv

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from backend.core.config import EXPORT_DIR
from backend.services.report_service import (
    get_student_report,
    get_class_report,
    get_exam_report,
    get_daily_report,
)


# ============================================================
# COMMON HELPERS
# ============================================================

def _ensure_export_directory():
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)


def _auto_adjust_columns(worksheet):
    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)

        for cell in column_cells:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))

        worksheet.column_dimensions[column_letter].width = min(
            max_length + 2,
            40,
        )


def _style_title(cell):
    cell.font = Font(bold=True, size=14)


def _style_heading(cell):
    cell.font = Font(bold=True, size=11)


# ============================================================
# CSV EXPORTS
# ============================================================

def export_student_report_csv(student_id):
    report = get_student_report(student_id)

    if report is None:
        raise ValueError("Student does not exist.")

    _ensure_export_directory()

    student = report["student"]
    summary = report["attendance_summary"]
    exams = report["exams"]

    file_path = Path(EXPORT_DIR) / f"student_{student_id}_attendance.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Student Attendance Report"])
        writer.writerow([])

        writer.writerow(["Student ID", student["student_id"]])
        writer.writerow(["Student Name", student["student_name"]])
        writer.writerow(["Class ID", student["class_id"]])
        writer.writerow(["Face Registered", student["face_registered"]])

        writer.writerow([])

        writer.writerow(["Attendance Summary"])
        writer.writerow(["Total Exams", summary["total_records"]])
        writer.writerow(["Present", summary["present_count"]])
        writer.writerow(["Late", summary["late_count"]])
        writer.writerow(["Absent", summary["absent_count"]])
        writer.writerow(
            ["Attendance Percentage", summary["attendance_percentage"]]
        )

        writer.writerow([])

        writer.writerow(["Exams"])
        writer.writerow(
            ["Exam ID", "Exam Name", "Exam Date", "Start Time", "Class ID"]
        )

        for exam in exams:
            writer.writerow(
                [
                    exam["exam_id"],
                    exam["exam_name"],
                    exam["exam_date"],
                    exam["start_time"],
                    exam["class_id"],
                ]
            )

    return str(file_path)


def export_class_report_csv(class_id):
    report = get_class_report(class_id)

    if report is None:
        raise ValueError("Class does not exist.")

    _ensure_export_directory()

    class_data = report["class"]
    summary = report["attendance_summary"]
    students = report["students"]
    exams = report["exams"]

    file_path = Path(EXPORT_DIR) / f"class_{class_id}_attendance.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Class Attendance Report"])
        writer.writerow([])

        writer.writerow(["Class ID", class_data["class_id"]])
        writer.writerow(["Class Name", class_data["class_name"]])
        writer.writerow(["Department", class_data["department"]])
        writer.writerow(["Semester", class_data["semester"]])

        writer.writerow([])

        writer.writerow(["Attendance Summary"])
        writer.writerow(["Total Records", summary["total_records"]])
        writer.writerow(["Present", summary["present_count"]])
        writer.writerow(["Late", summary["late_count"]])
        writer.writerow(["Absent", summary["absent_count"]])
        writer.writerow(
            ["Attendance Percentage", summary["attendance_percentage"]]
        )

        writer.writerow([])

        writer.writerow(["Students"])
        writer.writerow(
            [
                "Student ID",
                "Student Name",
                "Face Registered",
                "Total",
                "Present",
                "Late",
                "Absent",
                "Attendance %",
            ]
        )

        for student in students:
            attendance = student["attendance"]

            writer.writerow(
                [
                    student["student_id"],
                    student["student_name"],
                    student["face_registered"],
                    attendance["total_records"],
                    attendance["present_count"],
                    attendance["late_count"],
                    attendance["absent_count"],
                    attendance["attendance_percentage"],
                ]
            )

        writer.writerow([])

        writer.writerow(["Exams"])
        writer.writerow(
            ["Exam ID", "Exam Name", "Exam Date", "Start Time"]
        )

        for exam in exams:
            writer.writerow(
                [
                    exam["exam_id"],
                    exam["exam_name"],
                    exam["exam_date"],
                    exam["start_time"],
                ]
            )

    return str(file_path)


def export_exam_report_csv(exam_id):
    report = get_exam_report(exam_id)

    if report is None:
        raise ValueError("Exam does not exist.")

    _ensure_export_directory()

    exam = report["exam"]
    summary = report["attendance_summary"]
    roster = report["roster"]
    attendance = report["attendance"]

    attendance_by_student = {
        record["student_id"]: record
        for record in attendance
    }

    file_path = Path(EXPORT_DIR) / f"exam_{exam_id}_attendance.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Exam Attendance Report"])
        writer.writerow([])

        writer.writerow(["Exam ID", exam["exam_id"]])
        writer.writerow(["Exam Name", exam["exam_name"]])
        writer.writerow(["Class ID", exam["class_id"]])
        writer.writerow(["Exam Date", exam["exam_date"]])
        writer.writerow(["Start Time", exam["start_time"]])

        writer.writerow([])

        writer.writerow(["Attendance Summary"])
        writer.writerow(["Expected Students", summary["total_records"]])
        writer.writerow(["Present", summary["present_count"]])
        writer.writerow(["Late", summary["late_count"]])
        writer.writerow(["Absent", summary["absent_count"]])
        writer.writerow(
            ["Attendance Percentage", summary["attendance_percentage"]]
        )

        writer.writerow([])

        writer.writerow(["Student Attendance"])
        writer.writerow(
            [
                "Student ID",
                "Student Name",
                "Status",
                "Attendance Date",
                "Attendance Time",
                "Verification Score",
            ]
        )

        for student in roster:
            student_id = student["student_id"]
            record = attendance_by_student.get(student_id)

            if record is None:
                writer.writerow(
                    [
                        student_id,
                        student["student_name"],
                        "Absent",
                        "",
                        "",
                        "",
                    ]
                )
            else:
                writer.writerow(
                    [
                        student_id,
                        student["student_name"],
                        record["status"],
                        record["attendance_date"],
                        record["attendance_time"],
                        record["verification_score"],
                    ]
                )

    return str(file_path)


def export_daily_report_csv(attendance_date):
    report = get_daily_report(attendance_date)

    _ensure_export_directory()

    file_path = (
        Path(EXPORT_DIR)
        / f"daily_attendance_{attendance_date}.csv"
    )

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Daily Attendance Report"])
        writer.writerow([])

        writer.writerow(["Attendance Date", attendance_date])

        summary = report["attendance_summary"]

        writer.writerow([])
        writer.writerow(["Attendance Summary"])
        writer.writerow(["Expected Records", summary["total_records"]])
        writer.writerow(["Present", summary["present_count"]])
        writer.writerow(["Late", summary["late_count"]])
        writer.writerow(["Absent", summary["absent_count"]])
        writer.writerow(
            ["Attendance Percentage", summary["attendance_percentage"]]
        )

        writer.writerow([])

        writer.writerow(["Exams"])
        writer.writerow(
            [
                "Exam ID",
                "Exam Name",
                "Class ID",
                "Exam Date",
                "Start Time",
                "Expected",
                "Present",
                "Late",
                "Absent",
                "Attendance %",
            ]
        )

        for exam_report in report["exams"]:
            exam = exam_report["exam"]
            exam_summary = exam_report["attendance_summary"]

            writer.writerow(
                [
                    exam["exam_id"],
                    exam["exam_name"],
                    exam["class_id"],
                    exam["exam_date"],
                    exam["start_time"],
                    exam_summary["total_records"],
                    exam_summary["present_count"],
                    exam_summary["late_count"],
                    exam_summary["absent_count"],
                    exam_summary["attendance_percentage"],
                ]
            )

    return str(file_path)


# ============================================================
# EXCEL EXPORTS
# ============================================================

def export_student_report_excel(student_id):
    report = get_student_report(student_id)

    if report is None:
        raise ValueError("Student does not exist.")

    _ensure_export_directory()

    student = report["student"]
    summary = report["attendance_summary"]
    exams = report["exams"]

    file_path = (
        Path(EXPORT_DIR)
        / f"student_{student_id}_attendance.xlsx"
    )

    workbook = Workbook()

    # -------------------------
    # Summary Sheet
    # -------------------------

    worksheet = workbook.active
    worksheet.title = "Summary"

    worksheet["A1"] = "Student Attendance Report"
    _style_title(worksheet["A1"])

    worksheet["A3"] = "Student ID"
    worksheet["B3"] = student["student_id"]

    worksheet["A4"] = "Student Name"
    worksheet["B4"] = student["student_name"]

    worksheet["A5"] = "Class ID"
    worksheet["B5"] = student["class_id"]

    worksheet["A6"] = "Face Registered"
    worksheet["B6"] = student["face_registered"]

    worksheet["A8"] = "Attendance Summary"
    _style_heading(worksheet["A8"])

    worksheet["A9"] = "Total Exams"
    worksheet["B9"] = summary["total_records"]

    worksheet["A10"] = "Present"
    worksheet["B10"] = summary["present_count"]

    worksheet["A11"] = "Late"
    worksheet["B11"] = summary["late_count"]

    worksheet["A12"] = "Absent"
    worksheet["B12"] = summary["absent_count"]

    worksheet["A13"] = "Attendance Percentage"
    worksheet["B13"] = summary["attendance_percentage"]

    # -------------------------
    # Exams Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Exams")

    worksheet.append(
        ["Exam ID", "Exam Name", "Exam Date", "Start Time", "Class ID"]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for exam in exams:
        worksheet.append(
            [
                exam["exam_id"],
                exam["exam_name"],
                exam["exam_date"],
                exam["start_time"],
                exam["class_id"],
            ]
        )

    _auto_adjust_columns(worksheet)

    _auto_adjust_columns(workbook["Summary"])

    workbook.save(file_path)

    return str(file_path)


def export_class_report_excel(class_id):
    report = get_class_report(class_id)

    if report is None:
        raise ValueError("Class does not exist.")

    _ensure_export_directory()

    class_data = report["class"]
    summary = report["attendance_summary"]
    students = report["students"]
    exams = report["exams"]

    file_path = (
        Path(EXPORT_DIR)
        / f"class_{class_id}_attendance.xlsx"
    )

    workbook = Workbook()

    # -------------------------
    # Summary Sheet
    # -------------------------

    worksheet = workbook.active
    worksheet.title = "Summary"

    worksheet["A1"] = "Class Attendance Report"
    _style_title(worksheet["A1"])

    worksheet["A3"] = "Class ID"
    worksheet["B3"] = class_data["class_id"]

    worksheet["A4"] = "Class Name"
    worksheet["B4"] = class_data["class_name"]

    worksheet["A5"] = "Department"
    worksheet["B5"] = class_data["department"]

    worksheet["A6"] = "Semester"
    worksheet["B6"] = class_data["semester"]

    worksheet["A8"] = "Attendance Summary"
    _style_heading(worksheet["A8"])

    worksheet["A9"] = "Total Records"
    worksheet["B9"] = summary["total_records"]

    worksheet["A10"] = "Present"
    worksheet["B10"] = summary["present_count"]

    worksheet["A11"] = "Late"
    worksheet["B11"] = summary["late_count"]

    worksheet["A12"] = "Absent"
    worksheet["B12"] = summary["absent_count"]

    worksheet["A13"] = "Attendance Percentage"
    worksheet["B13"] = summary["attendance_percentage"]

    # -------------------------
    # Students Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Students")

    worksheet.append(
        [
            "Student ID",
            "Student Name",
            "Face Registered",
            "Total",
            "Present",
            "Late",
            "Absent",
            "Attendance %",
        ]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for student in students:
        attendance = student["attendance"]

        worksheet.append(
            [
                student["student_id"],
                student["student_name"],
                student["face_registered"],
                attendance["total_records"],
                attendance["present_count"],
                attendance["late_count"],
                attendance["absent_count"],
                attendance["attendance_percentage"],
            ]
        )

    # -------------------------
    # Exams Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Exams")

    worksheet.append(
        ["Exam ID", "Exam Name", "Exam Date", "Start Time"]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for exam in exams:
        worksheet.append(
            [
                exam["exam_id"],
                exam["exam_name"],
                exam["exam_date"],
                exam["start_time"],
            ]
        )

    for worksheet in workbook.worksheets:
        _auto_adjust_columns(worksheet)

    workbook.save(file_path)

    return str(file_path)


def export_exam_report_excel(exam_id):
    report = get_exam_report(exam_id)

    if report is None:
        raise ValueError("Exam does not exist.")

    _ensure_export_directory()

    exam = report["exam"]
    summary = report["attendance_summary"]
    roster = report["roster"]
    attendance = report["attendance"]

    attendance_by_student = {
        record["student_id"]: record
        for record in attendance
    }

    file_path = (
        Path(EXPORT_DIR)
        / f"exam_{exam_id}_attendance.xlsx"
    )

    workbook = Workbook()

    # -------------------------
    # Summary Sheet
    # -------------------------

    worksheet = workbook.active
    worksheet.title = "Summary"

    worksheet["A1"] = "Exam Attendance Report"
    _style_title(worksheet["A1"])

    worksheet["A3"] = "Exam ID"
    worksheet["B3"] = exam["exam_id"]

    worksheet["A4"] = "Exam Name"
    worksheet["B4"] = exam["exam_name"]

    worksheet["A5"] = "Class ID"
    worksheet["B5"] = exam["class_id"]

    worksheet["A6"] = "Exam Date"
    worksheet["B6"] = exam["exam_date"]

    worksheet["A7"] = "Start Time"
    worksheet["B7"] = exam["start_time"]

    worksheet["A9"] = "Attendance Summary"
    _style_heading(worksheet["A9"])

    worksheet["A10"] = "Expected Students"
    worksheet["B10"] = summary["total_records"]

    worksheet["A11"] = "Present"
    worksheet["B11"] = summary["present_count"]

    worksheet["A12"] = "Late"
    worksheet["B12"] = summary["late_count"]

    worksheet["A13"] = "Absent"
    worksheet["B13"] = summary["absent_count"]

    worksheet["A14"] = "Attendance Percentage"
    worksheet["B14"] = summary["attendance_percentage"]

    # -------------------------
    # Student Attendance Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Student Attendance")

    worksheet.append(
        [
            "Student ID",
            "Student Name",
            "Status",
            "Attendance Date",
            "Attendance Time",
            "Verification Score",
        ]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for student in roster:
        student_id = student["student_id"]
        record = attendance_by_student.get(student_id)

        if record is None:
            worksheet.append(
                [
                    student_id,
                    student["student_name"],
                    "Absent",
                    "",
                    "",
                    "",
                ]
            )
        else:
            worksheet.append(
                [
                    student_id,
                    student["student_name"],
                    record["status"],
                    record["attendance_date"],
                    record["attendance_time"],
                    record["verification_score"],
                ]
            )

    # -------------------------
    # Roster Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Roster")

    worksheet.append(
        [
            "Student ID",
            "Student Name",
            "Class ID",
            "Face Registered",
        ]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for student in roster:
        worksheet.append(
            [
                student["student_id"],
                student["student_name"],
                student["class_id"],
                student["face_registered"],
            ]
        )

    for worksheet in workbook.worksheets:
        _auto_adjust_columns(worksheet)

    workbook.save(file_path)

    return str(file_path)


def export_daily_report_excel(attendance_date):
    report = get_daily_report(attendance_date)

    _ensure_export_directory()

    file_path = (
        Path(EXPORT_DIR)
        / f"daily_attendance_{attendance_date}.xlsx"
    )

    workbook = Workbook()

    # -------------------------
    # Summary Sheet
    # -------------------------

    worksheet = workbook.active
    worksheet.title = "Summary"

    worksheet["A1"] = "Daily Attendance Report"
    _style_title(worksheet["A1"])

    worksheet["A3"] = "Attendance Date"
    worksheet["B3"] = attendance_date

    summary = report["attendance_summary"]

    worksheet["A5"] = "Attendance Summary"
    _style_heading(worksheet["A5"])

    worksheet["A6"] = "Expected Records"
    worksheet["B6"] = summary["total_records"]

    worksheet["A7"] = "Present"
    worksheet["B7"] = summary["present_count"]

    worksheet["A8"] = "Late"
    worksheet["B8"] = summary["late_count"]

    worksheet["A9"] = "Absent"
    worksheet["B9"] = summary["absent_count"]

    worksheet["A10"] = "Attendance Percentage"
    worksheet["B10"] = summary["attendance_percentage"]

    # -------------------------
    # Exams Sheet
    # -------------------------

    worksheet = workbook.create_sheet("Exams")

    worksheet.append(
        [
            "Exam ID",
            "Exam Name",
            "Class ID",
            "Exam Date",
            "Start Time",
            "Expected",
            "Present",
            "Late",
            "Absent",
            "Attendance %",
        ]
    )

    for cell in worksheet[1]:
        _style_heading(cell)

    for exam_report in report["exams"]:
        exam = exam_report["exam"]
        exam_summary = exam_report["attendance_summary"]

        worksheet.append(
            [
                exam["exam_id"],
                exam["exam_name"],
                exam["class_id"],
                exam["exam_date"],
                exam["start_time"],
                exam_summary["total_records"],
                exam_summary["present_count"],
                exam_summary["late_count"],
                exam_summary["absent_count"],
                exam_summary["attendance_percentage"],
            ]
        )

    for worksheet in workbook.worksheets:
        _auto_adjust_columns(worksheet)

    workbook.save(file_path)

    return str(file_path)

def export_exam_report_pdf(exam_id):
    report = get_exam_report(exam_id)

    if report is None:
        raise ValueError("Exam does not exist.")

    _ensure_export_directory()

    exam = report["exam"]
    summary = report["attendance_summary"]
    roster = report["roster"]
    attendance = report["attendance"]

    attendance_by_student = {
        record["student_id"]: record
        for record in attendance
    }

    file_path = (
        Path(EXPORT_DIR)
        / f"exam_{exam_id}_attendance.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "Exam Attendance Report",
            styles["Title"],
        )
    )

    story.append(Spacer(1, 8))

    # ========================================================
    # EXAM DETAILS
    # ========================================================

    exam_details = [
        ["Exam ID", exam["exam_id"]],
        ["Exam Name", exam["exam_name"]],
        ["Class ID", exam["class_id"]],
        ["Exam Date", exam["exam_date"]],
        ["Start Time", exam["start_time"]],
    ]

    details_table = Table(
        exam_details,
        colWidths=[45 * mm, 120 * mm],
    )

    details_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(details_table)
    story.append(Spacer(1, 12))

    # ========================================================
    # ATTENDANCE SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "Attendance Summary",
            styles["Heading2"],
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Expected Students", summary["total_records"]],
        ["Present", summary["present_count"]],
        ["Late", summary["late_count"]],
        ["Absent", summary["absent_count"]],
        [
            "Attendance Percentage",
            f'{summary["attendance_percentage"]}%',
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[80 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    # ========================================================
    # STUDENT ATTENDANCE
    # ========================================================

    story.append(
        Paragraph(
            "Student Attendance",
            styles["Heading2"],
        )
    )

    attendance_data = [
        [
            "Student ID",
            "Student Name",
            "Status",
            "Date",
            "Time",
            "Score",
        ]
    ]

    for student in roster:
        student_id = student["student_id"]
        record = attendance_by_student.get(student_id)

        if record is None:
            attendance_data.append(
                [
                    student_id,
                    student["student_name"],
                    "Absent",
                    "",
                    "",
                    "",
                ]
            )
        else:
            attendance_data.append(
                [
                    student_id,
                    student["student_name"],
                    record["status"],
                    record["attendance_date"],
                    record["attendance_time"],
                    (
                        f'{record["verification_score"]:.4f}'
                        if record["verification_score"] is not None
                        else ""
                    ),
                ]
            )

    attendance_table = Table(
        attendance_data,
        repeatRows=1,
        colWidths=[
            35 * mm,
            38 * mm,
            22 * mm,
            28 * mm,
            25 * mm,
            20 * mm,
        ],
    )

    attendance_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("ALIGN", (5, 1), (5, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(attendance_table)

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(story)

    return str(file_path)


def export_student_report_pdf(student_id):
    report = get_student_report(student_id)

    if report is None:
        raise ValueError("Student does not exist.")

    _ensure_export_directory()

    student = report["student"]
    summary = report["attendance_summary"]
    exams = report["exams"]

    file_path = (
        Path(EXPORT_DIR)
        / f"student_{student_id}_attendance.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(
            "Student Attendance Report",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 10))

    student_details = [
        ["Student ID", student["student_id"]],
        ["Student Name", student["student_name"]],
        ["Class ID", student["class_id"]],
        ["Face Registered", student["face_registered"]],
    ]

    details_table = Table(
        student_details,
        colWidths=[50 * mm, 115 * mm],
    )

    details_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(details_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Attendance Summary",
            styles["Heading2"],
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Exams", summary["total_records"]],
        ["Present", summary["present_count"]],
        ["Late", summary["late_count"]],
        ["Absent", summary["absent_count"]],
        [
            "Attendance Percentage",
            f'{summary["attendance_percentage"]}%',
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[80 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Exams",
            styles["Heading2"],
        )
    )

    exam_data = [
        [
            "Exam ID",
            "Exam Name",
            "Date",
            "Time",
            "Class",
        ]
    ]

    for exam in exams:
        exam_data.append(
            [
                exam["exam_id"],
                exam["exam_name"],
                exam["exam_date"],
                exam["start_time"],
                exam["class_id"],
            ]
        )

    exam_table = Table(
        exam_data,
        repeatRows=1,
        colWidths=[
            18 * mm,
            55 * mm,
            28 * mm,
            25 * mm,
            20 * mm,
        ],
    )

    exam_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(exam_table)

    document.build(story)

    return str(file_path)



def export_class_report_pdf(class_id):
    report = get_class_report(class_id)

    if report is None:
        raise ValueError("Class does not exist.")

    _ensure_export_directory()

    class_data = report["class"]
    summary = report["attendance_summary"]
    students = report["students"]

    file_path = (
        Path(EXPORT_DIR)
        / f"class_{class_id}_attendance.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(
            "Class Attendance Report",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 10))

    class_details = [
        ["Class ID", class_data["class_id"]],
        ["Class Name", class_data["class_name"]],
        ["Department", class_data["department"]],
        ["Semester", class_data["semester"]],
    ]

    details_table = Table(
        class_details,
        colWidths=[45 * mm, 120 * mm],
    )

    details_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(details_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Attendance Summary",
            styles["Heading2"],
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Records", summary["total_records"]],
        ["Present", summary["present_count"]],
        ["Late", summary["late_count"]],
        ["Absent", summary["absent_count"]],
        [
            "Attendance Percentage",
            f'{summary["attendance_percentage"]}%',
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[80 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Students",
            styles["Heading2"],
        )
    )

    student_data = [
        [
            "Student ID",
            "Student Name",
            "Present",
            "Late",
            "Absent",
            "Attendance %",
        ]
    ]

    for student in students:
        attendance = student["attendance"]

        student_data.append(
            [
                student["student_id"],
                student["student_name"],
                attendance["present_count"],
                attendance["late_count"],
                attendance["absent_count"],
                f'{attendance["attendance_percentage"]}%',
            ]
        )

    student_table = Table(
        student_data,
        repeatRows=1,
        colWidths=[
            38 * mm,
            48 * mm,
            20 * mm,
            18 * mm,
            20 * mm,
            25 * mm,
        ],
    )

    student_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(student_table)

    document.build(story)

    return str(file_path)



def export_daily_report_pdf(attendance_date):
    report = get_daily_report(attendance_date)

    _ensure_export_directory()

    summary = report["attendance_summary"]

    file_path = (
        Path(EXPORT_DIR)
        / f"daily_attendance_{attendance_date}.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(
            "Daily Attendance Report",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"Attendance Date: {attendance_date}",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 8))

    summary_data = [
        ["Metric", "Value"],
        ["Expected Records", summary["total_records"]],
        ["Present", summary["present_count"]],
        ["Late", summary["late_count"]],
        ["Absent", summary["absent_count"]],
        [
            "Attendance Percentage",
            f'{summary["attendance_percentage"]}%',
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[80 * mm, 60 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Exams",
            styles["Heading2"],
        )
    )

    exam_data = [
        [
            "Exam ID",
            "Exam Name",
            "Class",
            "Expected",
            "Present",
            "Late",
            "Absent",
            "Attendance %",
        ]
    ]

    for exam_report in report["exams"]:
        exam = exam_report["exam"]
        exam_summary = exam_report["attendance_summary"]

        exam_data.append(
            [
                exam["exam_id"],
                exam["exam_name"],
                exam["class_id"],
                exam_summary["total_records"],
                exam_summary["present_count"],
                exam_summary["late_count"],
                exam_summary["absent_count"],
                f'{exam_summary["attendance_percentage"]}%',
            ]
        )

    exam_table = Table(
        exam_data,
        repeatRows=1,
        colWidths=[
            15 * mm,
            48 * mm,
            18 * mm,
            18 * mm,
            18 * mm,
            15 * mm,
            15 * mm,
            25 * mm,
        ],
    )

    exam_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    story.append(exam_table)

    document.build(story)

    return str(file_path)