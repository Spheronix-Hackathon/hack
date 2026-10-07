document.addEventListener('DOMContentLoaded', () => {
    // Utility function: Debounce to prevent lag during fast typing
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // 1. Populate States and Districts
    const stateSelect = document.getElementById('state');
    const districtSelect = document.getElementById('district');
    
    // Add states
    Object.keys(StateAndDistricts).sort().forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        stateSelect.appendChild(option);
    });

    // Handle state change
    stateSelect.addEventListener('change', (e) => {
        const selectedState = e.target.value;
        districtSelect.innerHTML = '<option value="">Select District</option>';
        
        if (selectedState && StateAndDistricts[selectedState]) {
            StateAndDistricts[selectedState].sort().forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });
        }
    });

    // 2. Uppercase inputs (optimized to trigger on blur to prevent cursor jump)
    document.querySelectorAll('.uppercase-input').forEach(input => {
        input.addEventListener('blur', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    });

    // 3. Phase Switching
    const phase1 = document.getElementById('phase-1');
    const phase2 = document.getElementById('phase-2');
    const step1 = document.getElementById('step-indicator-1');
    const step2 = document.getElementById('step-indicator-2');
    const form = document.getElementById('nodalRegistrationForm');

    // Auto-Save Draft
    const draftKey = 'nodalRegistrationDraft';
    
    function saveDraft() {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        delete data.emailOtp;
        localStorage.setItem(draftKey, JSON.stringify(data));
    }

    const debouncedSaveDraft = debounce(saveDraft, 500);
    form.addEventListener('input', debouncedSaveDraft);
    form.addEventListener('change', saveDraft);

    function loadDraft() {
        const saved = localStorage.getItem(draftKey);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                
                if (data.state) {
                    document.getElementById('state').value = data.state;
                    stateSelect.dispatchEvent(new Event('change'));
                }
                
                Object.keys(data).forEach(key => {
                    const el = form.elements[key];
                    if (el) {
                        el.value = data[key];
                        if (key === 'category') el.dispatchEvent(new Event('change'));
                    }
                });
            } catch (e) {
                console.error("Failed to load draft", e);
            }
        }
    }
    
    loadDraft();

    // Prevent implicit submission on Enter key which triggers browser validation on hidden fields
    form.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
        }
    });

    document.getElementById('btn-next').addEventListener('click', () => {
        // Simple HTML5 validation check for phase 1 elements
        let valid = true;
        phase1.querySelectorAll('input, select').forEach(el => {
            if (!el.checkValidity()) {
                valid = false;
                el.reportValidity();
            }
        });
        
        if (valid) {
            phase1.style.display = 'none';
            phase2.style.display = 'grid';
            step1.classList.remove('active');
            step2.classList.add('active');
        }
    });

    document.getElementById('btn-back').addEventListener('click', () => {
        phase2.style.display = 'none';
        phase1.style.display = 'grid';
        step2.classList.remove('active');
        step1.classList.add('active');
    });

    // 4. Category "Others" logic
    const categorySelect = document.getElementById('category');
    const specifyCategoryGroup = document.getElementById('specifyCategoryGroup');
    const specifyCategoryInput = document.getElementById('specifyCategory');

    categorySelect.addEventListener('change', (e) => {
        if (e.target.value === 'Others') {
            specifyCategoryGroup.style.display = 'block';
            specifyCategoryInput.required = true;
        } else {
            specifyCategoryGroup.style.display = 'none';
            specifyCategoryInput.required = false;
            specifyCategoryInput.value = '';
        }
    });

    // 5. Verification Logic
    async function requestOtp(url, contact, statusEl, groupEl) {
        statusEl.textContent = 'Sending OTP...';
        statusEl.className = 'status-msg';
        
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contact: contact })
            });
            const data = await res.json();
            
            if (res.ok) {
                statusEl.textContent = data.message || 'OTP Sent successfully. Please check.';
                statusEl.className = 'status-msg success';
                groupEl.style.display = 'block';
                groupEl.querySelector('input').required = true;
                return true;
            } else {
                throw new Error(data.detail || 'Failed to send OTP');
            }
        } catch (err) {
            statusEl.textContent = err.message;
            statusEl.className = 'status-msg error';
            return false;
        }
    }

    document.getElementById('btn-verify-email').addEventListener('click', async () => {
        const emailInput = document.getElementById('principalEmail');
        const email = emailInput.value;
        if (!email) {
            alert("Please enter Principal's email first.");
            return;
        }
        if (emailInput.validationMessage) {
            alert(emailInput.validationMessage);
            return;
        }

        // Force a synchronous check to prevent race condition between blur and click
        try {
            const res = await fetch('/api/register/check-exists', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field: 'principalEmail', value: email.trim() })
            });
            const data = await res.json();
            if (data.exists) {
                alert("This Email Address is already registered.");
                return;
            }
        } catch(e) {
            console.error(e);
        }

        requestOtp('/api/register/send-email-otp', email, 
            document.getElementById('email-status'), 
            document.getElementById('email-otp-group'));
    });

    // 6. Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let valid = true;
        form.querySelectorAll('input, select').forEach(el => {
            if (!el.checkValidity()) {
                valid = false;
                el.reportValidity();
            }
        });
        
        if (!valid) return;
        
        const btnSubmit = document.getElementById('btn-submit');
        btnSubmit.disabled = true;
        btnSubmit.textContent = 'Submitting...';

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const res = await fetch('/api/register/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await res.json();
            
            if (res.ok) {
                localStorage.removeItem(draftKey);
                form.style.display = 'none';
                document.getElementById('success-message').style.display = 'block';
            } else {
                let errMsg = 'Registration failed';
                if (result.detail) {
                    if (typeof result.detail === 'string') {
                        errMsg = result.detail;
                    } else if (Array.isArray(result.detail)) {
                        errMsg = result.detail.map(e => `${e.loc[e.loc.length-1]}: ${e.msg}`).join('\\n');
                    } else {
                        errMsg = JSON.stringify(result.detail);
                    }
                }
                throw new Error(errMsg);
            }
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.textContent = 'Submit Registration';
        }
    });

    // 7. Real-time Uniqueness Validation
    async function validateUniqueness(inputEl, fieldName, errorMsg) {
        if (!inputEl.value.trim()) return;
        
        try {
            const res = await fetch('/api/register/check-exists', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field: fieldName, value: inputEl.value.trim() })
            });
            const data = await res.json();
            
            const formGroup = inputEl.closest('.field');
            let errorEl = formGroup.querySelector('.unique-error');
            
            if (!errorEl) {
                errorEl = document.createElement('small');
                errorEl.className = 'unique-error status-msg error';
                formGroup.appendChild(errorEl);
            }
            
            if (res.ok && data.exists) {
                errorEl.textContent = errorMsg;
                errorEl.style.display = 'block';
                inputEl.setCustomValidity(errorMsg);
            } else {
                errorEl.style.display = 'none';
                inputEl.setCustomValidity('');
            }
        } catch (e) {
            console.error("Validation error", e);
        }
    }

    const uniqueFields = [
        { id: 'collegeCode', msg: 'This College Code already exists.' },
        { id: 'principalName', msg: 'A registration with this Principal Name already exists.' },
        { id: 'principalEmail', msg: 'A registration with this Principal Gmail Address already exists.' },
        { id: 'principalMobile', msg: 'A registration with this Principal Mobile Number already exists.' },
        { id: 'nodalOfficerName', msg: 'A registration with this Nodal Officer Name already exists.' },
        { id: 'nodalOfficerEmail', msg: 'A registration with this Nodal Officer Gmail Address already exists.' },
        { id: 'nodalOfficerMobile', msg: 'A registration with this Nodal Officer Mobile Number already exists.' }
    ];

    uniqueFields.forEach(f => {
        const el = document.getElementById(f.id);
        if (el) {
            el.addEventListener('blur', () => validateUniqueness(el, f.id, f.msg));
            // Also validate on input using debounce to prevent heavy API spam
            const debouncedValidate = debounce(() => {
                if(el.validationMessage) {
                    validateUniqueness(el, f.id, f.msg);
                }
            }, 600);
            el.addEventListener('input', debouncedValidate);
        }
    });

});
