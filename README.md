# ИП "ГРАНД МЕБЕЛЬ" — Счета на оплату v2.0

Веб-приложение для создания, хранения и экспорта счетов на оплату с поддержкой ЭСФ.

## Возможности

- Создание и редактирование счетов
- Хранение контрагентов и товаров
- Экспорт в Excel (формат для печати A4)
- Экспорт в XML (формат ЭСФ)
- Отправка в ИС ЭСФ Казахстана (тестовый режим)
- Электронная цифровая подпись (ЭЦП) — локально

## Локальный запуск

```bash
pip install -r requirements.txt
python app.py
# Откройте http://localhost:5000
```

## Развёртывание на Zeabur (бесплатно)

### 1. Создайте базу данных PostgreSQL на Neon

1. Зарегистрируйтесь на [neon.tech](https://neon.tech)
2. Создайте новый проект
3. Скопируйте строку подключения (Connection string)

### 2. Загрузите на GitHub

```bash
cd invoice_app_v2
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ВАШ_НИК/НАЗВАНИЕ.git
git push -u origin main
```

### 3. Разверните на Zeabur

1. Зарегистрируйтесь на [zeabur.com](https://zeabur.com)
2. Подключите GitHub
3. Создайте проект
4. Добавьте сервис → Deploy from GitHub → выберите репозиторий
5. В переменных окружения добавьте:
   - `DATABASE_URL` = строка подключения Neon
   - `SECRET_KEY` = любой секретный ключ

### 4. Готово!

Приложение будет доступно по адресу: `https://invoice-app.zeabur.app`

## Развёртывание на Render.com

См. раздел выше, но используйте:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
- Подключите PostgreSQL через Add-on

## Структура проекта

```
invoice_app_v2/
├── app.py              # Основной код Flask
├── requirements.txt    # Зависимости Python
├── Dockerfile         # Для Zeabur
├── templates/          # HTML шаблоны
├── esf_client/        # Клиент ЭСФ
└── instance/          # SQLite (локально)
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Ключ сессии | invoice-app-secret |
| `DATABASE_URL` | PostgreSQL URL | SQLite локально |
| `PORT` | Порт | 5000 |
| `ESF_SENDER_BIN` | БИН отправителя | 910226302322 |

## База данных

- **Локально:** SQLite в папке `instance/`
- **Zeabur:** PostgreSQL на Neon (бесплатно)

## Ограничения

- ЭЦП (GOST512) работает только локально
- На облачных платформах доступен только тестовый режим ЭСФ

## Лицензия

MIT
