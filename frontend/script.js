document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration & State ---
    const API_URL = '/ask';
    let isProcessing = false;
    let activityLog = [];

    // Sanitize HTML to prevent XSS
    const sanitizeHTML = (str) =>
      str.replace(/&/g,'&amp;').replace(/</g,'&lt;')
         .replace(/>/g,'&gt;').replace(/"/g,'&quot;');

    // Utility: Debounce function to prevent redundant calls
    const debounce = (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // --- UI Elements ---
    const navbar = document.getElementById('navbar');
    const chatOverlay = document.getElementById('chatOverlay');
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const typingIndicator = document.getElementById('typingIndicator');
    const activityList = document.getElementById('activityList');

    // --- Navigation & Scroll Effects ---
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // --- Guided Entry Flow & Section Interactivity ---
    const setupInteractions = () => {
        // Hero Guide Buttons
        document.querySelectorAll('.guide-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.getAttribute('data-target');
                const prompt = btn.getAttribute('data-prompt');
                
                scrollToSection(target);
                if (prompt) {
                    setTimeout(() => openChatAndAsk(prompt), 800);
                }
            });
        });

        // Section Interactivity (Clicking cards triggers AI)
        document.querySelectorAll('.guide-card').forEach(card => {
            card.addEventListener('click', () => {
                const title = card.querySelector('h3').innerText;
                openChatAndAsk(`Tell me more about ${title} in the context of voter registration.`);
            });
        });

        // Chat Suggestions
        document.querySelectorAll('.suggest-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                openChatAndAsk(query);
            });
        });
    };

    const scrollToSection = (id) => {
        const element = document.querySelector(id);
        if (element) {
            const offset = 100;
            const bodyRect = document.body.getBoundingClientRect().top;
            const elementRect = element.getBoundingClientRect().top;
            const elementPosition = elementRect - bodyRect;
            const offsetPosition = elementPosition - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    };

    // --- AI Chat Assistant Logic ---
    const openChatBtn = document.getElementById('openChatBtn');
    const closeChatBtn = document.getElementById('closeChatBtn');

    openChatBtn.onclick = () => {
        chatOverlay.classList.add('open');
        chatOverlay.setAttribute('aria-hidden', 'false');
        setTimeout(() => {
            const input = document.getElementById('userInput');
            if (input) input.focus();
        }, 100);
    };
    closeChatBtn.onclick = () => {
        chatOverlay.classList.remove('open');
        chatOverlay.setAttribute('aria-hidden', 'true');
        openChatBtn.focus();
    };

    // Keyboard: Escape closes chat, Tab traps focus inside
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && chatOverlay.classList.contains('open')) {
            closeChatBtn.click();
        }
        // Focus trap: keep Tab inside chat when open
        if (e.key === 'Tab' && chatOverlay.classList.contains('open')) {
            const focusable = chatOverlay.querySelectorAll('button, input, [tabindex]');
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    });

    const openChatAndAsk = (question) => {
        chatOverlay.classList.add('open');
        handleSendMessage(question);
    };

    const handleSendMessage = async (text) => {
        if (isProcessing || !text.trim()) return;

        isProcessing = true;
        appendMessage(text, 'user');
        userInput.value = '';
        
        showTyping(true);
        logActivity(text);

        try {
            const headers = { 'Content-Type': 'application/json' };
            if (window.authHeader) {
                headers['Authorization'] = window.authHeader;
            }

            chatMessages.setAttribute('aria-busy', 'true');
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ question: text })
            });

            const data = await response.json();
            showTyping(false);

            if (response.ok) {
                appendMessage(data.answer, 'ai');
            } else {
                handleAiError(response.status);
            }
        } catch (error) {
            console.error('AI API Error:', error);
            showTyping(false);
            handleAiError();
        } finally {
            isProcessing = false;
            chatMessages.setAttribute('aria-busy', 'false');
        }
    };

    const appendMessage = (text, type) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}-msg`;
        msgDiv.innerHTML = `<div class="msg-content">${sanitizeHTML(text)}</div>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const showTyping = (show) => {
        if (show) {
            typingIndicator.classList.remove('hidden');
        } else {
            typingIndicator.classList.add('hidden');
        }
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const handleAiError = (status) => {
        let msg = "Something went wrong. Please try again.";
        if (status === 503) msg = "AI service is temporarily unavailable. Please try again shortly.";
        if (status === 429) msg = "Too many requests. Please wait a moment.";
        if (status === 400) msg = "Your question was flagged by safety filters. Please rephrase it.";
        if (status === 500) msg = "An internal error occurred. Please try again.";
        appendMessage(msg, 'ai');
    };

    const debouncedSubmit = debounce((text) => {
        handleSendMessage(text);
    }, 300);

    chatForm.onsubmit = (e) => {
        e.preventDefault();
        const text = userInput.value;
        if (text.trim()) {
            debouncedSubmit(text);
        }
    };

    // --- Voting Day Simulator Logic ---
    const setupSimulator = () => {
        const navBtns = document.querySelectorAll('.sim-nav-btn');
        const steps = document.querySelectorAll('.sim-step');
        const nextBtns = document.querySelectorAll('.sim-next');

        const switchStep = (stepNum) => {
            navBtns.forEach(btn => btn.classList.remove('active'));
            steps.forEach(step => step.classList.remove('active'));

            document.querySelector(`.sim-nav-btn[data-sim="${stepNum}"]`).classList.add('active');
            document.getElementById(`sim-step-${stepNum}`).classList.add('active');
        };

        navBtns.forEach(btn => {
            btn.onclick = () => switchStep(btn.getAttribute('data-sim'));
        });

        nextBtns.forEach(btn => {
            btn.onclick = () => switchStep(btn.getAttribute('data-next'));
        });
    };

    // --- Activity Tracking (Firebase visibility) ---
    const logActivity = (query) => {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        activityLog.unshift({ query, time });
        if (activityLog.length > 5) activityLog.pop();
        updateActivityUI();
    };

    const updateActivityUI = () => {
        if (activityLog.length === 0) return;
        
        // Optimize DOM updates using DocumentFragment
        const fragment = document.createDocumentFragment();
        activityLog.forEach(item => {
            const div = document.createElement('div');
            div.className = 'activity-item animate-slide-up';
            div.innerHTML = `<span class="query">${sanitizeHTML(item.query)}</span>
                     <span class="time">${item.time}</span>`;
            fragment.appendChild(div);
        });
        
        activityList.innerHTML = '';
        activityList.appendChild(fragment);
    };

    // --- Initialize ---
    setupInteractions();
    setupSimulator();
});
