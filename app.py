import streamlit as st
import datetime
from modules.evolucion import generar_texto_evolucion
from modules.infusiones import (
    calcular_infusion_universal,
    construir_detalle_infusion,
    evaluar_rango_infusion,
    obtener_diccionario_drogas,
    requiere_confirmacion_extra,
    texto_rango_infusion,
)
from modules.scores import calcular_scores_contexto, formatear_scores_detectados, motor_scores
from modules.scores_catalog import agrupar_catalogo_por_categoria, resumen_estado_catalogo
from modules.terminologia import cargar_diccionario_medico, detectar_en_db, normalizar_texto_medico
from modules.upp import (
    BRADEN_ACTIVIDAD,
    BRADEN_FRICCION,
    BRADEN_HUMEDAD,
    BRADEN_MOVILIDAD,
    BRADEN_NUTRICION,
    BRADEN_PERCEPCION,
    DECUBITOS,
    DOLOR_UPP,
    ESTADIOS_UPP,
    EXUDADOS_UPP,
    INFECCION_UPP,
    LATERALIDADES_UPP,
    LECHOS_UPP,
    MEDIDAS_PREVENCION,
    PERILESIONAL_UPP,
    SUPERFICIES_APOYO,
    FRECUENCIAS_CAMBIO,
    VISTAS_CORPORALES,
    calcular_braden,
    obtener_zonas_mapa,
    resumen_mapa_corporal,
)
from modules.validaciones import (
    calcular_par,
    calcular_qtc_bazett,
    calcular_tam_pp,
    formatear_alerta,
    generar_validaciones_datos_criticos,
)

# --- INICIALIZACIÓN DE ESTADOS DE SESIÓN ---
if 'rk' not in st.session_state:
    st.session_state['rk'] = 0
if 'evolucion_generada' not in st.session_state:
    st.session_state['evolucion_generada'] = False
if 'infusiones_automatizadas' not in st.session_state:
    st.session_state['infusiones_automatizadas'] = []
if 'limpiar_prellenado' not in st.session_state:
    st.session_state['limpiar_prellenado'] = False

def d_str(valor_default):
    """Retorna un string vacío si la orden de limpieza global está activa."""
    return "" if st.session_state.get('limpiar_prellenado', False) else valor_default

def rerun_app():
    """Reejecuta la app manteniendo compatibilidad con versiones de Streamlit."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

rk = st.session_state['rk']

# --- MÓDULOS V2.0: infusiones, terminología, validaciones, scores y evolución ---
# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
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
    div[data-testid="stExpander"] label,
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] .stMarkdown {
        color: #F0F2F6 !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-color: #333333 !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Estructura Completa Garantizada | Lab y ECG Extendidos | Auto-Scores | Guías ESC 2024")

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📌 Contexto del Paciente")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", min_value=18, max_value=120, value=65, step=1, key=f"edad_{rk}")
        sexo_paciente = st.selectbox("Sexo", ["Masculino", "Femenino"], key=f"sexo_{rk}")
        peso_paciente = st.number_input("Peso Estimado (kg)", min_value=1.0, value=70.0, step=1.0, key=f"peso_{rk}")
        fecha_hosp = st.date_input("Fecha de Ingreso Institución", format="DD/MM/YYYY", key=f"fhosp_{rk}")
        fecha_uti = st.date_input("Fecha de ingreso UTI/UCCO", format="DD/MM/YYYY", key=f"futi_{rk}")
        dias_arm = st.text_input("Días ARM", placeholder="Ej: 0 o dejar vacío", key=f"darm_{rk}")

    st.header("📋 Diagnóstico de Ingreso")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos (Escriba 'FA' para activar score):", d_str("1. \n2. "), height=120, key=f"diag_{rk}")

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days

d_arm_limpio = dias_arm.strip().lower()
paciente_ventilado = bool(d_arm_limpio and d_arm_limpio not in ["0", "-", "no"])

# --- INICIALIZACIÓN DE VARIABLES PARA DATOS FALTANTES ---
apache_cronico = 0
apache_ira = False
child_encef = "Ausente"
child_ascitis = "Ausente"
albumina = 0.0
meld_dialisis = False
bisap_derrame = False

# Scores manuales e inicialización de lógicos
sofa = qsofa = apache = killip = grace = timi = nyha = stevenson = aha_ic = ""
kdigo_ira = kdigo_erc = child = meld = bisap = ranson = balthazar = ""
nihss = mrs = hunt = fisher = curb65 = psi = gold = wells_tep = pesi = wells_tvp = blatchford = rockall = isth = ""
chf = hta = diabetes = stroke_fa = vascular = False

# Variables opcionales para scores UCCO/UTI ampliados
timi_riesgo_ge3 = timi_cad = timi_aspirina = timi_angina = timi_st = timi_marcadores = False
heart_historia = heart_ecg = heart_riesgo = heart_troponina = ""
hasbled_hta_no_controlada = hasbled_renal = hasbled_hepatica = False
hasbled_sangrado = hasbled_inr_labil = hasbled_drogas = hasbled_alcohol = False

db_terminologia = cargar_diccionario_medico()
diag_norm = normalizar_texto_medico(diagnostico)

is_isquemia = detectar_en_db("isquemia", diag_norm, db_terminologia)
is_ic = detectar_en_db("ic", diag_norm, db_terminologia)
is_sepsis = detectar_en_db("sepsis", diag_norm, db_terminologia)
is_renal = detectar_en_db("renal", diag_norm, db_terminologia)
is_hepato = detectar_en_db("hepato", diag_norm, db_terminologia)
is_pancreas = detectar_en_db("pancreas", diag_norm, db_terminologia)
is_acv = detectar_en_db("acv", diag_norm, db_terminologia)
is_hsa = detectar_en_db("hsa", diag_norm, db_terminologia)
is_nac = detectar_en_db("nac", diag_norm, db_terminologia)
is_fa = detectar_en_db("fa", diag_norm, db_terminologia)

# --- RECOLECCIÓN DE DATOS FALTANTES PARA SCORES ---
if any([is_isquemia, is_ic, is_sepsis, is_renal, is_hepato, is_pancreas, is_acv, is_hsa, is_nac, is_fa]):
    st.markdown("### ⚙️ Complemento de Scores")
    st.caption("Complete los datos faltantes para lograr un cálculo automático preciso, o ingrese el score manualmente para sobreescribir.")

if is_isquemia:
    with st.expander("🫀 Síndrome Coronario Agudo (SCA) / IAM", expanded=False):
        c1, c2, c3 = st.columns(3)
        killip = c1.selectbox("Killip y Kimball", ["", "I (Sin IC)", "II (R3/Estertores)", "III (EAP)", "IV (Shock)"], key=f"killip_{rk}")
        grace = c2.text_input("GRACE Manual", key=f"grace_{rk}")
        timi = c3.text_input("TIMI Manual", key=f"timi_{rk}")

        st.divider()
        st.caption("Cálculo automático opcional TIMI / HEART. Los criterios no marcados se consideran ausentes.")
        t_cols = st.columns(4)
        timi_riesgo_ge3 = t_cols[0].checkbox("TIMI: ≥3 factores de riesgo coronario", key=f"timi_riesgo_ge3_{rk}")
        timi_cad = t_cols[1].checkbox("TIMI: CAD conocida ≥50%", key=f"timi_cad_{rk}")
        timi_aspirina = t_cols[2].checkbox("TIMI: AAS últimos 7 días", key=f"timi_aspirina_{rk}")
        timi_angina = t_cols[3].checkbox("TIMI: ≥2 anginas 24 h", key=f"timi_angina_{rk}")
        t2_cols = st.columns(2)
        timi_st = t2_cols[0].checkbox("TIMI: desviación ST", key=f"timi_st_{rk}")
        timi_marcadores = t2_cols[1].checkbox("TIMI: biomarcadores positivos", key=f"timi_marcadores_{rk}")

        h1, h2, h3, h4 = st.columns(4)
        heart_historia = h1.selectbox("HEART Historia", ["", "0 pts - Baja sospecha", "1 pt - Moderada", "2 pts - Alta sospecha"], key=f"heart_historia_{rk}")
        heart_ecg = h2.selectbox("HEART ECG", ["", "0 pts - Normal", "1 pt - Alteraciones inespecíficas", "2 pts - ST significativo"], key=f"heart_ecg_{rk}")
        heart_riesgo = h3.selectbox("HEART Factores riesgo", ["", "0 pts - Sin factores", "1 pt - 1-2 factores", "2 pts - ≥3 factores o aterosclerosis"], key=f"heart_riesgo_{rk}")
        heart_troponina = h4.selectbox("HEART Troponina", ["", "0 pts - Normal", "1 pt - 1-3x límite", "2 pts - >3x límite"], key=f"heart_troponina_{rk}")
if is_ic:
    with st.expander("🫀 Insuficiencia Cardíaca", expanded=False):
        ic1, ic2, ic3 = st.columns(3)
        nyha = ic1.selectbox("Clase NYHA", ["", "I", "II", "III", "IV"], key=f"nyha_{rk}")
        stevenson = ic2.selectbox("Perfil Stevenson", ["", "A (Seco-Cal)", "B (Húm-Cal)", "C (Húm-Frío)", "L (Seco-Frío)"], key=f"stevenson_{rk}")
        aha_ic = ic3.selectbox("Estadio AHA", ["", "A", "B", "C", "D"], key=f"aha_{rk}")
if is_sepsis:
    with st.expander("🦠 Sepsis (APACHE II / SOFA)", expanded=False):
        st.info("Datos faltantes para cálculo automático de APACHE II:")
        col_a1, col_a2 = st.columns(2)
        apache_cronico = col_a1.selectbox("Puntaje Enfermedad Crónica", [0, 2, 5], format_func=lambda x: f"{x} pts (0=No, 2=Electiva, 5=NoQx/Urgencia)", key=f"apache_cronico_{rk}")
        apache_ira = col_a2.checkbox("Falla Renal Aguda (Duplica pts de Creatinina)", key=f"apache_ira_{rk}")
        st.divider()
        s1, s2, s3 = st.columns(3)
        qsofa = s1.text_input("qSOFA manual", key=f"qsofa_{rk}")
        sofa = s2.text_input("SOFA manual", key=f"sofa_{rk}")
        apache = s3.text_input("APACHE II manual", key=f"apache_{rk}")
if is_renal:
    with st.expander("🩸 Nefrología", expanded=False):
        ren1, ren2 = st.columns(2)
        kdigo_ira = ren1.selectbox("KDIGO (IRA)", ["", "1", "2", "3"], key=f"kdigo_ira_{rk}")
        kdigo_erc = ren2.selectbox("Estadio ERC", ["", "G1", "G2", "G3a", "G3b", "G4", "G5"], key=f"kdigo_erc_{rk}")
if is_hepato:
    with st.expander("🟡 Hepatopatía (Child-Pugh / MELD)", expanded=False):
        st.info("Datos faltantes para cálculo automático de MELD / Child-Pugh:")
        hp_c1, hp_c2, hp_c3 = st.columns(3)
        child_encef = hp_c1.selectbox("Encefalopatía", ["Ausente", "Grado I-II", "Grado III-IV"], key=f"child_encef_{rk}")
        child_ascitis = hp_c2.selectbox("Ascitis", ["Ausente", "Leve/Moderada", "Severa/Refractaria"], key=f"child_ascitis_{rk}")
        albumina = hp_c3.number_input("Albúmina (g/dL) para Score", min_value=0.0, value=0.0, step=0.1, key=f"albumina_{rk}")
        meld_dialisis = st.checkbox("Paciente en Diálisis (Calcula Cr como 4.0 para MELD)", key=f"meld_dialisis_{rk}")
        st.divider()
        hp1, hp2 = st.columns(2)
        child = hp1.selectbox("Child-Pugh Manual", ["", "A", "B", "C"], key=f"child_{rk}")
        meld = hp2.text_input("MELD Manual", key=f"meld_{rk}")
if is_pancreas:
    with st.expander("⚕️ Pancreatitis Aguda", expanded=False):
        st.info("Datos faltantes para cálculo de BISAP:")
        bisap_derrame = st.checkbox("Presencia de Derrame Pleural", key=f"bisap_derrame_{rk}")
        st.divider()
        p1, p2, p3 = st.columns(3)
        bisap = p1.text_input("BISAP Manual", key=f"bisap_{rk}")
        ranson = p2.text_input("Ranson Manual", key=f"ranson_{rk}")
        balthazar = p3.selectbox("Balthazar (TC)", ["", "A", "B", "C", "D", "E"], key=f"balthazar_{rk}")
if is_acv:
    with st.expander("🧠 ACV Isquémico", expanded=False):
        a1, a2 = st.columns(2)
        nihss = a1.text_input("NIHSS", key=f"nihss_{rk}")
        mrs = a2.selectbox("Rankin (mRS)", ["", "0", "1", "2", "3", "4", "5", "6"], key=f"mrs_{rk}")
if is_hsa:
    with st.expander("🧠 Hemorragia Subaracnoidea", expanded=False):
        hsa1, hsa2 = st.columns(2)
        hunt = hsa1.selectbox("Hunt & Hess", ["", "I", "II", "III", "IV", "V"], key=f"hunt_{rk}")
        fisher = hsa2.selectbox("Escala Fisher (TC)", ["", "I", "II", "III", "IV"], key=f"fisher_{rk}")
if is_nac:
    with st.expander("🫁 Neumonía (NAC)", expanded=False):
        n1, n2 = st.columns(2)
        curb65 = n1.text_input("CURB-65 manual", key=f"curb65_{rk}")
        psi = n2.text_input("PSI / PORT manual", key=f"psi_{rk}")
if is_fa:
    with st.expander("🫀 Fibrilación Auricular (CHA₂DS₂-VA | ESC 2024)", expanded=True):
        st.info("💡 **Nota:** La edad se lee de forma automática del panel lateral. Según Guías ESC 2024, se omite la categoría de sexo.")
        fa1, fa2 = st.columns(2)
        chf = fa1.checkbox("Insuf. Cardíaca / Disfunción VI (C - 1 pt)", key=f"chf_{rk}")
        hta = fa1.checkbox("Hipertensión Arterial (H - 1 pt)", key=f"hta_{rk}")
        diabetes = fa1.checkbox("Diabetes Mellitus (D - 1 pt)", key=f"diabetes_{rk}")
        stroke_fa = fa2.checkbox("ACV / TIA previo (S₂ - 2 pts)", key=f"stroke_fa_{rk}")
        vascular = fa2.checkbox("Enfermedad Vascular (V - 1 pt)", key=f"vascular_{rk}")

        st.divider()
        st.caption("HAS-BLED opcional para estimar riesgo hemorrágico. No contraindica anticoagulación: orienta corrección de factores modificables.")
        hb1, hb2, hb3 = st.columns(3)
        hasbled_hta_no_controlada = hb1.checkbox("HAS-BLED: HTA no controlada", key=f"hasbled_hta_{rk}")
        hasbled_renal = hb1.checkbox("HAS-BLED: función renal alterada", key=f"hasbled_renal_{rk}")
        hasbled_hepatica = hb1.checkbox("HAS-BLED: función hepática alterada", key=f"hasbled_hepatica_{rk}")
        hasbled_sangrado = hb2.checkbox("HAS-BLED: sangrado previo/predisposición", key=f"hasbled_sangrado_{rk}")
        hasbled_inr_labil = hb2.checkbox("HAS-BLED: INR lábil", key=f"hasbled_inr_{rk}")
        hasbled_drogas = hb3.checkbox("HAS-BLED: fármacos predisponentes", key=f"hasbled_drogas_{rk}")
        hasbled_alcohol = hb3.checkbox("HAS-BLED: alcohol", key=f"hasbled_alcohol_{rk}")

st.divider()

# --- CUERPO PRINCIPAL ---
tab_clinica, tab_lab, tab_estudios, tab_piel, tab_planes = st.tabs([
    "🩺 Clínica y Examen",
    "🧪 Laboratorio Integral",
    "🩻 ECG y Estudios",
    "🩹 Piel / UPP / Decúbito",
    "📋 Plan y FAST-HUG"
])

with tab_clinica:
    with st.container(border=True):
        st.subheader("(S) Subjetivo")
        subj = st.text_area("Novedades:", d_str("Paciente estable, sin intercurrencias agudas."), height=68, key=f"subj_{rk}")

    with st.container(border=True):
        st.subheader("💊 Infusiones y Dispositivos")
        with st.expander("🧮 Calculadora de Infusiones Farmacológicas (Por Ampollas)", expanded=False):
            dict_calc_drogas = obtener_diccionario_drogas()

            droga_sel = st.selectbox("Seleccione el fármaco y presentación:", list(dict_calc_drogas.keys()), key=f"droga_sel_{rk}")
            info_droga = dict_calc_drogas[droga_sel]
            unidad_activa = info_droga["unidad"]
            mg_base = info_droga["mg"]

            st.caption(f"Rango orientativo configurado: **{texto_rango_infusion(info_droga)}**")
            if info_droga.get("nota"):
                st.caption(f"Nota de seguridad: {info_droga['nota']}")

            c_calc1, c_calc2 = st.columns(2)
            cant_ampollas = c_calc1.number_input("Cantidad Ampollas", min_value=0.0, value=1.0, step=0.5, key=f"cant_amp_{rk}")
            volumen_ml = c_calc2.number_input("Volumen Dilución (ml)", min_value=0.0, value=100.0, step=10.0, key=f"vol_ml_{rk}")

            droga_mg = cant_ampollas * mg_base
            calc_modo = st.radio("Dirección del cálculo", [f"Calcular DOSIS ({unidad_activa})", "Calcular VELOCIDAD (ml/h)"], horizontal=True, key=f"calc_modo_{rk}")
            nombre_limpio = droga_sel.split(" (")[0]

            def mostrar_control_seguridad_infusion(dosis_resultado, velocidad_resultado, sufijo_key):
                evaluacion = evaluar_rango_infusion(dosis_resultado, info_droga)
                estado = evaluacion.get("estado")
                mensaje = evaluacion.get("mensaje", "")

                if estado == "ok":
                    st.success(f"✅ {mensaje}")
                elif estado == "critico":
                    st.error(f"🚨 {mensaje}")
                else:
                    st.warning(f"⚠️ {mensaje}")

                detalle = construir_detalle_infusion(
                    nombre_limpio,
                    dosis_resultado,
                    unidad_activa,
                    velocidad_resultado,
                    droga_mg,
                    volumen_ml,
                )

                if st.button(f"➕ Anexar {nombre_limpio}", type="secondary", key=f"btn_anex_{sufijo_key}_{rk}"):
                    if detalle not in st.session_state['infusiones_automatizadas']:
                        st.session_state['infusiones_automatizadas'].append(detalle)
                        rerun_app()

            if "DOSIS" in calc_modo:
                vel_mlh = st.number_input("Velocidad en bomba (ml/h)", min_value=0.0, value=0.0, step=1.0, key=f"vel_mlh_{rk}")
                if droga_mg > 0 and volumen_ml > 0:
                    dosis_calc = calcular_infusion_universal("DOSIS", droga_mg, volumen_ml, peso_paciente, vel_mlh, unidad_activa)
                    st.success(f"**Resultado:** {dosis_calc:.4f} {unidad_activa}")
                    mostrar_control_seguridad_infusion(dosis_calc, vel_mlh, "dosis")
            else:
                dosis_obj = st.number_input(f"Dosis indicada ({unidad_activa})", min_value=0.0, value=0.0, format="%.4f", key=f"dosis_obj_{rk}")
                if droga_mg > 0 and volumen_ml > 0:
                    vel_calc = calcular_infusion_universal("VELOCIDAD", droga_mg, volumen_ml, peso_paciente, dosis_obj, unidad_activa)
                    st.success(f"**Programar bomba a:** {vel_calc:.2f} ml/h")
                    mostrar_control_seguridad_infusion(dosis_obj, vel_calc, "velocidad")

            if st.session_state['infusiones_automatizadas']:
                st.caption("📋 **En memoria:**")
                for inf in st.session_state['infusiones_automatizadas']:
                    st.markdown(f"- `{inf}`")
                if st.button("🗑️ Borrar memoria", key=f"btn_del_mem_{rk}"):
                    st.session_state['infusiones_automatizadas'] = []
                    rerun_app()

        st.caption("Invasiones / Accesos")
        d1, d2, d3, d4 = st.columns(4)
        cvc_info = d1.text_input("CVC (Sitio/Día)", key=f"cvc_info_{rk}")
        ca_info = d2.text_input("Cat. Art (Sitio/Día)", key=f"ca_info_{rk}")
        sv_dias = d3.text_input("SV (Día)", key=f"sv_dias_{rk}")
        sng_dias = d4.text_input("SNG (Día)", key=f"sng_dias_{rk}")

    with st.container(border=True):
        st.subheader("1. Neurológico y Hemodinamia")
        n1, n2, n3, n4 = st.columns(4)
        neuro_estado = n1.text_input("Estado", d_str("Alerta"), key=f"neuro_{rk}")
        glasgow = n2.text_input("Glasgow", d_str("15/15"), key=f"glasgow_{rk}")
        rass = n3.text_input("RASS", d_str("0"), key=f"rass_{rk}")
        cam = n4.text_input("CAM-ICU", d_str("-"), key=f"cam_{rk}")

        h1, h2, h3, h4, h5 = st.columns(5)
        ta = h1.text_input("TA", placeholder="120/80", key=f"ta_{rk}")
        fc = h2.text_input("FC (lpm)", key=f"fc_{rk}")
        fr = h3.text_input("FR (rpm)", key=f"fr_{rk}")
        sat = h4.text_input("SatO2 (%)", key=f"sat_{rk}")
        temp = h5.text_input("Temp (°C)", key=f"temp_{rk}")

        v1, v2, v3 = st.columns(3)
        pvc = v1.text_input("PVC (cmH2O)", key=f"pvc_{rk}")
        relleno_cap = v2.text_input("Relleno Capilar", d_str("< 2 seg"), key=f"relleno_{rk}")

        _, _, tam_tmp, _ = calcular_tam_pp(ta)
        par_ui_str = calcular_par(fc, pvc, tam_tmp)
        v3.text_input("PAR (Auto)", value=par_ui_str, disabled=True, help="Fórmula: (FC × PVC) / TAM", key=f"par_{rk}")

        ex_cv = st.text_area("Ex. Cardiovascular", d_str("Sin livideces. R1/R2 normofonéticos."), key=f"ex_cv_{rk}")

    with st.container(border=True):
        st.subheader("2. Respiratorio y ARM")
        r_b1, r_b2, r_b3 = st.columns(3)
        if paciente_ventilado:
            via_aerea = r_b1.text_input("Vía Aérea", d_str("TOT"), key=f"va_{rk}")
        else:
            via_aerea = r_b1.selectbox("Dispositivo O2", ["AA (Aire Ambiente)", "Cánula Nasal", "Máscara Venturi 24%", "Máscara Venturi 28%", "Máscara Venturi 31%", "Máscara Venturi 35%", "Máscara Venturi 40%", "Máscara Venturi 50%", "Máscara Reservorio", "CAF", "VNI", "TQTAA"], key=f"va_{rk}")

        fio2 = r_b2.number_input("FiO2 (%)", 21, 100, 21, key=f"fio2_{rk}")
        pafi_manual = r_b3.text_input("PaFiO2 (Opcional)", key=f"pafi_man_{rk}")

        modo = peep = ppico = pplat = comp = vt = dp_manual = ""
        if paciente_ventilado:
            r1, r2, r3, r4 = st.columns(4)
            modo = r1.text_input("Modo", d_str("VCV"), key=f"modo_{rk}")
            peep = r2.number_input("PEEP (cmH2O)", 0, 30, 5, key=f"peep_{rk}")
            vt = r3.text_input("Vt (ml)", key=f"vt_{rk}")
            dp_manual = r4.text_input("Driving P.", key=f"dp_{rk}")
            r5, r6, r7 = st.columns(3)
            ppico = r5.text_input("P.Pico (cmH2O)", key=f"ppico_{rk}")
            pplat = r6.text_input("P.Plateau (cmH2O)", key=f"pplat_{rk}")
            comp = r7.text_input("Comp.", key=f"comp_{rk}")

        ex_resp = st.text_input("Examen Respiratorio", d_str("Buena entrada de aire bilateral."), key=f"ex_resp_{rk}")

    with st.container(border=True):
        st.subheader("3. Digestivo y Nutrición")
        a1, a2 = st.columns(2)
        ex_abd = a1.text_input("Abdomen", d_str("Blando, depresible."), key=f"ex_abd_{rk}")
        nutricion = a2.selectbox("Nutrición", ["", "Ayuno", "SNG / Enteral", "NPT", "Oral"], key=f"nutri_{rk}")

    with st.container(border=True):
        st.subheader("4. Renal y Balance Hídrico")
        ex_renal = st.text_input("Examen Renal", d_str("Conservado."), key=f"ex_ren_{rk}")
        st.caption("Egresos y Balance (ml)")
        bh1, bh2, bh3, bh4 = st.columns(4)
        ingresos = bh1.text_input("Ingresos Totales", key=f"ing_{rk}")
        diuresis = bh2.text_input("Diuresis", key=f"diu_{rk}")
        drenajes = bh3.text_input("Drenajes", key=f"dre_{rk}")
        catarsis = bh4.text_input("Catarsis", key=f"cat_{rk}")

    with st.container(border=True):
        st.subheader("5. Infectología")
        tmax = st.text_input("Temp. Máxima 24h (°C)", key=f"tmax_{rk}")

        st.caption("Esquema Antibiótico (Completar según necesidad)")
        atb_col1, atb_col2, atb_col3, atb_col4 = st.columns(4)
        atb1 = atb_col1.text_input("ATB 1 y Día", key=f"atb1_{rk}")
        atb2 = atb_col2.text_input("ATB 2 y Día", key=f"atb2_{rk}")
        atb3 = atb_col3.text_input("ATB 3 y Día", key=f"atb3_{rk}")
        atb4 = atb_col4.text_input("ATB 4 y Día", key=f"atb4_{rk}")

        st.caption("Cultivos")
        c_1, c_2 = st.columns(2)
        cult_hemo = c_1.text_input("Hemocultivos", key=f"cult_hemo_{rk}")
        cult_uro = c_2.text_input("Urocultivo", key=f"cult_uro_{rk}")
        c_3, c_4 = st.columns(2)
        cult_resp = c_3.text_input("Respiratorios (BAL/Mini-BAL)", key=f"cult_resp_{rk}")
        cult_otros = c_4.text_input("Otros (LCR, Catéter, Piel/PB)", key=f"cult_otros_{rk}")

# --- LABORATORIO EXTENDIDO ---
with tab_lab:
    st.info("💡 Solo se imprimirán en la evolución los valores que completes explícitamente.")
    with st.container(border=True):
        st.subheader("🌬️ EAB (Estado Ácido-Base)")
        e1, e2, e3, e4, e5, e6, e7 = st.columns(7)
        ph = e1.text_input("pH", key=f"ph_{rk}")
        pco2 = e2.text_input("pCO2 (mmHg)", key=f"pco2_{rk}")
        po2 = e3.text_input("pO2 (mmHg)", key=f"po2_{rk}")
        sato2_eab = e4.text_input("SatO2 (%)", key=f"eab_sato2_{rk}")
        hco3 = e5.text_input("HCO3 (mEq/L)", key=f"hco3_{rk}")
        eb = e6.text_input("EB (mEq/L)", key=f"eb_{rk}")
        lactato = e7.text_input("Lac (mmol/L)", key=f"lac_{rk}")

    with st.container(border=True):
        st.subheader("🩸 Hemograma y Coagulación")
        l1, l2, l3, l4 = st.columns(4)
        hb = l1.text_input("Hb (g/dL)", key=f"hb_{rk}")
        hto = l2.text_input("Hto (%)", key=f"hto_{rk}")
        gb = l3.text_input("GB (/mm³)", key=f"gb_{rk}")
        plaq = l4.text_input("Plaq (/mm³)", key=f"plaq_{rk}")

        c1, c2, c3 = st.columns(3)
        app = c1.text_input("APP (%)", key=f"app_{rk}")
        kptt = c2.text_input("KPTT (s)", key=f"kptt_{rk}")
        rin = c3.text_input("RIN", key=f"rin_{rk}")

    with st.container(border=True):
        st.subheader("🧪 Química Plasmática y Electrólitos")
        q1, q2, q3, q4, q5, q6 = st.columns(6)
        urea = q1.text_input("Urea (mg/dL)", key=f"urea_{rk}")
        cr = q2.text_input("Cr (mg/dL)", key=f"cr_{rk}")
        gluc = q3.text_input("Glucemia (mg/dL)", key=f"gluc_{rk}")
        na = q4.text_input("Na (mEq/L)", key=f"na_{rk}")
        potasio = q5.text_input("K (mEq/L)", key=f"k_{rk}")
        cl = q6.text_input("Cl (mEq/L)", key=f"cl_{rk}")

        qe1, qe2, qe3, qe4 = st.columns(4)
        mg = qe1.text_input("Mg (mg/dL)", key=f"mg_{rk}")
        ca_tot = qe2.text_input("Calcemia (mg/dL)", key=f"ca_tot_{rk}")
        ca_io = qe3.text_input("Ca++ Iónico (mmol/L)", key=f"ca_io_{rk}")
        fosforo = qe4.text_input("Fosfatemia (mg/dL)", key=f"p_{rk}")

    with st.container(border=True):
        st.subheader("🟡 Hepatograma, Proteínas y Biomarcadores")
        he1, he2, he3, he4, he5, he6 = st.columns(6)
        bt = he1.text_input("BT (mg/dL)", key=f"bt_{rk}")
        bd = he2.text_input("BD (mg/dL)", key=f"bd_{rk}")
        got = he3.text_input("GOT (UI/L)", key=f"got_{rk}")
        gpt = he4.text_input("GPT (UI/L)", key=f"gpt_{rk}")
        fal = he5.text_input("FAL (UI/L)", key=f"fal_{rk}")
        ggt = he6.text_input("GGT (UI/L)", key=f"ggt_{rk}")

        pi1, pi2, pi3, pi4 = st.columns(4)
        prot_tot = pi1.text_input("Prot. Totales (g/dL)", key=f"prot_{rk}")
        albumina_lab = pi2.text_input("Albúmina (g/dL)", key=f"alb_lab_{rk}")
        vsg = pi3.text_input("VSG (mm/h)", key=f"vsg_{rk}")
        pcr = pi4.text_input("PCR (mg/L)", key=f"pcr_{rk}")

        b1, b2, b3, b4, b5, b6 = st.columns(6)
        ldh = b1.text_input("LDH (UI/L)", key=f"ldh_{rk}")
        cpk = b2.text_input("CPK (UI/L)", key=f"cpk_{rk}")
        cpk_mb = b3.text_input("CPK-MB (UI/L)", key=f"cpk_mb_{rk}")
        tropo = b4.text_input("Tropo I (ng/mL)", key=f"tropo_{rk}")
        bnp = b5.text_input("proBNP (pg/mL)", key=f"bnp_{rk}")
        pct = b6.text_input("PCT (ng/mL)", key=f"pct_{rk}")

with tab_estudios:
    with st.container(border=True):
        st.subheader("📊 Electrocardiograma (ECG)")
        e_col0, e_col1, e_col2, e_col3 = st.columns(4)
        ecg_fc = e_col0.text_input("FC (lpm)", key=f"ecg_fc_{rk}", help="Se usa para calcular QTc")
        ecg_ritmo = e_col1.text_input("Ritmo", key=f"ecg_ritmo_{rk}")
        ecg_eje = e_col2.text_input("Eje (°)", key=f"ecg_eje_{rk}")
        ecg_pr = e_col3.text_input("PR (ms)", key=f"ecg_pr_{rk}")

        e_col4, e_col5, e_col6, e_col7, e_col8 = st.columns(5)
        ecg_qrs_ms = e_col4.text_input("QRS (ms)", key=f"ecg_qrs_{rk}")
        ecg_qt = e_col5.text_input("QT (ms)", key=f"ecg_qt_{rk}")

        qtc_ui_str = calcular_qtc_bazett(ecg_fc, ecg_qt)

        ecg_qtc = e_col6.text_input("QTc Auto (ms)", value=qtc_ui_str, disabled=True, help="Bazett: QT / √RR", key=f"ecg_qtc_{rk}")
        ecg_onda_p = e_col7.text_input("Onda P (ms)", key=f"ecg_ondap_{rk}")
        ecg_st = e_col8.text_input("Segmento ST", key=f"ecg_st_{rk}")

        ecg_conclusiones = st.text_area("Conclusiones ECG", height=68, key=f"ecg_conc_{rk}")

    with st.container(border=True):
        st.subheader("🩻 Imágenes y Procedimientos")
        rx_torax = st.text_area("Rx Tórax / Radiografías", height=68, key=f"rx_{rk}")
        tc = st.text_area("Tomografía (TC)", height=68, key=f"tc_{rk}")
        eco = st.text_area("Ecografía / POCUS", height=68, key=f"eco_{rk}")


# --- PIEL / UPP / DECÚBITO ---
with tab_piel:
    st.info("💡 Módulo simple para registrar piel, decúbito, prevención de UPP, lesiones y score de Braden.")

    with st.container(border=True):
        st.subheader("🩹 Estado de piel y decúbito")
        piel_estado = st.text_area(
            "Estado general de piel",
            d_str("Piel íntegra, sin lesiones por presión visibles."),
            height=70,
            key=f"piel_estado_{rk}",
        )

        d_col1, d_col2, d_col3 = st.columns(3)
        decubito_actual = d_col1.selectbox("Decúbito actual", DECUBITOS, key=f"decubito_actual_{rk}")
        cambios_posturales = d_col2.selectbox("Cambios posturales", FRECUENCIAS_CAMBIO, key=f"cambios_posturales_{rk}")
        superficie_apoyo = d_col3.selectbox("Superficie de apoyo", SUPERFICIES_APOYO, key=f"superficie_apoyo_{rk}")

        upp_medidas_prevencion = st.multiselect(
            "Medidas preventivas",
            MEDIDAS_PREVENCION,
            default=[],
            key=f"upp_medidas_prevencion_{rk}",
        )
        upp_conducta_general = st.text_area(
            "Conducta general piel / UPP",
            placeholder="Ej: continuar cambios posturales c/2 h, protección sacra, descarga de talones...",
            height=68,
            key=f"upp_conducta_general_{rk}",
        )

    with st.container(border=True):
        st.subheader("📊 Score de Braden")
        st.caption("Escala de 6 a 23 puntos. A menor puntaje, mayor riesgo de lesión por presión.")

        b1, b2, b3 = st.columns(3)
        braden_percepcion = b1.selectbox("Percepción sensorial", BRADEN_PERCEPCION, key=f"braden_percepcion_{rk}")
        braden_humedad = b2.selectbox("Humedad", BRADEN_HUMEDAD, key=f"braden_humedad_{rk}")
        braden_actividad = b3.selectbox("Actividad", BRADEN_ACTIVIDAD, key=f"braden_actividad_{rk}")

        b4, b5, b6 = st.columns(3)
        braden_movilidad = b4.selectbox("Movilidad", BRADEN_MOVILIDAD, key=f"braden_movilidad_{rk}")
        braden_nutricion = b5.selectbox("Nutrición", BRADEN_NUTRICION, key=f"braden_nutricion_{rk}")
        braden_friccion = b6.selectbox("Fricción / cizalla", BRADEN_FRICCION, key=f"braden_friccion_{rk}")

        braden_resultado = calcular_braden(
            braden_percepcion,
            braden_humedad,
            braden_actividad,
            braden_movilidad,
            braden_nutricion,
            braden_friccion,
        )
        braden_puntaje = braden_resultado.get("puntaje")
        braden_texto = f"Braden: {braden_puntaje}/23 - {braden_resultado.get('riesgo')}" if braden_puntaje is not None else "Braden no calculado"

        if braden_resultado.get("nivel") in ["critico"]:
            st.error(braden_texto)
        elif braden_resultado.get("nivel") in ["alto", "intermedio"]:
            st.warning(braden_texto)
        else:
            st.success(braden_texto)
        st.caption(braden_resultado.get("detalle", ""))

        with st.expander("🔎 Ver componentes de Braden", expanded=False):
            for componente, valor in braden_resultado.get("componentes", {}).items():
                st.markdown(f"- **{componente}:** {valor} pts")

    with st.container(border=True):
        st.subheader("🗺️ Mapa corporal de lesiones por presión / piel")
        st.caption("Seleccione la vista corporal y luego la zona anatómica del mapa para cada lesión. Esto se volcará automáticamente en la evolución final.")

        mapa_resumen = resumen_mapa_corporal()
        mp1, mp2 = st.columns(2)
        with mp1:
            st.markdown("**Vista anterior**")
            st.caption(mapa_resumen.get("Anterior", ""))
            st.markdown("**Vista lateral derecha**")
            st.caption(mapa_resumen.get("Lateral derecha", ""))
            st.markdown("**Vista lateral izquierda**")
            st.caption(mapa_resumen.get("Lateral izquierda", ""))
        with mp2:
            st.markdown("**Vista posterior**")
            st.caption(mapa_resumen.get("Posterior", ""))
            st.markdown("**Cabeza / cara / dispositivos**")
            st.caption(mapa_resumen.get("Cabeza / cara / dispositivos", ""))

        cantidad_lesiones_upp = st.number_input(
            "Cantidad de lesiones a registrar",
            min_value=0,
            max_value=8,
            value=0,
            step=1,
            key=f"cantidad_lesiones_upp_{rk}",
        )

        upp_lesiones = []
        for idx in range(int(cantidad_lesiones_upp)):
            with st.expander(f"Lesión {idx + 1}", expanded=True):
                l1, l2, l3 = st.columns(3)
                vista = l1.selectbox("Vista corporal", VISTAS_CORPORALES, key=f"upp_vista_{idx}_{rk}")
                zonas_vista = obtener_zonas_mapa(vista)
                localizacion = l2.selectbox("Zona anatómica del mapa", zonas_vista, key=f"upp_loc_{idx}_{rk}")
                lateralidad = l3.selectbox("Lado", LATERALIDADES_UPP, key=f"upp_lado_{idx}_{rk}")

                estadio = st.selectbox("Grado / estadio / tipo", ESTADIOS_UPP, key=f"upp_estadio_{idx}_{rk}")
                detalle_topografico = st.text_input(
                    "Detalle anatómico adicional (opcional)",
                    placeholder="Ej: paramediana sacra derecha, región trocantérica posterior, borde externo del talón...",
                    key=f"upp_detalle_topografico_{idx}_{rk}",
                )

                m1, m2, m3 = st.columns(3)
                largo_cm = m1.text_input("Largo (cm)", key=f"upp_largo_{idx}_{rk}")
                ancho_cm = m2.text_input("Ancho (cm)", key=f"upp_ancho_{idx}_{rk}")
                profundidad_cm = m3.text_input("Profundidad (cm)", key=f"upp_prof_{idx}_{rk}")

                c1, c2, c3 = st.columns(3)
                lecho = c1.selectbox("Características del lecho", LECHOS_UPP, key=f"upp_lecho_{idx}_{rk}")
                exudado = c2.selectbox("Exudado", EXUDADOS_UPP, key=f"upp_exudado_{idx}_{rk}")
                perilesional = c3.selectbox("Piel perilesional", PERILESIONAL_UPP, key=f"upp_perilesional_{idx}_{rk}")

                c4, c5 = st.columns(2)
                infeccion = c4.selectbox("Signos de infección", INFECCION_UPP, key=f"upp_infeccion_{idx}_{rk}")
                dolor = c5.selectbox("Dolor", DOLOR_UPP, key=f"upp_dolor_{idx}_{rk}")

                observaciones = st.text_area("Observaciones / características adicionales", height=68, key=f"upp_obs_{idx}_{rk}")
                conducta = st.text_area("Conducta / curación indicada", height=68, key=f"upp_cond_{idx}_{rk}")

                upp_lesiones.append({
                    "vista": vista,
                    "localizacion": localizacion,
                    "lateralidad": lateralidad,
                    "detalle_topografico": detalle_topografico,
                    "estadio": estadio,
                    "largo_cm": largo_cm,
                    "ancho_cm": ancho_cm,
                    "profundidad_cm": profundidad_cm,
                    "lecho": lecho,
                    "exudado": exudado,
                    "perilesional": perilesional,
                    "infeccion": infeccion,
                    "dolor": dolor,
                    "observaciones": observaciones,
                    "conducta": conducta,
                })


# --- RUTINA CENTRAL DE AUTO-CÁLCULO V2.0 ---
flags_scores = {
    "is_isquemia": is_isquemia,
    "is_ic": is_ic,
    "is_sepsis": is_sepsis,
    "is_renal": is_renal,
    "is_hepato": is_hepato,
    "is_pancreas": is_pancreas,
    "is_acv": is_acv,
    "is_hsa": is_hsa,
    "is_nac": is_nac,
    "is_fa": is_fa,
}

manuales_scores = {
    "sofa": sofa,
    "qsofa": qsofa,
    "apache": apache,
    "killip": killip,
    "grace": grace,
    "timi": timi,
    "nyha": nyha,
    "stevenson": stevenson,
    "aha_ic": aha_ic,
    "kdigo_ira": kdigo_ira,
    "kdigo_erc": kdigo_erc,
    "child": child,
    "meld": meld,
    "bisap": bisap,
    "ranson": ranson,
    "balthazar": balthazar,
    "nihss": nihss,
    "mrs": mrs,
    "hunt": hunt,
    "fisher": fisher,
    "curb65": curb65,
    "psi": psi,
}

datos_score = {
    "ta": ta,
    "glasgow": glasgow,
    "fio2": fio2,
    "pafi_manual": pafi_manual,
    "po2": po2,
    "plaq": plaq,
    "bt": bt,
    "cr": cr,
    "fr": fr,
    "fc": fc,
    "pvc": pvc,
    "urea": urea,
    "edad_paciente": edad_paciente,
    "temp": temp,
    "ph": ph,
    "pco2": pco2,
    "na": na,
    "potasio": potasio,
    "hto": hto,
    "gb": gb,
    "rin": rin,
    "paciente_ventilado": paciente_ventilado,
    "infusiones_automatizadas": st.session_state.get("infusiones_automatizadas", []),
    "apache_cronico": apache_cronico,
    "apache_ira": apache_ira,
    "meld_dialisis": meld_dialisis,
    "albumina": albumina,
    "child_encef": child_encef,
    "child_ascitis": child_ascitis,
    "bisap_derrame": bisap_derrame,
    "is_fa": is_fa,
    "chf": chf,
    "hta": hta,
    "diabetes": diabetes,
    "stroke_fa": stroke_fa,
    "vascular": vascular,
    "sexo_paciente": sexo_paciente,
    "sat": sat,
    "lactato": lactato,
    "tropo": tropo,
    "via_aerea": via_aerea,
    "is_isquemia": is_isquemia,
    "timi_riesgo_ge3": timi_riesgo_ge3,
    "timi_cad": timi_cad,
    "timi_aspirina": timi_aspirina,
    "timi_angina": timi_angina,
    "timi_st": timi_st,
    "timi_marcadores": timi_marcadores,
    "heart_historia": heart_historia,
    "heart_ecg": heart_ecg,
    "heart_riesgo": heart_riesgo,
    "heart_troponina": heart_troponina,
    "hasbled_hta_no_controlada": hasbled_hta_no_controlada,
    "hasbled_renal": hasbled_renal,
    "hasbled_hepatica": hasbled_hepatica,
    "hasbled_sangrado": hasbled_sangrado,
    "hasbled_inr_labil": hasbled_inr_labil,
    "hasbled_drogas": hasbled_drogas,
    "hasbled_alcohol": hasbled_alcohol,
}

auto_scores = calcular_scores_contexto(datos_score)

# Variables derivadas disponibles para UI/generación.
sys_bp = auto_scores["sys_bp"]
dia_bp = auto_scores["dia_bp"]
tam_val = auto_scores["tam_val"]
pp_val = auto_scores["pp_val"]
pafi_final = auto_scores["pafi_final"]
fc_n = auto_scores["fc_n"]
pvc_n = auto_scores["pvc_n"]

# --- VALIDACIÓN DE DATOS CRÍTICOS Y ALERTAS DE SEGURIDAD V2.0 ---
datos_validacion = dict(datos_score)
datos_validacion.update({
    "sat": sat,
    "gluc": gluc,
    "hb": hb,
    "lactato": lactato,
    "ecg_qtc": ecg_qtc,
})
alertas_seguridad = generar_validaciones_datos_criticos(datos_validacion, auto_scores)


def mostrar_item_score(item, categoria, indice):
    """Renderiza una tarjeta de score con origen, riesgo, faltantes y detalle desplegable."""
    nombre = item.get("nombre", "Score")
    valor = item.get("valor", "")
    origen = item.get("origen", "")
    nivel = item.get("nivel", "info")
    interpretacion = item.get("interpretacion", "")
    faltantes = item.get("faltantes_bloqueantes") or []

    encabezado = f"**{nombre}:** `{valor}` · **Origen:** {origen}"
    cuerpo = f"{encabezado}  \n{interpretacion}"

    if nivel in ["critico"]:
        st.error(cuerpo)
    elif nivel in ["alto", "intermedio"]:
        st.warning(cuerpo)
    elif nivel == "bajo":
        st.success(cuerpo)
    elif nivel in ["bloqueado", "pendiente"]:
        st.info(cuerpo)
    else:
        st.info(cuerpo)

    if faltantes:
        st.caption("Datos faltantes que bloquean interpretación: " + ", ".join(faltantes))

    toggle_label = f"🔎 Ver cómo se calculó {nombre}"
    key = f"detalle_score_{categoria}_{nombre}_{indice}_{rk}".replace(" ", "_").replace("/", "_")
    ver_detalle = st.toggle(toggle_label, key=key) if hasattr(st, "toggle") else st.checkbox(toggle_label, key=key)
    if ver_detalle:
        detalle = item.get("detalle") or []
        faltantes_generales = item.get("faltantes") or []
        catalogo = item.get("catalogo") or {}

        if catalogo:
            estado = str(catalogo.get("estado", "")).replace("_", " ")
            st.markdown(f"**Biblioteca:** {catalogo.get('categoria', 'Sin categoría')} · **Estado:** {estado}")
            if catalogo.get("uso_clinico"):
                st.caption(catalogo.get("uso_clinico"))
            requeridos = catalogo.get("inputs_requeridos") or []
            if requeridos:
                st.markdown("**Datos requeridos por el score:**")
                st.markdown(" · ".join([f"`{x}`" for x in requeridos]))

        if detalle:
            st.markdown("**Componentes usados:**")
            for linea in detalle:
                st.markdown(f"- {linea}")
        else:
            st.caption("Este score fue ingresado manualmente o no tiene componentes automáticos disponibles.")

        if faltantes_generales:
            st.markdown("**Datos faltantes:**")
            for faltante in faltantes_generales:
                st.markdown(f"- {faltante}")

        if catalogo.get("referencia"):
            st.markdown("**Referencia base:**")
            st.caption(catalogo.get("referencia"))
        if catalogo.get("nota"):
            st.markdown("**Nota institucional:**")
            st.caption(catalogo.get("nota"))
        if origen == "Manual":
            st.caption("Origen manual: el sistema no recalculó este valor; verificar consistencia con la historia clínica.")


with tab_planes:
    with st.container(border=True):
        st.subheader("🚨 Validación de datos críticos y alertas de seguridad")
        if alertas_seguridad:
            for alerta in alertas_seguridad:
                texto_alerta = f"**{alerta.get('campo', 'Dato')}:** {formatear_alerta(alerta)}"
                if alerta.get("nivel") == "critico":
                    st.error(texto_alerta)
                elif alerta.get("nivel") == "advertencia":
                    st.warning(texto_alerta)
                else:
                    st.info(texto_alerta)
        else:
            st.success("Sin alertas críticas detectadas con los datos cargados.")

    with st.container(border=True):
        st.subheader("📚 Biblioteca institucional de scores")
        with st.expander("Ver catálogo de scores disponibles / próximos a automatizar", expanded=False):
            resumen = resumen_estado_catalogo()
            st.caption(
                "Catálogo inspirado en bibliotecas de calculadoras clínicas: muestra qué scores están implementados, "
                "cuáles son manuales y cuáles quedan pendientes de automatización institucional."
            )
            st.markdown(
                f"Implementados: **{resumen.get('implementado', 0)}** · "
                f"Manuales: **{resumen.get('manual', 0)}** · "
                f"Manual con automatización pendiente: **{resumen.get('manual_pendiente_auto', 0)}**"
            )
            grupos_catalogo = agrupar_catalogo_por_categoria()
            categoria_catalogo = st.selectbox(
                "Categoría",
                list(grupos_catalogo.keys()),
                key=f"catalogo_scores_categoria_{rk}",
            )
            for meta in grupos_catalogo.get(categoria_catalogo, []):
                estado = str(meta.get("estado", "")).replace("_", " ")
                st.markdown(f"**{meta.get('nombre')}** · `{estado}`")
                st.caption(meta.get("uso_clinico", ""))
                requeridos = meta.get("inputs_requeridos") or []
                if requeridos:
                    st.markdown("Datos requeridos: " + " · ".join([f"`{x}`" for x in requeridos]))
                st.caption(f"Referencia: {meta.get('referencia', 'No consignada')}")
                st.divider()

    with st.container(border=True):
        st.subheader("🛡️ FAST HUG BID")
        fast_dict = {
            'F': 'Feeding', 'A': 'Analgesia', 'S': 'Sedación',
            'T': 'Tromboprofilaxis', 'H': 'Head 30°', 'U': 'Úlceras estrés',
            'G': 'Glucemia', 'B': 'Bowel', 'I': 'Invasiones', 'D': 'Desescalar ATB'
        }
        f_cols = st.columns(5)
        fast_sel = []
        for i, (letra, descripcion) in enumerate(fast_dict.items()):
            if f_cols[i % 5].checkbox(letra, help=descripcion, key=f"fast_{letra}_{rk}"):
                fast_sel.append(f"{letra} - {descripcion}")

    with st.container(border=True):
        st.subheader("(A) Problemas Activos")

        scores_globales = motor_scores(flags_scores, manuales_scores, auto_scores)

        if scores_globales:
            st.info("**Scores Inteligentes Detectados:** se distingue origen Manual/Auto, se bloquea interpretación si faltan datos críticos y se usa color por nivel de riesgo.")
            for g_idx, grupo in enumerate(scores_globales):
                st.markdown(f"#### {grupo.get('categoria', 'Scores')}")
                items = grupo.get("items", [])
                if items:
                    for i_idx, item in enumerate(items):
                        mostrar_item_score(item, grupo.get("categoria", "Scores"), i_idx)
                else:
                    texto_scores = formatear_scores_detectados([grupo])
                    st.info("\n".join(texto_scores))
        else:
            st.caption("No se detectaron scores automáticos. Escriba diagnósticos clave arriba para activarlos (ej. Sepsis, IAM, FA).")

        problemas_activos_manual = st.text_area("Agregar otros problemas activos (Manual):", height=80, key=f"prob_man_{rk}")

    with st.container(border=True):
        st.subheader("(P) Plan 24hs")
        plan = st.text_area("Indicaciones / Conducta:", d_str("- Cultivar: \n- Interconsultas:"), height=100, key=f"plan_{rk}")

    st.divider()

    col_gen, col_limp = st.columns(2)
    btn_generar = col_gen.button("🚀 Generar Evolución", use_container_width=True, type="primary")
    btn_limpiar = col_limp.button("🧹 LIMPIAR PLANILLA", use_container_width=True)

    if btn_limpiar:
        new_rk = st.session_state.get('rk', 0) + 1
        st.session_state.clear()
        st.session_state['rk'] = new_rk
        st.session_state['infusiones_automatizadas'] = []
        st.session_state['evolucion_generada'] = False
        st.session_state['limpiar_prellenado'] = True
        rerun_app()

    if btn_generar:
        scores_para_imprimir = motor_scores(flags_scores, manuales_scores, auto_scores)
        datos_evolucion = dict(locals())
        datos_evolucion["infusiones_automatizadas"] = st.session_state.get("infusiones_automatizadas", [])
        # Las alertas de seguridad se muestran solo en la ventana general de la app.
        # No se incorporan al texto final de evolución.

        texto_final = generar_texto_evolucion(datos_evolucion, auto_scores, scores_para_imprimir)

        st.success("✅ Evolución generada con éxito, lista para exportar a Historia Clínica.")
        st.code(texto_final, language="markdown")
