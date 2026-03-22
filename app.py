import streamlit as st
import re

st.set_page_config(page_title="Evolución UTI/UCCO", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    stTextArea textarea { font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Con Laboratorio Avanzado y Scores por Guías Internacionales")

# --- DATOS GENERALES (SIDEBAR) ---
with st.sidebar:
    st.header("📌 Datos de Base")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    st.divider()
    st.info("💡 Escribe palabras como 'Sepsis', 'IAM', 'ACV', 'NAC', 'TEP', 'HDA' o 'Pancreatitis' en el diagnóstico para activar los scores correspondientes.")

# --- INICIALIZACIÓN DE SCORES DINÁMICOS ---
sofa = qsofa = apache = ""
killip = grace = timi = ""
bisap = ranson = balthazar = ""
nihss = mrs = ""
curb65 = psi = ""
wells = pesi = ""
blatchford = rockall = ""

# --- DIAGNÓSTICO E INTELIGENCIA SEMÁNTICA ---
st.subheader("📋 Diagnóstico Principal")
diagnostico = st.text_area("Diagnósticos de Ingreso / Actuales:", "1. \n2. ")

diag_norm = diagnostico.lower()
diag_norm = re.sub(r'[áäâà]', 'a', diag_norm)
diag_norm = re.sub(r'[éëêè]', 'e', diag_norm)
diag_norm = re.sub(r'[íïîì]', 'i', diag_norm)
diag_norm = re.sub(r'[óöôò]', 'o', diag_norm)
diag_norm = re.sub(r'[úüûù]', 'u', diag_norm)

kw_cardio = ["scasest", "iam", "iamcest", "infarto", "angina", "angor", "coronario", "isquemia"]
kw_sepsis = ["sepsis", "septic", "shock"]
kw_pancreatitis = ["pancreatitis"]
kw_acv = ["acv", "ictus", "stroke", "isquemico", "hemorragico"]
kw_nac = ["nac", "neumonia", "pulmonia"]
kw_tep = ["tep", "tromboembolismo", "embolia"]
kw_hda = ["hda", "hemorragia digestiva", "melena", "hematemesis"]

is_cardio = any(kw in diag_norm for kw in kw_cardio)
is_sepsis = any(kw in diag_norm for kw in kw_sepsis)
is_pancreatitis = any(kw in diag_norm for kw in kw_pancreatitis)
is_acv = any(kw in diag_norm for kw in kw_acv)
is_nac = any(kw in diag_norm for kw in kw_nac)
is_tep = any(kw in diag_norm for kw in kw_tep)
is_hda = any(kw in diag_norm for kw in kw_hda)

# --- RENDERIZADO DE MÓDULOS DE GUÍAS INTERNACIONALES ---
if any([is_cardio, is_sepsis, is_pancreatitis, is_acv, is_nac, is_tep, is_hda]):
    st.markdown("### ⚙️ Escalas y Scores Validados (Guías Internacionales)")

if is_cardio:
    with st.expander("🫀 Cardiopatía Isquémica (AHA/ACC/ESC)", expanded=True):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (Estertores/R3)", "III (EAP)", "IV (Shock)"])
        grace = c2.text_input("Score GRACE (% Mort)")
        timi = c3.text_input("Score TIMI (0-7)")

if is_sepsis:
    with st.expander("🦠 Sepsis (Surviving Sepsis Campaign)", expanded=True):
        s1, s2, s3 = st.columns(3)
        qsofa = s1.text_input("qSOFA (0-3)")
        sofa = s2.text_input("SOFA Score")
        apache = s3.text_input("APACHE II")

if is_pancreatitis:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=True):
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP (0-5)")
        ranson = p2.text_input("Ranson")
        balthazar = p3.selectbox("Balthazar (TC)", ["", "A (Normal)", "B (Agrandamiento)", "C (Inflamación)", "D (1 Colección)", "E (≥2 Col/Gas)"])

if is_acv:
    with st.expander("🧠 Ataque Cerebrovascular (AHA/ASA)", expanded=True):
        a1, a2 = st.columns(2)
        nihss = a1.text_input("Escala NIHSS (0-42)")
        mrs = a2.selectbox("Escala Rankin Modificada (mRS)", ["", "0 - Sin síntomas", "1 - Discapacidad no significativa", "2 - Discapacidad leve", "3 - Discapacidad moderada", "4 - Discapacidad mod-severa", "5 - Discapacidad severa", "6 - Muerte"])

if is_nac:
    with st.expander("🫁 Neumonía Adquirida en la Comunidad (IDSA/ATS)", expanded=True):
        n1, n2 = st.columns(2)
        curb65 = n1.text_input("CURB-65 (0-5)")
        psi = n2.text_input("PSI / PORT Score")

if is_tep:
    with st.expander("🩸 Tromboembolismo Pulmonar (ESC)", expanded=True):
        t1, t2 = st.columns(2)
        wells = t1.text_input("Score de Wells (TEP)")
        pesi = t2.text_input("Score PESI / sPESI")

if is_hda:
    with st.expander("🩸 Hemorragia Digestiva Alta", expanded=True):
        h1, h2 = st.columns(2)
        blatchford = h1.text_input("Glasgow-Blatchford")
        rockall = h2.text_input("Score de Rockall")

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Examen Físico / Clínica", "🧪 Laboratorio / Biomarcadores", "📋 FAST HUG y Plan Final"])

with tab_clinca:
    st.subheader("(S) Subjetivo")
    subj = st.text_area("Novedades y Subjetivo:", "Paciente estable, sin cambios agudos.")

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

    st.subheader("1. Neurológico y Sedación")
    n1, n2, n3, n4 = st.columns(4)
    neuro_estado = n1.text_input("Estado", "Alerta")
    glasgow = n2.text_input("Glasgow", "15/15")
    rass = n3.text_input("RASS", "0")
    cam = n4.text_input("CAM-ICU", "-")
    ex_neuro = st.text_area("Detalle Neuro", "Vigil, conectado, moviliza 4 miembros.")

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

    st.subheader("3. Respiratorio (ARM) y Mecánica")
    r1, r2, r3, r4 = st.columns(4)
    via_aerea = r1.text_input("Vía Aérea", "TOT")
    modo = r2.text_input("Modo", "VCV")
    fio2 = r3.number_input("FiO2 (%)", 21, 100, 21)
    peep = r4.number_input("PEEP", 0, 30, 5)
    
    r5, r6, r7, r8 = st.columns(4)
    ppico = r5.text_input("P. Pico")
    pplat = r6.text_input("P. Plateau")
    comp = r7.text_input("Compliance")
    vt = r8.text_input("Volumen Tidal (Vt)")

    r9, r10 = st.columns(2)
    dp_manual = r9.text_input("Driving Pressure (Calculada auto si vacío)")
    pafi_manual = r10.text_input("PaFiO2 (Calculada auto si vacío)")

    ex_resp = st.text_area("Examen Respiratorio", "Buena entrada de aire bilateral, sin ruidos agregados.")

    st.subheader("4. Otros Sistemas")
    o1, o2 = st.columns(2)
    ex_abd = o1.text_area("Abdominal", "Blando, depresible, indoloro.")
    ex_renal = o2.text_area("Renal/Balance", "Diuresis conservada.")

    st.subheader("5. Infectología")
    inf1, inf2, inf3 = st.columns(3)
    tmax = inf1.text_input("T. Max 24h")
    atb1 = inf2.text_input("ATB 1 (Día)")
    atb2 = inf3.text_input("ATB 2 (Día)")
    cultivos = st.text_area("Cultivos en curso", "Hemocultivos:\nUrocultivo:\nMini-BAL:")

with tab_lab:
    st.subheader("🌬️ Estado Ácido Base (EAB)")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    ph = e1.text_input("pH")
    pco2 = e2.text_input("pCO2")
    po2 = e3.text_input("pO2")
    hco3 = e4.text_input("HCO3")
    eb = e5.text_input("EB")
    lactato = e6.text_input("Ác. Láctico")

    st.divider()

    st.subheader("🩸 Hemograma Completo y Coagulograma")
    l1, l2, l3, l4 = st.columns(4)
    hb = l1.text_input("Hemoglobina (Hb)")
    hto = l2.text_input("Hematocrito (Hto)")
    gb = l3.text_input("Glóbulos Blancos (GB)")
    plaq = l4.text_input("Plaquetas")
    
    st.caption("Fórmula Leucocitaria (%)")
    f1, f2, f3, f4 = st.columns(4)
    neut = f1.text_input("Neutrófilos")
    linf = f2.text_input("Linfocitos")
    mono = f3.text_input("Monocitos")
    eos = f4.text_input("Eosinófilos")

    st.caption("Coagulograma")
    c1, c2, c3 = st.columns(3)
    app = c1.text_input("TP / APP (%)")
    kptt = c2.text_input("KPTT (seg)")
    rin = c3.text_input("RIN")

    st.divider()

    st.subheader("🧪 Química, Medio Interno y Hepatograma")
    q1, q2, q3, q4, q5, q6, q7 = st.columns(7)
    urea = q1.text_input("Urea")
    cr = q2.text_input("Creatinina")
    na = q3.text_input("Sodio (Na)")
    k = q4.text_input("Potasio (K)")
    cl = q5.text_input("Cloro (Cl)")
    mg = q6.text_input("Magnesio (Mg)")
    ca = q7.text_input("Calcio (Ca)")

    st.caption("Hepatograma")
    he1, he2, he3, he4, he5, he6 = st.columns(6)
    bt = he1.text_input("Bil. Total")
    bd = he2.text_input("Bil. Directa")
    got = he3.text_input("GOT/AST")
    gpt = he4.text_input("GPT/ALT")
    fal = he5.text_input("FAL")
    ggt = he6.text_input("GGT")

    st.divider()

    st.subheader("🧬 Biomarcadores y Enzimas")
    b1, b2, b3, b4, b5, b6 = st.columns(6)
    cpk = b1.text_input("CPK")
    cpk_mb = b2.text_input("CPK-MB")
    tropo = b3.text_input("Troponina I")
    probnp = b4.text_input("ProBNP")
    ldh = b5.text_input("LDH")
    pct = b6.text_input("Procalcitonina (PCT)")

with tab_planes:
    st.subheader("🛡️ FAST HUG BID")
    fast_dict = {'F':'Feeding','A':'Analgesia','S':'Sedación','T':'Trombo','H':'Head','U':'Ulcer','G':'Glucemia','B':'Bowel','I':'Invasiones','D':'Drogas'}
    fast_sel = []
    f_cols = st.columns(5)
    for i, (k, v) in enumerate(fast_dict.items()):
        if f_cols[i % 5].checkbox(k, help=v):
            fast_sel.append(f"{k} - {v}")

    st.subheader("(A/P) Análisis y Plan")
    analisis = st.text_area("Análisis General")
    plan = st.text_area("Plan 24hs", "- Cultivar: \n- Imágenes: \n- Interconsultas:")

# --- GENERACIÓN DE TEXTO ---
if st.button("🚀 GENERAR EVOLUCIÓN PARA GECLISA"):
    # Ensamblaje de Módulos Dinámicos
    txt_modulos = ""
    if is_cardio and (killip or grace or timi):
        txt_modulos += f"\n[+] CARDIO (AHA/ESC) -> Killip: {killip} | GRACE: {grace} | TIMI: {timi}"
    if is_sepsis and (qsofa or sofa or apache):
        txt_modulos += f"\n[+] SEPSIS -> qSOFA: {qsofa} | SOFA: {sofa} | APACHE II: {apache}"
    if is_pancreatitis and (bisap or ranson or balthazar):
        txt_modulos += f"\n[+] PANCREATITIS -> BISAP: {bisap} | Ranson: {ranson} | Balthazar: {balthazar}"
    if is_acv and (nihss or mrs):
        txt_modulos += f"\n[+] NEURO (ACV) -> NIHSS: {nihss} | Rankin Modificado (mRS): {mrs}"
    if is_nac and (curb65 or psi):
        txt_modulos += f"\n[+] NEUMONÍA -> CURB-65: {curb65} | PSI/PORT: {psi}"
    if is_tep and (wells or pesi):
        txt_modulos += f"\n[+] TEP -> Wells: {wells} | PESI: {pesi}"
    if is_hda and (blatchford or rockall):
        txt_modulos += f"\n[+] HDA -> Glasgow-Blatchford: {blatchford} | Rockall: {rockall}"

    # Cálculos Automáticos
    tam_txt = ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_txt = f"(TAM {round((s+2*d)/3)})"
        except: pass

    dp_final = dp_manual
    if not dp_final and pplat and peep:
        try: dp_final = str(int(float(str(pplat).replace(',','.')) - float(str(peep).replace(',','.'))))
        except: pass

    pafi_final = pafi_manual
    if not pafi_final and po2 and fio2:
        try: pafi_final = str(int(float(str(po2).replace(',','.')) / (float(fio2)/100)))
        except: pass

    texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Int: {dias_int} | Días ARM: {dias_arm}

DIAGNÓSTICO:
{diagnostico}{txt_modulos}

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
- INFECTO: Tmax {tmax}°C | ATB: {atb1} / {atb2} | Cultivos: {cultivos.replace(chr(10), ' ')}

>> LABORATORIO Y MEDIO INTERNO:
- EAB: pH {ph} | pCO2 {pco2} | pO2 {po2} | HCO3 {hco3} | EB {eb} | Lac {lactato}
- HEMOGRAMA: Hb {hb} | Hto {hto} | GB {gb} (N:{neut}% L:{linf}% M:{mono}% E:{eos}%) | Plaq {plaq}
- COAGULOGRAMA: TP/APP {app} | KPTT {kptt} | RIN {rin}
- QUÍMICA: Urea {urea} | Cr {cr} | Na {na} | K {k} | Cl {cl} | Mg {mg} | Ca {ca}
- HEPATOGRAMA: BT {bt} | BD {bd} | GOT {got} | GPT {gpt} | FAL {fal} | GGT {ggt}
- BIOMARCADORES: CPK {cpk} | CPK-MB {cpk_mb} | Tropo I {tropo} | ProBNP {probnp} | LDH {ldh} | PCT {pct}

>> FAST HUG BID:
{chr(10).join(['  ✓ ' + x for x in fast_sel]) if fast_sel else '  Sin marcar.'}

(A/P) ANÁLISIS Y PLAN:
{analisis}
PLAN:
{plan}
"""
    st.subheader("📋 Resultado para copiar:")
    st.text_area("Final:", texto_final, height=500)
