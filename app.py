import streamlit as st
import re
import json
import os
import datetime
import math

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

# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
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
st.caption("Estructura Completa Garantizada | Lab y ECG Extendidos | Auto-Scores")

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

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days

d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- INICIALIZACIÓN DE VARIABLES PARA DATOS FALTANTES ---
apache_cronico = 0
apache_ira = False
child_encef = "Ausente"
child_ascitis = "Ausente"
albumina = 0.0
meld_dialisis = False
bisap_derrame = False

# Scores manuales (Sobreescrituras)
sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""

@st.cache_data
def cargar_diccionario_medico():
    ruta_db = "diccionario.json"
    fallback_db = {
        "isquemia": ["sca", "scacest", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina", "angor", "coronario"],
        "ic": ["ic", "ica", "icc", "insuficiencia cardiaca", "falla cardiaca", "eap", "cor pulmonale"],
        "sepsis": ["sepsis", "septic", "shock", "sirs", "bacteriemia", "vasoplegia", "falla multiorganica"],
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

# --- RECOLECCIÓN DE DATOS FALTANTES PARA SCORES ---
if any([is_isquemia, is_ic, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac]):
    st.markdown("### ⚙️ Complemento de Scores")
    st.caption("Complete los datos faltantes para lograr un cálculo automático preciso, o ingrese el score manualmente para sobreescribir.")

if is_isquemia:
    with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=False):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
        grace = c2.text_input("GRACE Manual")
        timi = c3.text_input("TIMI Manual")
if is_ic:
    with st.expander("🫀 Insuficiencia Cardíaca", expanded=False):
        ic1, ic2, ic3 = st.columns(3)
        nyha = ic1.selectbox("Clase NYHA", ["", "I", "II", "III", "IV"])
        stevenson = ic2.selectbox("Perfil Stevenson", ["", "A (Seco-Cal)", "B (Húm-Cal)", "C (Húm-Frío)", "L (Seco-Frío)"])
        aha_ic = ic3.selectbox("Estadio AHA", ["", "A", "B", "C", "D"])
if is_sepsis:
    with st.expander("🦠 Sepsis (APACHE II / SOFA)", expanded=False):
        st.info("Datos faltantes para cálculo automático de APACHE II:")
        col_a1, col_a2 = st.columns(2)
        apache_cronico = col_a1.selectbox("Puntaje Enfermedad Crónica", [0, 2, 5], format_func=lambda x: f"{x} pts (0=No, 2=Electiva, 5=NoQx/Urgencia)")
        apache_ira = col_a2.checkbox("Falla Renal Aguda (Duplica pts de Creatinina)")
        st.divider()
        s1, s2, s3 = st.columns(3)
        qsofa = s1.text_input("qSOFA manual")
        sofa = s2.text_input("SOFA manual")
        apache = s3.text_input("APACHE II manual")
if is_renal:
    with st.expander("🩸 Nefrología", expanded=False):
        ren1, ren2 = st.columns(2)
        kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
        kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"])
if is_hepato:
    with st.expander("🟡 Hepatopatía (Child-Pugh / MELD)", expanded=False):
        st.info("Datos faltantes para cálculo automático de MELD / Child-Pugh:")
        hp_c1, hp_c2, hp_c3 = st.columns(3)
        child_encef = hp_c1.selectbox("Encefalopatía", ["Ausente", "Grado I-II", "Grado III-IV"])
        child_ascitis = hp_c2.selectbox("Ascitis", ["Ausente", "Leve/Moderada", "Severa/Refractaria"])
        albumina = hp_c3.number_input("Albúmina (g/dL) para Score", min_value=0.0, value=0.0, step=0.1)
        meld_dialisis = st.checkbox("Paciente en Diálisis (Calcula Cr como 4.0 para MELD)")
        st.divider()
        hp1, hp2 = st.columns(2)
        child = hp1.selectbox("Child-Pugh Manual", ["", "A", "B", "C"])
        meld = hp2.text_input("MELD Manual")
if is_pancreas:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=False):
        st.info("Datos faltantes para cálculo de BISAP:")
        bisap_derrame = st.checkbox("Presencia de Derrame Pleural")
        st.divider()
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP Manual")
        ranson = p2.text_input("Ranson Manual")
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
        psi = n2.text_input("PSI / PORT manual")

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
            cant_ampollas = c_calc1.number_input("Cantidad Ampollas", min_value=0.0, value=1.0, step=0.5)
            volumen_ml = c_calc2.number_input("Volumen Dilución (ml)", min_value=0.0, value=100.0, step=10.0)

            droga_mg = cant_ampollas * mg_base
            calc_modo = st.radio("Dirección del cálculo", [f"Calcular DOSIS ({unidad_activa})", "Calcular VELOCIDAD (ml/h)"], horizontal=True)
            nombre_limpio = droga_sel.split(" (")[0]

            if "DOSIS" in calc_modo:
                vel_mlh = st.number_input("Velocidad en bomba (ml/h)", min_value=0.0, value=0.0, step=1.0)
                if droga_mg > 0 and volumen_ml > 0:
                    dosis_calc = calcular_infusion_universal("DOSIS", droga_mg, volumen_ml, peso_paciente, vel_mlh, unidad_activa)
                    st.success(f"**Resultado:** {dosis_calc:.4f} {unidad_activa}")
                    if st.button(f"➕ Anexar {nombre_limpio}", type="secondary"):
                        item = f"{nombre_limpio}: {dosis_calc:.4f} {unidad_activa}"
                        if item not in st.session_state['infusiones_automatizadas']:
                            st.session_state['infusiones_automatizadas'].append(item)
                            st.rerun()
            else:
                dosis_obj = st.number_input(f"Dosis indicada ({unidad_activa})", min_value=0.0, value=0.0, format="%.4f")
                if droga_mg > 0 and volumen_ml > 0:
                    vel_calc = calcular_infusion_universal("VELOCIDAD", droga_mg, volumen_ml, peso_paciente, dosis_obj, unidad_activa)
                    st.success(f"**Programar bomba a:** {vel_calc:.2f} ml/h")

            if st.session_state['infusiones_automatizadas']:
                st.caption("📋 **En memoria:**")
                for inf in st.session_state['infusiones_automatizadas']: st.markdown(f"- `{inf}`")
                if st.button("🗑️ Borrar memoria"):
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
        except: pass
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
            r1, r2, r3, r4 = st.columns(4)
            modo = r1.text_input("Modo", "VCV")
            peep = r2.number_input("PEEP (cmH2O)", 0, 30, 5)
            vt = r3.text_input("Vt (ml)")
            dp_manual = r4.text_input("Driving P.")
            r5, r6, r7 = st.columns(3)
            ppico = r5.text_input("P.Pico (cmH2O)")
            pplat = r6.text_input("P.Plateau (cmH2O)")
            comp = r7.text_input("Comp.")

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

    # --- INFECTOLOGÍA COMPLETA RESTAURADA ---
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

# --- LABORATORIO EXTENDIDO ---
with tab_lab:
    st.info("💡 Solo se imprimirán en la evolución los valores que completes explícitamente.")
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
        gluc = q3.text_input("Glucemia (mg/dL)")
        na = q4.text_input("Na (mEq/L)")
        potasio = q5.text_input("K (mEq/L)")
        cl = q6.text_input("Cl (mEq/L)")

        qe1, qe2, qe3, qe4 = st.columns(4)
        mg = qe1.text_input("Mg (mg/dL)")
        ca_tot = qe2.text_input("Calcemia (mg/dL)")
        ca_io = qe3.text_input("Ca++ Iónico (mmol/L)")
        fosforo = qe4.text_input("Fosfatemia (mg/dL)")

    with st.container(border=True):
        st.subheader("🟡 Hepatograma, Proteínas y Biomarcadores")
        he1, he2, he3, he4, he5, he6 = st.columns(6)
        bt = he1.text_input("BT (mg/dL)")
        bd = he2.text_input("BD (mg/dL)")
        got = he3.text_input("GOT (UI/L)")
        gpt = he4.text_input("GPT (UI/L)")
        fal = he5.text_input("FAL (UI/L)")
        ggt = he6.text_input("GGT (UI/L)")

        # --- NUEVA FILA: PROTEÍNAS E INFLAMACIÓN ---
        pi1, pi2, pi3, pi4 = st.columns(4)
        prot_tot = pi1.text_input("Prot. Totales (g/dL)")
        albumina_lab = pi2.text_input("Albúmina (g/dL)")
        vsg = pi3.text_input("VSG (mm/h)")
        pcr = pi4.text_input("PCR (mg/L)")

        # --- FILA EXISTENTE DE BIOMARCADORES ---
        b1, b2, b3, b4, b5, b6 = st.columns(6)
        ldh = b1.text_input("LDH (UI/L)")
        cpk = b2.text_input("CPK (UI/L)")
        cpk_mb = b3.text_input("CPK-MB (UI/L)")
        tropo = b4.text_input("Tropo I (ng/mL)")
        bnp = b5.text_input("proBNP (pg/mL)")
        pct = b6.text_input("PCT (ng/mL)")

with tab_estudios:
    with st.container(border=True):
        st.subheader("📊 Electrocardiograma (ECG)")
        e_col0, e_col1, e_col2, e_col3 = st.columns(4)
        ecg_fc = e_col0.text_input("FC (lpm)", key="ecg_fc_input", help="Se usa para calcular QTc")
        ecg_ritmo = e_col1.text_input("Ritmo")
        ecg_eje = e_col2.text_input("Eje (°)")
        ecg_pr = e_col3.text_input("PR (ms)")

        e_col4, e_col5, e_col6, e_col7, e_col8 = st.columns(5)
        ecg_qrs_ms = e_col4.text_input("QRS (ms)")
        ecg_qt = e_col5.text_input("QT (ms)")

        # --- CÁLCULO DE QTc BAZETT EN TIEMPO REAL ---
        qtc_ui_str = ""
        try:
            if ecg_fc.strip() and ecg_qt.strip():
                fc_val = float(ecg_fc.replace(',', '.'))
                qt_val = float(ecg_qt.replace(',', '.'))
                if fc_val > 0:
                    rr_sec = 60.0 / fc_val
                    qtc_val = qt_val / math.sqrt(rr_sec)
                    qtc_ui_str = f"{qtc_val:.0f}"
        except: pass

        ecg_qtc = e_col6.text_input("QTc Auto (ms)", value=qtc_ui_str, disabled=True, help="Bazett: QT / √RR")
        ecg_onda_p = e_col7.text_input("Onda P (ms)")
        ecg_st = e_col8.text_input("Segmento ST")

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
temp_n = p_num(temp)
ph_f = p_num(ph)
pco2_f = p_num(pco2)
na_f = p_num(na)
k_f = p_num(potasio)
hto_f = p_num(hto)
gb_f = p_num(gb)
rin_n = p_num(rin)

# --- CÁLCULO SOFA ---
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

# --- CÁLCULO qSOFA & CURB-65 ---
q_calc = sum([gl_val < 15, fr_n is not None and fr_n >= 22, sys_bp is not None and sys_bp <= 100])
c_calc = sum([gl_val < 15, urea_n is not None and urea_n >= 42, fr_n is not None and fr_n >= 30, (sys_bp is not None and sys_bp < 90) or (dia_bp is not None and dia_bp <= 60), edad_n >= 65])

# --- CÁLCULO APACHE II AUTOMÁTICO ---
apache_auto_pts = 0
faltan_datos_apache = False

if edad_n >= 75: apache_auto_pts += 6
elif edad_n >= 65: apache_auto_pts += 5
elif edad_n >= 55: apache_auto_pts += 3
elif edad_n >= 45: apache_auto_pts += 2

if temp_n is not None:
    if temp_n >= 41 or temp_n <= 29.9: apache_auto_pts += 4
    elif temp_n >= 39 or 30 <= temp_n <= 31.9: apache_auto_pts += 3
    elif 32 <= temp_n <= 33.9: apache_auto_pts += 2
    elif 38.5 <= temp_n <= 38.9 or 34 <= temp_n <= 35.9: apache_auto_pts += 1
else: faltan_datos_apache = True

if tam_val:
    if tam_val >= 160 or tam_val <= 49: apache_auto_pts += 4
    elif 130 <= tam_val <= 159: apache_auto_pts += 3
    elif 110 <= tam_val <= 129 or 50 <= tam_val <= 69: apache_auto_pts += 2
else: faltan_datos_apache = True

if fc_n is not None:
    if fc_n >= 180 or fc_n <= 39: apache_auto_pts += 4
    elif 140 <= fc_n <= 179 or 40 <= fc_n <= 54: apache_auto_pts += 3
    elif 110 <= fc_n <= 139 or 55 <= fc_n <= 69: apache_auto_pts += 2
else: faltan_datos_apache = True

if fr_n is not None:
    if fr_n >= 50 or fr_n <= 5: apache_auto_pts += 4
    elif 35 <= fr_n <= 49: apache_auto_pts += 3
    elif 6 <= fr_n <= 9: apache_auto_pts += 2
    elif 25 <= fr_n <= 34 or 10 <= fr_n <= 11: apache_auto_pts += 1
else: faltan_datos_apache = True

if fio2 and po2_n:
    if fio2 >= 50 and pco2_f:
        fio2_dec = fio2 / 100.0
        AaDO2 = (fio2_dec * 713) - (pco2_f / 0.8) - po2_n
        if AaDO2 >= 500: apache_auto_pts += 4
        elif AaDO2 >= 350: apache_auto_pts += 3
        elif AaDO2 >= 200: apache_auto_pts += 2
    elif fio2 < 50:
        if po2_n < 55: apache_auto_pts += 4
        elif po2_n <= 60: apache_auto_pts += 3
        elif po2_n <= 70: apache_auto_pts += 1
else: faltan_datos_apache = True

if ph_f:
    if ph_f >= 7.7 or ph_f < 7.15: apache_auto_pts += 4
    elif 7.6 <= ph_f <= 7.69 or 7.15 <= ph_f <= 7.24: apache_auto_pts += 3
    elif 7.25 <= ph_f <= 7.32: apache_auto_pts += 2
    elif 7.5 <= ph_f <= 7.59: apache_auto_pts += 1

if na_f:
    if na_f >= 180 or na_f <= 110: apache_auto_pts += 4
    elif 160 <= na_f <= 179 or 111 <= na_f <= 119: apache_auto_pts += 3
    elif 155 <= na_f <= 159 or 120 <= na_f <= 129: apache_auto_pts += 2
    elif 150 <= na_f <= 154: apache_auto_pts += 1

if k_f:
    if k_f >= 7 or k_f <= 2.4: apache_auto_pts += 4
    elif 6 <= k_f <= 6.9: apache_auto_pts += 3
    elif 2.5 <= k_f <= 2.9: apache_auto_pts += 2
    elif 5.5 <= k_f <= 5.9 or 3 <= k_f <= 3.4: apache_auto_pts += 1

if cr_n:
    cr_pts = 0
    if cr_n >= 3.6: cr_pts = 4
    elif 1.5 <= cr_n <= 3.49: cr_pts = 2
    elif cr_n < 0.6: cr_pts = 2
    if apache_ira: cr_pts *= 2
    apache_auto_pts += cr_pts

if hto_f:
    if hto_f >= 60 or hto_f < 20: apache_auto_pts += 4
    elif 50 <= hto_f <= 59.9 or 20 <= hto_f <= 29.9: apache_auto_pts += 2
    elif 46 <= hto_f <= 49.9: apache_auto_pts += 1

if gb_f:
    gb_val = gb_f / 1000 if gb_f > 100 else gb_f
    if gb_val >= 40 or gb_val < 1: apache_auto_pts += 4
    elif 20 <= gb_val <= 39.9 or 1 <= gb_val <= 2.9: apache_auto_pts += 2
    elif 15 <= gb_val <= 19.9: apache_auto_pts += 1

if gl_val: apache_auto_pts += (15 - gl_val)
if apache_cronico: apache_auto_pts += apache_cronico

apache_final_str = f"{apache_auto_pts} (Auto)" if not faltan_datos_apache else "Faltan gases/vitales"

# --- CÁLCULO MELD & CHILD-PUGH ---
meld_auto_str = "Faltan datos (Cr, BT, INR, Na)"
if cr_n and bt_n and rin_n:
    cr_meld = max(1.0, cr_n)
    bt_meld = max(1.0, bt_n)
    inr_meld = max(1.0, rin_n)
    if meld_dialisis: cr_meld = 4.0
    meld_score = 3.78 * math.log(bt_meld) + 11.2 * math.log(inr_meld) + 9.57 * math.log(cr_meld) + 6.43
    meld_score = round(meld_score)
    if na_f and 125 <= na_f <= 137:
        meld_na = meld_score + 1.32*(137-na_f) - (0.033*meld_score*(137-na_f))
        meld_auto_str = f"{round(meld_na)} (MELD-Na Auto)"
    else:
        meld_auto_str = f"{meld_score} (Auto)"

child_auto_str = "Faltan datos"
if bt_n and rin_n and albumina > 0:
    pts_child = 0
    if bt_n < 2: pts_child += 1
    elif bt_n <= 3: pts_child += 2
    else: pts_child += 3
    if rin_n < 1.7: pts_child += 1
    elif rin_n <= 2.2: pts_child += 2
    else: pts_child += 3
    if albumina > 3.5: pts_child += 1
    elif albumina >= 2.8: pts_child += 2
    else: pts_child += 3
    if "I-II" in child_encef: pts_child += 2
    elif "III-IV" in child_encef: pts_child += 3
    else: pts_child += 1
    if "Leve" in child_ascitis: pts_child += 2
    elif "Severa" in child_ascitis: pts_child += 3
    else: pts_child += 1
    clase = "A" if pts_child <= 6 else "B" if pts_child <= 9 else "C"
    child_auto_str = f"{pts_child} pts - Clase {clase} (Auto)"

# --- CÁLCULO BISAP ---
bisap_auto_str = "Faltan datos"
if urea_n is not None:
    bisap_pts = 0
    if urea_n > 53.5: bisap_pts += 1 # BUN > 25
    if gl_val < 15: bisap_pts += 1
    if edad_n > 60: bisap_pts += 1
    if bisap_derrame: bisap_pts += 1
    sirs_pts = 0
    if temp_n and (temp_n < 36 or temp_n > 38): sirs_pts += 1
    if fc_n and fc_n > 90: sirs_pts += 1
    if fr_n and (fr_n > 20 or (pco2_f and pco2_f < 32)): sirs_pts += 1
    if gb_f:
        g_val = gb_f / 1000 if gb_f > 100 else gb_f
        if g_val < 4 or g_val > 12: sirs_pts += 1
    if sirs_pts >= 2: bisap_pts += 1
    bisap_auto_str = f"{bisap_pts}/5 (Auto)"

# --- CÁLCULO TFG ---
tfg_str = ""
if cr_n and cr_n > 0:
    factor_mdrd = 0.742 if sexo_paciente == "Femenino" else 1.0
    mdrd_val = 175 * (cr_n ** -1.154) * (edad_n ** -0.203) * factor_mdrd
    tfg_str = f" | TFG (MDRD4): {mdrd_val:.1f} ml/min"

# --- MOTOR INTELIGENTE CENTRAL DE SCORES ---
def motor_scores():
    resultados = []

    # --- SEPSIS ---
    if is_sepsis:
        sofa_val = sofa if sofa.strip() else str(s_pts)
        qsofa_val = qsofa if qsofa.strip() else str(q_calc)
        apache_val = apache if apache.strip() else apache_final_str

        resultados.append({
            "categoria": "Sepsis",
            "scores": {
                "SOFA": sofa_val,
                "qSOFA": qsofa_val,
                "APACHE II": apache_val
            }
        })

    # --- CARDIO ---
    if is_isquemia:
        resultados.append({
            "categoria": "SCA/IAM",
            "scores": {
                "Killip": killip if killip else "Pendiente",
                "GRACE": grace if grace else "Pendiente",
                "TIMI": timi if timi else "Pendiente"
            }
        })

    if is_ic:
        resultados.append({
            "categoria": "Insuficiencia Cardíaca",
            "scores": {
                "NYHA": nyha if nyha else "Pendiente",
                "Stevenson": stevenson if stevenson else "Pendiente",
                "AHA": aha_ic if aha_ic else "Pendiente"
            }
        })

    # --- RENAL ---
    if is_renal:
        resultados.append({
            "categoria": "Renal",
            "scores": {
                "KDIGO IRA": kdigo_ira if kdigo_ira else "Pendiente",
                "ERC": kdigo_erc if kdigo_erc else "Pendiente",
                "TFG": tfg_str if tfg_str else "No calculado"
            }
        })

    # --- HEPATO ---
    if is_hepato:
        resultados.append({
            "categoria": "Hepatopatía",
            "scores": {
                "Child-Pugh": child if child else child_auto_str,
                "MELD": meld if meld else meld_auto_str
            }
        })

    # --- PANCREAS ---
    if is_pancreas:
        resultados.append({
            "categoria": "Pancreatitis",
            "scores": {
                "BISAP": bisap if bisap else bisap_auto_str,
                "Ranson": ranson if ranson else "Pendiente",
                "Balthazar": balthazar if balthazar else "Pendiente"
            }
        })

    # --- NEURO ---
    if is_acv:
        resultados.append({
            "categoria": "ACV",
            "scores": {
                "NIHSS": nihss if nihss else "Pendiente",
                "mRS": mrs if mrs else "Pendiente"
            }
        })

    if is_hsa:
        resultados.append({
            "categoria": "HSA",
            "scores": {
                "Hunt & Hess": hunt if hunt else "Pendiente",
                "Fisher": fisher if fisher else "Pendiente"
            }
        })

    # --- RESP ---
    if is_nac:
        resultados.append({
            "categoria": "Neumonía",
            "scores": {
                "CURB-65": curb65 if curb65 else str(c_calc),
                "PSI": psi if psi else "Pendiente"
            }
        })

    return resultados

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

      scores_globales = motor_scores()

if scores_globales:
    texto_scores = []
    for grupo in scores_globales:
        linea = f"{grupo['categoria']} -> " + " | ".join(
            [f"{k}: {v}" for k, v in grupo['scores'].items()]
        )
        texto_scores.append(f"- {linea}")

    st.info("**Scores Inteligentes Detectados:**\n\n" + "\n".join(texto_scores))
else:
    st.caption("No se detectaron scores automáticos.")

    with st.container(border=True):
        st.subheader("(P) Plan 24hs")
        plan = st.text_area("Indicaciones / Conducta:", "- Cultivar: \n- Interconsultas:", height=100)

    st.divider()

    col_gen, col_limp = st.columns(2)
    btn_generar = col_gen.button("🚀 Generar Evolución", use_container_width=True, type="primary")
    btn_limpiar = col_limp.button("🧹 LIMPIAR PLANILLA", use_container_width=True)

    if btn_limpiar:
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.session_state['infusiones_automatizadas'] = []
        st.session_state['evolucion_generada'] = False
        st.rerun()

    if btn_generar:
        if st.session_state['infusiones_automatizadas']: str_automatizadas = " | ".join(st.session_state['infusiones_automatizadas'])
        else: str_automatizadas = "Sin infusiones activas."

        def construir_linea_lab(items):
            validos = [f"{nombre} {val} {uni}".strip() for nombre, val, uni in items if val.strip()]
            return " | ".join(validos) if validos else ""

        l_eab = construir_linea_lab([("pH", ph, ""), ("pCO2", pco2, "mmHg"), ("pO2", po2, "mmHg"), ("SatO2", sato2_eab, "%"), ("HCO3", hco3, "mEq/L"), ("EB", eb, "mEq/L"), ("Lac", lactato, "mmol/L")])
        l_hemo = construir_linea_lab([("Hb", hb, "g/dL"), ("Hto", hto, "%"), ("GB", gb, "/mm³"), ("Plaq", plaq, "/mm³")])
        l_coag = construir_linea_lab([("APP", app, "%"), ("KPTT", kptt, "s"), ("RIN", rin, "")])

        l_quim = construir_linea_lab([
            ("Urea", urea, "mg/dL"), ("Cr", cr, "mg/dL"), ("Gluc", gluc, "mg/dL"),
            ("Na", na, "mEq/L"), ("K", potasio, "mEq/L"), ("Cl", cl, "mEq/L"),
            ("Mg", mg, "mg/dL"), ("Ca", ca_tot, "mg/dL"), ("Ca++", ca_io, "mmol/L"), ("P", fosforo, "mg/dL")
        ])

        l_hepa = construir_linea_lab([
            ("BT", bt, "mg/dL"), ("BD", bd, "mg/dL"), ("GOT", got, "UI/L"),
            ("GPT", gpt, "UI/L"), ("FAL", fal, "UI/L"), ("GGT", ggt, "UI/L")
        ])

        # --- SE CREA LA LÍNEA DE PROTEÍNAS E INFLAMACIÓN ---
        l_inflam = construir_linea_lab([
            ("Prot.Tot", prot_tot, "g/dL"), ("Alb", albumina_lab, "g/dL"),
            ("VSG", vsg, "mm/h"), ("PCR", pcr, "mg/L")
        ])

        l_bio = construir_linea_lab([
            ("LDH", ldh, "UI/L"), ("CPK", cpk, "UI/L"), ("CPK-MB", cpk_mb, "UI/L"),
            ("Tropo I", tropo, "ng/mL"), ("proBNP", bnp, "pg/mL"), ("PCT", pct, "ng/mL")
        ])

        # --- SE AÑADE LA LÍNEA l_inflam AL BLOQUE FINAL DE LABORATORIO ---
        lab_blocks = [l for l in [l_eab, l_hemo, l_coag, l_quim, l_hepa, l_inflam, l_bio] if l]
        texto_laboratorio = "\n".join(lab_blocks) if lab_blocks else "Pendiente / No consta."

        ecg_items = [
            ("FC", ecg_fc, "lpm"), ("Ritmo", ecg_ritmo, ""), ("Eje", ecg_eje, "°"), ("PR", ecg_pr, "ms"),
            ("QRS", ecg_qrs_ms, "ms"), ("QT", ecg_qt, "ms"), ("QTc", ecg_qtc, "ms"), ("Onda P", ecg_onda_p, "ms"), ("ST", ecg_st, "")
        ]
        ecg_validos = [f"{n} {v}{u}".strip() for n, v, u in ecg_items if v.strip()]
        if ecg_conclusiones.strip():
            ecg_validos.append(f"Conclusión: {ecg_conclusiones.strip()}")
        ecg_final = "- ECG: " + " | ".join(ecg_validos) if ecg_validos else ""

        est_list = []
        if rx_torax.strip(): est_list.append(f"- Rx Tórax/Imágenes: {rx_torax.strip()}")
        if tc.strip(): est_list.append(f"- Tomografía (TC): {tc.strip()}")
        if eco.strip(): est_list.append(f"- Ecografía/POCUS: {eco.strip()}")
        texto_adicionales = "\n".join(est_list)

        bloque_estudios = ""
        if ecg_final or texto_adicionales:
            partes_estudios = [p for p in [ecg_final, texto_adicionales] if p]
            bloque_estudios = "\n>> ECG Y ESTUDIOS COMPLEMENTARIOS:\n" + "\n".join(partes_estudios) + "\n"

        # --- SE RECONSTRUYE TODA LA INFECTOLOGÍA COMPLETA PARA LA EXPORTACIÓN ---
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
            par_str = f"\n  PAR: {(fc_n * pvc_n) / tam_val:.2f}"

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
            try: bal = float(ingresos.replace(',','.')) - float(egresos.replace(',','.')); balance_txt = f" | Ingresos: {ingresos} ml / Egresos: {egresos} ml (Balance: {bal:+.0f} ml)"
            except: pass

        nutri_txt = f" | Nutrición: {nutricion}" if nutricion else ""
        fast_texto = "\n".join([f"  ✓ {letra}" for letra in fast_sel]) if fast_sel else "  Sin marcar."

        bloque_scores_impresion = "\n".join([f"- {s}" for s in auto_scores_list]) + "\n" if auto_scores_list else ""
        bloque_problemas_manual = f"Otros: {problemas_activos_manual.strip()}\n" if problemas_activos_manual.strip() else ""

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
- ABD/RENAL: {ex_abd} | {ex_renal}{nutri_txt}{balance_txt}

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
