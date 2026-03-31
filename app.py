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
st.caption("Motor MBE: Balance, Nutrición y Laboratorio con Unidades Convencionales")

# --- DATOS GENERALES ---
with st.sidebar:
    st.header("📌 Datos de Base")
    dias_int = st.text_input("Días Internación")
    dias_arm = st.text_input("Días ARM")
    st.divider()
    st.info("💡 Escribe diagnósticos clave (Sepsis, IAM, IC, FA, Renal, Cirrosis, EPOC, ACV, HSA, CID, Pancreatitis) para activar escalas.")

# --- INICIALIZACIÓN DE SCORES ---
sofa = qsofa = apache = ""
killip = grace = timi = nyha = stevenson = aha_ic = cha2ds2 = hasbled = ""
kdigo_ira = kdigo_erc = ""
child = meld = ""
bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = ""
curb65 = psi = gold = ""
wells_tep = pesi = wells_tvp = ""
blatchford = rockall = isth = ""

# --- INTELIGENCIA SEMÁNTICA ---
st.subheader("📋 Diagnóstico Principal")
diagnostico = st.text_area("Diagnósticos (Palabras clave activan scores automáticos):", "1. \n2. ")

diag_norm = diagnostico.lower()
diag_norm = re.sub(r'[áäâà]', 'a', diag_norm)
diag_norm = re.sub(r'[éëêè]', 'e', diag_norm)
diag_norm = re.sub(r'[íïîì]', 'i', diag_norm)
diag_norm = re.sub(r'[óöôò]', 'o', diag_norm)
diag_norm = re.sub(r'[úüûù]', 'u', diag_norm)

kw_isquemia = ["scasest", "iam", "iamcest", "infarto", "angina", "angor", "coronario"]
kw_ic = ["ic", "insuficiencia cardiaca", "falla cardiaca"]
kw_fa = ["fa", "fibrilacion auricular", "aleteo", "flutter"]
kw_sepsis = ["sepsis", "septic", "shock"]
kw_renal = ["ira", "aki", "insuficiencia renal", "falla renal", "erc", "nefropatia"]
kw_hepato = ["cirrosis", "hepatopatia", "falla hepatica", "dcl", "hepatitis"]
kw_pancreas = ["pancreatitis"]
kw_acv = ["acv", "ictus", "stroke", "isquemico", "hemorragico"]
kw_hsa = ["hsa", "hemorragia subaracnoidea", "aneurisma"]
kw_nac = ["nac", "neumonia", "pulmonia"]
kw_epoc = ["epoc", "bronquitis cronica", "enfisema"]
kw_tep = ["tep", "tromboembolismo pulmonar"]
kw_tvp = ["tvp", "trombosis venosa"]
kw_hda = ["hda", "hemorragia digestiva", "melena", "hematemesis"]
kw_cid = ["cid", "coagulacion intravascular diseminada"]

is_isquemia = any(kw in diag_norm for kw in kw_isquemia)
is_ic = any(kw in diag_norm for kw in kw_ic)
is_fa = any(kw in diag_norm for kw in kw_fa)
is_sepsis = any(kw in diag_norm for kw in kw_sepsis)
is_renal = any(kw in diag_norm for kw in kw_renal)
is_hepato = any(kw in diag_norm for kw in kw_hepato)
is_pancreas = any(kw in diag_norm for kw in kw_pancreas)
is_acv = any(kw in diag_norm for kw in kw_acv)
is_hsa = any(kw in diag_norm for kw in kw_hsa)
is_nac = any(kw in diag_norm for kw in kw_nac)
is_epoc = any(kw in diag_norm for kw in kw_epoc)
is_tep = any(kw in diag_norm for kw in kw_tep)
is_tvp = any(kw in diag_norm for kw in kw_tvp)
is_hda = any(kw in diag_norm for kw in kw_hda)
is_cid = any(kw in diag_norm for kw in kw_cid)

# --- MÓDULOS DE GUÍAS INTERNACIONALES ---
if any([is_isquemia, is_ic, is_fa, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_epoc, is_tep, is_tvp, is_hda, is_cid]):
    st.markdown("### ⚙️ Scores Médicos Activados")

if is_isquemia:
    with st.expander("🫀 SCASEST / IAM (AHA/ESC)", expanded=True):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"])
        grace = c2.text_input("GRACE (% Mort)")
        timi = c3.text_input("TIMI (0-7)")

if is_ic:
    with st.expander("🫀 Insuficiencia Cardíaca (AHA/ACC/ESC)", expanded=True):
        ic1, ic2, ic3 = st.columns(3)
        nyha = ic1.selectbox("Clase NYHA", ["", "I (Sin lim)", "II (Lim leve)", "III (Lim marcada)", "IV (Reposo)"])
        stevenson = ic2.selectbox("Perfil Stevenson", ["", "A (Seco-Caliente)", "B (Húmedo-Caliente)", "C (Húmedo-Frío)", "L (Seco-Frío)"])
        aha_ic = ic3.selectbox("Estadio AHA", ["", "A (Riesgo)", "B (Estructural sin sit)", "C (Sintomático)", "D (Avanzada)"])

if is_fa:
    with st.expander("💓 Fibrilación Auricular", expanded=True):
        fa1, fa2 = st.columns(2)
        cha2ds2 = fa1.text_input("CHA2DS2-VASc (Riesgo ACV)")
        hasbled = fa2.text_input("HAS-BLED (Riesgo Sangrado)")

if is_sepsis:
    with st.expander("🦠 Sepsis (Surviving Sepsis)", expanded=True):
        s1, s2, s3 = st.columns(3)
        qsofa = s1.text_input("qSOFA (0-3)")
        sofa = s2.text_input("SOFA Score")
        apache = s3.text_input("APACHE II")

if is_renal:
    with st.expander("🩸 Nefrología (KDIGO)", expanded=True):
        ren1, ren2 = st.columns(2)
        kdigo_ira = ren1.selectbox("KDIGO - Injuria Renal Aguda (IRA)", ["", "1 (Cr x1.5-1.9 o Diur <0.5 x6h)", "2 (Cr x2.0-2.9 o Diur <0.5 x12h)", "3 (Cr x3.0 o TRS o Anuria)"])
        kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1 (TFG >90)", "G2 (TFG 60-89)", "G3a (TFG 45-59)", "G3b (TFG 30-44)", "G4 (TFG 15-29)", "G5 (TFG <15)"])

if is_hepato:
    with st.expander("🟡 Hepatopatía / Cirrosis", expanded=True):
        hp1, hp2 = st.columns(2)
        child = hp1.selectbox("Child-Pugh", ["", "A (5-6 pts)", "B (7-9 pts)", "C (10-15 pts)"])
        meld = hp2.text_input("MELD / MELD-Na")

if is_pancreas:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=True):
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP (0-5)")
        ranson = p2.text_input("Ranson")
        balthazar = p3.selectbox("Balthazar (TC)", ["", "A", "B", "C", "D", "E"])

if is_acv:
    with st.expander("🧠 ACV (AHA/ASA)", expanded=True):
        a1, a2 = st.columns(2)
        nihss = a1.text_input("NIHSS (0-42)")
        mrs = a2.selectbox("Rankin (mRS)", ["", "0", "1", "2", "3", "4", "5", "6"])

if is_hsa:
    with st.expander("🧠 Hemorragia Subaracnoidea", expanded=True):
        hsa1, hsa2 = st.columns(2)
        hunt = hsa1.selectbox("Hunt & Hess", ["", "I (Asint/Cefalea leve)", "II (Cefalea mod-sev/Rigidez)", "III (Somnolencia/Déficit leve)", "IV (Estupor/Hemiparesia)", "V (Coma profundo)"])
        fisher = hsa2.selectbox("Escala Fisher (TC)", ["", "I (Sin sangre)", "II (Difusa <1mm)", "III (Coágulo grueso >1mm)", "IV (Intraventricular/Parenquimatosa)"])

if is_nac:
    with st.expander("🫁 Neumonía (NAC)", expanded=True):
        n1, n2 = st.columns(2)
        curb65 = n1.text_input("CURB-65 (0-5)")
        psi = n2.text_input("PSI / PORT")

if is_epoc:
    with st.expander("🫁 EPOC (GOLD)", expanded=True):
        gold = st.selectbox("Clasificación GOLD", ["", "A (Pocos sint, bajo riesgo)", "B (Muchos sint, bajo riesgo)", "E (Riesgo exacerbaciones)"])

if is_tep or is_tvp:
    with st.expander("🩸 Enfermedad Tromboembólica Venosa", expanded=True):
        t1, t2, t3 = st.columns(3)
        wells_tep = t1.text_input("Wells (TEP)")
        pesi = t2.text_input("PESI / sPESI (TEP)")
        wells_tvp = t3.text_input("Wells (TVP)")

if is_hda:
    with st.expander("🩸 Hemorragia Digestiva Alta", expanded=True):
        hd1, hd2 = st.columns(2)
        blatchford = hd1.text_input("Glasgow-Blatchford")
        rockall = hd2.text_input("Score Rockall")

if is_cid:
    with st.expander("🩸 Coagulación Intravascular Diseminada", expanded=True):
        isth = st.selectbox("Score ISTH", ["", "Compatible con CID (≥5 puntos)", "No sugerente de CID (<5 puntos)"])

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Clínica / ARM", "🧪 Laboratorio Integral", "📋 Plan Final"])

with tab_clinca:
    st.subheader("(S) Subjetivo")
    subj = st.text_area("Novedades y Subjetivo:", "Paciente estable, sin cambios agudos.")

    st.subheader("💊 Infusiones y Drogas")
    st.caption("Escribe la dosis sólo en las drogas que use. Las vacías se borrarán solas.")
    i1, i2 = st.columns(2)
    
    sedo_def = "Fentanilo: \nRemifentanilo: \nMorfina: \nPropofol: \nMidazolam: \nDexmedetomidina: \nKetamina: \nBloq. NM (Atracurio/Rocuronio): "
    sedo = i1.text_area("Sedoanalgesia (PADIS)", sedo_def, height=220)
    
    vaso_def = "Noradrenalina: \nVasopresina: \nAdrenalina: \nDobutamina: \nMilrinona: \nLevosimendan: \nDopamina: \nNTG/NTP: \nLabetalol/Esmolol: "
    vaso = i2.text_area("Vasoactivos/Inotrópicos (AHA/SSC)", vaso_def, height=220)

    st.subheader("💉 Dispositivos e Invasiones")
    d1, d2, d3, d4 = st.columns(4)
    cvc_info = d1.text_input("CVC (Sitio/Día)")
    ca_info = d2.text_input("Cat. Art. (Sitio/Día)")
    sv_dias = d3.text_input("SV (Día)")
    sng_dias = d4.text_input("SNG (Día)")

    st.divider()
    
    st.subheader("1. Neurológico")
    n1, n2, n3, n4 = st.columns(4)
    neuro_estado = n1.text_input("Estado", "Alerta")
    glasgow = n2.text_input("Glasgow", "15/15")
    rass = n3.text_input("RASS", "0")
    cam = n4.text_input("CAM-ICU", "-")
    ex_neuro = st.text_area("Ex. Neuro", "Vigil, conectado, moviliza 4 miembros.")

    st.subheader("2. Hemodinamia y ECG")
    h1, h2, h3, h4, h5 = st.columns(5)
    ta = h1.text_input("TA (ej: 120/80)", placeholder="120/80")
    
    tam_val, pp_val = "", ""
    if "/" in ta:
        try:
            s, d = map(float, ta.split("/"))
            tam_val = round((s + 2*d)/3)
            pp_val = int(s - d)
            st.caption(f"💡 Calculado - TAM: {tam_val} mmHg | PP: {pp_val} mmHg")
        except: pass

    fc = h2.text_input("FC (lpm)")
    fr = h3.text_input("FR (rpm)")
    sat = h4.text_input("SatO2 (%)")
    temp = h5.text_input("Temp (°C)")

    h6, h7 = st.columns(2)
    relleno_cap = h6.text_input("Relleno Capilar", "< 2 seg")
    tdg = h7.text_input("Perfusión periférica (Livideces/TDG)", "Sin livideces")

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
    ex_cv = st.text_area("Ex. CV (Auscultación)", "R1 y R2 normofonéticos. Sin soplos ni R3.")

    st.subheader("3. Respiratorio (ARM)")
    r1, r2, r3, r4 = st.columns(4)
    via_aerea = r1.text_input("Vía Aérea", "TOT")
    modo = r2.text_input("Modo", "VCV")
    fio2 = r3.number_input("FiO2 (%)", 21, 100, 21)
    peep = r4.number_input("PEEP (cmH2O)", 0, 30, 5)
    r5, r6, r7, r8 = st.columns(4)
    ppico = r5.text_input("P.Pico (cmH2O)")
    pplat = r6.text_input("P.Plateau (cmH2O)")
    comp = r7.text_input("Comp. (ml/cmH2O)")
    vt = r8.text_input("Vt (ml)")
    r9, r10 = st.columns(2)
    dp_manual = r9.text_input("Driving P. (cmH2O)")
    pafi_manual = r10.text_input("PaFiO2")
    ex_resp = st.text_area("Ex. Resp", "Buena entrada de aire bilateral.")

    st.subheader("4. Abdominal, Renal y Nutrición")
    a1, a2, a3 = st.columns(3)
    ex_abd = a1.text_area("Abdominal", "Blando, depresible, indoloro.")
    ex_renal = a2.text_area("Renal / Diuresis", "Diuresis conservada.")
    nutricion = a3.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral / Dieta blanda", "Oral / Dieta general"])

    st.caption("💧 Balance Hídrico (24hs)")
    bh1, bh2, bh3 = st.columns(3)
    ingresos = bh1.text_input("Ingresos Totales (ml)", placeholder="Ej: 2500")
    egresos = bh2.text_input("Egresos Totales (ml)", placeholder="Ej: 1800")
    
    balance_val = ""
    if ingresos and egresos:
        try:
            balance_val = float(ingresos.replace(',','.')) - float(egresos.replace(',','.'))
            bh3.info(f"Balance: {balance_val:+.0f} ml")
        except: pass

    st.subheader("5. Infectología y Cultivos (IDSA/SADI)")
    i_1, i_2, i_3 = st.columns(3)
    tmax = i_1.text_input("T.Max 24h (°C)")
    atb1 = i_2.text_input("ATB 1 (Día)")
    atb2 = i_3.text_input("ATB 2 (Día)")
    
    st.caption("Panel de Cultivos (Solo se imprimirán los que completes)")
    c_1, c_2 = st.columns(2)
    cult_hemo = c_1.text_input("Hemocultivos")
    cult_uro = c_2.text_input("Urocultivo")
    c_3, c_4 = st.columns(2)
    cult_resp = c_3.text_input("Respiratorios (BAL/Mini-BAL)")
    cult_otros = c_4.text_input("Otros (LCR, Catéter, Piel/PB)")

with tab_lab:
    st.subheader("🌬️ EAB (Estado Ácido-Base)")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    ph = e1.text_input("pH")
    pco2 = e2.text_input("pCO2 (mmHg)")
    po2 = e3.text_input("pO2 (mmHg)")
    hco3 = e4.text_input("HCO3 (mEq/L)")
    eb = e5.text_input("EB (mEq/L)")
    lactato = e6.text_input("Lactato (mmol/L)")

    st.subheader("🩸 Hemograma y Coagulograma")
    l1, l2, l3, l4 = st.columns(4)
    hb = l1.text_input("Hb (g/dL)")
    hto = l2.text_input("Hto (%)")
    gb = l3.text_input("GB (/mm³)")
    plaq = l4.text_input("Plaq (/mm³)")
    
    st.caption("Fórmula Leucocitaria")
    f1, f2, f3, f4 = st.columns(4)
    neut = f1.text_input("Neut (%)")
    linf = f2.text_input("Linf (%)")
    mono = f3.text_input("Mono (%)")
    eos = f4.text_input("Eos (%)")
    
    st.caption("Coagulograma")
    c1, c2, c3 = st.columns(3)
    app = c1.text_input("APP (%)")
    kptt = c2.text_input("KPTT (seg)")
    rin = c3.text_input("RIN")

    st.subheader("🧪 Química y Hepatograma")
    q1, q2, q3, q4, q5, q6, q7 = st.columns(7)
    urea = q1.text_input("Urea (mg/dL)")
    cr = q2.text_input("Cr (mg/dL)")
    na = q3.text_input("Na (mEq/L)")
    k = q4.text_input("K (mEq/L)")
    cl = q5.text_input("Cl (mEq/L)")
    mg = q6.text_input("Mg (mg/dL)")
    ca = q7.text_input("Ca (mg/dL)")
    
    st.caption("Hepatograma")
    he1, he2, he3, he4, he5, he6 = st.columns(6)
    bt = he1.text_input("BT (mg/dL)")
    bd = he2.text_input("BD (mg/dL)")
    got = he3.text_input("GOT (UI/L)")
    gpt = he4.text_input("GPT (UI/L)")
    fal = he5.text_input("FAL (UI/L)")
    ggt = he6.text_input("GGT (UI/L)")

    st.subheader("🧬 Biomarcadores")
    b1, b2, b3, b4, b5, b6 = st.columns(6)
    cpk = b1.text_input("CPK (UI/L)")
    cpk_mb = b2.text_input("CPK-MB (UI/L)")
    tropo = b3.text_input("Tropo I (ng/mL)")
    probnp = b4.text_input("ProBNP (pg/mL)")
    ldh = b5.text_input("LDH (UI/L)")
    pct = b6.text_input("PCT (ng/mL)")

with tab_planes:
    st.subheader("🛡️ FAST HUG BID")
    
    fast_dict = {
        'F': 'Alimentación (Feeding)', 'A': 'Analgesia', 'S': 'Sedación',
        'T': 'Tromboprofilaxis', 'H': 'Cabecera a 30-45°', 'U': 'Úlceras estrés',
        'G': 'Control Glucémico', 'B': 'Bowel (Intestino)', 'I': 'Retiro Invasiones', 'D': 'Desescalamiento ATB'
    }
    
    f_cols = st.columns(5)
    fast_sel = []
    for i, (k, v) in enumerate(fast_dict.items()):
        if f_cols[i % 5].checkbox(k, help=v):
            fast_sel.append(f"{k} - {v}")

    st.divider()
    st.subheader("(A/P) Análisis y Plan")
    analisis = st.text_area("Análisis General")
    plan = st.text_area("Plan 24hs", "- Cultivar: \n- Imágenes: \n- Interconsultas:")

if st.button("🚀 GENERAR EVOLUCIÓN PARA GECLISA"):
    
    sedo_clean = " | ".join([line.strip() for line in sedo.split('\n') if line.strip() and not line.strip().endswith(':')])
    if not sedo_clean: sedo_clean = "Sin infusiones."
    
    vaso_clean = " | ".join([line.strip() for line in vaso.split('\n') if line.strip() and not line.strip().endswith(':')])
    if not vaso_clean: vaso_clean = "Sin infusiones."

    lista_cultivos = []
    if cult_hemo: lista_cultivos.append(f"Hemo: {cult_hemo}")
    if cult_uro: lista_cultivos.append(f"Uro: {cult_uro}")
    if cult_resp: lista_cultivos.append(f"Resp: {cult_resp}")
    if cult_otros: lista_cultivos.append(f"Otros: {cult_otros}")
    cultivos_final = " | ".join(lista_cultivos) if lista_cultivos else "Sin cultivos registrados/pendientes."

    txt_modulos = ""
    if is_isquemia and any([killip, grace, timi]): txt_modulos += f"\n[+] IAM -> Killip: {killip} | GRACE: {grace} | TIMI: {timi}"
    if is_ic and any([nyha, stevenson, aha_ic]): txt_modulos += f"\n[+] IC -> NYHA: {nyha} | Stevenson: {stevenson} | AHA: {aha_ic}"
    if is_fa and any([cha2ds2, hasbled]): txt_modulos += f"\n[+] FA -> CHA2DS2-VASc: {cha2ds2} | HAS-BLED: {hasbled}"
    if is_sepsis and any([qsofa, sofa, apache]): txt_modulos += f"\n[+] SEPSIS -> qSOFA: {qsofa} | SOFA: {sofa} | APACHE: {apache}"
    if is_renal and any([kdigo_ira, kdigo_erc]): txt_modulos += f"\n[+] NEFRO -> IRA: {kdigo_ira} | ERC: {kdigo_erc}"
    if is_hepato and any([child, meld]): txt_modulos += f"\n[+] HEPATO -> Child: {child} | MELD: {meld}"
    if is_pancreas and any([bisap, ranson, balthazar]): txt_modulos += f"\n[+] PANCREATITIS -> BISAP: {bisap} | Ranson: {ranson} | Balthazar: {balthazar}"
    if is_acv and any([nihss, mrs]): txt_modulos += f"\n[+] ACV -> NIHSS: {nihss} | mRS: {mrs}"
    if is_hsa and any([hunt, fisher]): txt_modulos += f"\n[+] HSA -> Hunt&Hess: {hunt} | Fisher: {fisher}"
    if is_nac and any([curb65, psi]): txt_modulos += f"\n[+] NAC -> CURB-65: {curb65} | PSI: {psi}"
    if is_epoc and gold: txt_modulos += f"\n[+] EPOC -> GOLD: {gold}"
    if is_tep and any([wells_tep, pesi]): txt_modulos += f"\n[+] TEP -> Wells: {wells_tep} | PESI: {pesi}"
    if is_tvp and wells_tvp: txt_modulos += f"\n[+] TVP -> Wells: {wells_tvp}"
    if is_hda and any([blatchford, rockall]): txt_modulos += f"\n[+] HDA -> Blatchford: {blatchford} | Rockall: {rockall}"
    if is_cid and isth: txt_modulos += f"\n[+] CID -> ISTH: {isth}"

    tam_txt = ""
    if "/" in ta:
        try:
            partes = ta.split("/")
            s_val, d_val = float(partes[0]), float(partes[1])
            tam_txt = f"(TAM {round((s_val+2*d_val)/3)} | PP {int(s_val-d_val)})"
        except: pass

    dp_final = dp_manual
    if not dp_final and pplat and peep:
        try: dp_final = str(int(float(str(pplat).replace(',','.')) - float(str(peep).replace(',','.'))))
        except: pass

    pafi_final = pafi_manual
    if not pafi_final and po2 and fio2:
        try: pafi_final = str(int(float(str(po2).replace(',','.')) / (float(fio2)/100)))
        except: pass

    balance_txt = ""
    if ingresos and egresos:
        try:
            bal = float(ingresos.replace(',','.')) - float(egresos.replace(',','.'))
            balance_txt = f" | Ingresos: {ingresos} ml / Egresos: {egresos} ml (Balance 24h: {bal:+.0f} ml)"
        except: pass

    nutri_txt = f" | Nutrición: {nutricion}" if nutricion else ""
    fast_texto = "\n".join([f"  ✓ {x}" for x in fast_sel]) if fast_sel else "  Sin marcar."

    texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Int: {dias_int} | Días ARM: {dias_arm}

DIAGNÓSTICO:{txt_modulos}
{diagnostico}

(S) SUBJETIVO: {subj}

(O) OBJETIVO:
>> INFUSIONES Y DROGAS:
Sedoanalgesia: {sedo_clean}
Vasoactivos: {vaso_clean}

>> INVASIONES: CVC: {cvc_info} | Cat.Art: {ca_info} | SV: {sv_dias} | SNG: {sng_dias}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}, CAM {cam}. {ex_neuro}
- HEMO: TA {ta} mmHg {tam_txt}, FC {fc} lpm, FR {fr} rpm, Sat {sat}%, Temp {temp}°C. 
  Perfusión: Relleno Capilar {relleno_cap}. {tdg}.
- ECG (AHA/ACC/HRS): Ritmo {ecg_ritmo}, Eje {ecg_eje}, PR {ecg_pr}ms, QRS {ecg_qrs_ms}ms, QTc {ecg_qtc}ms. ST: {ecg_st}, Onda T: {ecg_onda_t}. {ecg_otros}
- CV: {ex_cv}
- RESP: {via_aerea}, Modo {modo}, FiO2 {fio2}%, PEEP {peep} cmH2O, PPlat {pplat} cmH2O, Vt {vt} ml.
  Mecánica: P.Pico {ppico} cmH2O | Comp {comp} ml/cmH2O | DP {dp_final} cmH2O | PaFiO2 {pafi_final}. 
  Examen: {ex_resp}
- ABD Y NUTRICIÓN: {ex_abd}{nutri_txt}
- RENAL Y BALANCE: {ex_renal}{balance_txt}
- INFECTO: Tmax {tmax}°C | ATB: {atb1} / {atb2}
  Cultivos: {cultivos_final}

>> LABORATORIO Y MEDIO INTERNO:
- EAB: pH {ph} | pCO2 {pco2} mmHg | pO2 {po2} mmHg | HCO3 {hco3} mEq/L | EB {eb} mEq/L | Lac {lactato} mmol/L
- HEMOGRAMA: Hb {hb} g/dL | Hto {hto} % | GB {gb} /mm³ (N:{neut}% L:{linf}% M:{mono}% E:{eos}%) | Plaq {plaq} /mm³
- COAGULOGRAMA: TP/APP {app} % | KPTT {kptt} seg | RIN {rin}
- QUÍMICA: Urea {urea} mg/dL | Cr {cr} mg/dL | Na {na} mEq/L | K {k} mEq/L | Cl {cl} mEq/L | Mg {mg} mg/dL | Ca {ca} mg/dL
- HEPATOGRAMA: BT {bt} mg/dL | BD {bd} mg/dL | GOT {got} UI/L | GPT {gpt} UI/L | FAL {fal} UI/L | GGT {ggt} UI/L
- BIOMARCADORES: CPK {cpk} UI/L | CPK-MB {cpk_mb} UI/L | Tropo I {tropo} ng/mL | ProBNP {probnp} pg/mL | LDH {ldh} UI/L | PCT {pct} ng/mL

>> FAST HUG BID:
{fast_texto}

(A/P) ANÁLISIS Y PLAN:
{analisis}
PLAN:
{plan}
"""
    st.subheader("📋 Resultado listo para GECLISA:")
    st.info("Pasa el mouse sobre el cuadro de abajo y haz clic en el botón de copiar (📝) en la esquina superior derecha.")
    st.code(texto_final, language="markdown")
