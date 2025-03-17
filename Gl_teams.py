import telebot
import logging
import sqlite3
from telebot import types

# ------------------- إعدادات السجل -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_log.txt'),
        logging.StreamHandler()
    ]
)

# ------------------- إعداد التوكن -------------------
BOT_TOKEN = '7571054483:AAENS5T6VftaFkId0T6wj5tQ_WaOXFRG19w'
bot = telebot.TeleBot(BOT_TOKEN)

# ------------------- إعداد قاعدة البيانات -------------------
conn = sqlite3.connect('gl_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT DEFAULT 'ar',
    current_menu TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# ------------------- الإعدادات العامة -------------------
ADMINS = [5530049632]  # قائمة المدراء
CHANNEL = "@GL_TEAMSp"  # قناة الاشتراك الإجبارية

# ------------------- الدوال المساعدة -------------------
def create_accept_reject_buttons(user_id):
    markup = types.InlineKeyboardMarkup()
    accept_btn = types.InlineKeyboardButton("قبول ✅", callback_data=f"accept_{user_id}")
    reject_btn = types.InlineKeyboardButton("رفض ❌", callback_data=f"reject_{user_id}")
    markup.add(accept_btn, reject_btn)
    return markup

def update_user_menu(user_id, menu_name):
    cursor.execute('UPDATE users SET current_menu = ? WHERE user_id = ?', (menu_name, user_id))
    conn.commit()

def get_current_menu(user_id):
    cursor.execute('SELECT current_menu FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def is_admin(user_id):
    return user_id in ADMINS

def is_subscribed(chat_id):
    try:
        status = bot.get_chat_member(CHANNEL, chat_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"فشل التحقق من الاشتراك: {e}")
        return False

def get_user_lang(user_id):
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 'ar'

# ------------------- معالجة الأوامر -------------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id

        if not is_subscribed(chat_id):
            bot.send_message(chat_id, "⛔️ يجب الاشتراك في القناة أولاً:\nhttps://t.me/GL_TEAMSp")
            return

        welcome_text = """🌟 أهلًا بك في بوت فريق GL TEAMS الرسمي!

↯【 يمكنك هنا 】↯
- التقديم للانضمام للفريق
- معرفة الشروط المطلوبة
- التواصل مع الإدارة
- متابعة حساباتنا الرسمية"""

        bot.send_message(chat_id, welcome_text)

        cursor.execute('INSERT OR REPLACE INTO users (user_id, language, current_menu) VALUES (?, ?, ?)', 
                      (user_id, 'ar', 'main_menu'))
        conn.commit()

        send_main_menu(chat_id)

    except Exception as e:
        logging.error(f"خطأ في أمر /start: {e}")
        bot.reply_to(message, "❌ حدث خطأ غير متوقع، يرجى المحاولة لاحقًا")

# ------------------- القوائم الرئيسية -------------------
def send_main_menu(chat_id):
    user_id = chat_id
    lang = get_user_lang(user_id)

    texts = {
        'ar': {
            'message': "اختر من القائمة:",
            'buttons': ['الشروط 📜', 'قناة التلجرام 📣', 'مواقع التواصل 🌐', 'الدعم الفني 🛠', 'English']
        },
        'en': {
            'message': "Choose from menu:",
            'buttons': ['Conditions 📜', 'Telegram Channel 📣', 'Social Media 🌐', 'Support 🛠', 'العربية']
        }
    }

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(btn) for btn in texts[lang]['buttons']]
    markup.add(*buttons)

    update_user_menu(user_id, 'main_menu')
    bot.send_message(chat_id, texts[lang]['message'], reply_markup=markup)

# ------------------- معالجة الشروط -------------------
@bot.message_handler(func=lambda m: m.text in ['الشروط 📜', 'Conditions 📜'])
def show_conditions(message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)

    conditions = {
        'ar': """📜 شروط الانضمام إلى GL TEAMS:

1️⃣ بطاقة تغيير اسم (مهلة 30 يوم) ⏳
2️⃣ مستوى الحساب لازم يكون 50 🎮
3️⃣ الموسم ماسي V 🏅
4️⃣ KD فوق 3 🎯
5️⃣ التفاعل المستمر معنا 💬 (غيابك لأسبوع بدون عذر؟ 🚫 مرفوض!)
6️⃣ الاحترام التام بين الأعضاء 🤝 عشان نحافظ على أجواء مريحة وممتعة""",
        'en': """📜 GL TEAMS Joining Conditions:

1️⃣ Name change card (30-day deadline) ⏳
2️⃣ Account level must be 50 🎮
3️⃣ Season Master V 🏅
4️⃣ KD above 3 🎯
5️⃣ Continuous interaction with us 💬 (Absence for a week without an excuse? 🚫 Not acceptable!)
6️⃣ Full respect between members 🤝 to maintain a comfortable and enjoyable atmosphere"""
    }

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    apply_text = 'أطبق الشروط ✅' if lang == 'ar' else 'Apply Conditions ✅'
    back_text = 'عودة ↩️' if lang == 'ar' else 'Back ↩️'
    markup.add(types.KeyboardButton(apply_text), types.KeyboardButton(back_text))

    update_user_menu(user_id, 'conditions_menu')
    bot.send_message(message.chat.id, conditions[lang], reply_markup=markup)

# ------------------- معالجة القناة -------------------
@bot.message_handler(func=lambda m: m.text in ['قناة التلجرام 📣', 'Telegram Channel 📣'])
def show_channel(message):
    lang = get_user_lang(message.from_user.id)
    text = {
        'ar': "📢 قناتنا الرسمية على التلجرام:\nhttps://t.me/GL_TEAMSp",
        'en': "📢 Our official Telegram channel:\nhttps://t.me/GL_TEAMSp"
    }[lang]
    bot.send_message(message.chat.id, text)

# ------------------- معالجة مواقع التواصل -------------------
@bot.message_handler(func=lambda m: m.text in ['مواقع التواصل 🌐', 'Social Media 🌐'])
def show_social_media(message):
    lang = get_user_lang(message.from_user.id)

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("TikTok", url="https://www.tiktok.com/@abn_gaza05"),
        types.InlineKeyboardButton("Instagram", url="https://instagram.com/abn_gaza05")
    )
    markup.row(types.InlineKeyboardButton("YouTube", url="https://youtube.com/@abn_gaza05"))

    text = {
        'ar': "🌐 حساباتنا على منصات التواصل:",
        'en': "🌐 Our social media accounts:"
    }[lang]

    bot.send_message(message.chat.id, text, reply_markup=markup)

    # إضافة زر الرجوع
    back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_text = 'عودة ↩️' if lang == 'ar' else 'Back ↩️'
    back_markup.add(types.KeyboardButton(back_text))
    update_user_menu(message.from_user.id, 'social_menu')
    bot.send_message(message.chat.id, "↩️", reply_markup=back_markup)

# ------------------- معالجة الدعم الفني -------------------
@bot.message_handler(func=lambda m: m.text in ['الدعم الفني 🛠', 'Support 🛠'])
def show_support(message):
    lang = get_user_lang(message.from_user.id)
    text = {
        'ar': "📩 للدعم الفني:\n@Abn_gaza05\n@October7_2023",
        'en': "📩 Technical support:\n@Abn_gaza05\n@October7_2023"
    }[lang]
    bot.send_message(message.chat.id, text)

# ------------------- معالجة الرجوع -------------------
@bot.message_handler(func=lambda m: m.text in ['عودة ↩️', 'Back ↩️'])
def handle_back(message):
    send_main_menu(message.chat.id)

# ------------------- معالجة التقديم -------------------
@bot.message_handler(func=lambda m: m.text in ['أطبق الشروط ✅', 'Apply Conditions ✅'])
def handle_apply(message):
    lang = get_user_lang(message.from_user.id)
    update_user_menu(message.from_user.id, 'awaiting_video')
    text = {
        'ar': "🎥 يرجى إرسال فيديو يوضح إحصائياتك:",
        'en': "🎥 Please send a video showing your stats:"
    }[lang]
    bot.send_message(message.chat.id, text)

# ------------------- معالجة استقبال الفيديو -------------------
@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    if get_current_menu(user_id) == 'awaiting_video':
        response = {
            'ar': "✅ تم استلام الفيديو، سيتم مراجعته من قبل الإدارة",
            'en': "✅ Video received, will be reviewed by admin"
        }[lang]
        bot.reply_to(message, response)

        # إرسال الفيديو للمدراء مع أزرار القبول/الرفض
        username = message.from_user.username
        caption = f"طلب انضمام جديد من المستخدم: {user_id}"
        if username:
            caption += f" (@{username})"

        for admin in ADMINS:
            try:
                bot.send_video(
                    admin,
                    message.video.file_id,
                    caption=caption,
                    reply_markup=create_accept_reject_buttons(user_id)
                )
            except Exception as e:
                logging.error(f"فشل إرسال الفيديو إلى المدير {admin}: {e}")

        update_user_menu(user_id, 'main_menu')
        send_main_menu(message.chat.id)
    else:
        bot.reply_to(message, "تم استلام الفيديو.")

# ------------------- معالجة الرسائل غير الفيديو أثناء انتظار الفيديو -------------------
@bot.message_handler(func=lambda m: get_current_menu(m.from_user.id) == 'awaiting_video' and m.content_type in ['text', 'photo'])
def handle_non_video(message):
    lang = get_user_lang(message.from_user.id)
    response = {
        'ar': "❌ يرجى إرسال فيديو فقط يوضح إحصائياتك:",
        'en': "❌ Please send a video only showing your stats:"
    }[lang]
    bot.reply_to(message, response)

# ------------------- معالجة إدخال الايدي لببجي -------------------
@bot.message_handler(func=lambda m: get_current_menu(m.from_user.id) == 'awaiting_pubg_id' and m.content_type == 'text')
def handle_pubg_id(message):
    lang = get_user_lang(message.from_user.id)
    pubg_id = message.text.strip()
    if not pubg_id.isdigit():
        response = {
            'ar': "يرجى كتابت الايدي الصحيح",
            'en': "Please enter the correct ID"
        }[lang]
        bot.reply_to(message, response)
    else:
        # إرسال الايدي للمدراء
        for admin in ADMINS:
            try:
                bot.send_message(admin, f"قام المستخدم {message.from_user.id} بإرسال الايدي: {pubg_id}")
            except Exception as e:
                logging.error(f"فشل إرسال الايدي إلى المدير {admin}: {e}")

        response = {
            'ar': "تم استلام الايدي بنجاح ✅! يُرجى الانتظار حتى يصلك طلب الصداقة داخل اللعبة 🎮.",
            'en': "ID received successfully ✅! Please wait until you receive a friend request in-game 🎮."
        }[lang]
        bot.send_message(message.chat.id, response)
        update_user_menu(message.from_user.id, 'main_menu')
        send_main_menu(message.chat.id)

# ------------------- معالجة باقي المحتويات -------------------
# هنا يتم الرد على المحتويات التي لا تتعلق بحالات انتظار الفيديو أو إدخال الايدي
@bot.message_handler(func=lambda m: get_current_menu(m.from_user.id) not in ['awaiting_video', 'awaiting_pubg_id'] and m.content_type in ['text', 'photo'])
def handle_other_content(message):
    lang = get_user_lang(message.from_user.id)
    response = {
        'ar': "❌ يرجى إرسال فيديو فقط يوضح إحصائياتك:",
        'en': "❌ Please send a video only showing your stats:"
    }[lang]
    bot.reply_to(message, response)

# ------------------- معالجة ردود الإدارة -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith(('accept_', 'reject_')))
def handle_admin_response(call):
    try:
        action, user_id = call.data.split('_')
        user_id = int(user_id)
        admin_id = call.from_user.id

        if admin_id not in ADMINS:
            bot.answer_callback_query(call.id, "غير مصرح لك بهذا الإجراء!")
            return

        lang = get_user_lang(user_id)

        try:
            if action == 'accept':
                user_msg = "تهانينا! تم قبولك 🎉. يُرجى إرسال الايدي وانتظار طلب الصداقة في ببجي 🤝." if lang == 'ar' else "Congratulations! You've been accepted 🎉. Please send your ID and wait for a friend request in PUBG 🤝."
                update_user_menu(user_id, 'awaiting_pubg_id')
                admin_msg = f"✅ تم قبول طلب المستخدم {user_id}"
            else:
                user_msg = "نعتذر، لم يتم قبول طلبك هذه المرة. نؤمن بقدراتك ونشجعك على تطوير نفسك والمحاولة مجدداً. 💪😊" if lang == 'ar' else "We apologize, your application was not accepted this time. We believe in your abilities and encourage you to develop yourself and try again. 💪😊"
                update_user_menu(user_id, 'main_menu')
                admin_msg = f"❌ تم رفض طلب المستخدم {user_id}"

            bot.send_message(user_id, user_msg)
            if action == 'reject':
                send_main_menu(user_id)
        except telebot.apihelper.ApiTelegramException as e:
            if e.result.status_code == 403:
                error_msg = f"⚠️ تعذر إرسال الرسالة للمستخدم {user_id} (قام بحظر البوت)"
                bot.send_message(admin_id, error_msg)

        bot.send_message(admin_id, admin_msg)

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        logging.error(f"خطأ في معالجة الرد: {e}")

# ------------------- تبديل اللغات -------------------
@bot.message_handler(func=lambda m: m.text in ['English', 'العربية'])
def change_language(message):
    user_id = message.from_user.id
    new_lang = 'en' if message.text == 'English' else 'ar'

    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (new_lang, user_id))
    conn.commit()

    confirm_text = {
        'ar': 'تم تغيير اللغة إلى العربية بنجاح ✅',
        'en': 'Language changed to English successfully ✅'
    }[new_lang]

    bot.send_message(message.chat.id, confirm_text)
    send_main_menu(message.chat.id)

# ------------------- تشغيل البوت -------------------
if __name__ == '__main__':
    try:
        logging.info("Starting GL TEAMS bot...")
        bot.infinity_polling()
    except Exception as e:
        logging.critical(f"Bot crashed: {e}")
    finally:
        conn.close()
        logging.info("Database connection closed")