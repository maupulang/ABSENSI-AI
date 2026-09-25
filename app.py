import os
import io
import csv
import json
import logging
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import requests

from firebase_config import get_db, get_web_firebase_config, FIREBASE_DATABASE_URL
from attendance_service import attendance_service
from face_recognition_service import face_service

load_dotenv()

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "absensi_ai_super_secret_key_2026_change_in_production")

# Global template helper
@app.context_processor
def inject_globals():
    return {
        "current_user": session,
        "firebase_config": get_web_firebase_config(),
        "today_str": attendance_service.get_today_string(),
        "app_name": "ABSENSI AI"
    }


# ==========================================
# AUTH DECORATORS
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash("Akses ditolak! Halaman ini hanya untuk Administrator.", "danger")
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def sanitize_student(sdata: dict) -> dict:
    """Never expose face embedding vector to frontend/users."""
    if not isinstance(sdata, dict):
        return {}
    clean = dict(sdata)
    clean.pop('faceEmbedding', None)
    clean.pop('password_hash', None)
    return clean


# ==========================================
# PUBLIC & AUTH ROUTES
# ==========================================
@app.route('/')
def index():
    if 'uid' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and 'uid' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email dan kata sandi wajib diisi.", "danger")
            return render_template('login.html')

        db = get_db()
        students = db.get("students") or {}

        # Search for user by email
        matched_uid = None
        user_data = None
        for uid, sdata in students.items():
            if isinstance(sdata, dict) and sdata.get('email', '').lower() == email:
                matched_uid = uid
                user_data = sdata
                break

        # Check default admin if no students registered yet
        if not user_data and email == "admin@absensi.ai" and password == "admin123":
            matched_uid = "admin_default"
            user_data = {
                "nama": "Administrator",
                "email": "admin@absensi.ai",
                "role": "admin",
                "nis": "ADMIN-001",
                "kelas": "Admin Staff",
                "status": "aktif"
            }
            # Auto-seed admin to Firebase
            db.set(f"students/{matched_uid}", user_data)

        if not user_data:
            flash("Email atau kata sandi tidak cocok.", "danger")
            return render_template('login.html')

        # Check password hash if present, or fallback to direct compare for initial setup
        stored_hash = user_data.get('password_hash')
        stored_pw = user_data.get('password') # legacy/initial setup fallback
        password_valid = False

        if stored_hash and check_password_hash(stored_hash, password):
            password_valid = True
        elif stored_pw and stored_pw == password:
            password_valid = True
        elif email == "admin@absensi.ai" and password == "admin123":
            password_valid = True

        if not password_valid:
            flash("Email atau kata sandi tidak cocok.", "danger")
            return render_template('login.html')

        if user_data.get('status', 'aktif') != 'aktif':
            flash("Akun Anda telah dinonaktifkan. Hubungi admin sekolah.", "warning")
            return render_template('login.html')

        # Set session
        session['uid'] = matched_uid
        session['nama'] = user_data.get('nama', 'User')
        session['email'] = user_data.get('email', email)
        session['role'] = user_data.get('role', 'siswa')
        session['nis'] = user_data.get('nis', '-')
        session['kelas'] = user_data.get('kelas', '-')

        flash(f"Selamat datang, {session['nama']}!", "success")
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah berhasil keluar.", "info")
    return redirect(url_for('login'))


# ==========================================
# STUDENT ROUTES
# ==========================================
@app.route('/student/dashboard')
@student_required
def student_dashboard():
    uid = session['uid']
    db = get_db()
    student = db.get(f"students/{uid}") or {}

    today_str = attendance_service.get_today_string()
    today_attendance = attendance_service.check_today_attendance(uid, today_str)

    history = attendance_service.get_student_history(uid)

    # Compute personal stats
    hadir_count = sum(1 for h in history if h.get('status') == 'Hadir')
    terlambat_count = sum(1 for h in history if h.get('status') == 'Terlambat')
    izin_count = sum(1 for h in history if h.get('status') in ['Izin', 'Sakit'])
    total_absen = len(history)

    return render_template(
        'student/dashboard.html',
        student=sanitize_student(student),
        today_attendance=today_attendance,
        hadir_count=hadir_count,
        terlambat_count=terlambat_count,
        izin_count=izin_count,
        total_absen=total_absen,
        recent_history=history[:5]
    )


@app.route('/student/attendance')
@student_required
def student_attendance():
    uid = session['uid']
    today_str = attendance_service.get_today_string()
    today_attendance = attendance_service.check_today_attendance(uid, today_str)
    return render_template('student/attendance.html', today_attendance=today_attendance)


@app.route('/student/history')
@student_required
def student_history():
    uid = session['uid']
    history = attendance_service.get_student_history(uid)
    return render_template('student/history.html', history=history)


# ==========================================
# ADMIN ROUTES
# ==========================================
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    today_str = attendance_service.get_today_string()
    stats = attendance_service.get_dashboard_stats(today_str)
    today_attendance = attendance_service.get_attendance_for_date(today_str)
    return render_template('admin/dashboard.html', stats=stats, today_attendance=today_attendance)


@app.route('/admin/students')
@admin_required
def admin_students():
    db = get_db()
    students_raw = db.get("students") or {}
    students_list = []
    for uid, sdata in students_raw.items():
        if isinstance(sdata, dict):
            clean = sanitize_student(sdata)
            clean['uid'] = uid
            clean['has_face'] = bool(sdata.get('faceEmbedding'))
            students_list.append(clean)

    students_list.sort(key=lambda s: s.get('nama', '').lower())
    return render_template('admin/students.html', students=students_list)


@app.route('/admin/attendance')
@admin_required
def admin_attendance():
    date_filter = request.args.get('date', attendance_service.get_today_string())
    attendance_data = attendance_service.get_attendance_for_date(date_filter)

    db = get_db()
    students = db.get("students") or {}

    attendance_list = []
    for uid, rec in attendance_data.items():
        if isinstance(rec, dict):
            entry = dict(rec)
            entry['uid'] = uid
            attendance_list.append(entry)

    attendance_list.sort(key=lambda x: x.get('waktu', ''), reverse=True)
    return render_template(
        'admin/attendance.html',
        selected_date=date_filter,
        attendance_list=attendance_list,
        students=students
    )


@app.route('/admin/reports')
@admin_required
def admin_reports():
    today_str = attendance_service.get_today_string()
    start_date = request.args.get('start_date', today_str)
    end_date = request.args.get('end_date', today_str)
    kelas = request.args.get('kelas', '').strip()
    status = request.args.get('status', '').strip()
    student_uid = request.args.get('student_uid', '').strip()

    reports = attendance_service.filter_reports(
        start_date=start_date,
        end_date=end_date,
        kelas=kelas if kelas else None,
        student_uid=student_uid if student_uid else None,
        status=status if status else None
    )

    db = get_db()
    students = db.get("students") or {}
    classes = sorted(list(set(s.get('kelas') for s in students.values() if isinstance(s, dict) and s.get('kelas'))))

    return render_template(
        'admin/reports.html',
        reports=reports,
        start_date=start_date,
        end_date=end_date,
        kelas=kelas,
        status=status,
        student_uid=student_uid,
        students=students,
        classes=classes
    )


@app.route('/admin/register-face', methods=['GET'])
@admin_required
def admin_register_face():
    student_uid = request.args.get('uid', '')
    db = get_db()
    students_raw = db.get("students") or {}
    students_list = []
    for uid, sdata in students_raw.items():
        if isinstance(sdata, dict):
            s = sanitize_student(sdata)
            s['uid'] = uid
            s['has_face'] = bool(sdata.get('faceEmbedding'))
            students_list.append(s)

    selected_student = students_raw.get(student_uid) if student_uid else None
    if selected_student:
        selected_student = sanitize_student(selected_student)
        selected_student['uid'] = student_uid

    return render_template(
        'admin/register_face.html',
        students=students_list,
        selected_student=selected_student,
        target_uid=student_uid
    )


# ==========================================
# REST API ENDPOINTS
# ==========================================
@app.route('/api/attendance/face', methods=['POST'])
def api_face_attendance():
    """Face recognition attendance API."""
    data = request.get_json() or {}
    image_base64 = data.get('image')

    if not image_base64:
        return jsonify({"success": False, "message": "Data gambar kamera tidak boleh kosong."}), 400

    # If student is logged in, verify against their own profile
    expected_uid = session.get('uid') if session.get('role') == 'siswa' else None

    result = attendance_service.record_face_attendance(
        image_base64=image_base64,
        expected_uid=expected_uid
    )

    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route('/api/admin/students', methods=['POST'])
@admin_required
def api_add_student():
    """Create new student in Firebase Realtime Database."""
    data = request.get_json() or {}
    nis = data.get('nis', '').strip()
    nama = data.get('nama', '').strip()
    kelas = data.get('kelas', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '123456')
    role = data.get('role', 'siswa')
    status = data.get('status', 'aktif')

    if not nis or not nama or not kelas or not email:
        return jsonify({"success": False, "message": "NIS, Nama, Kelas, dan Email wajib diisi."}), 400

    # Ensure role is strictly 'siswa' or 'admin'
    if role not in ['siswa', 'admin']:
        role = 'siswa'

    db = get_db()
    existing = db.get("students") or {}
    for uid, s in existing.items():
        if isinstance(s, dict):
            if s.get('email', '').lower() == email:
                return jsonify({"success": False, "message": "Email sudah terdaftar."}), 400
            if s.get('nis') == nis:
                return jsonify({"success": False, "message": "NIS sudah terdaftar."}), 400

    uid = f"student_{int(datetime.now().timestamp() * 1000)}"
    new_student = {
        "nis": nis,
        "nama": nama,
        "kelas": kelas,
        "email": email,
        "role": role,
        "foto": "",
        "faceEmbedding": None,
        "status": status,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now().isoformat()
    }

    success = db.set(f"students/{uid}", new_student)
    if success:
        return jsonify({"success": True, "message": "Siswa berhasil ditambahkan!", "uid": uid})
    return jsonify({"success": False, "message": "Gagal menyimpan data siswa ke Firebase."}), 500


@app.route('/api/admin/students/<uid>', methods=['PUT'])
@admin_required
def api_update_student(uid):
    """Update student info in Firebase."""
    data = request.get_json() or {}
    db = get_db()
    student = db.get(f"students/{uid}")
    if not student:
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    update_fields = {}
    if 'nama' in data: update_fields['nama'] = data['nama'].strip()
    if 'nis' in data: update_fields['nis'] = data['nis'].strip()
    if 'kelas' in data: update_fields['kelas'] = data['kelas'].strip()
    if 'email' in data: update_fields['email'] = data['email'].strip().lower()
    if 'status' in data: update_fields['status'] = data['status']
    if 'role' in data and data['role'] in ['siswa', 'admin']:
        update_fields['role'] = data['role']
    if 'password' in data and data['password']:
        update_fields['password_hash'] = generate_password_hash(data['password'])

    success = db.update(f"students/{uid}", update_fields)
    if success:
        return jsonify({"success": True, "message": "Data siswa berhasil diperbarui!"})
    return jsonify({"success": False, "message": "Gagal memperbarui data siswa."}), 500


@app.route('/api/admin/students/<uid>', methods=['DELETE'])
@admin_required
def api_delete_student(uid):
    """Delete student from Firebase."""
    db = get_db()
    success = db.delete(f"students/{uid}")
    if success:
        return jsonify({"success": True, "message": "Siswa berhasil dihapus."})
    return jsonify({"success": False, "message": "Gagal menghapus siswa."}), 500


@app.route('/api/admin/register-face', methods=['POST'])
@admin_required
def api_admin_register_face():
    """Register face embedding for a student."""
    data = request.get_json() or {}
    uid = data.get('uid')
    image_base64 = data.get('image')

    if not uid or not image_base64:
        return jsonify({"success": False, "message": "UID siswa dan foto wajib disediakan."}), 400

    result = attendance_service.register_student_face(uid, image_base64)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route('/api/admin/attendance/manual', methods=['POST'])
@admin_required
def api_manual_attendance():
    """Manual mark attendance by admin."""
    data = request.get_json() or {}
    uid = data.get('uid')
    date_str = data.get('date', attendance_service.get_today_string())
    status = data.get('status', 'Hadir')
    note = data.get('note', '')

    if not uid or not status:
        return jsonify({"success": False, "message": "UID siswa dan status absensi wajib diisi."}), 400

    success = attendance_service.manual_mark_attendance(uid, date_str, status, note)
    if success:
        return jsonify({"success": True, "message": f"Status absensi berhasil diubah menjadi {status}!"})
    return jsonify({"success": False, "message": "Gagal mencatat absensi manual."}), 500


@app.route('/admin/reports/export')
@admin_required
def export_reports_csv():
    """Export attendance reports to CSV file."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    kelas = request.args.get('kelas')
    status = request.args.get('status')
    student_uid = request.args.get('student_uid')

    reports = attendance_service.filter_reports(
        start_date=start_date,
        end_date=end_date,
        kelas=kelas if kelas else None,
        student_uid=student_uid if student_uid else None,
        status=status if status else None
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    # Indonesian CSV headers
    writer.writerow(['No', 'Tanggal', 'Waktu', 'NIS', 'Nama Siswa', 'Kelas', 'Status Kehadiran', 'Metode Absensi'])

    for idx, rec in enumerate(reports, 1):
        writer.writerow([
            idx,
            rec.get('tanggal', ''),
            rec.get('waktu', ''),
            rec.get('nis', ''),
            rec.get('nama', ''),
            rec.get('kelas', ''),
            rec.get('status', ''),
            rec.get('method', '')
        ])

    csv_data = output.getvalue()
    filename = f"Laporan_Absensi_{start_date or 'Semua'}_sd_{end_date or 'Semua'}.csv"

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ['true', '1', 'yes']
    logger.info(f"Starting ABSENSI AI server on port {port} (Debug: {debug})...")
    app.run(host='0.0.0.0', port=port, debug=debug)
