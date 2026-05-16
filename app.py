import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. إعدادات الصفحة والمنطقة الزمنية
st.set_page_config(page_title="WhatsApp Pro AI", page_icon="💬", layout="wide")
egypt_tz = pytz.timezone('Africa/Cairo')

# تحديث الصفحة كل ثانية ونصف لتلقي الجديد فوراً
st_autorefresh(interval=1500, key="chat_refresh")

# حقن كود CSS لتغيير الألوان وتصميم الـ UI ليشبه الواتساب الحقيقي
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #efeae2; /* لون خلفية شات الواتساب الشهيرة */
    }
    [data-testid="stSidebar"] {
        background-color: #111b21 !important; /* لون شريط الواتساب الغامق */
    }
    .main-header {
        background-color: #008069; /* أخضر واتساب */
        padding: 15px;
        color: white;
        font-size: 22px;
        font-weight: bold;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .msg-container {
        display: flex;
        flex-direction: column;
        margin: 10px 0;
    }
    .msg-box-sent {
        background-color: #d9fdd3; /* لون رسالتي */
        color: #111b21;
        align-self: flex-end;
        padding: 10px 15px;
        border-radius: 10px 0px 10px 10px;
        max-width: 60%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    .msg-box-recv {
        background-color: #ffffff; /* لون رسالة الطرف الآخر */
        color: #111b21;
        align-self: flex-start;
        padding: 10px 15px;
        border-radius: 0px 10px 10px 10px;
        max-width: 60%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    .time-text {
        font-size: 10px;
        color: #667781;
        text-align: right;
        margin-top: 5px;
    }
    .user-label {
        font-size: 11px;
        color: #008069;
        font-weight: bold;
        margin-bottom: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. إنشاء الاتصال بالداتابيز وتطوير الجداول
conn = sqlite3.connect("whatsapp_pro.db", check_same_thread=False)
c = conn.cursor()

# جدول المستخدمين والمسؤولين
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    is_admin INTEGER DEFAULT 0
)
""")
# إضافة مستخدمين افتراضيين لو الجدول فاضي
c.execute("INSERT OR IGNORE INTO users VALUES ('عبد الرحمن', 1)")
c.execute("INSERT OR IGNORE INTO users VALUES ('أحمد', 0)")
c.execute("INSERT OR IGNORE INTO users VALUES ('محمد', 0)")

# جدول الرسائل الجديد (يدعم الشاتات المختلفة وميزة تم القراءة)
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    time TEXT,
    is_read INTEGER DEFAULT 0
)
""")
conn.commit()

# 3. نظام تسجيل الدخول البسيط
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.username:
    st.markdown("<div class='main-header'>تسجيل الدخول إلى WhatsApp Pro</div>", unsafe_allow_html=True)
    user_input = st.selectbox("اختر اسمك للدخول:", ["", "عبد الرحمن", "أحمد", "محمد"])
    if user_input:
        st.session_state.username = user_input
        # التحقق هل هو أدمن؟
        admin_check = c.execute("SELECT is_admin FROM users WHERE username=?", (user_input,)).fetchone()
        st.session_state.is_admin = bool(admin_check[0]) if admin_check else False
        st.rerun()
    st.stop()
# 4. الشريط الجانبي (Sidebar) - قايمة الشاتات والتحكم
with st.sidebar:
    st.markdown(f"<h3 style='color:white;'>مرحباً، {st.session_state.username} 💬</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#222c32;'>", unsafe_allow_html=True)
