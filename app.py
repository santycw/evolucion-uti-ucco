import streamlit as st
import re
import json
import os
import datetime
import math
import streamlit.components.v1 as components

# --- INICIALIZACIÓN DE ESTADOS DE SESIÓN ---
if 'evolucion_generada' not in st.session_state:
    st.session_state['evolucion_generada'] = False
if 'infusiones_automatizadas' not in st.session_state:
    st.session_state['infusiones_automatizadas'] = []
if 'tema_oscuro' not in st.session_state:
    st.session_state['tema_oscuro'] = True # Por defecto oscuro

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

# --- CSS PERSONALIZADO Y BADGES ---
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
    .metric-card {
        padding: 10px; border-radius: 8px; color: white; font-weight: bold; text-align: center; font-size: 1.1em;
    }
    .bg-green { background-color: #2e7d32; }
    .bg-yellow { background-color: #f9a825; color: black !important; }
    .bg-red { background-color: #c62828; }
    .badge {
        display: inline-block; padding: 0.25em 0.6em; font-size: 85%; font-weight: 700;
        line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: 0.5rem;
        color: white; margin-left: 5px;
    }
    .tooltip {
        position: relative; display: inline-block; border-bottom: 1px dotted white; cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden; width: 220px; background-color: #555; color: #fff; text-align: center;
        border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%;
        margin-left: -110px; opacity: 0; transition: opacity 0.3s; font-size: 12px; font-weight: normal;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Panel de Alertas Inteligentes | Lab Crítico | Badges Dinámicos")

# --- PLACEHOLDER PARA HEADER DE VITALES ---
vitals_header_placeholder = st.empty()

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
        diagnostico = st.text_area("Diagnósticos (Escriba 'FA' para activar score):", "1. \n2. ", height=120)

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days
d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- LÓGICA DE DICCIONARIO ---
apache_cronico = 0
apache_ira = False
child_encef = "Ausente"
child_ascitis = "Ausente"
albumina = 0.0
meld_dialisis = False
bisap_derrame = False

sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""
chf = hta = diabetes = stroke_fa = vascular = False

@st.cache_data
def cargar_diccionario_medico():
    ruta_db = "diccionario.json"
    fallback_db = {
        "isquemia": ["sca", "scacest", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina"],
        "ic": ["ic", "ica", "icc", "insuficiencia cardiaca", "falla cardiaca", "eap", "cor pulmonale"],
        "sepsis": ["sepsis", "septic", "shock", "sirs", "bacteriemia", "vasoplegia", "falla multiorganica"],
        "renal": ["ira", "aki", "insuficiencia renal", "falla renal", "erc", "nefropatia"],
        "hepato": ["cirrosis", "hepatopatia", "falla hepatica", "dcl", "hepatitis", "encefalopatia"],
        "pancreas": ["pancreatitis", "pa", "necrosis pancreatica"],
        "acv": ["acv", "ictus", "stroke", "isquemico", "hemorragico", "ait", "tia"],
        "hsa": ["hsa", "hemorragia subaracnoidea", "aneurisma"],
        "nac": ["nac", "neumonia", "pulmonia", "bronconeumonia", "nih"],
        "fa": ["fa", "fibrilacion", "fibrilacion auricular", "af", "auricular fibrillation"]
    }
    return fallback_db

db_terminologia = cargar_diccionario_medico()
diag_norm = diagnostico.lower().replace('.', '').replace(',', ' ')
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
is_fa = detectar_en_db("fa", diag_norm)

# --- RECOLECCIÓN DE DATOS PARA SCORES ---
if any([is_isquemia, is_ic, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_fa]):
    st.markdown("### ⚙️ Complemento de Scores")

if is_isquemia:
    with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=False):
        killip = st.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
if is_ic:
    with st.expander("🫀 Insuficiencia Cardíaca", expanded=False):
        nyha = st.selectbox("Clase NYHA", ["", "I", "II", "III", "IV"])
if is_sepsis:
    with st.expander("🦠 Sepsis (APACHE II / SOFA)", expanded=False):
        apache_cronico = st.selectbox("Puntaje Enf. Crónica (APACHE)", [0, 2, 5])
        apache_ira = st.checkbox("Falla Renal Aguda (Duplica pts de Cr)")
if is_renal:
    with st.expander("🩸 Nefrología", expanded=False):
        kdigo_ira = st.selectbox("KDIGO (IRA)", ["", "1", "2", "3"])
if is_hepato:
    with st.expander("🟡 Hepatopatía (Child-Pugh / MELD)", expanded=False):
        child_encef = st.selectbox("Encefalopatía", ["Ausente", "Grado I-II", "Grado III-IV"])
        child_ascitis = st.selectbox("Ascitis", ["Ausente", "Leve/Moderada", "Severa/Refractaria"])
        albumina = st.number_input("Albúmina (g/dL) para Score", min_value=0.0, value=0.0, step=0.1)
        meld_dialisis = st.checkbox("Paciente en Diálisis")
if is_pancreas:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=False):
        bisap_derrame = st.checkbox("Presencia de Derrame Pleural")
if is_fa:
    with st.expander("🫀 Fibrilación Auricular (CHA₂DS₂-VA | ESC 2024)", expanded=True):
        fa1, fa2 = st.columns(2)
        chf = fa1.checkbox("Insuf. Cardíaca / Disfunción VI (C)")
        hta = fa1.checkbox("Hipertensión Arterial (H)")
        diabetes = fa1.checkbox("Diabetes Mellitus (D)")
        stroke_fa = fa2.checkbox("ACV / TIA previo (S₂)")
        vascular = fa2.checkbox("Enfermedad Vascular (V)")

st.divider()

# --- INPUTS PRINCIPALES ---
tab_clinca, tab_lab, tab_estudios, tab_planes = st.tabs([
    "🩺 Clínica y Examen", "🧪 Laboratorio Integral", "🩻 ECG y Estudios", "📋 Plan y FAST-HUG"
])

with tab_clinca:
    with st.container(border=True):
        st.subheader("(S) Subjetivo")
        subj = st.text_area("Novedades:", "Paciente estable, sin intercurrencias agudas.", height=68)

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

        v1, v2 = st.columns(2)
        pvc = v1.text_input("PVC (cmH2O)")
        relleno_cap = v2.text_input("Relleno Capilar", "< 2 seg")
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
        st.subheader("3. Digestivo, Renal y Balance")
        a1, a2, a3 = st.columns(3)
        ex_abd = a1.text_input("Abdomen", "Blando, depresible.")
        nutricion = a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"])
        ex_renal = a3.text_input("Diuresis", "Conservada.")

        bh1, bh2 = st.columns(2)
        ingresos = bh1.text_input("Ingresos (ml)")
        egresos = bh2.text_input("Egresos (ml)")

with tab_lab:
    with st.container(border=True):
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        ph = e1.text_input("pH")
        pco2 = e2.text_input("pCO2")
        po2 = e3.text_input("pO2")
        hco3 = e4.text_input("HCO3")
        eb = e5.text_input("EB")
        lactato = e6.text_input("Lac")

        l1, l2, l3, l4 = st.columns(4)
        hb = l1.text_input("Hb")
        hto = l2.text_input("Hto")
        gb = l3.text_input("GB")
        plaq = l4.text_input("Plaq")

        q1, q2, q3, q4, q5, q6 = st.columns(6)
        urea = q1.text_input("Urea")
        cr = q2.text_input("Cr")
        gluc = q3.text_input("Gluc")
        na = q4.text_input("Na")
        potasio = q5.text_input("K")
        cl = q6.text_input("Cl")

        he1, he2, he3 = st.columns(3)
        bt = he1.text_input("BT")
        rin = he2.text_input("RIN")
        albumina_lab = he3.text_input("Albúmina")

with tab_estudios:
    with st.container(border=True):
        e_col0, e_col1, e_col2 = st.columns(3)
        ecg_fc = e_col0.text_input("FC ECG (lpm)")
        ecg_qt = e_col1.text_input("QT (ms)")
        ecg_conclusiones = st.text_area("Conclusiones ECG", height=68)

def p_num(val):
    try: return float(str(val).replace(',', '.').strip())
    except: return None

sys_bp, dia_bp, tam_val = None, None, ""
if ta and "/" in ta:
    try:
        sys_bp = float(ta.split("/")[0])
        dia_bp = float(ta.split("/")[1])
        tam_val = round((sys_bp + 2*dia_bp)/3)
    except: pass

gl_val = 15
if glasgow:
    try: gl_val = int(glasgow.split("/")[0])
    except: pass

pafi_val = p_num(pafi_manual)
po2_n = p_num(po2)
if not pafi_val and po2_n and fio2: pafi_val = float(int(po2_n / (fio2/100)))

plaq_n = p_num(plaq)
bt_n = p_num(bt)
cr_n = p_num(cr)
fr_n = p_num(fr)
fc_n = p_num(fc)
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

# --- RUTINAS DE ALERTAS (PAFI, DP, QTC, BALANCE) ---
alertas_clinicas = []

pafi_final_str = f"{pafi_val:.0f}" if pafi_val else ""
if pafi_val:
    if pafi_val <= 100: pafi_final_str += " (SDRA Severo 🔴)"
    elif pafi_val <= 200: pafi_final_str += " (SDRA Mod 🟠)"
    elif pafi_val <= 300: pafi_final_str += " (SDRA Leve 🟡)"

dp_final = dp_manual
pplat_val = p_num(pplat)
if not dp_final and pplat_val and peep:
    try: dp_final = str(int(pplat_val - float(peep)))
    except: pass
if p_num(dp_final) and p_num(dp_final) > 15:
    alertas_clinicas.append("🔴 DP > 15 cmH2O (Riesgo VILI)")

qtc_val = None
qtc_ui_str = ""
if ecg_fc.strip() and ecg_qt.strip():
    try:
        f_ecg = p_num(ecg_fc)
        q_ecg = p_num(ecg_qt)
        if f_ecg > 0:
            qtc_val = q_ecg / math.sqrt(60.0 / f_ecg)
            qtc_ui_str = f"{qtc_val:.0f}"
            if qtc_val > 500: alertas_clinicas.append("🔴 QTc > 500ms (Riesgo Torsades)")
    except: pass

bal_str = ""
if ingresos and egresos:
    try:
        bal = float(ingresos.replace(',','.')) - float(egresos.replace(',','.'))
        if bal > 1500: bal_str = f"🔴 Balance muy positivo ({bal:+.0f} ml)"
        elif bal > 800: bal_str = f"🟡 Balance positivo ({bal:+.0f} ml)"
        else: bal_str = f"🟢 Balance ({bal:+.0f} ml)"
    except: pass

# --- CÁLCULO DE SCORES ---
s_pts = q_calc = apache_auto_pts = bisap_pts = chadva_score = 0

if pafi_val: s_pts += 4 if pafi_val<100 else 3 if pafi_val<200 else 2 if pafi_val<300 else 1
if cr_n: s_pts += 4 if cr_n>=5 else 3 if cr_n>=3.5 else 2 if cr_n>=2 else 1
if plaq_n: s_pts += 4 if plaq_n<20000 else 3 if plaq_n<50000 else 2 if plaq_n<100000 else 1
if bt_n: s_pts += 4 if bt_n>=12 else 3 if bt_n>=6 else 2 if bt_n>=2 else 1

q_calc = sum([gl_val < 15, fr_n is not None and fr_n >= 22, sys_bp is not None and sys_bp <= 100])
c_calc = sum([gl_val < 15, urea_n is not None and urea_n >= 42, fr_n is not None and fr_n >= 30, (sys_bp is not None and sys_bp < 90), edad_n >= 65])

if is_fa:
    if chf: chadva_score += 1
    if hta: chadva_score += 1
    if edad_n >= 75: chadva_score += 2
    elif 65 <= edad_n <= 74: chadva_score += 1
    if diabetes: chadva_score += 1
    if stroke_fa: chadva_score += 2
    if vascular: chadva_score += 1

# --- GENERADOR DE BADGES HTML ---
def get_badge(name, val, max_val, thresholds, tooltips):
    color = "bg-green"
    tt = tooltips[0]
    if val >= thresholds[2]: color = "bg-red"; tt = tooltips[3]
    elif val >= thresholds[1]: color = "bg-yellow"; tt = tooltips[2]
    elif val >= thresholds[0]: color = "bg-yellow"; tt = tooltips[1]

    return f"""<div class="tooltip badge {color}">{name}: {val}
               <span class="tooltiptext">{tt}</span></div>"""

scores_html = ""
if is_sepsis:
    scores_html += get_badge("SOFA", s_pts, 24, [4, 8, 12], ["Mortalidad <10%", "Mort ~20%", "Mort ~40%", "Mort >50%"])
    scores_html += get_badge("qSOFA", q_calc, 3, [1, 2, 3], ["Bajo riesgo", "Riesgo moderado", "Alto riesgo", "Alta mortalidad"])
if is_nac:
    scores_html += get_badge("CURB-65", c_calc, 5, [1, 2, 3], ["Ambulatorio", "Considerar Sala", "Ingreso UCI", "UCI Urgente"])
if is_fa:
    scores_html += get_badge("CHA₂DS₂-VA", chadva_score, 8, [1, 2, 3], ["Bajo riesgo ACV", "Considerar ACO", "Indicación formal ACO", "Alto Riesgo ACO"])

# --- HEADER DE VITALES (LLENADO DEL PLACEHOLDER) ---
with vitals_header_placeholder.container():
    def val_color(val, lim_low, lim_high, crit_low, crit_high):
        if val is None: return "bg-green"
        if val <= crit_low or val >= crit_high: return "bg-red"
        if val <= lim_low or val >= lim_high: return "bg-yellow"
        return "bg-green"

    c_sys = val_color(sys_bp, 100, 160, 90, 180)
    c_fc = val_color(fc_n, 50, 100, 40, 130)
    c_fr = val_color(fr_n, 12, 24, 8, 30)
    sat_n = p_num(sat)
    c_sat = val_color(sat_n, 93, 100, 90, 100) if sat_n else "bg-green"
    c_temp = val_color(temp_n, 36.0, 38.0, 35.0, 39.5)

    v1, v2, v3, v4, v5 = st.columns(5)
    v1.markdown(f'<div class="metric-card {c_sys}">TA: {ta if ta else "--"}</div>', unsafe_allow_html=True)
    v2.markdown(f'<div class="metric-card {c_fc}">FC: {fc if fc else "--"}</div>', unsafe_allow_html=True)
    v3.markdown(f'<div class="metric-card {c_fr}">FR: {fr if fr else "--"}</div>', unsafe_allow_html=True)
    v4.markdown(f'<div class="metric-card {c_sat}">Sat: {sat if sat else "--"}%</div>', unsafe_allow_html=True)
    v5.markdown(f'<div class="metric-card {c_temp}">T°: {temp if temp else "--"}</div>', unsafe_allow_html=True)
    st.divider()

with tab_planes:
    st.markdown("### (A) Problemas Activos y Scores Inteligentes")
    if scores_html: st.markdown(scores_html, unsafe_allow_html=True)
    if alertas_clinicas:
        for alerta in alertas_clinicas: st.error(alerta)

    plan = st.text_area("Plan 24hs", "- Cultivar: \n- Interconsultas:", height=100)
    st.divider()

    col1, col2, col3 = st.columns(3)
    btn_generar = col1.button("🚀 Generar Evolución", use_container_width=True, type="primary")
    btn_limpiar = col2.button("🧹 Limpiar", use_container_width=True)

    if btn_limpiar:
        st.session_state.clear()
        st.rerun()

    if btn_generar:
        texto_resp = f"Vía: {via_aerea} | FiO2 {fio2}% | PaFiO2: {pafi_final_str}\nDP: {dp_final}\n{ex_resp}"

        texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Hosp: {dias_int_hosp} | Días UTI: {dias_int_uti} | Días ARM: {dias_arm}

DIAGNÓSTICO:
{diagnostico}

(S) SUBJETIVO: {subj}

(O) OBJETIVO:
- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}.
- HEMODINAMIA: TA {ta} | FC {fc} | PVC {pvc} | T° {temp}
- RESPIRATORIO: {texto_resp}
- ABD/RENAL: {ex_abd} | {ex_renal} | {bal_str}

(A) PROBLEMAS Y SCORES:
{plan}
"""
        st.success("✅ Evolución lista.")
        st.code(texto_final, language="markdown")

        # BOTÓN MAGICO DE IMPRESIÓN
        imprimir_html = f"""
        <script>
            function printEvolution() {{
                var printWindow = window.open('', '', 'height=600,width=800');
                printWindow.document.write('<html><head><title>Imprimir Evolución</title></head><body>');
                printWindow.document.write('<pre style="font-family: monospace; font-size: 14px;">{texto_final.replace(chr(10), '<br>')}</pre>');
                printWindow.document.write('</body></html>');
                printWindow.document.close();
                printWindow.print();
            }}
        </script>
        <button onclick="printEvolution()" style="background-color: #008CBA; color: white; padding: 10px 24px; border: none; border-radius: 4px; cursor: pointer;">🖨️ Imprimir Evolución</button>
        """
        components.html(imprimir_html, height=50)
