import os
import json
import yt_dlp
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_USERNAME = "@bdalalhm"
ADMIN_ID = 8328994103  # آيدي التلجرام الخاص بك للتحكم في البوت

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

STARS_PRICE = 50  # سعر الاشتراك بنجوم تلجرام

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
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    is_vip = is_vip_active(user_id)
    vip_status = "👑 **أنت مشترك في VIP حالياً!**" if is_vip else "⚡ **النسخة المجانية:** (تنزيل عادي حتى 30MB)"

    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        f"الحالة: {vip_status}\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, YouTube, Facebook, Instagram...) وسأقوم بتحميله لك فوراً.\n"
    )
    
    keyboard = []
    if not is_vip:
        keyboard.append([InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")])
    
    keyboard.append([InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمدير البوت فقط.")
        return

    try:
        new_vip_id = int(context.args[0])
        expiry_time = activate_vip_for_days(new_vip_id, days=30)
        
        await update.message.reply_text(
            f"✅ تم ترقية المستخدم `{new_vip_id}` إلى VIP لمدة 30 يوماً بنجاح!\n"
            f"📅 ينتهي الاشتراك بتاريخ: `{expiry_time}`",
            parse_mode="Markdown"
        )
        
        try:
            await context.bot.send_message(
                chat_id=new_vip_id,
                text=f"🎉 **تهانينا! تم تفعيل اشتراك VIP بحسابك بنجاح لمدة شهر.**\n📅 ينتهي في: `{expiry_time}`\nيمكنك الآن التحميل بجودة HD واستخراج MP3!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\n`/addvip 123456789`", parse_mode="Markdown")


async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    try:
        remove_id = str(int(context.args[0]))
        if remove_id in VIP_USERS:
            del VIP_USERS[remove_id]
            save_vip_users(VIP_USERS)
            await update.message.reply_text(f"✅ تم إزالة المستخدم `{remove_id}` من VIP بنجاح.")
        else:
            await update.message.reply_text("⚠️ المستخدم غير موجود في قائمة VIP.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\n`/delvip 123456789`", parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=(
                f"🔔 **إشعار دفع جديد (بنكك)!**\n\n"
                f"👤 **المستخدم:** {user.first_name} (@{user.username if user.username else 'لا يوجد'})\n"
                f"🆔 **الآيدي:** `{user.id}`\n\n"
                f"⚡ **لتفعيل المشترك لمدة شهر اضغط على الأمر للنسخ:**\n"
                f"`/addvip {user.id}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending photo to admin: {e}")

    await update.message.reply_text(
        "✅ **تم استلام صورة الإشعار بنجاح!**\n\n"
        "جاري مراجعة الإشعار وتفعيل حسابك كـ VIP لمدة شهر في أقرب وقت. 👑",
        parse_mode="Markdown"
    )

# ==================== نظام الدفع عبر Telegram Stars ====================

async def send_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    
    title = "اشتراك VIP المميز (شهر كامل) 👑"
    description = "التحميل بأعلى جودة HD متاحة لسرعة السيرفر + استخراج الصوت MP3 لمدة 30 يوماً"
    payload = "vip_subscription_stars"
    currency = "XTR"
    prices = [LabeledPrice("اشتراك 30 يوم VIP", STARS_PRICE)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency=currency,
        prices=prices
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "vip_subscription_stars":
        await query.answer(ok=False, error_message="حدث خطأ أثناء المعالجة.")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    expiry_time = activate_vip_for_days(user_id, days=30)

    await update.message.reply_text(
        f"🎉 **تم الدفع بنجاح عبر نجوم تلجرام!**\n\n"
        f"تم ترقية حسابك إلى **VIP** لمدة 30 يوماً تلقائياً!\n"
        f"📅 ينتهي اشتراكك في: `{expiry_time}`",
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💰 **شراء VIP تلقائي لمدة شهر (Telegram Stars)!**\n\n"
                f"👤 **المستخدم:** {user_name}\n"
                f"🆔 **الآيدي:** `{user_id}`\n"
                f"⭐️ **المبلغ:** {STARS_PRICE} نجمة\n"
                f"📅 **الانتهاء:** `{expiry_time}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notifying admin: {e}")

# ==================== التنزيل ومعالجة الصوت والفيديو ====================

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    query = update.callback_query
    user_id = update.effective_user.id
    msg = await query.message.reply_text("🎧 جاري استخراج الصوت وتحويله إلى MP3... انتظر قليلاً")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{user_id}_audio.%(ext)s',
            'quiet': True,
        }

        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base_name, _ = os.path.splitext(filename)
                return base_name + ".mp3"

        filename = await loop.run_in_executor(None, download_process)

        await msg.edit_text("📤 جاري رفع الملف الصوتي إليك...")

        with open(filename, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ حدث خطأ أثناء استخراج الصوت: {str(e)}")


async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, is_hd: bool = False):
    user_id = update.effective_user.id
    is_vip = is_vip_active(user_id)
    
    if update.message:
        msg = await update.message.reply_text("🔍 جاري فحص الرابط ومعالجة الفيديو...")
    else:
        msg = await update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة ممتازة...")

    keyboard = [
        [
            InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"dl_mp3_{url}"),
            InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD", callback_data=f"dl_hd_{url}")
        ]
    ]
    
    if not is_vip:
        keyboard.append([InlineKeyboardButton("💳 ترقية لحساب VIP (شهر كامل)", callback_data="vip_info")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_hd:
        format_setting = 'best[filesize<=150M]/bestvideo[filesize<=100M]+bestaudio/best[height<=720]/best'
    else:
        format_setting = 'best[filesize<=30M]/worst'

    try:
        ydl_opts = {
            'format': format_setting,
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download_process)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 150:
            os.remove(filename)
            await msg.edit_text(
                "⚠️ **تنبيه:** حجم الفيديو كبير جداً فوق طاقة السيرفر المجاني الحالي (أكبر من 150 ميجابايت).\n"
                "تم إيقاف التحميل لمنع تعطل البوت."
            )
            return

        await msg.edit_text("📤 جاري رفع الفيديو إليك الآن...")

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح {'(بجودة عالية 👑)' if is_hd else ''}!\n\n🎬 *تم إرسال الفيديو بالكامل كملف واحد.*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text("⚠️ تعذر تنزيل الفيديو! قد يكون الحجم كبيراً جداً أو الرابط غير مدعوم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https أو أرسل صورة إشعار التحويل.")
        return

    await download_and_send(update, context, url, is_hd=False)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "vip_info":
        vip_text = (
            "👑 **مميزات العضوية الممتازة (VIP) - لمدة شهر:**\n"
            "• تنزيل الفيديوهات بأعلى دقة متاحة كفيديو واحد.\n"
            "• تحويل أي فيديو إلى مقطع صوتي MP3 بنقرة زر.\n"
            "• أولوية وسرعة فائقة في المعالجة.\n\n"
            "------------------------------\n"
            "💳 **طرق الدفع المتاحة:**\n\n"
            "1️⃣ **الدفع المحلي (بنكك - Bankak):**\n"
            f"• رقم الحساب: `{BANKAK_ACCOUNT}`\n"
            f"• الاسم: **{BANKAK_NAME}**\n"
            f"• المبلغ: **{BANKAK_PRICE}**\n\n"
            "📸 **طريقة التفعيل:** قم بتحويل المبلغ ثم **أرسل صورة الإشعار هنا مباشرة داخل البوت** وسيتم التفعيل فوراً لمدة شهر كامل!\n\n"
            "2️⃣ **الدفع العالمي (نجوم تلجرام - Telegram Stars):**\n"
            f"• القيمة: **{STARS_PRICE} نجمة ⭐️** (تفعيل تلقائي مائة بالمائة)\n"
        )
        keyboard = [
            [InlineKeyboardButton(f"⭐ الدفع الفوري بالنجمات ({STARS_PRICE} ⭐️)", callback_data="pay_stars")],
            [InlineKeyboardButton("💬 التواصل المباشر مع الآدمن", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
        ]
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "pay_stars":
        await send_stars_invoice(update, context)

    elif data.startswith("dl_hd_"):
        url = data.replace("dl_hd_", "")
        if not is_vip_active(user_id):
            await query.message.reply_text(
                "🔒 **الجودة العالية مخصصة لمشتركي VIP فقط (أو انتهت فترة اشتراكك)!**\n\n"
                "اشترك الآن للاستفادة من الميزات بدون حدود مجانية.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        url = data.replace("dl_mp3_", "")
        if not is_vip_active(user_id):
            await query.message.reply_text(
                "🔒 **استخراج الصوت MP3 مخصص لمشتركي VIP فقط (أو انتهت فترة اشتراكك)!**\n\n"
                "اشترك الآن لفتح ميزة استخراج MP3 بنقرة واحدة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await download_audio(update, context, url)

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل الرئيسي ====================

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addvip", add_vip))
    app_bot.add_handler(CommandHandler("delvip", del_vip))
    import os
import json
import yt_dlp
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_USERNAME = "@bdalalhm"
ADMIN_ID = 8328994103  # آيدي التلجرام الخاص بك للتحكم في البوت

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

STARS_PRICE = 50  # سعر الاشتراك بنجوم تلجرام

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
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    is_vip = is_vip_active(user_id)
    vip_status = "👑 **أنت مشترك في VIP حالياً!**" if is_vip else "⚡ **النسخة المجانية:** (تنزيل عادي حتى 30MB)"

    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        f"الحالة: {vip_status}\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, YouTube, Facebook, Instagram...) وسأقوم بتحميله لك فوراً.\n"
    )
    
    keyboard = []
    if not is_vip:
        keyboard.append([InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")])
    
    keyboard.append([InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمدير البوت فقط.")
        return

    try:
        new_vip_id = int(context.args[0])
        expiry_time = activate_vip_for_days(new_vip_id, days=30)
        
        await update.message.reply_text(
            f"✅ تم ترقية المستخدم `{new_vip_id}` إلى VIP لمدة 30 يوماً بنجاح!\n"
            f"📅 ينتهي الاشتراك بتاريخ: `{expiry_time}`",
            parse_mode="Markdown"
        )
        
        try:
            await context.bot.send_message(
                chat_id=new_vip_id,
                text=f"🎉 **تهانينا! تم تفعيل اشتراك VIP بحسابك بنجاح لمدة شهر.**\n📅 ينتهي في: `{expiry_time}`\nيمكنك الآن التحميل بجودة HD واستخراج MP3!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\n`/addvip 123456789`", parse_mode="Markdown")


async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    try:
        remove_id = str(int(context.args[0]))
        if remove_id in VIP_USERS:
            del VIP_USERS[remove_id]
            save_vip_users(VIP_USERS)
            await update.message.reply_text(f"✅ تم إزالة المستخدم `{remove_id}` من VIP بنجاح.")
        else:
            await update.message.reply_text("⚠️ المستخدم غير موجود في قائمة VIP.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\n`/delvip 123456789`", parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=(
                f"🔔 **إشعار دفع جديد (بنكك)!**\n\n"
                f"👤 **المستخدم:** {user.first_name} (@{user.username if user.username else 'لا يوجد'})\n"
                f"🆔 **الآيدي:** `{user.id}`\n\n"
                f"⚡ **لتفعيل المشترك لمدة شهر اضغط على الأمر للنسخ:**\n"
                f"`/addvip {user.id}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending photo to admin: {e}")

    await update.message.reply_text(
        "✅ **تم استلام صورة الإشعار بنجاح!**\n\n"
        "جاري مراجعة الإشعار وتفعيل حسابك كـ VIP لمدة شهر في أقرب وقت. 👑",
        parse_mode="Markdown"
    )

# ==================== نظام الدفع عبر Telegram Stars ====================

async def send_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    
    title = "اشتراك VIP المميز (شهر كامل) 👑"
    description = "التحميل بأعلى جودة HD متاحة لسرعة السيرفر + استخراج الصوت MP3 لمدة 30 يوماً"
    payload = "vip_subscription_stars"
    currency = "XTR"
    prices = [LabeledPrice("اشتراك 30 يوم VIP", STARS_PRICE)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",
        currency=currency,
        prices=prices
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "vip_subscription_stars":
        await query.answer(ok=False, error_message="حدث خطأ أثناء المعالجة.")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    expiry_time = activate_vip_for_days(user_id, days=30)

    await update.message.reply_text(
        f"🎉 **تم الدفع بنجاح عبر نجوم تلجرام!**\n\n"
        f"تم ترقية حسابك إلى **VIP** لمدة 30 يوماً تلقائياً!\n"
        f"📅 ينتهي اشتراكك في: `{expiry_time}`",
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💰 **شراء VIP تلقائي لمدة شهر (Telegram Stars)!**\n\n"
                f"👤 **المستخدم:** {user_name}\n"
                f"🆔 **الآيدي:** `{user_id}`\n"
                f"⭐️ **المبلغ:** {STARS_PRICE} نجمة\n"
                f"📅 **الانتهاء:** `{expiry_time}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notifying admin: {e}")

# ==================== التنزيل ومعالجة الصوت والفيديو ====================

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    query = update.callback_query
    user_id = update.effective_user.id
    msg = await query.message.reply_text("🎧 جاري استخراج الصوت وتحويله إلى MP3... انتظر قليلاً")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{user_id}_audio.%(ext)s',
            'quiet': True,
        }

        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base_name, _ = os.path.splitext(filename)
                return base_name + ".mp3"

        filename = await loop.run_in_executor(None, download_process)

        await msg.edit_text("📤 جاري رفع الملف الصوتي إليك...")

        with open(filename, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"⚠️ حدث خطأ أثناء استخراج الصوت: {str(e)}")


async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, is_hd: bool = False):
    user_id = update.effective_user.id
    is_vip = is_vip_active(user_id)
    
    if update.message:
        msg = await update.message.reply_text("🔍 جاري فحص الرابط ومعالجة الفيديو...")
    else:
        msg = await update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة ممتازة...")

    keyboard = [
        [
            InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"dl_mp3_{url}"),
            InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD", callback_data=f"dl_hd_{url}")
        ]
    ]
    
    if not is_vip:
        keyboard.append([InlineKeyboardButton("💳 ترقية لحساب VIP (شهر كامل)", callback_data="vip_info")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_hd:
        format_setting = 'best[filesize<=150M]/bestvideo[filesize<=100M]+bestaudio/best[height<=720]/best'
    else:
        format_setting = 'best[filesize<=30M]/worst'

    try:
        ydl_opts = {
            'format': format_setting,
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        loop = asyncio.get_event_loop()
        def download_process():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download_process)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if file_size_mb > 150:
            os.remove(filename)
            await msg.edit_text(
                "⚠️ **تنبيه:** حجم الفيديو كبير جداً فوق طاقة السيرفر المجاني الحالي (أكبر من 150 ميجابايت).\n"
                "تم إيقاف التحميل لمنع تعطل البوت."
            )
            return

        await msg.edit_text("📤 جاري رفع الفيديو إليك الآن...")

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح {'(بجودة عالية 👑)' if is_hd else ''}!\n\n🎬 *تم إرسال الفيديو بالكامل كملف واحد.*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text("⚠️ تعذر تنزيل الفيديو! قد يكون الحجم كبيراً جداً أو الرابط غير مدعوم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https أو أرسل صورة إشعار التحويل.")
        return

    await download_and_send(update, context, url, is_hd=False)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "vip_info":
        vip_text = (
            "👑 **مميزات العضوية الممتازة (VIP) - لمدة شهر:**\n"
            "• تنزيل الفيديوهات بأعلى دقة متاحة كفيديو واحد.\n"
            "• تحويل أي فيديو إلى مقطع صوتي MP3 بنقرة زر.\n"
            "• أولوية وسرعة فائقة في المعالجة.\n\n"
            "------------------------------\n"
            "💳 **طرق الدفع المتاحة:**\n\n"
            "1️⃣ **الدفع المحلي (بنكك - Bankak):**\n"
            f"• رقم الحساب: `{BANKAK_ACCOUNT}`\n"
            f"• الاسم: **{BANKAK_NAME}**\n"
            f"• المبلغ: **{BANKAK_PRICE}**\n\n"
            "📸 **طريقة التفعيل:** قم بتحويل المبلغ ثم **أرسل صورة الإشعار هنا مباشرة داخل البوت** وسيتم التفعيل فوراً لمدة شهر كامل!\n\n"
            "2️⃣ **الدفع العالمي (نجوم تلجرام - Telegram Stars):**\n"
            f"• القيمة: **{STARS_PRICE} نجمة ⭐️** (تفعيل تلقائي مائة بالمائة)\n"
        )
        keyboard = [
            [InlineKeyboardButton(f"⭐ الدفع الفوري بالنجمات ({STARS_PRICE} ⭐️)", callback_data="pay_stars")],
            [InlineKeyboardButton("💬 التواصل المباشر مع الآدمن", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
        ]
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "pay_stars":
        await send_stars_invoice(update, context)

    elif data.startswith("dl_hd_"):
        url = data.replace("dl_hd_", "")
        if not is_vip_active(user_id):
            await query.message.reply_text(
                "🔒 **الجودة العالية مخصصة لمشتركي VIP فقط (أو انتهت فترة اشتراكك)!**\n\n"
                "اشترك الآن للاستفادة من الميزات بدون حدود مجانية.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        url = data.replace("dl_mp3_", "")
        if not is_vip_active(user_id):
            await query.message.reply_text(
                "🔒 **استخراج الصوت MP3 مخصص لمشتركي VIP فقط (أو انتهت فترة اشتراكك)!**\n\n"
                "اشترك الآن لفتح ميزة استخراج MP3 بنقرة واحدة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await download_audio(update, context, url)

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل الرئيسي ====================

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addvip", add_vip))
    app_bot.add_handler(CommandHandler("delvip", del_vip))
    
    app_bot.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app_bot.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل بنجاح...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()

    app_bot.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app_bot.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل بنجاح...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
