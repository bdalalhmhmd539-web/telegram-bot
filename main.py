import os
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
    CallbackContext
)

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا_إذا_لم_تستخدم_Variables")
ADMIN_USERNAME = "@bdalalhm" # يوزر الآدمن للاستفسارات والإشعارات

# بيانات الدفع المحلي (بنكك)
BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

# قائمة آيديهات المشتركين في VIP (مثال: {123456789, 987654321})
VIP_USERS = set()

# ==================== الأوامر والرسائل ====================

def start(update: Update, context: CallbackContext):
    """رسالة البداية والترحيب"""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, YouTube, Facebook, Instagram...) وسأقوم بتحميله لك فوراً.\n\n"
        "⚡ **النسخة المجانية:** تنزيل تلقائي بالجودة العادية (حتى 50 ميجابايت).\n"
        "👑 **عضوية VIP:** تنزيل بأعلى جودة HD بدون حدود، واستخراج MP3!"
    )
    
    keyboard = [
        [InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")],
        [InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


def download_and_send(update: Update, context: CallbackContext, url: str, is_hd: bool = False):
    """دالة عامة لتحميل وإرسال الفيديو بناءً على الجودة"""
    user_id = update.effective_user.id
    
    # تحديد رسالة الانتظار
    if update.message:
        msg = update.message.reply_text("🔍 جاري التحميل والمعالجة...")
    else:
        msg = update.callback_query.message.reply_text("🔍 جاري التحميل بأعلى جودة HD...")

    # خيارات الأزرار التفاعلية أسفل الفيديو
    keyboard = [
        [
            InlineKeyboardButton("🎵 استخراج الصوت MP3 🔒", callback_data=f"dl_mp3_{url}"),
            InlineKeyboardButton("⚡ تنزيل بأعلى دقة HD 🔒", callback_data=f"dl_hd_{url}")
        ],
        [InlineKeyboardButton("💳 ترقية لحساب VIP (بدون حدود)", callback_data="vip_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # تحديد خيارات التحميل بحسب الجودة
    if is_hd:
        format_setting = 'best' # أعلى جودة ممكنة بدون حدود
    else:
        format_setting = 'best[filesize<=50M]/best' # جودة متوازنة بحجم أقضاه 50 ميجا

    try:
        ydl_opts = {
            'format': format_setting,
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        msg.edit_text("📤 جاري رفع الفيديو إليك الآن...")

        with open(filename, 'rb') as video_file:
            context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح {'(بجودة عالية HD 👑)' if is_hd else ''}!\n\n💡 *اشترك في VIP للحصول على جودة HD واستخراج الصوت.*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        # حذف الملف بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)
        msg.delete()

    except Exception as e:
        msg.edit_text(
            "⚠️ **تعذر تنزيل الفيديو بهذه الجودة!**\n\n"
            "قد يكون حجم الفيديو كبيراً جداً للمستخدمين المجانيين.\n"
            "للتحميل بدون حدود وبأعلى جودة، اشترك في VIP:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الترقية لـ VIP الآن", callback_data="vip_info")]])
        )


def handle_message(update: Update, context: CallbackContext):
    """عند إرسال رابط عادي من قبل المستخدم"""
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        update.message.reply_text("❌ يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https.")
        return

    # التنزيل التلقائي المباشر بالجودة العادية
    download_and_send(update, context, url, is_hd=False)


def button_callback(update: Update, context: CallbackContext):
    """معالجة الأزرار التفاعلية"""
    query = update.callback_query
    query.answer()
    
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
            f"• المبلغ: **{BANKAK_PRICE}**\n"
            f"*(بعد التحويل أرسل صورة الإشعار للآدمن {ADMIN_USERNAME} لترقية حسابك فوراً)*\n\n"
            "2️⃣ **الدفع العالمي (نجوم تلجرام - Telegram Stars):**\n"
            "• القيمة: **50 نجمة ⭐️**\n"
        )
        keyboard = [
            [InlineKeyboardButton("⭐ الدفع عبر Telegram Stars (50 ⭐️)", callback_data="pay_stars")],
            [InlineKeyboardButton("📩 إرسال إشعار بنك للآدمن", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="close_menu")]
        ]
        query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("dl_hd_"):
        url = data.replace("dl_hd_", "")
        # فحص هل المستخدم VIP
        if user_id not in VIP_USERS:
            query.message.reply_text(
                "🔒 **الجودة العالية HD مخصصة لمشتركي VIP فقط!**\n\n"
                "اشترك الآن للاستفادة من التنزيل بأعلى جودة وبدون حدود للحجم.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            # تنزيل بجودة HD للمشتركين
            download_and_send(update, context, url, is_hd=True)

    elif data.startswith("dl_mp3_"):
        if user_id not in VIP_USERS:
            query.message.reply_text(
                "🔒 **استخراج الصوت MP3 مخصص لمشتركي VIP فقط!**\n\n"
                "اشترك الآن لفتح ميزة استخراج MP3 بنقرة واحدة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب لـ VIP", callback_data="vip_info")]])
            )
        else:
            query.message.reply_text("🎧 جاري استخراج الصوت MP3 لمشتركي VIP...")

    elif data == "pay_stars":
        query.message.reply_text(
            f"🚨 لتفعيل VIP عن طريق Telegram Stars، تواصل مباشرة مع الإدارة: {ADMIN_USERNAME}"
        )

    elif data == "close_menu":
        query.message.delete()

# ==================== التشغيل الرئيسي ====================

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل بنجاح...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

