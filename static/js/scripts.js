document.addEventListener('DOMContentLoaded', () => {
            const burger = document.getElementById('burger');
            const navLinks = document.getElementById('nav-links');

            if (burger && navLinks) {
                burger.addEventListener('click', () => {
                    console.log('you clicked');
                    navLinks.classList.toggle('show');
                });

                // Автозакрытие меню при клике на ссылку (по желанию)
                navLinks.querySelectorAll('a').forEach(link => {
                    link.addEventListener('click', () => {
                        navLinks.classList.remove('show');
                    });
                });
            }
        });