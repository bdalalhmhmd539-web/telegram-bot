import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ==================== الإعدادات الثابتة ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا_إذا_لم_تستخدم_Variables")
ADMIN_USERNAME = "@bdalalhm" # يوزر الآدمن للاستفسارات والإشعارات

# بيانات الدفع المحلي (بنكك)
BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

# قائمة المستخدمين المشتركين في VIP (في إنتاج حقيقي يُفضل ربطها بـ Database)
VIP_USERS = set()

# ==================== الأوامر والرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة البداية والترحيب"""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت تنزيل الفيديوهات السريع! 🚀\n\n"
        "🎬 **كيفية الاستخدام:**\n"
        "أرسل لي رابط فيديو من (TikTok, YouTube, Facebook, Instagram...) وسأقوم بتحميله لك فوراً.\n\n"
        "⚡ **النسخة المجانية:** حدود التنزيل للملفات حتى 50 ميجابايت.\n"
        "👑 **عضوية VIP:** تنزيل مفتوح الحجم، استخراج الصوت MP3، وسرعة فائقة!"
    )
    
    keyboard = [
        [InlineKeyboardButton("👑 الاشتراك في VIP", callback_data="vip_info")],
        [InlineKeyboardButton("💬 الدعم والمساعدة", url=f"https://t.me/{ADMIN_USERNAME.replace('@', '')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الروابط المرسلة من المستخدم"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https.")
        return

    msg = await update.message.reply_text("🔍 جاري فحص الرابط ومعالجة الفيديو...")
    
    # خيارات الواجهة التفاعلية أسفل كل فيديو
    keyboard = [
        [
            InlineKeyboardButton("🎵 استخراج الصوت MP3 🔒", callback_data="vip_feature_audio"),
            InlineKeyboardButton("⚡ تنزيل بأعلى دقة VIP 🔒", callback_data="vip_feature_hd")
        ],
        [InlineKeyboardButton("💳 ترقية لحساب VIP (بدون حدود)", callback_data="vip_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # إعدادات yt-dlp للتحميل المجاني (محدد بحجم 50 ميجابايت)
        ydl_opts = {
            'format': 'best[filesize<=50M]/best',
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)

        await msg.edit_text("📤 جاري رفع الفيديو إليك الآن...")

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ تم التنزيل بنجاح!\n\n💡 *اشترك في VIP للحصول على سرعة مضاعفة واستخراج الصوت.*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        # مسح الملف من السيرفر فوراً لحفظ المساحة
        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(
            "⚠️ **تعذر تنزيل الفيديو بالنظام المجاني!**\n\n"
            "قد يكون حجم الفيديو أكبر من **50 ميجابايت** أو يتطلب صلاحيات VIP.\n"
            "اضغط على الزر أدناه للترقية وتحميل المقاطع الكبيرة بدون قيود:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 الترقية لـ VIP الآن", callback_data="vip_info")]])
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغط الأزرار للتفاعل والتنبيهات"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id

    if data == "vip_info":
        vip_text = (
            "👑 **مميزات العضوية الممتازة (VIP):**\n"
            "• تنزيل الفيديوهات والأفلام الكبيرة بدون حدود 50MB.\n"
            "• تحويل أي فيديو إلى مقطع صوتي MP3 بنقرة زر.\n"
            "• أولوية وسرعة فائقة في معالجة السيرفر.\n\n"
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
        await query.message.reply_text(vip_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data in ["vip_feature_audio", "vip_feature_hd"]:
        if user_id not in VIP_USERS:
            await query.message.reply_text(
                "🔒 **هذه الميزة مخصصة لمشتركي VIP فقط!**\n\n"
                "اشترك الآن للاستفادة من استخراج الصوت والتنزيل الفائق الدقة.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 ترقية الحساب الآن", callback_data="vip_info")]])
            )
        else:
            await query.message.reply_text("✅ جارٍ معالجة طلبك كعضو VIP...")

    elif data == "pay_stars":
        await query.message.reply_text(
            f"🚨 لتفعيل VIP عن طريق Telegram Stars أو لمساعدتك فوراً، تواصل مباشرة مع الإدارة: {ADMIN_USERNAME}"
        )

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل الرئيسي ====================

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # بناء البوت
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # تسجيل الأوامر والروابط
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == "__main__":
    main()
