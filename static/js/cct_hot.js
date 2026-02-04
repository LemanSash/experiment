function disableGameControls(disabled) {
    const action = disabled ? 'none' : 'auto';
    document.querySelectorAll('.hot-card').forEach(card => {
        card.style.pointerEvents = action;
    });
}

function closeInstructions() {
    document.getElementById('instruction-modal').style.display = 'none';
    disableGameControls(false);
    fetch('/mark_instructions_viewed/cct_hot', { method: 'POST' });
}

function showInstructions() {
    document.getElementById('instruction-modal').style.display = 'block';
    disableGameControls(true);
    const endTurnButton = document.getElementById('end-turn');
    endTurnButton.disabled = true;
}

document.addEventListener('DOMContentLoaded', () => {
    let flipNumber = 0;
    let trialFinished = false;
    let reactionTimes = [];
    let reactionStartTime = Date.now();
    // Check if instructions should be shown
    if (showInstructionsFlag) {
        showInstructions();
        // Disable game interactions
        disableGameControls(true);
    }
    const cards = document.querySelectorAll('.hot-card');
    const pointsDisplay = document.getElementById('points');
    const endTurnButton = document.getElementById('end-turn');
    const lossCardsDisplay = document.getElementById('loss-cards');
    const gainAmountDisplay = document.getElementById('gain-amount');
    const lossAmountDisplay = document.getElementById('loss-amount');
    const trialNumberDisplay = document.getElementById('trial-number');

    let points = 0;
    let lossCards = parseInt(lossCardsDisplay.textContent);
    let gainAmount = parseInt(gainAmountDisplay.textContent);
    let lossAmount = parseInt(lossAmountDisplay.textContent);
    const totalCards = 32;
    const safeThreshold = totalCards - lossCards;
    let trialNumber = parseInt(trialNumberDisplay.textContent.split('/')[0]);
    let selectedCardsCount = 0;
    endTurnButton.disabled = true;
    cards.forEach(card => {
        card.style.pointerEvents = 'auto';
        card.classList.remove('disabled');
    });

    // Обработчик событий на клавиатуру
    document.addEventListener('keydown', function(e) {
        // Если фокус на каком-либо поле ввода, можно не реагировать
        if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") {
            return;
        }
        // Если отображается модальное окно с инструкцией, можно игнорировать нажатия
        if (document.getElementById('instruction-modal').style.display === 'block') {
            return;
        }
        // Обработка нажатий
        if (e.code === "Space") {   // Клавиша пробел
            // Если кнопка Надуть доступна, симулируем нажатие
            if (!endTurnButton.disabled) {
                e.preventDefault();  // Отключаем возможную прокрутку страницы
                endTurnButton.click();
            }
        }
    });


    // Randomly assign loss cards
    const lossCardIndices = [];
    while (lossCardIndices.length < lossCards) {
        const randomIndex = Math.floor(Math.random() * 32);
        if (!lossCardIndices.includes(randomIndex)) {
            lossCardIndices.push(randomIndex);
        }
    }

    cards.forEach((card, index) => {
    card.addEventListener('click', () => {
        if (!card.classList.contains('flipped')) {
            card.classList.add('flipped');
            // Зафиксировать RT на эту карту
            const rt = Date.now() - reactionStartTime;
            reactionTimes.push(rt);
            reactionStartTime = Date.now();

            selectedCardsCount++;
            flipNumber++;
            const isLoss =
                (trialType === "experimental" && selectedCardsCount === safeThreshold + 1) ||
                (trialType === "random_loss" && lossCardIndices.includes(index));

            const currentResult = isLoss ? "loss" : "win";

            endTurnButton.disabled = false; // Enable when at least one card is flipped
            
            fetch('/save_cct_hot', { //ДОБАВИЛА
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: "flip",
                        trialNumber: trialNumber,
                        flip_number: flipNumber,
                        decision: 1,
                        result: currentResult,
                        current_points: points,
                        reaction_time: rt
                    })
                });
            if (trialType === "experimental") {
                // In experimental trials, do not assign any loss until safeThreshold+1
                if (selectedCardsCount === safeThreshold + 1) {
                    // For experimental trial, force loss on this card.
                    // Set score as: (safeThreshold * gainAmount) - lossAmount
                    points = 0 - lossAmount;
                    card.innerHTML = `<p style="color: red;">-${lossAmount}</p>`;
                    pointsDisplay.textContent = points;
                    cards.forEach(card => {
                        card.style.pointerEvents = 'none';
                        card.classList.add('disabled');
                    });
                    setTimeout(endTurn, 500); // Automatically end the trial.
                    return;
                } else {
                    // Otherwise, add the gain normally.
                    points += gainAmount;
                    card.innerHTML = `<p style="color: green;">+${gainAmount}</p>`;
                }
            } else if (trialType === "random_loss") {
                // In random loss trials, use previous logic.
                // (Assume you have code to preassign loss indices in this branch)
                if (lossCardIndices.includes(index)) {
                    points = 0 - lossAmount;
                    fetch('/save_cct_hot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: "flip",
                            trialNumber: trialNumber,
                            flip_number: flipNumber,
                            decision: 1,
                            result: currentResult,
                            current_points: points,
                            reaction_time: rt
                        })
                    });
                    card.innerHTML = `<p style="color: red;">-${lossAmount}</p>`;
                    pointsDisplay.textContent = points;
                    cards.forEach(card => {
                        card.style.pointerEvents = 'none';
                        card.classList.add('disabled');
                    });
                    setTimeout(endTurn, 500);
                    return;
                } else {
                    points += gainAmount;
                    card.innerHTML = `<p style="color: green;">+${gainAmount}</p>`;
                }
            }
            pointsDisplay.textContent = points;

        }
    });
});

    endTurnButton.addEventListener('click', endTurn);

    function endTurn() {
        if (trialFinished) return;
        trialFinished = true;

        const rt = Date.now() - reactionStartTime;
        if (!trialFinished) {
            fetch('/save_cct_hot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: "stop",
                    trialNumber: trialNumber,
                    flip_number: flipNumber + 1,
                    decision: 0,
                    current_points: points,
                    reaction_time: rt
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.href = '/next_trial/cct_hot';
                }
            });
        }
    }



});