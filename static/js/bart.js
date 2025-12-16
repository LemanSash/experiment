// bart.js
// Instruction functions
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
    cashOutButton.disabled = disabled;
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
    let pumps = 0;
    let popped = false;
    let pointsEarned = 0;
    let previousEarned = 0;


    // Initialize balloon
    balloon.style.backgroundColor = balloonType;
    cashOutButton.disabled = true;

    // Event listeners
    pumpButton.addEventListener('click', handlePump);
    cashOutButton.addEventListener('click', handleCashOut);

    // Обработчик событий на клавиатуру
    // document.addEventListener('keydown', function(e) {
    //     // Если фокус на каком-либо поле ввода, можно не реагировать
    //     if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") {
    //         return;
    //     }
    //     // Если отображается модальное окно с инструкцией, можно игнорировать нажатия
    //     if (document.getElementById('instructionModal').style.display === 'block') {
    //         return;
    //     }
    //     // Обработка нажатий
    //     if (e.code === "Space") {   // Клавиша пробел
    //         // Если кнопка Надуть доступна, симулируем нажатие
    //         if (!pumpButton.disabled) {
    //             e.preventDefault();  // Отключаем возможную прокрутку страницы
    //             pumpButton.click();
    //         }
    //     } else if (e.code === "Enter") { // Клавиша Enter
    //         if (!cashOutButton.disabled) {
    //             e.preventDefault();
    //             cashOutButton.click();
    //         }
    //     }
    // });

    function handlePump() {
        const rt = Date.now() - reactionStartTime;
        reactionTimes.push(rt);
        // перезапускаем таймер для следующего события
        reactionStartTime = Date.now();
        if (!popped) {
            pumps++;
             if (pumps === 1) {
                cashOutButton.disabled = false;
            }
            balloon.classList.add('balloon-pumped');
            setTimeout(() => balloon.classList.remove('balloon-pumped'), 300);
            updateBalloonSize();
            updateLastBalloonDisplay();
            checkExplosion();
        }
    }

    // function handleCashOut() {

    //     if (!popped) endTrial();
    // }

    function updateBalloonSize() {
        // balloon.style.width = `${100 + pumps * 10}px`;
        // balloon.style.height = `${150 + pumps * 10}px`;
        const container = document.querySelector('.balloon-container');
        const maxSize = container.clientHeight;
        const initialSize = 100;
        const maxPresses = 128;
        const increment = (maxSize - initialSize) / maxPresses;
        const newWidth = Math.min(initialSize + pumps * increment, maxSize);
        const newHeight = newWidth * 1.5;
        balloon.style.width = `${newWidth}px`;
        balloon.style.height = `${newHeight}px`;

        // const size = Math.min(
        //     100 + pumps * 15,  // Base size + pumps
        //     maxSize  // Don't exceed container size
        // );

        // balloon.style.width = `${size}px`;
        // balloon.style.height = `${size * 1.5}px`; // Maintain balloon proportion
    }

    function updateLastBalloonDisplay() {
        if (!popped) {
            pointsEarned = pumps * 5;
            //lastBalloonDisplay.textContent = (pointsEarned / 100).toFixed(2);
        } //else {
           // lastBalloonDisplay.textContent = '0.00';
       // }
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

    function handleCashOut() {
        if (!popped) {
            // RT нажатия "Забрать"
            const rt = Date.now() - reactionStartTime;
            reactionTimes.push(rt);
            reactionStartTime = Date.now();
            pointsEarned = pumps * 5;  // Only keep points if not popped
            endTrial();
        }
    }

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
                balloonType: balloonType,
                pumps,
                popped,
                pointsEarned: finalPoints,
                reaction_time: avgReactionTime
            }),
        })
        .then(response => response.json())
        .then(handleResponse);
    }


    function handleResponse(data) {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            window.location.reload();
        }
    }
});

