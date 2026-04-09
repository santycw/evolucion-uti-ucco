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

# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .stTextArea textarea, .stTextInput input, .stNumberInput input { font-family: 'Consolas', monospace; font-size: 14px; }
    div[data-testid="stExpander"] { background-color: #1E1E1E !important; border-radius: 8px; border: 1px solid #333333; }
    div[data-testid="stExpander"] label, div[data-testid="stExpander"] p, div[data-testid="stExpander"] .stMarkdown { color: #F0F2F6 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("v3.6 | Estructura SOAP Estricta, Edad y Auto-Cálculo de Scores")

# --- PANEL LATERAL (DATOS GENERALES) ---
with st.sidebar:
    st.header("📌 Datos Generales")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", min_value=18, max_value=120, value=65, step=1)
        peso_paciente = st.number_input("Peso Estimado (kg)", min_value=1.0, value=70.0, step=1.0)
        fecha_hosp = st.date_input("Fecha de Ingreso Institución", format="DD/MM/YYYY")
        fecha_uti = st.date_input("Fecha de ingreso UTI/UCCO", format="DD/MM/YYYY")
        dias_arm = st.text_input("Días ARM", placeholder="Ej: 0 o dejar vacío")

    st.header("📋 Diagnóstico de Ingreso")
    with st.container(border=True):
        st.info("💡 El diagnóstico se imprimirá en el bloque de Assessment (Análisis) junto con los Scores.")
        diagnostico = st.text_area("Diagnósticos (Activan scores):", "1. \n2. ", height=120)

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days
d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- CONEXIÓN A BASE DE DATOS LOCAL ---
@st.cache_data
def cargar_diccionario_medico():
    ruta_db = "diccionario.json"
    fallback_db = {
        "isquemia": ["sca", "scacest", "scacst", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina", "angor", "coronario"],
        "ic": ["ic", "ica", "icc", "insuficiencia cardiaca", "falla cardiaca", "eap", "cor pulmonale"],
        "fa": ["fa", "fibrilacion auricular", "aleteo", "flutter", "tpsv", "arritmia completa"],
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
    return fallback_db

db_terminologia = cargar_diccionario_medico()
diag_norm = diagnostico.lower()

def detectar_en_db(categoria, texto):
    keywords = db_terminologia.get(categoria, [])
    patron = r'\b(?:' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    return bool(re.search(patron, texto))

is_isquemia = detectar_en_db("isquemia", diag_norm)
is_ic = detectar_en_db("ic", diag_norm)
is_fa = detectar_en_db("fa", diag_norm)
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

# --- INICIALIZACIÓN DE VARIABLES SCORE ---
sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = cha2ds2 = hasbled = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""

# --- SCORES MÉDICOS ---
if any([is_isquemia, is_ic, is_fa, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_epoc, is_tep, is_tvp, is_hda, is_cid]):
    st.markdown("### ⚙️ Scores Clínicos Sugeridos")
    st.caption("Si deja en blanco scores predictivos como qSOFA o CURB-65, el sistema intentará auto-calcularlos al generar la evolución usando la Edad y los Signos Vitales ingresados.")
    if is_isquemia:
        with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=True):
            c1, c2, c3 = st.columns(3)
            killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
            grace = c2.text_input("GRACE (% Mort)")
            timi = c3.text_input("TIMI (0-7)")
    if is_ic:
        with st.expander("🫀 Insuficiencia Cardíaca", expanded=True):
            ic1, ic2, ic3 = st.columns(3)
            nyha = ic1.selectbox("Clase NYHA", ["", "I", "II", "III", "IV"])
            stevenson = ic2.selectbox("Perfil Stevenson", ["", "A (Seco-Cal)", "B (Húm-Cal)", "C (Húm-Frío)", "L (Seco-Frío)"])
            aha_ic = ic3.selectbox("Estadio AHA", ["", "A", "B", "C", "D"])
    if is_fa:
        with st.expander("💓 Fibrilación Auricular", expanded=True):
            fa1, fa2 = st.columns(2)
            cha2ds2 = fa1.text_input("CHA2DS2-VASc")
            hasbled = fa2.text_input("HAS-BLED")
    if is_sepsis:
        with st.expander("🦠 Sepsis", expanded=True):
            s1, s2, s3 = st.columns(3)
            qsofa = s1.text_input("qSOFA")
            sofa = s2.text_input("SOFA")
            apache = s3.text_input("APACHE II")
    if is_renal:
        with st.expander("🩸 Nefrología", expanded=True):
            ren1, ren2 = st.columns(2)
            kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
            kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"])
    if is_hepato:
        with st.expander("🟡 Hepatopatía", expanded=True):
            hp1, hp2 = st.columns(2)
            child = hp1.selectbox("Child-Pugh", ["", "A", "B", "C"])
            meld = hp2.text_input("MELD")
    if is_pancreas:
        with st.expander("⚕️ Pancreatitis Aguda", expanded=True):
            p1, p2, p3 = st.columns(3)
            bisap = p1.text_input("BISAP")
            ranson = p2.text_input("Ranson")
            balthazar = p3.selectbox("Balthazar (TC)", ["", "A", "B", "C", "D", "E"])
    if is_acv:
        with st.expander("🧠 ACV Isquémico", expanded=True):
            a1, a2 = st.columns(2)
            nihss = a1.text_input("NIHSS")
            mrs = a2.selectbox("Rankin (mRS)", ["", "0", "1", "2", "3", "4", "5", "6"])
    if is_hsa:
        with st.expander("🧠 Hemorragia Subaracnoidea", expanded=True):
            hsa1, hsa2 = st.columns(2)
            hunt = hsa1.selectbox("Hunt & Hess", ["", "I", "II", "III", "IV", "V"])
            fisher = hsa2.selectbox("Escala Fisher (TC)", ["", "I", "II", "III", "IV"])
    if is_nac:
        with st.expander("🫁 Neumonía (NAC)", expanded=True):
            n1, n2 = st.columns(2)
            curb65 = n1.text_input("CURB-65")
            psi = n2.text_input("PSI / PORT")
    if is_epoc:
        with st.expander("🫁 EPOC", expanded=True):
            gold = st.selectbox("Clasificación GOLD", ["", "A", "B", "E"])
    if is_tep or is_tvp:
        with st.expander("🩸 Tromboembolismo", expanded=True):
            t1, t2, t3 = st.columns(3)
            wells_tep = t1.text_input("Wells (TEP)")
            pesi = t2.text_input("PESI / sPESI")
            wells_tvp = t3.text_input("Wells (TVP)")
    if is_hda:
        with st.expander("🩸 Hemorragia Digestiva", expanded=True):
            hd1, hd2 = st.columns(2)
            blatchford = hd1.text_input("Glasgow-Blatchford")
            rockall = hd2.text_input("Score Rockall")
    if is_cid:
        with st.expander("🩸 CID", expanded=True):
            isth = st.selectbox("Score ISTH", ["", "Compatible (≥5 pts)", "No sugerente (<5 pts)"])

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_estudios, tab_planes = st.tabs(["🩺 Clínica y Examen", "🧪 Laboratorio Integral", "🩻 ECG y Estudios", "📋 Plan y FAST-HUG"])

with tab_clinca:
    with st.container(border=True):
        st.subheader("(S) Subjetivo")
        subj = st.text_area("Novedades:", "Paciente estable.", height=68)

    with st.container(border=True):
        st.subheader("💊 Infusiones y Dispositivos")
        with st.expander("🧮 Calculadora de Infusiones Farmacológicas", expanded=True):
            dict_calc_drogas = {
                "Noradrenalina": "mcg/kg/min", "Adrenalina": "mcg/kg/min", "Dobutamina": "mcg/kg/min",
                "Milrinona": "mcg/kg/min", "Fentanilo": "mcg/kg/h", "Remifentanilo": "mcg/kg/h",
                "Morfina": "mg/h", "Propofol": "mg/kg/h", "Midazolam": "mg/kg/h", "Dexmedetomidina": "mcg/kg/h",
                "Ketamina": "mg/kg/h", "Atracurio": "mg/kg/h", "Pancuronio": "mg/kg/h", "Vasopresina": "UI/min"
            }
            droga_sel = st.selectbox("Fármaco:", list(dict_calc_drogas.keys()))
            unidad_activa = dict_calc_drogas[droga_sel]
            c_calc1, c_calc2 = st.columns(2)
            droga_mg = c_calc1.number_input("Droga (mg/UI)", min_value=0.0)
            volumen_ml = c_calc2.number_input("Volumen (ml)", min_value=0.0)
            calc_modo = st.radio("Cálculo:", [f"Dosis ({unidad_activa})", "Velocidad (ml/h)"], horizontal=True)
            if "Dosis" in calc_modo:
                vel_mlh = st.number_input("Velocidad actual en bomba (ml/h)", min_value=0.0)
                if droga_mg > 0 and volumen_ml > 0:
                    res = calcular_infusion_universal("DOSIS", droga_mg, volumen_ml, peso_paciente, vel_mlh, unidad_activa)
                    st.success(f"Resultado: {res:.4f} {unidad_activa}")
                    if st.button(f"➕ Anexar {droga_sel}", type="secondary"):
                        st.session_state['infusiones_automatizadas'].append(f"{droga_sel}: {res:.4f} {unidad_activa}")
                        st.rerun()
            else:
                dosis_obj = st.number_input(f"Dosis indicada ({unidad_activa})", min_value=0.0, format="%.4f")
                if droga_mg > 0 and volumen_ml > 0:
                    res = calcular_infusion_universal("VELOCIDAD", droga_mg, volumen_ml, peso_paciente, dosis_obj, unidad_activa)
                    st.success(f"Bomba: {res:.2f} ml/h")
                    if st.button(f"➕ Anexar {droga_sel}", type="secondary"):
                        st.session_state['infusiones_automatizadas'].append(f"{droga_sel}: {dosis_obj:.4f} {unidad_activa}")
                        st.rerun()

            if st.session_state['infusiones_automatizadas']:
                st.markdown("---")
                st.caption("📋 **Infusiones activas en memoria:**")
                for inf in st.session_state['infusiones_automatizadas']:
                    st.markdown(f"- `{inf}`")
                if st.button("🗑️ Borrar memoria de infusiones", key="borrar_infusiones"):
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
        neuro_estado, glasgow, rass, cam = n1.text_input("Estado", "Alerta"), n2.text_input("GCS", "15/15"), n3.text_input("RASS", "0"), n4.text_input("CAM", "-")
        h1, h2, h3, h4, h5 = st.columns(5)
        ta, fc, fr, sat, temp = h1.text_input("TA", placeholder="120/80"), h2.text_input("FC (lpm)"), h3.text_input("FR"), h4.text_input("Sat (%)"), h5.text_input("Temp (°C)")

        tam_val, pp_val = "", ""
        if "/" in ta:
            try:
                s_bp, d_bp = map(float, ta.split("/"))
                tam_val = round((s_bp + 2*d_bp)/3)
                pp_val = int(s_bp - d_bp)
            except: pass

        v1, v2 = st.columns(2)
        pvc = v1.text_input("PVC (cmH2O)")
        relleno_cap = v2.text_input("Relleno Capilar", "< 2 seg")
        ex_cv = st.text_area("Ex. Cardiovascular", "R1/R2 normofonéticos.")

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
            modo, peep, vt, dp_manual = r1.text_input("Modo", "VCV"), r2.number_input("PEEP (cmH2O)", 0, 30, 5), r3.text_input("Vt (ml)"), r4.text_input("Driving P. (cmH2O)")
            r5, r6, r7 = st.columns(3)
            ppico, pplat, comp = r5.text_input("P.Pico"), r6.text_input("P.Plateau"), r7.text_input("Comp.")

        ex_resp = st.text_input("Examen Respiratorio", "Buena entrada de aire bilateral.")

    with st.container(border=True):
        st.subheader("3. Digestivo y Nutrición")
        a1, a2 = st.columns(2)
        ex_abd, nutricion = a1.text_input("Abdomen", "Blando, depresible."), a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"])

    with st.container(border=True):
        st.subheader("4. Renal y Balance Hídrico")
        ex_renal = st.text_input("Diuresis / Ex. Renal", "Conservada.")
        bh1, bh2 = st.columns(2)
        ingresos, egresos = bh1.text_input("Ingresos Totales (ml)"), bh2.text_input("Egresos Totales (ml)")

    with st.container(border=True):
        st.subheader("5. Infectología")
        tmax = st.text_input("Temp. Máxima 24h (°C)")
        i_1, i_2 = st.columns(2)
        atb1, atb2 = i_1.text_input("ATB 1 y Día"), i_2.text_input("ATB 2 y Día")
        c_1, c_2, c_3, c_4 = st.columns(4)
        cult_hemo, cult_uro, cult_resp, cult_otros = c_1.text_input("Hemocultivos"), c_2.text_input("Urocultivo"), c_3.text_input("Respiratorios"), c_4.text_input("Otros")

with tab_lab:
    st.info("💡 Solo se imprimirán los valores que se completen explícitamente.")
    with st.container(border=True):
        st.subheader("🌬️ EAB (Estado Ácido-Base)")
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        ph, pco2, po2, hco3, eb, lactato = e1.text_input("pH"), e2.text_input("pCO2"), e3.text_input("pO2"), e4.text_input("HCO3"), e5.text_input("EB"), e6.text_input("Lac")

    with st.container(border=True):
        st.subheader("🩸 Hemograma y Coagulación")
        l1, l2, l3, l4 = st.columns(4)
        hb, hto, gb, plaq = l1.text_input("Hb (g/dL)"), l2.text_input("Hto (%)"), l3.text_input("GB (/mm³)"), l4.text_input("Plaq (/mm³)")
        st.caption("Fórmula Leucocitaria")
        f1, f2, f3, f4 = st.columns(4)
        neut, linf, mono, eos = f1.text_input("Neut %"), f2.text_input("Linf %"), f3.text_input("Mono %"), f4.text_input("Eos %")
        st.caption("Coagulación")
        c1, c2, c3 = st.columns(3)
        app, kptt, rin = c1.text_input("APP (%)"), c2.text_input("KPTT (s)"), c3.text_input("RIN")

    with st.container(border=True):
        st.subheader("🧪 Química Plasmática y Electrólitos")
        q1, q2, q3, q4, q5, q6 = st.columns(6)
        urea, cr, na, potasio, cl, mg = q1.text_input("Urea (mg/dL)"), q2.text_input("Cr (mg/dL)"), q3.text_input("Na"), q4.text_input("K"), q5.text_input("Cl"), q6.text_input("Mg")
        q7, q8 = st.columns(2)
        ca, phos = q7.text_input("Ca (mg/dL)"), q8.text_input("P (mg/dL)")
        gluc = st.text_input("Glucemia (mg/dL)")

    with st.container(border=True):
        st.subheader("🟡 Hepatograma y Biomarcadores")
        he1, he2, he3, he4, he5, he6 = st.columns(6)
        bt, bd, got, gpt, fal, ggt = he1.text_input("BT"), he2.text_input("BD"), he3.text_input("GOT"), he4.text_input("GPT"), he5.text_input("FAL"), he6.text_input("GGT")
        p1, p2 = st.columns(2)
        pt, alb = p1.text_input("Proteínas Totales (g/dL)"), p2.text_input("Albúmina (g/dL)")
        st.caption("Biomarcadores y Otros")
        b1, b2, b3, b4, b5, b6 = st.columns(6)
        cpk, cpkmb, tropo, bnp, ldh, pct = b1.text_input("CPK"), b2.text_input("CK-MB"), b3.text_input("Tropo I"), b4.text_input("proBNP"), b5.text_input("LDH"), b6.text_input("PCT")

with tab_estudios:
    with st.container(border=True):
        st.subheader("📊 Electrocardiograma (ECG)")
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        ecg_onda_p = ec1.text_input("Onda P")
        ecg_ritmo = ec2.text_input("Ritmo")
        ecg_eje = ec3.text_input("Eje (°)")
        ecg_pr = ec4.text_input("PR (ms)")
        ecg_qrs = ec5.text_input("QRS (ms)")

        ec6, ec7, ec8 = st.columns(3)
        ecg_qt = ec6.text_input("QT (ms)")

        # --- Lógica Cálculo QTc Bazett en vivo ---
        qtc_sug = ""
        if ecg_qt.strip() and fc.strip():
            try:
                q_val = float(ecg_qt.replace(',', '.'))
                f_val = float(fc.replace(',', '.'))
                if f_val > 0:
                    qtc_sug = str(int(q_val / ((60/f_val)**0.5)))
            except: pass

        ecg_qtc = ec7.text_input("QTc (ms)", value=qtc_sug)
        ecg_st = ec8.text_input("Segmento ST")
        ecg_otros = st.text_input("Otros hallazgos ECG")

    with st.container(border=True):
        st.subheader("🩻 Imágenes y Procedimientos")
        rx_torax = st.text_area("Rx Tórax / Radiografías", height=68)
        tc = st.text_area("Tomografía (TC)", height=68)
        eco = st.text_area("Ecografía / POCUS", height=68)
        otros_estudios = st.text_area("Otros (Endoscopía, EEG, Interconsultas específicas)", height=68)

with tab_planes:
    with st.container(border=True):
        st.subheader("🛡️ FAST HUG BID")
        fast_dict = {'F': 'Feeding', 'A': 'Analgesia', 'S': 'Sedación', 'T': 'Tromboprofilaxis', 'H': 'Head 30°', 'U': 'Úlceras estrés', 'G': 'Glucemia', 'B': 'Bowel', 'I': 'Invasiones', 'D': 'Desescalar ATB'}
        f_cols = st.columns(5)
        fast_sel = []
        for i, (letra, descripcion) in enumerate(fast_dict.items()):
            if f_cols[i % 5].checkbox(letra, help=descripcion):
                fast_sel.append(f"{letra} - {descripcion}")

    with st.container(border=True):
        st.subheader("(A/P) Análisis y Plan")
        analisis = st.text_area("Análisis General", height=150)
        plan = st.text_area("Plan 24hs", "- Cultivar: \n- Interconsultas:", height=150)

    st.divider()
    c_gen, c_lim = st.columns(2)

    btn_generar = c_gen.button("🚀 GENERAR HISTORIA CLÍNICA (GECLISA)", use_container_width=True, type="primary")
    if btn_generar:
        st.session_state['evolucion_generada'] = True

    if c_lim.button("🧹 LIMPIAR PLANILLA", use_container_width=True, disabled=not st.session_state['evolucion_generada']):
        st.session_state.clear()
        st.rerun()

    if btn_generar:
        # --- RUTINA DE AUTO-CÁLCULO DE SCORES ---
        sys_bp, dia_bp = 120, 80
        if "/" in ta:
            try: sys_bp, dia_bp = map(float, ta.split("/"))
            except: pass

        fr_val = 0
        try: fr_val = float(fr)
        except: pass

        gl_val = 15
        if "/" in glasgow:
            try: gl_val = int(glasgow.split("/")[0])
            except: pass
        elif glasgow.isdigit():
            try: gl_val = int(glasgow)
            except: pass

        urea_val = 0
        try: urea_val = float(urea.replace(',','.'))
        except: pass

        # Auto-qSOFA si hay Sepsis y está vacío
        if is_sepsis and not qsofa:
            q_calc = 0
            if gl_val < 15: q_calc += 1
            if fr_val >= 22: q_calc += 1
            if sys_bp <= 100: q_calc += 1
            qsofa = f"{q_calc} (Auto)"

        # Auto-CURB65 si hay Neumonía y está vacío
        if is_nac and not curb65:
            c_calc = 0
            if gl_val < 15: c_calc += 1
            if urea_val >= 42: c_calc += 1 # Aprox BUN > 19
            if fr_val >= 30: c_calc += 1
            if sys_bp < 90 or dia_bp <= 60: c_calc += 1
            if edad_paciente >= 65: c_calc += 1
            curb65 = f"{c_calc} (Auto)"

        # Bloque compilación de Scores para Assessment
        txt_mod = ""
        if is_isquemia and any([killip, grace, timi]): txt_mod += f"\n  • SCA/IAM -> Killip: {killip} | GRACE: {grace} | TIMI: {timi}"
        if is_ic and any([nyha, stevenson, aha_ic]): txt_mod += f"\n  • IC -> NYHA: {nyha} | Stevenson: {stevenson} | AHA: {aha_ic}"
        if is_sepsis and any([qsofa, sofa, apache]): txt_mod += f"\n  • SEPSIS -> qSOFA: {qsofa} | SOFA: {sofa} | APACHE: {apache}"
        if is_renal and any([kdigo_ira, kdigo_erc]): txt_mod += f"\n  • NEFRO -> IRA: {kdigo_ira} | ERC: {kdigo_erc}"
        if is_hepato and any([child, meld]): txt_mod += f"\n  • HEPATO -> Child: {child} | MELD: {meld}"
        if is_nac and any([curb65, psi]): txt_mod += f"\n  • NAC -> CURB-65: {curb65} | PSI: {psi}"

        str_automatizadas = " | ".join(st.session_state['infusiones_automatizadas']) if st.session_state['infusiones_automatizadas'] else "Sin infusiones activas."

        def construir_linea_lab(items):
            validos = [f"{nombre} {val} {uni}".strip() for nombre, val, uni in items if val.strip()]
            return " | ".join(validos) if validos else ""

        l_eab = construir_linea_lab([("pH", ph, ""), ("pCO2", pco2, "mmHg"), ("pO2", po2, "mmHg"), ("HCO3", hco3, "mEq/L"), ("EB", eb, "mEq/L"), ("Lac", lactato, "mmol/L")])
        gb_str = f"{gb}".strip() if gb.strip() else ""
        if gb_str:
            if any([neut.strip(), linf.strip(), mono.strip(), eos.strip()]): gb_str += f" /mm³ (N:{neut}% L:{linf}% M:{mono}% E:{eos}%)"
            else: gb_str += " /mm³"

        l_hemo = construir_linea_lab([("Hb", hb, "g/dL"), ("Hto", hto, "%"), ("GB", gb_str, ""), ("Plaq", plaq, "/mm³")])
        l_coag = construir_linea_lab([("APP", app, "%"), ("KPTT", kptt, "s"), ("RIN", rin, "")])
        l_quim = construir_linea_lab([("Urea", urea, "mg/dL"), ("Cr", cr, "mg/dL"), ("Gluc", gluc, "mg/dL"), ("Na", na, "mEq/L"), ("K", potasio, "mEq/L"), ("Cl", cl, "mEq/L"), ("Mg", mg, "mg/dL"), ("Ca", ca, "mg/dL"), ("P", phos, "mg/dL")])
        l_hepa = construir_linea_lab([("BT", bt, "mg/dL"), ("BD", bd, "mg/dL"), ("GOT", got, "UI/L"), ("GPT", gpt, "UI/L"), ("FAL", fal, "UI/L"), ("GGT", ggt, "UI/L"), ("PT", pt, "g/dL"), ("Alb", alb, "g/dL")])
        l_biom = construir_linea_lab([("CPK", cpk, "UI/L"), ("CK-MB", cpkmb, "UI/L"), ("Tropo I", tropo, "ng/mL"), ("proBNP", bnp, "pg/mL"), ("LDH", ldh, "UI/L"), ("PCT", pct, "ng/mL")])
        lab_blocks = [l for l in [l_eab, l_hemo, l_coag, l_quim, l_hepa, l_biom] if l]
        texto_laboratorio = "\n".join(lab_blocks) if lab_blocks else "Pendiente / No consta en el día de la fecha."

        # ECG Formato Extendido
        ecg_items = [("Onda P", ecg_onda_p, ""), ("Ritmo", ecg_ritmo, ""), ("Eje", ecg_eje, "°"), ("PR", ecg_pr, "ms"), ("QRS", ecg_qrs, "ms")]
        ecg_validos = [f"{n} {v}{u}".strip() for n, v, u in ecg_items if v.strip()]

        qt_final_str = ""
        if ecg_qt.strip() or ecg_qtc.strip():
            qt_final_str = f"QT/QTc {ecg_qt.strip() if ecg_qt.strip() else '-'}/{ecg_qtc.strip() if ecg_qtc.strip() else '-'} ms"
            ecg_validos.append(qt_final_str)

        if ecg_st.strip(): ecg_validos.append(f"ST {ecg_st.strip()}")
        if ecg_otros.strip(): ecg_validos.append(ecg_otros.strip())

        ecg_final = "- ECG: " + " | ".join(ecg_validos) if ecg_validos else ""

        est_list = []
        if rx_torax.strip(): est_list.append(f"- Rx: {rx_torax.strip()}")
        if tc.strip(): est_list.append(f"- TC: {tc.strip()}")
        if eco.strip(): est_list.append(f"- Eco/POCUS: {eco.strip()}")
        if otros_estudios.strip(): est_list.append(f"- Otros Estudios: {otros_estudios.strip()}")
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
        atb_str = f"ATB: {atb1} / {atb2}".strip(' /') if (atb1 or atb2) else ""
        infecto_parts = [p for p in [tmax_str, atb_str, cultivos_final] if p]
        bloque_infectologia = "\n>> INFECTOLOGÍA:\n" + "\n".join([f"- {p}" for p in infecto_parts]) + "\n" if infecto_parts else ""

        signos_vitales = f"""- SIGNOS VITALES:
  TA: {ta if ta.strip() else '-'} mmHg
  TAM: {tam_val if tam_val != "" else '-'} mmHg
  PP: {pp_val if pp_val != "" else '-'} mmHg
  PR: {fc if fc.strip() else '-'} lpm
  PVC: {pvc if pvc.strip() else '-'} cmH2O
  Rell. Capilar: {relleno_cap if relleno_cap.strip() else '-'}
  FR: {fr if fr.strip() else '-'} rpm
  SatO2: {sat if sat.strip() else '-'} %
  FiO2: {fio2 if fio2 else '-'} %
  T°: {temp if temp.strip() else '-'} °C"""

        pafi_final = pafi_manual
        if not pafi_final and po2 and fio2:
            try: pafi_final = str(int(float(str(po2).replace(',','.')) / (float(fio2)/100)))
            except: pass

        if paciente_ventilado:
            dp_final = dp_manual
            if not dp_final and pplat and peep:
                try: dp_final = str(int(float(str(pplat).replace(',','.')) - float(str(peep).replace(',','.'))))
                except: pass
            texto_resp = f"""{via_aerea}, Modo {modo}, FiO2 {fio2}%, PEEP {peep} cmH2O, PPlat {pplat} cmH2O, Vt {vt} ml.
  Mecánica: P.Pico {ppico} cmH2O | Comp {comp} | DP {dp_final} | PaFiO2 {pafi_final}.
  Examen: {ex_resp}"""
        else:
            pafi_str = f" | PaFiO2 {pafi_final}" if pafi_final else ""
            texto_resp = f"""Dispositivo: {via_aerea} | FiO2 {fio2}%{pafi_str}.
  Examen: {ex_resp}"""

        balance_txt = ""
        if ingresos and egresos:
            try:
                bal = float(ingresos.replace(',','.')) - float(egresos.replace(',','.'))
                balance_txt = f" | Ingresos: {ingresos} ml / Egresos: {egresos} ml (Balance 24h: {bal:+.0f} ml)"
            except: pass

        nutri_txt = f" | Nutrición: {nutricion}" if nutricion else ""
        fast_texto = "\n".join([f"  ✓ {letra}" for letra in fast_sel]) if fast_sel else "  Sin marcar."

        # Ensamblaje Final SOAP Estricto
        texto_final = f"""EVOLUCIÓN UTI / UCCO
Datos Generales: Edad: {edad_paciente} años | Peso Estimado: {peso_paciente} kg
Días Hosp: {dias_int_hosp} | Días UTI: {dias_int_uti} | Días ARM: {dias_arm}

(S) SUBJETIVO:
{subj}

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
{bloque_infectologia}
>> LABORATORIO Y MEDIO INTERNO:
{texto_laboratorio}
{bloque_estudios}
>> FAST HUG BID:
{fast_texto}

(A) ASSESSMENT / ANÁLISIS:
>> DIAGNÓSTICOS ACTIVOS:
{diagnostico}
>> SCORES DE GRAVEDAD Y PRONÓSTICO:{txt_mod if txt_mod else " No aplica / No calculados."}

>> ANÁLISIS CLÍNICO:
{analisis}

(P) PLAN 24HS:
{plan}
"""
        st.success("✅ Evolución generada con éxito. Lista para exportar a GECLISA.")
        st.code(texto_final, language="markdown")
