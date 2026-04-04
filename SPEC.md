# СПЕЦИФИКАЦИЯ ПРОЕКТА
## ИП "ГРАНД МЕБЕЛЬ" — Система счетов на оплату v2.0

---

## 1. ОБЗОР

Веб-приложение для создания, хранения и экспорта счетов на оплату. Написано на Python (Flask). Работает локально или в облаке (Render). Поддерживает экспорт в Excel и XML для отправки в ИС ЭСФ КГД.

---

## 2. ТЕХНИЧЕСКИЙ СТЕК

| Компонент     | Технология                        |
|---------------|-----------------------------------|
| Язык          | Python 3.10+                      |
| Веб-фреймворк | Flask 3.0.0                       |
| ORM / БД      | Flask-SQLAlchemy 3.1.1 + SQLite   |
| БД (прод.)    | PostgreSQL (через DATABASE_URL)   |
| Шаблоны       | Jinja2 (встроен в Flask)          |
| Excel         | openpyxl 3.1.2                    |
| ESF/SOAP      | zeep 4.2.1 + lxml 5.1.0           |
| ЭЦП           | cryptography, pyOpenSSL, pycryptodome |
| Сервер (прод.)| gunicorn 21.2.0                   |
| Деплой        | Render.com                        |
| Репозиторий   | GitHub (приватный)                |

---

## 3. СТРУКТУРА ФАЙЛОВ

```
invoice_app/
├── app.py                    # Основной модуль: конфиг, модели, маршруты
├── requirements.txt          # Зависимости Python
├── Procfile                  # Команда запуска для Render
├── render.yaml               # Конфиг автодеплоя Render
├── README.md                 # Документация
├── SPEC.md                   # Эта спецификация
│
├── esf_client/
│   ├── __init__.py
│   ├── esf_client.py         # SOAP-клиент ИС ЭСФ
│   └── esf_models.py         # Модели данных ЭСФ (Participant, InvoiceItem, Invoice)
│
├── templates/                # HTML-шаблоны Jinja2
│   ├── base.html             # Базовый шаблон (навигация, стили, sidebar)
│   ├── index.html            # Список счетов + статистика
│   ├── invoice_form.html     # Переиспользуемая форма создания/редактирования счёта
│   ├── new_invoice.html      # Включает invoice_form.html (создание)
│   ├── edit_invoice.html     # Включает invoice_form.html (редактирование)
│   ├── invoice_view.html     # Просмотр одного счёта
│   ├── contractors.html      # Список + добавление контрагентов
│   ├── edit_contractor.html  # Редактирование контрагента
│   ├── products.html         # Список + добавление товаров/услуг
│   ├── edit_product.html     # Редактирование товара
│   └── esf_settings.html     # Настройки ЭЦП для ЭСФ
│
└── instance/
    └── invoice_app.db        # SQLite база данных (не в git)
```

---

## 4. МОДЕЛИ ДАННЫХ (SQLAlchemy)

### Contractor — Контрагент
```python
class Contractor(db.Model):
    id          Integer  PK autoincrement
    name        String(200)  NOT NULL
    bin_iin     String(50)   NOT NULL    # БИН или ИИН
    address     String(500)  NOT NULL
```

### Product — Товар / Услуга
```python
class Product(db.Model):
    id             Integer  PK autoincrement
    name           String(300)  NOT NULL
    unit           String(50)   default='Штука'
    default_price  Float        default=0
    is_service     Boolean      default=False
```

### Invoice — Счёт на оплату
```python
class Invoice(db.Model):
    id             Integer  PK autoincrement
    number         Integer  NOT NULL          # Порядковый номер
    date           Date     NOT NULL
    contractor_id  Integer  FK→Contractor
    contract_info  String(300)  default='Без договора'
    created_at     DateTime     default=now()

    # computed:
    total()        → sum(item.quantity * item.price)
    total_text()   → сумма прописью (тенге)
```

### InvoiceItem — Позиция счёта
```python
class InvoiceItem(db.Model):
    id          Integer  PK autoincrement
    invoice_id  Integer  FK→Invoice   NOT NULL
    product_id  Integer  FK→Product   NOT NULL
    quantity    Float    default=1
    price       Float    NOT NULL      # Цена на момент продажи
```

---

## 5. МАРШРУТЫ (API)

### Счета

| Метод | URL                         | Описание                              |
|-------|-----------------------------|---------------------------------------|
| GET   | `/`                         | Список всех счетов (поиск ?search=)  |
| GET   | `/invoice/new`              | Форма создания                        |
| POST  | `/invoice/new`              | Сохранить новый счёт                  |
| GET   | `/invoice/<id>`             | Просмотр счёта                        |
| GET   | `/invoice/edit/<id>`        | Форма редактирования                  |
| POST  | `/invoice/edit/<id>`        | Сохранить изменения                   |
| GET   | `/invoice/delete/<id>`      | Удалить счёт                          |
| GET   | `/invoice/export/<id>`      | Скачать Excel (.xlsx)                 |

### ESF / ЭСФ

| Метод | URL                         | Описание                              |
|-------|-----------------------------|---------------------------------------|
| GET   | `/esf/settings`             | Страница настроек ЭЦП                 |
| POST  | `/esf/settings`             | Сохранить настройки                   |
| GET   | `/esf/export/<id>`          | Скачать XML для ЭСФ                   |
| GET   | `/esf/send/<id>`            | Отправить ЭСФ (если есть ЭЦП)        |

### Контрагенты

| Метод | URL                         | Описание                              |
|-------|-----------------------------|---------------------------------------|
| GET   | `/contractors`              | Список (поиск ?search=)               |
| POST  | `/contractors/add`          | Добавить контрагента                  |
| GET   | `/contractors/edit/<id>`    | Форма редактирования                  |
| POST  | `/contractors/edit/<id>`    | Сохранить                             |
| GET   | `/contractors/delete/<id>`  | Удалить (нельзя если есть счета)      |

### Товары / Услуги

| Метод | URL                         | Описание                              |
|-------|-----------------------------|---------------------------------------|
| GET   | `/products`                 | Список (поиск ?search=)               |
| POST  | `/products/add`             | Добавить товар                        |
| GET   | `/products/edit/<id>`       | Форма редактирования                  |
| POST  | `/products/edit/<id>`       | Сохранить                             |
| GET   | `/products/delete/<id>`     | Удалить                               |

### JSON API

| Метод | URL                  | Ответ                                         |
|-------|----------------------|-----------------------------------------------|
| GET   | `/api/product/<id>`  | `{id, name, unit, price}` — для JS в форме   |

---

## 6. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

| Переменная         | По умолчанию                    | Описание                                  |
|--------------------|---------------------------------|-------------------------------------------|
| `SECRET_KEY`       | `invoice-app-secret-key-2026`  | Flask сессии и flash-сообщения            |
| `DATABASE_URL`     | SQLite `instance/invoice_app.db`| PostgreSQL строка подключения (Render)    |
| `ESF_CERT_PATH`    | `""`                            | Путь к файлу ЭЦП (.p12)                  |
| `ESF_CERT_PASSWORD`| `Aa123456`                      | Пароль к сертификату ЭЦП                 |
| `ESF_SENDER_BIN`   | `910226302322`                  | БИН отправителя для ИС ЭСФ               |

> **Важно:** `DATABASE_URL` начинающийся с `postgres://` автоматически конвертируется в `postgresql://` (требование SQLAlchemy 1.4+).

---

## 7. ESF КЛИЕНТ (esf_client/)

### ESFClient — реальный клиент
Отправляет ЭСФ через SOAP на серверы КГД.

**Эндпоинты ИС ЭСФ:**
```
Продуктивный:  https://esf.gov.kz:8443
Тестовый:      https://test3.esf.kgd.gov.kz:8443

SessionService:       /esf-web/ws/api1/SessionService
UploadInvoiceService: /esf-web/ws/api1/UploadInvoiceService
InvoiceService:       /esf-web/ws/api1/InvoiceService
```

**Методы:**
```python
ESFClient(cert_path, cert_password, sender_bin)
  .create_session()       → str sessionId
  .close_session()        → None
  .send_invoice(xml_str)  → {success, uuid, error?}
  .get_invoice_status(id) → {success, status, error?}
```

**Подпись:** ЭЦП НУЦ РК, алгоритм ГОСТ 2015, файл `.p12`.

### MockESFClient — тестовый клиент
Используется автоматически, если `ESF_CERT_PATH` не задан или файл не существует. Возвращает успешный ответ с фейковым UUID.

### esf_models.py — модели ЭСФ XML

```python
Participant(bin_iin, name, address, bank_account?, bank_name?, bik?)
InvoiceItem(name, unit_code, unit_name, quantity, price, tax_rate)
Invoice(invoice_number, invoice_date, seller, buyer, shipment_date, items[])
  .to_xml_string() → str  # Готовый XML по стандарту ИС ЭСФ v1
```

---

## 8. EXCEL ЭКСПОРТ

Файл формируется в памяти (`BytesIO`), не сохраняется на диск.  
Имя файла: `Счет_№{N}_от_{ДД.ММ.ГГГГ}.xlsx`

**Структура листа:**
- Строка 1: Уведомление (предупреждение об оплате)
- Строка 3: Заголовок "СЧЁТ НА ОПЛАТУ" + водяной знак
- Строки 5-7: Реквизиты поставщика (ИП ГРАНД МЕБЕЛЬ)
- Строка 9: Номер и дата счёта
- Строки 11-13: Поставщик / Покупатель / Договор
- Строка 15+: Таблица позиций (7 столбцов A-G)
- После таблицы: ИТОГО, НДС, сумма прописью
- Подписи сторон

---

## 9. УСТАНОВКА И ЗАПУСК ЛОКАЛЬНО

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Murkin1980/grand-mebel-invoices.git
cd grand-mebel-invoices

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить
python app.py

# 5. Открыть в браузере
http://localhost:5000
```

При первом запуске автоматически создаётся база данных и заполняется тестовыми данными (8 контрагентов, 24 товара/услуги).

---

## 10. ДЕПЛОЙ НА RENDER

1. Подключить GitHub репозиторий в [render.com](https://render.com)
2. New → **Web Service**
3. Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Создать **PostgreSQL** базу (New → PostgreSQL)
5. Добавить переменные окружения:
   - `DATABASE_URL` = Internal URL из PostgreSQL
   - `SECRET_KEY` = случайная строка

---

## 11. РАЗРАБОТКА В ДРУГИХ РЕДАКТОРАХ

### VS Code
Рекомендуемые расширения:
- Python (Microsoft)
- Pylance
- Jinja (wholroyd)
- SQLite Viewer

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### PyCharm
- File → Open → выбрать папку проекта
- Settings → Project → Python Interpreter → Add → Virtualenv → путь к `venv/`
- Отметить папку `templates/` как Template Folder (ПКМ → Mark Directory As → Template Folder)

### Cursor / другие редакторы
Корневой файл проекта: **`app.py`** — всё приложение в одном файле.

---

## 12. ТЕСТИРОВАНИЕ

Встроенный тест Flask (без дополнительных библиотек):

```python
import app as a
a.app.config['TESTING'] = True
with a.app.test_client() as c:
    a.init_db()
    assert c.get('/').status_code == 200
    assert c.get('/contractors').status_code == 200
    assert c.get('/products').status_code == 200
    assert c.get('/invoice/new').status_code == 200
    print("OK")
```

---

## 13. GITHUB

Репозиторий: `https://github.com/Murkin1980/grand-mebel-invoices` (приватный)

Ветка по умолчанию: `master`

`.gitignore` исключает:
- `instance/*.db` — база данных
- `Aa123456/` — папка с ЭЦП `.p12`
- `__pycache__/`, `*.pyc` — кэш Python
- `venv/` — виртуальное окружение
- Сохранённые Excel файлы (`Счет*.xlsx`)
