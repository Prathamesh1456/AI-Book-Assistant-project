// AI Book Assistant — requires Firebase Auth; API calls send Bearer ID token.

const elements = {
    themeToggle: document.getElementById('themeToggle'),
    pdfInput: document.getElementById('pdfInput'),
    uploadBtn: document.getElementById('uploadBtn'),
    uploadArea: document.getElementById('uploadArea'),
    uploadStatus: document.getElementById('uploadStatus'),
    actionsSection: document.getElementById('actionsSection'),
    askBtn: document.getElementById('askBtn'),
    summarizeBtn: document.getElementById('summarizeBtn'),
    insightsBtn: document.getElementById('insightsBtn'),
    translateBtn: document.getElementById('translateBtn'),
    sentimentBtn: document.getElementById('sentimentBtn'),
    speakBtn: document.getElementById('speakBtn'),
    clearBtn: document.getElementById('clearBtn'),
    questionModal: document.getElementById('questionModal'),
    closeQuestionModal: document.getElementById('closeQuestionModal'),
    questionInput: document.getElementById('questionInput'),
    submitQuestion: document.getElementById('submitQuestion'),
    translateModal: document.getElementById('translateModal'),
    closeTranslateModal: document.getElementById('closeTranslateModal'),
    languageInput: document.getElementById('languageInput'),
    submitTranslation: document.getElementById('submitTranslation'),
    resultsSection: document.getElementById('resultsSection'),
    qaResult: document.getElementById('qaResult'),
    summaryResult: document.getElementById('summaryResult'),
    insightsResult: document.getElementById('insightsResult'),
    translationResult: document.getElementById('translationResult'),
    sentimentResult: document.getElementById('sentimentResult'),
    audioCard: document.getElementById('audioCard'),
    questionText: document.getElementById('questionText'),
    answerText: document.getElementById('answerText'),
    summaryText: document.getElementById('summaryText'),
    insightsText: document.getElementById('insightsText'),
    targetLanguage: document.getElementById('targetLanguage'),
    translationText: document.getElementById('translationText'),
    sentimentText: document.getElementById('sentimentText'),
    audioPlayer: document.getElementById('audioPlayer'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    userEmail: document.getElementById('userEmail'),
    btnLogout: document.getElementById('btnLogout'),
    historySection: document.getElementById('historySection'),
    historyList: document.getElementById('historyList'),
    historyEmpty: document.getElementById('historyEmpty'),
    refreshHistoryBtn: document.getElementById('refreshHistoryBtn'),
};

let currentSummary = '';
let isProcessing = false;
let pdfUploaded = false;

async function getAuthHeaders() {
    if (!window.firebaseReady || typeof firebase === 'undefined') {
        return {};
    }
    const u = firebase.auth().currentUser;
    if (!u) {
        return {};
    }
    const t = await u.getIdToken();
    return { Authorization: 'Bearer ' + t };
}

async function parseApiResponse(response) {
    const ct = response.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
        const text = await response.text();
        return {
            ok: false,
            data: {
                success: false,
                error: 'Server returned non-JSON (' + response.status + '). ' + text.slice(0, 200),
            },
        };
    }
    const data = await response.json();
    return { ok: response.ok, data };
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    if (!window.firebaseReady) {
        showToast('Firebase web config is missing. Set FIREBASE_WEB_* in server .env and restart.', 'error');
        return;
    }

    firebase.auth().onAuthStateChanged((user) => {
        if (!user) {
            window.location.replace('/login');
            return;
        }

        if (elements.userEmail) {
            elements.userEmail.textContent = user.email || user.uid;
        }
        if (elements.btnLogout) {
            elements.btnLogout.addEventListener('click', () => {
                firebase.auth().signOut().then(() => {
                    window.location.href = '/login';
                });
            });
        }

        initUpload();
        initActions();
        initModal();
        restoreSession();
    });
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    elements.themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = elements.themeToggle.querySelector('i');
    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

async function restoreSession() {
    try {
        const headers = await getAuthHeaders();
        const response = await fetch('/api/session', { headers });
        const { ok, data } = await parseApiResponse(response);
        if (!ok || !data.success) {
            return;
        }
        if (data.has_pdf) {
            pdfUploaded = true;
            enableActions();
            const name = data.pdf_name || 'your book';
            showUploadStatus('success', 'Signed in — loaded: ' + name + ' (' + data.text_length + ' chars stored)');
            if (data.truncated) {
                showToast('Stored text was truncated for Firestore size limits.', 'warning');
            }
        }
    } catch (e) {
        console.warn('Session restore failed', e);
    }
}

function initUpload() {
    elements.uploadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.pdfInput.click();
    });

    elements.uploadArea.addEventListener('click', () => {
        elements.pdfInput.click();
    });

    elements.pdfInput.addEventListener('change', handleFileSelect);

    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('dragover');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('dragover');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

async function handleFile(file) {
    if (!file.type || !file.type.includes('pdf')) {
        showUploadStatus('error', 'Invalid file type. Please upload a PDF file.');
        showToast('Please upload a PDF file', 'error');
        return;
    }

    if (file.size > 16 * 1024 * 1024) {
        showUploadStatus('error', 'File too large. Maximum size is 16MB.');
        showToast('File too large. Maximum size is 16MB.', 'error');
        return;
    }

    showLoading('Uploading PDF...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const auth = await getAuthHeaders();
        if (!auth.Authorization) {
            hideLoading();
            showToast('Not signed in. Redirecting…', 'warning');
            window.location.href = '/login';
            return;
        }

        const response = await fetch('/upload', {
            method: 'POST',
            headers: auth,
            body: formData,
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            pdfUploaded = true;
            showUploadStatus('success', data.message);
            showToast('PDF uploaded successfully!', 'success');
            if (data.truncated_stored) {
                showToast('Very long books are truncated when saved to the cloud.', 'warning');
            }
            enableActions();
            clearResults();
        } else {
            showUploadStatus('error', data.error || 'Upload failed');
            showToast(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Upload error:', error);
        showUploadStatus('error', 'Failed to upload PDF. Check network and sign-in.');
        showToast('Failed to upload PDF. Please try again.', 'error');
    }
}

function showUploadStatus(type, message) {
    elements.uploadStatus.className = 'upload-status ' + type;
    elements.uploadStatus.textContent = message;
    elements.uploadStatus.style.display = 'block';
}

function initActions() {
    elements.askBtn.addEventListener('click', openQuestionModal);
    elements.summarizeBtn.addEventListener('click', generateSummary);
    elements.insightsBtn.addEventListener('click', generateInsights);
    elements.translateBtn.addEventListener('click', openTranslateModal);
    elements.sentimentBtn.addEventListener('click', analyzeSentiment);
    elements.speakBtn.addEventListener('click', playSummaryAsSpeech);
    elements.clearBtn.addEventListener('click', clearAll);
    elements.refreshHistoryBtn.addEventListener('click', loadDocumentHistory);
}

function enableActions() {
    elements.actionsSection.style.display = 'block';
    elements.historySection.style.display = 'block';
    elements.askBtn.disabled = false;
    elements.summarizeBtn.disabled = false;
    elements.insightsBtn.disabled = false;
    elements.translateBtn.disabled = false;
    elements.sentimentBtn.disabled = false;
    elements.speakBtn.disabled = false;
    loadDocumentHistory();
}

function disableActions() {
    elements.askBtn.disabled = true;
    elements.summarizeBtn.disabled = true;
    elements.insightsBtn.disabled = true;
    elements.translateBtn.disabled = true;
    elements.sentimentBtn.disabled = true;
    elements.speakBtn.disabled = true;
}

function clearResults() {
    elements.resultsSection.style.display = 'none';
    elements.qaResult.style.display = 'none';
    elements.summaryResult.style.display = 'none';
    elements.insightsResult.style.display = 'none';
    elements.translationResult.style.display = 'none';
    elements.sentimentResult.style.display = 'none';
    elements.audioCard.style.display = 'none';
    currentSummary = '';
}

function initModal() {
    elements.closeQuestionModal.addEventListener('click', closeQuestionModal);
    elements.questionModal.querySelector('.modal-overlay').addEventListener('click', closeQuestionModal);
    elements.submitQuestion.addEventListener('click', submitQuestion);

    elements.closeTranslateModal.addEventListener('click', closeTranslateModal);
    elements.translateModal.querySelector('.modal-overlay').addEventListener('click', closeTranslateModal);
    elements.submitTranslation.addEventListener('click', submitTranslation);

    elements.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            submitQuestion();
        }
    });
}

function openQuestionModal() {
    elements.questionModal.classList.add('active');
    elements.questionInput.focus();
}

function closeQuestionModal() {
    elements.questionModal.classList.remove('active');
    elements.questionInput.value = '';
}

function openTranslateModal() {
    elements.translateModal.classList.add('active');
    elements.languageInput.focus();
}

function closeTranslateModal() {
    elements.translateModal.classList.remove('active');
}

async function submitQuestion() {
    const question = elements.questionInput.value.trim();

    if (!question) {
        showToast('Please enter a question', 'warning');
        return;
    }

    closeQuestionModal();
    showLoading('Getting answer from AI...');

    try {
        const headers = {
            'Content-Type': 'application/json',
            ...(await getAuthHeaders()),
        };
        const response = await fetch('/ask', {
            method: 'POST',
            headers,
            body: JSON.stringify({ question }),
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            displayAnswer(data.question, data.answer);
            showToast('Answer generated successfully!', 'success');
        } else {
            showToast(data.error || 'Request failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Ask error:', error);
        showToast('Failed to get answer. Please try again.', 'error');
    }
}

function displayAnswer(question, answer) {
    elements.resultsSection.style.display = 'block';
    elements.qaResult.style.display = 'block';

    elements.questionText.textContent = question;
    elements.answerText.textContent = answer;

    elements.qaResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function generateSummary() {
    showLoading('Generating summary...');

    try {
        const headers = await getAuthHeaders();
        const response = await fetch('/summarize', {
            method: 'GET',
            headers,
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            currentSummary = data.summary;
            displaySummary(data.summary);
            showToast('Summary generated successfully!', 'success');
        } else {
            showToast(data.error || 'Summary failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Summarize error:', error);
        showToast('Failed to generate summary. Please try again.', 'error');
    }
}

function displaySummary(summary) {
    elements.resultsSection.style.display = 'block';
    elements.summaryResult.style.display = 'block';

    elements.summaryText.textContent = summary;

    elements.summaryResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function playSummaryAsSpeech() {
    if (!currentSummary) {
        showToast('Please generate a summary first', 'warning');
        return;
    }

    showLoading('Converting to speech...');

    try {
        const headers = {
            'Content-Type': 'application/json',
            ...(await getAuthHeaders()),
        };
        const response = await fetch('/speak', {
            method: 'POST',
            headers,
            body: JSON.stringify({ text: currentSummary }),
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            displayAudio(data.audio_file);
            showToast('Audio generated successfully!', 'success');
        } else {
            showToast(data.error || 'TTS failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Speak error:', error);
        showToast('Failed to convert to speech. Please try again.', 'error');
    }
}

function displayAudio(audioPath) {
    elements.resultsSection.style.display = 'block';
    elements.audioCard.style.display = 'block';

    elements.audioPlayer.src = audioPath;

    elements.audioCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

    elements.audioPlayer.play().catch(() => {
        showToast('Click play on the audio player if sound does not start (browser autoplay policy).', 'warning');
    });
}

async function clearAll() {
    showLoading('Clearing data...');

    try {
        const headers = await getAuthHeaders();
        const response = await fetch('/clear', {
            method: 'POST',
            headers,
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            pdfUploaded = false;
            elements.uploadStatus.style.display = 'none';
            elements.actionsSection.style.display = 'none';
            disableActions();
            clearResults();
            elements.pdfInput.value = '';

            showToast('All data cleared', 'success');
        } else {
            showToast(data.error || 'Clear failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Clear error:', error);
        showToast('Failed to clear data', 'error');
    }
}

async function generateInsights() {
    showLoading('Extracting key insights...');

    try {
        const headers = await getAuthHeaders();
        const response = await fetch('/insights', {
            method: 'GET',
            headers,
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            displayInsights(data.insights);
            showToast('Key insights generated successfully!', 'success');
        } else {
            showToast(data.error || 'Insights generation failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Insights error:', error);
        showToast('Failed to generate insights. Please try again.', 'error');
    }
}

async function submitTranslation() {
    const targetLanguage = elements.languageInput.value;

    if (!targetLanguage) {
        showToast('Please select a target language', 'warning');
        return;
    }

    closeTranslateModal();
    showLoading('Translating document...');

    try {
        const headers = {
            'Content-Type': 'application/json',
            ...(await getAuthHeaders()),
        };
        const response = await fetch('/translate', {
            method: 'POST',
            headers,
            body: JSON.stringify({ language: targetLanguage }),
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            displayTranslation(data.translation, data.target_language);
            showToast('Document translated successfully!', 'success');
        } else {
            showToast(data.error || 'Translation failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Translation error:', error);
        showToast('Failed to translate document. Please try again.', 'error');
    }
}

async function analyzeSentiment() {
    showLoading('Analyzing sentiment...');

    try {
        const headers = await getAuthHeaders();
        const response = await fetch('/sentiment', {
            method: 'GET',
            headers,
        });

        const { data } = await parseApiResponse(response);
        hideLoading();

        if (data.success) {
            displaySentiment(data.analysis);
            showToast('Sentiment analysis completed!', 'success');
        } else {
            showToast(data.error || 'Sentiment analysis failed', 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Sentiment error:', error);
        showToast('Failed to analyze sentiment. Please try again.', 'error');
    }
}

function displayInsights(insights) {
    elements.resultsSection.style.display = 'block';
    elements.insightsResult.style.display = 'block';

    elements.insightsText.innerHTML = insights.replace(/\n/g, '<br>');

    elements.insightsResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function displayTranslation(translation, targetLanguage) {
    elements.resultsSection.style.display = 'block';
    elements.translationResult.style.display = 'block';

    elements.targetLanguage.textContent = targetLanguage;
    elements.translationText.innerHTML = translation.replace(/\n/g, '<br>');

    elements.translationResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function displaySentiment(analysis) {
    elements.resultsSection.style.display = 'block';
    elements.sentimentResult.style.display = 'block';

    elements.sentimentText.innerHTML = analysis.replace(/\n/g, '<br>');

    elements.sentimentResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function showLoading(message) {
    isProcessing = true;
    const loadingText = document.querySelector('.loading-text');
    if (loadingText) {
        loadingText.textContent = message;
    }
    elements.loadingOverlay.style.display = 'flex';
    disableActions();
}

function hideLoading() {
    isProcessing = false;
    elements.loadingOverlay.style.display = 'none';

    if (pdfUploaded) {
        enableActions();
    }
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;

    let icon = '';
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'error':
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
    }

    toast.innerHTML = icon + '<span>' + message + '</span>';

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && elements.questionModal.classList.contains('active')) {
        closeQuestionModal();
    }

    if (e.key === 'Escape' && elements.translateModal.classList.contains('active')) {
        closeTranslateModal();
    }

    if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        elements.pdfInput.click();
    }
});

document.addEventListener('submit', (e) => {
    e.preventDefault();
});

// Document History Functions
async function loadDocumentHistory() {
    try {
        const response = await fetch('/history?limit=10', {
            method: 'GET',
            headers: await getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayDocumentHistory(data.history);
        } else {
            console.error('Failed to load history:', data.error);
        }
    } catch (error) {
        console.error('Error loading document history:', error);
    }
}

function displayDocumentHistory(history) {
    if (!history || history.length === 0) {
        elements.historyEmpty.style.display = 'block';
        elements.historyList.innerHTML = '<div class="history-empty" id="historyEmpty"><i class="fas fa-folder-open"></i><p>No previous documents found</p></div>';
        return;
    }
    
    let historyHTML = '';
    history.forEach(doc => {
        const uploadDate = new Date(doc.uploadedAt).toLocaleDateString();
        const uploadTime = new Date(doc.uploadedAt).toLocaleTimeString();
        
        historyHTML += `
            <div class="history-item" data-book-id="${doc.bookId}">
                <div class="history-info">
                    <div class="history-title">${doc.pdfName}</div>
                    <div class="history-meta">
                        <span><i class="fas fa-calendar"></i> ${uploadDate} ${uploadTime}</span>
                        <span><i class="fas fa-file-alt"></i> ${doc.charCount.toLocaleString()} characters</span>
                        ${doc.truncated ? '<span><i class="fas fa-exclamation-triangle"></i> Truncated</span>' : ''}
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-sm btn-primary" onclick="loadHistoricalDocument('${doc.bookId}')" title="Load this document">
                        <i class="fas fa-folder-open"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteHistoricalDocument('${doc.bookId}')" title="Delete this document">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    elements.historyList.innerHTML = historyHTML;
}

async function loadHistoricalDocument(bookId) {
    try {
        showLoading();
        
        const response = await fetch(`/history/load/${bookId}`, {
            method: 'GET',
            headers: await getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            // Reload the page to refresh the current document state
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error loading historical document:', error);
        showToast('Failed to load document', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteHistoricalDocument(bookId) {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/history/delete/${bookId}`, {
            method: 'DELETE',
            headers: await getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadDocumentHistory(); // Refresh the history list
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error deleting historical document:', error);
        showToast('Failed to delete document', 'error');
    }
}
