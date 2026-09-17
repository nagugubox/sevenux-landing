// ADS Final Quiz - Frontend Application Logic

// --- STATE MANAGEMENT ---
let allQuestions = [];
let activeQuestions = [];
let currentQuestionIndex = 0;
let selectedMode = 'iterative'; // default mode
let selectedCategory = null;

// Session stats
let sessionCorrectCount = 0;
let sessionIncorrectCount = 0;
let answeredInSession = [];

// Persistent user stats (LocalStorage)
const STORAGE_KEYS = {
    THEME: 'ads_quiz_theme',
    FAILED_IDS: 'ads_quiz_failed_ids',
    TOTAL_ANSWERED: 'ads_quiz_total_answered',
    TOTAL_CORRECT: 'ads_quiz_total_correct',
    CAT_STATS: 'ads_quiz_category_stats' // object of { categoryName: { answered, correct } }
};

let userStats = {
    failedQuestionIds: [],
    totalAnswered: 0,
    totalCorrect: 0,
    categoryStats: {}
};

// --- DOM ELEMENTS ---
const elements = {
    screenSetup: document.getElementById('screen-setup'),
    screenQuiz: document.getElementById('screen-quiz'),
    screenResults: document.getElementById('screen-results'),
    modalStats: document.getElementById('modal-stats'),
    
    // Header actions
    btnThemeToggle: document.getElementById('btn-theme-toggle'),
    btnStats: document.getElementById('btn-stats'),
    btnCloseStats: document.getElementById('btn-close-stats'),
    btnResetHistory: document.getElementById('btn-reset-history'),
    
    // Setup Screen
    setupCategoriesList: document.getElementById('setup-categories-list'),
    btnStartQuiz: document.getElementById('btn-start-quiz'),
    modeCards: document.querySelectorAll('.mode-card'),
    iterativeErrorsCount: document.getElementById('iterative-errors-count'),
    
    // Quiz Screen
    quizCategoryTag: document.getElementById('quiz-category-tag'),
    currentQuestionNum: document.getElementById('current-question-num'),
    totalQuestionsNum: document.getElementById('total-questions-num'),
    quizProgressBar: document.getElementById('quiz-progress-bar'),
    questionText: document.getElementById('question-text'),
    choicesList: document.getElementById('choices-list'),
    feedbackContainer: document.getElementById('feedback-container'),
    feedbackIcon: document.getElementById('feedback-icon'),
    feedbackTitle: document.getElementById('feedback-title'),
    explanationText: document.getElementById('explanation-text'),
    btnShowExplanation: document.getElementById('btn-show-explanation'),
    btnNextQuestion: document.getElementById('btn-next-question'),
    
    // Results Screen
    resScorePct: document.getElementById('res-score-pct'),
    resCorrectCount: document.getElementById('res-correct-count'),
    resIncorrectCount: document.getElementById('res-incorrect-count'),
    resErrorsLeft: document.getElementById('res-errors-left'),
    btnRestartErrors: document.getElementById('btn-restart-errors'),
    btnReturnMenu: document.getElementById('btn-return-menu'),
    resultsMessage: document.getElementById('results-message'),
    
    // Stats Modal
    statsTotalAnswered: document.getElementById('stats-total-answered'),
    statsAvgScore: document.getElementById('stats-avg-score'),
    statsErrorsQueued: document.getElementById('stats-errors-queued'),
    categoryStatsContainer: document.getElementById('category-stats-container')
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    loadLocalStats();
    initTheme();
    setupEventListeners();
    await fetchAppInitData();
});

// --- LOCAL STORAGE DATA LOAD ---
function loadLocalStats() {
    try {
        const failedIds = localStorage.getItem(STORAGE_KEYS.FAILED_IDS);
        userStats.failedQuestionIds = failedIds ? JSON.parse(failedIds) : [];
        
        userStats.totalAnswered = parseInt(localStorage.getItem(STORAGE_KEYS.TOTAL_ANSWERED)) || 0;
        userStats.totalCorrect = parseInt(localStorage.getItem(STORAGE_KEYS.TOTAL_CORRECT)) || 0;
        
        const catStats = localStorage.getItem(STORAGE_KEYS.CAT_STATS);
        userStats.categoryStats = catStats ? JSON.parse(catStats) : {};
        
        updateErrorsBadge();
    } catch (e) {
        console.error("Error loading LocalStorage values", e);
    }
}

function saveLocalStats() {
    localStorage.setItem(STORAGE_KEYS.FAILED_IDS, JSON.stringify(userStats.failedQuestionIds));
    localStorage.setItem(STORAGE_KEYS.TOTAL_ANSWERED, userStats.totalAnswered.toString());
    localStorage.setItem(STORAGE_KEYS.TOTAL_CORRECT, userStats.totalCorrect.toString());
    localStorage.setItem(STORAGE_KEYS.CAT_STATS, JSON.stringify(userStats.categoryStats));
    updateErrorsBadge();
}

function updateErrorsBadge() {
    const errorCount = userStats.failedQuestionIds.length;
    if (elements.iterativeErrorsCount) {
        if (errorCount === 0) {
            elements.iterativeErrorsCount.textContent = "¡Sin errores pendientes!";
            elements.iterativeErrorsCount.style.background = 'var(--color-success-bg)';
            elements.iterativeErrorsCount.style.color = 'var(--color-success)';
        } else {
            elements.iterativeErrorsCount.textContent = `${errorCount} ${errorCount === 1 ? 'pregunta fallada' : 'preguntas falladas'}`;
            elements.iterativeErrorsCount.style.background = 'var(--color-danger-bg)';
            elements.iterativeErrorsCount.style.color = 'var(--color-danger)';
        }
    }
}

// --- THEME MANAGEMENT ---
function initTheme() {
    const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';
    document.body.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem(STORAGE_KEYS.THEME, newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = elements.btnThemeToggle.querySelector('i');
    if (theme === 'light') {
        icon.className = 'fa-solid fa-sun';
    } else {
        icon.className = 'fa-solid fa-moon';
    }
}

// --- API DATA FETCHING ---
async function fetchAppInitData() {
    try {
        // Fetch all questions
        const qRes = await fetch('api/questions');
        allQuestions = await qRes.json();
        
        // Fetch categories
        const cRes = await fetch('api/categories');
        const categories = await cRes.json();
        
        renderCategoriesSetup(categories);
    } catch (e) {
        console.error("Error fetching initial quiz data", e);
        elements.setupCategoriesList.innerHTML = `<p class="error-text"><i class="fa-solid fa-circle-exclamation"></i> Error al conectar con el servidor local. Asegúrate de que FastAPI está corriendo.</p>`;
    }
}

function renderCategoriesSetup(categories) {
    elements.setupCategoriesList.innerHTML = '';
    
    // Add "Todos" chip
    const allChip = document.createElement('div');
    allChip.className = 'category-chip selected';
    allChip.textContent = 'Todos los temas';
    allChip.dataset.cat = 'all';
    allChip.addEventListener('click', () => selectCategoryChip(allChip, null));
    elements.setupCategoriesList.appendChild(allChip);
    
    categories.forEach(cat => {
        const chip = document.createElement('div');
        chip.className = 'category-chip';
        chip.textContent = cat;
        chip.dataset.cat = cat;
        chip.addEventListener('click', () => selectCategoryChip(chip, cat));
        elements.setupCategoriesList.appendChild(chip);
    });
}

function selectCategoryChip(chipElement, categoryValue) {
    // Deselect all
    elements.setupCategoriesList.querySelectorAll('.category-chip').forEach(c => {
        c.classList.remove('selected');
    });
    
    chipElement.classList.add('selected');
    selectedCategory = categoryValue;
}

// --- SETUP EVENT LISTENERS ---
function setupEventListeners() {
    // Theme
    elements.btnThemeToggle.addEventListener('click', toggleTheme);
    
    // Mode cards click
    elements.modeCards.forEach(card => {
        card.addEventListener('click', () => {
            elements.modeCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedMode = card.dataset.mode;
        });
    });
    
    // Start Quiz
    elements.btnStartQuiz.addEventListener('click', startQuizSession);
    
    // Quiz buttons
    elements.btnNextQuestion.addEventListener('click', handleNextQuestionClick);
    elements.btnShowExplanation.addEventListener('click', toggleExplanationBox);
    
    // Return menu
    elements.btnReturnMenu.addEventListener('click', showSetupScreen);
    elements.btnRestartErrors.addEventListener('click', restartFailedSession);
    
    // Stats modal
    elements.btnStats.addEventListener('click', openStatsModal);
    elements.btnCloseStats.addEventListener('click', closeStatsModal);
    elements.btnResetHistory.addEventListener('click', resetAllHistory);
    
    // Close modal on background click
    elements.modalStats.addEventListener('click', (e) => {
        if (e.target === elements.modalStats) closeStatsModal();
    });
}

// --- SCREEN NAVIGATION ---
function showScreen(screenElement) {
    elements.screenSetup.classList.remove('active');
    elements.screenQuiz.classList.remove('active');
    elements.screenResults.classList.remove('active');
    
    screenElement.classList.add('active');
}

function showSetupScreen() {
    loadLocalStats(); // Refresh errors badge count
    showScreen(elements.screenSetup);
}

// --- SHUFFLE HELPER ---
function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

// --- START SESSION ---
function startQuizSession() {
    activeQuestions = [];
    
    // 1. Filter by category if chosen
    let questionsPool = allQuestions;
    if (selectedCategory) {
        questionsPool = allQuestions.filter(q => q.category === selectedCategory);
    }
    
    // 2. Filter based on selected mode
    if (selectedMode === 'iterative') {
        // Find questions in pool that are marked as failed
        activeQuestions = questionsPool.filter(q => userStats.failedQuestionIds.includes(q.id));
        
        if (activeQuestions.length === 0) {
            // No errors in selected pool
            alert("¡No tenés errores acumulados en esta categoría! Se iniciará la práctica con preguntas generales para entrenar.");
            activeQuestions = shuffleArray(questionsPool).slice(0, 15);
        } else {
            // Shuffle errors list
            activeQuestions = shuffleArray(activeQuestions);
        }
    } else {
        // Regular Practice mode: shuffle and take a subset (max 15 questions per session to avoid fatigue)
        activeQuestions = shuffleArray(questionsPool).slice(0, 15);
    }
    
    // Reset session variables
    currentQuestionIndex = 0;
    sessionCorrectCount = 0;
    sessionIncorrectCount = 0;
    answeredInSession = [];
    
    showScreen(elements.screenQuiz);
    renderQuestion();
}

function restartFailedSession() {
    // Focus specifically on the errors from the session we just ended
    selectedMode = 'iterative';
    startQuizSession();
}

// --- RENDER QUESTION ---
function renderQuestion() {
    // Clean states
    elements.feedbackContainer.classList.add('hidden');
    elements.btnShowExplanation.classList.add('hidden');
    elements.btnNextQuestion.classList.add('hidden');
    
    const q = activeQuestions[currentQuestionIndex];
    
    // Category tag
    elements.quizCategoryTag.textContent = q.category;
    
    // Progress
    elements.currentQuestionNum.textContent = currentQuestionIndex + 1;
    elements.totalQuestionsNum.textContent = activeQuestions.length;
    const progressPct = ((currentQuestionIndex) / activeQuestions.length) * 100;
    elements.quizProgressBar.style.width = `${progressPct}%`;
    
    // Question Text
    elements.questionText.textContent = q.question || "Responde de acuerdo con los apuntes de ADS:";
    
    // Choices / Options
    elements.choicesList.innerHTML = '';
    
    // Shuffle choices to ensure correct answer is not always in the same place
    const shuffledOptions = shuffleArray(q.options);
    const alphabet = ['A', 'B', 'C', 'D', 'E', 'F'];
    
    shuffledOptions.forEach((opt, index) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn animate-fade-in';
        btn.style.animationDelay = `${index * 0.05}s`;
        
        const prefix = document.createElement('span');
        prefix.className = 'option-prefix';
        prefix.textContent = alphabet[index] || '';
        
        const textSpan = document.createElement('span');
        textSpan.className = 'option-text';
        textSpan.textContent = opt;
        
        btn.appendChild(prefix);
        btn.appendChild(textSpan);
        
        btn.addEventListener('click', () => handleOptionSelection(btn, opt, q));
        elements.choicesList.appendChild(btn);
    });
}

// --- OPTION SELECTION ---
function handleOptionSelection(selectedBtn, chosenOption, question) {
    const isCorrect = chosenOption.trim().toLowerCase() === question.correct_answer.trim().toLowerCase();
    
    // Disable all options
    const allButtons = elements.choicesList.querySelectorAll('.option-btn');
    allButtons.forEach(btn => {
        btn.disabled = true;
        
        // Highlight correct option in green
        const text = btn.querySelector('.option-text').textContent;
        if (text.trim().toLowerCase() === question.correct_answer.trim().toLowerCase()) {
            btn.classList.add('correct');
        }
    });
    
    // Record stats
    userStats.totalAnswered += 1;
    
    // Track stats by category
    if (!userStats.categoryStats[question.category]) {
        userStats.categoryStats[question.category] = { answered: 0, correct: 0 };
    }
    userStats.categoryStats[question.category].answered += 1;
    
    if (isCorrect) {
        sessionCorrectCount += 1;
        userStats.totalCorrect += 1;
        userStats.categoryStats[question.category].correct += 1;
        
        // Remove from failed questions list if correct
        userStats.failedQuestionIds = userStats.failedQuestionIds.filter(id => id !== question.id);
        
        // Feedback style
        elements.feedbackContainer.className = 'feedback-container correct-style animate-fade-in';
        elements.feedbackIcon.className = 'fa-solid fa-circle-check';
        elements.feedbackTitle.textContent = '¡Excelente! Respuesta Correcta.';
    } else {
        sessionIncorrectCount += 1;
        selectedBtn.classList.add('incorrect');
        
        // Add to failed list if not already there
        if (!userStats.failedQuestionIds.includes(question.id)) {
            userStats.failedQuestionIds.push(question.id);
        }
        
        // Feedback style
        elements.feedbackContainer.className = 'feedback-container incorrect-style animate-fade-in';
        elements.feedbackIcon.className = 'fa-solid fa-circle-xmark';
        elements.feedbackTitle.textContent = `Incorrecto. La respuesta correcta era: "${question.correct_answer}"`;
    }
    
    // Format explanation text with line breaks and bullets
    let formattedExplanation = question.explanation;
    // Replace ● bullet markers with formatted HTML
    formattedExplanation = formattedExplanation.replace(/●\s*(.*?)(?=\n|●|$)/g, '<li>$1</li>');
    if (formattedExplanation.includes('<li>')) {
        formattedExplanation = formattedExplanation.replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>');
        // clean redundant overlapping tags if any
        formattedExplanation = formattedExplanation.replace(/<\/ul>\s*<ul>/g, '');
    }
    
    // Replace page markers if missed
    formattedExplanation = formattedExplanation.replace(/--- PAGE \d+ ---/g, '');
    elements.explanationText.innerHTML = formattedExplanation;
    
    // Save stats
    saveLocalStats();
    
    // Show feedback and reveal footer buttons
    elements.feedbackContainer.classList.remove('hidden');
    elements.btnShowExplanation.classList.remove('hidden');
    elements.btnNextQuestion.classList.remove('hidden');
    
    // Update button text for last question
    if (currentQuestionIndex === activeQuestions.length - 1) {
        elements.btnNextQuestion.innerHTML = 'Ver Resultados <i class="fa-solid fa-circle-arrow-right"></i>';
    } else {
        elements.btnNextQuestion.innerHTML = 'Siguiente Pregunta <i class="fa-solid fa-arrow-right"></i>';
    }
}

// --- BUTTON TRIGGERS ---
function toggleExplanationBox() {
    const feedbackBox = elements.feedbackContainer;
    if (feedbackBox.classList.contains('hidden')) {
        feedbackBox.classList.remove('hidden');
    } else {
        // smooth scroll to explanation
        feedbackBox.scrollIntoView({ behavior: 'smooth' });
    }
}

function handleNextQuestionClick() {
    if (currentQuestionIndex < activeQuestions.length - 1) {
        currentQuestionIndex += 1;
        renderQuestion();
    } else {
        // Finish Quiz session
        showResultsScreen();
    }
}

// --- RESULTS DISPLAY ---
function showResultsScreen() {
    const total = activeQuestions.length;
    const scorePct = Math.round((sessionCorrectCount / total) * 100) || 0;
    
    elements.resScorePct.textContent = `${scorePct}%`;
    elements.resCorrectCount.textContent = sessionCorrectCount;
    elements.resIncorrectCount.textContent = sessionIncorrectCount;
    
    // Customize end message based on performance
    if (scorePct >= 90) {
        elements.resultsMessage.textContent = "¡Brillante! Estás al nivel de un experto en ADS.";
    } else if (scorePct >= 70) {
        elements.resultsMessage.textContent = "¡Muy bien! Tenés una base sólida para el examen.";
    } else if (scorePct >= 40) {
        elements.resultsMessage.textContent = "Vas por buen camino, pero necesitás repasar más las explicaciones.";
    } else {
        elements.resultsMessage.textContent = "Estudiá las explicaciones del apunte y volvé a intentarlo.";
    }
    
    // If we have failed questions left, show button to review them
    const errorsCount = userStats.failedQuestionIds.length;
    if (errorsCount > 0) {
        elements.resErrorsLeft.textContent = errorsCount;
        elements.btnRestartErrors.classList.remove('hidden');
    } else {
        elements.btnRestartErrors.classList.add('hidden');
    }
    
    // Fill the progress bar completely
    elements.quizProgressBar.style.width = `100%`;
    
    showScreen(elements.screenResults);
}

// --- STATS OVERLAY ---
function openStatsModal() {
    // Populate stats modal from local data
    elements.statsTotalAnswered.textContent = userStats.totalAnswered;
    
    const avgScore = userStats.totalAnswered > 0 
        ? Math.round((userStats.totalCorrect / userStats.totalAnswered) * 100) 
        : 0;
    elements.statsAvgScore.textContent = `${avgScore}%`;
    
    const errorsQueued = userStats.failedQuestionIds.length;
    elements.statsErrorsQueued.textContent = errorsQueued;
    
    // Category list render with progress bars
    elements.categoryStatsContainer.innerHTML = '';
    
    const categories = Object.keys(userStats.categoryStats);
    if (categories.length === 0) {
        elements.categoryStatsContainer.innerHTML = '<p class="muted-text">Aún no hay datos para mostrar. ¡Comenzá a jugar!</p>';
    } else {
        categories.forEach(cat => {
            const data = userStats.categoryStats[cat];
            const pct = Math.round((data.correct / data.answered) * 100) || 0;
            
            const row = document.createElement('div');
            row.className = 'category-stat-row';
            
            row.innerHTML = `
                <div class="cat-stat-info">
                    <span>${cat}</span>
                    <span>${pct}% (${data.correct}/${data.answered})</span>
                </div>
                <div class="cat-stat-bar-bg">
                    <div class="cat-stat-bar-fg" style="width: ${pct}%"></div>
                </div>
            `;
            elements.categoryStatsContainer.appendChild(row);
        });
    }
    
    elements.modalStats.classList.add('active');
}

function closeStatsModal() {
    elements.modalStats.classList.remove('active');
}

function resetAllHistory() {
    if (confirm("¿Estás seguro de que querés borrar tu historial de estadísticas y vaciar el registro de errores acumulados? Esta acción es irreversible.")) {
        localStorage.removeItem(STORAGE_KEYS.FAILED_IDS);
        localStorage.removeItem(STORAGE_KEYS.TOTAL_ANSWERED);
        localStorage.removeItem(STORAGE_KEYS.TOTAL_CORRECT);
        localStorage.removeItem(STORAGE_KEYS.CAT_STATS);
        
        // Reset state
        userStats = {
            failedQuestionIds: [],
            totalAnswered: 0,
            totalCorrect: 0,
            categoryStats: {}
        };
        
        saveLocalStats();
        closeStatsModal();
        alert("Historial restablecido exitosamente.");
    }
}
