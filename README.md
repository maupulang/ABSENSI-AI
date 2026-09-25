# ABSENSI AI - Sistem Absensi Berbasis Face Recognition & Firebase Realtime Database

Aplikasi web modern untuk manajemen presensi siswa menggunakan kamera dan **AI Face Recognition** (OpenCV YuNet + SFace 128-d Face Embedding) yang terintegrasi langsung dengan **Firebase Realtime Database**.

---

## 🌟 Fitur Utama

### 1. Role Siswa
* **Login Siswa**: Otentikasi aman menggunakan email dan kata sandi yang telah di-hash.
* **Dashboard Siswa**:
  * Status absensi hari ini (Hadir / Terlambat / Belum Hadir).
  * Statistik kehadiran pribadi (Total Hadir, Terlambat, Izin/Sakit, Total Absensi).
  * Log 5 riwayat absensi terkini.
* **Absensi Kamera AI**:
  * Pindai wajah langsung dari kamera webcam browser dengan animasi laser scanner.
  * Ekstraksi **128-dimensional Face Embedding** secara real-time.
  * Validasi kemiripan identitas wajah siswa dengan threshold yang dapat dikonfigurasi.
  * **Pencegahan Absensi Ganda**: Menolak pengulangan absensi pada tanggal yang sama (*"Anda sudah melakukan absensi hari ini"*).
  * Penentuan otomatis status **Hadir** atau **Terlambat** berdasarkan batas jam masuk sekolah (misal: 07:15).
* **Riwayat Absensi**:
  * Menampilkan seluruh rekam jejak presensi siswa.
  * Filter pencarian dinamis berdasarkan tanggal dan status.

### 2. Role Admin
* **Dashboard Administrator**:
  * Metrik KPI: Total Siswa Aktif, Hadir Hari Ini, Terlambat, dan Belum Hadir / Alpha.
  * Bar persentase tingkat kehadiran sekolah secara real-time.
  * Log daftar kehadiran hari ini beserta timestamp dan metode absensi.
* **Manajemen Siswa (CRUD)**:
  * Tambah siswa baru (NIS, Nama Lengkap, Kelas, Email, Kata Sandi, Status).
  * Edit profil siswa.
  * Hapus siswa dengan konfirmasi.
  * Indikator status wajah AI: *Terdaftar* atau *Belum Ada Wajah*.
  * Pencarian data siswa secara instan.
* **Registrasi Wajah Siswa**:
  * Pilih siswa dari daftar.
  * Pilihan mode: **Kamera Langsung (Webcam)** atau **Unggah File Foto**.
  * Validasi deteksi wajah otomatis.
  * Ekstraksi dan penyimpanan vector embedding ke profil siswa di Firebase.
* **Data Presensi & Presensi Manual**:
  * Pemilihan tanggal untuk melihat daftar absensi pada hari tertentu.
  * Fitur pencatatan presensi manual (Hadir, Terlambat, Izin, Sakit, Alpha) dengan catatan.
* **Laporan & Ekspor**:
  * Filter multi-kriteria: Rentang Tanggal (Mulai - Selesai), Kelas, Siswa, dan Status Kehadiran.
  * Ekspor laporan absensi ke format **CSV / Excel** dalam satu klik.

---

## 🏗️ Struktur Project

```text
absensi-ai/
├── app.py                      # Server Flask, routing, controller, & REST API
├── firebase_config.py          # Adapter Firebase (Admin SDK + fallback REST API)
├── face_recognition_service.py # Layanan AI Face Recognition (YuNet + SFace)
├── attendance_service.py       # Logika bisnis absensi & analitik Firebase
├── seed_data.py                # Script inisialisasi akun admin & siswa contoh
├── database.rules.json         # Firebase Realtime Database Security Rules
├── requirements.txt            # Daftar pustaka Python yang dibutuhkan
├── .env                        # Konfigurasi environment lokal (rahasia)
├── .env.example                # Template konfigurasi environment
├── .gitignore                  # Berkas yang diabaikan oleh Git
├── models/                     # Model AI Face Detection & Recognition ONNX
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
├── static/
│   ├── css/
│   │   └── style.css           # Styling kustom & animasi laser scan
│   └── js/
│       ├── main.js             # Utilitas notifikasi toast & interaksi UI
│       └── face_capture.js     # Logika webcam scanner & request absensi AI
├── templates/
│   ├── base.html               # Layout utama dengan sidebar & navbar responsif
│   ├── login.html              # Halaman login modern
│   ├── student/
│   │   ├── dashboard.html      # Dashboard siswa
│   │   ├── attendance.html     # Halaman scan wajah absensi
│   │   └── history.html        # Riwayat absensi siswa
│   └── admin/
│       ├── dashboard.html      # Dashboard utama admin
│       ├── students.html       # Kelola data siswa (CRUD)
│       ├── register_face.html  # Registrasi wajah siswa
│       ├── attendance.html     # Kelola absensi per tanggal
│       └── reports.html        # Laporan & filter absensi
└── README.md                   # Dokumentasi instalasi dan panduan
```

---

## 🧠 Alur Kerja AI Face Recognition

```text
Kamera Browser (Webcam)
          ↓
Capture Frame (Canvas Base64)
          ↓
Kirim POST ke /api/attendance/face
          ↓
Deteksi Wajah (OpenCV YuNet ONNX)
          ↓
Ekstraksi Face Embedding 128-D (OpenCV SFace ONNX)
          ↓
Perhitungan Jarak Kosinus (Cosine Distance) dengan Data Siswa
          ↓
Apakah Cocok dengan Threshold (<= 0.45)?
  ├─ Tidak ──> Respon: "Wajah tidak dikenali."
  └─ Ya ────> Validasi Identitas Siswa
                    ↓
              Cek Absensi Hari Ini di Firebase
                ├─ Sudah Absen ─> Respon: "Anda sudah melakukan absensi hari ini."
                └─ Belum Absen ─> Tentukan Status (Hadir / Terlambat)
                                        ↓
                                  Simpan ke Firebase:
                                  attendance/YYYY-MM-DD/UID/
                                        ↓
                                  Tampilkan Hasil Berhasil ke Layar
```

---

## 🗄️ Skema Data Firebase Realtime Database

### 1. Data Siswa (`students/{UID}`)
```json
{
  "nis": "2026101",
  "nama": "Budi Santoso",
  "kelas": "XII RPL 1",
  "email": "budi@absensi.ai",
  "role": "siswa",
  "status": "aktif",
  "foto": "",
  "faceEmbedding": [0.023, -0.045, 0.128, "... 128 float values ..."],
  "password_hash": "scrypt:32768:8:1$..."
}
```

### 2. Data Absensi (`attendance/{YYYY-MM-DD}/{UID}`)
```json
{
  "nis": "2026101",
  "nama": "Budi Santoso",
  "kelas": "XII RPL 1",
  "tanggal": "2026-09-25",
  "waktu": "07:05:12",
  "status": "Hadir",
  "timestamp": 1790323512,
  "method": "Face Recognition"
}
```

---

## ⚙️ Konfigurasi Environment (`.env`)

Salin file `.env.example` menjadi `.env`:

```ini
# Kunci rahasia session Flask
SECRET_KEY=absensi_ai_super_secret_key_2026_change_in_production
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# Konfigurasi Firebase Realtime Database
FIREBASE_DATABASE_URL=https://absensi-ai-a8281-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=absensi-ai-a8281
FIREBASE_STORAGE_BUCKET=absensi-ai-a8281.firebasestorage.app
FIREBASE_SERVICE_ACCOUNT_KEY=serviceAccountKey.json

# Pengaturan Face Recognition
# Ambang batas kemiripan kosinus (0.40 - 0.50 direkomendasikan)
FACE_MATCH_THRESHOLD=0.45

# Pengaturan Jam Absensi Masuk
ATTENDANCE_START_TIME=06:00
ATTENDANCE_LATE_TIME=07:15
ATTENDANCE_END_TIME=17:00
```

> **Catatan Autentikasi Firebase**:
> Aplikasi mendukung dual-mode Firebase. Jika Anda memiliki `serviceAccountKey.json` dari Google Cloud / Firebase Console, letakkan di folder root project. Jika belum ada, sistem secara cerdas menggunakan Firebase Realtime Database REST API client secara otomatis!

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Prasyarat
* Python 3.10 atau 3.11
* Koneksi internet (untuk akses Firebase Realtime Database)
* Webcam / Kamera terpasang di perangkat

### 2. Siapkan Virtual Environment
Buka terminal / PowerShell di direktori project:

```powershell
# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment di Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependensi
```powershell
pip install -r requirements.txt
```

### 4. Inisialisasi Data Default (Seeder)
Jalankan script untuk membuat akun Admin dan data siswa contoh di Firebase:

```powershell
python seed_data.py
```

Data akun awal:
* **Admin**:
  * Email: `admin@absensi.ai`
  * Sandi: `admin123`
* **Siswa Contoh**:
  * Email: `budi@absensi.ai` (Sandi: `123456`)
  * Email: `siti@absensi.ai` (Sandi: `123456`)

### 5. Jalankan Server Flask
```powershell
python app.py
```

Aplikasi akan aktif di:
👉 **http://localhost:5000** atau **http://127.0.0.1:5000**

---

## 🔒 Firebase Security Rules

Gunakan aturan berikut di menu **Realtime Database > Rules** pada Firebase Console:

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
        ".read": "auth != null && (root.child('students').child(auth.uid).child('role').val() === 'admin' || data.child(auth.uid).exists())",
        "$uid": {
          ".read": "auth != null && (auth.uid === $uid || root.child('students').child(auth.uid).child('role').val() === 'admin')",
          ".write": "auth != null && (auth.uid === $uid || root.child('students').child(auth.uid).child('role').val() === 'admin')",
          ".validate": "newData.hasChildren(['nis', 'nama', 'kelas', 'tanggal', 'waktu', 'status', 'timestamp', 'method']) && (!data.exists() || root.child('students').child(auth.uid).child('role').val() === 'admin')"
        }
      }
    }
  }
}
```

---

## 📝 Ringkasan Endpoint Aplikasi

| Rute URL | Role | Deskripsi |
|---|---|---|
| `/login` | Publik | Halaman login untuk Siswa dan Admin |
| `/logout` | Semua | Menghapus sesi dan keluar |
| `/student/dashboard` | Siswa | Dashboard rekapitulasi kehadiran pribadi |
| `/student/attendance` | Siswa | Pemindai wajah kamera AI untuk presensi |
| `/student/history` | Siswa | Riwayat presensi mandiri |
| `/admin/dashboard` | Admin | Dashboard metrik & analitik kehadiran |
| `/admin/students` | Admin | CRUD pengelolaan data siswa |
| `/admin/register-face` | Admin | Pendaftaran wajah siswa (Webcam/Upload) |
| `/admin/attendance` | Admin | Log kehadiran harian & presensi manual |
| `/admin/reports` | Admin | Laporan berfilter multi-kategori |
| `/admin/reports/export` | Admin | Unduh laporan kehadiran dalam format CSV |
| `/api/attendance/face` | API | Endpoint proses AI Face Recognition |
| `/api/admin/students` | API | REST endpoint penambahan siswa |
| `/api/admin/register-face` | API | REST endpoint penyimpanan face embedding |
| `/api/admin/attendance/manual`| API | REST endpoint penandaan presensi manual |
