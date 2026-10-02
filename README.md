<div align="center">

# 🎓 ABSENSI AI — AILA
### Sistem Absensi Cerdas Berbasis AI Face Recognition

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> Aplikasi web absensi sekolah berbasis kecerdasan buatan dengan teknologi **Face Recognition** menggunakan OpenCV YuNet + SFace, terintegrasi dengan **Firebase Realtime Database** untuk penyimpanan data real-time.

![ABSENSI AI Banner](https://img.shields.io/badge/-Live%20Demo%20%7C%20localhost%3A5000-6366f1?style=for-the-badge&logo=googlechrome&logoColor=white)

</div>

---

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Teknologi](#-teknologi)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Struktur Project](#-struktur-project)
- [Instalasi & Menjalankan](#-instalasi--menjalankan)
- [Akun Default](#-akun-default)
- [Halaman Aplikasi](#-halaman-aplikasi)
- [Alur Absensi Face Recognition](#-alur-absensi-face-recognition)
- [Firebase Security Rules](#-firebase-security-rules)
- [API Endpoints](#-api-endpoints)
- [Konfigurasi .env](#-konfigurasi-env)
- [Panduan Penggunaan](#-panduan-penggunaan)

---

## ✨ Fitur Utama

### 👨‍🎓 Siswa
| Fitur | Deskripsi |
|---|---|
| 🔐 Login Aman | Autentikasi berbasis email & password hash (scrypt) |
| 📸 Absensi Kamera AI | Scan wajah real-time via browser (tidak perlu app tambahan) |
| 🛡️ Anti Duplikat | Sistem mencegah absensi lebih dari 1x per hari |
| 📊 Riwayat Absensi | Lihat rekap kehadiran pribadi: Hadir, Terlambat, Izin, Sakit |
| 🖥️ Dashboard Pribadi | Statistik kehadiran bulan/semester berjalan |

### 👨‍💼 Admin
| Fitur | Deskripsi |
|---|---|
| 📈 Dashboard KPI | Statistik harian: total hadir, terlambat, izin, belum hadir |
| 👥 CRUD Data Siswa | Tambah, edit, hapus, dan nonaktifkan akun siswa |
| 🤖 Registrasi Wajah | Daftarkan face embedding siswa via kamera atau upload foto |
| 📋 Lihat Semua Absensi | Pantau kehadiran semua siswa per tanggal |
| 🔎 Filter Laporan | Filter berdasarkan tanggal, kelas, siswa, dan status |
| 📁 Export CSV | Ekspor laporan absensi ke file CSV/Excel |
| ✏️ Absensi Manual | Catat Izin / Sakit / Alpha secara manual |

---

## 🛠️ Teknologi

```
Backend       : Python 3.11+, Flask 3.x
AI / CV       : OpenCV 5.x, YuNet (Face Detection), SFace (Face Recognition)
Database      : Firebase Realtime Database (REST API / Admin SDK)
Auth          : Session-based Flask + Werkzeug Password Hash (scrypt)
Frontend      : HTML5, Tailwind CSS (CDN), Vanilla JavaScript
Camera API    : WebRTC MediaDevices (browser-native)
Model Format  : ONNX (YuNet + SFace pre-trained)
```

---

## 🏗️ Arsitektur Sistem

```
Browser (Webcam)
      │
      │  Base64 JPEG
      ▼
  Flask Server (app.py)
      │
      ├─► face_recognition_service.py
      │        ├─ YuNet: Detect face bounding box
      │        ├─ SFace: Extract 128-d face embedding
      │        └─ Cosine Distance: Match vs stored embeddings
      │
      ├─► attendance_service.py
      │        ├─ Cek absensi duplikat (Firebase)
      │        ├─ Tentukan status: Hadir / Terlambat
      │        └─ Simpan record ke Firebase
      │
      └─► firebase_config.py
               ├─ Mode 1: Firebase Admin SDK (jika serviceAccountKey.json ada)
               └─ Mode 2: REST API (fallback otomatis)
```

---

## 📁 Struktur Project

```
absensi-ai/
├── app.py                          # Flask app utama, routes, & REST API
├── attendance_service.py           # Logika absensi, statistik, laporan
├── face_recognition_service.py     # Face detection & recognition (YuNet + SFace)
├── firebase_config.py              # Koneksi Firebase (Admin SDK / REST)
├── seed_data.py                    # Script inisialisasi data awal ke Firebase
├── database.rules.json             # Firebase Security Rules
├── requirements.txt                # Dependensi Python
├── .env                            # Konfigurasi environment (tidak di-commit)
├── .env.example                    # Template konfigurasi
├── .gitignore
├── README.md
│
├── models/                         # ONNX AI Models (auto-download saat runtime)
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
│
├── templates/
│   ├── base.html                   # Layout utama (sidebar, navbar)
│   ├── login.html
│   ├── admin/
│   │   ├── dashboard.html          # Dashboard admin + KPI cards
│   │   ├── students.html           # CRUD data siswa
│   │   ├── attendance.html         # Data absensi per tanggal
│   │   ├── reports.html            # Laporan & filter
│   │   └── register_face.html      # Registrasi wajah siswa
│   └── student/
│       ├── dashboard.html          # Dashboard siswa
│       ├── attendance.html         # Halaman absensi kamera
│       └── history.html            # Riwayat absensi pribadi
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── face_capture.js         # Logika kamera & absensi face recognition
        └── main.js
```

---

## 🚀 Instalasi & Menjalankan

### Prasyarat
- Python **3.11+**
- Akun [Firebase](https://firebase.google.com) dengan project aktif
- Git

### 1. Clone Repository
```bash
git clone https://github.com/maupulang/ABSENSI-AI.git
cd ABSENSI-AI
```

### 2. Buat Virtual Environment
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment
```bash
cp .env.example .env
```
Edit file `.env` dan sesuaikan dengan konfigurasi Firebase Anda (lihat [Konfigurasi .env](#-konfigurasi-env)).

### 5. Inisialisasi Data Awal (Opsional)
```bash
python seed_data.py
```
> Script ini akan membuat akun Admin default dan 3 akun siswa contoh di Firebase.

### 6. Jalankan Aplikasi
```bash
python app.py
```

Aplikasi akan berjalan di: **http://localhost:5000**

> 💡 **Model AI** (YuNet & SFace ONNX) akan diunduh **otomatis** saat pertama kali dijalankan jika belum ada di folder `models/`.

---

## 🔑 Akun Default

| Role | Email | Password |
|---|---|---|
| 👨‍💼 **Admin** | `admin@absensi.ai` | `admin123` |
| 👨‍🎓 Siswa | `budi@absensi.ai` | `123456` |
| 👨‍🎓 Siswa | `siti@absensi.ai` | `123456` |
| 👨‍🎓 Siswa | `ahmad@absensi.ai` | `123456` |

> ⚠️ Ganti password admin setelah deploy ke production!

---

## 🖥️ Halaman Aplikasi

| URL | Role | Deskripsi |
|---|---|---|
| `/login` | Semua | Halaman login |
| `/admin/dashboard` | Admin | Dashboard statistik kehadiran |
| `/admin/students` | Admin | Manajemen data siswa (CRUD) |
| `/admin/attendance` | Admin | Data absensi per tanggal |
| `/admin/reports` | Admin | Laporan & filter + export CSV |
| `/admin/register-face` | Admin | Registrasi wajah siswa via kamera |
| `/student/dashboard` | Siswa | Dashboard pribadi siswa |
| `/student/attendance` | Siswa | Absensi menggunakan kamera AI |
| `/student/history` | Siswa | Riwayat absensi pribadi |

---

## 🤖 Alur Absensi Face Recognition

```
Kamera Browser
      │
      ▼ (Base64 JPEG)
[POST] /api/attendance/face
      │
      ├─ 1. Decode gambar dari Base64
      │
      ├─ 2. Deteksi wajah (YuNet ONNX)
      │       └─ Tidak ada wajah? → "Wajah tidak terdeteksi"
      │
      ├─ 3. Ekstrak face embedding 128-dimensi (SFace ONNX)
      │
      ├─ 4. Cocokkan dengan data siswa di Firebase
      │       └─ Jarak cosine > threshold? → "Wajah tidak dikenali"
      │
      ├─ 5. Cek absensi hari ini
      │       └─ Sudah absen? → "Anda sudah absen hari ini"
      │
      ├─ 6. Tentukan status: Hadir / Terlambat
      │       └─ Berdasarkan jam (default terlambat: 07:15)
      │
      └─ 7. Simpan ke Firebase → Tampilkan hasil ✅
```

**Threshold Konfigurasi:**
- Default cosine distance threshold: `0.45`
- Semakin kecil = semakin ketat pencocokan
- Dapat diubah via `.env`: `FACE_MATCH_THRESHOLD=0.45`

---

## 🔥 Firebase Setup

### Struktur Data Realtime Database

```json
{
  "students": {
    "uid": {
      "nis": "2026101",
      "nama": "Budi Santoso",
      "kelas": "XII RPL 1",
      "email": "budi@absensi.ai",
      "role": "siswa",
      "status": "aktif",
      "faceEmbedding": [0.12, -0.34, ...],
      "password_hash": "scrypt:...",
      "created_at": "2026-09-25T00:00:00"
    }
  },
  "attendance": {
    "2026-10-02": {
      "uid": {
        "nis": "2026101",
        "nama": "Budi Santoso",
        "kelas": "XII RPL 1",
        "tanggal": "2026-10-02",
        "waktu": "07:05:32",
        "status": "Hadir",
        "timestamp": 1759420000,
        "method": "Face Recognition"
      }
    }
  }
}
```

### Status Absensi
| Status | Keterangan |
|---|---|
| ✅ Hadir | Masuk sebelum jam terlambat |
| ⏰ Terlambat | Masuk setelah jam terlambat |
| 📋 Izin | Input manual oleh admin |
| 🤒 Sakit | Input manual oleh admin |
| ❌ Alpha | Input manual oleh admin |

---

## 🔒 Firebase Security Rules

File: [`database.rules.json`](database.rules.json)

```json
{
  "rules": {
    "students": {
      ".read": "auth != null",
      "$uid": {
        ".read": "auth != null && (auth.uid === $uid || root.child('students').child(auth.uid).child('role').val() === 'admin')",
        ".write": "auth != null && root.child('students').child(auth.uid).child('role').val() === 'admin'",
        "faceEmbedding": {
          ".read": "auth != null && root.child('students').child(auth.uid).child('role').val() === 'admin'"
        }
      }
    },
    "attendance": {
      "$date": {
        "$uid": {
          ".read": "auth != null && (auth.uid === $uid || root.child('students').child(auth.uid).child('role').val() === 'admin')",
          ".write": "auth != null && (auth.uid === $uid || root.child('students').child(auth.uid).child('role').val() === 'admin')"
        }
      }
    }
  }
}
```

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Deskripsi |
|---|---|---|---|
| `POST` | `/api/attendance/face` | Login | Proses absensi via face recognition |
| `POST` | `/api/admin/students` | Admin | Tambah siswa baru |
| `PUT` | `/api/admin/students/<uid>` | Admin | Update data siswa |
| `DELETE` | `/api/admin/students/<uid>` | Admin | Hapus siswa |
| `POST` | `/api/admin/register-face` | Admin | Daftarkan wajah siswa |
| `POST` | `/api/admin/attendance/manual` | Admin | Input absensi manual |
| `GET` | `/admin/reports/export` | Admin | Export laporan CSV |

---

## ⚙️ Konfigurasi .env

```env
# Flask
SECRET_KEY=your_super_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# Firebase
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_SERVICE_ACCOUNT_KEY=serviceAccountKey.json  # Opsional
FIREBASE_DB_SECRET=                                   # Legacy secret (opsional)

# Firebase Web SDK (untuk frontend)
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abc123

# AI Face Recognition
FACE_MATCH_THRESHOLD=0.45   # 0.0 (ketat) - 1.0 (longgar)
FACE_DETECTION_MODEL=opencv_dnn

# Jam Absensi
ATTENDANCE_START_TIME=06:00
ATTENDANCE_LATE_TIME=07:15
ATTENDANCE_END_TIME=17:00
```

### Mode Firebase
| Mode | Kondisi | Keterangan |
|---|---|---|
| **Admin SDK** | `serviceAccountKey.json` tersedia | Fitur penuh, lebih aman |
| **REST API** | Fallback otomatis | Tanpa service account, gunakan Database Secret |

---

## 📖 Panduan Penggunaan

### Setup Pertama (Admin)

1. **Login** sebagai Admin → `admin@absensi.ai` / `admin123`
2. **Tambah Siswa** → Menu **Kelola Siswa** → klik **"Tambah Siswa Baru"**
3. **Daftarkan Wajah** → Klik ikon 📷 di baris siswa → Halaman **Registrasi Wajah**
   - Aktifkan kamera → Posisikan wajah → Klik **"Ambil Foto Wajah"**
   - Atau upload foto dari file
   - Klik **"Simpan Face Embedding"**
4. Ulangi untuk semua siswa

### Absensi Harian (Siswa)

1. **Login** sebagai Siswa
2. Klik menu **Absensi Kamera** atau tombol absen di Dashboard
3. Klik **"Aktifkan Kamera"** → izinkan akses kamera
4. Posisikan wajah tepat di dalam bingkai
5. Klik **"Scan Wajah & Absen Sekarang"**
6. Sistem akan menampilkan konfirmasi: nama, jam, dan status kehadiran ✅

### Laporan & Export (Admin)

1. Menu **Laporan** → atur filter tanggal, kelas, status
2. Klik **"Terapkan Filter"**
3. Klik **"Ekspor ke CSV"** → file siap diimpor ke Excel

---

## 🔧 Troubleshooting

| Masalah | Solusi |
|---|---|
| Model AI tidak termuat | Pastikan folder `models/` dapat diakses dan ada koneksi internet untuk download otomatis |
| Firebase tidak terkoneksi | Cek `FIREBASE_DATABASE_URL` di `.env` dan pastikan rules Firebase mengizinkan akses |
| Kamera tidak bisa diakses | Pastikan browser mendapat izin kamera; gunakan HTTPS atau `localhost` |
| Wajah tidak terdeteksi | Pastikan pencahayaan cukup, wajah lurus menghadap kamera, tidak terhalang |
| Wajah tidak dikenali | Daftarkan ulang wajah dengan pencahayaan lebih baik, atau turunkan `FACE_MATCH_THRESHOLD` |

---

## 👨‍💻 Kontribusi

Pull request sangat diterima! Untuk perubahan besar, buka issue terlebih dahulu untuk mendiskusikan apa yang ingin diubah.

```bash
git checkout -b feature/fitur-baru
git commit -m "feat: tambahkan fitur baru"
git push origin feature/fitur-baru
```

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **MIT License**.

---

<div align="center">

**ABSENSI AI — AILA** | Dibuat dengan ❤️ menggunakan Python + Flask + OpenCV + Firebase

[![GitHub](https://img.shields.io/badge/GitHub-maupulang%2FABSENSI--AI-181717?style=flat-square&logo=github)](https://github.com/maupulang/ABSENSI-AI)

</div>
