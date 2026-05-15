import streamlit as st
import sqlite3
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. قاعدة البيانات ---
conn = sqlite3.connect('chat_app.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS messages (user TEXT, message TEXT, time TEXT, msg_type TEXT)')
conn.commit()

# --- 2. التحديث التلقائي (السر اللي بيخلي الرسايل تظهر عند الكل) ---
# التحديث كل ثانيتين عشان السرعة
st_autorefresh(interval=2000, key="datarefresh")

# --- 3. الدخول ---
if 'username' not in st.session_state:
    st.session_state.username = st.text_input("اسمك:")
    if st.button("دخول"): st.rerun()
    st.stop()

st.title(f"💬 واتساب {st.session_state.username}")

# --- 4. عرض الرسائل ---
messages = c.execute("SELECT user, message, time FROM messages ORDER BY ROWID ASC").fetchall()

# كود إشعار بسيط (Toast)
if 'count' not in st.session_state:
    st.session_state.count = len(messages)

if len(messages) > st.session_state.count:
    if messages[-1][0] != st.session_state.username:
        st.toast(f"📩 رسالة جديدة من {messages[-1][0]}")
    st.session_state.count = len(messages)

for m in messages:
    with st.chat_message("user" if m[0] == st.session_state.username else "assistant"):
        st.write(f"**{m[0]}:** {m[1]}  \n*🕒 {m[2]}*")

# --- 5. الإرسال ---
msg = st.chat_input("اكتب رسالتك...")
if msg:
    now = datetime.now().strftime("%I:%M %p")
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (st.session_state.username, msg, now, "text"))
    conn.commit()
    st.rerun()
