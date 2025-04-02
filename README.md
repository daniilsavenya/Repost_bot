# VK2TG Repost Bot
Автоматический репостер из VK в Telegram!

[🇬🇧 Switch to English version](README-EN.md)

> 98% кода разработано при помощи нейросети [Deepseek](https://deepseek.com)

---

## 1. Возможности бота
- **Автоматический мониторинг** новых постов на стене VK
- **Поддержка всех типов вложений:**
  - 📸 Фото/альбомы
  - 📄 Документы (PDF, Word)
  - 🎵 Аудио
  - 📊 Опросы
  - 🔄 Репосты
- **Умный парсинг:**
  - 📝 Сохранение исходного форматирования текста
  - 🔍 Автоопределение автора репостов
  - 🔗 Преобразование VK-ссылок в читаемый вид
- **Защита от дублей** (проверка по времени публикации)
- **Логирование операций** в реальном времени

---

## 2. Установка

### 2.1 Обязательные требования
- 🐍 Python 3.10+
- 🛠 Установленный Git
- 👤 Аккаунт VK с открытой стеной
- 🤖 Telegram-бот с правами администратора

### 2.2 Установка через `install.py`
#### Для Linux:
```sh
curl -L https://daniilsavenya.github.io/Repost_bot/install.py | python3
```
#### Для Windows:
```sh
curl -LO https://daniilsavenya.github.io/Repost_bot/install.py
python install.py
```

### 2.3 Клонирование репозитория
```sh
git clone https://github.com/daniilsavenya/Repost_bot.git
cd Repost_bot && python install.py
```

### 2.4 Получение данных
#### Telegram Bot Token:
1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Скопируйте токен вида `123456789:ABCdefGhIjKl...`

#### VK Access Token:
1. Авторизуйтесь через специальную страницу:  
   [VK Auth](https://daniilsavenya.github.io/Repost_bot/auth.html)
2. Скопируйте **User ID** и **Access Token**

#### ID Telegram-канала:
1. Добавьте бота в канал как администратора
2. Найдите ID через [@getidsbot](https://t.me/getidsbot)  
   (начинается с `-100`)

---

## 3. Инструкция по использованию

### Базовая настройка:
```sh
python main.py          # Стандартный запуск
python main.py --debug  # Режим отладки
```

### Сценарии использования:
- **Репост из группы VK** → Укажите **ID группы** в конфиге
- **Автопостинг личных записей** → Используйте **свой User ID**
- **Архивация медиаконтента** → Бот сохраняет все вложения

### Управление:
- 🛑 **Остановка:** `Ctrl+C`
- 🔄 **После изменения `config.json`** → перезапустите бота
- 🐧 **Для Linux:** `systemctl --user restart repost-bot`

---

## 4. Благодарности
👨‍💻 **[Кирилл Белоусов](https://github.com/cyrmax):**
- Оптимизация работы с VK API
- Система логирования

🎨 **[Амир Гумеров](https://github.com/gumerov-amir):**
- Асинхронная обработка вложений
- Дизайн интерфейса

---

## 5. Контакты
📩 **Техническая поддержка:**
- Telegram: [@daniilsavenya](https://t.me/daniilsavenya)
- GitHub Issues: [Repost_bot/issues](https://github.com/daniilsavenya/Repost_bot/issues)

💬 Ответ в течение **24 часов**. Для срочных запросов укажите `[VKBOT]` в сообщении.
