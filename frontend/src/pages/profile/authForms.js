import { state, login } from '../../services/state.js';
import { loginUser, registerUser } from '../../services/api_v2.js';
import { refreshCartCount } from '../../services/cartCount.js';
import { navigate } from '../../services/nav.js';
import { renderGoogleSignIn, setupGoogleSignIn } from './googleSignIn.js';
import { showToast } from '../../utils/toast.js';
import { logoSvg } from '../../components/Logo.js';

/** Login and registration, shown when logged out. state.ui.authMode is 'login' | 'register'. */
export function renderAuthForms() {
    const isLogin = state.ui.authMode === 'login';
    return `
    <div class="container page auth">
      <div class="auth-art" aria-hidden="true">
        <div class="auth-logo">${logoSvg({ tone: 'light' })}</div>
        <p>Your bag and orders are saved to your account, so they follow you from phone to laptop.</p>
      </div>
      <div class="panel auth-panel">
        <div class="tabs" role="tablist">
          <button role="tab" aria-selected="${isLogin}" class="tab ${isLogin ? 'active' : ''}" id="showLogin">Log in</button>
          <button role="tab" aria-selected="${!isLogin}" class="tab ${!isLogin ? 'active' : ''}" id="showRegister">Create account</button>
        </div>
        ${isLogin ? `
        <form id="loginForm" novalidate>
          ${renderGoogleSignIn()}
          <label class="field"><span>Email or username</span>
            <input class="input" id="loginIdentifier" autocomplete="username" required /></label>
          <label class="field"><span>Password</span>
            <input class="input" type="password" id="loginPassword" autocomplete="current-password" required /></label>
          <button id="loginBtn" class="btn btn-primary btn-block btn-lg" type="submit">Log in</button>
        </form>` : `
        <form id="registerForm" novalidate>
          <label class="field"><span>Username</span>
            <input class="input" id="regUsername" autocomplete="username" required minlength="3" maxlength="30" />
            <small>3–30 characters: letters, numbers, dot, dash or underscore.</small></label>
          <label class="field"><span>Email</span>
            <input class="input" type="email" id="regEmail" autocomplete="email" required /></label>
          <label class="field"><span>Password</span>
            <input class="input" type="password" id="regPassword" autocomplete="new-password" required minlength="6" />
            <small>At least 6 characters.</small></label>
          <button id="registerBtn" class="btn btn-primary btn-block btn-lg" type="submit">Create account</button>
        </form>`}
      </div>
    </div>`;
}

async function afterAuth(result, rerender, message) {
    login(result);
    await refreshCartCount();
    showToast(message);
    const next = state.afterLogin;
    state.afterLogin = null;
    if (next && next !== '#/profile') navigate(next);
    else rerender();
}

export function setupAuthFormsEvents(rerender) {
    if (state.ui.authMode === 'login') {
        setupGoogleSignIn((result) => afterAuth(result, rerender, `Welcome, ${result.username}!`));
    }

    document.getElementById('showRegister')?.addEventListener('click', () => {
        state.ui.authMode = 'register';
        rerender();
    });
    document.getElementById('showLogin')?.addEventListener('click', () => {
        state.ui.authMode = 'login';
        rerender();
    });

    document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const identifier = document.getElementById('loginIdentifier').value.trim();
        const password = document.getElementById('loginPassword').value;
        if (!identifier || !password) {
            showToast('Enter your email or username and your password.', 'info');
            return;
        }
        const btn = document.getElementById('loginBtn');
        btn.textContent = 'Logging in…';
        btn.disabled = true;
        try {
            const result = await loginUser(identifier, password);
            await afterAuth(result, rerender, `Welcome back, ${result.username}!`);
        } catch (err) {
            showToast(err.message, 'error');
            btn.textContent = 'Log in';
            btn.disabled = false;
        }
    });

    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        if (!username || !email || !password) {
            showToast('Fill in username, email and password.', 'info');
            return;
        }
        const btn = document.getElementById('registerBtn');
        btn.textContent = 'Creating account…';
        btn.disabled = true;
        try {
            const result = await registerUser(username, email, password);
            await afterAuth(result, rerender, 'Account created — you are logged in.');
        } catch (err) {
            showToast(err.message, 'error');
            btn.textContent = 'Create account';
            btn.disabled = false;
        }
    });
}
