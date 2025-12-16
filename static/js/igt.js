document.addEventListener('DOMContentLoaded', () => {
    // Define deck payouts and penalties
        const deckPayouts = {
            'A': 100,
            'B': 100,
            'C': 50,
            'D': 50
        };
        const deckPenalties = {
            'A': 250,
            'B': 250,
            'C': 50,
            'D': 50
        };

        function selectDeck(deck) {
            // Calculate payout and penalty
            const payout = deckPayouts[deck];
            let penalty = 0;
            if (Math.random() < 0.5) {  // 50% chance of penalty
                penalty = deckPenalties[deck];
            }

            // Calculate points earned
            const pointsEarned = payout - penalty;

            // Update total points
            const totalPointsElement = document.getElementById('total-points');
            const totalPoints = parseInt(totalPointsElement.textContent) + pointsEarned;
            totalPointsElement.textContent = totalPoints;

            // Show feedback overlay
            const feedbackOverlay = document.getElementById('feedback-overlay');
            feedbackOverlay.textContent = `Выигрыш: $${payout}\nШтраф: $${penalty}`;
            feedbackOverlay.style.display = 'block';

            // Hide feedback after 1 second
            setTimeout(() => {
                feedbackOverlay.style.display = 'none';
            }, 1000);

            // Send results to the server
            fetch('/save_igt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.href = '/next_trial/igt';
                }
            });
        }
});