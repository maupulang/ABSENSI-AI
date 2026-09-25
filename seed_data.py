"""
ABSENSI AI - Database Seeder Script
Inisialisasi akun Admin default dan data siswa contoh ke Firebase Realtime Database.
"""

import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

from firebase_config import get_db

load_dotenv()

def seed_database():
    db = get_db()
    print("Mengkoneksikan ke Firebase Realtime Database...")

    # 1. Admin Default Account
    admin_uid = "admin_default"
    admin_data = {
        "nis": "ADMIN-001",
        "nama": "Administrator Utama",
        "kelas": "Staf Administrator",
        "email": "admin@absensi.ai",
        "password_hash": generate_password_hash("admin123"),
        "role": "admin",
        "status": "aktif",
        "created_at": datetime.now().isoformat()
    }
    
    print(f"Menyimpan akun Admin ({admin_data['email']})...")
    db.set(f"students/{admin_uid}", admin_data)

    # 2. Sample Students
    sample_students = [
        {
            "uid": "student_101",
            "nis": "2026101",
            "nama": "Budi Santoso",
            "kelas": "XII RPL 1",
            "email": "budi@absensi.ai",
            "password_hash": generate_password_hash("123456"),
            "role": "siswa",
            "status": "aktif",
            "faceEmbedding": None,
            "created_at": datetime.now().isoformat()
        },
        {
            "uid": "student_102",
            "nis": "2026102",
            "nama": "Siti Nurhaliza",
            "kelas": "XII RPL 1",
            "email": "siti@absensi.ai",
            "password_hash": generate_password_hash("123456"),
            "role": "siswa",
            "status": "aktif",
            "faceEmbedding": None,
            "created_at": datetime.now().isoformat()
        },
        {
            "uid": "student_103",
            "nis": "2026103",
            "nama": "Ahmad Rizky Pratama",
            "kelas": "XII RPL 2",
            "email": "ahmad@absensi.ai",
            "password_hash": generate_password_hash("123456"),
            "role": "siswa",
            "status": "aktif",
            "faceEmbedding": None,
            "created_at": datetime.now().isoformat()
        }
    ]

    for s in sample_students:
        uid = s["uid"]
        print(f"Menyimpan siswa: {s['nama']} ({s['email']})...")
        db.set(f"students/{uid}", s)

    print("\nInisialisasi Data Selesai!")
    print("---------------------------------------------")
    print("Akun Admin : admin@absensi.ai / admin123")
    print("Akun Siswa : budi@absensi.ai / 123456")
    print("Akun Siswa : siti@absensi.ai / 123456")
    print("---------------------------------------------")

if __name__ == "__main__":
    seed_database()
