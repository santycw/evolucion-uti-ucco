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

# --- INTEGRACIÓN DECS (BIREME/OPS - Nativo en Español) ---
@st.cache_data(show_spinner=False)
def obtener_terminos_decs(query):
    """Consulta la API pública de DeCS (BIREME) para normalizar diagnósticos en español."""
    try:
        url = "https://decs.bvsalud.org/api/search"
        params = {"q": query, "lang": "es"}
        # Timeout reducido a 3 segundos para falla rápida en entornos sin red
        res = requests.get(url, params=params, timeout=3)

        if res.status_code == 200:
            data = res.json()
            terminos = []
            resultados = data.get("results", data) if isinstance(data, dict) else data

            if isinstance(resultados, list):
                for r in resultados[:3]:
                    nombre = r.get("term", r.get("descriptor", r.get("name", "")))
                    decs_id = r.get("id", r.get("decsCode", ""))
                    if isinstance(nombre, dict): nombre = nombre.get("es", str(nombre))
                    if nombre:
                        etiqueta = f"{nombre} (DeCS: {decs_id})" if decs_id else nombre
                        terminos.append(etiqueta)
            return terminos if terminos else ["Búsqueda finalizada: Sin equivalencia exacta en DeCS."]
        return [f"⚠️ Servidor DeCS no disponible (HTTP {res.status_code})."]

    except requests.exceptions.ConnectionError:
        return ["⚠️ Sin conexión a red externa. Normalización DeCS deshabilitada temporalmente."]
    except requests.exceptions.Timeout:
        return ["⚠️ Tiempo de espera agotado al contactar con BIREME."]
    except Exception as e:
        return ["⚠️ Error interno en el módulo de indexación diagnóstica."]

# Configuración de página
st.set_page_config(page_title="Sistema Evolutivo UTI", page_icon="🏥", layout="wide")

st.markdown("""
    <style>
    .stTextArea textarea, .stTextInput input, .stNumberInput input { font-family: 'Consolas', monospace; font-size: 14px; }
    div[data-testid="stExpander"] { background-color: #1E1E1E !important; border: 1px solid #333333; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Asistente de Evolución UTI / UCCO")
st.caption("Versión Actual | Normalización DeCS (Resiliente a Red) | Cálculo por Ampolla | Omisión de Vacíos")

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("📌 Datos Generales")
    with st.container(border=True):
        edad_paciente = st.number_input("Edad (años)", 18, 120, 65)
        sexo_paciente = st.selectbox("Sexo", ["Masculino", "Femenino"])
        peso_paciente = st.number_input("Peso Estimado (kg)", 1.0, 300.0, 70.0)
        fecha_hosp = st.date_input("Fecha Ingreso Hosp.", format="DD/MM/YYYY")
        fecha_uti = st.date_input("Fecha Ingreso UTI", format="DD/MM/YYYY")
        dias_arm = st.text_input("Días ARM", placeholder="0 o dejar vacío")

    st.header("📋 Diagnóstico")
    with st.container(border=True):
        diagnostico = st.text_area("Diagnósticos:", placeholder="Ej: Neumonía, Shock séptico...", height=100)
        if st.button("🌐 Normalizar con DeCS", use_container_width=True):
            lineas = [l.strip() for l in diagnostico.split('\n') if l.strip()]
            for l in lineas:
                q = re.sub(r'^[\d\.\-\*]+\s*', '', l).strip()
                terms = obtener_terminos_decs(q)
                if "⚠️" in terms[0]:
                    st.warning(f"**{q}** ➔ {terms[0]}")
                else:
                    st.info(f"**{q}** ➔ {', '.join(terms)}")

hoy = datetime.date.today()
dias_int_hosp = (hoy - fecha_hosp).days
dias_int_uti = (hoy - fecha_uti).days
paciente_ventilado = bool(dias_arm.strip() and dias_arm.strip() not in ["0", "-", "no"])

# --- PESTAÑAS PRINCIPALES ---
tab_clinca, tab_lab, tab_estudios, tab_planes = st.tabs(["🩺 Clínica", "🧪 Laboratorio", "🩻 ECG/Imagen", "📋 Plan"])

with tab_clinca:
    with st.container(border=True):
        st.subheader("Subjetivo e Infusiones")
        subj = st.text_area("Novedades (S):", placeholder="Paciente estable...", height=68)

        with st.expander("🧮 Calculadora por Ampolla (Argentina)", expanded=False):
            dict_calc = {
                "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
                "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0},
                "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0},
                "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0},
                "Fentanilo (0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25},
                "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0},
                "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0},
                "Dexmedetomidina (0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2}
            }
            droga = st.selectbox("Droga:", list(dict_calc.keys()))
            u = dict_calc[droga]["unidad"]
            mgb = dict_calc[droga]["mg"]

            c1, c2 = st.columns(2)
            amps = c1.number_input("Ampollas", 0.0, 20.0, 1.0, 0.5)
            vol = c2.number_input("Volumen (ml)", 0.0, 500.0, 100.0)

            modo_c = st.radio("Calcular:", [f"Dosis ({u})", "ml/h"], horizontal=True)
            if "Dosis" in modo_c:
                vel = st.number_input("ml/h actuales", 0.0)
                res = calcular_infusion_universal("DOSIS", amps*mgb, vol, peso_paciente, vel, u)
                if st.button("➕ Anexar"):
                    st.session_state['infusiones_automatizadas'].append(f"{droga.split(' (')[0]}: {res:.4f} {u}")
                    st.rerun()
            else:
                dos = st.number_input(f"Dosis {u}", 0.0, format="%.4f")
                res = calcular_infusion_universal("VELOCIDAD", amps*mgb, vol, peso_paciente, dos, u)
                st.write(f"Bomba: {res:.2f} ml/h")
                if st.button("➕ Anexar", key="anex_vel"):
                    st.session_state['infusiones_automatizadas'].append(f"{droga.split(' (')[0]}: {dos:.4f} {u}")
                    st.rerun()

            if st.session_state['infusiones_automatizadas']:
                st.write("---")
                for i in st.session_state['infusiones_automatizadas']: st.caption(f"✅ {i}")
                if st.button("🗑️ Limpiar Infusiones"): st.session_state['infusiones_automatizadas'] = []; st.rerun()

    with st.container(border=True):
        st.subheader("Examen Físico")
        c1, c2, c3, c4 = st.columns(4)
        ta, fc, fr, sat = c1.text_input("TA"), c2.text_input("FC"), c3.text_input("FR"), c4.text_input("SatO2")
        temp, glasgow, rass = c1.text_input("Temp"), c2.text_input("GCS"), c3.text_input("RASS")
        ex_cv = st.text_input("CV", placeholder="R1R2 normofonéticos...")
        ex_resp = st.text_input("Resp", placeholder="Buena entrada de aire...")
        ex_abd = st.text_input("Abd", placeholder="RHA presentes...")
        ex_renal = st.text_input("Renal/Diuresis", placeholder="Ritmo diurético...")

with tab_lab:
    st.info("💡 Solo se plasmarán los campos que se completen.")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    ph, pco2, po2, hco3, eb, lac = c1.text_input("pH"), c2.text_input("pCO2"), c3.text_input("pO2"), c4.text_input("HCO3"), c5.text_input("EB"), c6.text_input("Lac")

    st.divider()
    l1, l2, l3, l4, l5, l6 = st.columns(6)
    gb, hto, plaq, urea, cr, gluc = l1.text_input("GB"), l2.text_input("Hto"), l3.text_input("Plaq"), l4.text_input("Urea"), l5.text_input("Cr"), l6.text_input("Gluc")
    na, k, cl, mg, ca = l1.text_input("Na"), l2.text_input("K"), l3.text_input("Cl"), l4.text_input("Mg"), l5.text_input("Ca")

with tab_estudios:
    ecg = st.text_area("ECG:", placeholder="Ritmo sinusal, FC...", height=100)
    rx = st.text_area("Imágenes (Rx/TC/Eco):", placeholder="Sin infiltrados...", height=100)

with tab_planes:
    analisis = st.text_area("Análisis (A):", height=150)
    plan = st.text_area("Plan (P):", height=150)

    st.divider()
    c_gen, c_lim = st.columns(2)
    if c_lim.button("🧹 LIMPIAR PLANILLA", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if c_gen.button("🚀 GENERAR EVOLUCIÓN", use_container_width=True, type="primary"):
        # --- Lógica de ensamblado (Omisión de vacíos) ---
        tf = [f"EVOLUCIÓN UTI - {hoy.strftime('%d/%m/%Y')}",
              f"Edad: {edad_paciente} | Peso: {peso_paciente}kg | Días UTI: {dias_int_uti}"]

        if subj: tf.append(f"\n(S): {subj}")

        obj = ["\n(O) OBJETIVO:"]
        if st.session_state['infusiones_automatizadas']:
            obj.append("Infusiones: " + " | ".join(st.session_state['infusiones_automatizadas']))

        sv = [f"TA {ta}" if ta else "", f"FC {fc}" if fc else "", f"FR {fr}" if fr else "", f"Sat {sat}" if sat else "", f"T {temp}" if temp else ""]
        sv = [s for s in sv if s]
        if sv: obj.append("SV: " + " | ".join(sv))

        if glasgow or rass: obj.append(f"Neuro: GCS {glasgow} RASS {rass}")
        if ex_cv: obj.append(f"CV: {ex_cv}")
        if ex_resp: obj.append(f"Resp: {ex_resp}")
        if ex_abd: obj.append(f"Abd: {ex_abd}")
        if ex_renal: obj.append(f"Renal: {ex_renal}")

        # Laboratorio con omisión inteligente
        labs = [f"pH {ph}" if ph else "", f"pCO2 {pco2}" if pco2 else "", f"pO2 {po2}" if po2 else "", f"Lac {lac}" if lac else "",
                f"GB {gb}" if gb else "", f"Hto {hto}" if hto else "", f"Plaq {plaq}" if plaq else "",
                f"Urea {urea}" if urea else "", f"Cr {cr}" if cr else ""]
        labs = [l for l in labs if l]
        if labs: obj.append("Laboratorio: " + " | ".join(labs))

        tf.extend(obj)

        if analisis: tf.append(f"\n(A): {analisis}")
        if plan: tf.append(f"\n(P): {plan}")

        st.subheader("Generar Evolución")
        st.code("\n".join(tf), language="markdown")
