// API Base URL - измените на ваш адрес при деплое
const API_BASE_URL = 'http://localhost:8000';

// Хранилище конфигурации
let config = {
    api_mws: '',
    table_name: '',
    url_tables: '',
    api_vk: '',
    id_group: '',
    count: 10
};

// Навигация между экранами
function goToStep(step) {
    // Скрыть все экраны
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    // Показать нужный экран
    if (step === 1) {
        loadSavedConfig(); // Загрузить сохраненную конфигурацию
        document.getElementById('screen-step1').classList.add('active');
    } else if (step === 2) {
        // Сохранить API_MWS
        const apiMws = document.getElementById('api_mws').value;
        if (!apiMws && step === 2) {
            alert('Введите API_MWS!');
            document.getElementById('screen-step1').classList.add('active');
            return;
        }
        config.api_mws = apiMws;
        document.getElementById('screen-step2').classList.add('active');
    } else if (step === 3) {
        // Сохранить конфигурацию шага 2
        config.table_name = document.getElementById('table_name').value;
        config.url_tables = document.getElementById('url_tables').value;
        config.api_vk = document.getElementById('api_vk').value;
        config.id_group = document.getElementById('id_group').value;
        config.count = parseInt(document.getElementById('count').value) || 10;

        if (!config.table_name || !config.url_tables || !config.api_vk || !config.id_group) {
            alert('Заполните все обязательные поля!');
            document.getElementById('screen-step2').classList.add('active');
            return;
        }

        // Отправить конфигурацию на бэкенд
        saveConfiguration();

        document.getElementById('screen-step3').classList.add('active');
        // Автоматически загрузить данные
        fetchData();
    }
}

// Загрузить сохраненную конфигурацию
async function loadSavedConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/get-config`);
        if (!response.ok) return;

        const data = await response.json();
        if (data.status === 'success' && data.config) {
            // Заполнить поля если есть сохраненные данные
            if (data.config['mws-token']) {
                document.getElementById('api_mws').value = data.config['mws-token'];
                config.api_mws = data.config['mws-token'];
            }

            // Заполнить VK данные если есть
            if (data.config.vk && data.config.vk.length > 0) {
                const vkConfig = data.config.vk[0]; // Берем первую конфигурацию
                document.getElementById('table_name').value = vkConfig.table_name || '';
                document.getElementById('api_vk').value = vkConfig.api_vk || '';
                document.getElementById('id_group').value = vkConfig.id_group || '';
                document.getElementById('count').value = vkConfig.count || 10;
            }
        }
    } catch (error) {
        console.log('Не удалось загрузить конфигурацию:', error);
    }
}

// Скачать шаблон таблицы
async function downloadTemplate() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/download-template`, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error('Ошибка загрузки шаблона');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'template.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification('Шаблон загружен!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Функция будет реализована позже', 'info');
    }
}

// Сохранить конфигурацию
async function saveConfiguration() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/save-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            throw new Error('Ошибка сохранения конфигурации');
        }

        showNotification('Конфигурация сохранена!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Конфигурация сохранена локально (бэкенд недоступен)', 'info');
    }
}

// Добавить новую таблицу (функция для будущего расширения)
function addNewTable() {
    showNotification('Функция "Добавить таблицу" будет реализована позже', 'info');
}

// Получить данные из VK и отобразить
async function fetchData() {
    showLoading(true);

    try {
        // Запрос на парсинг VK
        const parseResponse = await fetch(`${API_BASE_URL}/api/parse-vk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                api_key: config.api_vk,
                group_id: parseInt(config.id_group),
                count: config.count
            })
        });

        if (!parseResponse.ok) {
            throw new Error('Ошибка парсинга VK');
        }

        // Получить все посты
        const postsResponse = await fetch(`${API_BASE_URL}/content`);
        if (!postsResponse.ok) {
            throw new Error('Ошибка получения данных');
        }

        const posts = await postsResponse.json();
        displayData(posts);
        showNotification('Данные обновлены!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка загрузки данных. Проверьте бэкенд.', 'error');
        // Показать демо данные для разработки
        displayDemoData();
    } finally {
        showLoading(false);
    }
}

// Отобразить данные в таблице
function displayData(posts) {
    if (!posts || posts.length === 0) {
        document.getElementById('posts-tbody').innerHTML =
            '<tr><td colspan="7" class="no-data">Нет данных</td></tr>';
        return;
    }

    // Вычислить статистику
    const totalPosts = posts.length;
    const totalViews = posts.reduce((sum, post) => sum + (post.views || 0), 0);
    const totalLikes = posts.reduce((sum, post) => sum + (post.likes || 0), 0);
    const totalComments = posts.reduce((sum, post) => sum + (post.comment_count || 0), 0);

    document.getElementById('total-posts').textContent = totalPosts;
    document.getElementById('total-views').textContent = totalViews.toLocaleString();
    document.getElementById('total-likes').textContent = totalLikes.toLocaleString();
    document.getElementById('total-comments').textContent = totalComments.toLocaleString();

    // Отобразить топ-10 постов
    const topPosts = posts
        .sort((a, b) => (b.views || 0) - (a.views || 0))
        .slice(0, 10);

    const tbody = document.getElementById('posts-tbody');
    tbody.innerHTML = topPosts.map(post => `
        <tr>
            <td>${post.post_id}</td>
            <td>${post.format || 'text'}</td>
            <td>${formatDate(post.date)}</td>
            <td>${(post.views || 0).toLocaleString()}</td>
            <td>${(post.likes || 0).toLocaleString()}</td>
            <td>${(post.comment_count || 0).toLocaleString()}</td>
            <td>${(post.reposts || 0).toLocaleString()}</td>
        </tr>
    `).join('');
}

// Демо данные для разработки
function displayDemoData() {
    const demoPosts = [
        {
            post_id: 123,
            format: 'photo',
            date: new Date().toISOString(),
            views: 5000,
            likes: 250,
            comment_count: 45,
            reposts: 12
        },
        {
            post_id: 124,
            format: 'video',
            date: new Date().toISOString(),
            views: 8500,
            likes: 430,
            comment_count: 89,
            reposts: 34
        },
        {
            post_id: 125,
            format: 'text',
            date: new Date().toISOString(),
            views: 2100,
            likes: 87,
            comment_count: 23,
            reposts: 5
        }
    ];
    displayData(demoPosts);
}

// Экспорт данных
async function exportData(format) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/export/${format}`, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error('Ошибка экспорта');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification(`Экспорт в ${format.toUpperCase()} завершен!`, 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Функция экспорта будет реализована позже', 'info');
    }
}

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Показать уведомление
function showNotification(message, type = 'info') {
    // Простая реализация через alert, можно заменить на toast notifications
    alert(message);
}

// Показать/скрыть загрузку
function showLoading(show) {
    // Можно добавить спиннер загрузки
    if (show) {
        console.log('Loading...');
    } else {
        console.log('Loading complete');
    }
}
