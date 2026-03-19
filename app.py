import streamlit as st

# Configuración de estética y página
st.set_page_config(page_title="Evolución UTI/UCCO", page_icon="🏥", layout="wide")

# Estilo CSS para que se vea más profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    stTextArea textarea { font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión Optimizada para GECLISA (Copia y Pega)")

# --- DATOS GENERALES (SIDEBAR) ---
with st.sidebar:
    st.header("📌 Datos de Base")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    sofa = st.text_input("SOFA")
    apache = st.text_input("APACHE II")
    st.divider()
    st.warning("⚠️ Los datos se borran al cerrar o refrescar la pestaña por seguridad del paciente.")

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Examen Físico / Clínica", "🧪 Laboratorio y EAB", "📋 FAST HUG y Plan Final"])

with tab_clinca:
    # 1. SUBJETIVO
    st.subheader("(S) Subjetivo")
    subj = st.text_area("Novedades y Subjetivo:", "Paciente estable, sin cambios agudos en las últimas horas.")

    # 2. INVASIONES (Movido arriba como pediste)
    st.subheader("💉 Dispositivos e Invasiones")
    d1, d2, d3, d4 = st.columns(4)
    cvc_sitio = d1.text_input("CVC Sitio")
    cvc_dias = d1.text_input("CVC Días")
    ca_sitio = d2.text_input("Cat. Art. Sitio")
    ca_dias = d2.text_input("Cat. Art. Días")
    sv_dias = d3.text_input("Sonda Vesical (Días)")
    sng_dias = d4.text_input("SNG (Días)")

    st.divider()

    # 3. SISTEMA NEUROLÓGICO
    st.subheader("1. Neurológico y Sedación")
    n1, n2, n3, n4 = st.columns(4)
    neuro_estado = n1.text_input("Estado", "Alerta")
    glasgow = n2.text_input("Glasgow", "15/15")
    rass = n3.text_input("RASS", "0")
    cam = n4.text_input("CAM-ICU", "-")
    pupilas = st.text_input("Pupilas", "Isocóricas Reactivas")
    ex_neuro = st.text_area("Detalle Examen Neuro", "Vigil, conectado, moviliza 4 miembros.")

    # 4. HEMODINAMIA
    st.subheader("2. Signos Vitales y Hemodinamia")
    h1, h2, h3, h4, h5 = st.columns(5)
    ta = h1.text_input("TA (S/D)", placeholder="120/80")
    fc = h2.text_input("FC (lpm)")
    fr = h3.text_input("FR (rpm)")
    sat = h4.text_input("SatO2 (%)")
    temp_actual = h5.text_input("Temp Actual (°C)")

    # Cálculos automáticos Hemodinamia
    tam_val, pp_val = "", ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_val = round((s + 2*d)/3)
            pp_val = int(s - d)
            st.info(f"💡 TAM: {tam_val} mmHg | PP: {pp_val} mmHg")
        except: pass

    h6, h7, h8, h9 = st.columns(4)
    pvc = h6.text_input("PVC")
    ritmo = h7.text_input("Ritmo", "Sinusal")
    relleno = h8.text_input("Relleno Capilar", "< 2 seg")
    tdg = h9.text_input("TDG")
    ex_cv = st.text_area("Detalle Examen CV", "R1 y R2 normofonéticos, silencios libres, sin edemas.")

    # 5. RESPIRATORIO
    st.subheader("3. Respiratorio (ARM)")
    r1, r2, r3, r4, r5 = st.columns(5)
    via_aerea = r1.text_input("Vía Aérea", "TOT")
    modo = r2.text_input("Modo", "VCV")
    fio2 = r3.number_input("FiO2 (%)", 21, 100, 21)
    peep = r4.number_input("PEEP", 0, 30, 5)
    vt = r5.text_input("Vt")
    
    r6, r7, r8, r9 = st.columns(4)
    ppico = r6.text_input("P. Pico")
    pplat = r7.text_input("P. Plateau")
    comp = r8.text_input("Compliance")
    pafi_manual = r9.text_input("PAFI Manual (si no hay EAB)")
    ex_resp = st.text_area("Detalle Examen Resp", "Buena entrada de aire bilateral, sin ruidos agregados.")

    # 6. OTROS SISTEMAS
    st.subheader("4. Otros Sistemas")
    o1, o2, o3 = st.columns(3)
    ex_abd = o1.text_area("Digestivo / Abd", "Blando, depresible, indoloro, RHA presentes.")
    ex_renal = o2.text_area("Renal / MI", "Diuresis clara, sin globo vesical.")
    nutri = o3.text_area("Nutrición / Glucemia", "SNG / Glucemia: 110 mg/dl")

with tab_lab:
    # EAB
    st.subheader("Estado Ácido Base (EAB)")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    ph = e1.text_input("pH")
    pco2 = e2.text_input("pCO2")
    po2 = e3.text_input("pO2")
    hco3 = e4.text_input("HCO3")
    eb = e5.text_input("EB")
    lactato = e6.text_input("Lactato")

    # Cálculo automático PAFI
    pafi_final = pafi_manual
    if po2 and fio2:
        try:
            pafi_final = int(float(po2) / (fio2/100))
            st.success(f"PAFI Calculada: {pafi_final}")
        except: pass

    st.divider()
    # LABORATORIO COMPLETO
    st.subheader("Laboratorio General")
    l1, l2, l3, l4, l5, l6, l7 = st.columns(7)
    hb = l1.text_input("Hb")
    hto = l2.text_input("Hto")
    gb_lab = l3.text_input("GB")
    plaq = l4.text_input("Plaq")
    app = l5.text_input("APP")
    kptt = l6.text_input("KPTT")
    rin = l7.text_input("RIN")

    l8, l9, l10, l11, l12, l13, l14 = st.columns(7)
    urea = l8.text_input("Urea")
    cr = l9.text_input("Cr")
    k = l10.text_input("K")
    na = l11.text_input("Na")
    mg = l12.text_input("Mg")
    cl = l13.text_input("Cl")
    ca = l14.text_input("Ca")

    st.caption("Perfil Hepático / Enzimático")
    p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
    got = p1.text_input("GOT")
    gpt = p2.text_input("GPT")
    ggt = p3.text_input("GGT")
    fal = p4.text_input("FAL")
    amilasa = p5.text_input("Amilasa")
    cpk = p6.text_input("CPK")
    tropo = p7.text_input("Tropo")

    st.subheader("Infectología")
    inf1, inf2, inf3, inf4 = st.columns(4)
    tmax = inf1.text_input("T. Max 24h")
    pct = inf2.text_input("PCT")
    atb1 = inf3.text_input("ATB 1 (Día)")
    atb2 = inf4.text_input("ATB 2 (Día)")
    cultivos = st.text_area("Cultivos en curso", "Negativos a la fecha.")

with tab_planes:
    # INFUSIONES
    st.subheader("💊 Infusiones Actuales")
    i1, i2 = st.columns(2)
    sedo = i1.text_area("Sedoanalgesia", "Fentanilo: \nPropofol: \nMidazolam: \nBloq NM:")
    vaso = i2.text_area("Vasoactivos", "Noradrenalina: \nVasopresina: \nDobutamina: \nAdrenalina:")

    st.divider()
    # FAST HUG BID DETALLADO
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

    # ANÁLISIS Y PLAN
    st.subheader("(A/P) Análisis y Plan")
    prob1 = st.text_input("Problema Activo 1")
    prob2 = st.text_input("Problema Activo 2")
    conclusion = st.text_area("Conclusión General")
    plan_final = st.text_area("Plan 24hs (Cultivos, Imágenes, Cambios)", "- Cultivar: \n- Imágenes: \n- Interconsultas: \n- Cambios Terap.:")

# --- GENERACIÓN DE TEXTO FINAL ---
st.markdown("---")
if st.button("🚀 GENERAR EVOLUCIÓN PARA GECLISA"):
    # Cálculo de Driving Pressure
    dp = ""
    try: dp = int(float(pplat) - float(peep))
    except: pass

    texto_final = f"""EVOLUCIÓN UTI / UCCO - DIARIA
================================================================
Días Internación: {dias_int} | Días ARM: {dias_arm} 
SOFA: {sofa} | APACHE II: {apache} 

(S) SUBJETIVO / NOVEDADES:
{subj}

================================================================
(O) OBJETIVO / EXAMEN FÍSICO
================================================================

>> INFUSIONES:
Sedoanalgesia: {sedo}
Vasoactivos: {vaso}

>> DISPOSITIVOS E INVASIONES:
- CVC: Sitio: {cvc_sitio} | Días: #{cvc_dias} 
- Cat. Arterial: Sitio: {ca_sitio} | Días: #{ca_dias} 
- Sonda Vesical: Días: #{sv_dias} 
- SNG: Días: #{sng_dias} 

----------------------------------------------------------------
>> REVISIÓN POR SISTEMAS
----------------------------------------------------------------

1. NEUROLÓGICO Y SEDACIÓN
Estado: {neuro_estado} | Glasgow {glasgow} | RASS {rass} | CAM {cam}
Pupilas: {pupilas}
Examen: {ex_neuro}

2. SIGNOS VITALES Y HEMODINAMIA
TA {ta} mmHg (TAM {tam_val} | PP {pp_val}) | FC {fc} lpm | FR {fr} rpm 
SatO2 {sat}% | Temp {temp_actual}°C | PVC {pvc} | Ritmo {ritmo}
Perfusión: Relleno {relleno} | TDG {tdg}
Examen: {ex_cv}

3. RESPIRATORIO (ARM)
Vía: {via_aerea} | Modo: {modo} | FiO2 {fio2}% | PEEP {peep} | Vt {vt}
Mecánica: Pico {ppico} | Plateau {pplat} | DP {dp} | Comp {comp}
PAFI: {pafi_final}
Examen: {ex_resp}

4. DIGESTIVO / ABDOMINAL: {ex_abd}
5. RENAL / MEDIO INTERNO: {ex_renal}
6. NUTRICIÓN: {nutri}

7. INFECTOLOGÍA
Tmax {tmax}°C | PCT {pct} | ATB1 {atb1} | ATB2 {atb2}
Cultivos: {cultivos}

8. ESTUDIOS COMPLEMENTARIOS
EAB: pH {ph} | pCO2 {pco2} | pO2 {po2} | HCO3 {hco3} | EB {eb} | Lac {lactato}
LAB: Hb {hb} | Hto {hto} | GB {gb_lab} | Plaq {plaq} | APP {app} | KPTT {kptt} | RIN {rin}
IONO: Urea {urea} | Cr {cr} | K {k} | Na {na} | Mg {mg} | Cl {cl} | Ca {ca}
ENZIMAS: GOT {got} | GPT {gpt} | GGT {ggt} | FAL {fal} | Amil {amilasa} | CPK {cpk} | Tropo {tropo}

----------------------------------------------------------------
>> CUIDADOS PREVENTIVOS (FAST HUG BID)
----------------------------------------------------------------
{chr(10).join(['  ✓ ' + x for x in fast_sel]) if fast_sel else '  Sin medidas marcadas.'}

================================================================
(A) ANÁLISIS Y (P) PLAN
================================================================
Problemas Activos:
1. {prob1}
2. {prob2}
CONCLUSIÓN: {conclusion}

PLAN 24HS:
{plan_final}
"""
    st.subheader("📋 Copia el texto de abajo:")
    st.text_area("Resultado final:", texto_final, height=500)
    st.success("¡Evolución generada! Selecciona el texto, copia y pega en GECLISA.")
    st.balloons()
