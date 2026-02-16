// document.addEventListener('DOMContentLoaded', () => {
//     // Define deck payouts and penalties
//         const deckPayouts = {
//             'A': 100,
//             'B': 100,
//             'C': 50,
//             'D': 50
//         };
//         const deckPenalties = {
//             'A': 250,
//             'B': 250,
//             'C': 50,
//             'D': 50
//         };

//         function selectDeck(deck) {
//             // Calculate payout and penalty
//             const payout = deckPayouts[deck];
//             let penalty = 0;
//             if (Math.random() < 0.5) {  // 50% chance of penalty
//                 penalty = deckPenalties[deck];
//             }

//             // Calculate points earned
//             const pointsEarned = payout - penalty;

//             // Update total points
//             const totalPointsElement = document.getElementById('total-points');
//             const totalPoints = parseInt(totalPointsElement.textContent) + pointsEarned;
//             totalPointsElement.textContent = totalPoints;

//             // Show feedback overlay
//             const feedbackOverlay = document.getElementById('feedback-overlay');
//             feedbackOverlay.textContent = `Выигрыш: $${payout}\nШтраф: $${penalty}`;
//             feedbackOverlay.style.display = 'block';

//             // Hide feedback after 1 second
//             setTimeout(() => {
//                 feedbackOverlay.style.display = 'none';
//             }, 1000);

//             // Send results to the server
//             fetch('/save_igt', {
//                 method: 'POST',
//                 headers: {'Content-Type': 'application/json'},
//                 body: JSON.stringify(data)
//             })
//             .then(response => response.json())
//             .then(data => {
//                 if (data.redirect_url) {
//                     window.location.href = data.redirect_url;
//                 } else {
//                     window.location.href = '/next_trial/igt';
//                 }
//             });
//         }
// });

// static/js/igt.js

let reactionStartTime;
let trialNumber;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize variables
    reactionStartTime = Date.now();
    trialNumber = parseInt(document.getElementById('trial-number').textContent.split('/')[0]);
    
    // Disable decks initially
    const decks = document.querySelectorAll('.deck-card');
    decks.forEach(deck => {
        deck.style.pointerEvents = 'none';
        deck.classList.add('disabled');
    });
    
    // Check if instructions should be shown
    if (document.body.dataset.showInstructions === 'true') {
        showInstructions();
    } else {
        // If instructions not needed - unlock after full load
        window.onload = () => {
            decks.forEach(deck => {
                deck.style.pointerEvents = 'auto';
                deck.classList.remove('disabled');
            });
        };
    }
    
    // Space key handler for closing feedback modal
    document.addEventListener('keydown', function(event) {
        if (event.code === "Space") {
            const modal = document.getElementById("feedback-modal");
            if (modal.style.display === 'block') {
                event.preventDefault();
                closeFeedback();
            }
        }
    });
});

function showInstructions() {
    document.getElementById('instruction-modal').style.display = 'block';
    // Disable game interactions
    document.querySelectorAll('.deck-card').forEach(deck => {
        deck.style.pointerEvents = 'none';
    });
}

function closeInstructions() {
    document.getElementById('instruction-modal').style.display = 'none';
    // Enable game interactions
    document.querySelectorAll('.deck-card').forEach(deck => {
        deck.style.pointerEvents = 'auto';
        deck.classList.remove('disabled');
    });
    // Mark instructions as viewed
    fetch('/mark_instructions_viewed/igt', {
        method: 'POST'
    });
}

function selectDeck(deck) {
    const reactionTime = Date.now() - reactionStartTime;
    
    // Get current trial number
    const trialNumberElement = document.getElementById('trial-number');
    const currentTrial = parseInt(trialNumberElement.textContent.split('/')[0]);

    // Send results to the server
    fetch('/save_igt', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
            deck: deck, 
            reaction_time: reactionTime 
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update feedback content
        document.getElementById('feedback-payout').textContent = data.payout;
        document.getElementById('feedback-penalty').textContent = data.penalty;
        document.getElementById('feedback-total').textContent = data.points_earned;

        // Show feedback overlay
        document.getElementById('feedback-modal').style.display = 'block';
    });
}

function closeFeedback() {
    // Hide feedback overlay
    document.getElementById('feedback-modal').style.display = 'none';
    
    // Disable decks while loading next trial
    const decks = document.querySelectorAll('.deck-card');
    decks.forEach(deck => {
        deck.style.pointerEvents = 'none';
        deck.classList.add('disabled');
    });

    // Automatically proceed to next trial or completion
    fetch('/next_trial/igt')
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        });
}