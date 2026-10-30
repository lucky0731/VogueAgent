import { getGoogleClientId, googleLogin } from '../../services/api_v2.js';
import { showToast } from '../../utils/toast.js';

let scriptLoadPromise = null;

function loadGoogleScript() {
    if (window.google?.accounts?.id) return Promise.resolve();
    if (!scriptLoadPromise) {
        scriptLoadPromise = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.onload = resolve;
            script.onerror = () => reject(new Error('Failed to load Google Sign-In'));
            document.head.appendChild(script);
        });
    }
    return scriptLoadPromise;
}

/** Container Google's script renders its own button into (hidden until configured). */
export function renderGoogleSignIn() {
    return `<div class="google-wrap" id="googleWrap" hidden>
      <div id="googleSignInDiv" class="google-signin"></div>
      <div class="divider"><span>or</span></div>
    </div>`;
}

/**
 * Mount the Google button if GOOGLE_CLIENT_ID is configured on the server;
 * otherwise do nothing, and the password form works on its own.
 */
export async function setupGoogleSignIn(onSuccess) {
    const container = document.getElementById('googleSignInDiv');
    if (!container) return;

    const clientId = await getGoogleClientId();
    if (!clientId || !clientId.endsWith('.apps.googleusercontent.com')) return;
    try {
        await loadGoogleScript();
    } catch (err) {
        console.error(err);
        return;
    }
    if (!document.body.contains(container)) return; // user navigated away meanwhile

    window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
            try {
                onSuccess(await googleLogin(response.credential));
            } catch (err) {
                showToast(err.message, 'error');
            }
        },
    });
    document.getElementById('googleWrap').hidden = false;
    window.google.accounts.id.renderButton(container, { theme: 'outline', size: 'large', width: 300, shape: 'pill' });
}
