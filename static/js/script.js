/**
 * Spheronix Hackathon Registration System
 * Updated flow: no admin/results, no participant ID, terms-gated payment, merged payment+registration.
 */

document.addEventListener("DOMContentLoaded", async () => {
    async function refreshPublicSettings() {
        try {
            const res = await fetch("/api/public-settings/?_t=" + Date.now(), {
                cache: "no-store",
                headers: { "Cache-Control": "no-cache", "Pragma": "no-cache" }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.registrationAmount !== undefined && data.registrationAmount !== null) {
                    window.GLOBAL_REGISTRATION_AMOUNT = Number(data.registrationAmount);
                }
                const summaryAmountSpan = document.getElementById("summary-amount");
                if (summaryAmountSpan) {
                    summaryAmountSpan.textContent = `₹${window.GLOBAL_REGISTRATION_AMOUNT}`;
                }
                const summaryFeePerPerson = document.getElementById("summary-fee-per-person");
                if (summaryFeePerPerson) {
                    summaryFeePerPerson.textContent = `₹${window.GLOBAL_REGISTRATION_AMOUNT}`;
                }
                let finalUpiId = (data && data.upiId && data.upiId.trim()) ? data.upiId.trim() : "334509931804612@CNRB";
                if (!finalUpiId || finalUpiId.toLowerCase().includes("spheronixhackathon@") || finalUpiId.toLowerCase().includes("example@")) {
                    finalUpiId = "334509931804612@CNRB";
                }
                window.GLOBAL_UPI_ID = finalUpiId;
                window.GLOBAL_UPI_PAYEE = (data && data.upiPayeeName && data.upiPayeeName.trim()) ? data.upiPayeeName.trim() : "Spheronix Hackathon";

                const displayUpiIdEl = document.getElementById("display-upi-id");
                if (displayUpiIdEl) {
                    displayUpiIdEl.textContent = finalUpiId;
                }
                const displayBankUpiIdEl = document.getElementById("display-bank-upi-id");
                if (displayBankUpiIdEl) {
                    displayBankUpiIdEl.textContent = finalUpiId;
                }

                if (data && data.bankName) {
                    window.GLOBAL_BANK_NAME = data.bankName.trim();
                    const el = document.getElementById("display-bank-name");
                    if (el) el.textContent = data.bankName;
                }
                if (data && data.accountHolderName) {
                    window.GLOBAL_ACCOUNT_HOLDER = data.accountHolderName.trim();
                    const el = document.getElementById("display-account-name");
                    if (el) el.textContent = data.accountHolderName;
                }
                if (data && data.accountNumber) {
                    window.GLOBAL_ACCOUNT_NUMBER = data.accountNumber.trim();
                    const el = document.getElementById("display-account-number");
                    if (el) el.textContent = data.accountNumber;
                }
                if (data && data.ifscCode) {
                    window.GLOBAL_IFSC_CODE = data.ifscCode.trim();
                    const el = document.getElementById("display-ifsc-code");
                    if (el) el.textContent = data.ifscCode;
                }
                return data;
            }
        } catch (e) {
            console.error("Failed to fetch dynamic settings", e);
        }
    }

    // Initial load
    await refreshPublicSettings();
    // Live update interval every 10 seconds for real-time admin updates
    setInterval(refreshPublicSettings, 10000);
    const MAX_TEAM_MEMBERS = 4;
    const MIN_TEAM_TOTAL = 2;
    const MAX_TEAM_TOTAL = 5;

    const landingView = document.getElementById("landing-view");
    const registerView = document.getElementById("register-view");
    const instructionsView = document.getElementById("instructions-view");

    const btnStartRegister = document.getElementById("btn-start-register");
    const btnInstructions = document.getElementById("btn-instructions");
    const btnBackLanding = document.getElementById("btn-back-landing");
    const btnBackInstructions = document.getElementById("btn-back-instructions");
    const btnStartFromInstructions = document.getElementById("btn-start-from-instructions");

    const navHome = document.getElementById("nav-home");
    const navInstructions = document.getElementById("nav-instructions");

    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const step4 = document.getElementById("step-4");
    const successView = document.getElementById("success-view");

    const stepIndicator1 = document.getElementById("step-indicator-1");
    const stepIndicator2 = document.getElementById("step-indicator-2");
    const stepIndicator3 = document.getElementById("step-indicator-3");
    const stepIndicator4 = document.getElementById("step-indicator-4");
    const progressLine1 = document.getElementById("progress-line-1");
    const progressLine2 = document.getElementById("progress-line-2");
    const progressLine3 = document.getElementById("progress-line-3");

    const btnGoogleAuth = document.getElementById("btn-google-auth");
    const authError = document.getElementById("auth-error");
    const alreadyRegistered = document.getElementById("already-registered");

    const registrationForm = document.getElementById("registration-form");

    const registrationDateInput = document.getElementById("registrationDate");
    const fullNameInput = document.getElementById("fullName");
    const emailInput = document.getElementById("email");
    const mobileInput = document.getElementById("mobile");
    const branchInput = document.getElementById("branch");
    const otherBranchWrapper = document.getElementById("other-branch-wrapper");
    const otherBranchInput = document.getElementById("otherBranchName");
    const collegeNameInput = document.getElementById("collegeName");
    const collegeSearchInput = document.getElementById("collegeSearch");
    const collegeDropdown = document.getElementById("college-dropdown");
    const otherCollegeWrapper = document.getElementById("other-college-wrapper");
    const otherCollegeInput = document.getElementById("otherCollegeName");
    const cityInput = document.getElementById("city");
    const rollNumberInput = document.getElementById("rollNumber");
    const currentYearInput = document.getElementById("currentYear");
    const otherYearWrapper = document.getElementById("other-year-wrapper");
    const otherCurrentYearInput = document.getElementById("otherCurrentYear");
    const projectSelectedInput = document.getElementById("projectSelected");
    const otherProjectWrapper = document.getElementById("other-project-wrapper");
    const otherProjectInput = document.getElementById("otherProjectSelected");

    const termsAcceptedInput = document.getElementById("termsAccepted");
    const paymentTermsModeText = document.getElementById("payment-terms-mode-text");
    const termsStatusBadge = document.getElementById("terms-status-badge");
    const btnOpenTerms = document.getElementById("btn-open-terms");
    const btnTermsAccept = document.getElementById("btn-terms-accept");
    const btnTermsReject = document.getElementById("btn-terms-reject");
    const termsModal = document.getElementById("terms-modal");

    const liveUpdateToast = document.getElementById("live-update-toast");
    const toastTitle = document.getElementById("toast-title");
    const toastMessage = document.getElementById("toast-message");
    const toastClose = document.getElementById("toast-close");

    const teamNameInput = document.getElementById("teamName");
    const leaderInfoEl = document.getElementById("leader-info");
    const leaderCollegeInfoEl = document.getElementById("leader-college-info");
    const btnAddMember = document.getElementById("btn-add-member");
    const memberLimitMsg = document.getElementById("member-limit-msg");
    const btnBackStep2 = document.getElementById("btn-back-step2");
    const btnNextPayment = document.getElementById("btn-next-payment");

    const btnSubmitFinal = document.getElementById("btn-submit-final");
    const btnBackStep3 = document.getElementById("btn-back-step3");

    // UPI Payment Elements
    const upiPaymentPanel = document.getElementById("upi-payment-panel");
    const upiQrImage = document.getElementById("upi-qr-image");
    const qrLoadingSpinner = document.getElementById("qr-loading-spinner");
    const qrDisplayAmount = document.getElementById("qr-display-amount");
    const displayUpiId = document.getElementById("display-upi-id");
    const btnCopyUpi = document.getElementById("btn-copy-upi");
    const btnUpiMobilePay = document.getElementById("btn-upi-mobile-pay");
    const upiUtrInput = document.getElementById("upi-utr-input");
    const btnVerifyUpi = document.getElementById("btn-verify-upi");
    const errorUpiUtr = document.getElementById("error-upiUtr");

    const receiptDropzone = document.getElementById("receipt-dropzone");
    const receiptFileInput = document.getElementById("receipt-file-input");
    const dropzoneContent = document.getElementById("dropzone-content");
    const receiptPreviewCard = document.getElementById("receipt-preview-card");
    const previewFilename = document.getElementById("preview-filename");
    const previewFilesize = document.getElementById("preview-filesize");
    const previewUploadStatus = document.getElementById("preview-upload-status");
    const previewIcon = document.getElementById("preview-icon");
    const btnRemoveReceipt = document.getElementById("btn-remove-receipt");
    const btnBrowseFile = document.getElementById("btn-browse-file");
    const errorReceiptUpload = document.getElementById("error-receiptUpload");
    const summaryReceiptLink = document.getElementById("summary-receipt-link");
    const summaryReceiptRow = document.getElementById("summary-receipt-row");

    // OCR Verification Elements
    const ocrStatusContainer = document.getElementById("ocr-status-container");
    const ocrScanningIndicator = document.getElementById("ocr-scanning-indicator");
    const ocrMatchBadge = document.getElementById("ocr-match-badge");
    const ocrMatchUtr = document.getElementById("ocr-match-utr");
    const ocrMismatchBox = document.getElementById("ocr-mismatch-box");
    const mismatchEnteredUtr = document.getElementById("mismatch-entered-utr");
    const mismatchReceiptUtr = document.getElementById("mismatch-receipt-utr");
    const ocrUnableBox = document.getElementById("ocr-unable-box");

    let detectedReceiptUtr = null;
    let ocrRawText = "";
    let ocrState = "idle"; // "idle" | "scanning" | "match" | "mismatch" | "unable"

    let currentUser = { email: "", name: "", googleId: "" };
    let currentPayment = { orderId: "", paymentId: "", gateway: "upi", amount: 0, receiptUrl: null, receiptName: null };
    let teamMemberCount = 1;
    let collegesLoaded = false;
    let termsAcceptedForPayment = false;
    let collegeFilterDebounce;
    let collegeDropdownItems = [];
    let activeCollegeIndex = -1;

    const FORM_STORAGE_KEY = "hackathon_registration_form";
    const WORKFLOW_STORAGE_KEY = "hackathon_registration_workflow";
    const WORKFLOW_MAX_AGE_MS = 24 * 60 * 60 * 1000;
    let currentStep = 1;
    let currentViewName = "landing";
    let paymentCompleted = false;
    let registrationSummary = null;
    let pollingInterval = null;

    function showToast(title, message) {
        if (!liveUpdateToast) return;
        if (toastTitle) toastTitle.textContent = title;
        if (toastMessage) toastMessage.textContent = message;
        liveUpdateToast.classList.remove("hidden");
        // small delay to allow display:block to apply before animation
        setTimeout(() => liveUpdateToast.classList.add("show"), 10);

        setTimeout(hideToast, 8000);
    }

    function hideToast() {
        if (!liveUpdateToast) return;
        liveUpdateToast.classList.remove("show");
        setTimeout(() => liveUpdateToast.classList.add("hidden"), 400); // match CSS transition duration
    }

    if (toastClose) {
        toastClose.addEventListener("click", hideToast);
    }

    function formatISTDateTime(dateValue = new Date()) {
        return new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: true,
        }).format(dateValue) + " IST";
    }

    function clearWorkflowState() {
        localStorage.removeItem(WORKFLOW_STORAGE_KEY);
    }

    function saveWorkflowState() {
        const state = {
            currentStep,
            currentViewName,
            currentUser,
            currentPayment,
            teamMemberCount,
            termsAcceptedForPayment,
            paymentCompleted,
            registrationSummary,
            savedAt: Date.now(),
        };
        localStorage.setItem(WORKFLOW_STORAGE_KEY, JSON.stringify(state));
    }

    function loadWorkflowState() {
        const raw = localStorage.getItem(WORKFLOW_STORAGE_KEY);
        if (!raw) return null;

        try {
            const state = JSON.parse(raw);
            const savedAt = Number(state.savedAt || 0);
            if (!savedAt || Date.now() - savedAt > WORKFLOW_MAX_AGE_MS) {
                clearWorkflowState();
                return null;
            }
            return state;
        } catch (_err) {
            clearWorkflowState();
            return null;
        }
    }

    function setBackButtonAfterPaymentState() {
        if (paymentCompleted) {
            btnBackStep3.classList.add("hidden");
            btnBackStep3.disabled = true;
            return;
        }

        btnBackStep3.classList.remove("hidden");
        btnBackStep3.disabled = false;
    }

    function applyPaymentStepState() {
        const paymentSuccess = document.getElementById("payment-success-msg");
        const paymentSummaryWrapper = document.getElementById("payment-summary-wrapper");
        const lockedNotice = document.getElementById("terms-locked-notice");
        const transactionIdEl = document.getElementById("display-transaction-id");

        const hasReceipt = Boolean(currentPayment.receiptUrl || currentPayment.receiptBase64);
        const entered = (upiUtrInput ? upiUtrInput.value : "").replace(/\D/g, "");
        const isMatch = (ocrState === "match" || (detectedReceiptUtr && entered === detectedReceiptUtr));

        if (paymentCompleted && currentPayment.orderId && hasReceipt && isMatch) {
            if (paymentSuccess) paymentSuccess.classList.remove("hidden");
            if (paymentSummaryWrapper) paymentSummaryWrapper.classList.add("hidden");
            if (lockedNotice) lockedNotice.classList.add("hidden");
            if (transactionIdEl) transactionIdEl.textContent = currentPayment.paymentId || currentPayment.orderId;
            btnSubmitFinal.classList.remove("hidden");
            setBackButtonAfterPaymentState();
            return;
        }

        if (paymentSuccess) paymentSuccess.classList.add("hidden");
        btnSubmitFinal.classList.add("hidden");

        if (termsAcceptedForPayment) {
            if (lockedNotice) lockedNotice.classList.add("hidden");
            if (paymentSummaryWrapper) paymentSummaryWrapper.classList.remove("hidden");
            if (upiUtrInput) upiUtrInput.disabled = false;
            if (btnVerifyUpi) {
                if (hasReceipt) {
                    btnVerifyUpi.classList.remove("hidden");
                    btnVerifyUpi.disabled = (entered.length !== 12 || ocrState === "mismatch" || ocrState === "scanning");
                } else {
                    btnVerifyUpi.classList.add("hidden");
                    btnVerifyUpi.disabled = true;
                }
            }
            loadUPIPaymentOrder();
        } else {
            if (lockedNotice) lockedNotice.classList.remove("hidden");
            if (paymentSummaryWrapper) paymentSummaryWrapper.classList.add("hidden");
            if (upiUtrInput) upiUtrInput.disabled = true;
            if (btnVerifyUpi) {
                btnVerifyUpi.classList.add("hidden");
                btnVerifyUpi.disabled = true;
            }
        }

        setBackButtonAfterPaymentState();
    }

    function restoreWorkflowProgress() {
        const state = loadWorkflowState();
        if (!state) return;

        if (state.currentUser && state.currentUser.email) {
            currentUser = {
                email: state.currentUser.email || "",
                name: state.currentUser.name || "",
                googleId: state.currentUser.googleId || "",
            };
            emailInput.value = currentUser.email;
            if (!fullNameInput.value && currentUser.name) {
                fullNameInput.value = currentUser.name;
            }
            if (!registrationDateInput.value) {
                registrationDateInput.value = formatISTDateTime();
            }

            if (currentUser.email && (!mobileInput.value || !collegeNameInput.value)) {
                fetch(`/api/draft/${encodeURIComponent(currentUser.email)}`)
                    .then(res => res.ok ? res.json() : null)
                    .then(data => {
                        if (data && data.hasDraft && data.draft) {
                            const d = data.draft;
                            if (!fullNameInput.value && d.fullName) fullNameInput.value = d.fullName;
                            if (!mobileInput.value && d.mobile) mobileInput.value = d.mobile;
                            if (!branchInput.value && d.branch) branchInput.value = d.branch;
                            if (!cityInput.value && d.city) cityInput.value = d.city;
                            if (!rollNumberInput.value && d.rollNumber) rollNumberInput.value = d.rollNumber;
                            if (!registrationDateInput.value && d.registrationDate) registrationDateInput.value = d.registrationDate;
                            if (currentYearInput && !currentYearInput.value && d.currentYear) {
                                currentYearInput.value = d.currentYear;
                            }
                            if (collegeNameInput && !collegeNameInput.value && d.collegeName && d.collegeName.toLowerCase() !== "other") {
                                syncHiddenSelectValue(d.collegeName);
                                collegeSearchInput.value = d.collegeName;
                            }
                            if (projectSelectedInput && !projectSelectedInput.value && d.projectSelected) {
                                projectSelectedInput.value = d.projectSelected;
                            }
                        }
                    })
                    .catch(() => {});
            }
        }

        teamMemberCount = Math.min(MAX_TEAM_MEMBERS, Math.max(1, Number(state.teamMemberCount || teamMemberCount || 1)));
        termsAcceptedForPayment = !!state.termsAcceptedForPayment;
        paymentCompleted = !!state.paymentCompleted;
        registrationSummary = state.registrationSummary || null;

        if (state.currentPayment) {
            currentPayment = {
                orderId: state.currentPayment.orderId || "",
                paymentId: state.currentPayment.paymentId || "",
                gateway: state.currentPayment.gateway || "upi",
                amount: Number(state.currentPayment.amount || 0),
                receiptUrl: state.currentPayment.receiptUrl || null,
                receiptName: state.currentPayment.receiptName || null,
                receiptBase64: state.currentPayment.receiptBase64 || null,
            };

            if ((currentPayment.receiptUrl || currentPayment.receiptBase64) && receiptPreviewCard && dropzoneContent) {
                dropzoneContent.classList.add("hidden");
                receiptPreviewCard.classList.remove("hidden");
                if (previewFilename) previewFilename.textContent = currentPayment.receiptName || "receipt.png";
                if (previewUploadStatus) {
                    previewUploadStatus.className = "preview-upload-status";
                    previewUploadStatus.innerHTML = '<i class="fas fa-check-circle"></i> Uploaded';
                }
            }
        }

        const requestedView = state.currentViewName;
        if (requestedView === "register") {
            showView(registerView);
        } else if (requestedView === "instructions") {
            showView(instructionsView);
        } else {
            showView(landingView);
        }

        const requestedStep = state.currentStep === "success" ? "success" : Number(state.currentStep || 1);
        if (requestedStep === "success") {
            showStep("success");
            if (registrationSummary) {
                renderSuccessSummary(registrationSummary);
            } else if (currentPayment.orderId) {
                fetchRegistrationSummary(currentPayment.orderId)
                    .then((summary) => {
                        registrationSummary = summary;
                        renderSuccessSummary(summary);
                        saveWorkflowState();
                    })
                    .catch(() => { });
            }
            return;
        }

        if (requestedStep >= 2 && !currentUser.email) {
            showStep(1);
            return;
        }

        if (requestedStep >= 3) {
            const step2Check = validateStep2(false);
            if (!step2Check.isValid) {
                showStep(2);
                return;
            }
            const mode = document.querySelector('input[name="participationMode"]:checked')?.value;
            if (mode === "team") {
                setupTeamStep();
            }
        }

        if (requestedStep === 4) {
            const step2Check = validateStep2(false);
            if (!step2Check.isValid) {
                showStep(2);
                return;
            }
            updatePaymentSummary();
            applyPaymentStepState();
        }

        showStep(requestedStep);
        saveWorkflowState();
    }

    function showView(view) {
        [landingView, registerView, instructionsView].forEach((v) => {
            v.classList.remove("active");
            v.classList.add("hidden");
        });
        view.classList.remove("hidden");
        view.classList.add("active");

        if (view === registerView) {
            currentViewName = "register";
        } else if (view === instructionsView) {
            currentViewName = "instructions";
        } else {
            currentViewName = "landing";
        }

        document.querySelectorAll(".nav-links a").forEach((a) => a.classList.remove("active"));
        if (view === landingView) navHome.classList.add("active");
        if (view === instructionsView) navInstructions.classList.add("active");

        if (currentViewName !== "register" || currentStep !== "success") {
            stopLiveUpdatesPolling();
        }

        saveWorkflowState();
    }

    function showStep(stepNum) {
        currentStep = stepNum;
        [step1, step2, step3, step4, successView].forEach((s) => {
            s.classList.remove("active-step");
            s.classList.add("hidden-step");
        });
        [stepIndicator1, stepIndicator2, stepIndicator3, stepIndicator4].forEach((s) => s.classList.remove("active", "completed"));
        [progressLine1, progressLine2, progressLine3].forEach((line) => line.classList.remove("active"));

        if (stepNum === 1) {
            step1.classList.add("active-step");
            step1.classList.remove("hidden-step");
            stepIndicator1.classList.add("active");
            saveWorkflowState();
            return;
        }
        if (stepNum === 2) {
            step2.classList.add("active-step");
            step2.classList.remove("hidden-step");
            stepIndicator1.classList.add("completed");
            stepIndicator2.classList.add("active");
            progressLine1.classList.add("active");
            saveWorkflowState();
            return;
        }
        if (stepNum === 3) {
            step3.classList.add("active-step");
            step3.classList.remove("hidden-step");
            stepIndicator1.classList.add("completed");
            stepIndicator2.classList.add("completed");
            stepIndicator3.classList.add("active");
            progressLine1.classList.add("active");
            progressLine2.classList.add("active");
            saveWorkflowState();
            return;
        }
        if (stepNum === 4) {
            step4.classList.add("active-step");
            step4.classList.remove("hidden-step");
            stepIndicator1.classList.add("completed");
            stepIndicator2.classList.add("completed");
            stepIndicator3.classList.add("completed");
            stepIndicator4.classList.add("active");
            progressLine1.classList.add("active");
            progressLine2.classList.add("active");
            progressLine3.classList.add("active");
            updatePaymentSummary();
            applyPaymentStepState();
            setBackButtonAfterPaymentState();
            saveWorkflowState();
            return;
        }

        successView.classList.add("active-step");
        successView.classList.remove("hidden-step");
        [stepIndicator1, stepIndicator2, stepIndicator3, stepIndicator4].forEach((s) => s.classList.add("completed"));
        [progressLine1, progressLine2, progressLine3].forEach((line) => line.classList.add("active"));
        saveWorkflowState();

        if (stepNum === "success") {
            startLiveUpdatesPolling();
        } else {
            stopLiveUpdatesPolling();
        }
    }

    let saveDraftDebounceTimer = null;
    let autosaveHideTimer = null;

    function showAutosaveBadge(status = "saving") {
        const badge = document.getElementById("autosave-status");
        if (!badge) return;
        clearTimeout(autosaveHideTimer);

        if (status === "saving") {
            badge.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving to database...';
            badge.style.color = '#3b82f6';
            badge.style.background = 'rgba(59, 130, 246, 0.1)';
            badge.style.opacity = '1';
        } else if (status === "saved") {
            badge.innerHTML = '<i class="fas fa-check-circle"></i> Saved in Database';
            badge.style.color = '#10b981';
            badge.style.background = 'rgba(16, 185, 129, 0.1)';
            badge.style.opacity = '1';
            autosaveHideTimer = setTimeout(() => {
                if (badge) badge.style.opacity = '0';
            }, 2500);
        } else if (status === "error") {
            badge.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Save Failed';
            badge.style.color = '#ef4444';
            badge.style.background = 'rgba(239, 68, 68, 0.1)';
            badge.style.opacity = '1';
            autosaveHideTimer = setTimeout(() => {
                if (badge) badge.style.opacity = '0';
            }, 3500);
        }
    }

    async function saveDraftToServer(isImmediate = false) {
        if (isImmediate) {
            clearTimeout(saveDraftDebounceTimer);
        }

        const userEmail = (currentUser && currentUser.email) ? currentUser.email : (emailInput ? emailInput.value.trim() : "");
        if (!userEmail) return;

        const mode = document.querySelector('input[name="participationMode"]:checked')?.value || "individual";

        const teamMembers = [];
        if (mode === "team") {
            for (let i = 1; i <= teamMemberCount; i++) {
                const mName = document.getElementById(`member${i}-name`)?.value.trim() || "";
                const mEmail = document.getElementById(`member${i}-email`)?.value.trim() || "";
                const mMobile = document.getElementById(`member${i}-mobile`)?.value.trim() || "";
                const mRoll = document.getElementById(`member${i}-roll`)?.value.trim() || "";
                if (mName || mEmail || mMobile || mRoll) {
                    teamMembers.push({
                        fullName: mName,
                        email: mEmail,
                        mobile: mMobile,
                        rollNumber: mRoll,
                    });
                }
            }
        }

        // Resolve college name: check collegeName select and collegeSearchInput
        let rawCollege = (collegeNameInput ? collegeNameInput.value.trim() : "");
        const searchCollege = (collegeSearchInput ? collegeSearchInput.value.trim() : "");
        let resolvedCollege = rawCollege;
        if (!resolvedCollege || resolvedCollege.toLowerCase() === "other") {
            resolvedCollege = (searchCollege.toLowerCase() !== "other") ? searchCollege : "";
        } else if (searchCollege && searchCollege.toLowerCase() !== rawCollege.toLowerCase() && searchCollege.toLowerCase() !== "other") {
            resolvedCollege = searchCollege;
        }

        // Resolve current year
        const rawYear = (currentYearInput ? currentYearInput.value.trim() : "");
        const otherYear = (otherCurrentYearInput ? otherCurrentYearInput.value.trim() : "");
        let resolvedYear = rawYear;
        if (rawYear === "Other" && otherYear) {
            resolvedYear = otherYear;
        }

        // Resolve branch / category
        const rawBranch = (branchInput ? branchInput.value.trim() : "");
        const otherBranch = (otherBranchInput ? otherBranchInput.value.trim() : "");
        let resolvedBranch = rawBranch;
        if (rawBranch === "Other" && otherBranch) {
            resolvedBranch = otherBranch;
        }

        // Resolve project / task category
        const rawProject = (projectSelectedInput ? projectSelectedInput.value.trim() : "");
        const otherProject = (otherProjectInput ? otherProjectInput.value.trim() : "");
        let resolvedProject = rawProject;
        if (rawProject === "Other" && otherProject) {
            resolvedProject = otherProject;
        }

        const draftPayload = {
            email: userEmail,
            fullName: fullNameInput ? fullNameInput.value.trim() : "",
            mobile: mobileInput ? mobileInput.value.trim() : "",
            branch: resolvedBranch,
            otherBranchName: otherBranch,
            collegeName: resolvedCollege,
            otherCollegeName: otherCollege,
            city: cityInput ? cityInput.value.trim() : "",
            rollNumber: rollNumberInput ? rollNumberInput.value.trim() : "",
            currentYear: resolvedYear,
            otherCurrentYear: otherYear,
            projectSelected: resolvedProject,
            otherProjectSelected: otherProject,
            participationMode: mode,
            registrationDate: registrationDateInput ? registrationDateInput.value.trim() : "",
            teamName: teamNameInput ? teamNameInput.value.trim() : "",
            teamMembers: teamMembers,
            orderId: (currentPayment && currentPayment.orderId) ? currentPayment.orderId : "",
        };

        showAutosaveBadge("saving");

        try {
            const res = await fetch("/api/save-draft", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(draftPayload),
            });
            if (res.ok) {
                const result = await res.json();
                console.log("[PIN-TO-PIN AUTOSAVE SUCCESS]", result.message || "Draft saved to database", draftPayload);
                showAutosaveBadge("saved");
            } else {
                const errData = await res.json().catch(() => ({}));
                console.warn("[AUTOSAVE ERROR]", res.status, errData);
                showAutosaveBadge("error");
            }
        } catch (err) {
            console.warn("Draft auto-save notice:", err);
            showAutosaveBadge("error");
        }
    }

    function triggerDebouncedSaveDraft() {
        clearTimeout(saveDraftDebounceTimer);
        saveDraftDebounceTimer = setTimeout(() => {
            saveDraftToServer(false);
        }, 250);
    }

    function saveFormData() {
        let collegeVal = (collegeNameInput ? collegeNameInput.value.trim() : "");
        const searchCollege = (collegeSearchInput ? collegeSearchInput.value.trim() : "");
        if (collegeVal.toLowerCase() === "other") collegeVal = "";
        if (!collegeVal && searchCollege && searchCollege.toLowerCase() !== "other") {
            collegeVal = searchCollege;
        }

        const data = {
            fullName: fullNameInput ? fullNameInput.value : "",
            mobile: mobileInput ? mobileInput.value : "",
            branch: branchInput ? branchInput.value : "",
            otherBranchName: otherBranchInput ? otherBranchInput.value.trim() : "",
            collegeName: collegeVal,
            collegeSearch: searchCollege,
            otherCollegeName: "",
            city: cityInput ? cityInput.value.trim() : "",
            rollNumber: rollNumberInput ? rollNumberInput.value.trim() : "",
            currentYear: currentYearInput ? currentYearInput.value : "",
            otherCurrentYear: otherCurrentYearInput ? otherCurrentYearInput.value.trim() : "",
            projectSelected: projectSelectedInput ? projectSelectedInput.value : "",
            otherProjectSelected: otherProjectInput ? otherProjectInput.value.trim() : "",
            participationMode: document.querySelector('input[name="participationMode"]:checked')?.value || "",
            registrationDate: registrationDateInput ? registrationDateInput.value : "",
            teamName: teamNameInput ? teamNameInput.value : "",
            termsAcceptedForPayment,
        };

        for (let i = 1; i <= MAX_TEAM_MEMBERS; i++) {
            data[`member${i}Name`] = document.getElementById(`member${i}-name`)?.value || "";
            data[`member${i}Email`] = document.getElementById(`member${i}-email`)?.value || "";
            data[`member${i}Mobile`] = document.getElementById(`member${i}-mobile`)?.value || "";
            data[`member${i}Roll`] = document.getElementById(`member${i}-roll`)?.value || "";
        }

        sessionStorage.setItem(FORM_STORAGE_KEY, JSON.stringify(data));
        triggerDebouncedSaveDraft();
    }

    function loadFormData() {
        const raw = sessionStorage.getItem(FORM_STORAGE_KEY);
        if (!raw) return;

        try {
            const data = JSON.parse(raw);
            fullNameInput.value = data.fullName || fullNameInput.value;
            mobileInput.value = data.mobile || mobileInput.value;
            if (data.branch) {
                branchInput.value = data.branch;
                if (data.branch === "Other") {
                    toggleOtherBranchInput(true);
                    if (data.otherBranchName && otherBranchInput) {
                        otherBranchInput.value = data.otherBranchName;
                    }
                } else {
                    toggleOtherBranchInput(false);
                }
            }
            if (data.collegeName && data.collegeName.toLowerCase() !== "other") {
                collegeNameInput.value = data.collegeName;
            } else {
                collegeNameInput.value = "";
            }
            if (otherCollegeInput) otherCollegeInput.value = "";
            cityInput.value = data.city || cityInput.value;
            rollNumberInput.value = data.rollNumber || rollNumberInput.value;
            if (currentYearInput && data.currentYear) {
                currentYearInput.value = data.currentYear;
                if (data.currentYear === "Other") {
                    toggleOtherYearInput(true);
                    if (otherCurrentYearInput && data.otherCurrentYear) {
                        otherCurrentYearInput.value = data.otherCurrentYear;
                    }
                } else {
                    toggleOtherYearInput(false);
                }
            }
            if (data.projectSelected) {
                projectSelectedInput.value = data.projectSelected;
                if (data.projectSelected === "Other") {
                    toggleOtherProjectInput(true);
                    if (data.otherProjectSelected && otherProjectInput) {
                        otherProjectInput.value = data.otherProjectSelected;
                    }
                } else {
                    toggleOtherProjectInput(false);
                }
            }
            teamNameInput.value = data.teamName || teamNameInput.value;

            if (data.participationMode) {
                const modeInput = document.querySelector(`input[name="participationMode"][value="${data.participationMode}"]`);
                if (modeInput) modeInput.checked = true;
            }

            termsAcceptedForPayment = !!data.termsAcceptedForPayment;
            if (termsAcceptedInput) termsAcceptedInput.checked = termsAcceptedForPayment;
            setTermsStatus(termsAcceptedForPayment ? "accepted" : "pending");
            applyPaymentStepState();

            for (let i = 1; i <= MAX_TEAM_MEMBERS; i++) {
                const card = document.getElementById(`member-${i}-card`);
                if (!card) continue;

                const name = data[`member${i}Name`] || "";
                const email = data[`member${i}Email`] || "";
                const mobile = data[`member${i}Mobile`] || "";
                const roll = data[`member${i}Roll`] || "";

                if (name || email || mobile || roll) {
                    card.classList.remove("hidden");
                    teamMemberCount = Math.max(teamMemberCount, i);
                }

                document.getElementById(`member${i}-name`).value = name;
                document.getElementById(`member${i}-email`).value = email;
                document.getElementById(`member${i}-mobile`).value = mobile;
                document.getElementById(`member${i}-roll`).value = roll;
            }
            updateAddMemberButton();

            if (collegesLoaded) {
                syncCollegeSearchFromSavedValue();
            }
        } catch (_err) {
            sessionStorage.removeItem(FORM_STORAGE_KEY);
        }
    }

    function clearFormData() {
        sessionStorage.removeItem(FORM_STORAGE_KEY);
        registrationSummary = null;
        toggleOtherBranchInput(false);
        toggleOtherCollegeInput(false);
        toggleOtherYearInput(false);
        toggleOtherProjectInput(false);
        clearWorkflowState();
    }

    function clearCollegeSelection() {
        if (collegeNameInput) collegeNameInput.value = "";
        if (collegeSearchInput) collegeSearchInput.value = "";
        if (otherCollegeInput) otherCollegeInput.value = "";
        toggleOtherCollegeInput(false);
    }

    function toggleOtherCollegeInput(show) {
        if (otherCollegeWrapper) {
            otherCollegeWrapper.classList.add("hidden");
            otherCollegeWrapper.style.display = "none";
        }
        if (otherCollegeInput) {
            otherCollegeInput.required = false;
            otherCollegeInput.value = "";
        }
        const error = document.getElementById("error-otherCollegeName");
        if (error) error.textContent = "";
    }

    function toggleOtherYearInput(show) {
        if (show) {
            if (otherYearWrapper) otherYearWrapper.classList.remove("hidden");
            if (otherCurrentYearInput) otherCurrentYearInput.required = true;
            return;
        }

        if (otherYearWrapper) otherYearWrapper.classList.add("hidden");
        if (otherCurrentYearInput) {
            otherCurrentYearInput.required = false;
            otherCurrentYearInput.value = "";
        }
        const error = document.getElementById("error-otherCurrentYear");
        if (error) error.textContent = "";
    }

    function toggleOtherBranchInput(show) {
        if (show) {
            if (otherBranchWrapper) otherBranchWrapper.classList.remove("hidden");
            if (otherBranchInput) otherBranchInput.required = true;
            return;
        }

        if (otherBranchWrapper) otherBranchWrapper.classList.add("hidden");
        if (otherBranchInput) {
            otherBranchInput.required = false;
            otherBranchInput.value = "";
        }
        const error = document.getElementById("error-otherBranchName");
        if (error) error.textContent = "";
    }

    function toggleOtherProjectInput(show) {
        if (show) {
            if (otherProjectWrapper) otherProjectWrapper.classList.remove("hidden");
            if (otherProjectInput) otherProjectInput.required = true;
            return;
        }

        if (otherProjectWrapper) otherProjectWrapper.classList.add("hidden");
        if (otherProjectInput) {
            otherProjectInput.required = false;
            otherProjectInput.value = "";
        }
        const error = document.getElementById("error-otherProjectSelected");
        if (error) error.textContent = "";
    }

    function hideCollegeDropdown() {
        collegeDropdown.classList.add("hidden");
        activeCollegeIndex = -1;
    }

    function syncHiddenSelectValue(collegeName) {
        const targetName = (collegeName || "").trim();
        if (!targetName) {
            collegeNameInput.value = "";
            return;
        }

        let option = Array.from(collegeNameInput.options).find((item) => item.value === targetName);
        if (!option) {
            option = document.createElement("option");
            option.value = targetName;
            option.textContent = targetName;
            collegeNameInput.appendChild(option);
        }
        collegeNameInput.value = targetName;
    }

    async function fetchColleges(queryText = "", maxItems = 500) {
        const params = new URLSearchParams({ include_other: "false", limit: String(maxItems) });
        const cleaned = (queryText || "").trim();
        if (cleaned) {
            params.set("q", cleaned);
        }

        const res = await fetch(`/api/colleges?${params.toString()}`);
        if (!res.ok) {
            throw new Error("Failed to fetch colleges");
        }

        const payload = await res.json();
        const list = payload.colleges || [];
        return list.filter(c => c && c.name && c.name.toLowerCase() !== "other" && !c.is_other);
    }

    function setActiveCollegeOption(index) {
        const options = Array.from(collegeDropdown.querySelectorAll(".college-option:not(.no-results)"));
        if (!options.length) {
            activeCollegeIndex = -1;
            return;
        }

        if (index < 0) index = options.length - 1;
        if (index >= options.length) index = 0;
        activeCollegeIndex = index;

        options.forEach((option, idx) => {
            option.classList.toggle("active", idx === activeCollegeIndex);
        });

        options[activeCollegeIndex].scrollIntoView({ block: "nearest" });
    }

    async function searchCollegesAndRender(queryText) {
        try {
            const items = await fetchColleges(queryText, 500);
            renderCollegeDropdown(items, queryText);
        } catch (_err) {
            renderCollegeDropdown([], queryText);
        }
    }

    function selectCollege(college) {
        if (!college || !college.name || college.name.toLowerCase() === "other") {
            return;
        }
        syncHiddenSelectValue(college.name);
        if (collegeSearchInput) {
            collegeSearchInput.value = college.name;
            collegeSearchInput.blur();
        }
        hideCollegeDropdown();
        toggleOtherCollegeInput(false);

        const error = document.getElementById("error-collegeName");
        if (error) error.textContent = "";

        saveFormData();
        saveDraftToServer(true);
    }

    function renderCollegeDropdown(items, queryText = "") {
        collegeDropdown.innerHTML = "";
        const filteredItems = (items || []).filter(c => c && c.name && c.name.toLowerCase() !== "other" && !c.is_other);
        collegeDropdownItems = filteredItems;
        activeCollegeIndex = -1;

        if (!filteredItems.length) {
            const empty = document.createElement("button");
            empty.type = "button";
            empty.className = "college-option no-results";
            empty.textContent = "No colleges found in list";
            empty.disabled = true;
            collegeDropdown.appendChild(empty);
        } else {
            filteredItems.forEach((college, idx) => {
                const option = document.createElement("button");
                option.type = "button";
                option.className = "college-option";
                option.textContent = college.name;
                option.dataset.value = college.name;
                option.addEventListener("mouseenter", () => setActiveCollegeOption(idx));
                option.addEventListener("mousedown", (e) => {
                    e.preventDefault();
                    selectCollege(college);
                });
                collegeDropdown.appendChild(option);
            });
        }

        collegeDropdown.classList.remove("hidden");
    }

    function syncCollegeSearchFromSavedValue() {
        const savedCollege = (collegeNameInput.value || "").trim();
        if (!savedCollege || savedCollege.toLowerCase() === "other") {
            clearCollegeSelection();
            return;
        }

        const matched = Array.from(collegeNameInput.options).find(
            opt => opt.value && opt.value.toLowerCase() === savedCollege.toLowerCase() && opt.value.toLowerCase() !== "other"
        );
        if (matched) {
            syncHiddenSelectValue(matched.value);
            if (collegeSearchInput) collegeSearchInput.value = matched.value;
        } else {
            clearCollegeSelection();
        }
        toggleOtherCollegeInput(false);
    }

    async function loadColleges() {
        const collegeLoading = document.getElementById("college-loading");
        if (collegeLoading) collegeLoading.style.display = "block";

        try {
            const colleges = await fetchColleges("", 500);

            while (collegeNameInput.options.length > 1) {
                collegeNameInput.remove(1);
            }

            colleges.forEach((college) => {
                if (college && college.name && college.name.toLowerCase() !== "other" && !college.is_other) {
                    const option = document.createElement("option");
                    option.value = college.name;
                    option.textContent = college.name;
                    collegeNameInput.appendChild(option);
                }
            });

            syncCollegeSearchFromSavedValue();

            collegesLoaded = true;
            if (collegeLoading) collegeLoading.style.display = "none";
        } catch (_err) {
            if (collegeLoading) {
                collegeLoading.style.color = "var(--error)";
                collegeLoading.innerHTML = '<i class="fas fa-exclamation-circle"></i> Failed to load colleges';
            }
        }
    }

    async function loadTaskCategories() {
        try {
            const res = await fetch("/api/task-categories");
            const categories = await res.json();

            if (Array.isArray(categories)) {
                const seen = new Set();
                const uniqueCategories = [];

                function getDomainCanonical(name) {
                    const low = String(name || "").toLowerCase();
                    if (low.includes("full stack") || low.includes("fullstack")) return { key: "fullstack", display: "Full Stack Application" };
                    if (low.includes("bug")) return { key: "bughunt", display: "Bug Hunt" };
                    if (low.includes("native") || low.includes("windows")) return { key: "nativeapps", display: "Native Apps (Windows)" };
                    if (low.includes("ideathon")) return { key: "ideathon", display: "Ideathon" };
                    return { key: low, display: name };
                }

                categories.forEach(cat => {
                    const normalized = String(cat || "").trim();
                    if (normalized) {
                        const { key, display } = getDomainCanonical(normalized);
                        if (key && !seen.has(key)) {
                            seen.add(key);
                            uniqueCategories.push(display);
                        }
                    }
                });

                ["Full Stack Application", "Bug Hunt", "Native Apps (Windows)", "Ideathon"].forEach(d => {
                    const { key, display } = getDomainCanonical(d);
                    if (!seen.has(key)) {
                        seen.add(key);
                        uniqueCategories.push(display);
                    }
                });

                // Always append Other option for Task Categories
                if (!uniqueCategories.some(c => c.toLowerCase() === "other")) {
                    uniqueCategories.push("Other");
                }

                // Clear existing options except the first placeholder option
                while (projectSelectedInput.options.length > 1) {
                    projectSelectedInput.remove(1);
                }

                uniqueCategories.forEach(cat => {
                    const option = document.createElement("option");
                    option.value = cat;
                    option.textContent = cat;
                    projectSelectedInput.appendChild(option);
                });

                // Re-sync after population
                const raw = sessionStorage.getItem(FORM_STORAGE_KEY);
                if (raw) {
                    const data = JSON.parse(raw);
                    if (data.projectSelected) {
                        projectSelectedInput.value = data.projectSelected;
                        if (data.projectSelected === "Other") {
                            toggleOtherProjectInput(true);
                            if (data.otherProjectSelected && otherProjectInput) {
                                otherProjectInput.value = data.otherProjectSelected;
                            }
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Failed to load task categories:", err);
        }
    }

    async function loadBranches() {
        try {
            const res = await fetch("/api/branches");
            const branches = await res.json();

            if (Array.isArray(branches)) {
                while (branchInput.options.length > 1) {
                    branchInput.remove(1);
                }

                branches.forEach(branch => {
                    if (branch && branch.toLowerCase() !== "other") {
                        const option = document.createElement("option");
                        option.value = branch;
                        option.textContent = branch;
                        branchInput.appendChild(option);
                    }
                });

                // Always append Other option for Branches / Categories
                const otherOpt = document.createElement("option");
                otherOpt.value = "Other";
                otherOpt.textContent = "Other";
                branchInput.appendChild(otherOpt);

                const raw = sessionStorage.getItem(FORM_STORAGE_KEY);
                if (raw) {
                    const data = JSON.parse(raw);
                    if (data.branch) {
                        branchInput.value = data.branch;
                        if (data.branch === "Other") {
                            toggleOtherBranchInput(true);
                            if (data.otherBranchName && otherBranchInput) {
                                otherBranchInput.value = data.otherBranchName;
                            }
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Failed to load branches:", err);
            // Fallback: ensure Other option exists
            if (!Array.from(branchInput.options).some(o => o.value.toLowerCase() === "other")) {
                const otherOpt = document.createElement("option");
                otherOpt.value = "Other";
                otherOpt.textContent = "Other";
                branchInput.appendChild(otherOpt);
            }
        }
    }

    async function loadPublicSettings() {
        try {
            const res = await fetch("/api/public-settings?_t=" + Date.now(), {
                cache: "no-store",
                headers: { "Cache-Control": "no-cache", "Pragma": "no-cache" }
            });
            if (res.ok) {
                const settingsData = await res.json();
                if (settingsData) {
                    if (settingsData.registrationAmount !== undefined && settingsData.registrationAmount !== null) {
                        window.GLOBAL_REGISTRATION_AMOUNT = Number(settingsData.registrationAmount);
                    }
                    if (settingsData.upiId) {
                        window.GLOBAL_UPI_ID = settingsData.upiId;
                    }
                    if (settingsData.upiPayeeName) {
                        window.GLOBAL_UPI_PAYEE = settingsData.upiPayeeName;
                    }
                    if (settingsData.bankName) {
                        window.GLOBAL_BANK_NAME = settingsData.bankName;
                        const el = document.getElementById("display-bank-name");
                        if (el) el.textContent = settingsData.bankName;
                    }
                    if (settingsData.accountNumber) {
                        window.GLOBAL_ACCOUNT_NUMBER = settingsData.accountNumber;
                        const el = document.getElementById("display-account-number");
                        if (el) el.textContent = settingsData.accountNumber;
                    }
                    if (settingsData.ifscCode) {
                        window.GLOBAL_IFSC_CODE = settingsData.ifscCode;
                        const el = document.getElementById("display-ifsc-code");
                        if (el) el.textContent = settingsData.ifscCode;
                    }
                    if (settingsData.accountHolderName) {
                        window.GLOBAL_ACCOUNT_HOLDER = settingsData.accountHolderName;
                        const el = document.getElementById("display-account-holder-name");
                        if (el) el.textContent = settingsData.accountHolderName;
                    }

                    if (displayUpiId && settingsData.upiId) {
                        displayUpiId.textContent = settingsData.upiId;
                    }
                    const displayBankUpi = document.getElementById("display-bank-upi-id");
                    if (displayBankUpi && settingsData.upiId) {
                        displayBankUpi.textContent = settingsData.upiId;
                    }

                    updatePaymentSummary();
                }
            }
        } catch (err) {
            console.error("Failed to load public settings:", err);
        }
    }

    async function checkDuplicate(field, value) {
        if (!value || !value.trim()) return { exists: false };

        try {
            let endpoint = "";
            if (field === "rollNumber") endpoint = `/api/check-roll-number/${encodeURIComponent(value)}`;
            if (field === "email") endpoint = `/api/check-email/${encodeURIComponent(value)}`;
            if (!endpoint) return { exists: false };

            const res = await fetch(endpoint);
            return await res.json();
        } catch (_err) {
            return { exists: false };
        }
    }

    async function checkFullDuplicate(data) {
        try {
            const res = await fetch("/api/check-duplicate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });
            if (!res.ok) return { hasDuplicate: false };
            return await res.json();
        } catch (_err) {
            return { hasDuplicate: false };
        }
    }

    function setFieldError(input, errorId, message) {
        const error = document.getElementById(errorId);
        if (error) error.textContent = message || "";
        if (input) {
            if (message) {
                input.classList.add("error");
            } else {
                input.classList.remove("error");
            }
        }
    }

    function validateField(input, errorId, regex = null, message = "Invalid value", minLength = 1) {
        if (!input) return false;
        const value = (input.value || "").trim();

        if (!value) {
            setFieldError(input, errorId, "This field is required");
            return false;
        }

        if (value.length < minLength) {
            setFieldError(input, errorId, `Must be at least ${minLength} characters`);
            return false;
        }

        if (regex && !regex.test(value)) {
            setFieldError(input, errorId, message);
            return false;
        }

        setFieldError(input, errorId, "");
        return true;
    }

    function validateStep2(showVisualErrors = true) {
        let isValid = true;
        let firstInvalidElement = null;

        function markInvalid(el, errorId, msg) {
            isValid = false;
            if (showVisualErrors) {
                setFieldError(el, errorId, msg);
                if (!firstInvalidElement && el) {
                    firstInvalidElement = el;
                }
            }
        }

        // 1. Full Name
        const fullName = (fullNameInput ? fullNameInput.value : "").trim();
        if (!fullName) {
            markInvalid(fullNameInput, "error-fullName", "Full Name is required");
        } else if (fullName.length < 2) {
            markInvalid(fullNameInput, "error-fullName", "Full Name must be at least 2 characters");
        } else if (!/^[a-zA-Z\s.'-]+$/.test(fullName)) {
            markInvalid(fullNameInput, "error-fullName", "Please enter a valid full name (letters only)");
        } else if (showVisualErrors) {
            setFieldError(fullNameInput, "error-fullName", "");
        }

        // 2. Email Address
        const email = (emailInput ? emailInput.value : (currentUser.email || "")).trim();
        if (!email) {
            markInvalid(emailInput, "auth-error-text", "Email is required. Please sign in with Google.");
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            markInvalid(emailInput, "auth-error-text", "Please provide a valid email address");
        }

        // 3. Mobile Number
        const mobile = (mobileInput ? mobileInput.value : "").trim();
        if (!mobile) {
            markInvalid(mobileInput, "error-mobile", "Mobile number is required");
        } else if (!/^\d{10}$/.test(mobile)) {
            markInvalid(mobileInput, "error-mobile", "Enter a valid 10-digit mobile number");
        } else if (showVisualErrors) {
            setFieldError(mobileInput, "error-mobile", "");
        }

        // 4. Categories / Branch
        const branch = (branchInput ? branchInput.value : "").trim();
        if (!branch) {
            markInvalid(branchInput, "error-branch", "Please select a category");
        } else if (branch === "Other") {
            const otherBr = (otherBranchInput ? otherBranchInput.value : "").trim();
            if (!otherBr) {
                markInvalid(otherBranchInput, "error-otherBranchName", "Please specify your branch / category");
            } else if (otherBr.length < 2) {
                markInvalid(otherBranchInput, "error-otherBranchName", "Branch / category must be at least 2 characters");
            } else if (showVisualErrors) {
                setFieldError(otherBranchInput, "error-otherBranchName", "");
                setFieldError(branchInput, "error-branch", "");
            }
        } else if (showVisualErrors) {
            setFieldError(branchInput, "error-branch", "");
            if (otherBranchInput) setFieldError(otherBranchInput, "error-otherBranchName", "");
        }

        // 5. College Name
        const college = (collegeNameInput ? collegeNameInput.value : "").trim();
        const searchVal = (collegeSearchInput ? collegeSearchInput.value : "").trim();
        const matchedCollege = Array.from(collegeNameInput ? collegeNameInput.options : []).find(
            opt => opt.value && opt.value.toLowerCase() === searchVal.toLowerCase() && opt.value.toLowerCase() !== "other"
        );

        if (!college || college.toLowerCase() === "other" || !searchVal || !matchedCollege) {
            markInvalid(collegeSearchInput, "error-collegeName", "Please select your college from the list");
        } else if (showVisualErrors) {
            setFieldError(collegeSearchInput, "error-collegeName", "");
        }

        // 6. City
        const city = (cityInput ? cityInput.value : "").trim();
        if (!city) {
            markInvalid(cityInput, "error-city", "City is required");
        } else if (city.length < 2) {
            markInvalid(cityInput, "error-city", "City must be at least 2 characters");
        } else if (showVisualErrors) {
            setFieldError(cityInput, "error-city", "");
        }

        // 7. Roll Number
        const roll = (rollNumberInput ? rollNumberInput.value : "").trim();
        if (!roll) {
            markInvalid(rollNumberInput, "error-rollNumber", "Roll number is required");
        } else if (roll.length < 2) {
            markInvalid(rollNumberInput, "error-rollNumber", "Roll number must be at least 2 characters");
        } else if (showVisualErrors) {
            setFieldError(rollNumberInput, "error-rollNumber", "");
        }

        // 8. Current Year
        if (currentYearInput) {
            const year = (currentYearInput.value || "").trim();
            if (!year) {
                markInvalid(currentYearInput, "error-currentYear", "Please select your current year");
            } else if (year === "Other") {
                const otherYr = (otherCurrentYearInput ? otherCurrentYearInput.value : "").trim();
                if (!otherYr) {
                    markInvalid(otherCurrentYearInput, "error-otherCurrentYear", "Please specify your current year / course");
                } else if (showVisualErrors) {
                    setFieldError(otherCurrentYearInput, "error-otherCurrentYear", "");
                    setFieldError(currentYearInput, "error-currentYear", "");
                }
            } else if (showVisualErrors) {
                setFieldError(currentYearInput, "error-currentYear", "");
                if (otherCurrentYearInput) setFieldError(otherCurrentYearInput, "error-otherCurrentYear", "");
            }
        }

        // 9. Select Project/Task
        if (projectSelectedInput) {
            const project = (projectSelectedInput.value || "").trim();
            if (!project) {
                markInvalid(projectSelectedInput, "error-projectSelected", "Please choose a task category");
            } else if (project === "Other") {
                const otherPr = (otherProjectInput ? otherProjectInput.value : "").trim();
                if (!otherPr) {
                    markInvalid(otherProjectInput, "error-otherProjectSelected", "Please specify your project / task category");
                } else if (otherPr.length < 2) {
                    markInvalid(otherProjectInput, "error-otherProjectSelected", "Project category must be at least 2 characters");
                } else if (showVisualErrors) {
                    setFieldError(otherProjectInput, "error-otherProjectSelected", "");
                    setFieldError(projectSelectedInput, "error-projectSelected", "");
                }
            } else if (showVisualErrors) {
                setFieldError(projectSelectedInput, "error-projectSelected", "");
                if (otherProjectInput) setFieldError(otherProjectInput, "error-otherProjectSelected", "");
            }
        }

        // 10. Participation Mode
        const mode = document.querySelector('input[name="participationMode"]:checked');
        const optionsContainer = document.querySelector('.participation-options');
        if (!mode) {
            isValid = false;
            if (showVisualErrors) {
                const errEl = document.getElementById("error-participationMode");
                if (errEl) errEl.textContent = "Please select a participation mode";
                if (optionsContainer) optionsContainer.classList.add("error");
                if (!firstInvalidElement) firstInvalidElement = optionsContainer;
            }
        } else if (showVisualErrors) {
            const errEl = document.getElementById("error-participationMode");
            if (errEl) errEl.textContent = "";
            if (optionsContainer) optionsContainer.classList.remove("error");
        }

        return { isValid, firstInvalidElement };
    }

    function showTermsError(text) {
        const error = document.getElementById("error-termsAccepted");
        if (error) error.textContent = text || "";
    }

    function setTermsStatus(status) {
        if (!termsStatusBadge) return;
        termsStatusBadge.classList.remove("pending", "accepted", "rejected");
        termsStatusBadge.classList.add(status);

        if (status === "accepted") {
            termsStatusBadge.innerHTML = '<i class="fas fa-check-circle"></i> Terms Accepted';
            return;
        }
        if (status === "rejected") {
            termsStatusBadge.innerHTML = '<i class="fas fa-times-circle"></i> Terms Rejected';
            return;
        }
        termsStatusBadge.innerHTML = '<i class="fas fa-clock"></i> Terms Not Accepted';
    }

    function prepareTermsForPayment(mode) {
        termsAcceptedForPayment = false;
        termsAcceptedInput.checked = false;
        if (upiUtrInput) {
            upiUtrInput.disabled = true;
            upiUtrInput.value = "";
        }
        if (btnVerifyUpi) {
            btnVerifyUpi.disabled = true;
            btnVerifyUpi.classList.add("hidden");
        }
        if (btnSubmitFinal) {
            btnSubmitFinal.classList.add("hidden");
        }
        setTermsStatus("pending");
        showTermsError("Please accept Terms and Conditions before verifying payment.");

        if (mode === "team") {
            paymentTermsModeText.textContent = "Team details completed. Accept Terms and Conditions to proceed with UPI payment.";
        } else {
            paymentTermsModeText.textContent = "Individual details completed. Accept Terms and Conditions to proceed with UPI payment.";
        }
    }

    function resetPaymentStepUI() {
        paymentCompleted = false;
        registrationSummary = null;
        currentPayment = { orderId: "", paymentId: "", gateway: "upi", amount: 0, receiptUrl: null, receiptName: null, receiptBase64: null };
        if (upiUtrInput) upiUtrInput.value = "";
        if (errorUpiUtr) errorUpiUtr.textContent = "";
        resetReceiptUpload();
        applyPaymentStepState();
        saveWorkflowState();
    }

    function isAllowedOAuthOrigin(messageOrigin) {
        if (!messageOrigin) return false;
        if (messageOrigin === window.location.origin) return true;

        try {
            const current = new URL(window.location.origin);
            const incoming = new URL(messageOrigin);
            const sameProtocol = current.protocol === incoming.protocol;
            const samePort = current.port === incoming.port;
            const localPair =
                (current.hostname === "localhost" && incoming.hostname === "127.0.0.1") ||
                (current.hostname === "127.0.0.1" && incoming.hostname === "localhost");
            return sameProtocol && samePort && localPair;
        } catch (_err) {
            return false;
        }
    }

    function openTermsModal() {
        termsModal.classList.remove("hidden");
    }

    function closeTermsModal() {
        termsModal.classList.add("hidden");
    }

    function ensureMemberCards() {
        const container = document.getElementById("team-members-container");
        for (let i = 1; i <= MAX_TEAM_MEMBERS; i++) {
            if (document.getElementById(`member-${i}-card`)) continue;

            const card = document.createElement("div");
            card.className = i === 1 ? "team-member-card" : "team-member-card hidden";
            card.id = `member-${i}-card`;
            card.innerHTML = `
                <div class="member-header">
                    <span>Member ${i}</span>
                    <button type="button" class="btn-remove-member" data-member="${i}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Full Name *</label>
                        <input type="text" id="member${i}-name" placeholder="Member name">
                    </div>
                    <div class="form-group">
                        <label>Email *</label>
                        <input type="email" id="member${i}-email" placeholder="Member email">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Mobile *</label>
                        <input type="tel" id="member${i}-mobile" maxlength="10" placeholder="10-digit number">
                    </div>
                    <div class="form-group">
                        <label>Roll Number *</label>
                        <input type="text" id="member${i}-roll" placeholder="Roll number">
                    </div>
                </div>
            `;
            container.appendChild(card);
        }

        document.querySelectorAll(".btn-remove-member").forEach((button) => {
            button.onclick = () => removeMember(parseInt(button.dataset.member, 10));
        });

        for (let i = 1; i <= MAX_TEAM_MEMBERS; i++) {
            ["name", "email", "mobile", "roll"].forEach(f => {
                const el = document.getElementById(`member${i}-${f}`);
                if (el && !el.dataset.hasAutoSave) {
                    el.dataset.hasAutoSave = "true";
                    el.addEventListener("input", saveFormData);
                    el.addEventListener("change", () => { saveFormData(); saveDraftToServer(true); });
                    el.addEventListener("blur", () => { saveFormData(); saveDraftToServer(true); });
                }
            });
        }
    }

    function clearMemberCard(index) {
        ["name", "email", "mobile", "roll"].forEach((field) => {
            const el = document.getElementById(`member${index}-${field}`);
            if (el) el.value = "";
        });
    }

    function copyMemberData(fromIndex, toIndex) {
        ["name", "email", "mobile", "roll"].forEach((field) => {
            const fromEl = document.getElementById(`member${fromIndex}-${field}`);
            const toEl = document.getElementById(`member${toIndex}-${field}`);
            if (fromEl && toEl) toEl.value = fromEl.value;
        });
    }

    function updateAddMemberButton() {
        if (teamMemberCount >= MAX_TEAM_MEMBERS) {
            btnAddMember.style.display = "none";
            memberLimitMsg.classList.remove("hidden");
        } else {
            btnAddMember.style.display = "inline-flex";
            memberLimitMsg.classList.add("hidden");
        }
    }

    function removeMember(memberNum) {
        for (let i = memberNum; i < MAX_TEAM_MEMBERS; i++) {
            const nextCard = document.getElementById(`member-${i + 1}-card`);
            if (nextCard && !nextCard.classList.contains("hidden")) {
                copyMemberData(i + 1, i);
            } else {
                clearMemberCard(i);
                break;
            }
        }

        const lastCard = document.getElementById(`member-${teamMemberCount}-card`);
        if (lastCard) {
            clearMemberCard(teamMemberCount);
            lastCard.classList.add("hidden");
        }

        if (teamMemberCount > 1) teamMemberCount -= 1;
        updateAddMemberButton();
        saveFormData();
    }

    function setupTeamStep() {
        ensureMemberCards();

        leaderInfoEl.textContent = `${fullNameInput.value} (${emailInput.value})`;
        const branchText = branchInput.options[branchInput.selectedIndex]?.text || branchInput.value;
        const taskText = projectSelectedInput.options[projectSelectedInput.selectedIndex]?.text || projectSelectedInput.value;
        const yearText = currentYearInput 
            ? (currentYearInput.value === "Other" && otherCurrentYearInput && otherCurrentYearInput.value.trim() 
                ? otherCurrentYearInput.value.trim() 
                : (currentYearInput.options[currentYearInput.selectedIndex]?.text || currentYearInput.value)) 
            : "";
        const displayCollege = collegeNameInput.value || collegeSearchInput.value || "N/A";
        leaderCollegeInfoEl.innerHTML = `<i class="fas fa-university"></i> ${displayCollege} | <i class="fas fa-code-branch"></i> ${branchText} ${yearText ? `(${yearText})` : ""} | <i class="fas fa-tasks"></i> ${taskText}`;

        for (let i = 1; i <= MAX_TEAM_MEMBERS; i++) {
            const card = document.getElementById(`member-${i}-card`);
            if (!card) continue;
            if (i <= teamMemberCount) {
                card.classList.remove("hidden");
            } else {
                card.classList.add("hidden");
            }
        }
        updateAddMemberButton();
    }

    function renderPaymentQRCode(intentUrl) {
        const qrContainer = document.getElementById("upi-qrcode-container");
        const qrSpinner = document.getElementById("qr-loading-spinner");

        if (typeof QRCode !== "undefined" && qrContainer) {
            try {
                qrContainer.innerHTML = "";
                new QRCode(qrContainer, {
                    text: intentUrl,
                    width: 200,
                    height: 200,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.M,
                });
                if (qrSpinner) qrSpinner.classList.add("hidden");
                if (upiQrImage) upiQrImage.classList.add("hidden");
                qrContainer.classList.remove("hidden");
                return;
            } catch (err) {
                console.warn("Client QRCode generator error, falling back to image API:", err);
            }
        }

        if (upiQrImage) {
            upiQrImage.classList.remove("hidden");
            upiQrImage.classList.add("loading-qr");
            const primaryUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&margin=10&data=${encodeURIComponent(intentUrl)}`;
            const backupUrl = `https://quickchart.io/qr?size=250&margin=2&text=${encodeURIComponent(intentUrl)}`;

            upiQrImage.onload = () => {
                if (qrSpinner) qrSpinner.classList.add("hidden");
                upiQrImage.classList.remove("loading-qr");
            };
            upiQrImage.onerror = () => {
                upiQrImage.src = backupUrl;
            };
            upiQrImage.src = primaryUrl;
        }
    }

    async function loadUPIPaymentOrder() {
        const mode = document.querySelector('input[name="participationMode"]:checked')?.value || "individual";
        const email = (currentUser.email || emailInput.value || "participant@spheronix.com").trim();
        const fullName = (fullNameInput.value || "Hackathon Participant").trim();
        const mobile = (mobileInput.value || "9999999999").trim();
        const projectSelected = projectSelectedInput.value || "";

        const totalMembers = mode === "team" ? (1 + teamMemberCount) : 1;
        const baseFee = (window.GLOBAL_REGISTRATION_AMOUNT !== undefined && window.GLOBAL_REGISTRATION_AMOUNT !== null) ? Number(window.GLOBAL_REGISTRATION_AMOUNT) : 399;
        const totalAmount = baseFee * totalMembers;

        const targetUpiId = window.GLOBAL_UPI_ID || (displayUpiId ? displayUpiId.textContent.trim() : "334509931804612@CNRB");
        const targetPayeeName = window.GLOBAL_UPI_PAYEE || "Spheronix Hackathon";
        const formattedAmount = Number(totalAmount).toFixed(2);

        if (displayUpiId) {
            displayUpiId.textContent = targetUpiId;
        }
        if (qrDisplayAmount) {
            qrDisplayAmount.textContent = `₹${totalAmount}`;
        }

        const initialIntentUrl = `upi://pay?pa=${encodeURIComponent(targetUpiId)}&pn=${encodeURIComponent(targetPayeeName)}&am=${formattedAmount}&cu=INR&tn=${encodeURIComponent("Hackathon Registration Fee")}`;

        if (btnUpiMobilePay) {
            btnUpiMobilePay.href = initialIntentUrl;
        }

        // Render QR Code immediately
        renderPaymentQRCode(initialIntentUrl);

        try {
            const res = await fetch("/api/payment/order?_t=" + Date.now(), {
                method: "POST",
                cache: "no-store",
                headers: {
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                },
                body: JSON.stringify({
                    participationMode: mode,
                    teamMembersCount: mode === "team" ? teamMemberCount : 0,
                    email: email,
                    fullName: fullName,
                    mobile: mobile,
                    projectSelected: projectSelected,
                    branch: branchInput ? branchInput.value : "",
                    collegeName: collegeNameInput ? collegeNameInput.value : "",
                    otherCollegeName: otherCollegeInput ? otherCollegeInput.value : "",
                    city: cityInput ? cityInput.value.trim() : "",
                    rollNumber: rollNumberInput ? rollNumberInput.value.trim() : "",
                    currentYear: currentYearInput ? currentYearInput.value : "",
                    otherCurrentYear: otherCurrentYearInput ? otherCurrentYearInput.value.trim() : "",
                    registrationDate: registrationDateInput ? registrationDateInput.value.trim() : "",
                    teamName: teamNameInput ? teamNameInput.value.trim() : "",
                }),
            });

            if (res.ok) {
                const data = await res.json();
                currentPayment.orderId = data.orderId;
                currentPayment.amount = data.amount;
                currentPayment.gateway = "upi";

                let serverUpiId = (data.upiId || targetUpiId).trim();
                if (!serverUpiId || serverUpiId.toLowerCase().includes("spheronixhackathon@") || serverUpiId.toLowerCase().includes("example@")) {
                    serverUpiId = "334509931804612@CNRB";
                }
                const serverPayeeName = (data.upiPayeeName || targetPayeeName).trim();
                const serverAmount = Number(data.amount || totalAmount).toFixed(2);

                if (displayUpiId) {
                    displayUpiId.textContent = serverUpiId;
                }
                const displayBankUpiIdEl = document.getElementById("display-bank-upi-id");
                if (displayBankUpiIdEl) {
                    displayBankUpiIdEl.textContent = serverUpiId;
                }

                if (data.bankName) {
                    const el = document.getElementById("display-bank-name");
                    if (el) el.textContent = data.bankName;
                }
                if (data.accountHolderName) {
                    const el = document.getElementById("display-account-name");
                    if (el) el.textContent = data.accountHolderName;
                }
                if (data.accountNumber) {
                    const el = document.getElementById("display-account-number");
                    if (el) el.textContent = data.accountNumber;
                }
                if (data.ifscCode) {
                    const el = document.getElementById("display-ifsc-code");
                    if (el) el.textContent = data.ifscCode;
                }

                const serverIntentUrl = data.upiIntentUrl || `upi://pay?pa=${encodeURIComponent(serverUpiId)}&pn=${encodeURIComponent(serverPayeeName)}&am=${serverAmount}&cu=INR&tn=${encodeURIComponent("Hackathon Registration Fee")}`;

                if (btnUpiMobilePay) {
                    btnUpiMobilePay.href = serverIntentUrl;
                }

                renderPaymentQRCode(serverIntentUrl);
            } else if (res.status === 409) {
                const errData = await res.json().catch(() => ({}));
                if (errData && errData.detail) {
                    showToast("Already Registered", errData.detail);
                }
            }
        } catch (e) {
            console.error("Background order sync notice:", e);
        }
    }

    function updatePaymentSummary() {
        const mode = document.querySelector('input[name="participationMode"]:checked')?.value;
        const summaryMode = document.getElementById("summary-mode");
        const summaryTeamRow = document.getElementById("summary-team-row");
        const summaryTeamSize = document.getElementById("summary-team-size");
        const summaryAmount = document.getElementById("summary-amount");
        const summaryFeePerPerson = document.getElementById("summary-fee-per-person");

        let baseFee = (window.GLOBAL_REGISTRATION_AMOUNT !== undefined && window.GLOBAL_REGISTRATION_AMOUNT !== null) ? Number(window.GLOBAL_REGISTRATION_AMOUNT) : 399;
        if (summaryFeePerPerson) {
            summaryFeePerPerson.textContent = `₹${baseFee}`;
        }

        let amount = baseFee;
        if (mode === "team") {
            const totalMembers = 1 + teamMemberCount;
            if (summaryMode) summaryMode.textContent = "Team";
            if (summaryTeamRow) summaryTeamRow.classList.remove("hidden");
            if (summaryTeamSize) summaryTeamSize.textContent = String(totalMembers);
            amount = baseFee * totalMembers;
        } else {
            if (summaryMode) summaryMode.textContent = "Individual";
            if (summaryTeamRow) summaryTeamRow.classList.add("hidden");
        }

        if (summaryAmount) summaryAmount.textContent = `₹${amount}`;
        if (qrDisplayAmount) qrDisplayAmount.textContent = `₹${amount}`;

        if (termsAcceptedForPayment) {
            loadUPIPaymentOrder();
        }
    }

    // Fix H-08: Removed duplicate definitions of formatApiError, collectMissingRegistrationFields,
    // and isAlreadyCompletedRegistrationError that were dead code (lines ~972-1014).
    // The canonical definitions are below near the submitRegistration function.
    function buildFallbackRegistrationSummary(apiResult, userData) {
        return {
            registrationId: apiResult.registrationId || currentPayment.orderId || "",
            transactionId: apiResult.transactionId || currentPayment.paymentId || "N/A",
            fullName: apiResult.fullName || userData.fullName || "",
            email: apiResult.email || userData.email || "",
            participantId: apiResult.participantId || null,
            teamId: apiResult.teamId || null,
            taskSelected: apiResult.taskSelected || userData.projectSelected || "",
            assignedChallenge: apiResult.assignedChallenge || null,
            paymentStatus: apiResult.paymentStatus || "success",
            teamMemberEmails: apiResult.teamMemberEmails || [],
            teamMemberNames: apiResult.teamMemberNames || (userData.teamMembers || []).map(m => m.fullName) || [],
        };
    }

    function renderSuccessSummary(summary) {
        const setText = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        setText("summary-id", summary.registrationId || "N/A");
        setText("summary-participant-id", summary.participantId || "N/A");
        setText("summary-transaction-id", summary.transactionId || "N/A");
        setText("summary-name", summary.fullName || "N/A");
        setText("summary-email", summary.email || "N/A");
        setText("summary-project", summary.taskSelected || "N/A");

        const teamIdRow = document.getElementById("summary-team-id-row");
        const teamIdValue = document.getElementById("summary-team-id");
        if (summary.teamId) {
            teamIdValue.textContent = summary.teamId;
            teamIdRow.classList.remove("hidden");
        } else {
            teamIdValue.textContent = "";
            teamIdRow.classList.add("hidden");
        }

        const teamMembersSummary = document.getElementById("team-members-summary");
        if (summary.teamMemberNames && summary.teamMemberNames.length) {
            teamMembersSummary.innerHTML = `<p><strong>Members:</strong> ${summary.teamMemberNames.join(", ")}</p>`;
            teamMembersSummary.classList.remove("hidden");
        } else if (summary.teamMemberEmails && summary.teamMemberEmails.length) {
            teamMembersSummary.innerHTML = `<p><strong>Members:</strong> ${summary.teamMemberEmails.join(", ")}</p>`;
            teamMembersSummary.classList.remove("hidden");
        } else {
            teamMembersSummary.innerHTML = "";
            teamMembersSummary.classList.add("hidden");
        }

        const summaryReceiptRow = document.getElementById("summary-receipt-row");
        const summaryReceiptLink = document.getElementById("summary-receipt-link");
        const receiptB64 = summary.payment_receipt_url || summary.payment_receipt_base64 || (currentPayment && (currentPayment.receiptUrl || currentPayment.receiptBase64));
        if (summaryReceiptRow && summaryReceiptLink) {
            if (receiptB64) {
                if (receiptB64.startsWith("data:")) {
                    summaryReceiptLink.href = "#";
                    summaryReceiptLink.onclick = function(e) {
                        e.preventDefault();
                        const win = window.open();
                        win.document.write(`<body style="margin:0;display:flex;justify-content:center;align-items:center;background:#111;"><img src="${receiptB64}" style="max-width:100%;max-height:100vh;"></body>`);
                    };
                } else {
                    summaryReceiptLink.href = receiptB64;
                    summaryReceiptLink.target = "_blank";
                    summaryReceiptLink.onclick = null;
                }
                summaryReceiptRow.classList.remove("hidden");
            } else {
                summaryReceiptRow.classList.add("hidden");
            }
        }

        const assignedChallengeCard = document.getElementById("assigned-challenge-card");
        if (assignedChallengeCard) {
            // Requirement: Hide the exact assigned challenge title/description from the registration UI.
            // The user will only see the general category (taskSelected). The exact challenge is revealed in the Exam Portal.
            assignedChallengeCard.classList.add("hidden");
        }
    }

    function stopLiveUpdatesPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    function startLiveUpdatesPolling() {
        stopLiveUpdatesPolling();

        pollingInterval = setInterval(async () => {
            if (!registrationSummary || !registrationSummary.registrationId) return;

            try {
                const latestSummary = await fetchRegistrationSummary(registrationSummary.registrationId);
                let changed = false;
                let messages = [];

                if (latestSummary.is_reviewed !== registrationSummary.is_reviewed) {
                    changed = true;
                    if (latestSummary.is_reviewed) {
                        messages.push("Your registration was reviewed by an admin" + (latestSummary.Reviewedby ? " (" + latestSummary.Reviewedby + ")" : "") + ".");
                    } else {
                        messages.push("Your registration review status was reset.");
                    }
                }

                if (latestSummary.is_selected !== registrationSummary.is_selected) {
                    changed = true;
                    if (latestSummary.is_selected) {
                        messages.push("Congratulations! Your registration was selected.");
                    } else {
                        messages.push("Your registration selection status was changed.");
                    }
                }

                if (latestSummary.user_feedback && latestSummary.user_feedback !== registrationSummary.user_feedback) {
                    changed = true;
                    messages.push("Admin left feedback: " + latestSummary.user_feedback);
                }

                if (changed) {
                    registrationSummary = { ...registrationSummary, ...latestSummary };
                    renderSuccessSummary(registrationSummary);
                    saveWorkflowState();
                    showToast("Registration Updated", messages.join(" "));
                }
            } catch (err) {
                console.warn("Live update poll failed:", err);
            }
        }, 5000); // 5 seconds

        // Fix M-09: Stop polling after 10 minutes or when terminal state is reached
        const MAX_POLL_MS = 10 * 60 * 1000;
        const pollStartTime = Date.now();
        const originalInterval = pollingInterval;
        const wrapExisting = setInterval(() => {
            if (Date.now() - pollStartTime >= MAX_POLL_MS) {
                stopLiveUpdatesPolling();
                clearInterval(wrapExisting);
                console.log("Live updates polling stopped after 10 minutes.");
            } else if (registrationSummary && registrationSummary.is_selected) {
                stopLiveUpdatesPolling();
                clearInterval(wrapExisting);
                console.log("Live updates polling stopped: registration selected.");
            }
        }, 15000);
    }

    async function fetchRegistrationSummary(registrationId) {
        const response = await fetch(`/api/registration/${encodeURIComponent(registrationId)}/summary`);
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || "Failed to load registration summary");
        }
        return payload;
    }

    async function showSuccess(apiResult, userData) {
        let summary = buildFallbackRegistrationSummary(apiResult, userData);
        const targetRegistrationId = apiResult.registrationId || currentPayment.orderId;

        if (targetRegistrationId) {
            try {
                summary = await fetchRegistrationSummary(targetRegistrationId);
            } catch (_err) {
                summary = buildFallbackRegistrationSummary(apiResult, userData);
            }
        }

        clearFormData();
        registrationSummary = summary;
        renderSuccessSummary(summary);
        showStep("success");
        if (typeof confetti === "function") {
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 }
            });
        }
    }

    async function submitRegistration(isTeam) {
        const mode = document.querySelector('input[name="participationMode"]:checked')?.value;
        const missingFields = collectMissingRegistrationFields(mode);
        if (missingFields.length) {
            if (currentPayment.orderId) {
                try {
                    const existingSummary = await fetchRegistrationSummary(currentPayment.orderId);
                    registrationSummary = existingSummary;
                    renderSuccessSummary(existingSummary);
                    showStep("success");
                    return;
                } catch (_err) {
                    // No completed registration found yet for this order, continue to show validation guidance.
                }
            }

            alert(
                `Registration details are incomplete in this session (${missingFields.join(", ")}). Please go back to Details and submit again.`
            );
            return;
        }

        if (!paymentCompleted) {
            showToast("Verification Required", "Please verify your payment and receipt first.");
            return;
        }

        // Validate mandatory payment receipt upload
        const hasReceipt = Boolean(currentPayment.receiptBase64 || currentPayment.receiptUrl);
        if (!hasReceipt) {
            if (errorReceiptUpload) {
                errorReceiptUpload.textContent = "Payment receipt / screenshot is mandatory. Please upload your payment slip to complete registration.";
            }
            if (receiptDropzone) {
                receiptDropzone.classList.add("has-error");
                receiptDropzone.scrollIntoView({ behavior: "smooth", block: "center" });
            }
            showToast("Receipt Required", "Uploading your payment receipt / screenshot is mandatory. Please attach your payment proof.");
            return;
        }

        // Validate OCR verification status (strictly block if mismatch or not match)
        const currentUtr = (upiUtrInput ? upiUtrInput.value : "").replace(/\D/g, "");
        if (ocrState !== "match" || (detectedReceiptUtr && currentUtr !== detectedReceiptUtr)) {
            if (errorUpiUtr) {
                errorUpiUtr.textContent = `Entered UTR does not match Receipt UTR (${detectedReceiptUtr || "not matched"}). Please fix before completing registration.`;
            }
            if (receiptDropzone) {
                receiptDropzone.classList.add("has-error");
                receiptDropzone.scrollIntoView({ behavior: "smooth", block: "center" });
            }
            showToast("UTR Mismatch", "Entered UTR does not match the uploaded receipt. Registration cannot be completed.");
            return;
        }

        const original = btnSubmitFinal.innerHTML;
        btnSubmitFinal.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        btnSubmitFinal.disabled = true;

        const selectedYear = currentYearInput 
            ? (currentYearInput.value === "Other" && otherCurrentYearInput && otherCurrentYearInput.value.trim() 
                ? otherCurrentYearInput.value.trim() 
                : currentYearInput.value.trim()) 
            : null;

        const selectedBranch = branchInput 
            ? (branchInput.value === "Other" && otherBranchInput && otherBranchInput.value.trim() 
                ? otherBranchInput.value.trim() 
                : branchInput.value.trim()) 
            : "";

        const selectedProject = projectSelectedInput 
            ? (projectSelectedInput.value === "Other" && otherProjectInput && otherProjectInput.value.trim() 
                ? otherProjectInput.value.trim() 
                : projectSelectedInput.value.trim()) 
            : "";

        const finalCollegeName = (collegeNameInput.value.trim().toLowerCase() !== "other") ? collegeNameInput.value.trim() : "";
        const finalOtherCollegeName = null;

        const payload = {
            fullName: fullNameInput.value.trim(),
            email: currentUser.email,
            mobile: mobileInput.value.trim(),
            branch: selectedBranch,
            otherBranchName: otherBranchInput ? otherBranchInput.value.trim() : null,
            collegeName: finalCollegeName,
            otherCollegeName: finalOtherCollegeName,
            city: cityInput.value.trim(),
            rollNumber: rollNumberInput.value.trim(),
            currentYear: selectedYear,
            projectSelected: selectedProject,
            otherProjectSelected: otherProjectInput ? otherProjectInput.value.trim() : null,
            participationMode: mode,
            isTeamLeader: isTeam,
            teamName: isTeam ? teamNameInput.value.trim() : null,
            teamMembers: [],
            payment_gateway: currentPayment.gateway,
            payment_utr: currentPayment.paymentId || (upiUtrInput ? upiUtrInput.value.trim() : null),
            utr_number: currentPayment.paymentId || (upiUtrInput ? upiUtrInput.value.trim() : null),
            transaction_id: currentPayment.paymentId || (upiUtrInput ? upiUtrInput.value.trim() : null),
            detected_receipt_utr: detectedReceiptUtr || null,
            rzp_payment_id: currentPayment.paymentId,
            rzp_order_id: currentPayment.orderId,
            order_id: currentPayment.orderId,
            payment_amount: currentPayment.amount,
            payment_receipt_url: currentPayment.receiptUrl || null,
            payment_receipt_base64: currentPayment.receiptBase64 || null,
            payment_receipt_name: currentPayment.receiptName || null,
        };

        if (isTeam) {
            for (let i = 1; i <= teamMemberCount; i++) {
                payload.teamMembers.push({
                    fullName: document.getElementById(`member${i}-name`).value.trim(),
                    email: document.getElementById(`member${i}-email`).value.trim(),
                    mobile: document.getElementById(`member${i}-mobile`).value.trim(),
                    rollNumber: document.getElementById(`member${i}-roll`).value.trim(),
                });
            }
        }

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const result = await response.json();

            if (!response.ok) {
                if (response.status === 409 && isAlreadyCompletedRegistrationError(result.detail)) {
                    // Treat duplicate submit for the same paid order as idempotent success.
                    await showSuccess(
                        {
                            registrationId: payload.rzp_order_id,
                            transactionId: payload.rzp_payment_id,
                            fullName: payload.fullName,
                            email: payload.email,
                            taskSelected: payload.projectSelected,
                            paymentStatus: "success",
                        },
                        payload,
                    );
                    return;
                }
                alert(`Registration Failed: ${formatApiError(result.detail)}`);
                return;
            }

            await showSuccess(result, payload);
        } catch (err) {
            console.error("Registration submit failed:", err);
            alert(err?.message ? `Registration failed: ${err.message}` : "Network error. Please try again.");
        } finally {
            btnSubmitFinal.innerHTML = original;
            btnSubmitFinal.disabled = false;
        }
    }

    function collectMissingRegistrationFields(mode) {
        const missing = [];
        if (!fullNameInput.value.trim()) missing.push("Full Name");
        if (!mobileInput.value.trim()) missing.push("Mobile");
        if (!branchInput.value) missing.push("Branch");
        if (!collegeNameInput.value.trim()) missing.push("College");
        if (!cityInput.value.trim()) missing.push("City");
        if (!rollNumberInput.value.trim()) missing.push("Roll Number");
        if (currentYearInput && !currentYearInput.value) missing.push("Current Year");
        if (!projectSelectedInput.value) missing.push("Project Category");
        if (!mode) missing.push("Participation Mode");

        if (mode === "team") {
            if (!teamNameInput.value.trim()) missing.push("Team Name");
            // Basic check for at least 1 member (total 2)
            if (teamMemberCount < 1) missing.push("At least 1 Team Member");
        }

        if (!currentPayment.orderId) missing.push("Payment Order ID");
        if (!currentPayment.paymentId) missing.push("Payment ID");

        return missing;
    }

    function isAlreadyCompletedRegistrationError(detail) {
        if (!detail) return false;
        const msg = String(detail).toLowerCase();
        return msg.includes("already registered") || msg.includes("duplicate") || msg.includes("exists");
    }

    function formatApiError(detail) {
        if (Array.isArray(detail)) {
            return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(", ");
        }
        if (typeof detail === "object" && detail !== null) {
            return detail.message || detail.detail || JSON.stringify(detail);
        }
        return detail || "Unknown error";
    }

    btnStartRegister.addEventListener("click", () => {
        showView(registerView);
        showStep(1);
    });

    btnInstructions.addEventListener("click", () => showView(instructionsView));
    btnBackLanding.addEventListener("click", () => showView(landingView));
    btnBackInstructions.addEventListener("click", () => showView(landingView));
    btnStartFromInstructions.addEventListener("click", () => {
        showView(registerView);
        showStep(1);
    });

    if (navHome) {
        navHome.addEventListener("click", (event) => {
            event.preventDefault();
            showView(landingView);
        });
    }

    const navGoBack = document.getElementById("nav-go-back");
    if (navGoBack) {
        navGoBack.addEventListener("click", (event) => {
            event.preventDefault();
            showView(landingView);
        });
    }

    if (navInstructions) {
        navInstructions.addEventListener("click", (event) => {
            event.preventDefault();
            showView(instructionsView);
        });
    }

    btnOpenTerms.addEventListener("click", openTermsModal);
    btnTermsAccept.addEventListener("click", () => {
        termsAcceptedForPayment = true;
        termsAcceptedInput.checked = true;
        setTermsStatus("accepted");
        showTermsError("");
        closeTermsModal();
        applyPaymentStepState();
        saveFormData();
        saveWorkflowState();

        // Smooth scroll to revealed payment summary and QR scanner
        const paymentWrapper = document.getElementById("payment-summary-wrapper");
        if (paymentWrapper) {
            setTimeout(() => {
                paymentWrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }, 150);
        }
    });

    btnTermsReject.addEventListener("click", () => {
        termsAcceptedForPayment = false;
        termsAcceptedInput.checked = false;
        setTermsStatus("rejected");
        showTermsError("You are not eligible for registration without accepting Terms and Conditions.");
        closeTermsModal();
        applyPaymentStepState();
        saveFormData();
        saveWorkflowState();
    });

    if (termsAcceptedInput) {
        termsAcceptedInput.addEventListener("change", () => {
            if (termsAcceptedInput.checked) {
                if (!termsAcceptedForPayment) {
                    openTermsModal();
                    termsAcceptedInput.checked = false;
                } else {
                    applyPaymentStepState();
                }
            } else {
                termsAcceptedForPayment = false;
                termsAcceptedInput.checked = false;
                setTermsStatus("pending");
                showTermsError("Please accept Terms and Conditions to display payment details.");
                applyPaymentStepState();
                saveFormData();
                saveWorkflowState();
            }
        });
    }

    termsModal.addEventListener("click", (event) => {
        if (event.target === termsModal) closeTermsModal();
    });

    btnGoogleAuth.addEventListener("click", (event) => {
        event.preventDefault();

        btnGoogleAuth.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        btnGoogleAuth.disabled = true;
        authError.classList.add("hidden");
        alreadyRegistered.classList.add("hidden");

        const width = 500;
        const height = 600;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;

        const popup = window.open(
            "/api/auth/login",
            "Google Auth",
            `width=${width},height=${height},top=${top},left=${left}`
        );

        if (!popup) {
            document.getElementById("auth-error-text").textContent =
                "Popup was blocked. Please allow popups for this site and try again.";
            authError.classList.remove("hidden");
            btnGoogleAuth.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
            btnGoogleAuth.disabled = false;
            return;
        }

        // To avoid COOP console warnings from checking popup.closed, we re-enable the button
        // when the main window regains focus. If the popup was closed or lost behind the window, 
        // the user can click the button again to refocus/reopen it.
        const onFocus = () => {
            setTimeout(() => {
                if (!currentUser.email && btnGoogleAuth.disabled) {
                    btnGoogleAuth.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
                    btnGoogleAuth.disabled = false;
                }
                window.removeEventListener("focus", onFocus);
            }, 500);
        };
        window.addEventListener("focus", onFocus);
        async function onAuthMessage(messageEvent) {
            if (!isAllowedOAuthOrigin(messageEvent.origin)) return;

            const data = messageEvent.data || {};
            if (!data || !data.status) return;
            if (data.status === "success") {
                if (data.alreadyRegistered) {
                    alreadyRegistered.classList.remove("hidden");
                    btnGoogleAuth.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
                    btnGoogleAuth.disabled = false;
                    window.removeEventListener("message", onAuthMessage);
                    return;
                }

                // Check for existing registration or payment
                const checkRes = await checkDuplicate("email", data.email);

                if (checkRes.registrationCompleted) {
                    alreadyRegistered.classList.remove("hidden");
                    btnGoogleAuth.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
                    btnGoogleAuth.disabled = false;
                    window.removeEventListener("message", onAuthMessage);
                    return;
                }

                currentUser = {
                    email: data.email,
                    name: data.name || "",
                    googleId: data.google_id || "",
                };

                emailInput.value = currentUser.email;
                if (!fullNameInput.value) fullNameInput.value = currentUser.name;
                registrationDateInput.value = formatISTDateTime();
                loadFormData();

                // If a draft exists in database, restore it
                try {
                    const draftRes = await fetch(`/api/draft/${encodeURIComponent(data.email)}`);
                    if (draftRes.ok) {
                        const draftData = await draftRes.json();
                        if (draftData.hasDraft && draftData.draft) {
                            const d = draftData.draft;
                            if (d.fullName && fullNameInput) fullNameInput.value = d.fullName;
                            if (d.mobile && mobileInput) mobileInput.value = d.mobile;
                            if (d.branch && branchInput) {
                                branchInput.value = d.branch;
                                if (d.branch === "Other" || (d.otherBranchName && d.otherBranchName.trim())) {
                                    branchInput.value = "Other";
                                    toggleOtherBranchInput(true);
                                    if (otherBranchInput) {
                                        otherBranchInput.value = d.otherBranchName || (d.branch !== "Other" ? d.branch : "");
                                    }
                                }
                            }
                            if (d.city && cityInput) cityInput.value = d.city;
                            if (d.rollNumber && rollNumberInput) rollNumberInput.value = d.rollNumber;
                            if (d.registrationDate && registrationDateInput) registrationDateInput.value = d.registrationDate;
                            if (d.currentYear && currentYearInput) {
                                currentYearInput.value = d.currentYear;
                                if (d.currentYear === "Other" && d.otherCurrentYear && otherCurrentYearInput) {
                                    toggleOtherYearInput(true);
                                    otherCurrentYearInput.value = d.otherCurrentYear;
                                }
                            }
                            if (d.collegeName && d.collegeName.toLowerCase() !== "other") {
                                syncHiddenSelectValue(d.collegeName);
                                if (collegeSearchInput) collegeSearchInput.value = d.collegeName;
                            } else {
                                clearCollegeSelection();
                            }
                            toggleOtherCollegeInput(false);
                            if (d.projectSelected && projectSelectedInput) {
                                projectSelectedInput.value = d.projectSelected;
                                if (d.projectSelected === "Other" || (d.otherProjectSelected && d.otherProjectSelected.trim())) {
                                    projectSelectedInput.value = "Other";
                                    toggleOtherProjectInput(true);
                                    if (otherProjectInput) {
                                        otherProjectInput.value = d.otherProjectSelected || (d.projectSelected !== "Other" ? d.projectSelected : "");
                                    }
                                }
                            }
                            if (d.participationMode) {
                                const modeInput = document.querySelector(`input[name="participationMode"][value="${d.participationMode}"]`);
                                if (modeInput) modeInput.checked = true;
                            }
                            if (d.teamName && teamNameInput) {
                                teamNameInput.value = d.teamName;
                            }
                            if (Array.isArray(d.teamMembers) && d.teamMembers.length > 0) {
                                teamMemberCount = Math.min(MAX_TEAM_MEMBERS, d.teamMembers.length);
                                d.teamMembers.forEach((m, idx) => {
                                    const num = idx + 1;
                                    const c = document.getElementById(`member-${num}-card`);
                                    if (c) c.classList.remove("hidden");
                                    const nEl = document.getElementById(`member${num}-name`);
                                    const eEl = document.getElementById(`member${num}-email`);
                                    const mEl = document.getElementById(`member${num}-mobile`);
                                    const rEl = document.getElementById(`member${num}-roll`);
                                    if (nEl) nEl.value = m.fullName || m.name || "";
                                    if (eEl) eEl.value = m.email || "";
                                    if (mEl) mEl.value = m.mobile || m.phone || "";
                                    if (rEl) rEl.value = m.rollNumber || "";
                                });
                                updateAddMemberButton();
                            }
                            if (d.orderId && currentPayment) {
                                currentPayment.orderId = d.orderId;
                            }
                            saveFormData();
                        }
                    }
                } catch (draftErr) {
                    console.warn("Draft restore notice:", draftErr);
                }
                saveDraftToServer(true);

                // Recovery logic: if they have already paid but not completed registration
                if (checkRes.hasPaid && checkRes.registrationId) {
                    console.log("Found existing successful payment, attempting recovery...");
                    try {
                        const summary = await fetchRegistrationSummary(checkRes.registrationId);
                        registrationSummary = summary;
                        currentPayment = {
                            orderId: summary.registrationId,
                            paymentId: summary.transactionId,
                            gateway: "razorpay",
                            amount: 0, // already paid
                        };
                        paymentCompleted = true;

                        // Populate form with recovered data
                        fullNameInput.value = summary.fullName || fullNameInput.value;
                        projectSelectedInput.value = summary.taskSelected || projectSelectedInput.value;

                        saveWorkflowState();
                        showView(registerView);
                        showStep(4); // Jump to payment verification step
                        applyPaymentStepState();

                        showToast("Registration Recovered", "Your previous payment was found. Please finalize your details.");
                        window.removeEventListener("message", onAuthMessage);
                        return;
                    } catch (err) {
                        console.warn("Recovery failed, proceeding with normal flow:", err);
                    }
                }
                showStep(2);
                saveWorkflowState();
            } else {
                document.getElementById("auth-error-text").textContent = data.error || "Authentication failed.";
                authError.classList.remove("hidden");
            }

            btnGoogleAuth.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
            btnGoogleAuth.disabled = false;
            window.removeEventListener("message", onAuthMessage);
        }

        window.addEventListener("message", onAuthMessage, false);
    });

    if (fullNameInput) {
        fullNameInput.addEventListener("input", () => {
            const val = fullNameInput.value.trim();
            if (val.length >= 2 && /^[a-zA-Z\s.'-]+$/.test(val)) {
                setFieldError(fullNameInput, "error-fullName", "");
            }
            saveFormData();
        });
    }

    if (mobileInput) {
        mobileInput.addEventListener("input", () => {
            mobileInput.value = mobileInput.value.replace(/[^0-9]/g, "").slice(0, 10);
            if (mobileInput.value.length === 10) {
                setFieldError(mobileInput, "error-mobile", "");
            }
            saveFormData();
        });
    }

    let rollDebounce;
    if (rollNumberInput) {
        rollNumberInput.addEventListener("input", () => {
            if (rollNumberInput.value.trim().length >= 2) {
                setFieldError(rollNumberInput, "error-rollNumber", "");
            }
            saveFormData();
            clearTimeout(rollDebounce);
            rollDebounce = setTimeout(async () => {
                if (!rollNumberInput.value.trim()) return;
                const result = await checkDuplicate("rollNumber", rollNumberInput.value.trim());
                if (result.exists) {
                    setFieldError(rollNumberInput, "error-rollNumber", result.message || "Already exists.");
                }
            }, 500);
        });
    }

    if (branchInput) {
        branchInput.addEventListener("change", () => {
            if (branchInput.value.trim()) {
                setFieldError(branchInput, "error-branch", "");
            }
            if (branchInput.value === "Other") {
                toggleOtherBranchInput(true);
                if (otherBranchInput) otherBranchInput.focus();
            } else {
                toggleOtherBranchInput(false);
            }
            saveFormData();
        });
    }

    if (otherBranchInput) {
        otherBranchInput.addEventListener("input", () => {
            if (otherBranchInput.value.trim().length >= 2) {
                setFieldError(otherBranchInput, "error-otherBranchName", "");
                setFieldError(branchInput, "error-branch", "");
            }
            saveFormData();
        });
    }

    if (cityInput) {
        cityInput.addEventListener("input", () => {
            if (cityInput.value.trim().length >= 2) {
                setFieldError(cityInput, "error-city", "");
            }
            saveFormData();
        });
    }

    if (collegeSearchInput) {
        collegeSearchInput.addEventListener("focus", () => {
            if (!collegesLoaded) return;
            searchCollegesAndRender(collegeSearchInput.value);
        });

        collegeSearchInput.addEventListener("input", () => {
            const inputValue = (collegeSearchInput.value || "").trim();
            
            const matchedOption = Array.from(collegeNameInput ? collegeNameInput.options : []).find(
                opt => opt.value && opt.value.toLowerCase() === inputValue.toLowerCase() && opt.value.toLowerCase() !== "other"
            );
            if (matchedOption) {
                syncHiddenSelectValue(matchedOption.value);
                setFieldError(collegeSearchInput, "error-collegeName", "");
            } else {
                if (collegeNameInput) collegeNameInput.value = "";
            }

            clearTimeout(collegeFilterDebounce);
            collegeFilterDebounce = setTimeout(() => {
                searchCollegesAndRender(inputValue);
            }, 180);
            saveFormData();
        });

        collegeSearchInput.addEventListener("keydown", (event) => {
            if (event.key === "ArrowDown") {
                event.preventDefault();
                if (collegeDropdown.classList.contains("hidden")) {
                    searchCollegesAndRender(collegeSearchInput.value);
                    return;
                }
                setActiveCollegeOption(activeCollegeIndex + 1);
                return;
            }

            if (event.key === "ArrowUp") {
                event.preventDefault();
                if (collegeDropdown.classList.contains("hidden")) return;
                setActiveCollegeOption(activeCollegeIndex - 1);
                return;
            }

            if (event.key === "Escape") {
                hideCollegeDropdown();
                return;
            }

            if (event.key !== "Enter") return;
            if (collegeDropdown.classList.contains("hidden")) return;

            event.preventDefault();
            const typedVal = (collegeSearchInput.value || "").trim();
            let selected = null;
            if (activeCollegeIndex >= 0 && collegeDropdownItems[activeCollegeIndex]) {
                selected = collegeDropdownItems[activeCollegeIndex];
            } else {
                const exact = collegeDropdownItems.find(c => c.name && c.name.toLowerCase() === typedVal.toLowerCase() && c.name.toLowerCase() !== "other");
                if (exact) {
                    selected = exact;
                }
            }
            if (selected && selected.name && selected.name.toLowerCase() !== "other") {
                selectCollege(selected);
            } else {
                hideCollegeDropdown();
            }
        });

        collegeSearchInput.addEventListener("blur", () => {
            const typed = (collegeSearchInput.value || "").trim();
            const selected = (collegeNameInput ? collegeNameInput.value : "").trim();

            if (typed && selected && typed.toLowerCase() === selected.toLowerCase() && selected.toLowerCase() !== "other") {
                collegeSearchInput.value = selected;
                setFieldError(collegeSearchInput, "error-collegeName", "");
            } else if (typed) {
                const matchedOption = Array.from(collegeNameInput ? collegeNameInput.options : []).find(
                    opt => opt.value && opt.value.toLowerCase() === typed.toLowerCase() && opt.value.toLowerCase() !== "other"
                );
                if (matchedOption) {
                    selectCollege({ name: matchedOption.value });
                    setFieldError(collegeSearchInput, "error-collegeName", "");
                } else {
                    if (collegeNameInput) collegeNameInput.value = "";
                    markInvalid(collegeSearchInput, "error-collegeName", "Please select your college from the list");
                }
            } else {
                if (collegeNameInput) collegeNameInput.value = "";
                setFieldError(collegeSearchInput, "error-collegeName", "");
            }
            window.setTimeout(hideCollegeDropdown, 200);
        });
    }

    if (otherCollegeInput) {
        otherCollegeInput.addEventListener("input", () => {
            if (otherCollegeInput.value.trim().length >= 2) {
                setFieldError(otherCollegeInput, "error-otherCollegeName", "");
            }
            saveFormData();
        });
    }

    if (currentYearInput) {
        currentYearInput.addEventListener("change", () => {
            if (currentYearInput.value.trim()) {
                setFieldError(currentYearInput, "error-currentYear", "");
            }
            if (currentYearInput.value === "Other") {
                toggleOtherYearInput(true);
                if (otherCurrentYearInput) otherCurrentYearInput.focus();
            } else {
                toggleOtherYearInput(false);
            }
            saveFormData();
        });
    }

    if (otherCurrentYearInput) {
        otherCurrentYearInput.addEventListener("input", () => {
            if (otherCurrentYearInput.value.trim()) {
                setFieldError(otherCurrentYearInput, "error-otherCurrentYear", "");
                setFieldError(currentYearInput, "error-currentYear", "");
            }
            saveFormData();
        });
    }

    if (projectSelectedInput) {
        projectSelectedInput.addEventListener("change", () => {
            if (projectSelectedInput.value.trim()) {
                setFieldError(projectSelectedInput, "error-projectSelected", "");
            }
            if (projectSelectedInput.value === "Other") {
                toggleOtherProjectInput(true);
                if (otherProjectInput) otherProjectInput.focus();
            } else {
                toggleOtherProjectInput(false);
            }
            if (!paymentCompleted) {
                currentPayment.orderId = "";
            }
            saveFormData();
        });
    }

    if (otherProjectInput) {
        otherProjectInput.addEventListener("input", () => {
            if (otherProjectInput.value.trim().length >= 2) {
                setFieldError(otherProjectInput, "error-otherProjectSelected", "");
                setFieldError(projectSelectedInput, "error-projectSelected", "");
            }
            saveFormData();
        });
    }

    document.querySelectorAll('input[name="participationMode"]').forEach(radio => {
        radio.addEventListener("change", () => {
            const errEl = document.getElementById("error-participationMode");
            if (errEl) errEl.textContent = "";
            const optionsContainer = document.querySelector('.participation-options');
            if (optionsContainer) optionsContainer.classList.remove("error");
            saveFormData();
            saveDraftToServer(true);
        });
    });

    document.addEventListener("click", (event) => {
        const selector = document.getElementById("college-selector");
        if (selector && !selector.contains(event.target)) {
            hideCollegeDropdown();
        }
    });

    const allStep2Inputs = [
        fullNameInput,
        mobileInput,
        branchInput,
        collegeSearchInput,
        collegeNameInput,
        otherCollegeInput,
        cityInput,
        rollNumberInput,
        currentYearInput,
        otherCurrentYearInput,
        projectSelectedInput,
        teamNameInput
    ];

    allStep2Inputs.forEach((el) => {
        if (el) {
            el.addEventListener("input", saveFormData);
            el.addEventListener("change", () => {
                saveFormData();
                saveDraftToServer(true);
            });
            el.addEventListener("blur", () => {
                saveFormData();
                saveDraftToServer(true);
            });
        }
    });

    registrationForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const { isValid, firstInvalidElement } = validateStep2(true);

        if (!isValid) {
            showToast("Required Fields Missing", "Please fill in all mandatory fields before proceeding.");
            if (firstInvalidElement) {
                firstInvalidElement.scrollIntoView({ behavior: "smooth", block: "center" });
                if (typeof firstInvalidElement.focus === "function") {
                    firstInvalidElement.focus();
                }
            }
            return;
        }

        const mode = document.querySelector('input[name="participationMode"]:checked');

        const dupData = {
            email: (emailInput.value || currentUser.email || "").trim(),
            rollNumber: rollNumberInput.value.trim(),
            mobile: mobileInput.value.trim(),
        };
        const dupResult = await checkFullDuplicate(dupData);
        if (dupResult.hasDuplicate) {
            dupResult.duplicates.forEach(d => {
                if (d.field === "email") {
                    alreadyRegistered.classList.remove("hidden");
                    showToast("Duplicate Error", "This email address is already registered.");
                } else if (d.field === "rollNumber") {
                    setFieldError(rollNumberInput, "error-rollNumber", d.message || "Roll number already registered.");
                    showToast("Duplicate Error", d.message || "Roll number already registered.");
                } else if (d.field === "mobile") {
                    setFieldError(mobileInput, "error-mobile", d.message || "Mobile number already registered.");
                    showToast("Duplicate Error", d.message || "Mobile number already registered.");
                }
            });
            return;
        }

        saveFormData();
        await saveDraftToServer(true);

        if (mode && mode.value === "team") {
            setupTeamStep();
            showStep(3);
        } else {
            resetPaymentStepUI();
            prepareTermsForPayment("individual");
            await loadPublicSettings();
            updatePaymentSummary();
            showStep(4);
        }
    });

    btnAddMember.addEventListener("click", () => {
        if (teamMemberCount >= MAX_TEAM_MEMBERS) return;
        teamMemberCount += 1;
        const card = document.getElementById(`member-${teamMemberCount}-card`);
        if (card) card.classList.remove("hidden");
        updateAddMemberButton();
        saveFormData();
    });

    btnBackStep2.addEventListener("click", () => showStep(2));

    btnNextPayment.addEventListener("click", async () => {
        // Clear previous errors
        document.querySelectorAll("#team-members-container input").forEach(el => el.classList.remove("error"));

        if (!teamNameInput.value.trim()) {
            setFieldError(teamNameInput, "error-teamName", "Team name is required");
            teamNameInput.scrollIntoView({ behavior: "smooth", block: "center" });
            teamNameInput.focus();
            return;
        }
        setFieldError(teamNameInput, "error-teamName", "");

        const totalMembers = 1 + teamMemberCount;
        if (totalMembers < MIN_TEAM_TOTAL || totalMembers > MAX_TEAM_TOTAL) {
            showToast("Team Size Error", `Team size must be between ${MIN_TEAM_TOTAL} and ${MAX_TEAM_TOTAL} members including leader.`);
            return;
        }

        const seenEmails = new Set([(currentUser.email || "").trim().toLowerCase()]);
        const seenMobiles = new Set([mobileInput.value.trim()]);
        const seenRolls = new Set([rollNumberInput.value.trim().toLowerCase()]);

        for (let i = 1; i <= teamMemberCount; i++) {
            const nameEl = document.getElementById(`member${i}-name`);
            const emailEl = document.getElementById(`member${i}-email`);
            const mobileEl = document.getElementById(`member${i}-mobile`);
            const rollEl = document.getElementById(`member${i}-roll`);

            const name = (nameEl ? nameEl.value : "").trim();
            const email = (emailEl ? emailEl.value : "").trim();
            const mobile = (mobileEl ? mobileEl.value : "").trim();
            const roll = (rollEl ? rollEl.value : "").trim();
            const emailKey = email.toLowerCase();
            const rollKey = roll.toLowerCase();

            if (!name) {
                if (nameEl) { nameEl.classList.add("error"); nameEl.scrollIntoView({ behavior: "smooth", block: "center" }); nameEl.focus(); }
                showToast("Missing Information", `Please provide full name for Member ${i}.`);
                return;
            }
            if (!email) {
                if (emailEl) { emailEl.classList.add("error"); emailEl.scrollIntoView({ behavior: "smooth", block: "center" }); emailEl.focus(); }
                showToast("Missing Information", `Please provide email address for Member ${i}.`);
                return;
            }
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                if (emailEl) { emailEl.classList.add("error"); emailEl.scrollIntoView({ behavior: "smooth", block: "center" }); emailEl.focus(); }
                showToast("Validation Error", `The email address format for Member ${i} is invalid.`);
                return;
            }
            if (!mobile) {
                if (mobileEl) { mobileEl.classList.add("error"); mobileEl.scrollIntoView({ behavior: "smooth", block: "center" }); mobileEl.focus(); }
                showToast("Missing Information", `Please provide mobile number for Member ${i}.`);
                return;
            }
            if (!/^\d{10}$/.test(mobile)) {
                if (mobileEl) { mobileEl.classList.add("error"); mobileEl.scrollIntoView({ behavior: "smooth", block: "center" }); mobileEl.focus(); }
                showToast("Validation Error", `The mobile number provided for Member ${i} is invalid. A 10-digit number is required.`);
                return;
            }
            if (!roll) {
                if (rollEl) { rollEl.classList.add("error"); rollEl.scrollIntoView({ behavior: "smooth", block: "center" }); rollEl.focus(); }
                showToast("Missing Information", `Please provide roll number for Member ${i}.`);
                return;
            }

            if (seenEmails.has(emailKey)) {
                if (emailEl) emailEl.classList.add("error");
                showToast("Duplicate Entry", `The email address for Member ${i} is already in use within your team. Each member must have a unique email.`);
                return;
            }
            if (seenMobiles.has(mobile)) {
                if (mobileEl) mobileEl.classList.add("error");
                showToast("Duplicate Entry", `The mobile number for Member ${i} is already in use. Mobile numbers must be unique.`);
                return;
            }
            if (seenRolls.has(rollKey)) {
                if (rollEl) rollEl.classList.add("error");
                showToast("Duplicate Entry", `The roll number for Member ${i} is already in use. Roll numbers must be unique.`);
                return;
            }

            seenEmails.add(emailKey);
            seenMobiles.add(mobile);
            seenRolls.add(rollKey);

            const dupRes = await checkFullDuplicate({
                email: emailKey,
                rollNumber: rollKey,
                mobile: mobile,
            });
            if (dupRes.hasDuplicate) {
                const msg = dupRes.duplicates.map(d => d.message).join(", ");
                if (emailEl) emailEl.classList.add("error");
                showToast("Duplicate Entry", `Registration conflict for Member ${i}: ${msg}`);
                return;
            }
        }

        resetPaymentStepUI();
        prepareTermsForPayment("team");
        saveFormData();
        await saveDraftToServer(true);
        await loadPublicSettings();
        updatePaymentSummary();
        saveWorkflowState();
        showStep(4);
    });

    if (btnCopyUpi) {
        btnCopyUpi.addEventListener("click", async () => {
            const upiId = displayUpiId ? displayUpiId.textContent.trim() : "334509931804612@CNRB";
            try {
                await navigator.clipboard.writeText(upiId);
                const originalHtml = btnCopyUpi.innerHTML;
                btnCopyUpi.innerHTML = '<i class="fas fa-check"></i> <span>Copied!</span>';
                btnCopyUpi.classList.add("copied");
                showToast("UPI ID Copied", "UPI ID copied to clipboard: " + upiId);
                setTimeout(() => {
                    btnCopyUpi.innerHTML = originalHtml;
                    btnCopyUpi.classList.remove("copied");
                }, 2500);
            } catch (_e) {
                showToast("UPI ID", "UPI ID: " + upiId);
            }
        });
    }

    const btnCopyAccNum = document.getElementById("btn-copy-acc-num");
    if (btnCopyAccNum) {
        btnCopyAccNum.addEventListener("click", async () => {
            const accNumEl = document.getElementById("display-account-number");
            const accNum = accNumEl ? accNumEl.textContent.trim() : "120036804612";
            try {
                await navigator.clipboard.writeText(accNum);
                const originalHtml = btnCopyAccNum.innerHTML;
                btnCopyAccNum.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btnCopyAccNum.classList.add("copied");
                showToast("Account Number Copied", "Account Number copied: " + accNum);
                setTimeout(() => {
                    btnCopyAccNum.innerHTML = originalHtml;
                    btnCopyAccNum.classList.remove("copied");
                }, 2500);
            } catch (_e) {
                showToast("Account Number", "Account Number: " + accNum);
            }
        });
    }

    const btnCopyIfsc = document.getElementById("btn-copy-ifsc");
    if (btnCopyIfsc) {
        btnCopyIfsc.addEventListener("click", async () => {
            const ifscEl = document.getElementById("display-ifsc-code");
            const ifsc = ifscEl ? ifscEl.textContent.trim() : "CNRB0000659";
            try {
                await navigator.clipboard.writeText(ifsc);
                const originalHtml = btnCopyIfsc.innerHTML;
                btnCopyIfsc.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btnCopyIfsc.classList.add("copied");
                showToast("IFSC Code Copied", "IFSC Code copied: " + ifsc);
                setTimeout(() => {
                    btnCopyIfsc.innerHTML = originalHtml;
                    btnCopyIfsc.classList.remove("copied");
                }, 2500);
            } catch (_e) {
                showToast("IFSC Code", "IFSC Code: " + ifsc);
            }
        });
    }

    const btnCopyBankUpi = document.getElementById("btn-copy-bank-upi");
    if (btnCopyBankUpi) {
        btnCopyBankUpi.addEventListener("click", async () => {
            const upiEl = document.getElementById("display-bank-upi-id") || displayUpiId;
            const upiId = upiEl ? upiEl.textContent.trim() : (window.GLOBAL_UPI_ID || "334509931804612@CNRB");
            try {
                await navigator.clipboard.writeText(upiId);
                const originalHtml = btnCopyBankUpi.innerHTML;
                btnCopyBankUpi.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btnCopyBankUpi.classList.add("copied");
                showToast("UPI ID Copied", "UPI ID copied to clipboard: " + upiId);
                setTimeout(() => {
                    btnCopyBankUpi.innerHTML = originalHtml;
                    btnCopyBankUpi.classList.remove("copied");
                }, 2500);
            } catch (_e) {
                showToast("UPI ID", "UPI ID: " + upiId);
            }
        });
    }

    // ============ Payment Receipt Upload Handling (Max 5MB) ============
    const MAX_RECEIPT_BYTES = 100 * 1024; // 100KB

    function formatReceiptSize(bytes) {
        if (!bytes) return "0 B";
        if (bytes >= 1024 * 1024) {
            return (bytes / (1024 * 1024)).toFixed(2) + " MB";
        }
        return (bytes / 1024).toFixed(0) + " KB";
    }

    // ============ OCR UTR Extraction & Verification Logic ============
    function extractLikelyUtr(text, enteredUtr = "") {
        if (!text) return null;
        const normalized = text.replace(/[\r\n]+/g, " ");

        // 1. Direct match with student's entered UTR if available and 12 digits
        if (enteredUtr && /^\d{12}$/.test(enteredUtr)) {
            if (normalized.includes(enteredUtr)) {
                return enteredUtr;
            }
            const digitsOnlyText = normalized.replace(/[^0-9]/g, "");
            if (digitsOnlyText.includes(enteredUtr)) {
                return enteredUtr;
            }
        }

        // 2. Primary: look for 12-digit number near UTR / UPI Ref / Transaction ID keywords
        const labeledRegexes = [
            /(?:UTR|UPI\s*(?:Ref|Reference)?(?:\s*(?:ID|No|Number))?|Ref(?:erence)?\s*(?:No|Number|ID)?|Transaction\s*(?:ID|No|Number)?|Txn\s*(?:ID|No|Number)?|RRN|Bank\s*Ref)\s*[:#\-\s]?\s*([0-9\s\-]{12,18})/i,
            /(?:UTR|UPI\s*Ref|Ref\s*No|Txn\s*ID|Transaction\s*ID|RRN)[\s\S]{0,35}?([0-9\s\-]{12,18})/i,
            /(?:ref\s*no|reference\s*no|utr\s*no|txn\s*id)[\s\S]{0,25}?([0-9\s\-]{12,18})/i,
        ];

        for (const re of labeledRegexes) {
            const match = normalized.match(re);
            if (match && match[1]) {
                const cleanDigits = match[1].replace(/\D/g, "");
                if (cleanDigits.length === 12) {
                    return cleanDigits;
                }
                if (cleanDigits.length > 12) {
                    return cleanDigits.slice(0, 12);
                }
            }
        }

        // 3. Secondary: find all 12-digit sequences in receipt text and prefer the one closest to reference labels
        const allTwelveDigits = normalized.match(/\b\d{12}\b/g) || [];
        const spacedCandidates = normalized.match(/\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b/g) || [];
        spacedCandidates.forEach(s => allTwelveDigits.push(s.replace(/\D/g, "")));

        if (allTwelveDigits.length > 0) {
            if (enteredUtr && allTwelveDigits.includes(enteredUtr)) {
                return enteredUtr;
            }
            const lower = normalized.toLowerCase();
            let bestCandidate = allTwelveDigits[0];
            let bestDistance = Infinity;

            for (const num of allTwelveDigits) {
                const idx = lower.indexOf(num);
                const keywords = ["utr", "upi", "ref", "rrn", "txn", "transaction", "payment", "bank"];
                for (const kw of keywords) {
                    const kwIdx = lower.lastIndexOf(kw, idx);
                    if (kwIdx !== -1) {
                        const dist = idx - kwIdx;
                        if (dist < bestDistance) {
                            bestDistance = dist;
                            bestCandidate = num;
                        }
                    }
                }
            }
            return bestCandidate;
        }

        return null;
    }

    function compareAndRenderUtrState() {
        const entered = (upiUtrInput ? upiUtrInput.value : "").replace(/\D/g, "");
        const hasReceipt = Boolean(currentPayment.receiptUrl || currentPayment.receiptBase64);

        // Control Verify Button visibility:
        // HIDDEN when no receipt is uploaded.
        // SHOWN ONLY when receipt has been uploaded (and terms accepted).
        if (btnVerifyUpi) {
            if (!hasReceipt) {
                btnVerifyUpi.classList.add("hidden");
                btnVerifyUpi.disabled = true;
            } else if (termsAcceptedForPayment) {
                btnVerifyUpi.classList.remove("hidden");
                btnVerifyUpi.disabled = (entered.length !== 12 || ocrState === "scanning");
            } else {
                btnVerifyUpi.classList.add("hidden");
                btnVerifyUpi.disabled = true;
            }
        }

        if (ocrState === "scanning") {
            if (ocrScanningIndicator) ocrScanningIndicator.classList.remove("hidden");
            if (ocrMatchBadge) ocrMatchBadge.classList.add("hidden");
            if (ocrMismatchBox) ocrMismatchBox.classList.add("hidden");
            if (ocrUnableBox) ocrUnableBox.classList.add("hidden");
            if (receiptDropzone) receiptDropzone.classList.remove("has-error");
            if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
            return;
        }

        if (ocrScanningIndicator) ocrScanningIndicator.classList.add("hidden");

        // If no receipt uploaded yet
        if (!hasReceipt) {
            ocrState = "idle";
            if (ocrMatchBadge) ocrMatchBadge.classList.add("hidden");
            if (ocrMismatchBox) ocrMismatchBox.classList.add("hidden");
            if (ocrUnableBox) ocrUnableBox.classList.add("hidden");
            if (receiptDropzone) receiptDropzone.classList.remove("has-error");
            if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
            return;
        }

        // Re-evaluate detectedReceiptUtr from raw OCR text with entered UTR
        if (ocrRawText) {
            if (!detectedReceiptUtr) {
                detectedReceiptUtr = extractLikelyUtr(ocrRawText, entered);
            } else if (entered.length === 12 && detectedReceiptUtr !== entered) {
                const recheck = extractLikelyUtr(ocrRawText, entered);
                if (recheck === entered) {
                    detectedReceiptUtr = entered;
                }
            }
        }

        // If OCR was unable to detect UTR from receipt
        if (!detectedReceiptUtr) {
            ocrState = "unable";
            if (ocrMatchBadge) ocrMatchBadge.classList.add("hidden");
            if (ocrMismatchBox) ocrMismatchBox.classList.add("hidden");
            if (ocrUnableBox) ocrUnableBox.classList.remove("hidden");
            if (receiptDropzone) receiptDropzone.classList.remove("has-error");
            if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
            return;
        }

        // We have detectedReceiptUtr!
        if (ocrUnableBox) ocrUnableBox.classList.add("hidden");

        if (entered.length === 12) {
            if (entered === detectedReceiptUtr) {
                // MATCH!
                ocrState = "match";
                if (ocrMismatchBox) ocrMismatchBox.classList.add("hidden");
                if (ocrMatchBadge) {
                    ocrMatchBadge.classList.remove("hidden");
                    if (ocrMatchUtr) ocrMatchUtr.textContent = detectedReceiptUtr;
                }
                if (receiptDropzone) receiptDropzone.classList.remove("has-error");
                if (upiUtrInput) upiUtrInput.classList.remove("error");
                if (errorUpiUtr) errorUpiUtr.textContent = "";
                if (btnVerifyUpi) btnVerifyUpi.disabled = false;

                // ONLY show Complete Registration when payment is verified AND UTR matches receipt
                if (paymentCompleted && currentPayment.orderId) {
                    if (btnSubmitFinal) btnSubmitFinal.classList.remove("hidden");
                    const paymentSuccess = document.getElementById("payment-success-msg");
                    if (paymentSuccess) paymentSuccess.classList.remove("hidden");
                    if (upiPaymentPanel) upiPaymentPanel.classList.add("hidden");
                    setBackButtonAfterPaymentState();
                } else {
                    if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                }
            } else {
                // MISMATCH!
                ocrState = "mismatch";
                if (ocrMatchBadge) ocrMatchBadge.classList.add("hidden");
                if (ocrMismatchBox) {
                    ocrMismatchBox.classList.remove("hidden");
                    if (mismatchEnteredUtr) mismatchEnteredUtr.textContent = entered;
                    if (mismatchReceiptUtr) mismatchReceiptUtr.textContent = detectedReceiptUtr;
                }
                if (receiptDropzone) receiptDropzone.classList.add("has-error");
                if (upiUtrInput) upiUtrInput.classList.add("error");
                if (errorUpiUtr) errorUpiUtr.textContent = `Entered UTR (${entered}) does not match Receipt UTR (${detectedReceiptUtr}). Please enter the correct UTR from your receipt.`;

                // Strictly hide Complete Registration on mismatch
                if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                const paymentSuccess = document.getElementById("payment-success-msg");
                if (paymentSuccess) paymentSuccess.classList.add("hidden");
                if (upiPaymentPanel) upiPaymentPanel.classList.remove("hidden");
                if (btnVerifyUpi) btnVerifyUpi.disabled = true;
            }
        } else {
            // Entered UTR is not yet 12 digits
            ocrState = "idle";
            if (ocrMatchBadge) ocrMatchBadge.classList.add("hidden");
            if (ocrMismatchBox) ocrMismatchBox.classList.add("hidden");
            if (receiptDropzone) receiptDropzone.classList.remove("has-error");
            if (upiUtrInput) upiUtrInput.classList.remove("error");
            if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
            if (btnVerifyUpi) btnVerifyUpi.disabled = true;
        }
    }

    async function runTesseractOcrOnReceipt(file) {
        if (!file) return;
        const ext = file.name.split(".").pop().toLowerCase();

        if (ext === "pdf") {
            detectedReceiptUtr = null;
            ocrRawText = "";
            ocrState = "unable";
            compareAndRenderUtrState();
            return;
        }

        if (typeof Tesseract === "undefined") {
            console.warn("Tesseract.js not loaded. Skipping OCR.");
            detectedReceiptUtr = null;
            ocrRawText = "";
            ocrState = "unable";
            compareAndRenderUtrState();
            return;
        }

        ocrState = "scanning";
        compareAndRenderUtrState();

        try {
            const { data } = await Tesseract.recognize(file, "eng", {
                logger: (m) => {
                    if (m.status === "recognizing text" && m.progress && ocrScanningIndicator) {
                        const pct = Math.round(m.progress * 100);
                        const span = ocrScanningIndicator.querySelector("span");
                        if (span) span.textContent = `Scanning receipt for UTR (${pct}%)...`;
                    }
                }
            });

            ocrRawText = (data && data.text) ? data.text : "";
            const currentEntered = (upiUtrInput ? upiUtrInput.value : "").replace(/\D/g, "");
            const foundUtr = extractLikelyUtr(ocrRawText, currentEntered);
            if (foundUtr && /^\d{12}$/.test(foundUtr)) {
                detectedReceiptUtr = foundUtr;
                console.log("[OCR Found UTR]:", detectedReceiptUtr);
            } else {
                detectedReceiptUtr = null;
                ocrState = "unable";
            }
        } catch (ocrErr) {
            console.warn("Tesseract OCR execution error:", ocrErr);
            detectedReceiptUtr = null;
            ocrRawText = "";
            ocrState = "unable";
        } finally {
            if (ocrState === "scanning") {
                ocrState = detectedReceiptUtr ? "idle" : "unable";
            }
            compareAndRenderUtrState();
        }
    }

    async function handleReceiptUpload(file) {
        if (errorReceiptUpload) errorReceiptUpload.textContent = "";
        if (receiptDropzone) receiptDropzone.classList.remove("has-error");
        if (!file) return;

        // Size check (max 5MB)
        if (file.size > MAX_RECEIPT_BYTES) {
            if (errorReceiptUpload) {
                errorReceiptUpload.textContent = "File size exceeds 100KB limit. Please choose a smaller file.";
            }
            if (receiptDropzone) receiptDropzone.classList.add("has-error");
            showToast("Upload Error", "File size exceeds 100KB limit. Please select a smaller receipt.");
            if (receiptFileInput) receiptFileInput.value = "";
            return;
        }

        // Extension check
        const ext = file.name.split(".").pop().toLowerCase();
        const validExts = ["png", "jpg", "jpeg"];
        if (!validExts.includes(ext)) {
            if (errorReceiptUpload) {
                errorReceiptUpload.textContent = "Invalid file type. Allowed formats: PNG, JPG, JPEG.";
            }
            if (receiptDropzone) receiptDropzone.classList.add("has-error");
            showToast("Upload Error", "Please upload a PNG, JPG, or JPEG file.");
            if (receiptFileInput) receiptFileInput.value = "";
            return;
        }

        // Show preview card in loading state
        if (dropzoneContent) dropzoneContent.classList.add("hidden");
        if (receiptPreviewCard) receiptPreviewCard.classList.remove("hidden");
        if (previewFilename) previewFilename.textContent = file.name;
        if (previewFilesize) previewFilesize.textContent = formatReceiptSize(file.size);
        if (previewIcon) {
            if (ext === "pdf") {
                previewIcon.className = "fas fa-file-pdf";
                previewIcon.parentElement.style.background = "#fee2e2";
                previewIcon.parentElement.style.color = "#dc2626";
            } else {
                previewIcon.className = "fas fa-file-image";
                previewIcon.parentElement.style.background = "#eff6ff";
                previewIcon.parentElement.style.color = "#2563eb";
            }
        }
        if (previewUploadStatus) {
            previewUploadStatus.className = "preview-upload-status uploading";
            previewUploadStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        }

        // Perform Upload
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/payment/upload-receipt", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();

            if (res.ok && data.status === "success") {
                let receiptFinalUrl = data.fullUrl || data.fileUrl;
                if (receiptFinalUrl) {
                    if (receiptFinalUrl.startsWith("/")) {
                        receiptFinalUrl = "https://puhackathon.spheronixtechnology.com" + receiptFinalUrl;
                    } else if (receiptFinalUrl.startsWith("http://localhost:8000")) {
                        receiptFinalUrl = receiptFinalUrl.replace("http://localhost:8000", "https://puhackathon.spheronixtechnology.com");
                    } else if (receiptFinalUrl.startsWith("http://127.0.0.1:8000")) {
                        receiptFinalUrl = receiptFinalUrl.replace("http://127.0.0.1:8000", "https://puhackathon.spheronixtechnology.com");
                    } else if (receiptFinalUrl.startsWith("http://")) {
                        receiptFinalUrl = "https://" + receiptFinalUrl.substring(7);
                    }
                }
                currentPayment.receiptUrl = receiptFinalUrl;
                currentPayment.receiptName = data.originalName || file.name;
                currentPayment.receiptBase64 = data.base64 || data.payment_receipt_base64 || data.receipt_base64 || "";

                if (previewUploadStatus) {
                    previewUploadStatus.className = "preview-upload-status";
                    previewUploadStatus.innerHTML = '<i class="fas fa-check-circle"></i> Uploaded';
                }
                if (errorReceiptUpload) errorReceiptUpload.textContent = "";
                if (receiptDropzone) receiptDropzone.classList.remove("has-error");
                saveWorkflowState();
                showToast("Receipt Uploaded", "Payment proof uploaded successfully (" + formatReceiptSize(file.size) + ")");
                if (btnVerifyUpi && termsAcceptedForPayment) {
                    btnVerifyUpi.classList.remove("hidden");
                }
                // Run OCR scanning on the uploaded receipt
                runTesseractOcrOnReceipt(file);
            } else {
                throw new Error(data.detail || "Failed to upload receipt file.");
            }
        } catch (err) {
            console.error("Receipt upload failed:", err);
            if (errorReceiptUpload) {
                errorReceiptUpload.textContent = err.message || "Upload failed. Please try again.";
            }
            if (receiptDropzone) receiptDropzone.classList.add("has-error");
            showToast("Upload Failed", err.message || "Failed to upload receipt.");
            resetReceiptUpload();
        }
    }

    function resetReceiptUpload() {
        currentPayment.receiptUrl = null;
        currentPayment.receiptName = null;
        currentPayment.receiptBase64 = null;
        detectedReceiptUtr = null;
        ocrRawText = "";
        ocrState = "idle";
        paymentCompleted = false;
        if (btnVerifyUpi) {
            btnVerifyUpi.classList.add("hidden");
            btnVerifyUpi.disabled = true;
        }
        if (btnSubmitFinal) {
            btnSubmitFinal.classList.add("hidden");
        }
        const paymentSuccess = document.getElementById("payment-success-msg");
        if (paymentSuccess) paymentSuccess.classList.add("hidden");
        if (upiPaymentPanel) upiPaymentPanel.classList.remove("hidden");
        compareAndRenderUtrState();
        if (receiptFileInput) receiptFileInput.value = "";
        if (dropzoneContent) dropzoneContent.classList.remove("hidden");
        if (receiptPreviewCard) receiptPreviewCard.classList.add("hidden");
        if (errorReceiptUpload) errorReceiptUpload.textContent = "";
        if (receiptDropzone) receiptDropzone.classList.remove("has-error");
        saveWorkflowState();
    }

    if (receiptFileInput) {
        receiptFileInput.addEventListener("change", (e) => {
            const file = e.target.files && e.target.files[0];
            if (file) handleReceiptUpload(file);
        });
    }

    if (btnBrowseFile) {
        btnBrowseFile.addEventListener("click", (e) => {
            e.stopPropagation();
            if (receiptFileInput) receiptFileInput.click();
        });
    }

    if (btnRemoveReceipt) {
        btnRemoveReceipt.addEventListener("click", (e) => {
            e.stopPropagation();
            resetReceiptUpload();
        });
    }

    if (receiptDropzone) {
        ["dragenter", "dragover"].forEach((eventName) => {
            receiptDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                receiptDropzone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            receiptDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                receiptDropzone.classList.remove("dragover");
            });
        });

        receiptDropzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt && dt.files;
            if (files && files.length > 0) {
                handleReceiptUpload(files[0]);
            }
        });
    }

    if (upiUtrInput) {
        upiUtrInput.addEventListener("input", (e) => {
            // Strictly digits only, max 12 digits
            e.target.value = e.target.value.replace(/\D/g, "").slice(0, 12);
            if (errorUpiUtr) errorUpiUtr.textContent = "";

            // If user changes UTR after completing payment, reset completion status
            if (paymentCompleted && currentPayment.paymentId && e.target.value !== currentPayment.paymentId) {
                paymentCompleted = false;
                if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                const paymentSuccess = document.getElementById("payment-success-msg");
                if (paymentSuccess) paymentSuccess.classList.add("hidden");
                if (upiPaymentPanel) upiPaymentPanel.classList.remove("hidden");
            }

            compareAndRenderUtrState();
        });
    }

    if (btnVerifyUpi) {
        btnVerifyUpi.addEventListener("click", async () => {
            if (!termsAcceptedForPayment) {
                showTermsError("Please accept Terms and Conditions before verifying payment.");
                return;
            }

            // Must have receipt uploaded
            const hasReceipt = Boolean(currentPayment.receiptUrl || currentPayment.receiptBase64);
            if (!hasReceipt) {
                if (errorReceiptUpload) errorReceiptUpload.textContent = "Payment receipt screenshot is mandatory before verification.";
                if (receiptDropzone) {
                    receiptDropzone.classList.add("has-error");
                    receiptDropzone.scrollIntoView({ behavior: "smooth", block: "center" });
                }
                showToast("Receipt Required", "Please upload your payment receipt before verifying.");
                return;
            }

            const utrValue = (upiUtrInput ? upiUtrInput.value : "").trim();
            if (!/^\d{12}$/.test(utrValue)) {
                if (errorUpiUtr) errorUpiUtr.textContent = "UTR number must be exactly 12 digits (numeric).";
                if (upiUtrInput) upiUtrInput.focus();
                showToast("Invalid UTR", "UPI Reference / UTR Number must be exactly 12 digits.");
                return;
            }
            if (errorUpiUtr) errorUpiUtr.textContent = "";

            if (ocrState === "scanning") {
                showToast("Scanning Receipt", "Please wait while OCR finishes scanning your receipt.");
                return;
            }

            // Re-check against raw OCR text if available
            if (ocrRawText && (!detectedReceiptUtr || detectedReceiptUtr !== utrValue)) {
                const candidate = extractLikelyUtr(ocrRawText, utrValue);
                if (candidate === utrValue) {
                    detectedReceiptUtr = utrValue;
                    ocrState = "match";
                }
            }

            // Block verification if OCR detects a mismatch
            if (ocrState === "mismatch" || (detectedReceiptUtr && utrValue !== detectedReceiptUtr)) {
                ocrState = "mismatch";
                compareAndRenderUtrState();
                if (errorUpiUtr) errorUpiUtr.textContent = `Entered UTR (${utrValue}) does not match Receipt UTR (${detectedReceiptUtr}). Please correct it.`;
                showToast("UTR Mismatch", "Entered UTR does not match the uploaded receipt.");
                if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                return;
            }

            // If not matched, do not allow verification
            if (ocrState !== "match") {
                ocrState = "unable";
                compareAndRenderUtrState();
                showToast("Verification Blocked", "Could not verify that entered UTR matches this receipt. Please upload a clear receipt showing the 12-digit UTR.");
                if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                return;
            }

            if (!currentPayment.orderId) {
                await loadUPIPaymentOrder();
            }

            if (!currentPayment.orderId) {
                showToast("Order Error", "Could not generate payment order. If this mobile/email is already registered, please use different details.");
                return;
            }

            const originalHtml = btnVerifyUpi.innerHTML;
            btnVerifyUpi.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
            btnVerifyUpi.disabled = true;

            try {
                const verifyRes = await fetch("/api/payment/verify", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        order_id: currentPayment.orderId,
                        utr_number: utrValue,
                        transaction_id: utrValue,
                    }),
                });

                const verifyData = await verifyRes.json();
                if (!verifyRes.ok) throw new Error(verifyData.detail || "Payment verification failed. Please check the UTR number.");

                currentPayment = {
                    orderId: verifyData.order_id || currentPayment.orderId,
                    paymentId: verifyData.transaction_id || utrValue,
                    gateway: "upi",
                    amount: currentPayment.amount,
                    receiptUrl: currentPayment.receiptUrl || null,
                    receiptName: currentPayment.receiptName || null,
                    receiptBase64: currentPayment.receiptBase64 || null,
                };

                paymentCompleted = true;
                setBackButtonAfterPaymentState();
                saveWorkflowState();

                // Complete Registration button ONLY shows if entered UTR matches receipt UTR and payment is confirmed
                if (ocrState === "match" && (!detectedReceiptUtr || utrValue === detectedReceiptUtr)) {
                    const paymentSuccess = document.getElementById("payment-success-msg");
                    const displayTxnId = document.getElementById("display-transaction-id");
                    if (paymentSuccess) paymentSuccess.classList.remove("hidden");
                    if (displayTxnId) displayTxnId.textContent = currentPayment.paymentId;
                    if (upiPaymentPanel) upiPaymentPanel.classList.add("hidden");
                    if (btnSubmitFinal) btnSubmitFinal.classList.remove("hidden");
                    showToast("Payment Under Verification", "Receipt uploaded and under verification! Click Complete Registration to finish.");
                } else {
                    if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                    compareAndRenderUtrState();
                }
            } catch (err) {
                paymentCompleted = false;
                if (btnSubmitFinal) btnSubmitFinal.classList.add("hidden");
                if (errorUpiUtr) errorUpiUtr.textContent = err.message || "Failed to verify payment.";
                alert(err.message || "Payment verification failed. Please check the UTR number and try again.");
            } finally {
                btnVerifyUpi.innerHTML = originalHtml;
                btnVerifyUpi.disabled = false;
            }
        });
    }

    btnSubmitFinal.addEventListener("click", async () => {
        const mode = document.querySelector('input[name="participationMode"]:checked')?.value;
        await submitRegistration(mode === "team");
    });

    btnBackStep3.addEventListener("click", () => {
        if (paymentCompleted) return;
        const mode = document.querySelector('input[name="participationMode"]:checked')?.value;
        showStep(mode === "team" ? 3 : 2);
    });

    const btnHomeEl = document.getElementById("btn-home");
    if (btnHomeEl) {
        btnHomeEl.addEventListener("click", () => {
            if (typeof confetti === "function") {
                confetti({
                    particleCount: 100,
                    spread: 90,
                    origin: { y: 0.5 }
                });
            }
            // Clear both workflow and form data so the app resets fully
            clearFormData();
            clearWorkflowState();
            // Navigate back to the landing view and reset to step 1
            showView(landingView);
            showStep(1);
            window.scrollTo(0, 0);
        });
    }

    window.addEventListener("beforeunload", saveWorkflowState);

    ensureMemberCards();
    loadColleges();
    loadTaskCategories();
    loadBranches();
    loadPublicSettings();
    loadFormData();
    restoreWorkflowProgress();
});

