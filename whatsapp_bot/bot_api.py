# -*- coding: utf-8 -*-
"""
Flask Blueprint: WhatsApp Bot API endpoints
Подключается к основному app.py через: app.register_blueprint(bot_bp)

Эндпоинты:
  POST /api/calc/kitchen      — расчёт кухни
  POST /api/calc/wardrobe     — расчёт шкафа
  POST /api/calc/desk         — расчёт стола
  POST /api/calc/wall_panel   — расчёт стеновых панелей
  POST /api/bot/webhook       — webhook для n8n / WhatsApp Cloud API
  POST /api/bot/lead          — сохранение лида (имя, телефон, интерес)
  GET  /api/bot/leads         — список лидов (для вас)
"""

from flask import Blueprint, request, jsonify
from .calc import (
    calc_kitchen, calc_wardrobe, calc_desk, calc_wall_panel,
    MATERIAL_COEFF, FURNITURE_COEFF, MATERIAL_NAMES, FURNITURE_NAMES
)

bot_bp = Blueprint('bot', __name__, url_prefix='/api')


# ─── Расчёт кухни ─────────────────────────────────────────────────────────────

@bot_bp.route('/calc/kitchen', methods=['POST'])
def api_calc_kitchen():
    """
    POST /api/calc/kitchen
    Body JSON:
      {
        "length": 3.0,           // длина в п.м. (обязательно)
        "material": "ldsp",      // ldsp | mdf | vpvdf | veneer | acrylic
        "furniture": "economy",  // economy | middle | blum
        "with_installation": true,
        "with_delivery": false
      }
    """
    d = request.get_json(force=True, silent=True) or {}
    length = float(d.get('length', 0))
    if length <= 0:
        return jsonify({"error": "length должен быть > 0"}), 400

    result = calc_kitchen(
        length=length,
        material=d.get('material', 'ldsp'),
        furniture=d.get('furniture', 'economy'),
        with_installation=bool(d.get('with_installation', True)),
        with_delivery=bool(d.get('with_delivery', False)),
    )
    return jsonify(result)


# ─── Расчёт шкафа ─────────────────────────────────────────────────────────────

@bot_bp.route('/calc/wardrobe', methods=['POST'])
def api_calc_wardrobe():
    """
    POST /api/calc/wardrobe
    Body JSON:
      {
        "size": "medium",        // small | medium | large | loft | archival
        "material": "ldsp",
        "furniture": "economy",
        "with_installation": true
      }
    """
    d = request.get_json(force=True, silent=True) or {}
    result = calc_wardrobe(
        size=d.get('size', 'medium'),
        material=d.get('material', 'ldsp'),
        furniture=d.get('furniture', 'economy'),
        with_installation=bool(d.get('with_installation', True)),
    )
    return jsonify(result)


# ─── Расчёт стола ─────────────────────────────────────────────────────────────

@bot_bp.route('/calc/desk', methods=['POST'])
def api_calc_desk():
    """
    POST /api/calc/desk
    Body JSON:
      {
        "desk_type": "simple",   // simple | metal | partition | shelf
        "material": "ldsp",
        "with_installation": false
      }
    """
    d = request.get_json(force=True, silent=True) or {}
    result = calc_desk(
        desk_type=d.get('desk_type', 'simple'),
        material=d.get('material', 'ldsp'),
        with_installation=bool(d.get('with_installation', False)),
    )
    return jsonify(result)


# ─── Расчёт стеновых панелей ──────────────────────────────────────────────────

@bot_bp.route('/calc/wall_panel', methods=['POST'])
def api_calc_wall_panel():
    """
    POST /api/calc/wall_panel
    Body JSON:
      { "area": 20.5 }   // площадь в м²
    """
    d = request.get_json(force=True, silent=True) or {}
    area = float(d.get('area', 0))
    if area <= 0:
        return jsonify({"error": "area должен быть > 0"}), 400
    result = calc_wall_panel(area)
    return jsonify(result)


# ─── Справочник коэффициентов ─────────────────────────────────────────────────

@bot_bp.route('/calc/options', methods=['GET'])
def api_calc_options():
    """Возвращает доступные материалы и фурнитуру с коэффициентами."""
    return jsonify({
        "materials": [
            {"code": k, "name": v, "coeff": MATERIAL_COEFF[k]}
            for k, v in MATERIAL_NAMES.items()
        ],
        "furniture": [
            {"code": k, "name": v, "coeff": FURNITURE_COEFF[k]}
            for k, v in FURNITURE_NAMES.items()
        ]
    })


# ─── Лиды (хранение клиентов из WhatsApp) ────────────────────────────────────

# Простое хранение в памяти (для MVP).
# В production — добавить модель Lead в БД.
_leads = []


@bot_bp.route('/bot/lead', methods=['POST'])
def save_lead():
    """
    POST /api/bot/lead
    Body JSON:
      {
        "phone": "+77001234567",
        "name": "Ерлан",
        "interest": "Кухня 3м МДФ",
        "price_estimate": 756000,
        "stage": "new"   // new | measuring | offer | won | lost
      }
    """
    d = request.get_json(force=True, silent=True) or {}
    if not d.get('phone'):
        return jsonify({"error": "phone обязателен"}), 400

    from datetime import datetime
    lead = {
        "id":             len(_leads) + 1,
        "phone":          d.get('phone', ''),
        "name":           d.get('name', 'Клиент'),
        "interest":       d.get('interest', ''),
        "price_estimate": d.get('price_estimate', 0),
        "stage":          d.get('stage', 'new'),
        "created_at":     datetime.now().isoformat(),
    }
    _leads.append(lead)
    return jsonify({"ok": True, "lead_id": lead["id"]})


@bot_bp.route('/bot/leads', methods=['GET'])
def get_leads():
    """GET /api/bot/leads — список всех лидов из WhatsApp."""
    return jsonify(_leads)


# ─── WhatsApp Webhook (от n8n или напрямую) ───────────────────────────────────

@bot_bp.route('/bot/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    POST /api/bot/webhook
    n8n отправляет сюда данные от WhatsApp Cloud API.
    Приложение возвращает текст ответа.

    Body JSON (пример от n8n):
      {
        "from": "+77001234567",
        "message": "Кухня 3 метра МДФ Blum",
        "session": { ... }   // состояние диалога
      }
    """
    d = request.get_json(force=True, silent=True) or {}
    phone   = d.get('from', '')
    message = d.get('message', '').strip().lower()
    session = d.get('session', {})

    # Минимальный роутер сообщений
    reply = _route_message(message, session, phone)

    return jsonify({
        "reply": reply['text'],
        "session": reply.get('session', session),
        "action":  reply.get('action', None),   # create_invoice | save_lead | None
        "data":    reply.get('data', {}),
    })


def _route_message(message: str, session: dict, phone: str) -> dict:
    """Простой конечный автомат диалога."""
    stage = session.get('stage', 'start')

    # ─ Приветствие / Главное меню ─
    if stage == 'start' or message in ('привет', 'здравствуйте', 'hi', 'hello', 'start', '0', 'меню'):
        return {
            'text': (
                "Здравствуйте! 👋 Я помогу рассчитать стоимость мебели за 1 минуту.\n\n"
                "Что вас интересует?\n"
                "1️⃣ Кухня\n"
                "2️⃣ Шкаф\n"
                "3️⃣ Рабочий стол\n"
                "4️⃣ Стеновые панели\n"
                "5️⃣ Другое / Свой вопрос\n\n"
                "_Напишите номер или название_"
            ),
            'session': {'stage': 'choose_type'}
        }

    # ─ Выбор типа ─
    if stage == 'choose_type' or message in ('1', '2', '3', '4', '5', 'кухня', 'шкаф', 'стол', 'панели'):
        if message in ('1', 'кухня'):
            return {
                'text': "🍳 Кухня — отлично!\n\nВведите длину кухни в метрах:\n_Пример: 2.5 или 3_",
                'session': {'stage': 'kitchen_length', 'type': 'kitchen'}
            }
        elif message in ('2', 'шкаф'):
            return {
                'text': (
                    "🚪 Шкаф!\n\nВыберите размер:\n"
                    "1️⃣ Маленький (до 900 мм)\n"
                    "2️⃣ Стандарт\n"
                    "3️⃣ Большой (2700+ мм)\n"
                    "4️⃣ Лофт стиль\n"
                    "5️⃣ Архивный Blum"
                ),
                'session': {'stage': 'wardrobe_size', 'type': 'wardrobe'}
            }
        elif message in ('3', 'стол'):
            return {
                'text': (
                    "🖥 Стол!\n\nВыберите тип:\n"
                    "1️⃣ Стандартный 1500×900\n"
                    "2️⃣ На металлокаркасе\n"
                    "3️⃣ Стол-перегородка\n"
                    "4️⃣ Полка 1500×400"
                ),
                'session': {'stage': 'desk_type', 'type': 'desk'}
            }
        elif message in ('4', 'панели', 'стеновые'):
            return {
                'text': "🧱 Стеновые панели из ЛДСП!\n\nВведите площадь в м²:\n_Пример: 20 или 35.5_",
                'session': {'stage': 'panel_area', 'type': 'wall_panel'}
            }
        else:
            return {
                'text': "Напишите нам напрямую, и мы свяжемся с вами в ближайшее время 📞\n\nИли выберите: 1, 2, 3, 4",
                'session': {'stage': 'choose_type'},
                'action': 'notify_manager',
                'data': {'phone': phone, 'message': message}
            }

    # ─ Кухня: длина ─
    if stage == 'kitchen_length':
        try:
            length = float(message.replace(',', '.').replace('м', '').strip())
            if length < 0.5 or length > 15:
                raise ValueError()
            return {
                'text': (
                    "📐 Длина принята!\n\nВыберите материал фасадов:\n"
                    "1️⃣ ЛДСП (базовый)\n"
                    "2️⃣ МДФ крашеный\n"
                    "3️⃣ ПВХ / VDF плёнка\n"
                    "4️⃣ Шпон натуральный\n"
                    "5️⃣ Акриловые фасады"
                ),
                'session': {'stage': 'kitchen_material', 'type': 'kitchen', 'length': length}
            }
        except ValueError:
            return {
                'text': "Введите длину числом, например: *3* или *2.5*",
                'session': session
            }

    # ─ Кухня: материал ─
    if stage == 'kitchen_material':
        mat_map = {'1': 'ldsp', '2': 'mdf', '3': 'vpvdf', '4': 'veneer', '5': 'acrylic',
                   'лдсп': 'ldsp', 'мдф': 'mdf', 'шпон': 'veneer', 'акрил': 'acrylic'}
        material = mat_map.get(message, 'ldsp')
        return {
            'text': (
                "✨ Выберите фурнитуру:\n"
                "1️⃣ Эконом\n"
                "2️⃣ Средний (Hettich)\n"
                "3️⃣ Премиум Blum 🏆"
            ),
            'session': {**session, 'stage': 'kitchen_furniture', 'material': material}
        }

    # ─ Кухня: фурнитура → расчёт ─
    if stage == 'kitchen_furniture':
        furn_map = {'1': 'economy', '2': 'middle', '3': 'blum',
                    'эконом': 'economy', 'средний': 'middle', 'blum': 'blum', 'блюм': 'blum'}
        furniture = furn_map.get(message, 'economy')
        result = calc_kitchen(
            length=session.get('length', 2.5),
            material=session.get('material', 'ldsp'),
            furniture=furniture,
            with_installation=True,
        )
        return {
            'text': (
                f"{result['text']}\n\n"
                "Что дальше?\n"
                "1️⃣ Запросить точный расчёт\n"
                "2️⃣ Вызвать замерщика\n"
                "3️⃣ Получить счёт на оплату\n"
                "0️⃣ Главное меню"
            ),
            'session': {'stage': 'after_calc', 'type': 'kitchen', 'price': result['price']},
            'action': 'show_price',
            'data': result
        }

    # ─ Шкаф: размер → расчёт ─
    if stage == 'wardrobe_size':
        size_map = {'1': 'small', '2': 'medium', '3': 'large', '4': 'loft', '5': 'archival',
                    'маленький': 'small', 'стандарт': 'medium', 'большой': 'large'}
        size = size_map.get(message, 'medium')
        result = calc_wardrobe(size=size, material='ldsp', furniture='economy')
        return {
            'text': (
                f"{result['text']}\n\n"
                "Что дальше?\n"
                "1️⃣ Точный расчёт\n"
                "2️⃣ Вызвать замерщика\n"
                "3️⃣ Счёт на оплату\n"
                "0️⃣ Главное меню"
            ),
            'session': {'stage': 'after_calc', 'type': 'wardrobe', 'price': result['price']},
            'action': 'show_price',
            'data': result
        }

    # ─ Стол: тип → расчёт ─
    if stage == 'desk_type':
        type_map = {'1': 'simple', '2': 'metal', '3': 'partition', '4': 'shelf'}
        desk_type = type_map.get(message, 'simple')
        result = calc_desk(desk_type=desk_type, material='ldsp')
        return {
            'text': (
                f"{result['text']}\n\n"
                "Что дальше?\n"
                "1️⃣ Точный расчёт\n"
                "2️⃣ Связаться с нами\n"
                "0️⃣ Главное меню"
            ),
            'session': {'stage': 'after_calc', 'type': 'desk', 'price': result['price']},
            'action': 'show_price',
            'data': result
        }

    # ─ Панели: площадь → расчёт ─
    if stage == 'panel_area':
        try:
            area = float(message.replace(',', '.').replace('м²', '').replace('м', '').strip())
            result = calc_wall_panel(area)
            return {
                'text': (
                    f"{result['text']}\n\n"
                    "1️⃣ Точный расчёт\n"
                    "2️⃣ Связаться\n"
                    "0️⃣ Главное меню"
                ),
                'session': {'stage': 'after_calc', 'price': result['price']},
                'action': 'show_price',
                'data': result
            }
        except ValueError:
            return {
                'text': "Введите площадь числом, например: *20* или *35.5*",
                'session': session
            }

    # ─ После расчёта ─
    if stage == 'after_calc':
        if message in ('1', 'расчёт', 'точный'):
            return {
                'text': (
                    "📋 Отлично! Для точного расчёта нам нужен замер.\n\n"
                    "Пожалуйста, напишите ваше *имя* 👇"
                ),
                'session': {**session, 'stage': 'get_name'}
            }
        elif message in ('2', 'замерщик', 'замер'):
            return {
                'text': "👷 Вызов замерщика!\n\nВведите ваш *номер телефона* для связи:",
                'session': {**session, 'stage': 'get_phone_for_measure'}
            }
        elif message in ('3', 'счёт', 'счет'):
            return {
                'text': "🧾 Для выставления счёта введите ваше *имя*:",
                'session': {**session, 'stage': 'get_name_for_invoice'}
            }
        elif message in ('0', 'меню', 'главное'):
            return _route_message('привет', {}, phone)

    # ─ Сбор имени ─
    if stage in ('get_name', 'get_name_for_invoice'):
        return {
            'text': f"Приятно познакомиться, *{message.title()}*! 🤝\n\nВведите ваш *телефон*:",
            'session': {**session, 'stage': 'get_phone', 'client_name': message.title()}
        }

    # ─ Сбор телефона → финал ─
    if stage in ('get_phone', 'get_phone_for_measure'):
        name = session.get('client_name', 'Клиент')
        price = session.get('price', 0)
        return {
            'text': (
                f"✅ Спасибо, *{name}*!\n\n"
                f"Ваша предварительная стоимость: *{price:,.0f} ₸*\n\n"
                "Наш менеджер свяжется с вами в течение 30 минут для уточнения деталей. 📞\n\n"
                "ИП ГРАНД МЕБЕЛЬ\n"
                "🏭 Аулиеагаш, Алматинская обл."
            ),
            'session': {'stage': 'done'},
            'action': 'save_lead',
            'data': {
                'phone': message,
                'name':  name,
                'interest': session.get('type', ''),
                'price_estimate': price
            }
        }

    # ─ Fallback ─
    return {
        'text': (
            "Я не совсем понял 🤔\n\n"
            "Напишите *0* для главного меню\n"
            "или позвоните нам напрямую."
        ),
        'session': session
    }
