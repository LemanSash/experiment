// static/js/cct_cold.js

let reactionStartTime;
let feedback_type;
let trialNumber;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize variables
    reactionStartTime = Date.now();
    feedback_type = document.body.dataset.feedbackType;
    trialNumber = parseInt(document.getElementById('trial-number').textContent.split('/')[0]);
    
    // Check if instructions should be shown
    if (document.body.dataset.showInstructions === 'true') {
        showInstructions();
        document.querySelectorAll('.number-card, .cct-card').forEach(el => {
            el.style.pointerEvents = 'none';
        });
    }
    
    // Add event listeners to number cards (вместо number-button)
    document.querySelectorAll('.number-card').forEach(button => {
        button.addEventListener('click', () => {
            const numCards = parseInt(button.textContent);
            selectCards(numCards);
        });
    });
});

function showInstructions() {
    document.getElementById('instruction-modal').style.display = 'block';
    document.querySelectorAll('.number-card, .cct-card').forEach(el => {
        el.style.pointerEvents = 'none';
    });
}

function closeInstructions() {
    document.getElementById('instruction-modal').style.display = 'none';
    document.querySelectorAll('.number-card, .cct-card').forEach(el => {
        el.style.pointerEvents = 'auto';
    });
    fetch('/mark_instructions_viewed/cct_cold', { method: 'POST' });
}

function showNotificationModal(message) {
    const notificationModal = document.createElement("div");
    notificationModal.id = "notification-modal";
    notificationModal.className = "modal";
    notificationModal.innerHTML = `
        <div class="modal-content">
            <h2>${message}</h2>
            <button onclick="hideNotificationModal()" class="btn-primary">
                <i class="fas fa-check"></i> Понял
            </button>
        </div>
    `;
    document.body.appendChild(notificationModal);
}

function hideNotificationModal() {
    const notificationModal = document.getElementById("notification-modal");
    if (notificationModal) {
        notificationModal.parentNode.removeChild(notificationModal);
    }
}

function showFeedbackMessage(selectedCards, badCardsSelected) {
    const feedbackDiv = document.getElementById('feedback');
    if (!feedbackDiv) return; // Проверяем, существует ли элемент
    
    feedbackDiv.style.display = 'block';
    feedbackDiv.innerHTML = `
        <i class="fas fa-info-circle"></i>
        Вы перевернули ${selectedCards} карт.<br/>
        Среди них: ${badCardsSelected} плохих.
    `;

    setTimeout(() => {
        feedbackDiv.style.display = 'none';
    }, 1000);
}

async function selectCards(numCards) {
    const reactionTime = Date.now() - reactionStartTime;

    // Disable all buttons
    document.querySelectorAll('.number-card').forEach(btn => {
        btn.style.pointerEvents = 'none';
        btn.classList.add('disabled');
    });

    try {
        const response = await fetch('/save_cct_cold', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(document.getElementById('trial-number').textContent.split('/')[0]),
                numCards: numCards,
                reaction_time: reactionTime
            })
        });

        const data = await response.json();
        
        // Show feedback based on conditions
        if (feedback_type === 'first_feedback') {
            if (trialNumber <= 48 && trialNumber > 0) {
                showFeedbackMessage(numCards, data.bad_cards_selected);
            } 
        } else if (feedback_type === 'last_feedback') {
            if (trialNumber >= 49) {
                showFeedbackMessage(numCards, data.bad_cards_selected);
            }
        }
        
        setTimeout(() => {
            if(data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                window.location.href = '/next_trial/cct_cold';
            }
        }, 1000);
    } catch (error) {
        console.error('Error:', error);
        const feedbackDiv = document.getElementById('feedback');
        if (feedbackDiv) {
            feedbackDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Ошибка соединения. Пожалуйста, подождите...`;
        }
        
        setTimeout(() => {
            if (feedbackDiv) feedbackDiv.style.display = 'none';
            document.querySelectorAll('.number-card').forEach(btn => {
                btn.style.pointerEvents = 'auto';
                btn.classList.remove('disabled');
            });
        }, 2000);
    }
}