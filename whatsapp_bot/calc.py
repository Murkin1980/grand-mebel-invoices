# -*- coding: utf-8 -*-
"""
Логика расчёта стоимости мебели для WhatsApp бота
ИП ГРАНД МЕБЕЛЬ

Все базовые цены взяты из реального каталога.
"""

# ─── Базовые цены из каталога (₸) ────────────────────────────────────────────

# Кухня: цена за 1 погонный метр (выведена из Olive VDF 505 564 ₸ / ~3.5м)
KITCHEN_BASE_PER_METER = 145_000  # ₸ за п.м. (нижний + верхний ряд)

# Шкафы: базовые цены за штуку
WARDROBE_BASE = {
    "small":  94_710,   # Шкаф гардеробный 2100*900*600
    "medium": 206_500,  # Шкаф стеллаж / стандарт
    "large":  700_700,  # Шкаф 2700*1500*600
    "loft":   136_500,  # Шкаф лофт
    "archival": 289_960, # Шкаф архивный Blum
}

# Рабочие столы: базовые цены
DESK_BASE = {
    "simple":   49_320,  # Стол 1500х900
    "metal":    80_320,  # Стол металокаркас 1400х700х750
    "partition": 154_000, # Стол перегородка
    "shelf":    57_520,  # Стол полка 1500х400
}

# Тумбы: базовые цены
CABINET_BASE = {
    "2drawer": 57_130,   # Тумба с 2 ящиками на колёсах
    "3drawer": 59_460,   # Тумба с 3 ящиками на колёсах
    "desk":    68_500,   # Стол-тумба с 3 ящиками
    "speaker": 26_700,   # Тумба под колонку
    "vdf":     36_500,   # Тумба Olive VDF
}

# Прочее
WALL_PANEL_PER_SQM = 18_514   # 2 555 000 / 138 м²
BED_BASE = 122_500             # Кровать 1000х2000

# ─── Коэффициенты материалов ──────────────────────────────────────────────────

MATERIAL_COEFF = {
    "ldsp":     1.0,   # ЛДСП — базовый
    "mdf":      1.35,  # МДФ крашеный
    "vpvdf":    1.45,  # Виниловая плёнка / VDF
    "veneer":   1.8,   # Шпон натуральный
    "acrylic":  1.6,   # Акриловые фасады
}

MATERIAL_NAMES = {
    "ldsp":    "ЛДСП",
    "mdf":     "МДФ крашеный",
    "vpvdf":   "ПВХ / VDF плёнка",
    "veneer":  "Шпон натуральный",
    "acrylic": "Акриловые фасады",
}

# ─── Коэффициенты фурнитуры ───────────────────────────────────────────────────

FURNITURE_COEFF = {
    "economy": 1.0,    # Эконом (Китай)
    "middle":  1.25,   # Средний (Турция / Hettich)
    "blum":    1.55,   # Премиум (Blum Австрия)
}

FURNITURE_NAMES = {
    "economy": "Эконом",
    "middle":  "Средний (Hettich)",
    "blum":    "Премиум Blum",
}

# ─── Надбавки за услуги ───────────────────────────────────────────────────────

INSTALLATION_RATE = 0.15   # Монтаж: +15% от стоимости
DELIVERY_FIXED    = 15_000  # Доставка: фиксированная сумма ₸


# ─── Функции расчёта ─────────────────────────────────────────────────────────

def calc_kitchen(length: float, material: str = "ldsp",
                 furniture: str = "economy",
                 with_installation: bool = True,
                 with_delivery: bool = False) -> dict:
    """
    Расчёт кухонного гарнитура.

    Args:
        length: Длина кухни в погонных метрах (например, 2.5)
        material: Код материала (ldsp / mdf / vpvdf / veneer / acrylic)
        furniture: Код фурнитуры (economy / middle / blum)
        with_installation: Включить монтаж
        with_delivery: Включить доставку
    """
    mat_k  = MATERIAL_COEFF.get(material, 1.0)
    furn_k = FURNITURE_COEFF.get(furniture, 1.0)

    base   = length * KITCHEN_BASE_PER_METER
    price  = round(base * mat_k * furn_k)
    install = round(price * INSTALLATION_RATE) if with_installation else 0
    delivery = DELIVERY_FIXED if with_delivery else 0
    total  = price + install + delivery

    lines = [
        f"Корпус + фасады ({length} п.м. × {mat_k:.2f}):  {price:,.0f} ₸"
    ]
    if install:
        lines.append(f"Монтаж (+15%):                  {install:,.0f} ₸")
    if delivery:
        lines.append(f"Доставка:                       {delivery:,.0f} ₸")

    return {
        "type": "kitchen",
        "price": total,
        "breakdown": {
            "base": price,
            "installation": install,
            "delivery": delivery
        },
        "params": {
            "length": length,
            "material": MATERIAL_NAMES.get(material, material),
            "furniture": FURNITURE_NAMES.get(furniture, furniture),
        },
        "detail_lines": lines,
        "text": _format_result("Кухонный гарнитур", total, lines,
                               length, "п.м.", material, furniture)
    }


def calc_wardrobe(size: str = "medium", material: str = "ldsp",
                  furniture: str = "economy",
                  with_installation: bool = True) -> dict:
    """
    Расчёт шкафа.

    Args:
        size: small / medium / large / loft / archival
        material: код материала
        furniture: код фурнитуры
    """
    mat_k  = MATERIAL_COEFF.get(material, 1.0)
    furn_k = FURNITURE_COEFF.get(furniture, 1.0)

    base   = WARDROBE_BASE.get(size, WARDROBE_BASE["medium"])
    price  = round(base * mat_k * furn_k)
    install = round(price * INSTALLATION_RATE) if with_installation else 0
    total  = price + install

    size_names = {
        "small": "до 900 мм", "medium": "стандарт", "large": "2700+ мм",
        "loft": "лофт стиль", "archival": "архивный Blum"
    }

    lines = [
        f"Шкаф ({size_names.get(size, size)}):  {price:,.0f} ₸"
    ]
    if install:
        lines.append(f"Монтаж (+15%):  {install:,.0f} ₸")

    return {
        "type": "wardrobe",
        "price": total,
        "breakdown": {"base": price, "installation": install},
        "params": {
            "size": size_names.get(size, size),
            "material": MATERIAL_NAMES.get(material, material),
            "furniture": FURNITURE_NAMES.get(furniture, furniture),
        },
        "detail_lines": lines,
        "text": _format_result("Шкаф", total, lines,
                               size_names.get(size, size), "", material, furniture)
    }


def calc_desk(desk_type: str = "simple", material: str = "ldsp",
              with_installation: bool = False) -> dict:
    """Расчёт рабочего стола."""
    mat_k = MATERIAL_COEFF.get(material, 1.0)
    base  = DESK_BASE.get(desk_type, DESK_BASE["simple"])
    price = round(base * mat_k)
    install = round(price * INSTALLATION_RATE) if with_installation else 0
    total = price + install

    type_names = {
        "simple": "1500х900", "metal": "металлокаркас 1400х700",
        "partition": "перегородка", "shelf": "полка 1500х400"
    }
    lines = [f"Стол ({type_names.get(desk_type, desk_type)}): {price:,.0f} ₸"]
    if install:
        lines.append(f"Монтаж: {install:,.0f} ₸")

    return {
        "type": "desk",
        "price": total,
        "breakdown": {"base": price, "installation": install},
        "params": {
            "desk_type": type_names.get(desk_type, desk_type),
            "material": MATERIAL_NAMES.get(material, material),
        },
        "detail_lines": lines,
        "text": _format_result("Рабочий стол", total, lines,
                               type_names.get(desk_type, desk_type), "",
                               material, "")
    }


def calc_wall_panel(area_sqm: float) -> dict:
    """Расчёт стеновых панелей из ЛДСП."""
    price = round(area_sqm * WALL_PANEL_PER_SQM)
    install = round(price * INSTALLATION_RATE)
    total = price + install
    lines = [
        f"Панели {area_sqm} м² × {WALL_PANEL_PER_SQM:,.0f} ₸/м²:  {price:,.0f} ₸",
        f"Монтаж (+15%):  {install:,.0f} ₸"
    ]
    return {
        "type": "wall_panel",
        "price": total,
        "breakdown": {"base": price, "installation": install},
        "params": {"area": area_sqm},
        "detail_lines": lines,
        "text": _format_result("Стеновые панели ЛДСП", total, lines,
                               f"{area_sqm} м²", "", "", "")
    }


# ─── Вспомогательная функция ──────────────────────────────────────────────────

def _format_result(name, total, lines, size, unit, material, furniture) -> str:
    """Форматирует текст ответа для WhatsApp."""
    text = f"💰 *{name}*\n\n"
    for line in lines:
        text += f"  • {line.strip()}\n"
    text += f"\n*Итого: {total:,.0f} ₸*\n"
    if material:
        mat_name = MATERIAL_NAMES.get(material, material)
        text += f"  Материал: {mat_name}\n"
    if furniture:
        furn_name = FURNITURE_NAMES.get(furniture, furniture)
        text += f"  Фурнитура: {furn_name}\n"
    text += "\n_Точная стоимость — после замера._"
    return text
