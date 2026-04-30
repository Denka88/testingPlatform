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
        // На десктопе просто убираем класс closed
        if (isDesktop()) {
            sidebar.classList.remove('closed');
            mainContent.classList.remove('expanded');
            // Сохраняем состояние после открытия
            saveSidebarState();
        } else {
            // На мобильных добавляем класс open
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('active');
        }
    }

    // Закрытие меню
    function closeSidebar() {
        if (isDesktop()) {
            // На десктопе добавляем класс closed
            sidebar.classList.add('closed');
            mainContent.classList.add('expanded');
        } else {
            // На мобильных убираем класс open
            sidebar.classList.remove('open');
        }
        sidebarOverlay.classList.remove('active');
        // Сохраняем состояние после закрытия
        if (isDesktop()) {
            saveSidebarState();
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
                mainContent.classList.add('expanded');
            } else {
                sidebar.classList.remove('closed');
                mainContent.classList.remove('expanded');
            }
            // На десктопе overlay всегда скрыт
            sidebarOverlay.classList.remove('active');
        } else {
            // На мобильных всегда начинаем с закрытым меню
            sidebar.classList.remove('open');
            mainContent.classList.remove('expanded');
            sidebarOverlay.classList.remove('active');
        }
        // Убираем inline-стиль после применения состояния
        document.documentElement.style.removeProperty('--sidebar-initial-state');
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
            closeSidebar();
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

    // Выпадающее меню пользователя
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    const userMenuContainer = userMenuBtn ? userMenuBtn.closest('.user-menu') : null;

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
            if (userMenuContainer) {
                userMenuContainer.classList.toggle('open');
            }
        });

        // Закрытие при клике вне меню
        document.addEventListener('click', function() {
            userDropdown.classList.remove('show');
            if (userMenuContainer) {
                userMenuContainer.classList.remove('open');
            }
        });

        // Закрытие при клике на пункт меню
        const dropdownItems = userDropdown.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(function(item) {
            item.addEventListener('click', function() {
                userDropdown.classList.remove('show');
                if (userMenuContainer) {
                    userMenuContainer.classList.remove('open');
                }
            });
        });
    }
})();

// ==================== Глобальные уведомления ====================
function showNotification(message, type) {
    const notificationCenter = document.getElementById('notificationCenter');
    if (!notificationCenter || !message) {
        return;
    }

    const normalizedType = String(type || 'info').split(' ')[0];
    const allowedTypes = new Set(['success', 'error', 'warning', 'info']);
    const safeType = allowedTypes.has(normalizedType) ? normalizedType : 'info';

    const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };

    const notification = document.createElement('div');
    notification.className = 'notification notification-' + safeType;
    notification.innerHTML = `
        <span style="flex-shrink:0; display:flex; align-items:center;">${icons[safeType]}</span>
        <span class="notification-content"></span>
        <button type="button" class="notification-close" aria-label="Закрыть уведомление">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;
    notification.querySelector('.notification-content').textContent = message;

    function closeNotification() {
        if (notification.classList.contains('is-closing')) {
            return;
        }
        notification.classList.add('is-closing');
        setTimeout(function() {
            notification.remove();
        }, 300);
    }

    notification.querySelector('.notification-close').addEventListener('click', closeNotification);

    notificationCenter.appendChild(notification);
    setTimeout(closeNotification, 4000);
}

// ==================== Подтверждение действий ====================
let activeConfirmCleanup = null;

function showConfirmDialog(message, options) {
    const overlay = document.getElementById('globalConfirmOverlay');
    const textEl = document.getElementById('globalConfirmText');
    const titleEl = document.getElementById('globalConfirmTitle');
    const acceptBtn = document.getElementById('globalConfirmAccept');
    const cancelBtn = document.getElementById('globalConfirmCancel');

    if (!overlay || !textEl || !titleEl || !acceptBtn || !cancelBtn) {
        return Promise.resolve(window.confirm(message || '\u0412\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b?'));
    }

    if (activeConfirmCleanup) {
        activeConfirmCleanup(false);
    }

    const config = options || {};
    titleEl.textContent = config.title || '\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435';
    textEl.textContent = message || '\u0412\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b?';
    acceptBtn.textContent = config.confirmText || '\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c';
    cancelBtn.textContent = config.cancelText || '\u041e\u0442\u043c\u0435\u043d\u0430';
    overlay.hidden = false;

    return new Promise((resolve) => {
        function finish(result) {
            overlay.hidden = true;
            document.removeEventListener('keydown', handleKeydown);
            overlay.removeEventListener('click', handleOverlayClick);
            acceptBtn.removeEventListener('click', handleAccept);
            cancelBtn.removeEventListener('click', handleCancel);
            activeConfirmCleanup = null;
            resolve(result);
        }

        function handleAccept() {
            finish(true);
        }

        function handleCancel() {
            finish(false);
        }

        function handleOverlayClick(event) {
            if (event.target === overlay) {
                finish(false);
            }
        }

        function handleKeydown(event) {
            if (event.key === 'Escape') {
                finish(false);
            }
        }

        activeConfirmCleanup = finish;

        acceptBtn.addEventListener('click', handleAccept);
        cancelBtn.addEventListener('click', handleCancel);
        overlay.addEventListener('click', handleOverlayClick);
        document.addEventListener('keydown', handleKeydown);
        acceptBtn.focus();
    });
}

function confirmAction(eventOrMessage, maybeMessage, options) {
    let event = null;
    let message = maybeMessage;

    if (typeof eventOrMessage === 'string' || eventOrMessage == null) {
        message = eventOrMessage || maybeMessage;
    } else {
        event = eventOrMessage;
    }

    if (!event) {
        return false;
    }

    event.preventDefault();

    const target = event.currentTarget;
    const href = target && target.getAttribute ? target.getAttribute('href') : null;
    const form = target && target.closest ? target.closest('form') : null;
    const submitter = target && target.matches && target.matches('button, input[type="submit"]') ? target : null;

    showConfirmDialog(message || '\u0412\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b?', options).then((confirmed) => {
        if (!confirmed) {
            return;
        }

        if (href) {
            window.location.href = href;
            return;
        }

        if (form) {
            if (typeof form.requestSubmit === 'function') {
                form.requestSubmit(submitter || undefined);
            } else {
                form.submit();
            }
        }
    });

    return false;
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
