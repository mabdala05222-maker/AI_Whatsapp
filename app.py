import streamlit as st
import sqlite3
import pytz
import os
import hashlib
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder

# --- 1. الإعدادات وقاعدة البيانات ---
if not os.path.exists("media"):
    os.makedirs("media")

conn = sqlite3.connect('chat_app.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS messages 
             (user TEXT, message TEXT, time TEXT, msg_type TEXT)''')
conn.commit()

# --- 2. تهيئة الصفحة والستايل ---
st.set_page_config(page_title="WhatsApp Pro", page_icon="💬", layout="centered")

# التحديث التلقائي (السر في ظهور الرسائل عند الطرفين)
st_autorefresh(interval=1000, key="chatupdate")

st.markdown("""
    <style>
    .stChatMessage { background-color: #e4f2fe; border-radius: 15px; padding: 10px; margin: 5px 0; }
    .stTextInput { border-radius: 20px; }
    .stFileUploader section { padding: 0; }
    </style>
    <script>
    function notifyMe(user, message) {
        if (Notification.permission === "granted") {
            new Notification(user, { body: message, icon: "https://cdn-icons-png.flaticon.com/512/733/733585.png" });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    }
    </script>
    """, unsafe_allow_html=True)

# --- 3. نظام تسجيل الدخول ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔒  المحادثات")
    with st.container():
        pwd = st.text_input("كلمة السر:", type="password")
        user = st.text_input("اسمك:")
        if st.button("دخول"):
            if pwd in ["123", "admin99"]:
                st.session_state.authenticated = True
                st.session_state.username = user
                st.session_state.is_admin = (pwd == "admin99")
                st.rerun()
            else:
                st.error("خطأ!")
    st.stop()

# --- 4. عرض الرسائل والإشعارات ---
st.title(f"💬 مرحباً {st.session_state.username}")

if st.session_state.is_admin:
    if st.sidebar.button("🗑️ مسح الشات"):
        c.execute("DELETE FROM messages")
        conn.commit()
        st.rerun()

# 1. جلب الرسائل (نضيف السطر ده عشان نضمن إنه مش بيقرأ من الكاش)
c.execute("SELECT user, message, time, msg_type FROM messages ORDER BY ROWID ASC")
messages = c.fetchall()

# 2. منطق الإشعارات (تعديل بسيط عشان التزامن)
if 'last_count' not in st.session_state:
    st.session_state.last_count = len(messages)

# التحقق من وجود رسائل جديدة
if len(messages) > st.session_state.last_count:
    last_m = messages[-1]
    # لو الرسالة مش بتاعتي، طلع الإشعار
    if last_m[0] != st.session_state.username:
        st.toast(f"📩 رسالة جديدة من {last_m[0]}")
        # دي عشان الإشعار يظهر في المتصفح حتى لو إنت مش باصص عليه
        components.html(f"<script>window.parent.notifyMe('{last_m[0]}', '{last_m[1] if last_m[3]=='text' else 'مرفق جديد'}')</script>", height=0)
    
    # تحديث العداد فوراً
    st.session_state.last_count = len(messages)

# عرض كل الرسائل (نص، صور، فيديو، صوت)
for m in messages:
    with st.chat_message("user" if m[0] == st.session_state.username else "assistant"):
        st.write(f"**{m[0]}**")
        if m[3] == "text": st.write(m[1])
        elif m[3] == "image": st.image(m[1])
        elif m[3] == "video": st.video(m[1])
        elif m[3] == "audio": st.audio(m[1])
        st.caption(f"🕒 {m[2]}")

# --- 5. منطقة الإرسال المطورة ---
st.markdown("---")
col_file, col_main, col_voice = st.columns([0.8, 4, 0.8])

with col_file:
    up_file = st.file_uploader("📎", type=["png", "jpg", "jpeg", "mp4"], label_visibility="collapsed")

with col_main:
    with st.form("my_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns([4, 1])
        with f_col1:
            txt_input = st.text_input("", placeholder="اكتب هنا...", label_visibility="collapsed")
        with f_col2:
            btn_send = st.form_submit_button("🚀")

with col_voice:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="✅", key='mic')

# --- 6. معالجة الإرسال ---
# تحديد المنطقة الزمنية للقاهرة
egypt_tz = pytz.timezone('Africa/Cairo')
# تجيب الوقت الحالي في القاهرة وتنسقه
now = datetime.now(egypt_tz).strftime("%I:%M %p")

# إرسال النص
if btn_send and txt_input:
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (st.session_state.username, txt_input, now, "text"))
    conn.commit()
    st.rerun()

# إرسال الصور والفيديوهات
if up_file:
    f_bytes = up_file.getvalue()
    f_hash = hashlib.md5(f_bytes).hexdigest()
    if 'l_f_h' not in st.session_state or st.session_state.l_f_h != f_hash:
        f_path = os.path.join("media", f"{f_hash}_{up_file.name}")
        with open(f_path, "wb") as f: f.write(f_bytes)
        m_t = "video" if up_file.name.lower().endswith("mp4") else "image"
        c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (st.session_state.username, f_path, now, m_t))
        conn.commit()
        st.session_state.l_f_h = f_hash
        st.rerun()

# إرسال التسجيل الصوتي
if audio:
    a_hash = hashlib.md5(audio['bytes']).hexdigest()
    if 'l_a_h' not in st.session_state or st.session_state.l_a_h != a_hash:
        a_path = os.path.join("media", f"v_{a_hash}.wav")
        with open(a_path, "wb") as f: f.write(audio['bytes'])
        c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (st.session_state.username, a_path, now, "audio"))
        conn.commit()
        st.session_state.l_a_h = a_hash
        st.rerun()
