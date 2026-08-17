import os
import json
import yt_dlp
import asyncio
import subprocess
import sys
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ==================== التحديث التلقائي للمكتبات ====================
def update_ytdlp():
    try:
        print("🔄 جاري فحص وتحديث مكتبة yt-dlp تلقائياً لأحدث إصدار...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("✅ تم تحديث yt-dlp بنجاح!")
    except Exception as e:
        print(f"⚠️ تعذر التحديث التلقائي: {e}")

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_USERNAME = "@bdalalhm"
ADMIN_ID = 8328994103 

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

STARS_PRICE = 50 

# ==================== إدارة ملف جميع المستخدمين ====================
ALL_USERS_FILE = "all_users.json"

def load_all_users() -> dict:
    if os.path.exists(ALL_USERS_FILE):
        try:
            with open(ALL_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_users(users_dict: dict):
    with open(ALL_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, indent=4, ensure_ascii=False)

ALL_USERS = load_all_users()

def register_user(user):
    str_id = str(user.id)
    if str_id not in ALL_USERS:
        ALL_USERS[str_id] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "بدون يوزر",
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_all_users(ALL_USERS)

# ==================== إدارة بيانات الـ VIP ====================
VIP_FILE = "vip_users.json"

def load_vip_users() -> dict:
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_vip_users(vip_dict: dict):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump(vip_dict, f, indent=4)

VIP_USERS = load_vip_users()

def is_vip_active(user_id: int) -> bool:
    str_id = str(user_id)
    if str_id not in VIP_USERS:
        return False
    
    expiry_str = VIP_USERS[str_id]
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expiry_date:
            return True
        else:
            del VIP_USERS[str_id]
            save_vip_users(VIP_USERS)
            return False
    except Exception:
        return False

def activate_vip_for_days(user_id: int, days: int = 30):
    str_id = str(user_id)
    now = datetime.now()
    
    if is_vip_active(user_id):
        current_expiry = datetime.strptime(VIP_USERS[str_id], "%Y-%m-%d %H:%M:%S")
        new_expiry = current_expiry + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)
        
    VIP_USERS[str_id] = new_expiry.strftime("%Y-%m-%d %H:%M:%S")
    save_vip_users(VIP_USERS)
    return VIP_USERS[str_id]

# ==================== الأوامر والرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    
    is_vip = is_vip_active(user.id)
    vip_status = "👑 **أنت مشترك في VIP حالياً!**" if is_vip else "⚡ **النسخة المجانية:** (تنزيل عادي حتى 30MB)"

    welcome_text = (
        f"أهلاً بك يا {user.first_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        f"الحالة: {vip_status}\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, Instagram, YouTube, Facebook...) وسأقوم بتحميله لك فوراً.\n\n"
        "⚠️ **تنويه وإخلاء مسؤولية:**\n"
        "هذا البوت أداة تقنية مخصصة للتنزيل فقط، ويتحمل المستخدم وحده المسؤولية الشرعية والقانونية عن نوعية المحتوى الذي يقوم بتحميله."
    )
    
    inline_keyboard = []
    if not is_vip:
        inline_keyboard.append([InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")])
        inline_keyboard.append([InlineKeyboardButton("🏦 التحويل بي بنكك", callback_data="bankak_info")])
    
    inline_keyboard.append([InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")])
    
    # إضافة أزرار الكيبورد الثابتة في أسفل الشاشة للأدمن فقط
    reply_markup_keyboard = None
    if user.id == ADMIN_ID:
        admin_keyboard = [
            [KeyboardButton("📊 الإحصائيات والتقدم"), KeyboardButton("📋 قائمة المشتركين")]
        ]
        reply_markup_keyboard = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    if reply_markup_keyboard:
        await update.message.reply_text("👑 **مرحباً بك يا مدير! تم تفعيل أزرار لوحة التحكم الثابتة في الكيبورد بالأسفل.**", reply_markup=reply_markup_keyboard)

# معالجة نصوص أزرار الكيبورد الثابتة للأدمن
async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        return False

    if text == "📊 الإحصائيات والتقدم":
        await stats(update, context)
        return True
    elif text == "📋 قائمة المشتركين":
        await list_users(update, context)
        return True
        
    return False

# أمر معرفة التقدم والإحصائيات الكلية
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    total_users = len(ALL_USERS)
    vip_count = len(VIP_USERS)
    free_users = total_users - vip_count
    
    report = (
        "📊 **تقرير تقدم وانتشار البوت:**\n\n"
        f"👥 **إجمالي المشتركين الكلي:** `{total_users}` شخص\n"
        f"👑 **عدد مشتركي VIP:** `{vip_count}`\n"
        f"🆓 **عدد مستخدمي المجاني:** `{free_users}`"
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# أمر استخراج قائمة بكل المستخدمين
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not ALL_USERS:
        await update.message.reply_text("لا يوجد مستخدمون مسجلون بعد.")
        return

    text = "📋 **قائمة المشتركين في البوت:**\n\n"
    for uid, data in ALL_USERS.items():
        vip_tag = " [👑 VIP]" if is_vip_active(int(uid)) else ""
        text += f"• {data['name']} ({data['username']}) - `{uid}`{vip_tag}\n"
    
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        new_vip_id = int(context.args[0])
        expiry_time = activate_vip_for_days(new_vip_id, days=30)
        await update.message.reply_text(f"✅ تم تفعيل VIP لمدة 30 يوم لـ `{new_vip_id}`", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=new_vip_id,
                text=f"🎉 **تم تفعيل اشتراك VIP بحسابك بنجاح لمدة 30 يوماً!**\n📅 ينتهي في: `{expiry_time}`",
                parse_mode="Markdown"
            )
        except:
            pass
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ طريقة الاستخدام: `/addvip 123456789`", parse_mode="Markdown")

async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        remove_id = str(int(context.args[0]))
        if remove_id in VIP_USERS:
            del VIP_USERS[remove_id]
            save_vip_users(VIP_USERS)
            await update.message.reply_text(f"✅ تم إزالة `{remove_id}` من VIP.", parse_mode="Markdown")
    except:
        pass

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    photo_file_id = update.message.photo[-1].file_id
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=(
            f"🔔 **إشعار دفع جديد (بنكك)!**\n\n"
            f"👤 **المستخدم:** {user.first_name}\n"
            f"🆔 **الآيدي تلقائياً:** `{user.id}`\n\n"
            f"⚡ **اضغط على الأمر أدناه لنسخه وتفعيل المشترك فوراً:**\n"
            f"`/addvip {user.id}`"
        ),
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("✅ **تم استلام صورة الإشعار بنجاح!**\nجاري مراجعة التحويل وتفعيل حسابك كـ VIP في أقرب وقت.")

# ==================== التنزيل ومعالجة الرسائل ====================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin_button = await handle_admin_buttons(update, context)
    if is_admin_button:
        return

    url = update.message.text
    await download_and_send(update, context, url)

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    query = update.callback_query
    user = update.effective_user
    register_user(user)
    msg = await query.message.reply_text("🎧 جاري استخراج الصوت MP3...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': f'downloads/{user.id}_audio.%(ext)s',
            'quiet': True,
        }
        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        filename = await loop.run_in_executor(None, download_process)
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(filename, 'rb'))
        if os.path.exists(filename): os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"⚠️ تعذر استخراج الصوت: {str(e)}")

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, is_hd: bool = False):
    user = update.effective_user
    register_user(user)
    is_vip = is_vip_active(user.id)
    
    if update.message:
        msg = await update.message.reply_text("🔍 جاري فحص الرابط والتنزيل...")
    else:
        msg = await update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة ممتازة...")

    format_setting = 'best[filesize<=150M]/best' if is_hd else 'best[filesize<=30M]/worst'

    try:
        ydl_opts = {'format': format_setting, 'outtmpl': f'downloads/{user.id}_%(id)s.%(ext)s', 'quiet': True}
        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download_process)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 150:
            os.remove(filename)
            await msg.edit_text("⚠️ **تنبيه:** حجم الفيديو يتجاوز الحد الأقصى المسموح به للبوت وهو **150 ميجابايت** لحماية السيرفر.")
            return

        await msg.edit_text("📤 جاري رفع الفيديو إليك...")
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"dl_mp3_{url}"),
                InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD", callback_data=f"dl_hd_{url}")
            ]
        ]
        if not is_vip:
            keyboard.append([InlineKeyboardButton("👑 ترقية لحساب VIP", callback_data="vip_info")])

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open(filename, 'rb'),
            caption="✅ تم التنزيل بنجاح!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        if os.path.exists(filename): os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit_text("⚠️ تعذر التحميل! قد يكون الرابط غير مدعوم، أو تجاوز حجم الملف الحد الأقصى (150MB).")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    register_user(user)
    await query.answer()

    if data == "vip_info":
        vip_text = (
            "👑 **مميزات وشروط عضوية VIP (مدة شهر كامل):**\n\n"
            "✨ **المميزات:**\n"
            "• التحميل بأعلى جودة ممتازة متوفرة.\n"
            "• الحد الأقصى للملفات يصل إلى **150 ميجابايت**.\n"
            "• إمكانية تحويل أي مقطع فيديو إلى صوت MP3 بنقرة زر.\n\n"
            "------------------------------\n"
            f"🆔 **الآيدي الخاص بك:** `{user.id}` *(اضغط عليه للنسخ)*\n\n"
            "💳 **طرق الدفع والتفعيل:**\n"
            "1️⃣ **عبر تطبيق بنكك (Bankak):** اضغط على زر (التحويل بي بنكك) بالأسفل لفتح بيانات الحساب.\n"
            f"2️⃣ **عبر نجوم تلجرام (Telegram Stars):** بقيمة **{STARS_PRICE} نجمة ⭐️** (تفعيل تلقائي مائة بالمائة)\n\n"
            "📜 **شروط الخدمة والتعويض:**\n"
            "• في حال حدوث أي عطل تقني طارئ في السيرفر، يتم تعويض المشتركين بأيام إضافية مجانية تضمن حقهم كاملاً."
        )
        keyboard = [
            [InlineKeyboardButton("🏦 التحويل بي بنكك", callback_data="bankak_info")],
            [InlineKeyboardButton(f"⭐ الدفع الفوري بالنجمات ({STARS_PRICE} ⭐️)", callback_data="pay_stars")],
            [InlineKeyboardButton("🔙 إغلاق", callback_data="close_menu")]
        ]
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "bankak_info":
        bankak_text = (
            "🏦 **بيانات الدفع عبر تطبيق بنكك (Bankak):**\n\n"
            f"💰 **سعر الاشتراك (شهر كامل):** {BANKAK_PRICE}\n"
            f"🔢 **رقم الحساب:** `{BANKAK_ACCOUNT}` *(اضغط عليه للنسخ)*\n"
            f"👤 **اسم صاحب الحساب:** {BANKAK_NAME}\n\n"
            "------------------------------\n"
            "📸 **قم بتحويل المبلغ ثم أرسل صورة الإشعار هنا مباشرة في الشات وسأقوم برفعها للإدارة لتفعيل حسابك فوراً!**"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
        await query.message.reply_text(bankak_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("dl_hd_"):
        url = data.replace("dl_hd_", "")
        if not is_vip_active(user.id):
            await query.message.reply_text("🔒 التحميل بجودة HD مخصص لمشتركي VIP فقط.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")]]))
        else:
            await download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        url = data.replace("dl_mp3_", "")
        if not is_vip_active(user.id):
            await query.message.reply_text("🔒 استخراج الصوت MP3 مخصص لمشتركي VIP فقط.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")]]))
        else:
            await download_audio(update, context, url)

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل ====================

def main():
    update_ytdlp()
    if not os.path.exists("downloads"): os.makedirs("downloads")

    while True: # حلقة تكرارية لمنع توقف البوت نهائياً
        try:
            print("🚀 جاري تشغيل البوت...")
            app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
            
            app_bot.add_handler(CommandHandler("start", start))
            app_bot.add_handler(CommandHandler("addvip", add_vip))
            app_bot.add_handler(CommandHandler("delvip", del_vip))
            app_bot.add_handler(CommandHandler("stats", stats))
            app_bot.add_handler(CommandHandler("users", list_users))
            
            app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
            app_bot.add_handler(CallbackQueryHandler(button_callback))
            
            app_bot.run_polling()
            
        except Exception as e:
            print(f"⚠️ حدث خطأ فادح: {e}، جاري إعادة التشغيل في 5 ثوانٍ...")
            time.sleep(5)

if __name__ == "__main__":
    main()
import os
import json
import yt_dlp
import asyncio
import subprocess
import sys
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ==================== التحديث التلقائي للمكتبات ====================
def update_ytdlp():
    try:
        print("🔄 جاري فحص وتحديث مكتبة yt-dlp تلقائياً لأحدث إصدار...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("✅ تم تحديث yt-dlp بنجاح!")
    except Exception as e:
        print(f"⚠️ تعذر التحديث التلقائي: {e}")

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_USERNAME = "@bdalalhm"
ADMIN_ID = 8328994103 

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

STARS_PRICE = 50 

# ==================== إدارة ملف جميع المستخدمين ====================
ALL_USERS_FILE = "all_users.json"

def load_all_users() -> dict:
    if os.path.exists(ALL_USERS_FILE):
        try:
            with open(ALL_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_users(users_dict: dict):
    with open(ALL_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, indent=4, ensure_ascii=False)

ALL_USERS = load_all_users()

def register_user(user):
    str_id = str(user.id)
    if str_id not in ALL_USERS:
        ALL_USERS[str_id] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "بدون يوزر",
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_all_users(ALL_USERS)

# ==================== إدارة بيانات الـ VIP ====================
VIP_FILE = "vip_users.json"

def load_vip_users() -> dict:
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_vip_users(vip_dict: dict):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump(vip_dict, f, indent=4)

VIP_USERS = load_vip_users()

def is_vip_active(user_id: int) -> bool:
    str_id = str(user_id)
    if str_id not in VIP_USERS:
        return False
    
    expiry_str = VIP_USERS[str_id]
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expiry_date:
            return True
        else:
            del VIP_USERS[str_id]
            save_vip_users(VIP_USERS)
            return False
    except Exception:
        return False

def activate_vip_for_days(user_id: int, days: int = 30):
    str_id = str(user_id)
    now = datetime.now()
    
    if is_vip_active(user_id):
        current_expiry = datetime.strptime(VIP_USERS[str_id], "%Y-%m-%d %H:%M:%S")
        new_expiry = current_expiry + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)
        
    VIP_USERS[str_id] = new_expiry.strftime("%Y-%m-%d %H:%M:%S")
    save_vip_users(VIP_USERS)
    return VIP_USERS[str_id]

# ==================== الأوامر والرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    
    is_vip = is_vip_active(user.id)
    vip_status = "👑 **أنت مشترك في VIP حالياً!**" if is_vip else "⚡ **النسخة المجانية:** (تنزيل عادي حتى 30MB)"

    welcome_text = (
        f"أهلاً بك يا {user.first_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        f"الحالة: {vip_status}\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, Instagram, YouTube, Facebook...) وسأقوم بتحميله لك فوراً.\n\n"
        "⚠️ **تنويه وإخلاء مسؤولية:**\n"
        "هذا البوت أداة تقنية مخصصة للتنزيل فقط، ويتحمل المستخدم وحده المسؤولية الشرعية والقانونية عن نوعية المحتوى الذي يقوم بتحميله."
    )
    
    inline_keyboard = []
    if not is_vip:
        inline_keyboard.append([InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")])
        inline_keyboard.append([InlineKeyboardButton("🏦 التحويل بي بنكك", callback_data="bankak_info")])
    
    inline_keyboard.append([InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")])
    
    # إضافة أزرار الكيبورد الثابتة في أسفل الشاشة للأدمن فقط
    reply_markup_keyboard = None
    if user.id == ADMIN_ID:
        admin_keyboard = [
            [KeyboardButton("📊 الإحصائيات والتقدم"), KeyboardButton("📋 قائمة المشتركين")]
        ]
        reply_markup_keyboard = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard))
    
    if reply_markup_keyboard:
        await update.message.reply_text("👑 **مرحباً بك يا مدير! تم تفعيل أزرار لوحة التحكم الثابتة في الكيبورد بالأسفل.**", reply_markup=reply_markup_keyboard)

# معالجة نصوص أزرار الكيبورد الثابتة للأدمن
async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        return False

    if text == "📊 الإحصائيات والتقدم":
        await stats(update, context)
        return True
    elif text == "📋 قائمة المشتركين":
        await list_users(update, context)
        return True
        
    return False

# أمر معرفة التقدم والإحصائيات الكلية
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    total_users = len(ALL_USERS)
    vip_count = len(VIP_USERS)
    free_users = total_users - vip_count
    
    report = (
        "📊 **تقرير تقدم وانتشار البوت:**\n\n"
        f"👥 **إجمالي المشتركين الكلي:** `{total_users}` شخص\n"
        f"👑 **عدد مشتركي VIP:** `{vip_count}`\n"
        f"🆓 **عدد مستخدمي المجاني:** `{free_users}`"
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# أمر استخراج قائمة بكل المستخدمين
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not ALL_USERS:
        await update.message.reply_text("لا يوجد مستخدمون مسجلون بعد.")
        return

    text = "📋 **قائمة المشتركين في البوت:**\n\n"
    for uid, data in ALL_USERS.items():
        vip_tag = " [👑 VIP]" if is_vip_active(int(uid)) else ""
        text += f"• {data['name']} ({data['username']}) - `{uid}`{vip_tag}\n"
    
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")

async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        new_vip_id = int(context.args[0])
        expiry_time = activate_vip_for_days(new_vip_id, days=30)
        await update.message.reply_text(f"✅ تم تفعيل VIP لمدة 30 يوم لـ `{new_vip_id}`", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=new_vip_id,
                text=f"🎉 **تم تفعيل اشتراك VIP بحسابك بنجاح لمدة 30 يوماً!**\n📅 ينتهي في: `{expiry_time}`",
                parse_mode="Markdown"
            )
        except:
            pass
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ طريقة الاستخدام: `/addvip 123456789`", parse_mode="Markdown")

async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        remove_id = str(int(context.args[0]))
        if remove_id in VIP_USERS:
            del VIP_USERS[remove_id]
            save_vip_users(VIP_USERS)
            await update.message.reply_text(f"✅ تم إزالة `{remove_id}` من VIP.", parse_mode="Markdown")
    except:
        pass

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    photo_file_id = update.message.photo[-1].file_id
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=(
            f"🔔 **إشعار دفع جديد (بنكك)!**\n\n"
            f"👤 **المستخدم:** {user.first_name}\n"
            f"🆔 **الآيدي تلقائياً:** `{user.id}`\n\n"
            f"⚡ **اضغط على الأمر أدناه لنسخه وتفعيل المشترك فوراً:**\n"
            f"`/addvip {user.id}`"
        ),
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("✅ **تم استلام صورة الإشعار بنجاح!**\nجاري مراجعة التحويل وتفعيل حسابك كـ VIP في أقرب وقت.")

# ==================== التنزيل ومعالجة الرسائل ====================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin_button = await handle_admin_buttons(update, context)
    if is_admin_button:
        return

    url = update.message.text
    await download_and_send(update, context, url)

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    query = update.callback_query
    user = update.effective_user
    register_user(user)
    msg = await query.message.reply_text("🎧 جاري استخراج الصوت MP3...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': f'downloads/{user.id}_audio.%(ext)s',
            'quiet': True,
        }
        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        filename = await loop.run_in_executor(None, download_process)
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(filename, 'rb'))
        if os.path.exists(filename): os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"⚠️ تعذر استخراج الصوت: {str(e)}")

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, is_hd: bool = False):
    user = update.effective_user
    register_user(user)
    is_vip = is_vip_active(user.id)
    
    if update.message:
        msg = await update.message.reply_text("🔍 جاري فحص الرابط والتنزيل...")
    else:
        msg = await update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة ممتازة...")

    format_setting = 'best[filesize<=150M]/best' if is_hd else 'best[filesize<=30M]/worst'

    try:
        ydl_opts = {'format': format_setting, 'outtmpl': f'downloads/{user.id}_%(id)s.%(ext)s', 'quiet': True}
        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download_process)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 150:
            os.remove(filename)
            await msg.edit_text("⚠️ **تنبيه:** حجم الفيديو يتجاوز الحد الأقصى المسموح به للبوت وهو **150 ميجابايت** لحماية السيرفر.")
            return

        await msg.edit_text("📤 جاري رفع الفيديو إليك...")
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"dl_mp3_{url}"),
                InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD", callback_data=f"dl_hd_{url}")
            ]
        ]
        if not is_vip:
            keyboard.append([InlineKeyboardButton("👑 ترقية لحساب VIP", callback_data="vip_info")])

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open(filename, 'rb'),
            caption="✅ تم التنزيل بنجاح!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        if os.path.exists(filename): os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit_text("⚠️ تعذر التحميل! قد يكون الرابط غير مدعوم، أو تجاوز حجم الملف الحد الأقصى (150MB).")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    register_user(user)
    await query.answer()

    if data == "vip_info":
        vip_text = (
            "👑 **مميزات وشروط عضوية VIP (مدة شهر كامل):**\n\n"
            "✨ **المميزات:**\n"
            "• التحميل بأعلى جودة ممتازة متوفرة.\n"
            "• الحد الأقصى للملفات يصل إلى **150 ميجابايت**.\n"
            "• إمكانية تحويل أي مقطع فيديو إلى صوت MP3 بنقرة زر.\n\n"
            "------------------------------\n"
            f"🆔 **الآيدي الخاص بك:** `{user.id}` *(اضغط عليه للنسخ)*\n\n"
            "💳 **طرق الدفع والتفعيل:**\n"
            "1️⃣ **عبر تطبيق بنكك (Bankak):** اضغط على زر (التحويل بي بنكك) بالأسفل لفتح بيانات الحساب.\n"
            f"2️⃣ **عبر نجوم تلجرام (Telegram Stars):** بقيمة **{STARS_PRICE} نجمة ⭐️** (تفعيل تلقائي مائة بالمائة)\n\n"
            "📜 **شروط الخدمة والتعويض:**\n"
            "• في حال حدوث أي عطل تقني طارئ في السيرفر، يتم تعويض المشتركين بأيام إضافية مجانية تضمن حقهم كاملاً."
        )
        keyboard = [
            [InlineKeyboardButton("🏦 التحويل بي بنكك", callback_data="bankak_info")],
            [InlineKeyboardButton(f"⭐ الدفع الفوري بالنجمات ({STARS_PRICE} ⭐️)", callback_data="pay_stars")],
            [InlineKeyboardButton("🔙 إغلاق", callback_data="close_menu")]
        ]
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "bankak_info":
        bankak_text = (
            "🏦 **بيانات الدفع عبر تطبيق بنكك (Bankak):**\n\n"
            f"💰 **سعر الاشتراك (شهر كامل):** {BANKAK_PRICE}\n"
            f"🔢 **رقم الحساب:** `{BANKAK_ACCOUNT}` *(اضغط عليه للنسخ)*\n"
            f"👤 **اسم صاحب الحساب:** {BANKAK_NAME}\n\n"
            "------------------------------\n"
            "📸 **قم بتحويل المبلغ ثم أرسل صورة الإشعار هنا مباشرة في الشات وسأقوم برفعها للإدارة لتفعيل حسابك فوراً!**"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]]
        await query.message.reply_text(bankak_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("dl_hd_"):
        url = data.replace("dl_hd_", "")
        if not is_vip_active(user.id):
            await query.message.reply_text("🔒 التحميل بجودة HD مخصص لمشتركي VIP فقط.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")]]))
        else:
            await download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        url = data.replace("dl_mp3_", "")
        if not is_vip_active(user.id):
            await query.message.reply_text("🔒 استخراج الصوت MP3 مخصص لمشتركي VIP فقط.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")]]))
        else:
            await download_audio(update, context, url)

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل ====================

def main():
    update_ytdlp()
    if not os.path.exists("downloads"): os.makedirs("downloads")

    while True: # حلقة تكرارية لمنع توقف البوت نهائياً
        try:
            print("🚀 جاري تشغيل البوت...")
            app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
            
            app_bot.add_handler(CommandHandler("start", start))
            app_bot.add_handler(CommandHandler("addvip", add_vip))
            app_bot.add_handler(CommandHandler("delvip", del_vip))
            app_bot.add_handler(CommandHandler("stats", stats))
            app_bot.add_handler(CommandHandler("users", list_users))
            
            app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
            app_bot.add_handler(CallbackQueryHandler(button_callback))
            
            app_bot.run_polling()
            
        except Exception as e:
            print(f"⚠️ حدث خطأ فادح: {e}، جاري إعادة التشغيل في 5 ثوانٍ...")
            time.sleep(5)

if __name__ == "__main__":
    main()
