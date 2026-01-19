// bart.js
let pumps = 0;
function showInstructions() {
    document.getElementById('instructionModal').style.display = 'block';
    disableGameControls(true);
}

function closeInstructions() {
    document.getElementById('instructionModal').style.display = 'none';
    disableGameControls(false);
    fetch('/mark_instructions_viewed/bart', { method: 'POST' });
}

function disableGameControls(disabled) {
    const pumpButton = document.getElementById('pump-button');
    const cashOutButton = document.getElementById('cash-out-button');
    pumpButton.disabled = disabled;
    // Only enable cash-out if not disabled AND pumps > 0
    // cashOutButton.disabled = disabled;
    cashOutButton.disabled = disabled || pumps === 0;  // Отключаем, если не было накачено
}

document.addEventListener('DOMContentLoaded', () => {
    // Instruction handling
    if (showInstructionsFlag) {
        showInstructions();
        disableGameControls(true);
    }
    // Собираем все RT внутри trial:
    let reactionTimes = [];
    // Инициализируем стартовый отсчёт
    let reactionStartTime = Date.now();

    // Game elements
    const balloon = document.getElementById('balloon');
    const pumpButton = document.getElementById('pump-button');
    const cashOutButton = document.getElementById('cash-out-button');
    const trialNumberDisplay = document.getElementById('trial-number');
    const totalPointsDisplay = document.getElementById('total-points');
    const lastBalloonDisplay = document.getElementById('last-balloon');

    // Game state
    //let pumps = 0;
    let popped = false;
    let pointsEarned = 0;
    let previousEarned = 0;
    let pumpNumber = 0;
    let breakPoint = explosionPoint;
    let trialEnded = false;
    let trialPoints = 0;



    // Initialize balloon
    balloon.style.backgroundColor = 'blue';
    cashOutButton.disabled = true;

    // Event listeners
    pumpButton.addEventListener('click', handlePump);
    cashOutButton.addEventListener('click', handleCashOut);

    // function handlePump() {
    //     pumpNumber++;
    //     const rt = Date.now() - reactionStartTime;
    //     reactionStartTime = Date.now();
    //     let popped = pumpNumber === breakPoint;
    //     if (!popped) {
    //         trialPoints = pumpNumber * 5;
    //         updateBalloonSize();
    //     } else {
    //         trialPoints = 0;
    //         trialEnded = true;
    //     }

    //     fetch('/save_bart', {
    //         method: 'POST',
    //         headers: {'Content-Type': 'application/json'},
    //         body: JSON.stringify({
    //             trialNumber: parseInt(trialNumberDisplay.textContent),
    //             pumpNumber: pumpNumber,
    //             breakPoint: breakPoint,
    //             reaction_time: rt,
    //             trialEnded: popped
    //         })
    //     });

    //     if (popped) {
    //         balloon.style.backgroundColor = 'red';
    //         setTimeout(() => window.location.reload(), 500);
    //     }
    // }

    let fetching = false;

    function handlePump() {
        if (fetching) return; // Заблокировать дополнительные запросы
        fetching = true;

        pumpNumber++;
        pumps++;
        const rt = Date.now() - reactionStartTime;
        reactionStartTime = Date.now();
        let popped = pumpNumber === breakPoint;
        if (!popped) {
            trialPoints = pumpNumber * 5;
            updateBalloonSize();
        } else {
            trialPoints = 0;
            trialEnded = true;
        }

        fetch('/save_bart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(trialNumberDisplay.textContent),
                pumpNumber: pumpNumber,
                breakPoint: breakPoint,
                reaction_time: rt,
                trialEnded: popped
            })
        }).then(() => {
            fetching = false;
        });

        if (popped) {
            balloon.style.backgroundColor = 'red';
            setTimeout(() => window.location.reload(), 500);
        }
    }


    function updateBalloonSize() {
        const container = document.querySelector('.balloon-container');
        const maxSize = container.clientHeight;
        const initialSize = 100;
        const maxPresses = 64;
        const increment = (maxSize - initialSize) / maxPresses;
        const newWidth = Math.min(initialSize + pumps * increment, maxSize);
        const newHeight = newWidth * 1.5;
        balloon.style.width = `${newWidth}px`;
        balloon.style.height = `${newHeight}px`;
    }

    function updateLastBalloonDisplay() {
        if (!popped) {
            pointsEarned = pumps * 5;
        } 
    }

    function checkExplosion() {
        if (pumps === explosionPoint) {
            const rt = Date.now() - reactionStartTime;
            reactionTimes.push(rt);
            popped = true;
            balloon.style.backgroundColor = 'red';
            cashOutButton.disabled = true;
            pointsEarned = 0;  // Обнуляем заработанные баллы
            lastBalloonDisplay.textContent = '0.00';  // Обновляем отображение
            endTrial();
        }
    }

    // function handleCashOut() {
    //     trialEnded = true;
    //     fetch('/save_bart', {
    //         method: 'POST',
    //         headers: {'Content-Type': 'application/json'},
    //         body: JSON.stringify({
    //             trialNumber: parseInt(trialNumberDisplay.textContent),
    //             pumpNumber: pumpNumber,
    //             breakPoint: breakPoint,
    //             reaction_time: Date.now() - reactionStartTime,
    //             trialEnded: true
    //         })
    //     }).then(() => window.location.reload());

    // }

    function handleCashOut() {
        trialEnded = true;
        fetch('/save_bart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(trialNumberDisplay.textContent),
                pumpNumber: pumpNumber,
                breakPoint: breakPoint,
                reaction_time: Date.now() - reactionStartTime,
                trialEnded: true
            })
        }).then(() => {
            endTrial();  // Завершаем испытание
        });
    }

    // function endTrial() {
    //     // вычислим среднее время реакции
    //     const sum = reactionTimes.reduce((a, b) => a + b, 0);
    //     const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
    //     // Ensure we send 0 points if popped
    //     const finalPoints = popped ? 0 : pumps * 5;
    //     previousEarned = finalPoints;

    //     fetch('/save_bart', {
    //         method: 'POST',
    //         headers: {'Content-Type': 'application/json'},
    //         body: JSON.stringify({
    //             trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
    //             pumps,
    //             popped,
    //             pointsEarned: finalPoints,
    //             reaction_time: avgReactionTime
    //         }),
    //     })
    //     .then(response => response.json())
    //     .then(handleResponse);
    // }

    function endTrial() {
        // вычислим среднее время реакции
        const sum = reactionTimes.reduce((a, b) => a + b, 0);
        const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
        // Ensure we send 0 points if popped
        const finalPoints = popped ? 0 : pumps * 5;
        previousEarned = finalPoints;

        fetch('/save_bart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
                pumpNumber,
                breakPoint,
                popped,
                pointsEarned: finalPoints,
                reaction_time: avgReactionTime
            }),
        })
        .then(response => response.json())
        .then(handleResponse);
    }


    // function handleResponse(data) {
    //     if (data.redirect_url) {
    //         window.location.href = data.redirect_url;
    //     } else {
    //         window.location.reload();
    //     }
    // }

    function handleResponse(data) {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            updateUI(); 
            resetGameState();  // Сбросить состояние игры
                   // Обновить UI
        }
    }

    function resetGameState() {
        pumps = 0;
        popped = false;
        pointsEarned = 0;
        previousEarned = 0;
        pumpNumber = 0;
        trialEnded = false;
        trialPoints = 0;
        balloon.style.backgroundColor = 'blue';
        cashOutButton.disabled = false;
        updateBalloonSize();  // Сбросить размер шарика
    }

    function updateUI() {
        trialNumberDisplay.textContent = parseInt(trialNumberDisplay.textContent.split('/')[0]) + 1;
        totalPointsDisplay.textContent = parseInt(totalPointsDisplay.textContent) + previousEarned;
        lastBalloonDisplay.textContent = previousEarned.toFixed(2);
    }
});

