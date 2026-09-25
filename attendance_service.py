import os
import time
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
import logging

from firebase_config import get_db
from face_recognition_service import face_service

logger = logging.getLogger(__name__)

ATTENDANCE_LATE_TIME = os.getenv("ATTENDANCE_LATE_TIME", "07:15")
ATTENDANCE_START_TIME = os.getenv("ATTENDANCE_START_TIME", "06:00")
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.45"))


class AttendanceService:
    def __init__(self):
        self.db = get_db()

    def get_today_string(self) -> str:
        """Returns current date string in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    def get_current_time_string(self) -> str:
        """Returns current time string in HH:MM:SS format."""
        return datetime.now().strftime("%H:%M:%S")

    def determine_attendance_status(self, current_time_str: Optional[str] = None) -> str:
        """
        Determines if student is 'Hadir' or 'Terlambat' based on ATTENDANCE_LATE_TIME.
        """
        if current_time_str is None:
            current_time_str = self.get_current_time_string()

        curr_parts = [int(p) for p in current_time_str.split(':')[:2]]
        late_parts = [int(p) for p in ATTENDANCE_LATE_TIME.split(':')[:2]]

        curr_minutes = curr_parts[0] * 60 + curr_parts[1]
        late_minutes = late_parts[0] * 60 + late_parts[1]

        if curr_minutes > late_minutes:
            return "Terlambat"
        return "Hadir"

    def get_all_students(self) -> Dict[str, Any]:
        """Fetch all students from Firebase Realtime Database."""
        data = self.db.get("students")
        if not data or not isinstance(data, dict):
            return {}
        return data

    def get_student(self, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch single student by UID."""
        data = self.db.get(f"students/{uid}")
        if data and isinstance(data, dict):
            return data
        return None

    def check_today_attendance(self, uid: str, date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check if student has already recorded attendance for the specified date."""
        if date_str is None:
            date_str = self.get_today_string()

        path = f"attendance/{date_str}/{uid}"
        record = self.db.get(path)
        if record and isinstance(record, dict):
            return record
        return None

    def record_face_attendance(
        self,
        image_base64: str,
        expected_uid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process face recognition attendance:
        1. Decode image & detect face
        2. Extract face embedding
        3. Match against registered student(s)
        4. Validate identity
        5. Check today's attendance (prevent duplicate)
        6. Save attendance to Firebase
        """
        # Step 1: Decode
        img = face_service.decode_base64_image(image_base64)
        if img is None:
            return {
                "success": False,
                "code": "INVALID_IMAGE",
                "message": "Format gambar tidak valid atau kamera tidak terbaca."
            }

        # Step 2: Extract embedding
        query_embedding = face_service.extract_face_embedding(img)
        if query_embedding is None:
            return {
                "success": False,
                "code": "NO_FACE_DETECTED",
                "message": "Wajah tidak terdeteksi. Posisikan wajah Anda tepat di depan kamera."
            }

        students = self.get_all_students()
        if not students:
            return {
                "success": False,
                "code": "NO_STUDENTS",
                "message": "Belum ada data siswa terdaftar di sistem."
            }

        # Step 3 & 4: Match student
        if expected_uid:
            # Student is logged in and verifying their own face
            target_student = students.get(expected_uid)
            if not target_student:
                return {
                    "success": False,
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Data siswa tidak ditemukan."
                }
            stored_embedding = target_student.get("faceEmbedding")
            if not stored_embedding:
                return {
                    "success": False,
                    "code": "NO_EMBEDDING_REGISTERED",
                    "message": "Wajah Anda belum didaftarkan oleh admin. Silakan hubungi admin."
                }
            dist = face_service.calculate_cosine_distance(query_embedding, stored_embedding)
            if dist > FACE_MATCH_THRESHOLD:
                return {
                    "success": False,
                    "code": "FACE_NOT_RECOGNIZED",
                    "message": "Wajah tidak dikenali. Pastikan pencahayaan cukup dan wajah terlihat jelas."
                }
            matched_uid = expected_uid
            matched_student = target_student
        else:
            # General camera scan (kiosk mode)
            matched_uid, matched_student, dist = face_service.find_matching_student(
                query_embedding, students, threshold=FACE_MATCH_THRESHOLD
            )
            if not matched_uid or not matched_student:
                return {
                    "success": False,
                    "code": "FACE_NOT_RECOGNIZED",
                    "message": "Wajah tidak dikenali."
                }

        # Step 5: Check today's attendance
        today = self.get_today_string()
        existing = self.check_today_attendance(matched_uid, today)
        if existing:
            return {
                "success": False,
                "code": "ALREADY_ATTENDED",
                "message": "Anda sudah melakukan absensi hari ini.",
                "data": {
                    "uid": matched_uid,
                    "nama": matched_student.get("nama"),
                    "nis": matched_student.get("nis"),
                    "kelas": matched_student.get("kelas"),
                    "waktu": existing.get("waktu"),
                    "status": existing.get("status")
                }
            }

        # Step 6: Determine status and record attendance
        curr_time = self.get_current_time_string()
        status = self.determine_attendance_status(curr_time)
        attendance_record = {
            "nis": matched_student.get("nis", "-"),
            "nama": matched_student.get("nama", "Siswa"),
            "kelas": matched_student.get("kelas", "-"),
            "tanggal": today,
            "waktu": curr_time,
            "status": status,
            "timestamp": int(time.time()),
            "method": "Face Recognition"
        }

        save_path = f"attendance/{today}/{matched_uid}"
        saved = self.db.set(save_path, attendance_record)

        if not saved:
            return {
                "success": False,
                "code": "SAVE_ERROR",
                "message": "Gagal menyimpan absensi ke Firebase."
            }

        return {
            "success": True,
            "code": "SUCCESS",
            "message": f"Absensi berhasil dicatat ({status})!",
            "data": {
                "uid": matched_uid,
                "nis": attendance_record["nis"],
                "nama": attendance_record["nama"],
                "kelas": attendance_record["kelas"],
                "tanggal": attendance_record["tanggal"],
                "waktu": attendance_record["waktu"],
                "status": attendance_record["status"],
                "method": attendance_record["method"]
            }
        }

    def register_student_face(self, uid: str, image_base64: str) -> Dict[str, Any]:
        """
        Extract face embedding from image and save to student profile in Firebase.
        """
        img = face_service.decode_base64_image(image_base64)
        if img is None:
            return {"success": False, "message": "Format foto tidak valid."}

        bbox = face_service.detect_face_bbox(img)
        if bbox is None:
            return {"success": False, "message": "Tidak ada wajah terdeteksi pada foto."}

        embedding = face_service.extract_face_embedding(img)
        if embedding is None:
            return {"success": False, "message": "Gagal menghasilkan face embedding."}

        # Update student record
        update_data = {
            "faceEmbedding": embedding,
            "foto": image_base64 if len(image_base64) < 100000 else "" # store preview if reasonable
        }
        res = self.db.update(f"students/{uid}", update_data)
        if res:
            return {"success": True, "message": "Wajah siswa berhasil didaftarkan!"}
        return {"success": False, "message": "Gagal menyimpan data wajah ke Firebase."}

    def get_attendance_for_date(self, date_str: str) -> Dict[str, Any]:
        """Fetch all attendance records for a specific date."""
        path = f"attendance/{date_str}"
        data = self.db.get(path)
        if data and isinstance(data, dict):
            return data
        return {}

    def get_student_history(self, uid: str) -> List[Dict[str, Any]]:
        """Fetch all attendance history for a single student."""
        all_attendance = self.db.get("attendance")
        history = []
        if not all_attendance or not isinstance(all_attendance, dict):
            return history

        for date_key, day_records in all_attendance.items():
            if isinstance(day_records, dict) and uid in day_records:
                record = day_records[uid]
                if isinstance(record, dict):
                    rec = dict(record)
                    rec["tanggal"] = date_key
                    history.append(rec)

        # Sort descending by date & time
        history.sort(key=lambda x: (x.get("tanggal", ""), x.get("waktu", "")), reverse=True)
        return history

    def get_dashboard_stats(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate KPI stats for Admin Dashboard:
        - Total Siswa
        - Hadir
        - Terlambat
        - Izin/Sakit
        - Belum Hadir / Alpha
        """
        if date_str is None:
            date_str = self.get_today_string()

        students = self.get_all_students()
        # Filter only active students with role 'siswa'
        active_students = {
            uid: s for uid, s in students.items() 
            if s.get("role") != "admin" and s.get("status", "aktif") == "aktif"
        }
        total_students = len(active_students)

        day_attendance = self.get_attendance_for_date(date_str)

        hadir_count = 0
        terlambat_count = 0
        izin_count = 0
        sakit_count = 0

        attended_uids = set()

        for uid, rec in day_attendance.items():
            if not isinstance(rec, dict):
                continue
            attended_uids.add(uid)
            st = rec.get("status", "")
            if st == "Hadir":
                hadir_count += 1
            elif st == "Terlambat":
                terlambat_count += 1
            elif st == "Izin":
                izin_count += 1
            elif st == "Sakit":
                sakit_count += 1

        belum_hadir_count = max(0, total_students - len(attended_uids))

        return {
            "date": date_str,
            "total_students": total_students,
            "hadir": hadir_count,
            "terlambat": terlambat_count,
            "izin": izin_count,
            "sakit": sakit_count,
            "belum_hadir": belum_hadir_count,
            "attendance_rate": round(((hadir_count + terlambat_count) / total_students * 100), 1) if total_students > 0 else 0
        }

    def filter_reports(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        kelas: Optional[str] = None,
        student_uid: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter attendance reports based on criteria.
        """
        all_attendance = self.db.get("attendance")
        results = []
        if not all_attendance or not isinstance(all_attendance, dict):
            return results

        today = self.get_today_string()
        if not start_date:
            start_date = today
        if not end_date:
            end_date = today

        for date_key, day_records in all_attendance.items():
            if not (start_date <= date_key <= end_date):
                continue

            if not isinstance(day_records, dict):
                continue

            for uid, rec in day_records.items():
                if not isinstance(rec, dict):
                    continue

                if student_uid and uid != student_uid:
                    continue

                if kelas and rec.get("kelas", "").lower() != kelas.lower():
                    continue

                if status and rec.get("status", "").lower() != status.lower():
                    continue

                entry = dict(rec)
                entry["uid"] = uid
                entry["tanggal"] = date_key
                results.append(entry)

        results.sort(key=lambda x: (x.get("tanggal", ""), x.get("waktu", "")), reverse=True)
        return results

    def manual_mark_attendance(
        self,
        uid: str,
        date_str: str,
        status: str,
        note: str = ""
    ) -> bool:
        """Allow admin to manually set/update attendance status."""
        student = self.get_student(uid)
        if not student:
            return False

        curr_time = self.get_current_time_string()
        record = {
            "nis": student.get("nis", "-"),
            "nama": student.get("nama", "Siswa"),
            "kelas": student.get("kelas", "-"),
            "tanggal": date_str,
            "waktu": curr_time,
            "status": status,
            "timestamp": int(time.time()),
            "method": f"Manual Admin ({note})" if note else "Manual Admin"
        }
        return self.db.set(f"attendance/{date_str}/{uid}", record)


attendance_service = AttendanceService()
