import streamlit as st

# Configuración de estética y página
st.set_page_config(page_title="Evolución UTI/UCCO", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    stTextArea textarea { font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión con Diagnóstico y ECG Estándar (AHA/ACC/HRS)")

# --- DATOS GENERALES (SIDEBAR) ---
with st.sidebar:
    st.header("📌 Datos de Base")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    sofa = st.text_input("SOFA")
    apache = st.text_input("APACHE II")
    st.divider()
    st.warning("⚠️ Los datos se borran al cerrar o refrescar la pestaña.")

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Examen Físico / Clínica", "🧪 Laboratorio y EAB", "📋 FAST HUG y Plan Final"])

with tab_clinca:
    # --- DIAGNÓSTICO (NUEVO) ---
    st.subheader("📋 Diagnóstico")
    diagnostico = st.text_area("Diagnóstico(s) de Ingreso / Actuales:", "1. \n2. ")
    
    st.divider()

    # --- SUBJETIVO ---
    st.subheader("(S) Subjetivo")
    subj = st.text_area("Novedades y Subjetivo:", "Paciente estable, sin cambios agudos.")

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
    temp = h5.text_input("Temp (°C)")

    # Apartado específico de ECG (Basado en recomendaciones 2007-2009)
    st.info("📊 Interpretación del Electrocardiograma (ECG)")
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
    ex_cv = st.text_area("Examen Cardiovascular (Auscultación/Edemas)", "R1 y R2 normofonéticos, silencios libres, sin edemas.")

    # 3. RESPIRATORIO
    st.subheader("3. Respiratorio (ARM)")
    r1, r2, r3, r4, r5 = st.columns(5)
    via_aerea = r1.text_input("Vía Aérea", "TOT")
    modo = r2.text_input("Modo", "VCV")
    fio2 = r3.number_input("FiO2 (%)", 21, 100, 21)
    peep = r4.number_input("PEEP", 0, 30, 5)
    pplat = r5.text_input("P. Plateau")
    ex_resp = st.text_area("Examen Respiratorio", "Buena entrada de aire bilateral, sin ruidos agregados.")

    st.subheader("4. Otros Sistemas")
    o1, o2 = st.columns(2)
    ex_abd = o1.text_area("Abdominal", "Blando, depresible, indoloro.")
    ex_renal = o2.text_area("Renal/Balance", "Diuresis conservada.")

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
    # Cálculo TAM aproximado
    tam_txt = ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_txt = f"(TAM {round((s+2*d)/3)})"
        except: pass

    # Cálculo PAFI
    pafi_txt = ""
    if po2 and fio2:
        try: pafi_txt = f"| PAFI: {int(float(po2)/(fio2/100))}"
        except: pass

    texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Int: {dias_int} | Días ARM: {dias_arm} | SOFA: {sofa}

DIAGNÓSTICO:
{diagnostico}

(S) SUBJETIVO: {subj}

(O) OBJETIVO:
>> INVASIONES: CVC: {cvc_info} | Cat.Art: {ca_info} | SV: {sv_dias} | SNG: {sng_dias}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}. {ex_neuro}
- HEMO: TA {ta} {tam_txt}, FC {fc} lpm, FR {fr} rpm, Sat {sat}%, Temp {temp}°C. 
- ECG (AHA/ACC/HRS): Ritmo {ecg_ritmo}, Eje {ecg_eje}, PR {ecg_pr}ms, QRS {ecg_qrs_ms}ms, QTc {ecg_qtc}ms. ST: {ecg_st}, Onda T: {ecg_onda_t}. {ecg_otros}
- CV: {ex_cv}
- RESP: {via_aerea}, Modo {modo}, FiO2 {fio2}%, PEEP {peep}, PPlat {pplat} {pafi_txt}. {ex_resp}
- ABD: {ex_abd}
- RENAL: {ex_renal}

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
