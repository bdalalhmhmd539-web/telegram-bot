
import os
import json
import yt_dlp
import asyncio
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
ADMIN_ID = 8328994103  # آيدي الأدمن لتلقي الإشعارات

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

STARS_PRICE = 50  # سعر الاشتراك بنجوم تلجرام

# ==================== إدارة بيانات الـ VIP (حفظ واسترجاع) ====================
VIP_FILE = "vip_users.json"

def load_vip_users() -> set:
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception:
            return set()
    return set()

def save_vip_users(vip_set: set):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump(list(vip_set), f, indent=4)

VIP_USERS = load_vip_users()

# ==================== الأوامر والرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, YouTube, Facebook, Instagram...) وسأقوم بتحميله لك فوراً.\n\n"
        "⚡ **النسخة المجانية:** تنزيل تلقائي بالجودة العادية (حتى 30 ميجابايت).\n"
        "👑 **عضوية VIP:** تنزيل بأعلى جودة HD بدون حدود، واستخراج MP3!"
    )
    
    keyboard = [
        [InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")],
        [InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر خاص بالآدمن لترقية المستخدمين لـ VIP يدويين"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمدير البوت فقط.")
        return

    try:
        new_vip_id = int(context.args[0])
        VIP_USERS.add(new_vip_id)
        save_vip_users(VIP_USERS)
        
        await update.message.reply_text(f"✅ تم ترقية المستخدم `{new_vip_id}` إلى قائمة VIP وحفظ البيانات بنجاح! 👑", parse_mode="Markdown")
        
        # إشعار العميل تلقائياً عند التفعيل
        try:
            await context.bot.send_message(
                chat_id=new_vip_id,
                text="🎉 **تهانينا! تم تفعيل اشتراك VIP بحسابك بنجاح.**\nيمكنك الآن التحميل بجودة HD واستخراج MP3 بدون حدود!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\nأرسل الأمر متبوعاً بآيدي المشترك هكذا:\n`/addvip 123456789`", parse_mode="Markdown")


async def del_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر خاص بالآدمن لإلغاء ترقية VIP"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    try:
        remove_id = int(context.args[0])
        if remove_id in VIP_USERS:
            VIP_USERS.remove(remove_id)
            save_vip_users(VIP_USERS)
            await update.message.reply_text(f"✅ تم إزالة المستخدم `{remove_id}` من VIP بنجاح.")
        else:
            await update.message.reply_text("⚠️ المستخدم غير موجود في قائمة VIP.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\n`/delvip 123456789`", parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال صورة إشعار بنكك وإرسالها للآدمن مع الآيدي"""
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    # 1. إرسال الصورة والمعلومات إلى الأدمن
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=(
                f"🔔 **إشعار دفع جديد (بنكك)!**\n\n"
                f"👤 **المستخدم:** {user.first_name} (@{user.username if user.username else 'لا يوجد'})\n"
                f"🆔 **الآيدي:** `{user.id}`\n\n"
                f"⚡ **لتفعيل المشترك اضغط على الأمر للنسخ:**\n"
                f"`/addvip {user.id}`"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending photo to admin: {e}")

    # 2. رد على العميل لتأكيد الاستلام
    await update.message.reply_text(
        "✅ **تم استلام صورة الإشعار بنجاح!**\n\n"
        "جاري مراجعة الإشعار من قبل الإدارة وسوف يتم تفعيل حسابك كـ VIP في أقرب وقت ممكن. 👑",
        parse_mode="Markdown"
    )

# ==================== نظام الدفع عبر Telegram Stars ====================

async def send_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال فاتورة النجوم للعميل"""
    query = update.callback_query
    chat_id = query.message.chat_id
    
    title = "اشتراك VIP المميز 👑"
    description = "التحميل بأعلى جودة HD وبدون حدود + استخراج الصوت MP3"
    payload = "vip_subscription_stars"
    currency = "XTR"  # رمز نجوم تلجرام
    prices = [LabeledPrice("اشتراك VIP", STARS_PRICE)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # فارغ لنجوم تلجرام
        currency=currency,
        prices=prices
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الموافقة المبدئية على العملية قبل الخصم"""
    query = update.pre_checkout_query
    if query.invoice_payload != "vip_subscription_stars":
        await query.answer(ok=False, error_message="حدث خطأ أثناء المعالجة.")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة التفعيل التلقائي بعد نجاح دفع النجمات"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # ترقية المستخدم وتخزينه تلقائياً
    VIP_USERS.add(user_id)
    save_vip_users(VIP_USERS)

    await update.message.reply_text(
        "🎉 **تم الدفع بنجاح عبر نجوم تلجرام!**\n\n"
        "تم ترقية حسابك إلى **VIP** تلقائياً! يمكنك الآن التحميل بأعلى جودة HD واستخراج MP3 بدون أي حدود. 👑",
        parse_mode="Markdown"
    )

    # إشعار الأدمن بعملية الشراء الناتجة
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💰 **شراء VIP تلقائي بنجاح (Telegram Stars)!**\n\n"
                f"👤 **المستخدم:** {user_name}\n"
                f"🆔 **الآيدي:** `{user_id}`\n"
                f"⭐ **المبلغ:** {STARS_PRICE} نجمة"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notifying admin: {e}")

# ==================== التنزيل والمعالجة ====================

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, is_hd: bool = False):
    user_id = update.effective_user.id
    
    if update.message:
        msg = await update.message.reply_text("🔍 جاري التحميل والمعالجة...")
    else:
        msg = await update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة HD...")

    keyboard = [
        [
            InlineKeyboardButton("🎵 استخراج الصوت MP3 🔒", callback_data=f"dl_mp3_{url}"),
            InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD 🔒", callback_data=f"dl_hd_{url}")
        ],
        [InlineKeyboardButton("💳 ترقية لحساب VIP (بدون حدود)", callback_data="vip_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    format_setting = 'best' if is_hd else 'best[filesize<=30M]/worst'

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

        await msg.edit_text("📤 جاري رفع الفيديو إليك الآن...")

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح {'(بجودة عالية HD 👑)' if is_hd else ''}!\n\n💡 *اشترك في VIP للحصول على جودة HD واستخراج الصوت.*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(
            "⚠️ **تعذر تنزيل الفيديو!**\n\n"
            "قد يكون حجم الفيديو كبيراً جداً على السيرفر المجاني.\n"
            "للتحميل بدون حدود وبأعلى جودة، اشترك في VIP:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الترقية لـ VIP الآن", callback_data="vip_info")]])
        )


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
            "👑 **مميزات العضوية الممتازة (VIP):**\n"
            "• تنزيل الفيديوهات بأعلى دقة HD بدون حدود للحجم.\n"
            "• تحويل أي فيديو إلى مقطع صوتي MP3 بنقرة زر.\n"
            "• أولوية وسرعة فائقة في المعالجة.\n\n"
            "------------------------------\n"
            "💳 **طرق الدفع المتاحة:**\n\n"
            "1️⃣ **الدفع المحلي (بنكك - Bankak):**\n"
            f"• رقم الحساب: `{BANKAK_ACCOUNT}`\n"
            f"• الاسم: **{BANKAK_NAME}**\n"
            f"• المبلغ: **{BANKAK_PRICE}**\n\n"
            "📸 **طريقة التفعيل:** قم بتحويل المبلغ ثم **أرسل صورة الإشعار هنا مباشرة داخل البوت** وسيتم التفعيل فوراً!\n\n"
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
        if user_id not in VIP_USERS:
            await query.message.reply_text(
                "🔒 **الجودة العالية HD مخصصة لمشتركي VIP فقط!**\n\n"
                "اشترك الآن للاستفادة من التنزيل بأعلى جودة وبدون حدود للحجم.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        if user_id not in VIP_USERS:
            await query.message.reply_text(
                "🔒 **استخراج الصوت MP3 مخصص لمشتركي VIP فقط!**\n\n"
                "اشترك الآن لفتح ميزة استخراج MP3 بنقرة واحدة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            await query.message.reply_text("🎧 جاري استخراج الصوت MP3 لمشتركي VIP...")

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل الرئيسي ====================

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # الأوامر الأساسية
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addvip", add_vip))
    app_bot.add_handler(CommandHandler("delvip", del_vip))
    
    # معالجة الشراء الفوري عبر النجمات
    app_bot.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app_bot.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # معالج الصور (لإشعار بنكك)
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # معالج النصوص (الروابط)
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأزرار
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل بنجاح...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
