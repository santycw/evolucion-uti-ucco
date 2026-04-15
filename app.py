import streamlit as st
import re
import json
import os
import datetime
import math
import requests

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

# --- INTEGRACIÓN NCBI E-UTILITIES (MeSH) ---
@st.cache_data(show_spinner=False)
def obtener_terminos_mesh(query):
    """Consulta la API de NCBI E-utilities para normalizar diagnósticos con MeSH."""
    try:
        # 1. Búsqueda en la base de datos MESH
        url_search = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=mesh&term={query}&retmode=json&retmax=3"
        res = requests.get(url_search, timeout=4).json()
        idlist = res.get("esearchresult", {}).get("idlist", [])

        if not idlist:
            # Reintento rápido asumiendo términos en inglés/traducidos por el motor de PubMed
            return []

        # 2. Resumen para obtener el nombre oficial del encabezado
        ids = ",".join(idlist)
        url_summary = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=mesh&id={ids}&retmode=json"
        sum_res = requests.get(url_summary, timeout=4).json()

        terminos = []
        for uid in idlist:
            nombre = sum_res.get("result", {}).get(uid, {}).get("ds_meshheading", "")
            if nombre:
                terminos.append(nombre)
        return terminos
    except Exception as e:
        return []

# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stTextArea textarea, .stTextInput input, .stNumberInput input { font-family: 'Consolas', monospace; font-size: 14px; }
    div[data-testid="stExpander"] { background-color: #1E1E1E !important; border-radius: 8px; border: 1px solid #333333; }
    div[data-testid="stExpander"] label, div[data-testid="stExpander"] p, div[data-testid="stExpander"] .stMarkdown { color: #F0F2F6 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("v4.9 | Motor NCBI E-utilities MeSH + Infusiones por Ampolla")

# --- PANEL LATERAL (DATOS GENERALES) ---
with st.sidebar:
    st.header("📌 Datos Generales")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", min_value=18, max_value=120, value=65, step=1)
        sexo_paciente = st.selectbox("Sexo (Para cálculos TFG)", ["Masculino", "Femenino"])
        peso_paciente = st.number_input("Peso Estimado (kg)", min_value=1.0, value=70.0, step=1.0)
        fecha_hosp = st.date_input("Fecha de Ingreso Institución", format="DD/MM/YYYY")
        fecha_uti = st.date_input("Fecha de ingreso UTI/UCCO", format="DD/MM/YYYY")
        dias_arm = st.text_input("Días ARM", placeholder="Ej: 0 o dejar vacío")

    st.header("📋 Diagnóstico de Ingreso")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos (Activan scores):", placeholder="1. Neumonia\n2. Sepsis...", height=120)

        # --- BOTÓN DE ANÁLISIS MESH ---
        if st.button("🌐 Analizar Diagnóstico con MeSH (NCBI)", use_container_width=True):
            lineas = [l.strip() for l in diagnostico.split('\n') if l.strip() and len(l) > 2]
            if lineas:
                st.markdown("---")
                st.markdown("📝 **Indexación MeSH Oficial:**")
                with st.spinner("Conectando con servidores del NLM/NCBI..."):
                    for linea in lineas:
                        # Limpiar viñetas y números para la búsqueda
                        q_limpio = re.sub(r'^[\d\.\-\*]+\s*', '', linea).strip()
                        mesh_terms = obtener_terminos_mesh(q_limpio)
                        if mesh_terms:
                            st.success(f"**{q_limpio}** ➔ {', '.join(mesh_terms)}")
                        else:
                            st.warning(f"**{q_limpio}** ➔ Sin match exacto (Intente términos médicos en inglés).")

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days
paciente_ventilado = bool(dias_arm.strip().lower() and dias_arm.strip().lower() not in ["0", "-", "no"])

# --- CONEXIÓN A BASE DE DATOS LOCAL (Fallback offline para scores) ---
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
    st.caption("Si deja en blanco scores predictivos, el sistema intentará calcularlos automáticamente leyendo Laboratorio y Signos Vitales.")
    if is_isquemia:
        with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=True):
            killip = st.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
            st.caption("Factores para Score TIMI:")
            timi_crit = st.multiselect("Criterios presentes:", ["AAS en últimos 7 días", "≥ 3 FR Cardiovasculares", "Enf. Coronaria conocida (Est. > 50%)", "Angina Severa (≥ 2 epi en 24h)", "Desviación ST ≥ 0.5mm", "Marcadores Cardíacos Positivos"])
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
            st.caption("APACHE II: Se calculará la fisiología aguda automáticamente.")
            apache_cro = st.selectbox("APACHE II - Salud Crónica", ["Ninguna", "Inmunosupresión", "Cirrosis/Falla Hepática", "Falla CV severa (NYHA IV)", "EPOC Severo", "Diálisis crónica"])
            apache_tipo = st.radio("Ingreso:", ["Médico / Quirúrgico Urgente", "Quirúrgico Electivo"], horizontal=True)
            s1, s2 = st.columns(2)
            qsofa = s1.text_input("qSOFA (Dejar vacío para auto-calc)")
            sofa = s2.text_input("SOFA (Dejar vacío para auto-calc)")
    if is_renal:
        with st.expander("🩸 Nefrología", expanded=True):
            st.caption("La TFG se calculará automáticamente mediante CKD-EPI y MDRD4 si ingresa Creatinina.")
            ren1, ren2 = st.columns(2)
            kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
            kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"])
    if is_hepato:
        with st.expander("🟡 Hepatopatía", expanded=True):
            st.caption("MELD y Child-Pugh se calcularán integrando el laboratorio.")
            hp1, hp2 = st.columns(2)
            cp_ascitis = hp1.selectbox("Grado Ascitis", ["Ausente", "Leve/Moderada", "Tensión/Refractaria"])
            cp_encef = hp2.selectbox("Grado Encefalopatía", ["Ninguna", "Grado I - II", "Grado III - IV"])
    if is_pancreas:
        with st.expander("⚕️ Pancreatitis Aguda", expanded=True):
            st.caption("Ranson se estimará al ingreso si se completan Leucocitos, LDH, GOT y Glucosa.")
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
            curb65 = n1.text_input("CURB-65 (Dejar vacío para auto-calc)")
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
        subj = st.text_area("Novedades:", placeholder="Paciente refiere...", height=68)

    with st.container(border=True):
        st.subheader("💊 Infusiones y Dispositivos")
        with st.expander("🧮 Calculadora de Infusiones (Por Ampolla)", expanded=True):
            dict_calc_drogas = {
                "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
                "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0},
                "Vasopresina (20 UI)": {"unidad": "UI/min", "mg": 20.0},
                "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0},
                "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0},
                "Milrinona (10 mg)": {"unidad": "mcg/kg/min", "mg": 10.0},
                "Levosimendán (12.5 mg)": {"unidad": "mcg/kg/min", "mg": 12.5},
                "Isoproterenol (1 mg)": {"unidad": "mcg/min", "mg": 1.0},
                "Nitroprusiato (50 mg)": {"unidad": "mcg/kg/min", "mg": 50.0},
                "Nitroglicerina (25 mg)": {"unidad": "mcg/min", "mg": 25.0},
                "Nitroglicerina (50 mg)": {"unidad": "mcg/min", "mg": 50.0},
                "Labetalol (20 mg)": {"unidad": "mg/min", "mg": 20.0},
                "Labetalol (100 mg)": {"unidad": "mg/min", "mg": 100.0},
                "Fentanilo (250 mcg = 0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25},
                "Remifentanilo (2 mg)": {"unidad": "mcg/kg/h", "mg": 2.0},
                "Remifentanilo (5 mg)": {"unidad": "mcg/kg/h", "mg": 5.0},
                "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0},
                "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0},
                "Midazolam (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
                "Dexmedetomidina (200 mcg = 0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2},
                "Morfina (10 mg)": {"unidad": "mg/h", "mg": 10.0},
                "Atracurio (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
                "Atracurio (25 mg)": {"unidad": "mg/kg/h", "mg": 25.0},
                "Rocuronio (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
                "Vecuronio (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
                "Pancuronio (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0}
            }

            droga_sel = st.selectbox("Fármaco y Presentación:", list(dict_calc_drogas.keys()))
            unidad_activa = dict_calc_drogas[droga_sel]["unidad"]
            mg_base = dict_calc_drogas[droga_sel]["mg"]

            c_calc1, c_calc2 = st.columns(2)
            cant_ampollas = c_calc1.number_input("Cant. Ampollas/Frascos en la dilución", min_value=0.0, value=1.0, step=0.5)
            volumen_ml = c_calc2.number_input("Volumen Total de la Dilución (ml)", min_value=0.0, value=100.0, step=10.0)

            droga_mg_total = cant_ampollas * mg_base
            st.caption(f"💡 Dosis total calculada en la solución: **{droga_mg_total} mg (o UI)**")

            calc_modo = st.radio("Cálculo:", [f"Dosis ({unidad_activa})", "Velocidad (ml/h)"], horizontal=True)
            nombre_limpio = droga_sel.split(" (")[0]

            if "Dosis" in calc_modo:
                vel_mlh = st.number_input("Velocidad actual en bomba (ml/h)", min_value=0.0)
                if droga_mg_total > 0 and volumen_ml > 0:
                    res = calcular_infusion_universal("DOSIS", droga_mg_total, volumen_ml, peso_paciente, vel_mlh, unidad_activa)
                    st.success(f"Resultado: {res:.4f} {unidad_activa}")
                    if st.button(f"➕ Anexar {nombre_limpio}", type="secondary"):
                        st.session_state['infusiones_automatizadas'].append(f"{nombre_limpio}: {res:.4f} {unidad_activa}")
                        st.rerun()
            else:
                dosis_obj = st.number_input(f"Dosis indicada ({unidad_activa})", min_value=0.0, format="%.4f")
                if droga_mg_total > 0 and volumen_ml > 0:
                    res = calcular_infusion_universal("VELOCIDAD", droga_mg_total, volumen_ml, peso_paciente, dosis_obj, unidad_activa)
                    st.success(f"Bomba: {res:.2f} ml/h")
                    if st.button(f"➕ Anexar {nombre_limpio}", type="secondary"):
                        st.session_state['infusiones_automatizadas'].append(f"{nombre_limpio}: {dosis_obj:.4f} {unidad_activa}")
                        st.rerun()

            if st.session_state['infusiones_automatizadas']:
                st.markdown("---")
                for inf in st.session_state['infusiones_automatizadas']: st.markdown(f"- `{inf}`")
                if st.button("🗑️ Borrar memoria", key="borrar_infusiones"):
                    st.session_state['infusiones_automatizadas'] = []
                    st.rerun()

        d1, d2, d3, d4 = st.columns(4)
        cvc_info, ca_info, sv_dias, sng_dias = d1.text_input("CVC (Día)", placeholder="Ej: Subclavia D (D2)"), d2.text_input("Cat. Art (Día)"), d3.text_input("SV (Día)"), d4.text_input("SNG (Día)")

    with st.container(border=True):
        st.subheader("1. Neurológico y Hemodinamia")
        n1, n2, n3, n4 = st.columns(4)
        neuro_estado, glasgow, rass, cam = n1.text_input("Estado", placeholder="Ej: Alerta"), n2.text_input("GCS", placeholder="Ej: 15"), n3.text_input("RASS", placeholder="Ej: 0"), n4.text_input("CAM", placeholder="Ej: Negativo")
        h1, h2, h3, h4, h5 = st.columns(5)

        ta, fc, fr, sat, temp = h1.text_input("TA", placeholder="120/80"), h2.text_input("FC (lpm)", key="fc_sv"), h3.text_input("FR"), h4.text_input("Sat (%)"), h5.text_input("Temp (°C)")

        tam_val, pp_val = "", ""
        if "/" in ta:
            try:
                s_bp, d_bp = map(float, ta.split("/"))
                tam_val = round((s_bp + 2*d_bp)/3)
                pp_val = int(s_bp - d_bp)
            except: pass

        v1, v2 = st.columns(2)
        pvc = v1.text_input("PVC (cmH2O)")
        relleno_cap = v2.text_input("Relleno Capilar", placeholder="Ej: < 2 seg")
        ex_cv = st.text_area("Ex. Cardiovascular", placeholder="Ej: R1/R2 normofonéticos. Sin soplos.")

    with st.container(border=True):
        st.subheader("2. Respiratorio y ARM")
        r_b1, r_b2, r_b3 = st.columns(3)
        via_aerea = r_b1.text_input("Vía Aérea", placeholder="Ej: TOT") if paciente_ventilado else r_b1.selectbox("Dispositivo O2", ["", "AA (Aire Ambiente)", "Cánula Nasal", "Máscara Reservorio", "CAF", "VNI", "TQTAA"])
        fio2 = r_b2.number_input("FiO2 (%)", min_value=21, max_value=100, value=21)
        pafi_manual = r_b3.text_input("PaFiO2 (Opcional)")

        modo = peep = ppico = pplat = comp = vt = dp_manual = ""
        if paciente_ventilado:
            st.info("⚙️ Consola de Mecánica Respiratoria Activa")
            r1, r2, r3, r4 = st.columns(4)
            modo, peep, vt, dp_manual = r1.text_input("Modo", placeholder="Ej: VCV"), r2.number_input("PEEP", 0, 30, 5), r3.text_input("Vt (ml)"), r4.text_input("Driving P.")
            r5, r6, r7 = st.columns(3)
            ppico, pplat, comp = r5.text_input("P.Pico"), r6.text_input("P.Plateau"), r7.text_input("Comp.")

        ex_resp = st.text_input("Examen Respiratorio", placeholder="Ej: Buena entrada de aire bilateral.")

    with st.container(border=True):
        st.subheader("3. Digestivo y Nutrición")
        a1, a2 = st.columns(2)
        ex_abd, nutricion = a1.text_input("Abdomen", placeholder="Ej: Blando, depresible."), a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"])

    with st.container(border=True):
        st.subheader("4. Renal y Balance Hídrico")
        ex_renal = st.text_input("Diuresis / Ex. Renal", placeholder="Ej: Ritmo diurético conservado.")
        bh1, bh2 = st.columns(2)
        ingresos, egresos = bh1.text_input("Ingresos Totales (ml)"), bh2.text_input("Egresos Totales (ml)")

    with st.container(border=True):
        st.subheader("5. Infectología")
        tmax = st.text_input("Temp. Máxima 24h (°C)")

        at1, at2, at3, at4 = st.columns(4)
        atb1 = at1.text_input("ATB 1 y Día")
        atb2 = at2.text_input("ATB 2 y Día")
        atb3 = at3.text_input("ATB 3 y Día")
        atb4 = at4.text_input("ATB 4 y Día")

        c_1, c_2, c_3, c_4 = st.columns(4)
        cult_hemo, cult_uro, cult_resp, cult_otros = c_1.text_input("Hemocultivos"), c_2.text_input("Urocultivo"), c_3.text_input("Respiratorios"), c_4.text_input("Otros", key="otros_cult")

with tab_lab:
    st.info("💡 Solo se imprimirán los valores completados.")
    with st.container(border=True):
        st.subheader("🌬️ EAB (Estado Ácido-Base)")
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        ph, pco2, po2, hco3, eb, lactato = e1.text_input("pH"), e2.text_input("pCO2"), e3.text_input("pO2"), e4.text_input("HCO3"), e5.text_input("EB"), e6.text_input("Lac")

    with st.container(border=True):
        st.subheader("🩸 Hemograma y Coagulación")
        l1, l2, l3, l4 = st.columns(4)
        hb, hto, gb, plaq = l1.text_input("Hb (g/dL)"), l2.text_input("Hto (%)"), l3.text_input("GB (/mm³ o mil)"), l4.text_input("Plaquetas")
        f1, f2, f3, f4 = st.columns(4)
        neut, linf, mono, eos = f1.text_input("Neut %"), f2.text_input("Linf %"), f3.text_input("Mono %"), f4.text_input("Eos %")
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
        b1, b2, b3, b4, b5, b6 = st.columns(6)
        cpk, cpkmb, tropo, bnp, ldh, pct = b1.text_input("CPK"), b2.text_input("CK-MB"), b3.text_input("Tropo I"), b4.text_input("proBNP"), b5.text_input("LDH"), b6.text_input("PCT")

with tab_estudios:
    with st.container(border=True):
        st.subheader("📊 Electrocardiograma (ECG)")
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        ecg_fc, ecg_ritmo, ecg_eje, ecg_onda_p, ecg_long_p = ec1.text_input("FC (lpm)", key="fc_ecg"), ec2.text_input("Ritmo"), ec3.text_input("Eje (°)"), ec4.text_input("Onda P"), ec5.text_input("Long. P (ms)")
        ec6, ec7, ec8, ec9, ec10 = st.columns(5)
        ecg_pr, ecg_qrs, ecg_qt = ec6.text_input("PR (ms)"), ec7.text_input("QRS (ms)"), ec8.text_input("QT (ms)")

        qtc_sug = ""
        f_val_target = ecg_fc.strip() if ecg_fc.strip() else fc.strip()
        if ecg_qt.strip() and f_val_target:
            try: qtc_sug = str(int(float(ecg_qt.replace(',', '.')) / ((60/float(f_val_target.replace(',', '.')))**0.5)))
            except: pass

        ecg_qtc, ecg_st, ecg_otros = ec9.text_input("QTc (ms)", value=qtc_sug), ec10.text_input("Segmento ST"), st.text_input("Otros hallazgos ECG")

    with st.container(border=True):
        st.subheader("🩻 Imágenes y Procedimientos")
        rx_torax, tc, eco, otros_estudios = st.text_area("Rx Tórax", height=68), st.text_area("TC", height=68), st.text_area("POCUS", height=68), st.text_area("Otros", height=68, key="otros_img")

with tab_planes:
    with st.container(border=True):
        st.subheader("🛡️ FAST HUG BID")
        fast_dict = {'F': 'Feeding', 'A': 'Analgesia', 'S': 'Sedación', 'T': 'Tromboprofilaxis', 'H': 'Head 30°', 'U': 'Úlceras estrés', 'G': 'Glucemia', 'B': 'Bowel', 'I': 'Invasiones', 'D': 'Desescalar ATB'}
        f_cols = st.columns(5)
        fast_sel = [f"{l} - {d}" for i, (l, d) in enumerate(fast_dict.items()) if f_cols[i % 5].checkbox(l, help=d)]

    with st.container(border=True):
        st.subheader("(A/P) Análisis y Plan")
        analisis, plan = st.text_area("Análisis General", placeholder="Escriba su análisis clínico aquí...", height=150), st.text_area("Plan 24hs", placeholder="Ej:\n- Cultivar\n- Interconsulta con...", height=150)

    st.divider()
    c_gen, c_lim = st.columns(2)

    btn_generar = c_gen.button("🚀 GENERAR EVOLUCIÓN", use_container_width=True, type="primary")
    if btn_generar: st.session_state['evolucion_generada'] = True

    if c_lim.button("🧹 LIMPIAR PLANILLA", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if btn_generar:
        # --- PARSEADORES DE DATOS ---
        def parse_num(val):
            try: return float(str(val).replace(',', '.').strip())
            except: return None

        cr_n, bt_n, plaq_n, urea_n, fr_n, fc_n = parse_num(cr), parse_num(bt), parse_num(plaq), parse_num(urea), parse_num(fr), parse_num(fc)
        temp_n, na_n, k_n, hto_n, rin_n, alb_n = parse_num(temp), parse_num(na), parse_num(potasio), parse_num(hto), parse_num(rin), parse_num(alb)
        gb_n, gluc_n, ldh_n, got_n, ph_n, po2_n = parse_num(gb), parse_num(gluc), parse_num(ldh), parse_num(got), parse_num(ph), parse_num(po2)

        sys_bp, dia_bp = 120, 80
        if "/" in ta:
            try: sys_bp, dia_bp = map(float, ta.split("/"))
            except: pass

        gl_val = 15
        try: gl_val = int(glasgow.split("/")[0]) if "/" in glasgow else int(glasgow)
        except: pass

        pafi_final = pafi_manual
        if not pafi_final and po2_n and fio2:
            try: pafi_final = str(int(po2_n / (fio2/100)))
            except: pass
        pafi_n = parse_num(pafi_final)

        # --- AUTO-CALCULOS SCORES ---
        clcr_str = ""
        if cr_n and cr_n > 0:
            factor_mdrd = 0.742 if sexo_paciente == "Femenino" else 1.0
            mdrd_val = 175 * (cr_n ** -1.154) * (edad_paciente ** -0.203) * factor_mdrd
            kappa = 0.7 if sexo_paciente == "Femenino" else 0.9
            alpha = -0.241 if sexo_paciente == "Femenino" else -0.302
            factor_ckd = 1.012 if sexo_paciente == "Femenino" else 1.0
            ckd_val = 142 * (min(cr_n/kappa, 1) ** alpha) * (max(cr_n/kappa, 1) ** -1.200) * (0.9938 ** edad_paciente) * factor_ckd
            clcr_str = f" | TFG: {mdrd_val:.1f} (MDRD4) - {ckd_val:.1f} (CKD-EPI) ml/min"

        if (is_sepsis and not sofa) or (not sofa and (pafi_n or cr_n or bt_n or plaq_n)):
            s_pts = 0
            if pafi_n:
                if pafi_n < 100 and paciente_ventilado: s_pts += 4
                elif pafi_n < 200 and paciente_ventilado: s_pts += 3
                elif pafi_n < 300: s_pts += 2
                elif pafi_n < 400: s_pts += 1
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
            cv_pts = 1 if tam_val and float(tam_val) < 70 else 0
            for inf in st.session_state['infusiones_automatizadas']:
                if "dobutamina" in inf.lower(): cv_pts = max(cv_pts, 2)
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
            sofa = f"{s_pts} (Auto)"

        if is_sepsis and not qsofa:
            q_calc = sum([gl_val < 15, fr_n and fr_n >= 22, sys_bp <= 100])
            qsofa = f"{q_calc} (Auto)"

        if is_nac and not curb65:
            c_calc = sum([gl_val < 15, urea_n and urea_n >= 42, fr_n and fr_n >= 30, sys_bp < 90 or dia_bp <= 60, edad_paciente >= 65])
            curb65 = f"{c_calc} (Auto)"

        if is_hepato and not meld and bt_n and cr_n and rin_n:
            b, c, r = max(1.0, bt_n), max(1.0, cr_n), max(1.0, rin_n)
            meld_score = 3.78 * math.log(b) + 11.2 * math.log(r) + 9.57 * math.log(c) + 6.43
            meld = f"{round(meld_score)} (Auto)"

        if is_hepato and not child and bt_n and alb_n and rin_n and cp_ascitis and cp_encef:
            cp_pts = sum([
                1 if bt_n < 2 else (2 if bt_n <= 3 else 3),
                1 if alb_n > 3.5 else (2 if alb_n >= 2.8 else 3),
                1 if rin_n < 1.7 else (2 if rin_n <= 2.2 else 3),
                1 if cp_ascitis == "Ausente" else (2 if cp_ascitis == "Leve/Moderada" else 3),
                1 if cp_encef == "Ninguna" else (2 if cp_encef == "Grado I - II" else 3)
            ])
            cp_clase = "A" if cp_pts <= 6 else ("B" if cp_pts <= 9 else "C")
            child = f"{cp_clase} ({cp_pts} pts) (Auto)"

        if is_isquemia and not timi and timi_crit is not None:
            timi = f"{len(timi_crit) + (1 if edad_paciente >= 65 else 0)}/7 (Auto)"

        if is_pancreas and not ranson:
            r_pts = sum([
                1 if edad_paciente > 55 else 0,
                1 if (gb_n * 1000 if gb_n and gb_n < 1000 else gb_n) > 16000 else 0,
                1 if gluc_n and gluc_n > 200 else 0,
                1 if ldh_n and ldh_n > 350 else 0,
                1 if got_n and got_n > 250 else 0
            ])
            ranson = f"{r_pts} (Auto Ingreso)"

        if is_sepsis and not apache:
            ap_pts = 0
            if temp_n: ap_pts += 4 if temp_n >= 41 or temp_n <= 29.9 else (3 if temp_n >= 39 or temp_n <= 31.9 else (2 if temp_n <= 33.9 else (1 if temp_n >= 38.5 or temp_n <= 35.9 else 0)))
            if tam_val and tam_val != "":
                tv = float(tam_val)
                ap_pts += 4 if tv >= 160 or tv <= 49 else (2 if tv >= 130 or tv <= 69 else (1 if tv >= 110 else 0))
            if fc_n: ap_pts += 4 if fc_n >= 180 or fc_n <= 39 else (3 if fc_n >= 140 or fc_n <= 54 else (2 if fc_n >= 110 or fc_n <= 69 else 0))
            if fr_n: ap_pts += 4 if fr_n >= 50 or fr_n <= 5 else (3 if fr_n >= 35 else (2 if fr_n <= 9 else (1 if fr_n >= 25 or fr_n <= 11 else 0)))
            if na_n: ap_pts += 4 if na_n >= 180 or na_n <= 110 else (3 if na_n >= 160 or na_n <= 119 else (2 if na_n >= 155 or na_n <= 129 else (1 if na_n >= 150 else 0)))
            if k_n: ap_pts += 4 if k_n >= 7.0 or k_n < 2.5 else (3 if k_n >= 6.0 else (2 if k_n <= 2.9 else (1 if k_n >= 5.5 or k_n <= 3.4 else 0)))
            if cr_n:
                cr_pts = 4 if cr_n >= 3.5 else (3 if cr_n >= 2.0 else (2 if cr_n >= 1.5 or cr_n < 0.6 else 0))
                ap_pts += (cr_pts * 2) if kdigo_ira and kdigo_ira != "" else cr_pts
            if gb_val := (gb_n * 1000 if gb_n and gb_n < 1000 else gb_n):
                ap_pts += 4 if gb_val >= 40000 or gb_val <= 999 else (2 if gb_val >= 20000 or gb_val <= 2999 else (1 if gb_val >= 15000 else 0))
            ap_pts += (15 - gl_val)
            ap_pts += 6 if edad_paciente >= 75 else (5 if edad_paciente >= 65 else (3 if edad_paciente >= 55 else (2 if edad_paciente >= 45 else 0)))
            if apache_cro and apache_cro != "Ninguna": ap_pts += 5 if apache_tipo == "Médico / Quirúrgico Urgente" else 2
            apache = f"{ap_pts} (Auto)"

        txt_mod = ""
        if is_isquemia and any([killip, grace, timi]): txt_mod += f"\n  • SCA/IAM -> Killip: {killip} | TIMI: {timi} | GRACE: {grace}"
        if is_ic and any([nyha, stevenson, aha_ic]): txt_mod += f"\n  • IC -> NYHA: {nyha} | Stevenson: {stevenson} | AHA: {aha_ic}"
        if is_sepsis and any([qsofa, sofa, apache]): txt_mod += f"\n  • SEPSIS -> qSOFA: {qsofa} | SOFA: {sofa} | APACHE II: {apache}"
        if is_renal and any([kdigo_ira, kdigo_erc, clcr_str]): txt_mod += f"\n  • NEFRO -> IRA: {kdigo_ira} | ERC: {kdigo_erc}{clcr_str}"
        if is_hepato and any([child, meld]): txt_mod += f"\n  • HEPATO -> Child-Pugh: {child} | MELD: {meld}"
        if is_pancreas and any([bisap, ranson, balthazar]): txt_mod += f"\n  • PANCREATITIS -> BISAP: {bisap} | Ranson: {ranson} | Balthazar: {balthazar}"
        if is_nac and any([curb65, psi]): txt_mod += f"\n  • NAC -> CURB-65: {curb65} | PSI: {psi}"

        # --- CONSTRUCCIÓN INTELIGENTE DE BLOQUES ---
        str_automatizadas = " | ".join(st.session_state['infusiones_automatizadas']) if st.session_state['infusiones_automatizadas'] else ""
        inv_list = [f"{k}: {v.strip()}" for k, v in [("CVC", cvc_info), ("Cat.Art", ca_info), ("SV", sv_dias), ("SNG", sng_dias)] if v.strip()]
        invasiones_str = "Invasiones: " + " | ".join(inv_list) if inv_list else ""

        sv_list = []
        if ta.strip(): sv_list.append(f"TA: {ta} mmHg")
        if tam_val != "": sv_list.append(f"TAM: {tam_val} mmHg")
        if pp_val != "": sv_list.append(f"PP: {pp_val} mmHg")
        if fc.strip(): sv_list.append(f"FC: {fc} lpm")
        if fr.strip(): sv_list.append(f"FR: {fr} rpm")
        if sat.strip(): sv_list.append(f"SatO2: {sat} %")
        if temp.strip(): sv_list.append(f"T°: {temp} °C")
        if pvc.strip(): sv_list.append(f"PVC: {pvc} cmH2O")
        if relleno_cap.strip(): sv_list.append(f"Rell. Capilar: {relleno_cap}")
        if fio2 and fio2 != 21: sv_list.append(f"FiO2: {fio2} %")
        signos_vitales = "- SIGNOS VITALES:\n  " + " | ".join(sv_list) if sv_list else ""

        neuro_items = [i for i in [neuro_estado, f"Glasgow {glasgow}" if glasgow.strip() else "", f"RASS {rass}" if rass.strip() else "", f"CAM {cam}" if cam.strip() else ""] if i]
        neuro_str = f"- NEURO: {', '.join(neuro_items)}." if neuro_items else ""

        cv_str = f"- CV: {ex_cv}" if ex_cv.strip() else ""
        abd_str = f"- ABD: {ex_abd}{f' | Nutrición: {nutricion}' if nutricion else ''}" if ex_abd.strip() or nutricion else ""

        balance_txt = ""
        if ingresos.strip() and egresos.strip():
            try: balance_txt = f" | Ingresos: {ingresos} ml / Egresos: {egresos} ml (Balance 24h: {parse_num(ingresos) - parse_num(egresos):+.0f} ml)"
            except: pass
        renal_str = f"- RENAL: {ex_renal}{balance_txt}" if ex_renal.strip() or balance_txt else ""

        resp_parts = []
        if paciente_ventilado:
            m_parts = [i for i in [f"P.Pico {ppico} cmH2O" if ppico.strip() else "", f"Comp {comp}" if comp.strip() else "", f"DP {dp_final}" if dp_final else "", f"PaFiO2 {pafi_final}" if pafi_final else ""] if i]
            mech_str = " | ".join(m_parts)

            r_txt = f"{via_aerea}" if via_aerea.strip() else "ARM"
            if modo.strip(): r_txt += f", Modo {modo}"
            if fio2: r_txt += f", FiO2 {fio2}%"
            if peep: r_txt += f", PEEP {peep} cmH2O"
            if pplat.strip(): r_txt += f", PPlat {pplat} cmH2O"
            if vt.strip(): r_txt += f", Vt {vt} ml"
            resp_parts.append(r_txt + ".")
            if mech_str: resp_parts.append(f"  Mecánica: {mech_str}.")
        else:
            if via_aerea.strip() or pafi_final:
                r_txt = f"Dispositivo: {via_aerea}" if via_aerea.strip() else "O2"
                if fio2 and fio2 != 21: r_txt += f" | FiO2 {fio2}%"
                if pafi_final: r_txt += f" | PaFiO2 {pafi_final}"
                resp_parts.append(r_txt + ".")

        if ex_resp.strip(): resp_parts.append(f"  Examen: {ex_resp}")
        texto_resp = "- RESP:\n  " + "\n  ".join(resp_parts) if resp_parts else ""

        # Infecto
        cultivos_list = [f"{n}: {v.strip()}" for n, v in [("Hemo", cult_hemo), ("Uro", cult_uro), ("Resp", cult_resp), ("Otros", cult_otros)] if v.strip()]
        atbs_activos = [a.strip() for a in [atb1, atb2, atb3, atb4] if a.strip()]

        infecto_parts = []
        if tmax.strip(): infecto_parts.append(f"Tmax 24h: {tmax.strip()}°C")
        if atbs_activos: infecto_parts.append("ATB: " + " / ".join(atbs_activos))
        if cultivos_list: infecto_parts.append("Cultivos: " + " | ".join(cultivos_list))
        bloque_infectologia = "\n>> INFECTOLOGÍA:\n" + "\n".join([f"- {p}" for p in infecto_parts]) if infecto_parts else ""

        # Laboratorio
        def line_lab(items):
            v = [f"{n} {val} {u}".strip() for n, val, u in items if val.strip()]
            return " | ".join(v) if v else ""

        gb_f = f"{gb}".strip() if gb.strip() else ""
        if gb_f and any([neut.strip(), linf.strip(), mono.strip(), eos.strip()]):
            gb_f += f" (N:{neut}% L:{linf}% M:{mono}% E:{eos}%)"

        lab_b = [l for l in [
            line_lab([("pH", ph, ""), ("pCO2", pco2, "mmHg"), ("pO2", po2, "mmHg"), ("HCO3", hco3, "mEq/L"), ("EB", eb, "mEq/L"), ("Lac", lactato, "mmol/L")]),
            line_lab([("Hb", hb, "g/dL"), ("Hto", hto, "%"), ("GB", gb_f, ""), ("Plaq", plaq, "")]),
            line_lab([("APP", app, "%"), ("KPTT", kptt, "s"), ("RIN", rin, "")]),
            line_lab([("Urea", urea, "mg/dL"), ("Cr", cr, "mg/dL"), ("Gluc", gluc, "mg/dL"), ("Na", na, "mEq/L"), ("K", potasio, "mEq/L"), ("Cl", cl, "mEq/L"), ("Mg", mg, "mg/dL"), ("Ca", ca, "mg/dL"), ("P", phos, "mg/dL")]),
            line_lab([("BT", bt, "mg/dL"), ("BD", bd, "mg/dL"), ("GOT", got, "UI/L"), ("GPT", gpt, "UI/L"), ("FAL", fal, "UI/L"), ("GGT", ggt, "UI/L"), ("PT", pt, "g/dL"), ("Alb", alb, "g/dL")]),
            line_lab([("CPK", cpk, "UI/L"), ("CK-MB", cpkmb, "UI/L"), ("Tropo I", tropo, "ng/mL"), ("proBNP", bnp, "pg/mL"), ("LDH", ldh, "UI/L"), ("PCT", pct, "ng/mL")])
        ] if l]
        texto_laboratorio = "\n".join(lab_b) if lab_b else ""

        # Estudios
        ecg_val = [f"{n} {v}{u}".strip() for n, v, u in [("FC", ecg_fc, "lpm"), ("Ritmo", ecg_ritmo, ""), ("Onda P", ecg_onda_p, ""), ("Long. P", ecg_long_p, "ms"), ("Eje", ecg_eje, "°"), ("PR", ecg_pr, "ms"), ("QRS", ecg_qrs, "ms")] if v.strip()]
        if ecg_qt.strip() or ecg_qtc.strip(): ecg_val.append(f"QT/QTc {ecg_qt.strip() if ecg_qt.strip() else '-'}/{ecg_qtc.strip() if ecg_qtc.strip() else '-'} ms")
        if ecg_st.strip(): ecg_val.append(f"ST {ecg_st.strip()}")
        if ecg_otros.strip(): ecg_val.append(ecg_otros.strip())

        est_list = [f"- {n}: {v.strip()}" for n, v in [("ECG", " | ".join(ecg_val)), ("Rx", rx_torax), ("TC", tc), ("POCUS", eco), ("Otros Estudios", otros_estudios)] if v.strip() and v.strip() != " | ".join(ecg_val)]
        if ecg_val: est_list.insert(0, f"- ECG: {' | '.join(ecg_val)}")
        bloque_estudios = "\n>> ECG Y ESTUDIOS COMPLEMENTARIOS:\n" + "\n".join(est_list) if est_list else ""

        # --- ENSAMBLAJE FINAL DINÁMICO ---
        tf = [
            "EVOLUCIÓN UTI / UCCO",
            f"Datos Generales: Edad: {edad_paciente} años | Peso Estimado: {peso_paciente} kg | Sexo: {sexo_paciente}",
            f"Días Hosp: {dias_int_hosp} | Días UTI: {dias_int_uti}" + (f" | Días ARM: {dias_arm.strip()}" if dias_arm.strip() else "")
        ]

        if subj.strip(): tf.extend(["\n(S) SUBJETIVO:", subj.strip()])

        tf.append("\n(O) OBJETIVO:")
        if str_automatizadas or invasiones_str:
            tf.append(">> INFUSIONES Y DISPOSITIVOS:")
            if str_automatizadas: tf.append(f"Infusiones Activas: {str_automatizadas}")
            if invasiones_str: tf.append(invasiones_str)

        b_fisico = [p for p in [signos_vitales, neuro_str, cv_str, texto_resp, abd_str, renal_str] if p]
        if b_fisico:
            tf.append("\n>> EXAMEN FÍSICO Y SIGNOS VITALES:")
            tf.extend(b_fisico)

        if bloque_infectologia: tf.append(bloque_infectologia)
        if texto_laboratorio: tf.extend(["\n>> LABORATORIO Y MEDIO INTERNO:", texto_laboratorio])
        if bloque_estudios: tf.append(bloque_estudios)
        if fast_sel: tf.extend(["\n>> FAST HUG BID:", "\n".join([f"  ✓ {l}" for l in fast_sel])])

        tf.append("\n(A) ASSESSMENT / ANÁLISIS:")
        if diagnostico.strip(): tf.extend([">> DIAGNÓSTICOS ACTIVOS:", diagnostico.strip()])
        if txt_mod.strip(): tf.extend([">> SCORES DE GRAVEDAD Y PRONÓSTICO:", txt_mod.strip()])
        if analisis.strip(): tf.extend(["\n>> ANÁLISIS CLÍNICO:", analisis.strip()])

        if plan.strip(): tf.extend(["\n(P) PLAN 24HS:", plan.strip()])

        texto_final = "\n".join(tf)
        st.success("✅ Evolución generada con éxito. Lista para exportar a GECLISA.")
        st.code(texto_final, language="markdown")
