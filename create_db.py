import sqlite3

# إنشاء الاتصال بقاعدة البيانات (سيتم إنشاء الملف إذا لم يكن موجودًا)
conn = sqlite3.connect("pharmacies.db")
cursor = conn.cursor()

# إنشاء جدول الصيدليات
cursor.execute("""
CREATE TABLE IF NOT EXISTS pharmacies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    date TEXT NOT NULL
)
""")

# بيانات تجريبية للإدخال
pharmacies = [
    ("صيدلية الشفاء", "حي 500 سكن", "0555 11 22 33", "2025-04-10"),
    ("صيدلية الرحمة", "حي المستقبل", "0666 77 88 99", "2025-04-10"),
    ("صيدلية الإيمان", "وسط المدينة", "0777 00 11 22", "2025-04-11")
]

# إدخال البيانات
cursor.executemany("INSERT INTO pharmacies (name, address, phone, date) VALUES (?, ?, ?, ?)", pharmacies)

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات وإضافة البيانات بنجاح.")
