/**
 * ABSENSI AI - Face Recognition & Camera Scanner Client
 */

let cameraStream = null;
let currentFacingMode = "user"; // 'user' or 'environment'
let isAnalyzing = false;

async function startCamera() {
    stopCamera();

    const videoEl = document.getElementById("webcam-video");
    const placeholder = document.getElementById("camera-placeholder");
    const statusDot = document.getElementById("camera-status-dot");
    const statusPing = document.getElementById("camera-status-ping");
    const statusText = document.getElementById("camera-status-text");
    const toggleBtnText = document.getElementById("btn-toggle-camera-text");
    const captureBtn = document.getElementById("btn-capture");
    const laser = document.getElementById("scanner-laser");

    try {
        const constraints = {
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: currentFacingMode
            },
            audio: false
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        cameraStream = stream;
        videoEl.srcObject = stream;
        videoEl.onloadedmetadata = () => {
            videoEl.play();
            placeholder.classList.add("hidden");
            statusDot.className = "relative inline-flex rounded-full h-3 w-3 bg-emerald-500";
            statusPing.classList.remove("hidden");
            statusText.innerText = "Kamera Aktif & Memindai";
            toggleBtnText.innerText = "Matikan Kamera";
            captureBtn.disabled = false;
            laser.classList.remove("hidden");
            laser.classList.add("scanner-laser-active");
        };
    } catch (err) {
        console.error("Camera access error:", err);
        statusText.innerText = "Kamera Gagal";
        alert("Tidak dapat mengakses kamera: " + (err.message || "Izin akses kamera ditolak."));
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    const videoEl = document.getElementById("webcam-video");
    if (videoEl) videoEl.srcObject = null;

    const placeholder = document.getElementById("camera-placeholder");
    const statusDot = document.getElementById("camera-status-dot");
    const statusPing = document.getElementById("camera-status-ping");
    const statusText = document.getElementById("camera-status-text");
    const toggleBtnText = document.getElementById("btn-toggle-camera-text");
    const captureBtn = document.getElementById("btn-capture");
    const laser = document.getElementById("scanner-laser");

    if (placeholder) placeholder.classList.remove("hidden");
    if (statusDot) statusDot.className = "relative inline-flex rounded-full h-3 w-3 bg-slate-500";
    if (statusPing) statusPing.classList.add("hidden");
    if (statusText) statusText.innerText = "Kamera Mati";
    if (toggleBtnText) toggleBtnText.innerText = "Aktifkan Kamera";
    if (captureBtn) captureBtn.disabled = true;
    if (laser) {
        laser.classList.add("hidden");
        laser.classList.remove("scanner-laser-active");
    }
}

function toggleCamera() {
    if (cameraStream) {
        stopCamera();
    } else {
        startCamera();
    }
}

function switchCamera() {
    currentFacingMode = (currentFacingMode === "user") ? "environment" : "user";
    if (cameraStream) {
        startCamera();
    }
}

async function captureAndRecognize() {
    if (isAnalyzing) return;

    const videoEl = document.getElementById("webcam-video");
    const canvas = document.getElementById("capture-canvas");
    const indicator = document.getElementById("processing-indicator");
    const captureBtn = document.getElementById("btn-capture");
    const resultBox = document.getElementById("result-box");

    if (!videoEl || !videoEl.videoWidth) {
        alert("Kamera belum siap.");
        return;
    }

    isAnalyzing = true;
    indicator.classList.remove("hidden");
    captureBtn.disabled = true;

    try {
        // Draw frame to offscreen canvas
        canvas.width = videoEl.videoWidth;
        canvas.height = videoEl.videoHeight;
        const ctx = canvas.getContext("2d");

        // If user-facing mode, un-mirror horizontally for accurate matching
        if (currentFacingMode === "user") {
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
        }
        ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

        const base64Image = canvas.toDataURL("image/jpeg", 0.9);

        // Send to backend Face Recognition Attendance API
        const response = await fetch("/api/attendance/face", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image: base64Image
            })
        });

        const resData = await response.json();
        renderResult(resData);

    } catch (err) {
        console.error("Attendance request failed:", err);
        renderResult({
            success: false,
            code: "NETWORK_ERROR",
            message: "Gagal terhubung ke server absensi: " + err.message
        });
    } finally {
        isAnalyzing = false;
        indicator.classList.add("hidden");
        captureBtn.disabled = false;
    }
}

function renderResult(res) {
    const resultBox = document.getElementById("result-box");
    resultBox.classList.remove("hidden");

    let cardHtml = "";

    if (res.success) {
        // SUCCESS CARD
        const d = res.data || {};
        cardHtml = `
            <div class="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-3xl p-6 sm:p-8 text-white shadow-2xl animate-[fadeIn_0.3s_ease-out] relative overflow-hidden">
                <div class="flex flex-col md:flex-row items-center justify-between gap-6">
                    <div class="flex items-center space-x-5">
                        <div class="w-16 h-16 rounded-2xl bg-white text-emerald-600 flex items-center justify-center text-3xl font-extrabold shadow-lg">
                            <i class="fa-solid fa-check"></i>
                        </div>
                        <div>
                            <div class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/20 text-xs font-bold uppercase tracking-wider mb-1">
                                <i class="fa-solid fa-circle-check"></i>
                                <span>ABSENSI BERHASIL</span>
                            </div>
                            <h3 class="text-2xl font-black">${d.nama || 'Siswa'}</h3>
                            <p class="text-xs text-emerald-100">NIS: <strong class="text-white">${d.nis}</strong> | Kelas: <strong class="text-white">${d.kelas}</strong></p>
                        </div>
                    </div>

                    <div class="flex items-center space-x-4 bg-white/15 backdrop-blur-md p-4 rounded-2xl border border-white/20">
                        <div class="text-center px-3 border-r border-white/20">
                            <div class="text-[10px] text-emerald-100 uppercase tracking-wider font-semibold">Status</div>
                            <div class="text-lg font-black text-white">${d.status}</div>
                        </div>
                        <div class="text-center px-3">
                            <div class="text-[10px] text-emerald-100 uppercase tracking-wider font-semibold">Waktu Masuk</div>
                            <div class="text-lg font-mono font-black text-white">${d.waktu}</div>
                        </div>
                    </div>
                </div>

                <div class="mt-6 pt-4 border-t border-white/20 flex items-center justify-between">
                    <span class="text-xs text-emerald-100 flex items-center">
                        <i class="fa-solid fa-cloud-check mr-1.5"></i> Tersimpan otomatis ke Firebase Realtime Database
                    </span>
                    <a href="/student/dashboard" class="px-4 py-2 rounded-xl bg-white text-emerald-700 text-xs font-bold hover:bg-emerald-50 transition-all">
                        Lihat Dashboard Siswa
                    </a>
                </div>
            </div>
        `;
    } else if (res.code === "ALREADY_ATTENDED") {
        // ALREADY ATTENDED CARD
        const d = res.data || {};
        cardHtml = `
            <div class="bg-amber-500 rounded-3xl p-6 sm:p-8 text-white shadow-2xl animate-[fadeIn_0.3s_ease-out]">
                <div class="flex items-center space-x-5">
                    <div class="w-16 h-16 rounded-2xl bg-white text-amber-600 flex items-center justify-center text-3xl font-extrabold shadow-lg flex-shrink-0">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                    </div>
                    <div>
                        <div class="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-white/20 text-xs font-bold tracking-wider mb-1">
                            <span>SUDAH ABSEN</span>
                        </div>
                        <h3 class="text-xl sm:text-2xl font-black">${res.message}</h3>
                        <p class="text-xs text-amber-100 mt-1">
                            ${d.nama ? `Siswa: <strong>${d.nama}</strong> (${d.nis} - ${d.kelas}) tercatat pada jam <strong>${d.waktu || '-'}</strong>.` : ''}
                        </p>
                    </div>
                </div>
            </div>
        `;
    } else {
        // ERROR / NOT RECOGNIZED CARD
        cardHtml = `
            <div class="bg-rose-600 rounded-3xl p-6 sm:p-8 text-white shadow-2xl animate-[fadeIn_0.3s_ease-out]">
                <div class="flex items-center space-x-5">
                    <div class="w-16 h-16 rounded-2xl bg-white text-rose-600 flex items-center justify-center text-3xl font-extrabold shadow-lg flex-shrink-0">
                        <i class="fa-solid fa-xmark"></i>
                    </div>
                    <div>
                        <div class="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-white/20 text-xs font-bold tracking-wider mb-1">
                            <span>VERIFIKASI GAGAL</span>
                        </div>
                        <h3 class="text-xl sm:text-2xl font-black">${res.message || 'Wajah tidak dikenali.'}</h3>
                        <p class="text-xs text-rose-100 mt-1">
                            Pastikan wajah Anda telah didaftarkan oleh administrator dan posisikan wajah lurus di dalam bingkai kamera.
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    resultBox.innerHTML = cardHtml;
    resultBox.scrollIntoView({ behavior: "smooth" });
}

// Automatically start camera on page load if user is on attendance page
document.addEventListener("DOMContentLoaded", () => {
    // Optionally auto start camera
    startCamera();
});
