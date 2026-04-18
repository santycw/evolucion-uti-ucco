import streamlit as st
import re
import json
import os
import datetime

# --- INICIALIZACIÓN DE ESTADOS DE SESIÓN ---
if 'evolucion_generada' not in st.session_state:
    st.session_state['evolucion_generada'] = False
if 'infusiones_automatizadas' not in st.session_state:
    st.session_state['infusiones_automatizadas'] = []

# --- MOTOR UNIVERSAL DE CÁLCULO DE INFUSIONES ---
def calcular_infusion_universal(modo, cantidad_droga_mg_ui, volumen_ml, peso_kg, valor_input, unidad_objetivo):
    if volumen_ml == 0 or cantidad_droga_mg_ui == 0:
        return 0.0

    conc_base = cantidad_droga_mg_ui / volumen_ml

    if "mcg" in unidad_objetivo or "gammas" in unidad_objetivo:
        conc_final = conc_base * 1000
    else:
        conc_final = conc_base

    usa_peso = "kg" in unidad_objetivo
    peso_factor = peso_kg if usa_peso else 1.0

    usa_min = "min" in unidad_objetivo
    tiempo_factor = 60.0 if usa_min else 1.0

    if modo == "DOSIS":
        dosis = (valor_input * conc_final) / (peso_factor * tiempo_factor)
        return dosis
    else:
        velocidad = (valor_input * peso_factor * tiempo_factor) / conc_final
        return velocidad

# Configuración de página con layout extendido
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO (Diseño Oscuro y Moderno) ---
st.markdown("""
    <style>
    .stTextArea textarea, .stTextInput input, .stNumberInput input {
        font-family: 'Consolas', monospace;
        font-size: 14px;
    }
    div[data-testid="stExpander"] {
        background-color: #1E1E1E !important;
        border-radius: 8px;
        border: 1px solid #333333;
    }
    div[data-testid="stExpander"] label,
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] .stMarkdown {
        color: #F0F2F6 !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-color: #333333 !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión Actual | Auto-Cálculo de Scores | Cálculo por Ampollas | Índice PAR en UI")

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📌 Contexto del Paciente")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", min_value=18, max_value=120, value=65, step=1)
        sexo_paciente = st.selectbox("Sexo", ["Masculino", "Femenino"])
        peso_paciente = st.number_input("Peso Estimado (kg)", min_value=1.0, value=70.0, step=1.0)
        fecha_hosp = st.date_input("Fecha de Ingreso Institución", format="DD/MM/YYYY")
        fecha_uti = st.date_input("Fecha de ingreso UTI/UCCO", format="DD/MM/YYYY")
        dias_arm = st.text_input("Días ARM", placeholder="Ej: 0 o dejar vacío")

    st.header("📋 Diagnóstico de Ingreso")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos (Activan scores):", "1. \n2. ", height=120)

# --- CÁLCULO DINÁMICO DE DÍAS ---
hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days

# --- VARIABLE CONDICIONAL: PACIENTE VENTILADO ---
d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- INICIALIZACIÓN DE SCORES MANUALES ---
sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""

# --- CONEXIÓN A BASE DE DATOS LOCAL ---
@st.cache_data
def cargar_diccionario_medico():
    ruta_db = "diccionario.json"
    fallback_db = {
        "isquemia": ["sca", "scacest", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina", "angor", "coronario"],
        "ic": ["ic", "ica", "icc", "insuficiencia cardiaca", "falla cardiaca", "eap", "cor pulmonale"],
        "sepsis": ["sepsis", "septic", "shock", "sirs", "bacteriemia"],
        "renal": ["ira", "aki", "insuficiencia renal", "falla renal", "erc", "nefropatia"],
        "hepato": ["cirrosis", "hepatopatia", "falla hepatica", "dcl", "hepatitis", "encefalopatia"],
        "pancreas": ["pancreatitis", "pa", "necrosis pancreatica"],
        "acv": ["acv", "ictus", "stroke", "isquemico", "hemorragico", "ait", "tia"],
        "hsa": ["hsa", "hemorragia subaracnoidea", "aneurisma"],
        "nac": ["nac", "neumonia", "pulmonia", "bronconeumonia", "nih"],
        "epoc": ["epoc", "bronquitis cronica", "enfisema", "aeepoc"],
        "tep": ["tep", "tromboembolismo", "embolia pulmonar"],
        "tvp": ["tvp", "trombosis venosa", "trombosis profunda"],
        "hda": ["hda", "hdb", "hemorragia digestiva", "melena", "hematemesis"],
        "cid": ["cid", "coagulacion intravascular diseminada"]
    }
    if os.path.exists(ruta_db):
        try:
            with open(ruta_db, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except: return fallback_db
    else: return fallback_db

db_terminologia = cargar_diccionario_medico()

diag_norm = diagnostico.lower()
diag_norm = re.sub(r'[áäâà]', 'a', diag_norm)
diag_norm = re.sub(r'[éëêè]', 'e', diag_norm)
diag_norm = re.sub(r'[íïîì]', 'i', diag_norm)
diag_norm = re.sub(r'[óöôò]', 'o', diag_norm)
diag_norm = re.sub(r'[úüûù]', 'u', diag_norm)

def detectar_en_db(categoria, texto):
    keywords = db_terminologia.get(categoria, [])
    if not keywords: return False
    patron = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    return bool(re.search(patron, texto))

is_isquemia = detectar_en_db("isquemia", diag_norm)
is_ic = detectar_en_db("ic", diag_norm)
is_sepsis = detectar_en_db("sepsis", diag_norm)
is_renal = detectar_en_db("renal", diag_norm)
is_hepato = detectar_en_db("hepato", diag_norm)
is_pancreas = detectar_en_db("pancreas", diag_norm)
is_acv = detectar_en_db("acv", diag_norm)
is_hsa = detectar_en_db("hsa", diag_norm)
is_nac = detectar_en_db("nac", diag_norm)
is_epoc = detectar_en_db("epoc", diag_norm)
is_tep = detectar_en_db("tep", diag_norm)
is_tvp = detectar_en_db("tvp", diag_norm)
is_hda = detectar_en_db("hda", diag_norm)
is_cid = detectar_en_db("cid", diag_norm)

# --- SCORES MÉDICOS MANUALES (Opcionales) ---
if any([is_isquemia, is_ic, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_epoc, is_tep, is_tvp, is_hda, is_cid]):
    st.markdown("### ⚙️ Ajustes Manuales de Scores")
    st.caption("Complete solo si desea sobrescribir el cálculo automático.")

if is_isquemia:
    with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=False):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
        grace = c2.text_input("GRACE (% Mort)")
        timi = c3.text_input("TIMI (0-7)")
if is_ic:
    with st.expander("🫀 Insuficiencia Cardíaca", expanded=False):
        ic1, ic2, ic3 = st.columns(3)
        nyha = ic1.selectbox("Clase NYHA", ["", "I", "II", "III", "IV"])
        stevenson = ic2.selectbox("Perfil Stevenson", ["", "A (Seco-Cal)", "B (Húm-Cal)", "C (Húm-Frío)", "L (Seco-Frío)"])
        aha_ic = ic3.selectbox("Estadio AHA", ["", "A", "B", "C", "D"])
if is_sepsis:
    with st.expander("🦠 Sepsis", expanded=False):
        s1, s2, s3 = st.columns(3)
        qsofa = s1.text_input("qSOFA manual")
        sofa = s2.text_input("SOFA manual")
        apache = s3.text_input("APACHE II")
if is_renal:
    with st.expander("🩸 Nefrología", expanded=False):
        ren1, ren2 = st.columns(2)
        kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
        kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"])
if is_hepato:
    with st.expander("🟡 Hepatopatía", expanded=False):
        hp1, hp2 = st.columns(2)
        child = hp1.selectbox("Child-Pugh", ["", "A", "B", "C"])
        meld = hp2.text_input("MELD")
if is_pancreas:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=False):
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP")
        ranson = p2.text_input("Ranson")
        balthazar = p3.selectbox("Balthazar (TC)", ["", "A", "B", "C", "D", "E"])
if is_acv:
    with st.expander("🧠 ACV Isquémico", expanded=False):
        a1, a2 = st.columns(2)
        nihss = a1.text_input("NIHSS")
        mrs = a2.selectbox("Rankin (mRS)", ["", "0", "1", "2", "3", "4", "5", "6"])
if is_hsa:
    with st.expander("🧠 Hemorragia Subaracnoidea", expanded=False):
        hsa1, hsa2 = st.columns(2)
        hunt = hsa1.selectbox("Hunt & Hess", ["", "I", "II", "III", "IV", "V"])
        fisher = hsa2.selectbox("Escala Fisher (TC)", ["", "I", "II", "III", "IV"])
if is_nac:
    with st.expander("🫁 Neumonía (NAC)", expanded=False):
        n1, n2 = st.columns(2)
        curb65 = n1.text_input("CURB-65 manual")
        psi = n2.text_input("PSI / PORT")

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_estudios, tab_planes = st.tabs([
    "🩺 Clínica y Examen",
    "🧪 Laboratorio Integral",
    "🩻 ECG y Estudios",
    "📋 Plan y FAST-HUG"
])

with tab_clinca:
    with st.container(border=True):
        st.subheader("(S) Subjetivo")
        subj = st.text_area("Novedades:", "Paciente estable, sin intercurrencias agudas.", height=68)

    with st.container(border=True):
        st.subheader("💊 Infusiones y Dispositivos")

        with st.expander("🧮 Calculadora de Infusiones Farmacológicas (Por Ampollas)", expanded=False):
            dict_calc_drogas = {
                "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
                "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0},
                "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0},
                "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0},
                "Milrinona (10 mg)": {"unidad": "mcg/kg/min", "mg": 10.0},
                "Vasopresina (20 UI)": {"unidad": "UI/min", "mg": 20.0},
                "Fentanilo (0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25},
                "Remifentanilo (2 mg)": {"unidad": "mcg/kg/h", "mg": 2.0},
                "Remifentanilo (5 mg)": {"unidad": "mcg/kg/h", "mg": 5.0},
                "Morfina (10 mg)": {"unidad": "mg/h", "mg": 10.0},
                "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0},
                "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0},
                "Midazolam (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
                "Dexmedetomidina (0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2},
                "Ketamina (500 mg)": {"unidad": "mg/kg/h", "mg": 500.0},
                "Atracurio (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
                "Pancuronio (4 mg)": {"unidad": "mg/kg/h", "mg": 4.0}
            }

            droga_sel = st.selectbox("Seleccione el fármaco y presentación:", list(dict_calc_drogas.keys()))
            unidad_activa = dict_calc_drogas[droga_sel]["unidad"]
            mg_base = dict_calc_drogas[droga_sel]["mg"]

            c_calc1, c_calc2 = st.columns(2)
            cant_ampollas = c_calc1.number_input("Cantidad de Ampollas/Frascos", min_value=0.0, value=1.0, step=0.5)
            volumen_ml = c_calc2.number_input("Volumen Total de Dilución (ml)", min_value=0.0, value=100.0, step=10.0)

            droga_mg = cant_ampollas * mg_base
            calc_modo = st.radio("Dirección del cálculo", [f"Calcular DOSIS ({unidad_activa})", "Calcular VELOCIDAD (ml/h)"], horizontal=True)
            nombre_limpio = droga_sel.split(" (")[0]

            if "DOSIS" in calc_modo:
                vel_mlh = st.number_input("Velocidad actual en bomba (ml/h)", min_value=0.0, value=0.0, step=1.0)
                if droga_mg > 0 and volumen_ml > 0:
                    dosis_calc = calcular_infusion_universal("DOSIS", droga_mg, volumen_ml, peso_paciente, vel_mlh, unidad_activa)
                    st.success(f"**Resultado:** {dosis_calc:.4f} {unidad_activa}")
                    if st.button(f"➕ Anexar {nombre_limpio} a la Evolución", type="secondary"):
                        item = f"{nombre_limpio}: {dosis_calc:.4f} {unidad_activa}"
                        if item not in st.session_state['infusiones_automatizadas']:
                            st.session_state['infusiones_automatizadas'].append(item)
                            st.rerun()
            else:
                dosis_obj = st.number_input(f"Dosis indicada ({unidad_activa})", min_value=0.0, value=0.0, format="%.4f")
                if droga_mg > 0 and volumen_ml > 0:
                    vel_calc = calcular_infusion_universal("VELOCIDAD", droga_mg, volumen_ml, peso_paciente, dosis_obj, unidad_activa)
                    st.success(f"**Programar bomba a:** {vel_calc:.2f} ml/h")
                    if st.button(f"➕ Anexar {nombre_limpio} a la Evolución", type="secondary"):
                        item = f"{nombre_limpio}: {dosis_obj:.4f} {unidad_activa}"
                        if item not in st.session_state['infusiones_automatizadas']:
                            st.session_state['infusiones_automatizadas'].append(item)
                            st.rerun()

            if st.session_state['infusiones_automatizadas']:
                st.markdown("---")
                st.caption("📋 **Infusiones activas en memoria:**")
                for inf in st.session_state['infusiones_automatizadas']: st.markdown(f"- `{inf}`")
                if st.button("🗑️ Borrar memoria de infusiones"):
                    st.session_state['infusiones_automatizadas'] = []
                    st.rerun()

        st.caption("Invasiones / Accesos")
        d1, d2, d3, d4 = st.columns(4)
        cvc_info = d1.text_input("CVC (Sitio/Día)")
        ca_info = d2.text_input("Cat. Art (Sitio/Día)")
        sv_dias = d3.text_input("SV (Día)")
        sng_dias = d4.text_input("SNG (Día)")

    with st.container(border=True):
        st.subheader("1. Neurológico y Hemodinamia")
        n1, n2, n3, n4 = st.columns(4)
        neuro_estado = n1.text_input("Estado", "Alerta")
        glasgow = n2.text_input("Glasgow", "15/15")
        rass = n3.text_input("RASS", "0")
        cam = n4.text_input("CAM-ICU", "-")

        h1, h2, h3, h4, h5 = st.columns(5)
        ta = h1.text_input("TA", placeholder="120/80")
        fc = h2.text_input("FC (lpm)")
        fr = h3.text_input("FR (rpm)")
        sat = h4.text_input("SatO2 (%)")
        temp = h5.text_input("Temp (°C)")

        v1, v2, v3 = st.columns(3)
        pvc = v1.text_input("PVC (cmH2O)")
        relleno_cap = v2.text_input("Relleno Capilar", "< 2 seg")

        # --- CÁLCULO DE PAR EN TIEMPO REAL PARA LA UI ---
        par_ui_str = ""
        try:
            if ta and "/" in ta and fc.strip() and pvc.strip():
                s_bp = float(ta.split("/")[0])
                d_bp = float(ta.split("/")[1])
                t_mean = (s_bp + 2 * d_bp) / 3
                if t_mean > 0:
                    fc_f = float(fc.replace(',', '.'))
                    pvc_f = float(pvc.replace(',', '.'))
                    par_calc = (fc_f * pvc_f) / t_mean
                    par_ui_str = f"{par_calc:.2f}"
        except:
            pass

        v3.text_input("PAR (Auto)", value=par_ui_str, disabled=True, help="Fórmula: (FC × PVC) / TAM")

        ex_cv = st.text_area("Ex. Cardiovascular", "Sin livideces. R1/R2 normofonéticos.")

    with st.container(border=True):
        st.subheader("2. Respiratorio y ARM")
        r_b1, r_b2, r_b3 = st.columns(3)
        if paciente_ventilado:
            via_aerea = r_b1.text_input("Vía Aérea", "TOT")
        else:
            via_aerea = r_b1.selectbox("Dispositivo O2", ["AA (Aire Ambiente)", "Cánula Nasal", "Máscara Reservorio", "CAF", "VNI", "TQTAA"])

        fio2 = r_b2.number_input("FiO2 (%)", 21, 100, 21)
        pafi_manual = r_b3.text_input("PaFiO2 (Opcional)")

        modo = peep = ppico = pplat = comp = vt = dp_manual = ""
        if paciente_ventilado:
            st.info("⚙️ Consola de Mecánica Respiratoria Activa")
            r1, r2, r3, r4 = st.columns(4)
            modo = r1.text_input("Modo", "VCV")
            peep = r2.number_input("PEEP (cmH2O)", 0, 30, 5)
            vt = r3.text_input("Vt (ml)")
            dp_manual = r4.text_input("Driving P. (cmH2O)")

            r5, r6, r7 = st.columns(3)
            ppico = r5.text_input("P.Pico (cmH2O)")
            pplat = r6.text_input("P.Plateau (cmH2O)")
            comp = r7.text_input("Comp. (ml/cmH2O)")

        ex_resp = st.text_input("Examen Respiratorio", "Buena entrada de aire bilateral.")

    with st.container(border=True):
        st.subheader("3. Digestivo y Nutrición")
        a1, a2 = st.columns(2)
        ex_abd = a1.text_input("Abdomen", "Blando, depresible.")
        nutricion = a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"])

    with st.container(border=True):
        st.subheader("4. Renal y Balance Hídrico")
        ex_renal = st.text_input("Diuresis / Ex. Renal", "Conservada.")
        bh1, bh2 = st.columns(2)
        ingresos = bh1.text_input("Ingresos Totales (ml)")
        egresos = bh2.text_input("Egresos Totales (ml)")

    with st.container(border=True):
        st.subheader("5. Infectología")
        tmax = st.text_input("Temp. Máxima 24h (°C)")

        st.caption("Esquema Antibiótico (Completar según necesidad)")
        atb_col1, atb_col2, atb_col3, atb_col4 = st.columns(4)
        atb1 = atb_col1.text_input("ATB 1 y Día")
        atb2 = atb_col2.text_input("ATB 2 y Día")
        atb3 = atb_col3.text_input("ATB 3 y Día")
        atb4 = atb_col4.text_input("ATB 4 y Día")

        st.caption("Cultivos")
        c_1, c_2 = st.columns(2)
        cult_hemo = c_1.text_input("Hemocultivos")
        cult_uro = c_2.text_input("Urocultivo")
        c_3, c_4 = st.columns(2)
        cult_resp = c_3.text_input("Respiratorios (BAL/Mini-BAL)")
        cult_otros = c_4.text_input("Otros (LCR, Catéter, Piel/PB)")

with tab_lab:
    st.info("💡 Solo se imprimirán los valores que se completen explícitamente.")
    with st.container(border=True):
        st.subheader("🌬️ EAB (Estado Ácido-Base)")
        e1, e2, e3, e4, e5, e6, e7 = st.columns(7)
        ph = e1.text_input("pH")
        pco2 = e2.text_input("pCO2 (mmHg)")
        po2 = e3.text_input("pO2 (mmHg)")
        sato2_eab = e4.text_input("SatO2 (%)", key="eab_sato2")
        hco3 = e5.text_input("HCO3 (mEq/L)")
        eb = e6.text_input("EB (mEq/L)")
        lactato = e7.text_input("Lac (mmol/L)")

    with st.container(border=True):
        st.subheader("🩸 Hemograma y Coagulación")
        l1, l2, l3, l4 = st.columns(4)
        hb = l1.text_input("Hb (g/dL)")
        hto = l2.text_input("Hto (%)")
        gb = l3.text_input("GB (/mm³)")
        plaq = l4.text_input("Plaq (/mm³)")

        c1, c2, c3 = st.columns(3)
        app = c1.text_input("APP (%)")
        kptt = c2.text_input("KPTT (s)")
        rin = c3.text_input("RIN")

    with st.container(border=True):
        st.subheader("🧪 Química Plasmática y Electrólitos")
        q1, q2, q3, q4, q5, q6 = st.columns(6)
        urea = q1.text_input("Urea (mg/dL)")
        cr = q2.text_input("Cr (mg/dL)")
        na = q3.text_input("Na (mEq/L)")
        potasio = q4.text_input("K (mEq/L)")
        cl = q5.text_input("Cl (mEq/L)")
        mg = q6.text_input("Mg (mg/dL)")
        gluc = st.text_input("Glucemia (mg/dL)")

    with st.container(border=True):
        st.subheader("🟡 Hepatograma, Proteínas y Biomarcadores")
        he1, he2, he3, he4, he5, he6 = st.columns(6)
        bt = he1.text_input("BT (mg/dL)")
        bd = he2.text_input("BD (mg/dL)")
        got = he3.text_input("GOT (UI/L)")
        gpt = he4.text_input("GPT (UI/L)")
        fal = he5.text_input("FAL (UI/L)")
        ggt = he6.text_input("GGT (UI/L)")

        b1, b2, b3, b4 = st.columns(4)
        cpk = b1.text_input("CPK (UI/L)")
        tropo = b2.text_input("Tropo I (ng/mL)")
        bnp = b3.text_input("proBNP (pg/mL)")
        pct = b4.text_input("PCT (ng/mL)")

with tab_estudios:
    with st.container(border=True):
        st.subheader("📊 Electrocardiograma (ECG)")
        e_col0, e_col1, e_col2, e_col3 = st.columns(4)
        ecg_fc = e_col0.text_input("FC (lpm)", key="ecg_fc_input")
        ecg_ritmo = e_col1.text_input("Ritmo")
        ecg_eje = e_col2.text_input("Eje (°)")
        ecg_pr = e_col3.text_input("PR (ms)")

        e_col4, e_col5, e_col6, e_col7 = st.columns(4)
        ecg_qrs_ms = e_col4.text_input("QRS (ms)")
        ecg_qtc = e_col5.text_input("QTc (ms)")
        ecg_onda_p = e_col6.text_input("Long. Onda P (ms)")
        ecg_st = e_col7.text_input("Segmento ST")

        ecg_conclusiones = st.text_area("Conclusiones ECG", height=68)

    with st.container(border=True):
        st.subheader("🩻 Imágenes y Procedimientos")
        rx_torax = st.text_area("Rx Tórax / Radiografías", height=68)
        tc = st.text_area("Tomografía (TC)", height=68)
        eco = st.text_area("Ecografía / POCUS", height=68)

# --- RUTINA CENTRAL DE AUTO-CÁLCULO ---
def p_num(val):
    try: return float(str(val).replace(',', '.').strip())
    except: return None

# Pre-procesamiento de variables vitales
sys_bp, dia_bp, tam_val, pp_val = None, None, "", ""
if ta and "/" in ta:
    try:
        sys_bp = float(ta.split("/")[0])
        dia_bp = float(ta.split("/")[1])
        tam_val = round((sys_bp + 2*dia_bp)/3)
        pp_val = int(sys_bp - dia_bp)
    except: pass

gl_val = 15
if glasgow:
    try: gl_val = int(glasgow.split("/")[0])
    except: pass

pafi_val = p_num(pafi_manual)
po2_n = p_num(po2)
if not pafi_val and po2_n and fio2:
    pafi_final = str(int(po2_n / (fio2/100)))
    pafi_val = float(pafi_final)
else:
    pafi_final = pafi_manual

plaq_n = p_num(plaq)
bt_n = p_num(bt)
cr_n = p_num(cr)
fr_n = p_num(fr)
fc_n = p_num(fc)
pvc_n = p_num(pvc)
urea_n = p_num(urea)
edad_n = int(edad_paciente)

# Calculo SOFA
s_pts = 0
if pafi_val:
    if pafi_val < 100 and paciente_ventilado: s_pts += 4
    elif pafi_val < 200 and paciente_ventilado: s_pts += 3
    elif pafi_val < 300: s_pts += 2
    elif pafi_val < 400: s_pts += 1
if plaq_n:
    p_val = plaq_n / 1000 if plaq_n > 2000 else plaq_n
    if p_val < 20: s_pts += 4
    elif p_val < 50: s_pts += 3
    elif p_val < 100: s_pts += 2
    elif p_val < 150: s_pts += 1
if bt_n:
    if bt_n >= 12.0: s_pts += 4
    elif bt_n >= 6.0: s_pts += 3
    elif bt_n >= 2.0: s_pts += 2
    elif bt_n >= 1.2: s_pts += 1
cv_pts = 1 if tam_val and tam_val < 70 else 0
for inf in st.session_state.get('infusiones_automatizadas', []):
    if "dobutamina" in inf.lower() or "dopamina" in inf.lower(): cv_pts = max(cv_pts, 2)
    if "adrenalina" in inf.lower() or "noradrenalina" in inf.lower(): cv_pts = 3
s_pts += cv_pts
if gl_val < 6: s_pts += 4
elif gl_val <= 9: s_pts += 3
elif gl_val <= 12: s_pts += 2
elif gl_val <= 14: s_pts += 1
if cr_n:
    if cr_n >= 5.0: s_pts += 4
    elif cr_n >= 3.5: s_pts += 3
    elif cr_n >= 2.0: s_pts += 2
    elif cr_n >= 1.2: s_pts += 1

# Calculo qSOFA
q_calc = sum([
    gl_val < 15,
    fr_n is not None and fr_n >= 22,
    sys_bp is not None and sys_bp <= 100
])

# Calculo CURB-65
c_calc = sum([
    gl_val < 15,
    urea_n is not None and urea_n >= 42,
    fr_n is not None and fr_n >= 30,
    (sys_bp is not None and sys_bp < 90) or (dia_bp is not None and dia_bp <= 60),
    edad_n >= 65
])

# Calculo TFG
tfg_str = ""
if cr_n and cr_n > 0:
    factor_mdrd = 0.742 if sexo_paciente == "Femenino" else 1.0
    mdrd_val = 175 * (cr_n ** -1.154) * (edad_n ** -0.203) * factor_mdrd
    tfg_str = f" | TFG (MDRD4): {mdrd_val:.1f} ml/min"


with tab_planes:
    with st.container(border=True):
        st.subheader("🛡️ FAST HUG BID")
        fast_dict = {
            'F': 'Feeding', 'A': 'Analgesia', 'S': 'Sedación',
            'T': 'Tromboprofilaxis', 'H': 'Head 30°', 'U': 'Úlceras estrés',
            'G': 'Glucemia', 'B': 'Bowel', 'I': 'Invasiones', 'D': 'Desescalar ATB'
        }
        f_cols = st.columns(5)
        fast_sel = []
        for i, (letra, descripcion) in enumerate(fast_dict.items()):
            if f_cols[i % 5].checkbox(letra, help=descripcion):
                fast_sel.append(f"{letra} - {descripcion}")

    with st.container(border=True):
        st.subheader("(A) Problemas Activos")

        auto_scores_list = []
        if is_sepsis:
            val_s = sofa if sofa.strip() else f"{s_pts} (Auto)"
            val_q = qsofa if qsofa.strip() else f"{q_calc} (Auto)"
            val_a = apache if apache.strip() else "Pendiente"
            auto_scores_list.append(f"Sepsis -> SOFA: {val_s} | qSOFA: {val_q} | APACHE II: {val_a}")
        if is_nac:
            val_c = curb65 if curb65.strip() else f"{c_calc} (Auto)"
            auto_scores_list.append(f"Neumonía -> CURB-65: {val_c} | PSI: {psi if psi.strip() else 'Pendiente'}")
        if is_isquemia:
            auto_scores_list.append(f"SCA/IAM -> Killip: {killip if killip.strip() else 'Pendiente'} | GRACE: {grace if grace.strip() else 'Pendiente'} | TIMI: {timi if timi.strip() else 'Pendiente'}")
        if is_renal:
            auto_scores_list.append(f"Renal -> IRA: {kdigo_ira if kdigo_ira.strip() else 'Pendiente'} | ERC: {kdigo_erc if kdigo_erc.strip() else 'Pendiente'}{tfg_str}")
        if is_hepato:
            auto_scores_list.append(f"Hepato -> Child-Pugh: {child if child.strip() else 'Pendiente'} | MELD: {meld if meld.strip() else 'Pendiente'}")

        if auto_scores_list:
            st.info("**Scores calculados / listados automáticamente según diagnóstico:**\n\n" + "\n".join([f"- {s}" for s in auto_scores_list]))
        else:
            st.caption("No se detectaron diagnósticos en la lista que activen un panel automático de scores.")

        problemas_activos_manual = st.text_area("Agregar otros problemas activos (Manual):", placeholder="Ej: Falla renal aguda en plan de hemodiálisis...", height=80)

    with st.container(border=True):
        st.subheader("(P) Plan 24hs")
        plan = st.text_area("Indicaciones / Conducta:", "- Cultivar: \n- Interconsultas:", height=100)

    st.divider()

    # --- BOTONES DE CONTROL GENERAL ---
    col_gen, col_limp = st.columns(2)

    btn_generar = col_gen.button("🚀 Generar Evolución", use_container_width=True, type="primary")

    # NUEVA FUNCIÓN DE BORRADO ABSOLUTO
    btn_limpiar = col_limp.button("🧹 LIMPIAR PLANILLA", use_container_width=True)

    if btn_limpiar:
        # Borra todos los identificadores en memoria y recarga (limpia 100% de la interfaz)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['infusiones_automatizadas'] = []
        st.session_state['evolucion_generada'] = False
        st.rerun()

    if btn_generar:
        st.session_state['evolucion_generada'] = True

        if st.session_state['infusiones_automatizadas']: str_automatizadas = " | ".join(st.session_state['infusiones_automatizadas'])
        else: str_automatizadas = "Sin infusiones activas."

        def construir_linea_lab(items):
            validos = [f"{nombre} {val} {uni}".strip() for nombre, val, uni in items if val.strip()]
            return " | ".join(validos) if validos else ""

        # --- SE AGREGÓ sato2_eab A LA LÍNEA DEL ESTADO ÁCIDO BASE ---
        l_eab = construir_linea_lab([("pH", ph, ""), ("pCO2", pco2, "mmHg"), ("pO2", po2, "mmHg"), ("SatO2", sato2_eab, "%"), ("HCO3", hco3, "mEq/L"), ("EB", eb, "mEq/L"), ("Lac", lactato, "mmol/L")])
        l_hemo = construir_linea_lab([("Hb", hb, "g/dL"), ("Hto", hto, "%"), ("GB", gb, "/mm³"), ("Plaq", plaq, "/mm³")])
        l_coag = construir_linea_lab([("APP", app, "%"), ("KPTT", kptt, "s"), ("RIN", rin, "")])
        l_quim = construir_linea_lab([("Urea", urea, "mg/dL"), ("Cr", cr, "mg/dL"), ("Gluc", gluc, "mg/dL"), ("Na", na, "mEq/L"), ("K", potasio, "mEq/L"), ("Cl", cl, "mEq/L"), ("Mg", mg, "mg/dL")])
        l_hepa = construir_linea_lab([("BT", bt, "mg/dL"), ("BD", bd, "mg/dL"), ("GOT", got, "UI/L"), ("GPT", gpt, "UI/L"), ("FAL", fal, "UI/L"), ("GGT", ggt, "UI/L")])

        lab_blocks = [l for l in [l_eab, l_hemo, l_coag, l_quim, l_hepa] if l]
        texto_laboratorio = "\n".join(lab_blocks) if lab_blocks else "Pendiente / No consta."

        ecg_items = [("FC", ecg_fc, "lpm"), ("Ritmo", ecg_ritmo, ""), ("Eje", ecg_eje, "°"), ("PR", ecg_pr, "ms"),
                     ("QRS", ecg_qrs_ms, "ms"), ("QTc", ecg_qtc, "ms"), ("Onda P", ecg_onda_p, "ms"), ("ST", ecg_st, "")]
        ecg_validos = [f"{n} {v}{u}".strip() for n, v, u in ecg_items if v.strip()]
        if ecg_conclusiones.strip():
            ecg_validos.append(f"Conclusión: {ecg_conclusiones.strip()}")
        ecg_final = "- ECG: " + " | ".join(ecg_validos) if ecg_validos else ""

        est_list = []
        if rx_torax.strip(): est_list.append(f"- Rx: {rx_torax.strip()}")
        if tc.strip(): est_list.append(f"- TC: {tc.strip()}")
        if eco.strip(): est_list.append(f"- Eco/POCUS: {eco.strip()}")
        texto_adicionales = "\n".join(est_list)

        bloque_estudios = ""
        if ecg_final or texto_adicionales:
            partes_estudios = [p for p in [ecg_final, texto_adicionales] if p]
            bloque_estudios = "\n>> ECG Y ESTUDIOS COMPLEMENTARIOS:\n" + "\n".join(partes_estudios) + "\n"

        lista_cultivos = []
        if cult_hemo.strip(): lista_cultivos.append(f"Hemo: {cult_hemo.strip()}")
        if cult_uro.strip(): lista_cultivos.append(f"Uro: {cult_uro.strip()}")
        if cult_resp.strip(): lista_cultivos.append(f"Resp: {cult_resp.strip()}")
        if cult_otros.strip(): lista_cultivos.append(f"Otros: {cult_otros.strip()}")
        cultivos_final = " | ".join(lista_cultivos)

        tmax_str = f"Tmax: {tmax.strip()}°C" if tmax.strip() else ""
        atbs_ingresados = [atb for atb in [atb1, atb2, atb3, atb4] if atb.strip()]
        atb_str = f"ATB: {' / '.join(atbs_ingresados)}" if atbs_ingresados else ""

        infecto_parts = [p for p in [tmax_str, atb_str, cultivos_final] if p]
        bloque_infectologia = "\n>> INFECTOLOGÍA:\n" + "\n".join([f"- {p}" for p in infecto_parts]) + "\n" if infecto_parts else ""

        tam_str = f"{tam_val}" if tam_val != "" else "-"
        pp_str = f"{pp_val}" if pp_val != "" else "-"

        par_str = ""
        if fc_n is not None and pvc_n is not None and tam_val and tam_val > 0:
            par_val = (fc_n * pvc_n) / tam_val
            par_str = f"\n  PAR: {par_val:.2f}"

        signos_vitales = f"""- SIGNOS VITALES:
  TA: {ta if ta.strip() else '-'} mmHg
  TAM: {tam_str} mmHg
  PP: {pp_str} mmHg
  FC: {fc if fc.strip() else '-'} lpm
  PVC: {pvc if pvc.strip() else '-'} cmH2O{par_str}
  Rell. Capilar: {relleno_cap if relleno_cap.strip() else '-'}
  FR: {fr if fr.strip() else '-'} rpm
  SatO2: {sat if sat.strip() else '-'} %
  FiO2: {fio2 if fio2 else '-'} %
  T°: {temp if temp.strip() else '-'} °C"""

        if paciente_ventilado:
            dp_final = dp_manual
            pplat_val = p_num(pplat)
            if not dp_final and pplat_val and peep:
                try: dp_final = str(int(pplat_val - float(peep)))
                except: pass

            texto_resp = f"""{via_aerea}, Modo {modo}, FiO2 {fio2}%, PEEP {peep} cmH2O, PPlat {pplat} cmH2O, Vt {vt} ml.
  Mecánica: P.Pico {ppico} cmH2O | DP {dp_final} | PaFiO2 {pafi_final}.
  Examen: {ex_resp}"""
        else:
            pafi_str = f" | PaFiO2 {pafi_final}" if pafi_final else ""
            texto_resp = f"""Dispositivo: {via_aerea} | FiO2 {fio2}%{pafi_str}.
  Examen: {ex_resp}"""

        balance_txt = ""
        if ingresos and egresos:
            try:
                bal = float(ingresos.replace(',','.')) - float(egresos.replace(',','.'))
                balance_txt = f" | Ingresos: {ingresos} ml / Egresos: {egresos} ml (Balance: {bal:+.0f} ml)"
            except: pass

        nutri_txt = f" | Nutrición: {nutricion}" if nutricion else ""
        fast_texto = "\n".join([f"  ✓ {letra}" for letra in fast_sel]) if fast_sel else "  Sin marcar."

        bloque_scores_impresion = ""
        if auto_scores_list:
            bloque_scores_impresion = "\n".join([f"- {s}" for s in auto_scores_list]) + "\n"

        bloque_problemas_manual = ""
        if problemas_activos_manual.strip():
            bloque_problemas_manual = f"Otros: {problemas_activos_manual.strip()}\n"

        texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Hosp: {dias_int_hosp} | Días UTI: {dias_int_uti} | Días ARM: {dias_arm}

DIAGNÓSTICO:
{diagnostico}
{bloque_infectologia}
(S) SUBJETIVO: {subj}

(O) OBJETIVO:
>> INFUSIONES Y DISPOSITIVOS:
Infusiones Activas: {str_automatizadas}
Invasiones: CVC: {cvc_info} | Cat.Art: {ca_info} | SV: {sv_dias} | SNG: {sng_dias}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
{signos_vitales}

- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}, CAM {cam}.
- CV: {ex_cv}
- RESP: {texto_resp}
- ABD: {ex_abd}{nutri_txt}
- RENAL: {ex_renal}{balance_txt}

>> LABORATORIO Y MEDIO INTERNO:
{texto_laboratorio}
{bloque_estudios}
>> FAST HUG BID:
{fast_texto}

(A) PROBLEMAS ACTIVOS:
{bloque_scores_impresion}{bloque_problemas_manual}
(P) PLAN:
{plan}
"""
        st.success("✅ Evolución generada con éxito, lista para exportar a Historia Clínica.")
        st.code(texto_final, language="markdown")
