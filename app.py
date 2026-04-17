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
    if volumen_ml == 0 or cantidad_droga_mg_ui == 0: return 0.0
    conc_base = cantidad_droga_mg_ui / volumen_ml
    conc_final = conc_base * 1000 if "mcg" in unidad_objetivo or "gammas" in unidad_objetivo else conc_base
    peso_factor = peso_kg if "kg" in unidad_objetivo else 1.0
    tiempo_factor = 60.0 if "min" in unidad_objetivo else 1.0

    if modo == "DOSIS": return (valor_input * conc_final) / (peso_factor * tiempo_factor)
    else: return (valor_input * peso_factor * tiempo_factor) / conc_final

# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .stTextArea textarea, .stTextInput input, .stNumberInput input { font-family: 'Consolas', monospace; font-size: 14px; }
    div[data-testid="stExpander"] { background-color: #1E1E1E !important; border: 1px solid #333333; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión Actual | Motor Offline (Tesauro Local) | Cálculo por Ampolla | Omisión de Vacíos")

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📌 Datos Generales")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", 18, 120, 65)
        sexo_paciente = st.selectbox("Sexo", ["Masculino", "Femenino"])
        peso_paciente = st.number_input("Peso Estimado (kg)", 1.0, 300.0, 70.0)
        fecha_hosp = st.date_input("Fecha Ingreso Hosp.", format="DD/MM/YYYY")
        fecha_uti = st.date_input("Fecha Ingreso UTI", format="DD/MM/YYYY")
        dias_arm = st.text_input("Días ARM", placeholder="0 o dejar vacío")

    st.header("📋 Diagnóstico")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos (Activan scores predictivos):", placeholder="Ej: Neumonía, Shock séptico...", height=100)
        st.caption("El motor interno interpretará automáticamente el texto para habilitar escalas clínicas relevantes.")

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days
paciente_ventilado = bool(dias_arm.strip() and dias_arm.strip() not in ["0", "-", "no"])

# --- CONEXIÓN A TESAURO LOCAL ---
@st.cache_data
def cargar_diccionario_medico():
    return {
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

db_terminologia = cargar_diccionario_medico()
diag_norm = diagnostico.lower()

def detectar_en_db(categoria, texto):
    patron = r'\b(?:' + '|'.join(re.escape(kw) for kw in db_terminologia.get(categoria, [])) + r')\b'
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
timi_crit = apache_cro = cp_ascitis = cp_encef = None

# --- SCORES MÉDICOS INTERACTIVOS ---
if any([is_isquemia, is_ic, is_fa, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_epoc, is_tep, is_tvp, is_hda, is_cid]):
    st.markdown("### ⚙️ Scores Clínicos Sugeridos")
    if is_isquemia:
        with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=True):
            killip = st.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
            timi_crit = st.multiselect("Criterios para Score TIMI:", ["AAS en últimos 7 días", "≥ 3 FR Cardiovasculares", "Enf. Coronaria conocida (Est. > 50%)", "Angina Severa (≥ 2 epi en 24h)", "Desviación ST ≥ 0.5mm", "Marcadores Cardíacos Positivos"])
            grace = st.text_input("GRACE (% Mort)")
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
        with st.expander("🦠 Sepsis y Estado Crítico", expanded=True):
            apache_cro = st.selectbox("APACHE II - Salud Crónica", ["Ninguna", "Inmunosupresión", "Cirrosis/Falla Hepática", "Falla CV severa (NYHA IV)", "EPOC Severo", "Diálisis crónica"])
            apache_tipo = st.radio("Ingreso:", ["Médico / Quirúrgico Urgente", "Quirúrgico Electivo"], horizontal=True)
            s1, s2 = st.columns(2)
            qsofa = s1.text_input("qSOFA")
            sofa = s2.text_input("SOFA")
    if is_renal:
        with st.expander("🩸 Nefrología", expanded=True):
            ren1, ren2 = st.columns(2)
            kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
            kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"])
    if is_hepato:
        with st.expander("🟡 Hepatopatía", expanded=True):
            hp1, hp2 = st.columns(2)
            cp_ascitis = hp1.selectbox("Grado Ascitis", ["Ausente", "Leve/Moderada", "Tensión/Refractaria"])
            cp_encef = hp2.selectbox("Grado Encefalopatía", ["Ninguna", "Grado I - II", "Grado III - IV"])
    if is_pancreas:
        with st.expander("⚕️ Pancreatitis Aguda", expanded=True):
            p1, p2 = st.columns(2)
            bisap = p1.text_input("BISAP")
            balthazar = p2.selectbox("Balthazar (TC)", ["", "A", "B", "C", "D", "E"])
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

# --- PESTAÑAS PRINCIPALES ---
tab_clinca, tab_lab, tab_estudios, tab_planes = st.tabs(["🩺 Clínica", "🧪 Laboratorio", "🩻 ECG/Imagen", "📋 Plan"])

with tab_clinca:
    with st.container(border=True):
        st.subheader("Subjetivo e Infusiones")
        subj = st.text_area("Novedades (S):", placeholder="Paciente refiere...", height=68)

        with st.expander("🧮 Calculadora por Ampolla (Argentina)", expanded=False):
            dict_calc = {
                "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
                "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0},
                "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0},
                "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0},
                "Fentanilo (0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25},
                "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0},
                "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0},
                "Dexmedetomidina (0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2}
            }
            droga = st.selectbox("Droga:", list(dict_calc.keys()))
            u = dict_calc[droga]["unidad"]
            mgb = dict_calc[droga]["mg"]

            c1, c2 = st.columns(2)
            amps = c1.number_input("Ampollas", 0.0, 20.0, 1.0, 0.5)
            vol = c2.number_input("Volumen (ml)", 0.0, 500.0, 100.0)

            modo_c = st.radio("Calcular:", [f"Dosis ({u})", "ml/h"], horizontal=True)
            if "Dosis" in modo_c:
                vel = st.number_input("ml/h actuales", 0.0)
                res = calcular_infusion_universal("DOSIS", amps*mgb, vol, peso_paciente, vel, u)
                if st.button("➕ Anexar"):
                    st.session_state['infusiones_automatizadas'].append(f"{droga.split(' (')[0]}: {res:.4f} {u}")
                    st.rerun()
            else:
                dos = st.number_input(f"Dosis {u}", 0.0, format="%.4f")
                res = calcular_infusion_universal("VELOCIDAD", amps*mgb, vol, peso_paciente, dos, u)
                st.write(f"Bomba: {res:.2f} ml/h")
                if st.button("➕ Anexar", key="anex_vel"):
                    st.session_state['infusiones_automatizadas'].append(f"{droga.split(' (')[0]}: {dos:.4f} {u}")
                    st.rerun()

            if st.session_state['infusiones_automatizadas']:
                st.write("---")
                for i in st.session_state['infusiones_automatizadas']: st.caption(f"✅ {i}")
                if st.button("🗑️ Limpiar Infusiones"): st.session_state['infusiones_automatizadas'] = []; st.rerun()

    with st.container(border=True):
        st.subheader("Examen Físico")
        c1, c2, c3, c4 = st.columns(4)
        ta, fc, fr, sat = c1.text_input("TA"), c2.text_input("FC"), c3.text_input("FR"), c4.text_input("SatO2")
        temp, glasgow, rass = c1.text_input("Temp"), c2.text_input("GCS"), c3.text_input("RASS")
        ex_cv = st.text_input("CV", placeholder="R1R2 normofonéticos...")
        ex_resp = st.text_input("Resp", placeholder="Buena entrada de aire...")
        ex_abd = st.text_input("Abd", placeholder="RHA presentes...")
        ex_renal = st.text_input("Renal/Diuresis", placeholder="Ritmo diurético...")

with tab_lab:
    st.info("💡 Solo se plasmarán los campos que se completen.")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    ph, pco2, po2, hco3, eb, lac = c1.text_input("pH"), c2.text_input("pCO2"), c3.text_input("pO2"), c4.text_input("HCO3"), c5.text_input("EB"), c6.text_input("Lac")

    st.divider()
    l1, l2, l3, l4, l5, l6 = st.columns(6)
    gb, hto, plaq, urea, cr, gluc = l1.text_input("GB"), l2.text_input("Hto"), l3.text_input("Plaq"), l4.text_input("Urea"), l5.text_input("Cr"), l6.text_input("Gluc")
    na, k, cl, mg, ca = l1.text_input("Na"), l2.text_input("K"), l3.text_input("Cl"), l4.text_input("Mg"), l5.text_input("Ca")

with tab_estudios:
    ecg = st.text_area("ECG:", placeholder="Ritmo sinusal, FC...", height=100)
    rx = st.text_area("Imágenes (Rx/TC/Eco):", placeholder="Sin infiltrados...", height=100)

with tab_planes:
    analisis = st.text_area("Análisis (A):", height=150)
    plan = st.text_area("Plan (P):", height=150)

    st.divider()
    c_gen, c_lim = st.columns(2)
    if c_lim.button("🧹 LIMPIAR PLANILLA", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if c_gen.button("🚀 GENERAR EVOLUCIÓN", use_container_width=True, type="primary"):
        # --- Lógica de ensamblado (Omisión de vacíos) ---
        tf = [f"EVOLUCIÓN UTI - {hoy.strftime('%d/%m/%Y')}",
              f"Edad: {edad_paciente} | Peso: {peso_paciente}kg | Días UTI: {dias_int_uti}"]

        if subj: tf.append(f"\n(S): {subj}")

        obj = ["\n(O) OBJETIVO:"]
        if st.session_state['infusiones_automatizadas']:
            obj.append("Infusiones: " + " | ".join(st.session_state['infusiones_automatizadas']))

        sv = [f"TA {ta}" if ta else "", f"FC {fc}" if fc else "", f"FR {fr}" if fr else "", f"Sat {sat}" if sat else "", f"T {temp}" if temp else ""]
        sv = [s for s in sv if s]
        if sv: obj.append("SV: " + " | ".join(sv))

        if glasgow or rass: obj.append(f"Neuro: GCS {glasgow} RASS {rass}")
        if ex_cv: obj.append(f"CV: {ex_cv}")
        if ex_resp: obj.append(f"Resp: {ex_resp}")
        if ex_abd: obj.append(f"Abd: {ex_abd}")
        if ex_renal: obj.append(f"Renal: {ex_renal}")

        # Laboratorio con omisión inteligente
        labs = [f"pH {ph}" if ph else "", f"pCO2 {pco2}" if pco2 else "", f"pO2 {po2}" if po2 else "", f"Lac {lac}" if lac else "",
                f"GB {gb}" if gb else "", f"Hto {hto}" if hto else "", f"Plaq {plaq}" if plaq else "",
                f"Urea {urea}" if urea else "", f"Cr {cr}" if cr else ""]
        labs = [l for l in labs if l]
        if labs: obj.append("Laboratorio: " + " | ".join(labs))

        tf.extend(obj)

        if analisis: tf.append(f"\n(A): {analisis}")
        if plan: tf.append(f"\n(P): {plan}")

        st.subheader("Generar Evolución")
        st.code("\n".join(tf), language="markdown")
