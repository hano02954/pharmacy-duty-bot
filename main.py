import logging
import os
import pandas as pd
from datetime import datetime, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask
from threading import Thread

# إعدادات السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت
TOKEN = "7531836319:AAH8dVoMQXxGas3FLLKOFjfkALByUVgoOxA"  # تأكد من أن التوكن صحيح

# اسم ملف Excel
EXCEL_FILE = "pharmacies.xlsx"

# قراءة البيانات من الملف
def قراءة_البيانات(المسار: str, تاريخ_اليوم: date) -> pd.DataFrame:
    if not os.path.exists(المسار):
        logger.error(f"الملف {المسار} غير موجود")
        return pd.DataFrame()

    try:
        df = pd.read_excel(المسار, engine="openpyxl")
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce').dt.date

        # معالجة رقم الهاتف إن وجد
        if 'الهاتف' in df.columns:
            df['الهاتف'] = df['الهاتف'].astype(str).str.strip()

        return df[df['التاريخ'] == تاريخ_اليوم]
    except Exception as e:
        logger.error(f"خطأ أثناء قراءة الملف: {e}")
        return pd.DataFrame()

# أمر /start
async def بدء(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📥 أمر /start وصل")  # لتأكيد وصول الأمر
    keyboard = [
        [InlineKeyboardButton("📅 صيدليات اليوم", callback_data="today")],
        [InlineKeyboardButton("🆘 المساعدة", callback_data="help")]
    ]
    await update.message.reply_text(
        "مرحباً بك في بوت صيدليات المناوبة!\nاختر أحد الخيارات:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# زر المساعدة
async def مساعدة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 كيفية الاستخدام:\n"
        "/start - عرض القائمة الرئيسية\n"
        "/monaweba YYYY-MM-DD - عرض صيدليات حسب التاريخ\n"
        "/help - المساعدة"
    )

# أمر حسب التاريخ
async def مناوبة(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("يرجى كتابة التاريخ هكذا: /monaweba 2025-04-12")
        return

    try:
        التاريخ = datetime.strptime(context.args[0], "%Y-%m-%d").date()
        بيانات = قراءة_البيانات(EXCEL_FILE, التاريخ)

        if بيانات.empty:
            await update.message.reply_text("❌ لا توجد صيدليات مناوبة في هذا التاريخ.")
            return

        نص = f"📅 صيدليات المناوبة ليوم {التاريخ}:\n\n"
        for _, row in بيانات.iterrows():
            نص += (
                f"🏥 {row['الاسم']}\n"
                f"📍 {row['العنوان']}\n"
                f"📞 {row.get('الهاتف', 'غير متوفر')}\n"
                f"{'-'*30}\n"
            )
        await update.message.reply_text(نص)
    except ValueError:
        await update.message.reply_text("⚠️ التاريخ غير صحيح. الصيغة: YYYY-MM-DD")

# معالجة الأزرار
async def معالجة_الزر(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "today":
        اليوم = date.today()
        بيانات = قراءة_البيانات(EXCEL_FILE, اليوم)

        if بيانات.empty:
            await query.edit_message_text("❌ لا توجد صيدليات مناوبة اليوم.")
            return

        نص = f"📅 صيدليات المناوبة ليوم {اليوم}:\n\n"
        for _, row in بيانات.iterrows():
            نص += (
                f"🏥 {row['الاسم']}\n"
                f"📍 {row['العنوان']}\n"
                f"📞 {row.get('الهاتف', 'غير متوفر')}\n"
                f"{'-'*30}\n"
            )
        await query.edit_message_text(نص)

    elif query.data == "help":
        await query.edit_message_text(
            "🆘 كيفية الاستخدام:\n"
            "/start - عرض القائمة الرئيسية\n"
            "/monaweba YYYY-MM-DD - عرض صيدليات حسب التاريخ\n"
            "/help - المساعدة"
        )

# في حال حدوث خطأ
async def خطأ(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"خطأ: {context.error}", exc_info=True)

# تشغيل Flask
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال 😎"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# دالة التشغيل
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", بدء))
    app.add_handler(CommandHandler("help", مساعدة))
    app.add_handler(CommandHandler("monaweba", مناوبة))
    app.add_handler(CallbackQueryHandler(معالجة_الزر))
    app.add_error_handler(خطأ)

    logger.info("✅ البوت يعمل...")
    keep_alive()  # لتشغيل Flask وتحميل البوت دائمًا
    app.run_polling()

if __name__ == "__main__":
    main()
