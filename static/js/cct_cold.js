document.addEventListener('DOMContentLoaded', () => {
    function selectCards(numCards) {
        fetch('/save_cct_cold', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(document.getElementById('trial-number').textContent.split('/')[0]),
                numCards: numCards
            })
        })
        .then(response => response.json())  // Parse JSON response
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;  // For final trial
            } else {
                window.location.href = '/next_trial/cct_cold';  // Regular trial
            }
        });
    }

    // Add event listeners to number buttons
    document.querySelectorAll('.number-button').forEach(button => {
        button.addEventListener('click', () => {
            const numCards = parseInt(button.dataset.numCards);
            selectCards(numCards);
        });
    });
});