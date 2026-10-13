import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="مستشفى الشوملي العام - بوابة الأقسام", page_icon="🏥", layout="wide")

def get_db_connection():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="Shomali2026@DB",
        host="db.cstiwpxcnffccttsqrzy.supabase.co",
        port="5432"
    )
    return conn

SUB_PORTALS_LIST = [
    "الصيدلية الداخلية", "الصيدلية الاستشاريه", "صيدلية الطوارئ",
    "الصيدلية الخارجية الخافرة", "الداخلية الخافرة", "الجناح العام الرجالي",
    "الجناح العام النسائي", "جناح الاطفال", "الخدج", "صالة الولادة",
    "صاله العمليات / الجناح الخاص", "الاسنان", "الاشعة", "السونار",
    "الطوارئ العامه", "الاسعاف الفوري", "الخدمات", "المختبرات",
    "الوبائيه", "لوكرات الصدمة", "الجناح الخاص", "العمليات"
]

st.title("🏥 مستشفى الشوملي العام - بوابة الأقسام والمسؤولين")
st.markdown("---")

selected_portal = st.sidebar.selectbox("اختر بوابتك / القسم:", SUB_PORTALS_LIST)
portal_pass = st.sidebar.text_input("أدخل كلمة مرور البوابة:", type="password")

if portal_pass == "1234":
    st.sidebar.success(f"تم تسجيل الدخول بنجاح إلى: {selected_portal}")
    st.subheader(f"📦 إدارة مخزون قسم: {selected_portal}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, register_name, national_code, item_name, remaining_qty, unit_price_iqd, expiry_date FROM items WHERE portal_scope = %s ORDER BY id DESC", (selected_portal,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "السجل", "الرمز الوطني", "اسم المادة", "المتبقي", "السعر المفرد", "تاريخ الانتهاء"])
            st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("⬇️ تسجيل صرف / تخريج مادة")
            
            item_names = [row[3] for row in rows]
            chosen_item_name = st.selectbox("اختر المادة للصرف:", item_names)
            
            if chosen_item_name:
                selected_row = next(r for r in rows if r[3] == chosen_item_name)
                item_id = selected_row[0]
                max_rem = selected_row[4]
                
                st.info(f"الرصيد المتبقي المتاح للمادة ({chosen_item_name}) هو: {max_rem} قطعة")
                dispense_qty = st.number_input("الكمية المراد صرفها:", min_value=1, max_value=max(1, max_rem), value=1)
                letter_ref = st.text_input("رقم كتاب الطلبية أو المستند:")
                
                if st.button("تأكيد الصرف وتنزيل الرصيد"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE items SET dispensed_qty = dispensed_qty + %s, remaining_qty = remaining_qty - %s, dispense_location = %s WHERE id = %s", (dispense_qty, dispense_qty, selected_portal, item_id))
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute("INSERT INTO daily_dispense_log (item_id, dispensed_amount, destination, letter_ref, batch_ref, remaining_after_dispense, dispense_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (item_id, dispense_qty, selected_portal, letter_ref, "صرف فرعي", max_rem - dispense_qty, now_str))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success("تم الصرف بنجاح وتحديث السحابة!")
                    st.rerun()
        else:
            st.warning("لا توجد مواد مسجلة حالياً في هذه البوابة. قم بإضافتها من الحاسبة الرئيسية أولاً.")
    except Exception as e:
        st.error(f"خطأ في الاتصال: {str(e)}")
else:
    st.sidebar.warning("أدخل كلمة المرور (1234).")
