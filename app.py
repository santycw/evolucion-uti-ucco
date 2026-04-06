import streamlit as st
import re
import json
import os

# Configuración de página con layout extendido
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO (Look Profesional SaaS Médico) ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stTextArea textarea, .stTextInput input { font-family: 'Consolas', monospace; font-size: 14px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: none; }
    div[data-testid="stForm"] { border-radius: 8px; background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("v2.1 | Flujo de Trabajo Integrado (Botón en Planificación)")

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📌 Contexto del Paciente")
    with st.container(border=True):
        dias_int_hosp = st.text_input("Días Int. (Hospital)", placeholder="Ej: 12")
        dias_int_uti = st.text_input("Días Int. (UTI/UCCO)", placeholder="Ej: 4")
        dias_arm = st.text_input("Días ARM", placeholder="Ej: 0 o dejar vacío si no usa")

    st.header("📋 Diagnóstico de Ingreso")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos (Activan scores):", "1. \n2. ", height=120)
        st.caption("Soporta siglas oficiales: SCA, EAP, AKI, NAC, EPOC, etc.")

# --- VARIABLE CONDICIONAL: PACIENTE VENTILADO ---
d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- INICIALIZACIÓN DE SCORES ---
sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = cha2ds2 = hasbled = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""

# --- CONEXIÓN A BASE DE DATOS LOCAL ---
@st.cache_data
def cargar_diccionario_medico():
    ruta_db = "diccionario.json"
    fallback_db = {
        "isquemia": ["sca", "scacest", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina", "angor", "coronario"],
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
    if os.path.exists(ruta_db):
        try:
            with open(ruta_db, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except: return fallback_db
    else: return fallback_db

db_terminologia = cargar_diccionario_medico()

diag_norm = diagnostico.lower()
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

# --- SCORES MÉDICOS ---
if any([is_isquemia, is_ic, is_fa, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_epoc, is_tep, is_tvp, is_hda, is_cid]):
    st.markdown("### ⚙️ Scores Clínicos Sugeridos")

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
tab_clinca, tab_lab, tab_planes = st.tabs(["🩺 Clínica y Examen", "🧪 Laboratorios Dinámicos", "📋 Plan y FAST-HUG"])

with tab_clinca:
    with st.container(border=True):
        st.subheader("(S) Subjetivo")
        subj = st.text_area("Novedades:", "Paciente estable, sin cambios agudos.", height=68)

    with st.container(border=True):
        st.subheader("💊 Infusiones y Dispositivos")
        i1, i2 = st.columns(2)
        sedo_def = "Fentanilo: \nRemifentanilo: \nMorfina: \nPropofol: \nMidazolam: \nDexmedetomidina: \nKetamina: "
        sedo = i1.text_area("Sedoanalgesia", sedo_def, height=180)
        vaso_def = "Noradrenalina: \nVasopresina: \nAdrenalina: \nDobutamina: \nMilrinona: \nLabetalol: "
        vaso = i2.text_area("Vasoactivos", vaso_def, height=180)

        st.caption("Invasiones")
        d1, d2, d3, d4 = st.columns(4)
        cvc_info = d1.text_input("CVC (Sitio/Día)")
        ca_info = d2.text_input("Cat. Art (Sitio/Día)")
        sv_dias = d3.text_input("SV (Día)")
        sng_dias = d4.text_input("SNG (Día)")

    with st.container(border=True):
        st.subheader("1. Neurológico y Hemodinamia")
        n1, n2, n3, n4 = st.columns(4)
        neuro_estado = n1.text_input("Estado", "Alerta")
        glasgow = n2.text_input("Glasgow", "15/15")
        rass = n3.text_input("RASS", "0")
        cam = n4.text_input("CAM-ICU", "-")

        h1, h2, h3, h4, h5 = st.columns(5)
        ta = h1.text_input("TA", placeholder="120/80")
        tam_val, pp_val = "", ""
        if "/" in ta:
            try:
                s, d = map(float, ta.split("/"))
                tam_val = round((s + 2*d)/3)
                pp_val = int(s - d)
            except: pass
        fc = h2.text_input("FC (lpm)")
        fr = h3.text_input("FR (rpm)")
        sat = h4.text_input("SatO2 (%)")
        temp = h5.text_input("Temp (°C)")

        ex_cv = st.text_area("Ex. Cardiovascular", "Relleno capilar <2s. Sin livideces. R1/R2 normofonéticos.")

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
            modo = r1.text_input("Modo", "VCV")
            peep = r2.number_input("PEEP (cmH2O)", 0, 30, 5)
            vt = r3.text_input("Vt (ml)")
            dp_manual = r4.text_input("Driving P. (cmH2O)")

            r5, r6, r7 = st.columns(3)
            ppico = r5.text_input("P.Pico (cmH2O)")
            pplat = r6.text_input("P.Plateau (cmH2O)")
            comp = r7.text_input("Comp. (ml/cmH2O)")

        ex_resp = st.text_input("Examen Respiratorio", "Buena entrada de aire bilateral.")

    with st.container(border=True):
        st.subheader("3. Digestivo, Renal e Infectología")
        a1, a2, a3 = st.columns(3)
        ex_abd = a1.text_input("Abdomen", "Blando, depresible.")
        nutricion = a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"])
        ex_renal = a3.text_input("Diuresis", "Conservada.")

        bh1, bh2 = st.columns(2)
        ingresos = bh1.text_input("Ingresos Totales (ml)")
        egresos = bh2.text_input("Egresos Totales (ml)")

        i_1, i_2 = st.columns(2)
        atb1 = i_1.text_input("ATB 1 y Día")
        atb2 = i_2.text_input("ATB 2 y Día")
        cult_hemo = st.text_input("Hemocultivos / Otros")

with tab_lab:
    st.info("💡 Completar únicamente los valores disponibles. Los campos en blanco no se imprimirán en el texto final.")
    with st.container(border=True):
        st.subheader("🌬️ EAB")
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        ph = e1.text_input("pH")
        pco2 = e2.text_input("pCO2")
        po2 = e3.text_input("pO2")
        hco3 = e4.text_input("HCO3")
        eb = e5.text_input("EB")
        lactato = e6.text_input("Lac")

    with st.container(border=True):
        st.subheader("🩸 Hemograma y Coagulación")
        l1, l2, l3, l4 = st.columns(4)
        hb = l1.text_input("Hb (g/dL)")
        hto = l2.text_input("Hto (%)")
        gb = l3.text_input("GB (/mm³)")
        plaq = l4.text_input("Plaq (/mm³)")

        f1, f2, f3, f4 = st.columns(4)
        neut = f1.text_input("Neut %")
        linf = f2.text_input("Linf %")
        mono = f3.text_input("Mono %")
        eos = f4.text_input("Eos %")

        c1, c2, c3 = st.columns(3)
        app = c1.text_input("APP (%)")
        kptt = c2.text_input("KPTT (s)")
        rin = c3.text_input("RIN")

    with st.container(border=True):
        st.subheader("🧪 Química y Biomarcadores")
        q1, q2, q3, q4, q5, q6 = st.columns(6)
        urea = q1.text_input("Urea")
        cr = q2.text_input("Cr")
        na = q3.text_input("Na")
        k = q4.text_input("K")
        cl = q5.text_input("Cl")
        mg = q6.text_input("Mg")

        he1, he2, he3, he4 = st.columns(4)
        bt = he1.text_input("BT")
        got = he2.text_input("GOT")
        gpt = he3.text_input("GPT")
        tropo = he4.text_input("Tropo I / PCT")

with tab_planes:
    with st.container(border=True):
        st.subheader("🛡️ FAST HUG BID")
        fast_dict = {
            'F': 'Feeding', 'A': 'Analgesia', 'S': 'Sedación',
            'T': 'Tromboprofilaxis', 'H': 'Head 30°', 'U': 'Úlceras estrés',
            'G': 'Glucemia', 'B': 'Bowel', 'I': 'Invasiones', 'D': 'Desescalar ATB'
        }
        f_cols = st.columns(5)
        fast_sel = []
        for i, (k, v) in enumerate(fast_dict.items()):
            if f_cols[i % 5].checkbox(k, help=v):
                fast_sel.append(f"{k} - {v}")

    with st.container(border=True):
        st.subheader("(A/P) Análisis y Plan")
        analisis = st.text_area("Análisis General")
        plan = st.text_area("Plan 24hs", "- Cultivar: \n- Interconsultas:")

    # --- EL BOTÓN AHORA ESTÁ ÚNICAMENTE DENTRO DE LA PESTAÑA PLANES ---
    st.divider()
    if st.button("🚀 GENERAR HISTORIA CLÍNICA (GECLISA)", use_container_width=True, type="primary"):

        dict_unidades = {
            "Fentanilo": "gammas/h", "Remifentanilo": "gammas/kg/min", "Morfina": "mg/h",
            "Propofol": "mg/kg/h", "Midazolam": "mg/h", "Dexmedetomidina": "gammas/kg/h",
            "Noradrenalina": "gammas/kg/min", "Vasopresina": "UI/min", "Adrenalina": "gammas/kg/min"
        }

        def procesar_drogas(texto_area):
            lista = []
            for line in texto_area.split('\n'):
                if ':' in line:
                    d, dosis = line.split(':', 1)
                    d, dosis = d.strip(), dosis.strip()
                    if dosis:
                        uni = dict_unidades.get(d, "") if not re.search(r'[a-zA-Z]', dosis) else ""
                        lista.append(f"{d}: {dosis} {uni}".strip())
            return " | ".join(lista) if lista else "Sin infusiones."

        sedo_clean = procesar_drogas(sedo)
        vaso_clean = procesar_drogas(vaso)

        # --- RUTINA DE LIMPIEZA DE LABORATORIO ---
        def construir_linea_lab(titulo, items):
            validos = [f"{nombre} {val} {uni}".strip() for nombre, val, uni in items if val.strip()]
            return f"- {titulo}: " + " | ".join(validos) if validos else ""

        l_eab = construir_linea_lab("EAB", [("pH", ph, ""), ("pCO2", pco2, "mmHg"), ("pO2", po2, "mmHg"), ("HCO3", hco3, "mEq/L"), ("EB", eb, "mEq/L"), ("Lac", lactato, "mmol/L")])

        gb_str = f"{gb} /mm³" if gb.strip() else ""
        if gb_str and any([neut.strip(), linf.strip(), mono.strip(), eos.strip()]):
            gb_str += f" (N:{neut}% L:{linf}% M:{mono}% E:{eos}%)"

        l_hemo = construir_linea_lab("HEMOGRAMA", [("Hb", hb, "g/dL"), ("Hto", hto, "%"), ("GB", gb_str, ""), ("Plaq", plaq, "/mm³")])
        l_coag = construir_linea_lab("COAGULOGRAMA", [("APP", app, "%"), ("KPTT", kptt, "s"), ("RIN", rin, "")])
        l_quim = construir_linea_lab("QUÍMICA", [("Urea", urea, "mg/dL"), ("Cr", cr, "mg/dL"), ("Na", na, "mEq/L"), ("K", k, "mEq/L"), ("Cl", cl, "mEq/L"), ("Mg", mg, "mg/dL")])
        l_hepa = construir_linea_lab("HEPATO/BIOMARC", [("BT", bt, "mg/dL"), ("GOT", got, "UI/L"), ("GPT", gpt, "UI/L"), ("Tropo/PCT", tropo, "")])

        lab_blocks = [l for l in [l_eab, l_hemo, l_coag, l_quim, l_hepa] if l]
        texto_laboratorio = "\n".join(lab_blocks) if lab_blocks else "Pendiente / No consta en el día de la fecha."

        # Bloque Scores
        txt_mod = ""
        if is_isquemia and any([killip, grace, timi]): txt_mod += f"\n[+] SCA/IAM -> Killip: {killip} | GRACE: {grace} | TIMI: {timi}"
        if is_ic and any([nyha, stevenson, aha_ic]): txt_mod += f"\n[+] IC -> NYHA: {nyha} | Stevenson: {stevenson} | AHA: {aha_ic}"
        if is_sepsis and any([qsofa, sofa, apache]): txt_mod += f"\n[+] SEPSIS -> qSOFA: {qsofa} | SOFA: {sofa} | APACHE: {apache}"
        if is_renal and any([kdigo_ira, kdigo_erc]): txt_mod += f"\n[+] NEFRO -> IRA: {kdigo_ira} | ERC: {kdigo_erc}"
        if is_hepato and any([child, meld]): txt_mod += f"\n[+] HEPATO -> Child: {child} | MELD: {meld}"
        if is_nac and any([curb65, psi]): txt_mod += f"\n[+] NAC -> CURB-65: {curb65} | PSI: {psi}"

        tam_txt = ""
        if "/" in ta:
            try:
                s, d = map(float, ta.split("/"))
                tam_txt = f"(TAM {round((s+2*d)/3)} | PP {int(s-d)})"
            except: pass

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
        fast_texto = "\n".join([f"  ✓ {x}" for x in fast_sel]) if fast_sel else "  Sin marcar."

        atb_txt = ""
        if atb1 or atb2: atb_txt = f"\n  ATB: {atb1} / {atb2}"

        texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Hosp: {dias_int_hosp} | Días UTI: {dias_int_uti} | Días ARM: {dias_arm}

DIAGNÓSTICO:{txt_mod}
{diagnostico}

(S) SUBJETIVO: {subj}

(O) OBJETIVO:
>> INFUSIONES Y DISPOSITIVOS:
Sedoanalgesia: {sedo_clean}
Vasoactivos: {vaso_clean}
Invasiones: CVC: {cvc_info} | Cat.Art: {ca_info} | SV: {sv_dias} | SNG: {sng_dias}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
- NEURO: {neuro_estado}, Glasgow {glasgow}, RASS {rass}, CAM {cam}.
- HEMO: TA {ta} mmHg {tam_txt}, FC {fc} lpm, FR {fr} rpm, Sat {sat}%, Temp {temp}°C.
  CV: {ex_cv}
- RESP: {texto_resp}
- ABD: {ex_abd}{nutri_txt}
- RENAL: {ex_renal}{balance_txt}
- INFECTO: {cult_hemo}{atb_txt}

>> LABORATORIO Y MEDIO INTERNO:
{texto_laboratorio}

>> FAST HUG BID:
{fast_texto}

(A/P) ANÁLISIS Y PLAN:
{analisis}
PLAN:
{plan}
"""
        st.success("✅ Evolución generada con éxito. Lista para exportar a GECLISA.")
        st.code(texto_final, language="markdown")
