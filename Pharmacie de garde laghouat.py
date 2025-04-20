import logging
import os
import pandas as pd
from datetime import datetime, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# تهيئة نظام التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات البوت
TOKEN = '7531836319:AAH8dVoMQXxGas3FLLKOFjfkALByUVgoOxA'  # تأكد من إبقاء التوكن سريًا في المشاريع الحقيقية

# مسار ملف Excel داخل Replit (نفس المجلد)
EXCEL_FILE = 'pharmacies.xlsx'

# دالة لقراءة البيانات
def قراءة_البيانات(مسار_الملف: str, تاريخ_الاستعلام: date) -> pd.DataFrame:
    if not os.path.exists(مسار_الملف):
        logger.error(f"⚠️ الملف {مسار_الملف} غير موجود.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(مسار_الملف, engine='openpyxl')

        # معالجة أعمدة البيانات
        if 'الهاتف' in df.columns:
            df['الهاتف'] = df['الهاتف'].astype(str).str.strip().str.replace(r'\D', '', regex=True)

        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce').dt.date

        الأعمدة_المطلوبة = {'الاسم', 'العنوان', 'التاريخ'}
        if not الأعمدة_المطلوبة.issubset(df.columns):
            logger.error("📄 الملف لا يحتوي على الأعمدة المطلوبة")
            return pd.DataFrame()

        return df[df['التاريخ'] == تاريخ_الاستعلام]
    except Exception as e:
        logger.error(f"خطأ في قراءة الملف: {e}")
        return pd.DataFrame()


# دالة بدء البوت
async def بدء(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 صيدليات اليوم", callback_data="today")],
        [InlineKeyboardButton("🆘 المساعدة", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "مرحباً بك في بوت صيدليات المناوبة!\nاختر أحد الخيارات:",
        reply_markup=reply_markup
    )


# دالة المساعدة
async def مساعدة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 كيفية استخدام البوت:\n\n"
        "1. /start - عرض القائمة الرئيسية\n"
        "2. /monaweba [YYYY-MM-DD] - عرض الصيدليات المناوبة لتاريخ معين\n"
        "3. /help - عرض هذه الرسالة\n\n"
        "أو اضغط على الزر '📅 صيدليات اليوم' لعرض المناوبة اليومية."
    )
    if update.message:
        await update.message.reply_text(text)


# دالة المناوبة حسب التاريخ
async def مناوبة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ يرجى تحديد التاريخ\nمثال: /monaweba 2025-04-10")
        return

    try:
        تاريخ = datetime.strptime(context.args[0], "%Y-%m-%d").date()
        بيانات = قراءة_البيانات(EXCEL_FILE, تاريخ)

        if بيانات.empty:
            await update.message.reply_text(f"⚠️ لا توجد صيدليات مناوبة في تاريخ {context.args[0]}")
            return

        response = f"📅 الصيدليات المناوبة ليوم {context.args[0]}:\n\n"
        for _, row in بيانات.iterrows():
            response += (
                f"🏥 الاسم: {row['الاسم']}\n"
                f"📍 العنوان: {row['العنوان']}\n"
                f"📞 الهاتف: {row.get('الهاتف', 'غير متوفر')}\n"
                f"{'-' * 30}\n"
            )
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("⛔ تنسيق التاريخ غير صحيح. استخدم YYYY-MM-DD")


# دالة الزر
async def معالجة_الزر(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "today":
        today = date.today()
        بيانات = قراءة_البيانات(EXCEL_FILE, today)

        if بيانات.empty:
            await query.edit_message_text("⚠️ لا توجد صيدليات مناوبة اليوم")
            return

        response = f"📅 الصيدليات المناوبة ليوم {today.strftime('%Y-%m-%d')}:\n\n"
        for _, row in بيانات.iterrows():
            response += (
                f"🏥 الاسم: {row['الاسم']}\n"
                f"📍 العنوان: {row['العنوان']}\n"
                f"📞 الهاتف: {row.get('الهاتف', 'غير متوفر')}\n"
                f"{'-' * 30}\n"
            )
        await query.edit_message_text(response)
    elif query.data == "help":
        await مساعدة(update, context)


# دالة الخطأ
async def خطأ(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}", exc_info=True)
    if hasattr(update, "message") and update.message:
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")


# تشغيل البوت
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", بدء))
    application.add_handler(CommandHandler("monaweba", مناوبة))
    application.add_handler(CommandHandler("help", مساعدة))
    application.add_handler(CallbackQueryHandler(معالجة_الزر))
    application.add_error_handler(خطأ)

    logger.info("✅ البوت يعمل الآن...")
    application.run_polling()


if __name__ == '__main__':
    main()
