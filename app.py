
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# --- НАСТРОЙКИ ВАШЕГО ИП ---
IP_NAME = "Restudia"
IP_UNP = "ИП Дьяков А.М." 
IP_ADDRESS = "Бульвар дружбы 11а"
IP_PHONE = "+375 (33) 355-43-43"
# ---------------------------

st.set_page_config(page_title="CRM Ремонт", page_icon="📱", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Segoe UI', Roboto, sans-serif; }
    [data-testid="stSidebar"] { background-color: #1E293B; }
    [data-testid="stSidebar"] * { color: #F8FAFC !important; }
    
    .stButton>button { border-radius: 8px; font-weight: 500; transition: all 0.2s; font-size: 12px !important; padding: 4px 10px !important; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #E2E8F0; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); background-color: #FAFAFA; }
    .total-box { background-color: #ecfdf5; border: 1px solid #10b981; padding: 15px; border-radius: 8px; color: #065f46; font-weight: bold; font-size: 18px; text-align: right; margin-top: 10px; }
    
    /* Уменьшаем шрифты */
    h1 { font-size: 20px !important; margin-bottom: 5px !important; }
    h2 { font-size: 16px !important; margin-bottom: 5px !important; }
    h3 { font-size: 14px !important; margin-bottom: 5px !important; }
    p, li, label { font-size: 12px !important; margin-bottom: 2px !important; }
    
    /* Компактные отступы */
    [data-testid="stHorizontalBlock"] { gap: 1rem !important; }
    [data-testid="stCheckbox"] { margin-bottom: -10px; }
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] { font-size: 12px !important; min-height: 30px !important; }
    
    /* Ограничиваем ширину страницы */
    .block-container {
        max-width: 900px !important;
        margin: 0 auto !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
        /* Разрешаем таблицам быть шире основного контейнера */
    div[data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Принудительно растягиваем саму таблицу внутри */
    div[data-testid="stDataFrame"] > div {
        width: 950px !important;
        min-width: 950px !important;
    }
    /* Ограничиваем ширину выпадающих списков (selectbox) */
    div[data-testid="stSelectbox"] {
        max-width: 300px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- База данных ---
conn = sqlite3.connect('repair_shop.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, surname TEXT, name TEXT, phone TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, display_num INTEGER, client_id INTEGER, device TEXT, issue TEXT, 
    kit TEXT, appearance TEXT, prepayment REAL, payment_method TEXT, master TEXT, 
    status TEXT, price REAL, created_at TEXT, updated_at TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id)
)''')
conn.commit()

c.execute("PRAGMA table_info(orders)")
columns = [info[1] for info in c.fetchall()]
if 'works_done' not in columns: c.execute("ALTER TABLE orders ADD COLUMN works_done TEXT DEFAULT ''")
if 'brand' not in columns: c.execute("ALTER TABLE orders ADD COLUMN brand TEXT DEFAULT ''")
if 'inspection' not in columns: c.execute("ALTER TABLE orders ADD COLUMN inspection TEXT DEFAULT ''")
if 'warranty' not in columns: c.execute("ALTER TABLE orders ADD COLUMN warranty TEXT DEFAULT ''")
if 'completed_at' not in columns: c.execute("ALTER TABLE orders ADD COLUMN completed_at TEXT DEFAULT ''")
if 'display_num' not in columns: 
    c.execute("ALTER TABLE orders ADD COLUMN display_num INTEGER DEFAULT 0")
    c.execute("SELECT id FROM orders ORDER BY created_at ASC")
    for idx, row in enumerate(c.fetchall(), start=1):
        c.execute("UPDATE orders SET display_num = ? WHERE id = ?", (idx, row[0]))
conn.commit()

# --- Функции ---
def num2words_rub(num):
    units = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    teens = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
    tens = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
    hundreds = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]
    
    num = float(num)
    kop = int(round((num - int(num)) * 100))
    rub = int(num)
    if rub == 0: return f"Ноль рублей {kop:02d} копеек"
    
    res = []
    if rub >= 100: res.append(hundreds[rub // 100]); rub %= 100
    if rub >= 20: res.append(tens[rub // 10]); rub %= 10
    elif rub >= 10: res.append(teens[rub - 10]); rub = 0
    if rub > 0: res.append(units[rub])
    
    word_rub = "рублей"
    if str(num).endswith('1') and not str(num).endswith('11'): word_rub = "рубль"
    elif str(num).endswith(('2','3','4')) and not str(num).endswith(('12','13','14')): word_rub = "рубля"
    return (" ".join(res) + f" {word_rub} {kop:02d} копеек").capitalize()

def generate_document(order, type_doc):
    if order.get('completed_at'):
        order_date = pd.to_datetime(order['completed_at']).strftime('%d.%m.%Y')
    else:
        order_date = datetime.now().strftime('%d.%m.%Y')
    
    if type_doc == "act":
        title = "Акт сдачи-приемки выполненных работ (оказанных услуг)"
        bottom_text = f"""
        <div style="margin-top: 10px; font-size: 12px;">
            Всего наименований {order.get('works_count', 1)}, на сумму {order['price']:.2f} руб<br>
            <b>{num2words_rub(order['price'])}</b><br>
            Вышеперечисленные услуги выполнены полностью и в срок.<br>
            Заказчик претензий по объему, качеству и срокам оказания услуг не имеет.
        </div>
        """
    elif type_doc == "warranty":
        title = "Гарантийный талон"
        bottom_text = ""
    else:
        title = "Квитанция о приеме устройства в ремонт"
        bottom_text = """
        <div style="margin-top: 15px; font-size: 10px; line-height: 1.3;">
            <b>Условия приема:</b><br>
            1. Срок диагностики и ремонта составляет до 30 дней. В случае необходимости заказа запчастей срок может быть увеличен.<br>
            2. Исполнитель не несет ответственности за сохранность данных (клиенту рекомендуется сделать резервную копию).<br>
            3. Неисправность установлена со слов клиента и является предварительной. Стоимость определяется после диагностики. При выявлении скрытых дефектов (следы влаги, окисление, падения) Исполнитель согласует новую стоимость с Заказчиком.<br>
            4. Устройство сдается в неразобранном виде. Гарантия не распространяется на скрытые дефекты предыдущего ремонта.<br>
            5. Клиент согласен с риском: во время диагностики скрытые дефекты могут проявиться и привести к выходу устройства из строя.<br>
            6. Бесплатное хранение — 30 дней. С 31-го дня плата 2 руб./день.<br>
            7. Если Заказчик не забирает устройство 60 дней, Исполнитель вправе взыскать долг через суд, не неся ответственности за сохранность.<br><br>
            <b>С условиями ознакомлен и согласен. Претензий к внешнему виду и комплектации не имею.</b>
        </div>
        """

    rows = ""
    total_price = 0
    works_count = 0
    
    if type_doc in ["act", "warranty"] and order.get('works_done'):
        for item in str(order['works_done']).split(';'):
            parts = item.split('|')
            if len(parts) >= 2:
                w_name = parts[0]
                try: w_price = float(parts[1])
                except: w_price = 0.0
                w_warranty = parts[2] if len(parts) > 2 else ""
                
                rows += f"<tr><td>{works_count+1}</td><td>{w_name}</td><td>{w_warranty}</td><td class='text-right'>1 шт.</td><td class='text-right'>{w_price:.2f}</td><td class='text-right'>{w_price:.2f}</td></tr>"
                total_price += w_price
                works_count += 1
    
    if not rows:
        rows = f"<tr><td>1</td><td>{order['issue']}</td><td>{order.get('warranty', '')}</td><td class='text-right'>1 шт.</td><td class='text-right'>{order['price']:.2f}</td><td class='text-right'>{order['price']:.2f}</td></tr>"
        total_price = order['price']
        works_count = 1

    html = f"""
    <html><head><meta charset="utf-8"><style>
        body {{ font-family: Arial, sans-serif; padding: 0; margin: 0; line-height: 1.2; color: #000; font-size: 11px; }}
        h1 {{ font-size: 14px; margin: 0 0 3px 0; font-weight: bold; }}
        .doc-num {{ font-size: 14px; font-weight: bold; margin-bottom: 10px; }}
        .info-block {{ display: flex; margin-bottom: 10px; }}
        .info-left {{ width: 50%; }} .info-right {{ width: 50%; }}
        .info-row {{ margin-bottom: 3px; }} .info-label {{ font-weight: bold; color: #444; display: inline-block; width: 80px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
        th {{ border-bottom: 2px solid #000; border-top: 2px solid #000; padding: 4px; text-align: left; font-size: 10px; }}
        td {{ border-bottom: 1px solid #ccc; padding: 4px; font-size: 11px; }}
        .text-right {{ text-align: right; }}
        .totals {{ float: right; width: 250px; margin-bottom: 10px; }}
        .totals-row {{ display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #ccc; }}
        .totals-row.bold {{ font-weight: bold; border-bottom: 2px solid #000; }}
        .terms {{ font-size: 9px; margin-top: 10px; clear: both; }}
        .terms ol {{ padding-left: 15px; margin-top: 3px; margin-bottom: 0; }} .terms li {{ margin-bottom: 2px; }}
        .signatures {{ margin-top: 30px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 11px; }}
        .sig-line {{ border-bottom: 1px solid #000; width: 120px; display: inline-block; margin: 0 5px; }}
    </style></head><body>
        <h1>{title}</h1><div class="doc-num">№ {order['display_num']} от {order_date}</div>
        <div class="info-block">
            <div class="info-left">
                <div class="info-row"><span class="info-label">Исполнитель:</span> {IP_NAME}</div>
                <div class="info-row"><span class="info-label">Адрес:</span> {IP_ADDRESS}</div>
                <div class="info-row"><span class="info-label">Телефон:</span> {IP_PHONE}</div>
            </div>
            <div class="info-right">
                <div class="info-row"><span class="info-label">Заказчик:</span> {order['client']}</div>
                <div class="info-row"><span class="info-label">Телефон:</span> {order['phone']}</div>
                <div class="info-row"><span class="info-label">Марка/модель:</span> {order.get('brand', '')} {order['device']}</div>
            </div>
        </div>
    """
    
    if type_doc == "receipt":
        html += f"""
        <div style="border: 1px solid #000; padding: 8px; margin-bottom: 10px;">
            <div style="margin-bottom: 3px;"><b>Заявленная неисправность:</b> {order['issue']}</div>
            <div style="margin-bottom: 3px;"><b>Комплектация:</b> {order['kit']}</div>
            <div><b>Состояние устройства:</b> {order['inspection']}</div>
        </div>
        
        <div class="totals">
            <div class="totals-row"><span>Предоплата:</span> <span>{order['prepayment']:.2f}</span></div>
            <div class="totals-row bold"><span>Предварительная стоимость:</span> <span>{total_price:.2f}</span></div>
        </div>
        {bottom_text}
        """
    else:
        html += f"""
        <table><thead><tr><th style="width: 30px;">№</th><th>Наименование товаров и услуг</th><th style="width: 70px;">Гарантия</th><th style="width: 80px;" class="text-right">Количество</th><th style="width: 60px;" class="text-right">Цена</th><th style="width: 60px;" class="text-right">Сумма</th></tr></thead>
        <tbody>{rows}</tbody></table>
        
        <div class="totals">
            <div class="totals-row"><span>Предоплата:</span> <span>{order['prepayment']:.2f}</span></div>
            <div class="totals-row bold"><span>Итого:</span> <span>{total_price:.2f}</span></div>
        </div>
        {bottom_text}
        """
    
    if type_doc == "warranty":
        html += f"""
        <div class="terms"><ol>
            <li>Гарантия распространяется исключительно на выполненные работы и установленные запасные части.</li>
            <li>Гарантия не действует при наличии: механических повреждений (падения, удары, трещины), следов попадания жидкости или влаги, следов самостоятельного вскрытия или ремонта в сторонних сервисах, а также повреждений, вызванных скачками напряжения.</li>
            <li>При обнаружении следов попадания влаги или коррозии после вскрытия устройства, исполнитель вправе отказать в гарантийном ремонте.</li>
            <li>Устройство принимается на гарантийное обслуживание только при предъявлении данного талона. Срок гарантийного ремонта составляет до 14 рабочих дней.</li>
            <li>С условиями гарантии ознакомлен и согласен.</li>
        </ol></div>
        
        html += f"""
                <div class="signatures">
                <div>Исполнитель: <span class="sig-line"></span> / {IP_UNP.replace('ИП ', '')} /</div>
                <div><span class="sig-line"></span> / Заказчик /</div>
            </div>
            <script>window.print();</script>
        </body></html>"""
    elif type_doc == "act":
        html += f"""
            <div class="signatures">
                <div>Исполнитель: <span class="sig-line"></span> / {IP_UNP.replace('ИП ', '')} /</div>
                <div><span class="sig-line"></span> / Заказчик /</div>
            </div>
            <script>window.print();</script>
        </body></html>"""
    else:
        html += f"""
            <div class="signatures">
                <div>Устройство принял: <span class="sig-line"></span> / {IP_UNP.replace('ИП ', '')} /</div>
                <div>Устройство сдал: <span class="sig-line"></span> / Заказчик /</div>
            </div>
            <script>window.print();</script>
        </body></html>"""

    return html

if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "Заказы"
def go_to_add_order(): st.session_state.menu_choice = "Добавить заказ"

st.sidebar.title("📱 Ремонт CRM")
menu = st.sidebar.radio("Навигация", ["Заказы", "Клиенты", "Добавить заказ"], key="menu_choice")
st.sidebar.divider()
with open("repair_shop.db", "rb") as f:
    st.sidebar.download_button(
        label="💾 Скачать резервную копию базы",
        data=f,
        file_name="repair_shop_backup.db",
        mime="application/octet-stream",
        help="Нажмите, чтобы сохранить всех клиентов и заказы на компьютер"
    )

# --- ДОБАВИТЬ ЗАКАЗ ---
if menu == "Добавить заказ":
    st.subheader("Новый заказ")
    client_mode = st.radio("Клиент:", ["Выбрать из базы", "Создать нового"], horizontal=True)
    client_id = None
    
    if client_mode == "Выбрать из базы":
        clients = pd.read_sql_query("SELECT id, surname, name, phone FROM clients", conn)
        if clients.empty: st.warning("В базе нет клиентов. Переключитесь на 'Создать нового'.")
        else:
            c_opts = clients.apply(lambda r: f"{(str(r['surname']) + ' ') if pd.notna(r['surname']) and str(r['surname']).strip() else ''}{r['name']} ({r['phone']})", axis=1).tolist()
        sel_c = st.selectbox("Выберите клиента", c_opts)
        client_id = int(clients.iloc[c_opts.index(sel_c)]['id'])
    else:
        col_s, col_n = st.columns(2)
        with col_s: new_surname = st.text_input("Фамилия")
        with col_n: new_name = st.text_input("Имя")
        st.write("Телефон (введите 9 цифр):")
        col1, col2 = st.columns([1, 4])
        with col1: st.text_input("Код", value="+375", disabled=True, label_visibility="collapsed", key="new_c_code")
        with col2: new_phone_raw = st.text_input("Номер", placeholder="33 696 87 87", label_visibility="collapsed", key="new_c_phone")

    st.divider()
    col_brand, col_model = st.columns(2)
    with col_brand: brand = st.text_input("Марка (Xiaomi, iPhone, Samsung...)")
    with col_model: device = st.text_input("Модель (Redmi Note 10, 13 Pro...)")
    issue = st.text_area("Неисправность со слов клиента")
    
    # Состояние устройства (фиксация при приемке)
     # Комплектация
    st.write("**Комплектация:**")
    
    k_case = st.checkbox("Чехол")
    k_sim = st.checkbox("СИМ-карта")
    k_sd = st.checkbox("Карта памяти (флешка)")
    
    k_other = st.checkbox("Другое")
    k_txt = st.text_input("Другое (текст):") if k_other else ""
    
    # Состояние устройства (фиксация при приемке)
    st.write("**Состояние устройства:**")
    
    s_nopower = st.checkbox("Не включается")
    s_noimage = st.checkbox("Нет изображения (черный экран)")
    s_water = st.checkbox("Следы влаги / окисление")
    s_crack = st.checkbox("Разбит дисплей")
    s_matrix = st.checkbox("Повреждена матрица")
    s_case = st.checkbox("Кривой / сколотый корпус")
    s_scratch = st.checkbox("Царапины")
    
    s_other = st.text_input("Другие видимые дефекты:")
    price = st.number_input("Предварительная цена", min_value=0.0, step=10.0)
    prepay = st.number_input("Предоплата", min_value=0.0, step=10.0)
    
    p_method = st.selectbox("Способ предоплаты", ["Не вносилась", "Наличные", "Карта"])
    master = st.text_input("Мастер")
    
    if st.button("Создать заказ", type="primary"):
        if not device: st.error("Укажите модель телефона!")
        elif client_mode == "Создать нового" and (not new_name or not new_phone_raw):
            st.error("Заполните все данные нового клиента!")
        else:
            if client_mode == "Создать нового":
                digits = ''.join(filter(str.isdigit, new_phone_raw))
                f_phone = f"+375 ({digits[:2]}) {digits[2:5]} {digits[5:7]} {digits[7:9]}" if len(digits) == 9 else f"+375 {new_phone_raw}"
                c.execute("INSERT INTO clients (surname, name, phone) VALUES (?, ?, ?)", (new_surname, new_name, f_phone))
                conn.commit()
                client_id = c.lastrowid
            
            # --- СЧИТАЕМ НОМЕР ЗАКАЗА ---
            total_orders = pd.read_sql_query("SELECT COUNT(*) as c FROM orders", conn).iloc[0]['c']
            new_display_num = total_orders + 1
            
            # --- СОБИРАЕМ КОМПЛЕКТАЦИЮ И ВНЕШНИЙ ВИД ---
            kit_l = [x for x, y in [(("Чехол", k_case)), (("СИМ", k_sim)), (("Флешка", k_sd))] if y]
            if k_other and k_txt: kit_l.append(k_txt)
            kit_s = ", ".join(kit_l) if kit_l else "Нет"
            
            # Сборка комплектации
            kit_l = []
            if k_case: kit_l.append("Чехол")
            if k_sim: kit_l.append("СИМ")
            if k_sd: kit_l.append("Флешка")
            if k_other and k_txt: kit_l.append(k_txt)
            kit_s = ", ".join(kit_l) if kit_l else "Нет"
            # Собираем состояние устройства в один текст
            state_list = []
            if s_nopower: state_list.append("Не включается")
            if s_noimage: state_list.append("Нет изображения")
            if s_water: state_list.append("Следы влаги")
            if s_crack: state_list.append("Разбит дисплей")
            if s_matrix: state_list.append("Повреждена матрица")
            if s_case: state_list.append("Кривой корпус")
            if s_scratch: state_list.append("Царапины")
            if s_other: state_list.append(s_other)
            
            insp_str = ", ".join(state_list) if state_list else "Без видимых повреждений"
            
            # --- СОХРАНЯЕМ ЗАКАЗ ---
            now = datetime.now().isoformat()
            insp_list = []
            if s_crack: insp_list.append("Разбит дисплей")
            if s_matrix: insp_list.append("Повреждена матрица")
            if s_case: insp_list.append("Кривой корпус")
            if s_nopower: insp_list.append("Не включается")
            if s_noimage: insp_list.append("Нет изображения")
            if s_water: insp_list.append("Следы влаги")
            if s_scratch: insp_list.append("Царапины")
            if s_other: insp_list.append(s_other)
            c.execute("INSERT INTO orders (display_num, client_id, brand, device, issue, kit, appearance, inspection, prepayment, payment_method, master, status, price, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (new_display_num, client_id, brand, device, issue, kit_s, insp_str, prepay, p_method, master, 'Принят', price, now, now))
            conn.commit()
            st.success(f"Заказ №{new_display_num} успешно создан!")

# --- СПИСОК ЗАКАЗОВ ---
elif menu == "Заказы":
    
    st.markdown("## Заказы")
    if st.button("➕ Создать заказ", type="primary", on_click=go_to_add_order): pass

    # АВТО-ПЕРЕНУМЕРАЦИЯ
    c.execute("SELECT id FROM orders ORDER BY created_at ASC")
    all_orders = c.fetchall()
    for idx, row in enumerate(all_orders, start=1):
        c.execute("UPDATE orders SET display_num = ? WHERE id = ?", (idx, row[0]))
    conn.commit()

    df = pd.read_sql_query("SELECT o.*, c.surname, c.name, c.phone FROM orders o JOIN clients c ON o.client_id = c.id ORDER BY o.display_num ASC", conn)
    
    if not df.empty:
        df['client'] = df['surname'].fillna('').apply(lambda x: str(x) + ' ' if str(x).strip() else '') + df['name'].fillna('')
        df['date_short'] = pd.to_datetime(df['created_at']).dt.strftime('%d.%m.%Y %H:%M')

    tabs = st.tabs(["Все заказы", "Новые", "В работе", "Готовые", "Выданные"])
    tab_statuses = [None, ["Принят"], ["В работе"], ["Готов"], ["Выдан"]]

    for i, tab in enumerate(tabs):
        with tab:
            if df.empty: st.info("Заказов пока нет"); continue
            f_df = df.copy()
            if tab_statuses[i]: f_df = f_df[f_df['status'].isin(tab_statuses[i])]
            
            if f_df.empty: st.info("Нет заказов с таким статусом"); continue
            
             # Склеиваем марку и модель для таблицы
            f_df['device_full'] = f_df['brand'].fillna('').apply(lambda x: str(x) + ' ' if str(x).strip() else '') + f_df['device'].fillna('')
            
            disp = f_df.rename(columns={'display_num': '№', 'status': 'Статус', 'date_short': 'Дата', 'client': 'Клиент', 'phone': 'Тел', 'device_full': 'Устройство', 'issue': 'Неисправность со слов клиента', 'price': 'Сумма'})
            
            # Форматируем сумму
            disp['Сумма'] = disp['Сумма'].apply(lambda x: f"{x:.2f} BYN")
            
            # ВСТАВЬ ЭТУ СТРОЧКУ СЮДА:
            st.markdown("<style>div[data-testid='stDataFrame'] { zoom: 0.8; }</style>", unsafe_allow_html=True)

            def color_stat(val):
                if val == 'Готов': return 'background-color: #10b981; color: white;'
                if val == 'В работе': return 'background-color: #f59e0b; color: white;'
                if val == 'Выдан': return 'background-color: #6b7280; color: white;'
                if val == 'Отменён': return 'background-color: #ef4444; color: white;'
                return 'background-color: #3b82f6; color: white;'
            
            # Красивая таблица с выравниванием
            styled_df = disp[['Статус', 'Дата', '№', 'Устройство', 'Клиент', 'Тел', 'Неисправность со слов клиента', 'Сумма']].style.map(color_stat, subset=['Статус'])
            
            # Центрируем номер и сумму, остальное по левому краю
            styled_df = styled_df.set_properties(**{'text-align': 'left'})
            styled_df = styled_df.set_properties(subset=['№', 'Сумма'], **{'text-align': 'center'})
            styled_df = styled_df.set_properties(subset=['Статус'], **{'text-align': 'center', 'font-weight': 'bold'})
            
            f_df['price'] = f_df['price'].round(2)
            disp['Сумма'] = disp['Сумма'].astype(str).str.replace(' BYN', '').apply(lambda x: f"{x} BYN")
            # Уменьшаем шрифт в таблице
            st.markdown("<style>div[data-testid='stDataFrame'] { font-size: 12px !important; }</style>", unsafe_allow_html=True)
            st.dataframe(disp[['Статус', 'Дата', '№', 'Устройство', 'Клиент', 'Тел', 'Неисправность со слов клиента', 'Сумма']].style.map(color_stat, subset=['Статус']), use_container_width=True, hide_index=True)
            
            opts = f_df.apply(lambda r: f"Заказ №{r['display_num']} | {r['client']} | {(str(r['brand']) + ' ') if pd.notna(r['brand']) and str(r['brand']).strip() else ''}{r['device']} ({r['status']})", axis=1).tolist()
            sel = st.selectbox("Подробности:", opts, key=f"sel_{i}")
            
            selected_index = opts.index(sel)
            o_id = int(f_df.iloc[selected_index]['id'])
            o_det = f_df[f_df['id'] == o_id].iloc[0]
            
            col_left, col_right = st.columns([2, 1], gap="large")
            
            with col_left:
                st.markdown(f"### Заказ №{o_det['display_num']}")
                st.write(f"**Клиент:** {o_det['client']} | {o_det['phone']}")
                st.write(f"**Устройство:** {o_det['brand']} {o_det['device']}")
                st.write(f"**Неисправность:** {o_det['issue']}")
                st.write(f"**Комплектация:** {o_det['kit']}")
                st.write(f"**Состояние:** {o_det.get('inspection', 'Не указано')}")
            
            with col_right:
                st.write(f"**Статус:** {o_det['status']}")
                st.write(f"**Стоимость:** {o_det['price']} руб. (Предоплата: {o_det['prepayment']})")
                st.write(f"**Мастер:** {o_det['master']}")
                
                sms_text = f"Здравствуйте, {o_det['client'].split()[0]}! Ваш {o_det['device']} готов. Сумма: {o_det['price']} BYN."
                st.markdown(f"<div style='white-space: pre-wrap; font-size: 12px; background: #f0f2f6; padding: 10px; border-radius: 5px;'>{sms_text}</div>", unsafe_allow_html=True)

            st.divider() # Разделитель между шапкой и управлением

            # --- УПРАВЛЕНИЕ ЗАКАЗОМ (на всю ширину) ---
            n_stat = st.selectbox("Изменить статус:", ["Принят", "В работе", "Готов", "Выдан", "Отменён"], index=["Принят", "В работе", "Готов", "Выдан", "Отменён"].index(o_det['status']), key=f"n_stat_{o_id}_{i}")
            
            works_key = f"works_list_{o_id}"
            if works_key not in st.session_state:
                st.session_state[works_key] = []
                if o_det.get('works_done'):
                    for item in str(o_det['works_done']).split(';'):
                        parts = item.split('|')
                        if len(parts) >= 2:
                            w_name = parts[0]
                            try: w_price = float(parts[1])
                            except: w_price = 0.0
                            w_warranty = parts[2] if len(parts) > 2 else ""
                            st.session_state[works_key].append({"name": w_name, "price": w_price, "warranty": w_warranty})
            
            if n_stat == "Выдан":
                st.markdown("**Выполненные работы:**")
                for idx, w in enumerate(st.session_state[works_key]):
                    c_w1, c_w2, c_w3, c_w4 = st.columns([3, 1, 1, 0.5])
                    new_name = c_w1.text_input(f"Работа {idx+1}", value=w['name'], key=f"wn_{o_id}_{idx}_{i}")
                    new_price = c_w2.number_input(f"Сумма {idx+1}", min_value=0.0, step=10.0, value=w['price'], key=f"wp_{o_id}_{idx}_{i}")
                    new_warranty = c_w3.text_input(f"Гар-тия {idx+1}", value=w.get('warranty', ''), key=f"ww_{o_id}_{idx}_{i}")
                    st.session_state[works_key][idx] = {"name": new_name, "price": new_price, "warranty": new_warranty}
                    if c_w4.button("❌", key=f"delw_{o_id}_{idx}_{i}"):
                        st.session_state[works_key].pop(idx)
                        st.rerun()

                if st.button("➕ Добавить еще работу", key=f"add_w_{o_id}_{i}"):
                    st.session_state[works_key].append({"name": "", "price": 0.0, "warranty": ""})
                    st.rerun()
                    
                calculated_price = sum(w['price'] for w in st.session_state[works_key] if w['name'].strip())
                st.markdown(f'<div class="total-box">Итоговая цена: {calculated_price:.2f} BYN</div>', unsafe_allow_html=True)
                n_price = calculated_price 
            else:
                n_price = st.number_input("Итоговая цена:", min_value=0.0, step=10.0, value=float(o_det['price']), key=f"pr_{o_id}_{i}")
            
            if st.button("Сохранить изменения", type="primary", key=f"s_{o_id}_{i}"):
                works_str = ";".join([f"{w['name']}|{w['price']}|{w.get('warranty', '')}" for w in st.session_state[works_key] if w['name'].strip()])
                now = datetime.now().isoformat()
                comp_at = now if n_stat == "Выдан" else o_det.get('completed_at', '')
                c.execute("UPDATE orders SET status=?, price=?, works_done=?, completed_at=?, updated_at=? WHERE id=?", (n_stat, n_price, works_str, comp_at, now, o_id))
                conn.commit()
                st.success("Сохранено!")
                st.rerun()
            
            # --- ДОКУМЕНТЫ ---
            o_dict = o_det.to_dict()
            works_count = len([w for w in str(o_det.get('works_done', '')).split(';') if w.strip()])
            o_dict['works_count'] = works_count if works_count > 0 else 1

            if o_det['status'] in ["Принят", "В работе"] and (tab_statuses[i] is None or tab_statuses[i] in [["Принят"], ["В работе"]]):
                st.markdown("### 🖨️ Документы (Приемка)")
                if st.button("🖨️ Печать квитанции о приеме", key=f"pr_rec_{o_id}_{i}", use_container_width=True, type="primary"):
                    components.html(generate_document(o_dict, "receipt"), height=800, scrolling=True)
            
            elif o_det['status'] == "Выдан" and (tab_statuses[i] is None or tab_statuses[i] == ["Выдан"]):
                st.markdown("### 🖨️ Документы (Выдача)")
                cp1, cp2, cp3 = st.columns(3)
                with cp1:
                    if st.button("Акт выполненных работ", key=f"pa_{o_id}_{i}", use_container_width=True):
                        components.html(generate_document(o_dict, "act"), height=800, scrolling=True)
                with cp2:
                    if st.button("Гарантийный талон", key=f"pw_{o_id}_{i}", use_container_width=True):
                        components.html(generate_document(o_dict, "warranty"), height=800, scrolling=True)
                with cp3:
                    if st.button("✂️ Печать комплекта", key=f"pboth_{o_id}_{i}", use_container_width=True, type="primary"):
                        html_act = generate_document(o_dict, "act")
                        html_warranty = generate_document(o_dict, "warranty")
                        html_act = html_act.replace("<script>window.print();</script>", "")
                        cut_line = """<div style="text-align: center; margin: 20px 0; position: relative; page-break-inside: avoid;"><div style="border-top: 1px dashed #000; width: 100%; position: absolute; top: 50%; z-index: 1;"></div><span style="background: #fff; padding: 0 10px; position: relative; z-index: 2; font-size: 16px;">✂️</span></div>"""
                        combined_html = html_act.replace("</body></html>", cut_line + html_warranty)
                        components.html(combined_html, height=1400, scrolling=True)
            
            st.markdown("---")
            if st.button("❌ Удалить заказ", type="secondary", key=f"d_{o_id}_{i}", use_container_width=True):
                c.execute("DELETE FROM orders WHERE id = ?", (o_id,))
                conn.commit()
                st.success("Удалено")
                st.rerun()

# --- КЛИЕНТЫ ---
elif menu == "Клиенты":
        st.subheader("Клиенты")
        df_c = pd.read_sql_query("SELECT * FROM clients", conn)
        
        if df_c.empty: 
            st.info("Нет клиентов")
        else:
            # Красивая таблица
            display_clients = df_c.copy()
            display_clients.insert(0, '№', range(1, len(display_clients) + 1))
            display_clients = display_clients.rename(columns={'surname': 'Фамилия', 'name': 'Имя', 'phone': 'Телефон', 'notes': 'Заметки'})
            st.dataframe(display_clients[['№', 'Фамилия', 'Имя', 'Телефон', 'Заметки']], use_container_width=True, hide_index=True)
            
            st.divider()
        
        # Блок редактирования
        st.subheader("✏️ Редактировать или удалить клиента")
        
        # Создаем словарь для выбора (Фамилия Имя - Телефон)
        opts = {f"{(str(r['surname']) + ' ') if pd.notna(r['surname']) and str(r['surname']).strip() else ''}{r['name']} ({r['phone']})": r['id'] for r in df_c.to_dict('records')}
        sel = st.selectbox("Выберите клиента:", list(opts.keys()))
        client_id = opts[sel]
        
        # Получаем текущие данные выбранного клиента
        client_data = df_c[df_c['id'] == client_id].iloc[0]
        
        # Форма редактирования
        col1, col2 = st.columns(2)
        with col1:
            new_surname = st.text_input("Фамилия", value=client_data['surname'])
        with col2:
            new_name = st.text_input("Имя", value=client_data['name'])
            
        # Телефон с маской
        st.write("Телефон (введите 9 цифр):")
        col_code, col_phone = st.columns([1, 4])
        with col_code:
            st.text_input("Код", value="+375", disabled=True, key="edit_code", label_visibility="collapsed")
        with col_phone:
            current_digits = ''.join(filter(str.isdigit, client_data['phone']))[-9:] if client_data['phone'] else ""
            new_phone_raw = st.text_input("Номер", value=current_digits, key="edit_phone", label_visibility="collapsed")
            
        new_notes = st.text_area("Заметки", value=client_data['notes'] if client_data['notes'] else "")
        
        # Кнопки действий
        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("💾 Сохранить изменения", type="primary", use_container_width=True):
                if not new_name or not new_phone_raw:
                    st.error("Заполните ФИО и телефон!")
                else:
                    digits = ''.join(filter(str.isdigit, new_phone_raw))
                    f_phone = f"+375 ({digits[:2]}) {digits[2:5]} {digits[5:7]} {digits[7:9]}" if len(digits) == 9 else f"+375 {new_phone_raw}"
                    
                    c.execute("UPDATE clients SET surname=?, name=?, phone=?, notes=? WHERE id=?", 
                              (new_surname, new_name, f_phone, new_notes, client_id))
                    conn.commit()
                    st.success("Данные клиента обновлены!")
                    st.rerun()
                    
        with col_del:
            if st.button("❌ Удалить клиента", type="secondary", use_container_width=True):
                # Проверяем, есть ли у клиента заказы
                if pd.read_sql_query(f"SELECT COUNT(*) as c FROM orders WHERE client_id={client_id}", conn).iloc[0]['c'] > 0:
                    st.error("У клиента есть заказы! Удаление невозможно.")
                else:
                    c.execute("DELETE FROM clients WHERE id=?", (client_id,))
                    conn.commit()
                    st.success("Клиент удален")
                    st.rerun()
