/** Small non-blocking notifications (instead of alert()). */
export function showToast(message, type = 'success', timeout = 3200) {
    const host = document.getElementById('toast-host');
    if (!host) return;
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.textContent = message;
    host.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast--in'));
    setTimeout(() => {
        toast.classList.remove('toast--in');
        setTimeout(() => toast.remove(), 300);
    }, timeout);
}
