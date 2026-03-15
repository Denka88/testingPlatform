// ==================== Переключение темы ====================
(function() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Получаем сохраненную тему или используем системную
    function getPreferredTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Применяем тему
    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    // Инициализация
    applyTheme(getPreferredTheme());

    // Обработчик переключения
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // Слушаем изменения системной темы
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
})();

// ==================== Боковое меню ====================
(function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const menuToggle = document.getElementById('menuToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.querySelector('.main-content');
    
    const DESKTOP_BREAKPOINT = 1024;
    
    // Проверка, десктоп ли сейчас
    function isDesktop() {
        return window.innerWidth >= DESKTOP_BREAKPOINT;
    }
    
    // Открытие меню
    function openSidebar() {
        sidebar.classList.remove('closed');
        sidebar.classList.add('open');
        sidebarOverlay.classList.add('active');
        mainContent.classList.remove('expanded');
    }
    
    // Закрытие меню
    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('active');
        if (isDesktop()) {
            sidebar.classList.add('closed');
            mainContent.classList.add('expanded');
        }
    }
    
    // Переключение меню
    function toggleSidebar() {
        if (isDesktop()) {
            // На десктопе: если меню закрыто (closed) - открываем, иначе закрываем
            if (sidebar.classList.contains('closed')) {
                openSidebar();
            } else {
                closeSidebar();
            }
        } else {
            // На мобильных: если меню открыто (open) - закрываем, иначе открываем
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        }
    }
    
    // Инициализация состояния меню
    function initSidebarState() {
        if (isDesktop()) {
            const savedState = localStorage.getItem('sidebarClosed');
            if (savedState === 'true') {
                sidebar.classList.add('closed');
                sidebar.classList.remove('open');
                mainContent.classList.add('expanded');
                sidebarOverlay.classList.remove('active');
            } else {
                sidebar.classList.remove('closed');
                sidebar.classList.add('open');
                mainContent.classList.remove('expanded');
                sidebarOverlay.classList.remove('active');
            }
        } else {
            // На мобильных всегда начинаем с закрытым меню
            sidebar.classList.remove('open', 'closed');
            mainContent.classList.remove('expanded');
            sidebarOverlay.classList.remove('active');
        }
    }
    
    // Сохранение состояния меню
    function saveSidebarState() {
        const isClosed = sidebar.classList.contains('closed');
        localStorage.setItem('sidebarClosed', isClosed ? 'true' : 'false');
    }
    
    // Обработчики событий
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', function() {
            if (isDesktop()) {
                closeSidebar();
                saveSidebarState();
            } else {
                closeSidebar();
            }
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            if (!isDesktop()) {
                closeSidebar();
            }
        });
    }
    
    // Предотвращаем всплытие клика внутри sidebar
    if (sidebar) {
        sidebar.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Обработка изменения размера окна
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            initSidebarState();
        }, 250);
    });
    
    // Инициализация
    initSidebarState();
    
    // Подсветка активного пункта меню при клике
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(function(item) {
        item.addEventListener('click', function() {
            // Удаляем active у всех пунктов
            navItems.forEach(function(nav) {
                nav.classList.remove('active');
            });
            // Добавляем active текущему
            item.classList.add('active');
        });
    });
})();

// ==================== Автозакрытие сообщений ====================
(function() {
    const messages = document.querySelectorAll('.message');

    messages.forEach(function(message) {
        // Автозакрытие через 5 секунд
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            message.style.transition = 'all 0.3s ease';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);

        // Кнопка закрытия
        const closeBtn = message.querySelector('.message-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                message.style.opacity = '0';
                message.style.transform = 'translateY(-10px)';
                message.style.transition = 'all 0.3s ease';
                setTimeout(function() {
                    message.remove();
                }, 300);
            });
        }
    });
})();

// ==================== Подтверждение действий ====================
function confirmAction(message) {
    return confirm(message || 'Вы уверены?');
}

// ==================== Утилиты ====================
// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('ru-RU', options);
}

// Форматирование времени
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Можно добавить уведомление об успешном копировании
    }).catch(function(err) {
        console.error('Ошибка копирования:', err);
    });
}
