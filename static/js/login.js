document.addEventListener('DOMContentLoaded', () => {
    let currentUserId = null;
    let setupSecret = null;

    const stepLogin = document.getElementById('step-login');
    const stepSetup = document.getElementById('step-2fa-setup');
    const stepVerify = document.getElementById('step-2fa-verify');
    const stepResetMfa = document.getElementById('step-reset-mfa');

    // Toggle panels for MFA Reset
    document.getElementById('lostMfaLink').addEventListener('click', (e) => {
        e.preventDefault();
        stepLogin.style.display = 'none';
        stepResetMfa.style.display = 'block';
    });

    document.getElementById('backToLoginLink').addEventListener('click', (e) => {
        e.preventDefault();
        stepResetMfa.style.display = 'none';
        stepLogin.style.display = 'block';
    });

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('userId').value;
        const password = document.getElementById('password').value;
        const errEl = document.getElementById('loginError');

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId, password })
            });
            const data = await res.json();
            
            if (res.ok) {
                currentUserId = userId;
                stepLogin.style.display = 'none';
                if (data.action === 'setup_2fa') {
                    // Fetch setup QR
                    const setupRes = await fetch('/api/auth/2fa/setup', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ userId })
                    });
                    const setupData = await setupRes.json();
                    setupSecret = setupData.secret;
                    document.getElementById('qrCodeImg').src = setupData.qr_code;
                    stepSetup.style.display = 'block';
                } else {
                    stepVerify.style.display = 'block';
                }
            } else {
                errEl.textContent = data.detail || 'Login failed';
                errEl.style.display = 'block';
            }
        } catch (err) {
            console.error(err);
        }
    });

    document.getElementById('setup2faForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('setupCode').value;
        const errEl = document.getElementById('setupError');

        try {
            const res = await fetch('/api/auth/2fa/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId: currentUserId, code, setupSecret })
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem('adminToken', data.token);
                window.location.href = '/dashboard.html';
            } else {
                errEl.textContent = data.detail || 'Verification failed';
                errEl.style.display = 'block';
            }
        } catch(err) {
            console.error(err);
        }
    });

    document.getElementById('verify2faForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('verifyCode').value;
        const errEl = document.getElementById('verifyError');

        try {
            const res = await fetch('/api/auth/2fa/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId: currentUserId, code })
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem('adminToken', data.token);
                window.location.href = '/dashboard.html';
            } else {
                errEl.textContent = data.detail || 'Verification failed';
                errEl.style.display = 'block';
            }
        } catch(err) {
            console.error(err);
        }
    });


});
