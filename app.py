import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import os
import urllib.parse

# --- הגדרות עסק ---
NAME = "אוהד - עיצוב שיער"
ADDRESS = "נחום שריג 33, באר שבע"
DB_FILE = "appointments.csv"

# פונקציה לקבלת השעה הנוכחית בישראל
def get_israel_time():
    return datetime.utcnow() + timedelta(hours=3)

# הגדרת שעות פעילות
def get_working_hours(selected_date):
    day = selected_date.weekday() # 6=ראשון, 4=שישי
    if day == 5: return None # שבת
    if day == 4: return (9, 15) # שישי
    return (9, 20) # א-ה

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["שם", "טלפון", "תאריך", "שעה", "סטטוס"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def generate_slots(selected_date):
    hours = get_working_hours(selected_date)
    if not hours: return []
    slots = []
    start, end = hours
    curr = datetime.combine(selected_date, time(start, 0))
    finish = datetime.combine(selected_date, time(end, 0))
    while curr < finish:
        slots.append(curr.strftime("%H:%M"))
        curr += timedelta(minutes=20)
    return slots

# --- עיצוב דף ---
st.set_page_config(page_title=NAME, page_icon="✂️")

st.markdown("""
<style>
    .main { background-color: #fdfdfd; }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        text-align: center;
        margin-bottom: 20px;
    }
    .waze-btn {
        background-color: #33ccff; color: white !important; padding: 12px 24px;
        text-decoration: none; border-radius: 30px; font-weight: bold;
        display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 10px;
    }
    .logo-container { text-align: center; padding: 10px 0; }
</style>
""", unsafe_allow_html=True)

# לוגו
st.markdown(f"""
<div class="logo-container">
    <svg width="100" height="100" viewBox="0 0 100 100" fill="black" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 10 L55 40 L45 40 Z M35 30 L45 45 L40 50 L30 35 Z M65 30 L55 45 L60 50 L70 35 Z" />
        <path d="M20 60 C 20 50, 45 50, 50 60 C 55 50, 80 50, 80 60 C 80 75, 60 70, 50 80 C 40 70, 20 75, 20 60" />
    </svg>
    <h1 style='margin-top: 0; font-family: serif; letter-spacing: 1px;'>{NAME}</h1>
</div>
""", unsafe_allow_html=True)

# כפתור WAZE
encoded_address = urllib.parse.quote(ADDRESS)
waze_url = f"https://waze.com/ul?q={encoded_address}&navigate=yes"
st.markdown(f"<div style='text-align: center;'><a href='{waze_url}' class='waze-btn'>🚙 נווט ב-Waze</a></div><br>", unsafe_allow_html=True)

df = load_data()
tab_client, tab_admin = st.tabs(["📅 הזמנת תור", "🔐 ניהול מספרה"])

# --- ממשק לקוח ---
with tab_client:
    now_il = get_israel_time()
    
    # בדיקה אם הלקוח הרגע הזמין תור כדי להציג לו הודעת הצלחה
    if 'last_booking' in st.session_state:
        b = st.session_state.last_booking
        st.markdown(f"""
            <div class="success-box">
                <h2>✅ התור הוזמן בהצלחה!</h2>
                <p>שם: <b>{b['name']}</b></p>
                <p>תאריך: <b>{b['date']}</b> | שעה: <b>{b['time']}</b></p>
                <p>אוהד מחכה לך בנחום שריג 33, באר שבע.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("לקביעת תור נוסף"):
            del st.session_state.last_booking
            st.rerun()
        st.balloons()
    else:
        st.markdown("<h4 style='text-align: center;'>בחר זמן לתספורת</h4>", unsafe_allow_html=True)
        d = st.date_input("תאריך", min_value=now_il.date())
        
        all_slots = generate_slots(d)
        booked = df[(df["תאריך"] == str(d)) & (df["סטטוס"].isin(["פעיל", "חסום"]))]["שעה"].tolist()
        available = [s for s in all_slots if s not in booked]
        
        # סינון שעות שעברו
        if d == now_il.date():
            current_time_str = now_il.strftime("%H:%M")
            available = [s for s in available if s > current_time_str]
        
        if not available:
            st.error("אין תורים פנויים לזמן שנבחר.")
        else:
            with st.form("book_form", clear_on_submit=True):
                c_name = st.text_input("שם מלא")
                c_phone = st.text_input("טלפון")
                c_slot = st.selectbox("שעה פנויה", available)
                submit = st.form_submit_button("אשר תור (לחץ פעם אחת)")
                
                if submit:
                    if c_name and c_phone:
                        # שמירה ל-CSV
                        new_row = pd.DataFrame([{"שם": c_name, "טלפון": c_phone, "תאריך": str(d), "שעה": c_slot, "סטטוס": "פעיל"}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        
                        # שמירת פרטי התור ב-Session State כדי להציג הודעת אישור
                        st.session_state.last_booking = {
                            "name": c_name,
                            "date": d.strftime("%d/%m/%Y"),
                            "time": c_slot
                        }
                        st.rerun()
                    else:
                        st.warning("בבקשה מלא את כל הפרטים.")

# --- ממשק ניהול (אוהד) ---
with tab_admin:
    pwd = st.text_input("סיסמת מנהל", type="password")
    if pwd == "1234":
        view_d = st.date_input("תאריך לניהול", value=get_israel_time().date())
        day_slots = df[df["תאריך"] == str(view_d)]
        
        st.subheader(f"תורים ליום {view_d.strftime('%d/%m/%Y')}")
        if not day_slots.empty:
            # תצוגה נקייה יותר של הטבלה
            display_df = day_slots[["שעה", "שם", "טלפון", "סטטוס"]].sort_values("שעה")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("אין תורים מוזמנים ליום זה.")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.write("🔒 חסימת שעה")
            h_to_block = st.selectbox("בחר שעה", generate_slots(view_d))
            if st.button("חסום שעה"):
                new_block = pd.DataFrame([{"שם": "חסום", "טלפון": "---", "תאריך": str(view_d), "שעה": h_to_block, "סטטוס": "חסום"}])
                df = pd.concat([df, new_block], ignore_index=True)
                save_data(df)
                st.rerun()
        with col2:
            st.write("🚫 סגירת יום")
            if st.button("סגור יום שלם"):
                all_day = generate_slots(view_d)
                new_blocks = pd.DataFrame([{"שם": "סגור", "טלפון": "---", "תאריך": str(view_d), "שעה": s, "סטטוס": "חסום"} for s in all_day])
                df = pd.concat([df, new_blocks], ignore_index=True)
                save_data(df)
                st.rerun()
        
        st.markdown("---")
        st.write("🗑️ ביטול תור / פתיחת חסימה")
        active = day_slots[day_slots["סטטוס"].isin(["פעיל", "חסום"])]
        if not active.empty:
            t_to_cancel = st.selectbox("בחר שעה לביטול", active["שעה"])
            if st.button("בטל תור/חסימה"):
                df.loc[(df["תאריך"] == str(view_d)) & (df["שעה"] == t_to_cancel), "סטטוס"] = "בוטל"
                save_data(df)
                st.rerun()
