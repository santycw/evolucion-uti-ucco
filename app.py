import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Evolución UTI/UCCO", page_icon="🏥", layout="wide")

st.title("🏥 Asistente de Evolución Diaria - UTI / UCCO")
st.markdown("---")

# --- SIDEBAR: DATOS GENERALES ---
with st.sidebar:
    st.header("📌 Identificación y Scores")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    sofa = st.text_input("SOFA")
    apache = st.text_input("APACHE II")
    st.markdown("---")
    st.info("Este programa no guarda datos en la nube por seguridad. Al recargar la página, los datos se borran.")

# --- SECCIONES PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🩺 Clínica y Examen", "🧪 Laboratorio/EAB", "💊 Infusiones/Invasiones", "📋 FAST HUG y Plan"])

with tab1:
    st.subheader("(S) Subjetivo / Novedades")
    subj = st.text_area("Novedades del turno:", "Paciente estable, sin cambios agudos.")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.subheader("1. Neurológico")
        neuro_estado = st.text_input("Estado", "Alerta")
        glasgow = st.text_input("Glasgow", "15/15")
        rass = st.text_input("RASS", "0")
    with col_n2:
        st.subheader("Examen Físico")
        ex_neuro = st.text_area("Detalle Neuro", "Vigil, conectado, moviliza 4 miembros.")

    st.subheader("2. Signos Vitales y Hemodinamia")
    c1, c2, c3, c4 = st.columns(4)
    ta = c1.text_input("TA (S/D)", placeholder="120/80")
    fc = c2.text_input("FC (lpm)")
    fr = c3.text_input("FR (rpm)")
    temp = c4.text_input("Temp (°C)")

    # Cálculo automático de TAM y PP
    tam_val, pp_val = "", ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_val = round((s + 2*d)/3)
            pp_val = int(s - d)
            st.caption(f"💡 Calculado: TAM {tam_val} mmHg | PP {pp_val} mmHg")
        except: pass
    
    c5, c6, c7 = st.columns(3)
    sat = c5.text_input("SatO2 (%)")
    relleno = c6.text_input("Relleno Capilar", "< 2 seg")
    tdg = c7.text_input("TDG")
    ex_cv = st.text_area("Examen Cardiovascular", "R1 y R2 normofonéticos, silencios libres, sin edemas.")

    st.subheader("3. Respiratorio")
    r1, r2, r3, r4 = st.columns(4)
    fio2 = r1.number_input("FiO2 (%)", 21, 100, 21)
    peep = r2.number_input("PEEP", 0, 30, 5)
    pplat = r3.text_input("P. Plateau")
    via_aerea = r4.text_input("Vía Aérea", "TOT")
    ex_resp = st.text_area("Examen Respiratorio", "Buena entrada de aire bilateral, sin ruidos agregados.")

with tab2:
    st.subheader("Estado Ácido-Base (EAB)")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    ph = e1.text_input("pH")
    pco2 = e2.text_input("pCO2")
    po2 = e3.text_input("pO2")
    hco3 = e4.text_input("HCO3")
    eb = e5.text_input("EB")
    lactato = e6.text_input("Lactato")

    # Cálculo automático de PAFI
    pafi_calc = ""
    if po2 and fio2:
        try:
            pafi_calc = int(float(po2) / (fio2/100))
            st.success(f"PAFI Calculada: {pafi_calc}")
        except: pass

    st.subheader("Laboratorio General")
    l1, l2, l3, l4 = st.columns(4)
    hb = l1.text_input("Hb/Hto")
    gb = l2.text_input("GB")
    plaq = l3.text_input("Plaquetas")
    cr = l4.text_input("Urea/Cr")

with tab3:
    st.subheader("💊 Infusiones")
    i1, i2 = st.columns(2)
    sedo = i1.text_area("Sedoanalgesia", "Fentanilo: \nPropofol: \nMidazolam:")
    vaso = i2.text_area("Vasoactivos", "Noradrenalina: \nVasopresina: \nDobutamina:")

    st.subheader("💉 Dispositivos e Invasiones")
    d1, d2, d3, d4 = st.columns(4)
    cvc = d1.text_input("CVC (Sitio/Día)")
    cart = d2.text_input("Cat. Art (Sitio/Día)")
    sv = d3.text_input("Sonda Vesical (Día)")
    sng = d4.text_input("SNG (Día)")

with tab4:
    st.subheader("🛡️ FAST HUG BID")
    fast_hug_dict = {
        'F': 'Alimentación (Feeding)', 'A': 'Analgesia', 'S': 'Sedación',
        'T': 'Tromboprofilaxis', 'H': 'Cabecera a 30-45°', 'U': 'Úlceras estrés',
        'G': 'Control Glucémico', 'B': 'Bowel (Intestino)', 'I': 'Retiro Invasiones', 'D': 'Desescalamiento ATB'
    }
    
    fast_sel = []
    f_cols = st.columns(5)
    for i, (k, v) in enumerate(fast_hug_dict.items()):
        if f_cols[i % 5].checkbox(f"{k}", help=v):
            fast_sel.append(f"{k} - {v}")

    st.subheader("(A) Análisis y (P) Plan")
    analisis = st.text_area("Conclusión / Análisis", "Paciente cursa día...")
    plan = st.text_area("Plan 24hs", "- Cultivar: \n- Imágenes: \n- Interconsultas:")

# --- GENERACIÓN DE TEXTO ---
st.markdown("---")
if st.button("🚀 GENERAR Y COPIAR EVOLUCIÓN"):
    # Cálculo de Driving Pressure
    dp = ""
    try: dp = int(float(pplat) - peep)
    except: pass

    resumen = f"""EVOLUCIÓN UTI / UCCO
Días Int: {dias_int} | ARM: {dias_arm} | SOFA: {sofa}

(S) SUBJETIVO: {subj}

(O) OBJETIVO:
>> INFUSIONES:
Sedoanalgesia: {sedo}
Vasoactivos: {vaso}

>> INVASIONES:
- CVC: {cvc} | Cat. Art: {cart}
- Sonda Vesical: {sv} | SNG: {sng}

>> EXAMEN FÍSICO:
1. NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}. {ex_neuro}
2. HEMO: TA {ta} (TAM {tam_val}), FC {fc}, FR {fr}, Sat {sat}%, Temp {temp}°. Relleno {relleno}. {ex_cv}
3. RESP: {via_aerea}, FiO2 {fio2}%, PEEP {peep}, PPlat {pplat} (DP {dp}). PAFI {pafi_calc}. {ex_resp}

>> LABORATORIO / EAB:
pH {ph} | pCO2 {pco2} | pO2 {po2} | HCO3 {hco3} | Lac {lactato}
Hb/Hto: {hb} | GB: {gb} | Plaq: {plaq} | Cr: {cr}

>> FAST HUG BID:
{chr(10).join(['  ✓ ' + x for x in fast_sel]) if fast_sel else '  Sin medidas marcadas.'}

(A/P) ANÁLISIS Y PLAN:
{analisis}
PLAN: {plan}
"""
    st.text_area("Evolución lista para GECLISA (Ctrl+C / Ctrl+V):", resumen, height=400)
    st.balloons()
