// // // // bart.js
// // // let pumps = 0;
// // // // Добавьте две глобальные переменные для отслеживания состояния
// // // let isMouseDown = false;
// // // let clickInProgress = false;
// // // const pumpButton = document.getElementById('pump-button');
// // // // Добавьте обработчики событий mousedown/mouseup
// // // pumpButton.addEventListener('mousedown', () => {
// // //     isMouseDown = true;
// // // });

// // // pumpButton.addEventListener('mouseup', () => {
// // //     isMouseDown = false;
// // // });

// // // function showInstructions() {
// // //     document.getElementById('instructionModal').style.display = 'block';
// // //     disableGameControls(true);
// // // }

// // // function closeInstructions() {
// // //     document.getElementById('instructionModal').style.display = 'none';
// // //     disableGameControls(false);
// // //     fetch('/mark_instructions_viewed/bart', { method: 'POST' });
// // // }

// // // function disableGameControls(disabled) {
// // //     const pumpButton = document.getElementById('pump-button');
// // //     const cashOutButton = document.getElementById('cash-out-button');
// // //     pumpButton.disabled = disabled;
// // //     // Only enable cash-out if not disabled AND pumps > 0
// // //     // cashOutButton.disabled = disabled;
// // //     cashOutButton.disabled = disabled || pumps === 0;  // Отключаем, если не было накачено
// // // }

// // // document.addEventListener('DOMContentLoaded', () => {
// // //     // Instruction handling
// // //     if (showInstructionsFlag) {
// // //         showInstructions();
// // //         disableGameControls(true);
// // //     }
// // //     // Собираем все RT внутри trial:
// // //     let reactionTimes = [];
// // //     // Инициализируем стартовый отсчёт
// // //     let reactionStartTime = Date.now();

// // //     // Game elements
// // //     const balloon = document.getElementById('balloon');
// // //     const pumpButton = document.getElementById('pump-button');
// // //     const cashOutButton = document.getElementById('cash-out-button');
// // //     const trialNumberDisplay = document.getElementById('trial-number');
// // //     const totalPointsDisplay = document.getElementById('total-points');
// // //     const lastBalloonDisplay = document.getElementById('last-balloon');

// // //     // Game state
// // //     //let pumps = 0;
// // //     let popped = false;
// // //     let pointsEarned = 0;
// // //     let previousEarned = 0;
// // //     let pumpNumber = 0;
// // //     let breakPoint = explosionPoint;
// // //     let trialEnded = false;
// // //     let trialPoints = 0;
// // //     let cashed = false;

// // //     // Initialize balloon
// // //     balloon.style.backgroundColor = 'blue';
// // //     cashOutButton.disabled = true;

// // //     // Event listeners
// // //     pumpButton.addEventListener('click', handlePump);
// // //     cashOutButton.addEventListener('click', handleCashOut);

// // //     let fetching = false;

// // //     // function handlePump() {
// // //     //     if (isMouseDown || clickInProgress) return;
// // //     //     clickInProgress = true;
// // //     //     if (fetching) return; // Заблокировать дополнительные запросы
// // //     //     fetching = true;

// // //     //     pumpNumber++;
// // //     //     pumps++;
// // //     //     const rt = Date.now() - reactionStartTime;
// // //     //     reactionStartTime = Date.now();
// // //     //     let popped = pumpNumber === breakPoint;
// // //     //     if (!popped) {
// // //     //         trialPoints = pumpNumber * 5;
// // //     //         updateBalloonSize();
// // //     //     } else {
// // //     //         trialPoints = 0;
// // //     //         trialEnded = true;
// // //     //     }

// // //     //     // Снимаем запрет с кнопки "Забрать", если это первый надув
// // //     //     if (pumps === 1) {
// // //     //         cashOutButton.disabled = false;
// // //     //     }

// // //     //     // fetch('/save_bart', {
// // //     //     //     method: 'POST',
// // //     //     //     headers: {'Content-Type': 'application/json'},
// // //     //     //     body: JSON.stringify({
// // //     //     //         trialNumber: parseInt(trialNumberDisplay.textContent),
// // //     //     //         pumpNumber: pumpNumber,
// // //     //     //         breakPoint: breakPoint,
// // //     //     //         reaction_time: rt,
// // //     //     //         trialEnded: popped
// // //     //     //     })
// // //     //     // }).then(() => {
// // //     //     //     fetching = false;
// // //     //     //     clickInProgress = false;
// // //     //     // });
// // //     //     fetching = false;
// // //     //     clickInProgress = false;
// // //     //     if (popped) {
// // //     //         const sum = reactionTimes.reduce((a, b) => a + b, 0);
// // //     //         const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
// // //     //         // Ensure we send 0 points if popped
// // //     //         //const finalPoints = popped ? 0 : pumps * 5;
// // //     //         const finalPoints = trialPoints;
// // //     //         previousEarned = finalPoints;
// // //     //         pumpButton.disabled = false;
// // //     //         pumpButton.disabled = true;
// // //     //         balloon.style.backgroundColor = 'red';
// // //     //         // setTimeout(() => window.location.reload(), 500);
// // //     //         fetch('/save_bart', {
// // //     //             method: 'POST',
// // //     //             headers: {'Content-Type': 'application/json'},
// // //     //             body: JSON.stringify({
// // //     //                 trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
// // //     //                 pumpNumber,
// // //     //                 breakPoint,
// // //     //                 popped,
// // //     //                 pointsEarned: finalPoints,
// // //     //                 reaction_time: avgReactionTime
// // //     //             }),
// // //     //         }).then(() => {
// // //     //             console.log("fetched");
// // //     //             endTrial();  // Завершаем испытание
// // //     //     });
// // //     //         // setTimeout(() => endTrial(), 500);
// // //     //     }
// // //     // }


// // //     function updateBalloonSize() {
// // //         const container = document.querySelector('.balloon-container');
// // //         const maxSize = container.clientHeight;
// // //         const initialSize = 100;
// // //         const maxPresses = 64;
// // //         const increment = (maxSize - initialSize) / maxPresses;
// // //         const newWidth = Math.min(initialSize + pumps * increment, maxSize);
// // //         const newHeight = newWidth * 1.5;
// // //         balloon.style.width = `${newWidth}px`;
// // //         balloon.style.height = `${newHeight}px`;
// // //     }

// // //     function updateLastBalloonDisplay() {
// // //         if (!popped) {
// // //             pointsEarned = pumps * 5;
// // //         } 
// // //     }

// // //     function checkExplosion() {
// // //         if (pumps === explosionPoint) {
// // //             const rt = Date.now() - reactionStartTime;
// // //             reactionTimes.push(rt);
// // //             popped = true;
// // //             balloon.style.backgroundColor = 'red';
// // //             cashOutButton.disabled = true;
// // //             pointsEarned = 0;  // Обнуляем заработанные баллы
// // //             lastBalloonDisplay.textContent = '0.00';  // Обновляем отображение
// // //             endTrial();
// // //         }
// // //     }

// // //     // function handleCashOut() {
// // //     //     cashed = true;
// // //     //     trialEnded = true;
// // //     //     fetch('/save_bart', {
// // //     //         method: 'POST',
// // //     //         headers: {'Content-Type': 'application/json'},
// // //     //         body: JSON.stringify({
// // //     //             trialNumber: parseInt(trialNumberDisplay.textContent),
// // //     //             pumpNumber: pumpNumber,
// // //     //             breakPoint: breakPoint,
// // //     //             reaction_time: Date.now() - reactionStartTime,
// // //     //             trialEnded: true
// // //     //         })
// // //     //     }).then(() => {
// // //     //         endTrial();  // Завершаем испытание
// // //     //     });
// // //     // }

// // //     // function endTrial() {
// // //     //     // вычислим среднее время реакции
// // //     //     const sum = reactionTimes.reduce((a, b) => a + b, 0);
// // //     //     const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
// // //     //     // Ensure we send 0 points if popped
// // //     //     //const finalPoints = popped ? 0 : pumps * 5;
// // //     //     const finalPoints = trialPoints;
// // //     //     previousEarned = finalPoints;
// // //     //     pumpButton.disabled = false;
// // //     //     window.location.reload();
// // //     //     //handleResponse();
// // //     //     setTimeout(() => handleResponse, 500);
// // //     //     cashed = false;

// // //     // //     if (cashed == false) {
// // //     // //         fetch('/save_bart', {
// // //     // //             method: 'POST',
// // //     // //             headers: {'Content-Type': 'application/json'},
// // //     // //             body: JSON.stringify({
// // //     // //                 trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
// // //     // //                 pumpNumber,
// // //     // //                 breakPoint,
// // //     // //                 popped,
// // //     // //                 pointsEarned: finalPoints,
// // //     // //                 reaction_time: avgReactionTime
// // //     // //             }),
// // //     // //         })
        
// // //     // //         .then(response => response.json())
// // //     // //         // .then(window.location.reload())
// // //     // //         // // .then(setTimeout(() => handleResponse, 500));
// // //     // //         // .then(handleResponse);
// // //     // //         .then(window.location.reload())
// // //     // //         .then(handleResponse());
// // //     // // } else {
        
// // //     // // }
// // //     // }

// // //     function handlePump() {
// // //         if (isMouseDown || clickInProgress) return;
// // //         clickInProgress = true;
        
// // //         if (fetching) return; // Блокировка новых запросов
// // //         fetching = true;

// // //         pumpNumber++;
// // //         pumps++;
// // //         const rt = Date.now() - reactionStartTime;
// // //         reactionStartTime = Date.now();
// // //         let popped = pumpNumber >= breakPoint;

// // //         if (!popped) {
// // //             trialPoints = pumpNumber * 5;
// // //             updateBalloonSize();
// // //         } else {
// // //             trialPoints = 0;
// // //             trialEnded = true;
// // //         }

// // //         // Включаем кнопку "Забрать", если впервые нажата кнопка "Подуть"
// // //         if (pumps === 1 && !cashed) {
// // //             cashOutButton.disabled = false;
// // //         }

// // //         fetching = false;
// // //         clickInProgress = false;

// // //         if (popped) {
// // //             saveDataAndEndTrial();
// // //         }
// // //     }

// // //     function handleCashOut() {
// // //         cashed = true;
// // //         trialEnded = true;
// // //         saveDataAndEndTrial();
// // //     }

// // //     async function saveDataAndEndTrial() {
// // //         const sum = reactionTimes.reduce((a, b) => a + b, 0);
// // //         const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
// // //         const finalPoints = trialPoints;
// // //         previousEarned = finalPoints;

// // //         try {
// // //             await fetch('/save_bart', {
// // //                 method: 'POST',
// // //                 headers: {'Content-Type': 'application/json'},
// // //                 body: JSON.stringify({
// // //                     trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
// // //                     pumpNumber: pumpNumber,
// // //                     breakPoint: breakPoint,
// // //                     popped: popped,
// // //                     pointsEarned: finalPoints,
// // //                     reaction_time: avgReactionTime
// // //                 })
// // //             });
            
// // //             // После успешной отправки переходим к следующему этапу
// // //             //endTrial();
// // //             updateUI();      // Обновляем UI
// // //             resetGameState(); // Подготавливаемся к новому раунду
// // //             // window.location.reload();
// // //             endTrial();
// // //         } catch (err) {
// // //             console.error(err); // Если произошла ошибка, выводим сообщение
// // //         }
// // //     }

// // //     function endTrial() {
// // //         // Перезагружаем страницу только после сохранения данных
// // //         window.location.reload();
// // //     }

// // //     function handleResponse(data) {
// // //         if (data.redirect_url) {
// // //             window.location.href = data.redirect_url;
// // //         } else {
// // //             updateUI(); 
// // //             console.log("handled");
// // //             resetGameState();  // Сбросить состояние игры 
            
// // //         }
// // //     }

// // //     function resetGameState() {
// // //         pumps = 0;
// // //         popped = false;
// // //         pointsEarned = 0;
// // //         previousEarned = 0;
// // //         pumpNumber = 0;
// // //         trialEnded = false;
// // //         trialPoints = 0;
// // //         balloon.style.backgroundColor = 'blue';
// // //         cashOutButton.disabled = true;
// // //         updateBalloonSize();  // Сбросить размер шарика
// // //     }

// // //     function updateUI() {
// // //         //trialNumberDisplay.textContent = parseInt(trialNumberDisplay.textContent.split('/')[0]) + 1;
// // //         trialNumberDisplay.textContent = `${parseInt(trialNumberDisplay.textContent.split('/')[0]) + 1}/50`;
// // //         totalPointsDisplay.textContent = parseInt(totalPointsDisplay.textContent) + previousEarned;
// // //         lastBalloonDisplay.textContent = previousEarned.toFixed(2);
// // //     }
// // // });

// // let pumps = 0;
// // let isMouseDown = false;
// // let clickInProgress = false;
// // let fetching = false;
// // let popped = false;
// // let pointsEarned = 0;
// // let previousEarned = 0; // Тут объявлена переменная previousEarned
// // let pumpNumber = 0;
// // let breakPoint = null; // Сервер установил эту точку при загрузке страницы
// // let trialEnded = false;
// // let trialPoints = 0;
// // let cashed = false;
// // let reactionTimes = []; // Времена реакций игрока
// // let reactionStartTime = Date.now(); // Начало времени реакции

// // // Элементы страницы
// // const balloon = document.getElementById('balloon');
// // const pumpButton = document.getElementById('pump-button');
// // const cashOutButton = document.getElementById('cash-out-button');
// // const trialNumberDisplay = document.getElementById('trial-number');
// // const totalPointsDisplay = document.getElementById('total-points');
// // const lastBalloonDisplay = document.getElementById('last-balloon');

// // // Обработчики мыши
// // pumpButton.addEventListener('mousedown', () => {
// //     isMouseDown = true;
// // });

// // pumpButton.addEventListener('mouseup', () => {
// //     isMouseDown = false;
// // });

// // // Показ инструкций
// // function showInstructions() {
// //     document.getElementById('instructionModal').style.display = 'block';
// //     disableGameControls(true);
// // }

// // // Закрытие инструкций
// // function closeInstructions() {
// //     document.getElementById('instructionModal').style.display = 'none';
// //     disableGameControls(false);
// //     fetch('/mark_instructions_viewed/bart', { method: 'POST' });
// // }

// // // Управление доступностью кнопок
// // function disableGameControls(disabled) {
// //     pumpButton.disabled = disabled;
// //     cashOutButton.disabled = disabled || pumps === 0;
// // }


// // // Плавно увеличиваем шарик
// // function updateBalloonSize() {
// //     const container = document.querySelector('.balloon-container');
// //     const maxSize = container.clientHeight;
// //     const initialSize = 100;
// //     const maxPresses = 64;
// //     const increment = (maxSize - initialSize) / maxPresses;
// //     const newWidth = Math.min(initialSize + pumps * increment, maxSize);
// //     const newHeight = newWidth * 1.5;
// //     balloon.style.width = `${newWidth}px`;
// //     balloon.style.height = `${newHeight}px`;
// // }

// // // Основная логика игры
// // document.addEventListener('DOMContentLoaded', () => {
// //     // Инструкция появляется при первом заходе
// //     if (showInstructionsFlag) {
// //         showInstructions();
// //         disableGameControls(true);
// //     }

// //     // Элементы игры
// //     const balloon = document.getElementById('balloon');
// //     const pumpButton = document.getElementById('pump-button');
// //     const cashOutButton = document.getElementById('cash-out-button');
// //     const trialNumberDisplay = document.getElementById('trial-number');
// //     const totalPointsDisplay = document.getElementById('total-points');
// //     const lastBalloonDisplay = document.getElementById('last-balloon');
// //     let reactionTimes = []; // Времена реакций игрока
// //     let reactionStartTime = Date.now(); // Начало времени реакции
// //     // State
// //     let popped = false;
// //     let pointsEarned = 0;
// //     let previousEarned = 0;
// //     let pumpNumber = 0;
// //     let breakPoint = explosionPoint; // Сервер установил эту точку при загрузке страницы
// //     let trialEnded = false;
// //     let trialPoints = 0;
// //     let cashed = false;
// //     let fetching = false;

// //     // Обработчики событий
// //     pumpButton.addEventListener('click', handlePump);
// //     cashOutButton.addEventListener('click', handleCashOut);

// //     // Первоначальная инициализация
// //     balloon.style.backgroundColor = '';
// //     balloon.style.backgroundColor = 'blue';
// //     // balloon.classList.add('blue');
// //     cashOutButton.disabled = true;

// //     // Обработчик нажатия "надуть"
// //     function handlePump() {
// //         if (isMouseDown || clickInProgress) return;
// //         clickInProgress = true;

// //         if (fetching) return; // Предотвращение множества кликов одновременно
// //         fetching = true;

// //         pumpNumber++;
// //         pumps++;
// //         const rt = Date.now() - reactionStartTime;
// //         reactionStartTime = Date.now();
// //         reactionTimes.push(rt); // Фиксируем реакцию
// //         let popped = pumpNumber >= breakPoint;

// //         if (!popped) {
// //             trialPoints = pumpNumber * 5;
// //             updateBalloonSize();
// //         } else {
// //             trialPoints = 0;
// //             trialEnded = true;
// //             pumpButton.disabled = true;
// //             balloon.style.backgroundColor = '';
// //             balloon.style.backgroundColor = 'red';
// //             // balloon.classList.remove('blue'); // Удаляем предыдущий цвет
// //             // balloon.classList.add('red');
// //         }

// //         // Включаем кнопку "Забрать", если была первая попытка
// //         if (pumps === 1 ) {
// //             cashOutButton.disabled = false;
// //         }

// //         fetching = false;
// //         clickInProgress = false;

// //         if (popped) {
// //             saveDataAndEndTrial();
// //         }
// //     }

// //     // Обработчик нажатия "забрать"
// //     function handleCashOut() {
// //         cashed = true;
// //         trialEnded = true;
// //         saveDataAndEndTrial();
// //     }

// //     // Сохраняет данные и переходит к следующему уровню
// //     async function saveDataAndEndTrial() {
// //         const sum = reactionTimes.reduce((a, b) => a + b, 0);
// //         const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
// //         const finalPoints = trialPoints;
// //         previousEarned = finalPoints;

// //         try {
// //             const response = await fetch('/save_bart', {
// //                 method: 'POST',
// //                 headers: {'Content-Type': 'application/json'},
// //                 body: JSON.stringify({
// //                     trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
// //                     pumpNumber: pumpNumber,
// //                     breakPoint: breakPoint,
// //                     popped: popped,
// //                     pointsEarned: finalPoints,
// //                     reaction_time: avgReactionTime,
// //                     trialEnded: trialEnded
// //                 })
// //             });
// //             const data = await response.json();
// //             if (data.status === 'ok') {
// //                 // получаем общие очки от сервера и обновляем UI
// //                 console.log(data.total_points);
// //                 totalPointsDisplay.textContent = data.total_points;
// //                 previousEarned = finalPoints;
// //                 if (data.redirect_url) {
// //                     window.location.href = data.redirect_url;
// //                 } else {
// //                     endTrial(); // Если перенаправления нет, перезагружаем игру
// //                 }
// //             } else {
// //                 alert('Что-то пошло не так при сохранении.');
// //             }
// //             // Переход к следующему раунду после сохранения данных
// //             // updateUI();
// //             // resetGameState();
// //             // endTrial();
// //         } catch (err) {
// //             console.error(err); // Логируем ошибку
// //         }
// //     }

// //     // Завершение испытания (перезагрузка страницы)
// //     function endTrial() {
// //         window.location.reload(); // Полная перезагрузка страницы для нового испытания
// //     }

// //     // Инициализация первого уровня
// //     resetGameState();
// // });

// // // Обновляем интерфейс
// // function updateUI() {
// //     trialNumberDisplay.textContent = `${parseInt(trialNumberDisplay.textContent.split('/')[0]) + 1}/50`;
// //     totalPointsDisplay.textContent = parseInt(totalPointsDisplay.textContent) + previousEarned;
// //     lastBalloonDisplay.textContent = previousEarned.toFixed(2);
// // }

// // // Готовим новый раунд
// // function resetGameState() {
// //     pumps = 0;
// //     popped = false;
// //     pointsEarned = 0;
// //     previousEarned = 0;
// //     pumpNumber = 0;
// //     trialEnded = false;
// //     trialPoints = 0;
// //     balloon.style.backgroundColor = '';
// //     balloon.style.backgroundColor = 'blue';
// //     // balloon.classList.remove('red'); // Убираем предыдущие цвета
// //     // balloon.classList.add('blue');
// //     cashOutButton.disabled = true;
// //     pumpButton.disabled = false;
// //     updateBalloonSize(); // Сброс размера шарика
// // }

// // bart.js

// // Глобальные переменные состояния
// let pumps = 0;
// let isMouseDown = false;
// let clickInProgress = false;
// let fetching = false;
// let popped = false;
// let pointsEarned = 0;
// let previousEarned = 0;
// let pumpNumber = 0;
// let breakPoint = null;
// let trialEnded = false;
// let trialPoints = 0;
// let cashed = false;
// let reactionTimes = [];
// let reactionStartTime = Date.now();

// // DOM элементы (будут инициализированы в DOMContentLoaded)
// let balloon, pumpButton, cashOutButton, trialNumberDisplay, totalPointsDisplay, lastBalloonDisplay;

// // Флаги из шаблона
// let explosionPoint = null;
// let showInstructionsFlag = false;

// // Обработчики мыши для предотвращения двойных кликов
// function initMouseHandlers() {
//     pumpButton.addEventListener('mousedown', () => {
//         isMouseDown = true;
//     });

//     pumpButton.addEventListener('mouseup', () => {
//         isMouseDown = false;
//     });
    
//     pumpButton.addEventListener('mouseleave', () => {
//         isMouseDown = false;
//     });
// }

// // Показ инструкций
// function showInstructions() {
//     const modal = document.getElementById('instructionModal');
//     if (modal) {
//         modal.style.display = 'block';
//         disableGameControls(true);
//     }
// }

// // Закрытие инструкций
// function closeInstructions() {
//     const modal = document.getElementById('instructionModal');
//     if (modal) {
//         modal.style.display = 'none';
//         disableGameControls(false);
//         fetch('/mark_instructions_viewed/bart', { method: 'POST' });
//     }
// }

// // Управление доступностью кнопок
// function disableGameControls(disabled) {
//     if (pumpButton) pumpButton.disabled = disabled;
//     if (cashOutButton) cashOutButton.disabled = disabled || pumps === 0;
// }

// // Плавное увеличение шарика
// function updateBalloonSize() {
//     if (!balloon) return;
    
//     const container = document.querySelector('.balloon-container');
//     if (!container) return;
    
//     const maxSize = Math.min(container.clientHeight, 500);
//     const initialSize = 100;
//     const maxPresses = 64;
//     const increment = (maxSize - initialSize) / maxPresses;
//     const newWidth = Math.min(initialSize + pumps * increment, maxSize);
//     const newHeight = newWidth * 1.5;
    
//     balloon.style.width = `${newWidth}px`;
//     balloon.style.height = `${newHeight}px`;
// }

// // Обработчик нажатия "надуть"
// function handlePump() {
//     if (isMouseDown || clickInProgress || fetching || trialEnded) return;
    
//     clickInProgress = true;
//     fetching = true;

//     pumpNumber++;
//     pumps++;
    
//     const rt = Date.now() - reactionStartTime;
//     reactionStartTime = Date.now();
//     reactionTimes.push(rt);
    
//     popped = pumpNumber >= breakPoint;

//     if (!popped) {
//         trialPoints = pumpNumber * 5;
//         updateBalloonSize();
//     } else {
//         trialPoints = 0;
//         trialEnded = true;
//         pumpButton.disabled = true;
//         balloon.style.backgroundColor = 'red';
//     }

//     // Включаем кнопку "Забрать" после первого нажатия
//     if (pumps === 1) {
//         cashOutButton.disabled = false;
//     }

//     fetching = false;
//     clickInProgress = false;

//     if (popped) {
//         saveDataAndEndTrial();
//     }
// }

// // Обработчик нажатия "забрать"
// function handleCashOut() {
//     if (fetching || trialEnded) return;
    
//     cashed = true;
//     trialEnded = true;
//     saveDataAndEndTrial();
// }

// // Сохранение данных и завершение попытки
// async function saveDataAndEndTrial() {
//     const sum = reactionTimes.reduce((a, b) => a + b, 0);
//     const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
//     const finalPoints = trialPoints;
//     previousEarned = finalPoints;

//     try {
//         const response = await fetch('/save_bart', {
//             method: 'POST',
//             headers: {'Content-Type': 'application/json'},
//             body: JSON.stringify({
//                 trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
//                 pumpNumber: pumpNumber,
//                 breakPoint: breakPoint,
//                 popped: popped,
//                 pointsEarned: finalPoints,
//                 reaction_time: avgReactionTime
//             })
//         });
        
//         const data = await response.json();
        
//         if (data.status === 'ok') {
//             // Обновляем отображение очков
//             if (data.total_points !== undefined) {
//                 totalPointsDisplay.textContent = data.total_points;
//             }
            
//             // Обновляем последний заработок
//             lastBalloonDisplay.textContent = finalPoints.toFixed(2);
            
//             if (data.redirect_url) {
//                 // Если это последняя попытка - перенаправляем
//                 window.location.href = data.redirect_url;
//             } else {
//                 // Иначе перезагружаем для следующей попытки
//                 setTimeout(() => {
//                     window.location.reload();
//                 }, 500);
//             }
//         } else {
//             console.error('Server error:', data);
//             // Разблокируем кнопки в случае ошибки
//             pumpButton.disabled = false;
//             cashOutButton.disabled = pumps === 0;
//         }
//     } catch (err) {
//         console.error('Network error:', err);
//         // Разблокируем кнопки в случае ошибки сети
//         pumpButton.disabled = false;
//         cashOutButton.disabled = pumps === 0;
//     }
// }

// // Сброс состояния игры
// function resetGameState() {
//     pumps = 0;
//     popped = false;
//     pointsEarned = 0;
//     previousEarned = 0;
//     pumpNumber = 0;
//     trialEnded = false;
//     trialPoints = 0;
//     cashed = false;
//     reactionTimes = [];
//     reactionStartTime = Date.now();
    
//     if (balloon) {
//         balloon.style.backgroundColor = 'blue';
//         balloon.style.width = '100px';
//         balloon.style.height = '150px';
//     }
    
//     if (cashOutButton) cashOutButton.disabled = true;
//     if (pumpButton) pumpButton.disabled = false;
// }

// // Основная инициализация при загрузке страницы
// document.addEventListener('DOMContentLoaded', () => {
//     // Получаем значения из data-атрибутов или глобальных переменных
//     explosionPoint = parseInt(document.body.dataset.explosionPoint);
//     showInstructionsFlag = document.body.dataset.showInstructions === 'true';
    
//     // Инициализация DOM элементов
//     balloon = document.getElementById('balloon');
//     pumpButton = document.getElementById('pump-button');
//     cashOutButton = document.getElementById('cash-out-button');
//     trialNumberDisplay = document.getElementById('trial-number');
//     totalPointsDisplay = document.getElementById('total-points');
//     lastBalloonDisplay = document.getElementById('last-balloon');
    
//     // Проверка наличия всех необходимых элементов
//     if (!balloon || !pumpButton || !cashOutButton || !trialNumberDisplay || !totalPointsDisplay || !lastBalloonDisplay) {
//         console.error('Required DOM elements not found');
//         return;
//     }
    
//     // Инициализация точки взрыва
//     breakPoint = explosionPoint;
    
//     // Сброс состояния
//     resetGameState();
    
//     // Инициализация обработчиков мыши
//     initMouseHandlers();
    
//     // Добавление обработчиков кликов
//     pumpButton.addEventListener('click', handlePump);
//     cashOutButton.addEventListener('click', handleCashOut);
    
//     // Показ инструкций при первом заходе
//     if (showInstructionsFlag) {
//         showInstructions();
//     }
    
//     // Обновление размера шарика при изменении размера окна
//     window.addEventListener('resize', () => {
//         if (!popped && pumps > 0) {
//             updateBalloonSize();
//         }
//     });
// });

// // Делаем функции доступными глобально для HTML-обработчиков
// window.closeInstructions = closeInstructions;
// window.showInstructions = showInstructions;

// bart.js

// Глобальные переменные состояния
let pumps = 0;
let isMouseDown = false;
let clickInProgress = false;
let fetching = false;
let popped = false;
let pointsEarned = 0;
let previousEarned = 0;
let pumpNumber = 0;
let breakPoint = null;
let trialEnded = false;
let trialPoints = 0;
let cashed = false;
let reactionTimes = [];
let reactionStartTime = Date.now();

// DOM элементы
let balloon, pumpButton, cashOutButton, trialNumberDisplay, totalPointsDisplay, lastBalloonDisplay;

// Флаг инструкций
let showInstructionsFlag = false;

// Получаем explosion point из сессии через сервер
async function getExplosionPoint() {
    try {
        const response = await fetch('/get_bart_explosion_point', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get explosion point');
        }
        
        const data = await response.json();
        return data.explosionPoint;
    } catch (error) {
        console.error('Error getting explosion point:', error);
        return 8; // Значение по умолчанию в случае ошибки
    }
}

// Обработчики мыши для предотвращения множественных кликов
function initMouseHandlers() {
    pumpButton.addEventListener('mousedown', () => {
        isMouseDown = true;
    });

    pumpButton.addEventListener('mouseup', () => {
        isMouseDown = false;
    });
    
    pumpButton.addEventListener('mouseleave', () => {
        isMouseDown = false;
    });
}

// Показ инструкций
function showInstructions() {
    const modal = document.getElementById('instructionModal');
    if (modal) {
        modal.style.display = 'block';
        disableGameControls(true);
    }
}

// Закрытие инструкций
function closeInstructions() {
    const modal = document.getElementById('instructionModal');
    if (modal) {
        modal.style.display = 'none';
        disableGameControls(false);
        fetch('/mark_instructions_viewed/bart', { method: 'POST' });
    }
}

// Управление доступностью кнопок
function disableGameControls(disabled) {
    if (pumpButton) pumpButton.disabled = disabled;
    if (cashOutButton) cashOutButton.disabled = disabled || pumps === 0;
}

// Плавное увеличение шарика
function updateBalloonSize() {
    if (!balloon) return;
    
    const container = document.querySelector('.balloon-container');
    if (!container) return;
    
    const maxSize = Math.min(container.clientHeight, 500);
    const initialSize = 100;
    const maxPresses = 64;
    const increment = (maxSize - initialSize) / maxPresses;
    const newWidth = Math.min(initialSize + pumps * increment, maxSize);
    const newHeight = newWidth * 1.5;
    
    balloon.style.width = `${newWidth}px`;
    balloon.style.height = `${newHeight}px`;
}

// // Обработчик нажатия "надуть"
// async function handlePump() {
//     if (isMouseDown || clickInProgress || fetching || trialEnded) return;
    
//     clickInProgress = true;
//     fetching = true;

//     pumpNumber++;
//     pumps++;
    
//     const rt = Date.now() - reactionStartTime;
//     reactionStartTime = Date.now();
//     reactionTimes.push(rt);
    
//     // Проверяем, не лопнул ли шарик
//     popped = pumpNumber >= breakPoint;

//     if (!popped) {
//         trialPoints = pumpNumber * 5;
//         updateBalloonSize();
//     } else {
//         trialPoints = 0;
//         trialEnded = true;
//         pumpButton.disabled = true;
//         balloon.style.backgroundColor = 'red';
//     }

//     // Включаем кнопку "Забрать" после первого нажатия
//     if (pumps === 1) {
//         cashOutButton.disabled = false;
//     }

//     fetching = false;
//     clickInProgress = false;

//     if (popped) {
//         await saveDataAndEndTrial();
//     }
// }

// // Обработчик нажатия "забрать"
// async function handleCashOut() {
//     if (fetching || trialEnded) return;
    
//     cashed = true;
//     trialEnded = true;
//     await saveDataAndEndTrial();
// }

// // Сохранение данных и завершение попытки
// async function saveDataAndEndTrial() {
//     const sum = reactionTimes.reduce((a, b) => a + b, 0);
//     const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
//     const finalPoints = trialPoints;
//     previousEarned = finalPoints;

//     try {
//         const response = await fetch('/save_bart', {
//             method: 'POST',
//             headers: {'Content-Type': 'application/json'},
//             body: JSON.stringify({
//                 trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
//                 pumpNumber: pumpNumber,
//                 popped: popped,
//                 pointsEarned: finalPoints,
//                 reaction_time: avgReactionTime
//                 // breakPoint не отправляем на сервер, так как он уже есть в сессии
//             })
//         });
        
//         const data = await response.json();
        
//         if (data.status === 'ok') {
//             // Обновляем отображение очков
//             if (data.total_points !== undefined) {
//                 totalPointsDisplay.textContent = data.total_points;
//             }
            
//             // Обновляем последний заработок
//             lastBalloonDisplay.textContent = finalPoints.toFixed(2);
            
//             if (data.redirect_url) {
//                 // Если это последняя попытка - перенаправляем
//                 window.location.href = data.redirect_url;
//             } else {
//                 // Иначе перезагружаем для следующей попытки
//                 setTimeout(() => {
//                     window.location.reload();
//                 }, 500);
//             }
//         } else {
//             console.error('Server error:', data);
//             // Разблокируем кнопки в случае ошибки
//             pumpButton.disabled = false;
//             cashOutButton.disabled = pumps === 0;
//         }
//     } catch (err) {
//         console.error('Network error:', err);
//         // Разблокируем кнопки в случае ошибки сети
//         pumpButton.disabled = false;
//         cashOutButton.disabled = pumps === 0;
//     }
// }

// В функции handlePump:
async function handlePump() {
    if (isMouseDown || clickInProgress || fetching || trialEnded) return;
    
    clickInProgress = true;
    fetching = true;

    pumpNumber++;
    pumps++;
    
    const rt = Date.now() - reactionStartTime;
    reactionStartTime = Date.now();
    reactionTimes.push(rt);
    
    // Проверяем, не лопнул ли шарик
    popped = pumpNumber >= breakPoint;
    let trialEndedNow = false;

    if (!popped) {
        trialPoints = pumpNumber * 5;
        updateBalloonSize();
    } else {
        trialPoints = 0;
        trialEnded = true;
        trialEndedNow = true;
        pumpButton.disabled = true;
        balloon.style.backgroundColor = 'red';
    }

    // Включаем кнопку "Забрать" после первого нажатия
    if (pumps === 1) {
        cashOutButton.disabled = false;
    }

    fetching = false;
    clickInProgress = false;

    if (popped) {
        await saveDataAndEndTrial(true); // Передаем true, так как попытка завершена (взрыв)
    }
}

// В функции handleCashOut:
async function handleCashOut() {
    if (fetching || trialEnded) return;
    
    cashed = true;
    trialEnded = true;
    await saveDataAndEndTrial(true); // Передаем true, так как попытка завершена (забрали)
}

// Обновленная функция saveDataAndEndTrial:
async function saveDataAndEndTrial(trialEnded = true) {
    const sum = reactionTimes.reduce((a, b) => a + b, 0);
    const avgReactionTime = reactionTimes.length ? Math.round(sum / reactionTimes.length) : 0;
    const finalPoints = trialPoints;
    previousEarned = finalPoints;

    try {
        const response = await fetch('/save_bart', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                trialNumber: parseInt(trialNumberDisplay.textContent.split('/')[0]),
                pumpNumber: pumpNumber,
                popped: popped,
                pointsEarned: finalPoints,
                reaction_time: avgReactionTime,
                trialEnded: trialEnded  // Важно! Отправляем флаг завершения попытки
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            // Обновляем отображение очков
            if (data.total_points !== undefined) {
                totalPointsDisplay.textContent = data.total_points;
            }
            
            // Обновляем последний заработок
            lastBalloonDisplay.textContent = finalPoints.toFixed(2);
            
            if (data.redirect_url) {
                // Если это последняя попытка - перенаправляем на intermediate
                window.location.href = data.redirect_url;
            } else {
                // Иначе перезагружаем для следующей попытки
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        } else {
            console.error('Server error:', data);
            // Разблокируем кнопки в случае ошибки
            pumpButton.disabled = false;
            cashOutButton.disabled = pumps === 0;
        }
    } catch (err) {
        console.error('Network error:', err);
        // Разблокируем кнопки в случае ошибки сети
        pumpButton.disabled = false;
        cashOutButton.disabled = pumps === 0;
    }
}

// Сброс состояния игры
function resetGameState() {
    pumps = 0;
    popped = false;
    pointsEarned = 0;
    previousEarned = 0;
    pumpNumber = 0;
    trialEnded = false;
    trialPoints = 0;
    cashed = false;
    reactionTimes = [];
    reactionStartTime = Date.now();
    
    if (balloon) {
        balloon.style.backgroundColor = 'blue';
        balloon.style.width = '100px';
        balloon.style.height = '150px';
    }
    
    if (cashOutButton) cashOutButton.disabled = true;
    if (pumpButton) pumpButton.disabled = false;
}

// Основная инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    // Инициализация DOM элементов
    balloon = document.getElementById('balloon');
    pumpButton = document.getElementById('pump-button');
    cashOutButton = document.getElementById('cash-out-button');
    trialNumberDisplay = document.getElementById('trial-number');
    totalPointsDisplay = document.getElementById('total-points');
    lastBalloonDisplay = document.getElementById('last-balloon');
    
    if (!balloon || !pumpButton || !cashOutButton || !trialNumberDisplay || !totalPointsDisplay || !lastBalloonDisplay) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Получаем флаг инструкций
    showInstructionsFlag = window.showInstructionsFlag || false;
    
    // Получаем точку взрыва с сервера
    breakPoint = await getExplosionPoint();
    
    // Сброс состояния
    resetGameState();
    
    // Инициализация обработчиков мыши
    initMouseHandlers();
    
    // Добавление обработчиков кликов
    pumpButton.addEventListener('click', handlePump);
    cashOutButton.addEventListener('click', handleCashOut);
    
    // Показ инструкций при первом заходе
    if (showInstructionsFlag) {
        showInstructions();
    }
    
    // Обновление размера шарика при изменении размера окна
    window.addEventListener('resize', () => {
        if (!popped && pumps > 0) {
            updateBalloonSize();
        }
    });
});

// Делаем функции доступными глобально для HTML-обработчиков
window.closeInstructions = closeInstructions;
window.showInstructions = showInstructions;