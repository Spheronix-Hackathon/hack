document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('adminToken');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    let parsedDataState = null;
    let eligibleRecordsState = 0;
    let totalAmountState = 0;
    
    // Store submissions globally for easy access
    let submissionsList = [];

    const elLoadingState = document.getElementById('loadingState');
    const elUploadFlow = document.getElementById('uploadFlow');
    const elSubmissionsListState = document.getElementById('submissionsListState');
    const elSubmissionDetailState = document.getElementById('submissionDetailState');
    const elFlipImagesState = document.getElementById('flipImagesState');
    const elCollegesManagementState = document.getElementById('collegesManagementState');
    const statusBadge = document.getElementById('statusBadge');
    const nodalOfficerNote = document.getElementById('nodalOfficerNote');
    
    // Buttons
    const btnSubmissions = document.getElementById('btnSubmissions');
    const btnFlipImages = document.getElementById('btnFlipImages');
    const btnManageColleges = document.getElementById('btnManageColleges');
    const btnNewSubmission = document.getElementById('btnNewSubmission');
    const btnBackToSubmissions = document.getElementById('btnBackToSubmissions');
    const btnCancelSubmission = document.getElementById('btnCancelSubmission');

    let currentFlipImages = [];

    // Fetch user profile and status
    try {
        showState(elLoadingState);

        const res = await fetch('/api/dashboard/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!res.ok) {
            localStorage.removeItem('adminToken');
            window.location.href = '/login.html';
            return;
        }

        const user = await res.json();
        const isAdmin = user.role === 'admin' || (user.userId && user.userId.toLowerCase() === 'admin');
        
        // Display User info
        const displayName = isAdmin ? 'Super Administrator' : (user.role === 'principal' ? (user.principalName || user.userId) : (user.role === 'nodal_officer' ? (user.nodalOfficerName || user.userId) : user.userId));
        const roleDisplay = isAdmin ? 'System Admin' : (user.role === 'nodal_officer' ? 'Nodal Officer' : user.role === 'principal' ? 'Principal' : user.role).replace('_', ' ');

        document.getElementById('navUserId').textContent = displayName;
        document.getElementById('navUserRole').textContent = roleDisplay;

        if (isAdmin) {
            if (nodalOfficerNote) nodalOfficerNote.style.display = 'none';
            document.getElementById('dashboardTitle').innerHTML = `<i class="fas fa-tools"></i> Administration Control Center`;
            document.getElementById('dashboardSubtitle').innerHTML = `${displayName} <span style="opacity: 0.5; margin: 0 5px;">|</span> Flip Reel &amp; Submissions Manager`;
            if (btnFlipImages) btnFlipImages.style.display = 'inline-flex';
            if (btnManageColleges) btnManageColleges.style.display = 'inline-flex';
            if (btnSubmissions) btnSubmissions.style.display = 'inline-flex';

            statusBadge.textContent = 'Admin Mode';
            statusBadge.className = 'status-badge completed';

            // Show Flip Images manager by default for admin
            await loadAdminFlipImages();
            showState(elFlipImagesState);
            // Also preload submissions in background
            fetchSubmissions(false);
        } else {
            const collegeName = user.collegeName || 'Administration';
            document.getElementById('dashboardTitle').innerHTML = `<i class="fas fa-building"></i> ${collegeName}`;
            document.getElementById('dashboardSubtitle').innerHTML = `${displayName} <span style="opacity: 0.5; margin: 0 5px;">|</span> ${roleDisplay}`;

            // Fetch submissions for regular user
            await fetchSubmissions(true);
        }
        
    } catch (err) {
        console.error('Error fetching user data', err);
        elLoadingState.innerHTML = '<p style="color:var(--danger);">Error loading dashboard. Please refresh.</p>';
    }
    
    async function fetchSubmissions(switchToView = true) {
        try {
            const res = await fetch('/api/dashboard/submissions', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                submissionsList = data.submissions || [];
                renderSubmissionsList();
                
                if (submissionsList.length > 0) {
                    btnSubmissions.style.display = 'inline-flex';
                    if (switchToView) {
                        statusBadge.textContent = `Status: ${submissionsList.length} Submission(s)`;
                        statusBadge.className = 'status-badge completed';
                        showState(elSubmissionsListState);
                    }
                } else {
                    if (switchToView) {
                        btnSubmissions.style.display = 'none';
                        btnCancelSubmission.style.display = 'none'; // Can't cancel if it's the only view
                        statusBadge.textContent = 'Status: Pending Upload';
                        statusBadge.className = 'status-badge';
                        showState(elUploadFlow);
                        resetUploadFlow();
                    }
                }
            }
        } catch (err) {
            console.error('Error fetching submissions', err);
        }
    }
    
    function renderSubmissionsList() {
        const tbody = document.getElementById('submissionsTableBody');
        tbody.innerHTML = '';
        
        submissionsList.forEach(sub => {
            const tr = document.createElement('tr');
            tr.className = 'clickable-row';
            
            // Format date
            const d = new Date(sub.paymentTimestamp);
            const dateStr = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
            const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            
            const submitterName = sub.submitterName || sub.userId;
            const submitterRole = sub.submitterRole ? `<br><small style="color:var(--text-muted);">${sub.submitterRole}</small>` : '';
            
            tr.innerHTML = `
                <td><strong>${sub.submissionId || 'Legacy'}</strong></td>
                <td>${submitterName}${submitterRole}</td>
                <td>${dateStr}, ${timeStr}</td>
                <td><i class="fas fa-file-excel" style="color: #10b981;"></i> ${sub.originalFilename || 'Data.xlsx'}</td>
                <td>${sub.eligibleRecords}</td>
                <td><strong>₹${sub.totalAmount}</strong></td>
                <td><span style="color: var(--success); font-weight: 600;">${sub.status}</span></td>
            `;
            
            tr.addEventListener('click', () => loadSubmissionDetail(sub.submissionId));
            tbody.appendChild(tr);
        });
    }
    
    async function loadSubmissionDetail(submissionId) {
        if (!submissionId) return; // Legacy fallback if needed
        
        try {
            showState(elLoadingState);
            const res = await fetch(`/api/dashboard/submissions/${submissionId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (res.ok) {
                const sub = await res.json();
                
                // Populate details
                document.getElementById('detailSubId').textContent = sub.submissionId;
                
                const d = new Date(sub.paymentTimestamp);
                document.getElementById('detailDate').textContent = `${d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}, ${d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
                
                document.getElementById('detailAmount').textContent = `₹${sub.totalAmount}`;
                document.getElementById('detailFilename').innerHTML = `<i class="fas fa-file-excel"></i> ${sub.originalFilename || 'Data.xlsx'}`;
                
                // Render Table
                if (sub.csvData && sub.csvData.length > 0) {
                    renderDetailTable(sub.csvData);
                } else {
                    document.getElementById('detailDataTableBody').innerHTML = '<tr><td colspan="100%" style="text-align:center;">No data available</td></tr>';
                }

                // Render Payment Proof
                const imgProof = document.getElementById('detailPaymentProof');
                const msgNoProof = document.getElementById('detailNoPaymentProofMsg');
                if (sub.paymentProof) {
                    imgProof.src = sub.paymentProof;
                    imgProof.style.display = 'inline-block';
                    msgNoProof.style.display = 'none';
                } else {
                    imgProof.style.display = 'none';
                    msgNoProof.style.display = 'block';
                }
                
                showState(elSubmissionDetailState);
            }
        } catch (err) {
            console.error('Error fetching submission detail', err);
            showState(elSubmissionsListState);
        }
    }

    function renderDetailTable(data) {
        if (!data || data.length === 0) return;
        
        const head = document.getElementById('detailDataTableHead');
        const body = document.getElementById('detailDataTableBody');
        head.innerHTML = '';
        body.innerHTML = '';

        // Get headers from the first object
        const headers = Object.keys(data[0]);
        headers.forEach(h => {
            const th = document.createElement('th');
            th.textContent = h;
            head.appendChild(th);
        });

        // Add rows
        data.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(h => {
                const td = document.createElement('td');
                td.textContent = row[h] || '';
                tr.appendChild(td);
            });
            body.appendChild(tr);
        });
    }
    
    // View Management
    function showState(el) {
        if (elLoadingState) elLoadingState.style.display = 'none';
        if (elUploadFlow) elUploadFlow.style.display = 'none';
        if (elSubmissionsListState) elSubmissionsListState.style.display = 'none';
        if (elSubmissionDetailState) elSubmissionDetailState.style.display = 'none';
        if (elFlipImagesState) elFlipImagesState.style.display = 'none';
        if (elCollegesManagementState) elCollegesManagementState.style.display = 'none';
        
        if (el) el.style.display = 'block';
    }
    
    function resetUploadFlow() {
        document.getElementById('step-upload').style.display = 'block';
        document.getElementById('step-validation-error').style.display = 'none';
        document.getElementById('step-payment').style.display = 'none';
        document.getElementById('uploadForm').reset();
        document.getElementById('submitForm').reset();
    }
    
    // Event Listeners for Navigation
    if (btnFlipImages) {
        btnFlipImages.addEventListener('click', () => {
            showState(elFlipImagesState);
            loadAdminFlipImages();
        });
    }

    if (btnManageColleges) {
        btnManageColleges.addEventListener('click', () => {
            showState(elCollegesManagementState);
            loadAdminColleges();
        });
    }

    if (btnSubmissions) {
        btnSubmissions.addEventListener('click', () => {
            showState(elSubmissionsListState);
        });
    }
    
    btnBackToSubmissions.addEventListener('click', () => {
        showState(elSubmissionsListState);
    });
    
    btnNewSubmission.addEventListener('click', () => {
        btnCancelSubmission.style.display = 'inline-block';
        resetUploadFlow();
        showState(elUploadFlow);
    });
    
    btnCancelSubmission.addEventListener('click', () => {
        showState(elSubmissionsListState);
    });

    document.getElementById('btnLogout').addEventListener('click', () => {
        localStorage.removeItem('adminToken');
        window.location.href = '/login.html';
    });

    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('csvFile');
        const errEl = document.getElementById('uploadError');
        
        if (!fileInput.files.length) return;
        const file = fileInput.files[0];

        const formData = new FormData();
        formData.append('file', file);

        const btnSubmit = e.target.querySelector('button[type="submit"]');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const res = await fetch('/api/dashboard/upload-data', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                if (!data.success && data.status === "validation_failed") {
                    // Show validation error UI
                    document.getElementById('step-upload').style.display = 'none';
                    document.getElementById('step-validation-error').style.display = 'block';
                    
                    document.getElementById('valTotalRecords').textContent = data.summary.total_rows;
                    document.getElementById('valValidRecords').textContent = data.summary.valid_rows;
                    document.getElementById('valInvalidRecords').textContent = data.summary.invalid_rows;
                    document.getElementById('valWarnings').textContent = data.summary.warnings;
                    
                    const tbody = document.getElementById('validationErrorBody');
                    tbody.innerHTML = '';
                    
                    data.errors.forEach(err => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${err.row}</td>
                            <td><strong>${err.field}</strong></td>
                            <td style="color: var(--danger);">${err.value || '<em>Empty</em>'}</td>
                            <td>${err.message}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    parsedDataState = data.parsedData;
                    eligibleRecordsState = data.eligibleRecords;
                    totalAmountState = data.totalAmount;

                    const dynamicUpiId = data.upiId || 'admin@upi';

                    document.getElementById('lblRecords').textContent = eligibleRecordsState;
                    document.getElementById('lblAmountPer').textContent = data.amountPerRecord;
                    document.getElementById('lblTotalAmount').textContent = totalAmountState;
                    document.getElementById('displayUpiId').textContent = dynamicUpiId;
                    
                    if (data.bankDetails && data.bankDetails.accountNumber) {
                        document.getElementById('bankDetailsContainer').style.display = 'block';
                        document.getElementById('displayBankName').textContent = data.bankDetails.bankName;
                        document.getElementById('displayAccountNumber').textContent = data.bankDetails.accountNumber;
                        document.getElementById('displayIfscCode').textContent = data.bankDetails.ifscCode;
                        document.getElementById('displayAccountHolderName').textContent = data.bankDetails.accountHolderName;
                    } else {
                        document.getElementById('bankDetailsContainer').style.display = 'none';
                    }
                    
                    // Generate simple QR using standard UPI format via API or just image
                    const upiString = `upi://pay?pa=${dynamicUpiId}&pn=Spheronix&am=${totalAmountState}&cu=INR&tn=Hackathon Registration`;
                    document.getElementById('paymentQrCode').src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(upiString)}`;

                    document.getElementById('step-upload').style.display = 'none';
                    document.getElementById('step-validation-error').style.display = 'none';
                    document.getElementById('step-payment').style.display = 'block';
                }
            } else {
                errEl.textContent = data.detail || 'Upload failed';
                errEl.style.display = 'block';
            }
        } catch (err) {
            console.error(err);
            errEl.textContent = 'An unexpected error occurred.';
            errEl.style.display = 'block';
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fas fa-cogs"></i> Process File';
        }
    });

    document.getElementById('submitForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const proofFile = document.getElementById('proofFile').files[0];
        const csvFile = document.getElementById('csvFile').files[0];
        const errEl = document.getElementById('submitError');

        if (!proofFile) return;
        if (proofFile.size > 30 * 1024) {
            errEl.textContent = "Payment proof exceeds the 30 KB size limit.";
            errEl.style.display = 'block';
            return;
        }

        const formData = new FormData();
        formData.append('paymentProof', proofFile);
        formData.append('parsedData', JSON.stringify(parsedDataState));
        formData.append('eligibleRecords', eligibleRecordsState);
        formData.append('totalAmount', totalAmountState);
        formData.append('originalFilename', csvFile ? csvFile.name : 'Unknown.xlsx');

        const btnSubmit = e.target.querySelector('button[type="submit"]');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

        try {
            const res = await fetch('/api/payment/submit', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                // Application submitted successfully
                // Instead of reloading, we fetch submissions and go to list state
                await fetchSubmissions();
            } else {
                errEl.textContent = data.detail || 'Submission failed';
                errEl.style.display = 'block';
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Application';
            }
        } catch (err) {
            console.error(err);
            errEl.textContent = 'An unexpected error occurred.';
            errEl.style.display = 'block';
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Application';
        }
    });

    // ══════════════════════════════════════════════════════════════
    // HERO FLIP BANNER IMAGES MANAGEMENT (ADMIN)
    // ══════════════════════════════════════════════════════════════
    const tabUploadFileBtn = document.getElementById('tabUploadFileBtn');
    const tabLinkUrlBtn = document.getElementById('tabLinkUrlBtn');
    const flipUploadForm = document.getElementById('flipUploadForm');
    const flipLinkForm = document.getElementById('flipLinkForm');
    const flipStatusMsg = document.getElementById('flipStatusMsg');
    const flipCountBadge = document.getElementById('flipCountBadge');
    const flipReelGrid = document.getElementById('flipReelGrid');
    const miniFlipPreviewTrack = document.getElementById('miniFlipPreviewTrack');
    const btnResetFlipDefaults = document.getElementById('btnResetFlipDefaults');

    // Switch between File Upload tab and Link/URL tab
    if (tabUploadFileBtn && tabLinkUrlBtn) {
        tabUploadFileBtn.addEventListener('click', () => {
            tabUploadFileBtn.classList.add('active');
            tabLinkUrlBtn.classList.remove('active');
            flipUploadForm.style.display = 'block';
            flipLinkForm.style.display = 'none';
        });

        tabLinkUrlBtn.addEventListener('click', () => {
            tabLinkUrlBtn.classList.add('active');
            tabUploadFileBtn.classList.remove('active');
            flipLinkForm.style.display = 'block';
            flipUploadForm.style.display = 'none';
        });
    }

    function showFlipStatus(msg, isSuccess = true) {
        if (!flipStatusMsg) return;
        flipStatusMsg.textContent = msg;
        flipStatusMsg.style.display = 'block';
        if (isSuccess) {
            flipStatusMsg.style.background = '#dcfce7';
            flipStatusMsg.style.color = '#166534';
            flipStatusMsg.style.border = '1px solid #bbf7d0';
        } else {
            flipStatusMsg.style.background = '#fee2e2';
            flipStatusMsg.style.color = '#991b1b';
            flipStatusMsg.style.border = '1px solid #fecaca';
        }
        setTimeout(() => {
            if (flipStatusMsg) flipStatusMsg.style.display = 'none';
        }, 4500);
    }

    async function loadAdminFlipImages() {
        try {
            const res = await fetch('/api/flip-images?_t=' + Date.now());
            if (res.ok) {
                const data = await res.json();
                currentFlipImages = data.images || [];
                if (flipCountBadge) flipCountBadge.textContent = currentFlipImages.length;
                renderFlipAdminGrid(currentFlipImages);
                renderMiniPreview(currentFlipImages);
            }
        } catch (err) {
            console.error('Error loading flip images:', err);
        }
    }

    function renderFlipAdminGrid(images) {
        if (!flipReelGrid) return;
        flipReelGrid.innerHTML = '';

        if (!images || images.length === 0) {
            flipReelGrid.innerHTML = `
                <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--text-muted); background: #f8fafc; border: 2px dashed #e2e8f0; border-radius: 12px;">
                    <i class="fas fa-images" style="font-size: 2.5rem; color: #cbd5e1; margin-bottom: 12px; display: block;"></i>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 500;">No images in the flip banner reel.</p>
                    <p style="margin: 6px 0 0 0; font-size: 0.9rem;">Upload a file or add an image link above to populate the hero banner.</p>
                </div>
            `;
            return;
        }

        images.forEach((img, idx) => {
            const card = document.createElement('div');
            card.className = 'flip-reel-card';
            card.dataset.id = img.id || `img-${idx}`;

            const typeLabel = img.type === 'link' ? 'Web Link' : (img.type === 'default' ? 'Default' : 'Uploaded File');
            const typeClass = img.type === 'link' ? 'flip-type-link' : (img.type === 'default' ? 'flip-type-default' : 'flip-type-upload');

            card.innerHTML = `
                <div class="flip-reel-thumb-wrap">
                    <img src="${img.url}" alt="${img.title || 'Flip Image'}" loading="lazy" onerror="this.src='images/COMPANY LOGO.png';">
                    <span class="flip-order-badge">#${idx + 1}</span>
                    <span class="flip-type-badge ${typeClass}">${typeLabel}</span>
                </div>
                <div class="flip-reel-content">
                    <div>
                        <div class="flip-reel-title" title="${img.title || 'Untitled'}">${img.title || 'Event Highlight'}</div>
                        <div class="flip-reel-url" title="${img.url}">${img.url}</div>
                    </div>
                    <div class="flip-actions-row">
                        <div style="display: flex; gap: 5px;">
                            <button type="button" class="btn-mini btn-move-left" data-index="${idx}" title="Move Earlier (#${idx})" ${idx === 0 ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>
                                <i class="fas fa-arrow-left"></i>
                            </button>
                            <button type="button" class="btn-mini btn-move-right" data-index="${idx}" title="Move Later (#${idx + 2})" ${idx === images.length - 1 ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>
                                <i class="fas fa-arrow-right"></i>
                            </button>
                        </div>
                        <button type="button" class="btn-mini btn-mini-danger btn-delete-flip" data-id="${img.id || ''}" data-url="${img.url}" title="Delete from banner">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;

            flipReelGrid.appendChild(card);
        });

        // Attach Reorder Listeners
        flipReelGrid.querySelectorAll('.btn-move-left').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                if (idx > 0) moveFlipImage(idx, idx - 1);
            });
        });

        flipReelGrid.querySelectorAll('.btn-move-right').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                if (idx < currentFlipImages.length - 1) moveFlipImage(idx, idx + 1);
            });
        });

        // Attach Delete Listeners
        flipReelGrid.querySelectorAll('.btn-delete-flip').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const url = btn.dataset.url;
                deleteFlipImage(id, url);
            });
        });
    }

    function renderMiniPreview(images) {
        if (!miniFlipPreviewTrack) return;
        const validUrls = (images || []).map(img => img.url).filter(Boolean);

        if (validUrls.length === 0) {
            miniFlipPreviewTrack.innerHTML = '<div style="color:#94a3b8;padding:20px;font-size:0.9rem;">No active images to preview.</div>';
            return;
        }

        if (validUrls.length === 1) {
            miniFlipPreviewTrack.style.animation = 'none';
            miniFlipPreviewTrack.style.justifyContent = 'center';
            miniFlipPreviewTrack.innerHTML = `
                <div class="mini-preview-item" style="margin-right: 0; width: 100%; aspect-ratio: 2 / 1;">
                    <img src="${validUrls[0]}" alt="Banner Preview" style="object-fit: contain;">
                </div>
            `;
            return;
        }

        miniFlipPreviewTrack.style.animation = '';
        miniFlipPreviewTrack.style.justifyContent = '';

        let base = [...validUrls];
        while (base.length < 5) {
            base = base.concat(validUrls);
        }
        const loopList = [...base, ...base];

        miniFlipPreviewTrack.innerHTML = loopList.map(url => `
            <div class="mini-preview-item">
                <img src="${url}" alt="Banner Preview" loading="lazy">
            </div>
        `).join('');
    }

    // Handle Upload File Form
    if (flipUploadForm) {
        flipUploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('flipImageFile');
            const titleInput = document.getElementById('flipImageTitle');
            const btnSubmit = document.getElementById('btnSubmitFlipUpload');

            if (!fileInput.files.length) {
                showFlipStatus('Please select an image file to upload.', false);
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            if (titleInput.value.trim()) {
                formData.append('title', titleInput.value.trim());
            }

            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

            try {
                const res = await fetch('/api/admin/flip-images/upload', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });
                const data = await res.json();

                if (res.ok) {
                    showFlipStatus(data.message || 'Image uploaded and added to banner!', true);
                    flipUploadForm.reset();
                    await loadAdminFlipImages();
                } else {
                    showFlipStatus(data.detail || 'Upload failed.', false);
                }
            } catch (err) {
                console.error(err);
                showFlipStatus('Server error during image upload.', false);
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fas fa-upload"></i> Upload &amp; Add to Banner';
            }
        });
    }

    // Handle Add Link Form
    if (flipLinkForm) {
        flipLinkForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const urlInput = document.getElementById('flipImageLinkUrl');
            const titleInput = document.getElementById('flipImageLinkTitle');
            const btnSubmit = document.getElementById('btnSubmitFlipLink');

            const url = urlInput.value.trim();
            if (!url) {
                showFlipStatus('Please enter a valid image URL.', false);
                return;
            }

            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

            try {
                const res = await fetch('/api/admin/flip-images/link', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        url: url,
                        title: titleInput.value.trim() || undefined
                    })
                });
                const data = await res.json();

                if (res.ok) {
                    showFlipStatus(data.message || 'Image link added to banner!', true);
                    flipLinkForm.reset();
                    await loadAdminFlipImages();
                } else {
                    showFlipStatus(data.detail || 'Failed to add image link.', false);
                }
            } catch (err) {
                console.error(err);
                showFlipStatus('Server error adding image link.', false);
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fas fa-plus"></i> Add Link to Banner';
            }
        });
    }

    // Delete Flip Image
    async function deleteFlipImage(id, url) {
        if (!confirm('Are you sure you want to remove this image from the hero banner?')) {
            return;
        }

        try {
            const res = await fetch('/api/admin/flip-images/delete', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: id, url: url })
            });
            const data = await res.json();

            if (res.ok) {
                showFlipStatus(data.message || 'Image removed from reel.', true);
                await loadAdminFlipImages();
            } else {
                showFlipStatus(data.detail || 'Could not delete image.', false);
            }
        } catch (err) {
            console.error(err);
            showFlipStatus('Server connection error.', false);
        }
    }

    // Reorder Flip Images
    async function moveFlipImage(fromIdx, toIdx) {
        if (fromIdx === toIdx || fromIdx < 0 || toIdx < 0 || fromIdx >= currentFlipImages.length || toIdx >= currentFlipImages.length) {
            return;
        }

        const newOrder = [...currentFlipImages];
        const [movedItem] = newOrder.splice(fromIdx, 1);
        newOrder.splice(toIdx, 0, movedItem);

        currentFlipImages = newOrder;
        renderFlipAdminGrid(currentFlipImages);
        renderMiniPreview(currentFlipImages);

        const imageIds = currentFlipImages.map(img => img.id).filter(Boolean);

        try {
            const res = await fetch('/api/admin/flip-images/reorder', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ imageIds: imageIds })
            });
            if (res.ok) {
                showFlipStatus('Reel order updated!', true);
            }
        } catch (err) {
            console.error('Error saving reorder:', err);
        }
    }

    // Reset to Defaults
    if (btnResetFlipDefaults) {
        btnResetFlipDefaults.addEventListener('click', async () => {
            if (!confirm('Reset the banner to the original 6 default hackathon photos?')) {
                return;
            }

            try {
                const res = await fetch('/api/admin/flip-images/reset-defaults', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();

                if (res.ok) {
                    showFlipStatus('Reset to default flip images!', true);
                    await loadAdminFlipImages();
                } else {
                    showFlipStatus(data.detail || 'Reset failed.', false);
                }
            } catch (err) {
                console.error(err);
                showFlipStatus('Server error resetting defaults.', false);
            }
        });
    }

    // ==========================================
    // NOMINATED COLLEGES & INSTITUTIONS MANAGER
    // ==========================================
    function updateCollegeCount(textareaEl, countEl) {
        if (!textareaEl || !countEl) return;
        const lines = textareaEl.value.split('\n').map(l => l.trim()).filter(Boolean);
        countEl.textContent = lines.length;
    }

    function attachQuickAdd(btnId, inputId, textareaId, countId) {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        const textarea = document.getElementById(textareaId);
        const count = document.getElementById(countId);
        if (!btn || !input || !textarea) return;

        const doAdd = () => {
            const val = input.value.trim();
            if (!val) return;
            const current = textarea.value.trim();
            textarea.value = current ? current + '\n' + val : val;
            input.value = '';
            updateCollegeCount(textarea, count);
            input.focus();
        };

        btn.addEventListener('click', doAdd);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                doAdd();
            }
        });

        textarea.addEventListener('input', () => {
            updateCollegeCount(textarea, count);
        });
    }

    function showCollegeStatus(msg, isSuccess) {
        const el = document.getElementById('collegesStatusMsg');
        if (!el) return;
        el.style.display = 'block';
        el.innerHTML = isSuccess 
            ? `<i class="fas fa-check-circle" style="margin-right:8px;"></i>${msg}` 
            : `<i class="fas fa-exclamation-circle" style="margin-right:8px;"></i>${msg}`;
        if (isSuccess) {
            el.style.background = '#dcfce7';
            el.style.color = '#166534';
            el.style.border = '1px solid #bbf7d0';
        } else {
            el.style.background = '#fee2e2';
            el.style.color = '#991b1b';
            el.style.border = '1px solid #fecaca';
        }
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        setTimeout(() => {
            if (el) el.style.display = 'none';
        }, 5000);
    }

    async function loadAdminColleges() {
        try {
            const res = await fetch('/api/public-settings?_t=' + Date.now());
            if (!res.ok) return;
            const data = await res.json();

            const txtInnov = document.getElementById('txtBestInnovation');
            const txtEmerg = document.getElementById('txtBestEmerging');
            const txtEngage = document.getElementById('txtBestEngagement');
            const txtState = document.getElementById('txtStateColleges');
            const txtDist = document.getElementById('txtDistrictColleges');
            const txtUni = document.getElementById('txtUniversities');

            const parseList = (list) => {
                if (!list) return '';
                if (Array.isArray(list)) return list.join('\n');
                return String(list);
            };

            if (txtInnov) txtInnov.value = parseList(data.bestInnovationColleges || []);
            if (txtEmerg) txtEmerg.value = parseList(data.bestEmergingTechnologyColleges || data.bestEmergingTechColleges || []);
            if (txtEngage) txtEngage.value = parseList(data.bestStudentEngagementColleges || []);
            if (txtState) txtState.value = parseList(data.stateLevelColleges || []);
            if (txtDist) txtDist.value = parseList(data.districtLevelColleges || []);
            if (txtUni) txtUni.value = parseList(data.andhraBestUniversities || data.bestUniversities || []);

            updateCollegeCount(txtInnov, document.getElementById('countInnov'));
            updateCollegeCount(txtEmerg, document.getElementById('countEmerg'));
            updateCollegeCount(txtEngage, document.getElementById('countEngage'));
        } catch (err) {
            console.error('Error loading colleges for admin:', err);
        }
    }

    async function saveAdminColleges() {
        const parseLines = (id) => {
            const el = document.getElementById(id);
            if (!el) return [];
            return el.value.split('\n').map(l => l.trim()).filter(Boolean);
        };

        const payload = {
            bestInnovationColleges: parseLines('txtBestInnovation'),
            bestEmergingTechnologyColleges: parseLines('txtBestEmerging'),
            bestEmergingTechColleges: parseLines('txtBestEmerging'),
            bestStudentEngagementColleges: parseLines('txtBestEngagement'),
            stateLevelColleges: parseLines('txtStateColleges'),
            districtLevelColleges: parseLines('txtDistrictColleges'),
            andhraBestUniversities: parseLines('txtUniversities')
        };

        const saveBtns = [document.getElementById('btnSaveAllColleges'), document.getElementById('btnSaveAllCollegesBottom')].filter(Boolean);
        saveBtns.forEach(b => {
            b.disabled = true;
            b.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        });

        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok) {
                showCollegeStatus('All college nominations successfully saved and live on landing page!', true);
                await loadAdminColleges();
            } else {
                showCollegeStatus(data.detail || 'Could not save college nominations.', false);
            }
        } catch (err) {
            console.error('Error saving colleges:', err);
            showCollegeStatus('Network/server error while saving college nominations.', false);
        } finally {
            saveBtns.forEach(b => {
                b.disabled = false;
                b.innerHTML = '<i class="fas fa-save"></i> Save All to Website';
            });
        }
    }

    // Attach Quick Add & Count Handlers
    attachQuickAdd('btnAddInnov', 'addInnovInput', 'txtBestInnovation', 'countInnov');
    attachQuickAdd('btnAddEmerg', 'addEmergInput', 'txtBestEmerging', 'countEmerg');
    attachQuickAdd('btnAddEngage', 'addEngageInput', 'txtBestEngagement', 'countEngage');

    // Attach Save Buttons
    const btnSaveTop = document.getElementById('btnSaveAllColleges');
    if (btnSaveTop) btnSaveTop.addEventListener('click', saveAdminColleges);

    const btnSaveBottom = document.getElementById('btnSaveAllCollegesBottom');
    if (btnSaveBottom) btnSaveBottom.addEventListener('click', saveAdminColleges);
});

