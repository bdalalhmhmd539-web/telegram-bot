import os
import yt_dlp
import asyncio
from aiohttp import web
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ==================== إعدادات الإدارة والدفع ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_USERNAME = "@bdalalhm"
ADMIN_ID = 7752459  # آيدي المدير لترقية المستخدمين

BANKAK_ACCOUNT = "7752459"
BANKAK_NAME = "محمد عبد الإله"
BANKAK_PRICE = "2000 جنيه سوداني"

VIP_USERS = set()

# ==================== خادم ويب مصغر لإرضاء Render ====================
async def handle_ping(request):
    return web.Response(text="Bot is running perfectly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server running on port {port}")

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
    """أمر خاص بالآدمن لترقية المستخدمين لـ VIP"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمدير البوت فقط.")
        return

    try:
        new_vip_id = int(context.args[0])
        VIP_USERS.add(new_vip_id)
        await update.message.reply_text(f"✅ تم ترقية المستخدم `{new_vip_id}` إلى قائمة VIP بنجاح! 👑", parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ **طريقة الاستخدام:**\nأرسل الأمر متبوعاً بآيدي المشترك هكذا:\n`/addvip 123456789`", parse_mode="Markdown")


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

        # تشغيل yt_dlp بطريقة غير معطلة (Non-blocking)
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
        await update.message.reply_text("❌ يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https.")
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

    elif data == "pay_stars":
        await query.message.reply_text(f"🚨 لتفعيل VIP عن طريق Telegram Stars، تواصل مباشرة مع الإدارة: {ADMIN_USERNAME}")

    elif data == "close_menu":
        await query.message.delete()

# ==================== التشغيل الرئيسي ====================

async def post_init(application):
    # تشغيل خادم الويب عند بدء البوت بشكل آمن
    await start_web_server()

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app_bot = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # تسجيل الأوامر
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addvip", add_vip))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت يعمل بنجاح...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()

