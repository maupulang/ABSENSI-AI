/**
 * ABSENSI AI - Main UI JavaScript Utilities
 */

// Helper to show modern floating toast
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-5 right-5 z-50 px-4 py-3 rounded-2xl shadow-xl border text-sm font-semibold flex items-center space-x-2.5 transition-all transform duration-300 translate-y-10 opacity-0`;
    
    let bg = 'bg-white text-slate-800 border-slate-200';
    let icon = 'fa-circle-info text-blue-500';

    if (type === 'success') {
        bg = 'bg-emerald-50 text-emerald-900 border-emerald-200';
        icon = 'fa-circle-check text-emerald-600';
    } else if (type === 'error' || type === 'danger') {
        bg = 'bg-rose-50 text-rose-900 border-rose-200';
        icon = 'fa-circle-exclamation text-rose-600';
    } else if (type === 'warning') {
        bg = 'bg-amber-50 text-amber-900 border-amber-200';
        icon = 'fa-triangle-exclamation text-amber-600';
    }

    toast.className += ` ${bg}`;
    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-y-10', 'opacity-0');
    }, 50);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('translate-y-10', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
