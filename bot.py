import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import datetime
import xml.etree.ElementTree as ET
import yadisk
import io

# ================= НАСТРОЙКИ =================
TOKEN = "vk1.a.cxQlfisAwdBvPfNmGh09jnediBSne4XgJPGR_mA3nN22S9VAi6KVb7POzCEfpuFGVpWLPCGtD597JXplVsxSVZxvwiUx3w3y39ZUANVGaEhB8yZFX_gr7rr_HrNNsSZsS-8JSbYTd-3ANRpYmAQuPz-iKN8z9meWCPmE7T7Cr_g6ivduoZ54KBnT5Oz8t8WZYy1sFyNJW2pkKmqHraseSw"
YADISK_TOKEN = "y0__xDB5ISCAhjblgMg7bvogxcwrP2v8gdD_maYFxg9V3Opg1DgOWyvgan1Kw"  # Получить на https://yandex.ru/dev/disk/poligon/

# Инициализация Яндекс.Диска
yd = yadisk.YaDisk(token=YADISK_TOKEN)

# Проверка подключения
try:
    if yd.check_token():
        print("✅ Яндекс.Диск подключен успешно!")
    else:
        print("❌ Ошибка токена Яндекс.Диска")
except:
    print("❌ Не удалось подключиться к Яндекс.Диску")

# ================= ФОТОГРАФИИ =================
PHOTO_TROTUAR_1 = "photo-212080985_457239100"
PHOTO_TROTUAR_2 = "photo-212080985_457239102"


PHOTO_PARKOVKA_1 = "photo-212080985_457239101"
PHOTO_PARKOVKA_2 = "photo-212080985_457239103"

PHOTO_BORDUR_TROTUAR   = "photo-212080985_457239097"
PHOTO_BORDUR_DOROZH = "photo-212080985_457239096"

# ================= ЦЕНЫ =================
PRICES = {
    'trotuar': {
        1: {'price': 5600, 'name': 'Стандартный'},
        2: {'price': 5900, 'name': 'Улучшенный'},
    },
    'parkovka': {
        1: {'price': 6400, 'name': 'Стандартный'},
        2: {'price': 7000, 'name': 'Усиленный'}
    },
    'bordur': {
        1: {'price': 1200, 'name': 'Тротуарный'},   # ← обновлено
        2: {'price': 2000, 'name': 'Дорожный'}       # ← обновлено
    }
}

# =============================================
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

users_state = {}


def get_user_name(user_id):
    """Получает имя пользователя из ВК"""
    try:
        user_info = vk.users.get(user_ids=user_id)[0]
        return user_info.get('first_name', '')
    except:
        return ''


def send_message(user_id, text, keyboard=None, attachment=None):
    params = {
        "user_id": user_id,
        "random_id": get_random_id(),
        "message": text
    }
    if keyboard is not None:
        if hasattr(keyboard, 'get_keyboard'):
            params["keyboard"] = keyboard.get_keyboard()
        else:
            params["keyboard"] = keyboard
    if attachment:
        params["attachment"] = attachment
    vk.messages.send(**params)


def save_to_yadisk(data):
    """Сохраняет XML на Яндекс.Диск"""
    try:
        folder_path = "/Заказы_XML"
        if not yd.exists(folder_path):
            yd.mkdir(folder_path)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        client_name  = data.get('name', 'Клиент').replace(' ', '_')
        filename     = f"Расчет_{client_name}_{current_time}.xml"

        root = ET.Element("Order")
        root.set("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Клиент
        client_el = ET.SubElement(root, "Client")
        ET.SubElement(client_el, "Name").text  = str(data.get('name', ''))
        ET.SubElement(client_el, "Phone").text = str(data.get('phone', ''))

        # Услуга
        service_el = ET.SubElement(root, "Service")
        ET.SubElement(service_el, "Type").text        = str(data.get('service', ''))
        ET.SubElement(service_el, "Variant").text     = str(data.get('variant', ''))
        ET.SubElement(service_el, "VariantName").text = str(data.get('variant_name', ''))
        ET.SubElement(service_el, "Area").text        = str(data.get('area', 0))
        ET.SubElement(service_el, "PricePerSqm").text = str(data.get('price_per_sqm', 0))
        ET.SubElement(service_el, "AreaCost").text    = str(data.get('cost_area', 0))

        # Бордюр тротуарный
        curb1_el = ET.SubElement(root, "CurbTrotuar")
        ET.SubElement(curb1_el, "Name").text         = PRICES['bordur'][1]['name']
        ET.SubElement(curb1_el, "Length").text        = str(data.get('curb1_length', 0))
        ET.SubElement(curb1_el, "PricePerMeter").text = str(PRICES['bordur'][1]['price'])
        ET.SubElement(curb1_el, "Cost").text          = str(data.get('cost_curb1', 0))

        # Бордюр дорожный
        curb2_el = ET.SubElement(root, "CurbDorozh")
        ET.SubElement(curb2_el, "Name").text         = PRICES['bordur'][2]['name']
        ET.SubElement(curb2_el, "Length").text        = str(data.get('curb2_length', 0))
        ET.SubElement(curb2_el, "PricePerMeter").text = str(PRICES['bordur'][2]['price'])
        ET.SubElement(curb2_el, "Cost").text          = str(data.get('cost_curb2', 0))

        # Итого
        ET.SubElement(root, "TotalPrice").text = str(data.get('total_price', 0))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        xml_bytes = io.BytesIO()
        tree.write(xml_bytes, encoding="utf-8", xml_declaration=True)
        xml_bytes.seek(0)

        yd.upload(xml_bytes, f"{folder_path}/{filename}")
        print(f"✅ Файл {filename} загружен на Яндекс.Диск")
        return filename

    except Exception as e:
        print(f"❌ Ошибка загрузки на Яндекс.Диск: {e}")
        return None


def build_confirm_message(user_data):
    """Формирует итоговое сообщение с расчётом"""
    return (
        f"📋 ПРОВЕРЬТЕ ДАННЫЕ:\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: {user_data['name']}\n"
        f"📱 Телефон: {user_data['phone']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠 Услуга: {user_data['service']}\n"
        f"   └ {user_data['variant_name']} (Вариант {user_data['variant']})\n"
        f"📐 Площадь: {user_data['area']} м² × {user_data['price_per_sqm']} руб = "
        f"{int(user_data['cost_area'])} руб\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧱 Бордюр тротуарный: {user_data['curb1_length']} м × "
        f"{PRICES['bordur'][1]['price']} руб = {int(user_data['cost_curb1'])} руб\n"
        f"🧱 Бордюр дорожный:   {user_data['curb2_length']} м × "
        f"{PRICES['bordur'][2]['price']} руб = {int(user_data['cost_curb2'])} руб\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 ИТОГО: {int(user_data['total_price'])} руб.\n\n"
        f"Всё верно?"
    )


print("🤖 Бот успешно запущен и готов к работе!")

# ===== ОСНОВНОЙ ЦИКЛ БОТА =====
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id    = event.user_id
        text       = event.text.strip()
        text_lower = text.lower()

        # ===== НАЧАЛО ДИАЛОГА =====
        if user_id not in users_state or text_lower in ['начать', 'start', 'привет', 'назад', 'заново']:
            users_state[user_id] = {'step': 'ask_name'}
            vk_name = get_user_name(user_id)

            if vk_name:
                users_state[user_id]['vk_name'] = vk_name
                kb = VkKeyboard(one_time=True)
                kb.add_button(f'Да, я {vk_name}', color=VkKeyboardColor.POSITIVE)
                kb.add_line()
                kb.add_button('Ввести другое имя', color=VkKeyboardColor.SECONDARY)
                send_message(
                    user_id,
                    f"Здравствуйте! Давайте рассчитаем стоимость.\n\nВас зовут {vk_name}?",
                    keyboard=kb
                )
            else:
                send_message(
                    user_id,
                    "Здравствуйте! Давайте рассчитаем стоимость.\nПожалуйста, введите ваше имя:",
                    keyboard=VkKeyboard.get_empty_keyboard()
                )
            continue

        user_data = users_state[user_id]
        step = user_data['step']

        # ===== ШАГ 1: ИМЯ =====
        if step == 'ask_name':
            if 'да' in text_lower and user_data.get('vk_name'):
                user_data['name'] = user_data['vk_name']
                user_data['step'] = 'ask_phone'
                send_message(user_id, f"Отлично, {user_data['name']}!\nТеперь введите ваш номер телефона:")
            elif text_lower == 'ввести другое имя':
                user_data['step'] = 'enter_custom_name'
                send_message(user_id, "Введите ваше имя:", keyboard=VkKeyboard.get_empty_keyboard())
            else:
                user_data['name'] = text
                user_data['step'] = 'ask_phone'
                send_message(user_id, f"Приятно познакомиться, {text}!\nТеперь введите ваш номер телефона:")

        elif step == 'enter_custom_name':
            user_data['name'] = text
            user_data['step'] = 'ask_phone'
            send_message(user_id, f"Приятно познакомиться, {text}!\nТеперь введите ваш номер телефона:")

        # ===== ШАГ 2: ТЕЛЕФОН =====
        elif step == 'ask_phone':
            user_data['phone'] = text
            user_data['step']  = 'ask_service'

            kb = VkKeyboard(one_time=True)
            kb.add_button('🚶 Тротуарные дорожки', color=VkKeyboardColor.PRIMARY)
            kb.add_line()
            kb.add_button('🚗 Парковка', color=VkKeyboardColor.PRIMARY)
            send_message(user_id, "Отлично! Какую услугу будем рассчитывать?", keyboard=kb)

        # ===== ШАГ 3: ВЫБОР УСЛУГИ =====
        elif step == 'ask_service':
            if 'тротуар' in text_lower or 'дорожк' in text_lower:
                user_data['service']     = 'Тротуарные дорожки'
                user_data['service_key'] = 'trotuar'
                user_data['step']        = 'ask_variant'

                # ── Только 2 варианта ──
                kb = VkKeyboard(one_time=True)
                kb.add_button('Вариант 1', color=VkKeyboardColor.SECONDARY)
                kb.add_button('Вариант 2', color=VkKeyboardColor.SECONDARY)

                msg = (
                    "🚶 Вы выбрали: Тротуарные дорожки\n\n"
                    f"📌 Вариант 1 — Стандартный: {PRICES['trotuar'][1]['price']} руб/м²\n"
                    f"📌 Вариант 2 — Улучшенный:  {PRICES['trotuar'][2]['price']} руб/м²\n\n"
                    "Выберите вариант:"
                )
                # Каждый вариант — своя картинка
                send_message(user_id, msg, keyboard=kb,
                             attachment=f"{PHOTO_TROTUAR_1},{PHOTO_TROTUAR_2}")

            elif 'парков' in text_lower:
                user_data['service']     = 'Парковка'
                user_data['service_key'] = 'parkovka'
                user_data['step']        = 'ask_variant'

                # ── 2 варианта ──
                kb = VkKeyboard(one_time=True)
                kb.add_button('Вариант 1', color=VkKeyboardColor.SECONDARY)
                kb.add_button('Вариант 2', color=VkKeyboardColor.SECONDARY)

                msg = (
                    "🚗 Вы выбрали: Парковка\n\n"
                    f"📌 Вариант 1 — Стандартный: {PRICES['parkovka'][1]['price']} руб/м²\n"
                    f"📌 Вариант 2 — Усиленный:   {PRICES['parkovka'][2]['price']} руб/м²\n\n"
                    "Выберите вариант:"
                )
                send_message(user_id, msg, keyboard=kb,
                             attachment=f"{PHOTO_PARKOVKA_1},{PHOTO_PARKOVKA_2}")
            else:
                send_message(user_id, "Пожалуйста, выберите услугу с помощью кнопок.")

        # ===== ШАГ 3.x: ВЫБОР ВАРИАНТА =====
        elif step == 'ask_variant':
            variant = None
            if '1' in text:
                variant = 1
            elif '2' in text:
                variant = 2

            if variant is None:
                send_message(user_id, "Пожалуйста, выберите вариант с помощью кнопок.")
                continue

            service_key = user_data['service_key']
            user_data['variant']       = variant
            user_data['variant_name']  = PRICES[service_key][variant]['name']
            user_data['price_per_sqm'] = PRICES[service_key][variant]['price']
            user_data['step']          = 'ask_area'

            send_message(
                user_id,
                f"✅ Выбран: {user_data['variant_name']} "
                f"({user_data['price_per_sqm']} руб/м²)\n\n"
                f"Введите площадь в квадратных метрах (только число):",
                keyboard=VkKeyboard.get_empty_keyboard()
            )

        # ===== ШАГ 4: ПЛОЩАДЬ =====
        elif step == 'ask_area':
            try:
                area = float(text.replace(',', '.'))
                user_data['area']      = area
                user_data['cost_area'] = area * user_data['price_per_sqm']
                user_data['step']      = 'ask_curb1_length'

                send_message(
                    user_id,
                    f"✅ Площадь принята: {area} м²\n\n"
                    f"🧱 Шаг 1 из 2 — Тротуарный бордюр\n"
                    f"Цена: {PRICES['bordur'][1]['price']} руб/м\n\n"
                    f"Введите длину тротуарного бордюра в метрах\n"
                    f"(если не нужен — введите 0):",
                    keyboard=VkKeyboard.get_empty_keyboard(),
                    attachment=PHOTO_BORDUR_TROTUAR
                )
            except ValueError:
                send_message(user_id, "Ошибка! Введите число (например: 25 или 30.5)")

        # ===== ШАГ 5а: ДЛИНА ТРОТУАРНОГО БОРДЮРА =====
        elif step == 'ask_curb1_length':
            try:
                curb1 = float(text.replace(',', '.'))
                user_data['curb1_length'] = curb1
                user_data['cost_curb1']   = curb1 * PRICES['bordur'][1]['price']
                user_data['step']         = 'ask_curb2_length'

                send_message(
                    user_id,
                    f"✅ Тротуарный бордюр: {curb1} м = "
                    f"{int(user_data['cost_curb1'])} руб\n\n"
                    f"🧱 Шаг 2 из 2 — Дорожный бордюр\n"
                    f"Цена: {PRICES['bordur'][2]['price']} руб/м\n\n"
                    f"Введите длину дорожного бордюра в метрах\n"
                    f"(если не нужен — введите 0):",
                    keyboard=VkKeyboard.get_empty_keyboard(),
                    attachment=PHOTO_BORDUR_DOROZH
                )
            except ValueError:
                send_message(user_id, "Ошибка! Введите число (например: 10 или 15.5)")

        # ===== ШАГ 5б: ДЛИНА ДОРОЖНОГО БОРДЮРА → ИТОГ =====
        elif step == 'ask_curb2_length':
            try:
                curb2 = float(text.replace(',', '.'))
                user_data['curb2_length'] = curb2
                user_data['cost_curb2']   = curb2 * PRICES['bordur'][2]['price']
                user_data['total_price']  = (
                    user_data['cost_area'] +
                    user_data['cost_curb1'] +
                    user_data['cost_curb2']
                )
                user_data['step'] = 'confirm'

                kb = VkKeyboard(one_time=True)
                kb.add_button('✅ Закончить ввод', color=VkKeyboardColor.POSITIVE)
                kb.add_line()
                kb.add_button('🔄 Повторить ввод', color=VkKeyboardColor.NEGATIVE)

                send_message(user_id, build_confirm_message(user_data), keyboard=kb)

            except ValueError:
                send_message(user_id, "Ошибка! Введите число (например: 10 или 15.5)")

        # ===== ШАГ 6: ПОДТВЕРЖДЕНИЕ =====
        elif step == 'confirm':
            if 'закончить' in text_lower or '✅' in text:
                filename = save_to_yadisk(user_data)

                result_msg = (
                    f"🎉 ВАША ЗАЯВКА ОФОРМЛЕНА!\n\n"
                    f"📊 ИТОГОВЫЙ РАСЧЁТ:\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 Клиент: {user_data['name']}\n"
                    f"📱 Телефон: {user_data['phone']}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛠 {user_data['service']} — {user_data['variant_name']}\n"
                    f"📐 Площадь: {user_data['area']} м² × "
                    f"{user_data['price_per_sqm']} руб = "
                    f"{int(user_data['cost_area'])} руб.\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🧱 Бордюр тротуарный: {user_data['curb1_length']} м × "
                    f"{PRICES['bordur'][1]['price']} руб = "
                    f"{int(user_data['cost_curb1'])} руб.\n"
                    f"🧱 Бордюр дорожный:   {user_data['curb2_length']} м × "
                    f"{PRICES['bordur'][2]['price']} руб = "
                    f"{int(user_data['cost_curb2'])} руб.\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 ИТОГО К ОПЛАТЕ: {int(user_data['total_price'])} руб.\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                result_msg += (
                    f"✅ Заявка сохранена: {filename}\n" if filename
                    else "⚠️ Ошибка сохранения на Яндекс.Диск\n"
                )
                result_msg += (
                    "Наш специалист свяжется с вами в ближайшее время.\n\n"
                    "💡 Чтобы сделать новый расчёт, напишите «Начать»"
                )

                send_message(user_id, result_msg)
                del users_state[user_id]

            elif 'повторить' in text_lower or '🔄' in text:
                users_state[user_id] = {'step': 'ask_name'}
                vk_name = get_user_name(user_id)

                if vk_name:
                    users_state[user_id]['vk_name'] = vk_name
                    kb = VkKeyboard(one_time=True)
                    kb.add_button(f'Да, я {vk_name}', color=VkKeyboardColor.POSITIVE)
                    kb.add_line()
                    kb.add_button('Ввести другое имя', color=VkKeyboardColor.SECONDARY)
                    send_message(user_id, f"🔄 Начинаем заново!\n\nВас зовут {vk_name}?",
                                 keyboard=kb)
                else:
                    send_message(user_id, "🔄 Начинаем заново!\n\nВведите ваше имя:",
                                 keyboard=VkKeyboard.get_empty_keyboard())
            else:
                send_message(user_id, "Пожалуйста, нажмите «Закончить ввод» или «Повторить ввод».")
