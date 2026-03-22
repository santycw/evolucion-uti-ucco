import streamlit as st
import re

# Configuración de estética y página
st.set_page_config(page_title="Evolución UTI/UCCO", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    stTextArea textarea { font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión Definitiva: Módulos Inteligentes + ARM Completo + ECG AHA")

# --- DATOS GENERALES (SIDEBAR) ---
with st.sidebar:
    st.header("📌 Datos de Base")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    st.divider()
    st.info("💡 Escribe palabras como 'Sepsis', 'IAM', o 'Pancreatitis' en el diagnóstico para activar los scores de gravedad automáticos.")

# --- INICIALIZACIÓN DE VARIABLES CONDICIONALES ---
sofa = apache = ""
killip = grace = timi = ""
bisap = ranson = balthazar = ""

# --- SECCIÓN DIAGNÓSTICO E INTELIGENCIA SEMÁNTICA ---
st.subheader("📋 Diagnóstico Principal")
diagnostico = st.text_area("Diagnósticos de Ingreso / Actuales:", "1. \n2. ")

# Normalización del texto para el análisis
diag_norm = diagnostico.lower()
diag_norm = re.sub(r'[áäâà]', 'a', diag_norm)
diag_norm = re.sub(r'[éëêè]', 'e', diag_norm)
diag_norm = re.sub(r'[íïîì]', 'i', diag_norm)
diag_norm = re.sub(r'[óöôò]', 'o', diag_norm)
diag_norm = re.sub(r'[úüûù]', 'u', diag_norm)

# Diccionarios de palabras clave
kw_cardio = ["scasest", "iam", "iamcest", "infarto", "angina", "angor", "coronario", "isquemia"]
kw_sepsis = ["sepsis", "septic", "infeccion", "neumonia", "itu", "meningitis", "peritonitis", "bacteriemia", "shock"]
kw_pancreatitis = ["pancreatitis"]

is_cardio = any(kw in diag_norm for kw in kw_cardio)
is_sepsis = any(kw in diag_norm for kw in kw_sepsis)
is_pancreatitis = any(kw in diag_norm for kw in kw_pancreatitis)

# --- RENDERIZADO DE MÓDULOS DINÁMICOS (SCORES) ---
if is_cardio or is_sepsis or is_pancreatitis:
    st.markdown("### ⚙️ Scores de Gravedad Activados")

if is_cardio:
    with st.expander("🫀 Estadificación Coronaria (SCASEST / IAM)", expanded=True):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (Estertores/R3)", "III (EAP)", "IV (Shock Cardiogénico)"])
        grace = c2.text_input("Score GRACE")
        timi = c3.text_input("Score TIMI (0-7)")

if is_sepsis:
    with st.expander("🦠 Scores de Sepsis", expanded=True):
        s1, s2 = st.columns(2)
        sofa = s1.text_input("SOFA Score")
        apache = s2.text_input("APACHE II")

if is_pancreatitis:
    with st.expander("⚕️ Estadificación Pancreática", expanded=True):
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP (0-5)")
        ranson = p2.text_input("Criterios de Ranson")
        balthazar = p3.selectbox("Balthazar (TC)", ["", "A (Normal)", "B (Agrandamiento)", "C (Inflamación)", "D (1 Colección)", "E (≥2 Colecciones / Gas)"])

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Examen Físico / Clínica", "🧪 Laboratorio y EAB", "📋 FAST HUG y Plan Final"])

with tab_clinca:
    st.subheader("(S) Subjetivo")
    subj = st.text_area("Novedades y Subjetivo:", "Paciente estable, sin cambios agudos.")

    # INFUSIONES Y DROGAS (Devueltas a la Pestaña Principal)
    st.subheader("💊 Infusiones y Drogas")
    i1, i2 = st.columns(2)
    sedo = i1.text_area("Sedoanalgesia", "Fentanilo: \nPropofol: \nMidazolam: \nBloq NM:")
    vaso = i2.text_area("Vasoactivos", "Noradrenalina: \nVasopresina: \nDobutamina: \nAdrenalina:")

    st.subheader("💉 Dispositivos e Invasiones")
    d1, d2, d3, d4 = st.columns(4)
    cvc_info = d1.text_input("CVC (Sitio/Día)")
    ca_info = d2.text_input("Cat. Art. (Sitio/Día)")
    sv_dias = d3.text_input("Sonda Vesical (Día)")
    sng_dias = d4.text_input("SNG (Día)")

    st.divider()

    # 1. NEUROLÓGICO
    st.subheader("1. Neurológico y Sedación")
    n1, n2, n3, n4 = st.columns(4)
    neuro_estado = n1.text_input("Estado", "Alerta")
    glasgow = n2.text_input("Glasgow", "15/15")
    rass = n3.text_input("RASS", "0")
    cam = n4.text_input("CAM-ICU", "-")
    ex_neuro = st.text_area("Detalle Neuro", "Vigil, conectado, moviliza 4 miembros.")

    # 2. HEMODINAMIA Y ECG
    st.subheader("2. Signos Vitales y Hemodinamia")
    h1, h2, h3, h4, h5 = st.columns(5)
    ta = h1.text_input("TA (S/D)", placeholder="120/80")
    fc = h2.text_input("FC (lpm)")
    fr = h3.text_input("FR (rpm)")
    sat = h4.text_input("SatO2 (%)")
    temp = h5.text_input("Temp Actual (°C)")

    st.info("📊 Electrocardiograma (AHA/ACC/HRS)")
    e_col1, e_col2, e_col3, e_col4 = st.columns(4)
    ecg_ritmo = e_col1.text_input("Ritmo", "Sinusal")
    ecg_eje = e_col2.text_input("Eje QRS (°)", "Normoeje")
    ecg_pr = e_col3.text_input("PR (ms)", placeholder="120-200")
    ecg_qrs_ms = e_col4.text_input("QRS (ms)", placeholder="<120")

    e_col5, e_col6, e_col7 = st.columns(3)
    ecg_qtc = e_col5.text_input("QTc (ms)")
    ecg_st = e_col6.text_input("Segmento ST", "Isonivelado")
    ecg_onda_t = e_col7.text_input("Onda T", "Normal/Asimétrica")

    ecg_otros = st.text_input("Otros (HVI/HVD, Bloqueos, Ondas Q)", "Sin bloqueos ni ondas Q patológicas.")
    ex_cv = st.text_area("Auscultación / Perfusión", "R1 y R2 normofonéticos. Relleno capilar < 2seg. Sin edemas.")

    # 3. RESPIRATORIO (COMPLIANCE, DP Y PAFI RESTAURADOS)
    st.subheader("3. Respiratorio (ARM) y Mecánica")
    r1, r2, r3, r4 = st.columns(4)
    via_aerea = r1.text_input("Vía Aérea", "TOT")
    modo = r2.text_input("Modo", "VCV")
    fio2 = r3.number_input("FiO2 (%)", 21, 100, 21)
    peep = r4.number_input("PEEP", 0, 30, 5)
    
    r5, r6, r7, r8 = st.columns(4)
    ppico = r5.text_input("P. Pico (cmH2O)")
    pplat = r6.text_input("P. Plateau (cmH2O)")
    comp = r7.text_input("Compliance (ml/cmH2O)")
    vt = r8.text_input("Volumen Tidal (Vt)")

    st.caption("Índices Respiratorios (Se calculan al generar, o puedes escribirlos a mano):")
    r9, r10 = st.columns(2)
    dp_manual = r9.text_input("Driving Pressure (DP)")
    pafi_manual = r10.text_input("PaFiO2")

    ex_resp = st.text_area("Examen Respiratorio", "Buena entrada de aire bilateral, sin ruidos agregados.")

    # 4. OTROS SISTEMAS
    st.subheader("4. Digestivo y Renal")
    o1, o2 = st.columns(2)
    ex_abd = o1.text_area("Abdominal", "Blando, depresible, indoloro.")
    ex_renal = o2.text_area("Renal/Balance", "Diuresis conservada.")

    # 5. INFECTOLOGÍA (Siempre visible)
    st.subheader("5. Infectología")
    inf1, inf2, inf3, inf4 = st.columns(4)
    tmax = inf1.text_input("T. Max 24h")
    pct = inf2.text_input("PCT")
    atb1 = inf3.text_input("ATB 1 (Día)")
    atb2 = inf4.text_input("ATB 2 (Día)")
    cultivos = st.text_area("Cultivos en curso", "Negativos a la fecha.")

with tab_lab:
    st.subheader("Estado Ácido Base y Laboratorio")
    l1, l2, l3, l4, l5, l6 = st.columns(6)
    ph = l1.text_input("pH")
    pco2 = l2.text_input("pCO2")
    po2 = l3.text_input("pO2")
    hco3 = l4.text_input("HCO3")
    eb = l5.text_input("EB")
    lac = l6.text_input("Lactato")

    st.divider()
    l7, l8, l9, l10, l11 = st.columns(5)
    hb = l7.text_input("Hb/Hto")
    gb = l8.text_input("GB")
    plaq = l9.text_input("Plaq")
    urea_cr = l10.text_input("Urea/Cr")
    iono = l11.text_input("Na/K/Cl")

with tab_planes:
    st.subheader("🛡️ FAST HUG BID")
    fast_dict = {'F':'Feeding','A':'Analgesia','S':'Sedación','T':'Trombo','H':'Head','U':'Ulcer','G':'Glucemia','B':'Bowel','I':'Invasiones','D':'Drogas'}
    fast_sel = []
    f_cols = st.columns(5)
    for i, (k, v) in enumerate(fast_dict.items()):
        if f_cols[i % 5].checkbox(k, help=v):
            fast_sel.append(f"{k} - {v}")

    st.subheader("(A/P) Análisis y Plan")
    analisis = st.text_area("Análisis")
    plan = st.text_area("Plan 24hs", "- Cultivar: \n- Imágenes: \n- Interconsultas:")

# --- GENERACIÓN DE TEXTO ---
if st.button("🚀 GENERAR EVOLUCIÓN PARA GECLISA"):
    # Ensamblaje de Módulos Dinámicos
    txt_modulos = ""
    if is_cardio and (killip or grace or timi):
        txt_modulos += f"\n[+] ESTADIFICACIÓN CARDIOVASCULAR:\n    Killip: {killip} | GRACE: {grace} | TIMI: {timi}\n"
    if is_sepsis and (sofa or apache):
        txt_modulos += f"\n[+] SCORES DE SEPSIS:\n    SOFA: {sofa} | APACHE II: {apache}\n"
    if is_pancreatitis and (bisap or ranson or balthazar):
        txt_modulos += f"\n[+] ESTADIFICACIÓN PANCREÁTICA:\n    BISAP: {bisap} | Ranson: {ranson} | Balthazar: {balthazar}\n"

    # Cálculo TAM Automático
    tam_txt = ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_txt = f"(TAM {round((s+2*d)/3)})"
        except: pass

    # Cálculo Driving Pressure (Híbrido: toma manual si existe, sino calcula)
    dp_final = dp_manual
    if not dp_final and pplat and peep:
        try: dp_final = str(int(float(str(pplat).replace(',','.')) - float(str(peep).replace(',','.'))))
        except: pass

    # Cálculo PAFI (Híbrido)
    pafi_final = pafi_manual
    if not pafi_final and po2 and fio2:
        try: pafi_final = str(int(float(str(po2).replace(',','.')) / (float(fio2)/100)))
        except: pass

    texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Int: {dias_int} | Días ARM: {dias_arm}

DIAGNÓSTICO:
{diagnostico}
{txt_modulos}
(S) SUBJETIVO: {subj}

(O) OBJETIVO:

>> INFUSIONES Y DROGAS:
Sedoanalgesia: {sedo.replace(chr(10), ' | ')}
Vasoactivos: {vaso.replace(chr(10), ' | ')}

>> INVASIONES: CVC: {cvc_info} | Cat.Art: {ca_info} | SV: {sv_dias} | SNG: {sng_dias}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}, CAM {cam}. {ex_neuro}
- HEMO: TA {ta} {tam_txt}, FC {fc} lpm, FR {fr} rpm, Sat {sat}%, Temp {temp}°C. 
- ECG: Ritmo {ecg_ritmo}, Eje {ecg_eje}, PR {ecg_pr}ms, QRS {ecg_qrs_ms}ms, QTc {ecg_qtc}ms. ST: {ecg_st}, Onda T: {ecg_onda_t}. {ecg_otros}
- CV (Perfusión): {ex_cv}
- RESP: {via_aerea}, Modo {modo}, FiO2 {fio2}%, PEEP {peep}, PPlat {pplat}, Vt {vt}.
  Mecánica: P.Pico {ppico} | Comp {comp} | DP {dp_final} | PaFiO2 {pafi_final}. 
  Examen: {ex_resp}
- ABD: {ex_abd}
- RENAL: {ex_renal}
- INFECTO: Tmax {tmax}°C | PCT {pct} | ATB: {atb1} / {atb2} | Cultivos: {cultivos.replace(chr(10), ' ')}

>> LABORATORIO / EAB:
pH {ph} | pCO2 {pco2} | pO2 {po2} | HCO3 {hco3} | Lac {lac}
HB/HTO {hb} | GB {gb} | Plaq {plaq} | Cr {urea_cr} | Iono {iono}

>> FAST HUG BID:
{chr(10).join(['  ✓ ' + x for x in fast_sel]) if fast_sel else '  Sin marcar.'}

(A/P) ANÁLISIS Y PLAN:
{analisis}
PLAN:
{plan}
"""
    st.subheader("📋 Resultado para copiar:")
    st.text_area("Final:", texto_final, height=500)
