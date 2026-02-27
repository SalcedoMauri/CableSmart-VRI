import streamlit as st
import math
import requests
import os
import random
from fpdf import FPDF
from decimal import Decimal, ROUND_HALF_UP
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ==============================================================================
# 0. ENLACE A TU BASE DE DATOS Y MOTOR DE CORREOS DE GOOGLE
# ==============================================================================
# PEGA AQUÍ TU NUEVA URL DE GOOGLE APPS SCRIPT:
URL_WEBHOOK = "https://script.google.com/macros/s/AKfycbzJVZqLrnT8etcYepM8ttu6u-i2T-QQlwSGkqfCuiGWpSBWopWAfbD7hL8V4DOzsbDW/exec"

# BASE DE DATOS DEL CABLE (N2XSY)
CABLES_DB = [
    [25,   0.927,  0.927,  0.2964, 0.1713,  180,    160,   24258.75], [35,   0.668,  0.669,  0.2849, 0.1627,  215,    190,   30045.60],
    [50,   0.494,  0.494,  0.2704, 0.1513,  250,    225,   38726.25], [70,   0.342,  0.342,  0.2579, 0.1426,  305,    275,   50300.45],
    [95,   0.247,  0.247,  0.2474, 0.1365,  360,    325,   64768.20], [120,  0.196,  0.196,  0.2385, 0.1305,  405,    370,   79235.95],
    [150,  0.159,  0.160,  0.2319, 0.1264,  445,    410,   96597.25], [185,  0.127,  0.128,  0.2250, 0.1230,  495,    460,   116852.10],
    [240,  0.098,  0.099,  0.2160, 0.1177,  570,    535,   148681.15], [300,  0.078,  0.080,  0.2091, 0.1139,  630,    600,   183403.75],
    [400,  0.062,  0.065,  0.2021, 0.1108,  685,    670,   241274.75], [500,  0.050,  0.053,  0.1957, 0.1081,  750,    745,   299145.75]
]

OPS_TENDIDO = ["Paralelos separados 7cm", "Agrupados en triángulo", "Un solo ducto-triángulo", "Tres ductos-linea horizontal", "Tres ductos-triángulo"]
OPS_TEMP = ["5", "10", "15", "20", "25", "30", "35", "40", "45"]
OPS_RES = ["50", "70", "90", "100", "120", "150", "200", "250", "300"]
OPS_PROF = ["0.5", "0.6", "0.7", "0.8", "1.0", "1.2", "1.5"]
RAIZ_3 = 1.732

def round_vba(val, precision=2): return float(Decimal(str(val)).quantize(Decimal(f"1.{'0'*precision}"), rounding=ROUND_HALF_UP))
def format_decimal_custom(val): return "{:,.2f}".format(float(Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))

def calcular_tir_manual(flujo_caja):
    guess = 0.1
    for _ in range(100):
        npv = sum(val / ((1 + guess) ** t) for t, val in enumerate(flujo_caja))
        d_npv = sum(-t * val / ((1 + guess) ** (t + 1)) for t, val in enumerate(flujo_caja))
        if d_npv == 0: return 0
        new_guess = guess - npv / d_npv
        if abs(new_guess - guess) < 1e-6: return new_guess
        guess = new_guess
    return guess

def obtener_ft(idx): return [1.10, 1.07, 1.04, 1.00, 0.96, 0.93, 0.89, 0.84, 0.80, 0.76][idx]
def obtener_fr(idx, st): return [1.26, 1.14, 1.04, 1.00, 0.93, 0.85, 0.76, 0.69, 0.63][idx]
def obtener_fe(idx, st): return [1.02, 1.01, 1.00, 0.98, 0.96, 0.95, 0.94][idx]
def obtener_fd(idx, st): return 1.0 if idx in [0,1] else 0.80

def enviar_codigo_otp_por_google(correo_destino, codigo):
    try:
        datos_peticion = {
            "accion": "enviar_otp",
            "correo": correo_destino,
            "codigo": codigo
        }
        respuesta = requests.post(URL_WEBHOOK, json=datos_peticion, timeout=10)
        return respuesta.status_code == 200
    except Exception as e:
        print(f"Error enviando orden a Google: {e}")
        return False

# ==============================================================================
# CLASE PDF CON MARCA DE AGUA Y DATOS
# ==============================================================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 35)
        self.set_text_color(240, 240, 240)
        for y in range(40, 290, 60):
            self.text(15, y, 'VRI UNI - INVESTIGACIÓN REFERENCIAL')
        self.set_text_color(0, 0, 0)

def generar_pdf(datos, chart_path):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE DE INVESTIGACIÓN: SELECCIÓN DE CABLES N2XSY", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 5, txt="Vicerrectorado de Investigación - Universidad Nacional de Ingeniería (UNI)", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="1. DATOS DEL PROYECTO", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 6, txt=f"Proyecto: {datos['proyecto']} | Investigador/Usuario: {datos['nombre']}", ln=True)
    pdf.cell(200, 6, txt=f"Empresa: {datos['empresa']} | Cargo: {datos['cargo']}", ln=True)
    pdf.cell(200, 6, txt=f"Contacto: {datos['correo']}  |  Celular: {datos['celular']}", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="2. PARÁMETROS DE ENTRADA", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, txt=f"Longitud: {datos['in_l']} km")
    pdf.cell(100, 6, txt=f"Potencia: {datos['in_pi']} MVA", ln=True)
    pdf.cell(100, 6, txt=f"Tensión Nominal: 10 kV")
    pdf.cell(100, 6, txt=f"Vida útil: 30 años", ln=True)
    pdf.cell(100, 6, txt=f"Tendido: {datos['in_tendido']}")
    pdf.cell(100, 6, txt=f"Temp. Suelo: {datos['in_tsuelo']} °C", ln=True)
    pdf.cell(100, 6, txt=f"Horas/Día: {datos['ec_horas']}")
    pdf.cell(100, 6, txt=f"Costo Energía: S/. {datos['ec_costo']}", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="3. RESULTADOS DE LA OPTIMIZACIÓN (TÉCNICO vs ECONÓMICO)", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, txt=f"Sección Técnica: {datos['res_st']} mm2")
    pdf.cell(100, 6, txt=f"Sección Económica: {datos['res_se']} mm2", ln=True)
    pdf.cell(100, 6, txt=f"Inversión Técnica: S/. {format_decimal_custom(datos['res_inv_t'])}")
    pdf.cell(100, 6, txt=f"Inversión Económica: S/. {format_decimal_custom(datos['res_inv_e'])}", ln=True)
    pdf.cell(100, 6, txt=f"Pérdidas Técnicas: S/. {format_decimal_custom(datos['res_perd_t'])}/año")
    pdf.cell(100, 6, txt=f"Pérdidas Económicas: S/. {format_decimal_custom(datos['res_perd_e'])}/año", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="4. INDICADORES Y REDUCCIÓN DE CO2 (VRI)", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, txt=f"Payback Simple: {datos['res_payback']} años")
    pdf.cell(100, 6, txt=f"TIR Estimada: {datos['res_tir']} %", ln=True)
    pdf.cell(100, 6, txt=f"Relación B/C: {datos['res_bc']}")
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 6, txt=f"Reducción de CO2: {format_decimal_custom(datos['res_co2'])} t/año", ln=True)
    pdf.ln(5)

    if os.path.exists(chart_path):
        pdf.image(chart_path, x=15, y=pdf.get_y(), w=180)
        pdf.set_y(pdf.get_y() + 105) 

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(46, 117, 182) 
    pdf.cell(200, 6, txt="5. CONTACTO PARA CONSULTORÍA Y ASESORÍA ESPECIALIZADA", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 6, txt="Ing. Mauricio Salcedo | Ingeniero Electrónico - Especialista en Aplicaciones", ln=True)
    pdf.cell(200, 6, txt="Correo: msalcedos@uni.pe | Celular / WhatsApp: 943 352 587", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# CONFIGURACIÓN UI Y CSS 
# ==============================================================================
st.set_page_config(page_title="CableSmart - Análisis N2XSY", layout="centered")

st.markdown("""
    <style>
    /* 1. Ocultar menús por defecto de Streamlit (sin romper la app) */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* 2. Forzar Modo Claro (Textos oscuros, fondos blancos) para el celular */
    .stApp { background-color: #F8F9FA !important; color: #1E293B !important; }
    p, label, span, h1, h2, h3, div { color: #1E293B !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #ffffff !important; border-color: #cbd5e1 !important; }
    div[data-baseweb="input"] input, div[data-baseweb="select"] div { color: #000000 !important; }
    
    /* 3. Estilos de casillas y botones */
    button[title="Step up"], button[title="Step down"], button[aria-label="Step up"], button[aria-label="Step down"], div[data-testid="stNumberInputContainer"] button { display: none !important; }
    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none !important; margin: 0 !important; }
    input[type=number] { -moz-appearance: textfield !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border: 1px solid #E2E8F0 !important; background-color: white !important; border-radius: 10px !important; padding: 15px !important; box-shadow: 0px 2px 4px rgba(0,0,0,0.05) !important; }
    .stButton > button { background-color: #0F62FE !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; border: none !important; padding: 10px 0 !important; }
    </style>
""", unsafe_allow_html=True)

# GESTIÓN DE ESTADOS (SESSION STATE) PARA OTP
if 'mostrar_formulario' not in st.session_state: st.session_state.mostrar_formulario = False
if 'otp_enviado' not in st.session_state: st.session_state.otp_enviado = False
if 'otp_codigo' not in st.session_state: st.session_state.otp_codigo = ""
if 'datos_usuario' not in st.session_state: st.session_state.datos_usuario = {}
if 'pdf_listo' not in st.session_state: st.session_state.pdf_listo = False
if 'pdf_bytes' not in st.session_state: st.session_state.pdf_bytes = None

# ==============================================================================
# PUERTA TRASERA FRONTAL DE SEGURIDAD (LINK SECRETO)
# ==============================================================================
llave_maestra = st.query_params.get("admin") == "mauricio"

if llave_maestra:
    with st.container(border=True):
        st.success("🔓 **MODO ADMINISTRADOR ACTIVADO**")
        modo = st.radio("Seleccione el entorno de trabajo:", ["👨‍💻 Modo Personal (Interactivo)", "🎓 Modo VRI (Investigación)"], horizontal=True)
else:
    modo = "🎓 Modo VRI (Investigación)"

st.markdown("<hr style='margin-top: 0;'>", unsafe_allow_html=True)

if modo == "👨‍💻 Modo Personal (Interactivo)":
    st.markdown("<h2 style='text-align: center; color: #1E293B; font-size: 22px;'>Cálculo Interactivo en Tiempo Real</h2>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align: center; color: #1E293B; font-size: 22px;'>Recopilación de Datos - Investigación Huella de Carbono</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 30px;'>Vicerrectorado de Investigación (VRI) - UNI</p>", unsafe_allow_html=True)

# ==============================================================================
# ENTRADAS UI (FIJAS PARA AMBOS MODOS)
# ==============================================================================
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.markdown("### Datos del Cable")
        l_km = st.number_input("Longitud (km)", value=0.30, step=0.01)
        st.text_input("Vida útil (años)", value="30", disabled=True)
with c2:
    with st.container(border=True):
        st.markdown("### Datos de la Carga")
        st.text_input("Tensión Nominal (kV)", value="10", disabled=True)
        pot_mva = st.number_input("Potencia (MVA)", value=4.50, min_value=0.01, step=0.1)

c3, c4 = st.columns(2)
with c3:
    with st.container(border=True):
        st.markdown("### Datos de Protección")
        caida_max_val = st.number_input("Caída tensión máx. (%)", min_value=0.1, max_value=3.0, value=3.0, step=0.1)
        pot_corto = st.number_input("Cortocircuito (MVA)", value=200)
        t_falla = st.number_input("Tiempo apertura (seg)", value=0.01, step=0.01)
with c4:
    with st.container(border=True):
        st.markdown("### Datos de Instalación")
        tendido_val = st.selectbox("Tipo de Tendido", OPS_TENDIDO, index=0)
        tsuelo_val = st.selectbox("Temp. Suelo (°C)", OPS_TEMP, index=4)
        rsuelo_val = st.selectbox("Resistividad (°C-cm/W)", OPS_RES, index=4)
        psuelo_val = st.selectbox("Profundidad (m)", OPS_PROF, index=5)

with st.container(border=True):
    st.markdown("### Datos Económicos")
    colA, colB, colC = st.columns(3)
    h_dia = colA.number_input("Horas/Día", value=10)
    d_anio = colB.number_input("Días/Año", value=365)
    c_energia = colC.number_input("Costo Energía (S/.)", value=0.1265, format="%.4f")
    colA, colB, _ = st.columns(3)
    c_dinero = colA.number_input("Costo Dinero (%)", value=12.0)
    inflacion = colB.number_input("Inflación (%)", value=7.0)

# ==============================================================================
# MOTOR DE CÁLCULO INVISIBLE
# ==============================================================================
vida_util = 30
tendido_idx, temp_idx = OPS_TENDIDO.index(tendido_val), OPS_TEMP.index(tsuelo_val)
res_idx, prof_idx = OPS_RES.index(rsuelo_val), OPS_PROF.index(psuelo_val)
es_grupo_a = (tendido_idx == 0)
corriente = (pot_mva * 1000000) / (RAIZ_3 * 10000)

si, sc, sv = 25, 25, 25 
for c in CABLES_DB:
    amp_tabla = c[5] if es_grupo_a else c[6]
    if (amp_tabla * obtener_ft(temp_idx) * obtener_fr(res_idx, c[0]) * obtener_fe(prof_idx, c[0]) * obtener_fd(tendido_idx, c[0])) > corriente: si = c[0]; break

icc = (pot_corto * 1000000) / (RAIZ_3 * 10000)
for c in CABLES_DB:
    if ((143 * c[0]) / math.sqrt(t_falla)) > icc: sc = c[0]; break
for c in CABLES_DB:
    rv, xv = (c[1], c[3]) if es_grupo_a else (c[2], c[4])
    if (RAIZ_3 * corriente * l_km * math.sqrt(rv**2 + xv**2)) < ((caida_max_val/100)*10000): sv = c[0]; break

st_val = max(si, sc, sv)
cab_t = next(c for c in CABLES_DB if c[0] == st_val)
r_t, x_t = (cab_t[1], cab_t[3]) if es_grupo_a else (cab_t[2], cab_t[4])

tasa_r = ((1 + c_dinero/100) / (1 + inflacion/100)) - 1
A_val = (((1 + tasa_r)**vida_util) - 1) / (((1 + tasa_r)**vida_util) * tasa_r) if tasa_r != 0 else vida_util
G_val = ((CABLES_DB[1][7] - CABLES_DB[0][7]) / 10) / 1000 
se_calc = corriente * math.sqrt((1.2 * 0.02236 * h_dia * d_anio * c_energia * A_val * 0.001) / G_val)
se_val = next((c[0] for c in CABLES_DB if c[0] >= (se_calc - 3)), 500)
cab_e = next(c for c in CABLES_DB if c[0] == se_val)
r_e, x_e = (cab_e[1], cab_e[3]) if es_grupo_a else (cab_e[2], cab_e[4])

inv_t, inv_e = l_km * cab_t[7] * 3, l_km * cab_e[7] * 3
perd_t = 3 * r_t * l_km * (corriente**2) * h_dia * d_anio * c_energia * 0.001
perd_e = 3 * r_e * l_km * (corriente**2) * h_dia * d_anio * c_energia * 0.001
co2_red = ((perd_t/c_energia - perd_e/c_energia) * 0.43) / 1000 

ahorro = perd_t - perd_e
inversion = inv_e - inv_t
payback, tir, bc = 0.0, 0.0, 0.0
if ahorro > 0:
    payback = round_vba(inversion / ahorro, 2)
    bc = round_vba((ahorro * A_val) / inversion, 2) if inversion != 0 else 0
    try: tir = round_vba(calcular_tir_manual([-inversion] + [ahorro]*30) * 100, 2)
    except: tir = 0.0

anios_g = list(range(31))
d_t, d_e = [], []
for t in anios_g:
    if t == 0: d_t.append(inv_t); d_e.append(inv_e)
    else:
        f_acu = ((1 + tasa_r)**t - 1) / tasa_r if tasa_r > 0 else t
        d_t.append(inv_t + (perd_t * f_acu)); d_e.append(inv_e + (perd_e * f_acu))
d_a = [t - e for t, e in zip(d_t, d_e)] 

t_int = 0
if ahorro > 0:
    v_log = 1 + (inversion * tasa_r / ahorro)
    if v_log > 0 and tasa_r > 0: t_int = math.log(v_log) / math.log(1 + tasa_r)
    else: t_int = inversion / ahorro

# ==============================================================================
# LOGICA SEGÚN EL MODO SELECCIONADO
# ==============================================================================
if modo == "👨‍💻 Modo Personal (Interactivo)":
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📊 RESULTADOS EN TIEMPO REAL")

    cr1, cr2 = st.columns(2)
    with cr1:
        with st.container(border=True):
            st.markdown("<p style='color:#2E75B6; font-weight:bold; margin-bottom:5px;'>Técnico</p>", unsafe_allow_html=True)
            st.text_input("Sección (mm²)", value=st_val, disabled=True, key="out_st")
            st.text_input("Inversión (S/.)", value=format_decimal_custom(inv_t), disabled=True, key="out_tot")
            st.text_input("Pérdidas (S/./año)", value=format_decimal_custom(perd_t), disabled=True, key="out_cp")
    with cr2:
        with st.container(border=True):
            st.markdown("<p style='color:#ED7D31; font-weight:bold; margin-bottom:5px;'>Económico</p>", unsafe_allow_html=True)
            st.text_input("Sección (mm²)", value=se_val, disabled=True, key="out_se")
            st.text_input("Inversión (S/.)", value=format_decimal_custom(inv_e), disabled=True, key="out_tot2")
            st.text_input("Pérdidas (S/./año)", value=format_decimal_custom(perd_e), disabled=True, key="out_cp2")

    fig_plotly = go.Figure()
    fig_plotly.add_trace(go.Scatter(x=anios_g, y=d_t, mode='lines', name='Costo Técnico Acumulado', line=dict(color='#2E75B6', width=2.5)))
    fig_plotly.add_trace(go.Scatter(x=anios_g, y=d_e, mode='lines', name='Costo Económico Acumulado', line=dict(color='#ED7D31', width=2.5)))
    fig_plotly.add_trace(go.Scatter(x=anios_g, y=d_a, mode='lines', name='Ahorro Neto', line=dict(color='#FFC000', width=2)))
    if 0 < t_int <= 30:
        y_int = inv_t + (((1 + tasa_r)**t_int - 1) / tasa_r if tasa_r > 0 else t_int) * perd_t
        fig_plotly.add_trace(go.Scatter(x=[t_int], y=[y_int], mode='markers', name='Punto de Equilibrio', marker=dict(color='red', size=10)))
    fig_plotly.update_layout(title="Análisis de Costo Total Acumulado", template="plotly_white", legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_plotly, use_container_width=True)

    with st.container(border=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Payback Simple", f"{payback} años")
        col_m2.metric("TIR (%)", f"{tir} %")
        col_m3.metric("B/C", bc)
    with st.container(border=True):
        st.metric("Impacto Ambiental (Reducción de CO2)", f"{format_decimal_custom(co2_red)} t / año")

elif modo == "🎓 Modo VRI (Investigación)":

    if not st.session_state.otp_enviado and not st.session_state.pdf_listo:
        if st.button("Ingresar Datos de Registro para Procesar", use_container_width=True):
            st.session_state.mostrar_formulario = True

        if st.session_state.mostrar_formulario:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("### 📝 Registro del Investigador / Usuario")

                with st.form("form_vri"):
                    col_f1, col_f2 = st.columns(2)
                    f_nombre = col_f1.text_input("Nombre y Apellidos")
                    f_profesion = col_f2.text_input("Profesión / Facultad")

                    col_f3, col_f4 = st.columns(2)
                    f_empresa = col_f3.text_input("Empresa / Institución")
                    f_cargo = col_f4.text_input("Cargo en la Institución/Empresa")

                    col_f5, col_f6 = st.columns(2)
                    f_correo = col_f5.text_input("Correo Corporativo / Institucional")
                    f_celular = col_f6.text_input("Teléfono / Celular (9 dígitos)", max_chars=9)

                    f_proyecto = st.text_input("Nombre del Proyecto")
                    f_notas = st.text_area("Observaciones técnicas (opcional)")

                    st.markdown("---")
                    no_robot = st.checkbox("☑️ Confirmo que los datos son correctos y veraces")

                    if st.form_submit_button("Solicitar Código de Verificación al Correo"):

                        f_celular_clean = f_celular.replace(" ", "").strip()
                        campos_llenos = bool(f_nombre.strip() and f_profesion.strip() and f_empresa.strip() and f_cargo.strip() and f_correo.strip() and f_celular_clean and f_proyecto.strip())

                        dominios_prohibidos = ['gmail.com', 'hotmail.com', 'yahoo.com', 'yahoo.es', 'outlook.com', 'live.com', 'icloud.com', 'aol.com', 'msn.com']
                        correo_valido = False
                        if f_correo and "@" in f_correo and "." in f_correo.split("@")[1]:
                            if f_correo.split("@")[1].lower().strip() not in dominios_prohibidos:
                                correo_valido = True

                        celular_valido = f_celular_clean.isdigit() and len(f_celular_clean) == 9

                        if not campos_llenos:
                            st.error("⚠️ Error: Por favor, complete todos los campos obligatorios del formulario.")
                        elif not correo_valido:
                            st.error("🚫 Correo Inválido: Solo se permiten cuentas corporativas/institucionales.")
                        elif not celular_valido:
                            st.error("📱 Teléfono Inválido: El número de celular debe contener exactamente 9 dígitos numéricos.")
                        elif not no_robot: 
                            st.error("🤖 Por favor, confirma marcando la casilla al final del formulario.")
                        elif "PEGA_AQUI" in URL_WEBHOOK:
                            st.error("⚠️ Error de sistema: Pegue su enlace de Google en la línea 16 de Python.")
                        else:
                            with st.spinner('Enviando código de verificación seguro a su correo...'):
                                codigo_generado = str(random.randint(100000, 999999))

                                if enviar_codigo_otp_por_google(f_correo, codigo_generado):
                                    st.session_state.otp_codigo = codigo_generado
                                    st.session_state.otp_enviado = True
                                    st.session_state.datos_usuario = {
                                        "accion": "guardar_datos", 
                                        "nombre": f_nombre, "profesion": f_profesion, "empresa": f_empresa, "cargo": f_cargo,
                                        "correo": f_correo, "celular": f_celular_clean, "proyecto": f_proyecto, "notas": f_notas,
                                        "in_l": l_km, "in_pi": pot_mva, "in_caida": caida_max_val, "in_pc": pot_corto, "in_ta": t_falla,
                                        "in_tendido": tendido_val, "in_tsuelo": tsuelo_val, "in_rsuelo": rsuelo_val, "in_psuelo": psuelo_val,
                                        "ec_horas": h_dia, "ec_dias": d_anio, "ec_costo": c_energia, "ec_dinero": c_dinero, "ec_inflacion": inflacion,
                                        "res_st": st_val, "res_se": se_val, "res_inv_t": inv_t, "res_inv_e": inv_e, 
                                        "res_perd_t": perd_t, "res_perd_e": perd_e, "res_payback": payback, "res_tir": tir, "res_bc": bc, "res_co2": co2_red
                                    }
                                    st.rerun() 
                                else:
                                    st.error("❌ Error de servidor: Google no pudo procesar el envío.")

    if st.session_state.otp_enviado and not st.session_state.pdf_listo:
        with st.container(border=True):
            st.markdown(f"### 🔐 Verificación de Identidad")
            st.info(f"Hemos enviado un código de seguridad de 6 dígitos a **{st.session_state.datos_usuario['correo']}**.")

            codigo_ingresado = st.text_input("Ingrese el código de verificación aquí:", max_chars=6)

            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("✅ Verificar y Generar Reporte", use_container_width=True):
                # SOLUCIÓN: Usamos .strip() para limpiar espacios accidentales de ambos lados
                if codigo_ingresado.strip() == str(st.session_state.otp_codigo).strip():
                    with st.spinner('Validación exitosa. Procesando reporte PDF...'):

                        plt.figure(figsize=(8, 4.5))
                        plt.plot(anios_g, d_t, label='Costo Técnico', color='#2E75B6', linewidth=2)
                        plt.plot(anios_g, d_e, label='Costo Económico', color='#ED7D31', linewidth=2)
                        plt.plot(anios_g, d_a, label='Ahorro Neto', color='#FFC000', linewidth=2) 

                        if 0 < t_int <= 30:
                            f_int = ((1 + tasa_r)**t_int - 1) / tasa_r if tasa_r > 0 else t_int
                            y_int = inv_t + f_int * perd_t
                            plt.plot(t_int, y_int, marker='o', markersize=8, color='red')
                            plt.annotate(f"Equilibrio: Año {t_int:.1f}", xy=(t_int, y_int), xytext=(10, -20),
                                         textcoords='offset points', color='white', bbox=dict(boxstyle="round,pad=0.3", fc="red", ec="none"))

                        plt.title("Proyección de Costos Acumulados a 30 Años", fontsize=12, fontweight='bold', color='#1E293B')
                        plt.xlabel("Años de Servicio", fontsize=10)
                        plt.ylabel("Costo Total Acumulado (S/.)", fontsize=10)
                        plt.grid(True, linestyle='--', alpha=0.5)
                        plt.legend(loc='upper left')
                        plt.tight_layout()

                        chart_path = "temp_chart.png"
                        plt.savefig(chart_path, dpi=150)
                        plt.close()

                        try:
                            requests.post(URL_WEBHOOK, json=st.session_state.datos_usuario, timeout=5)
                        except: pass

                        st.session_state.pdf_bytes = generar_pdf(st.session_state.datos_usuario, chart_path)
                        st.session_state.pdf_listo = True
                        st.rerun()
                else:
                    st.error("❌ El código ingresado es incorrecto. Asegúrate de usar el ÚLTIMO correo que te llegó.")

            if c_btn2.button("🔙 Cancelar y corregir correo", use_container_width=True):
                st.session_state.otp_enviado = False
                st.rerun()

    if st.session_state.pdf_listo and st.session_state.pdf_bytes:
        st.success("✅ ¡Correo validado y datos registrados exitosamente!")
        st.download_button(
            label="📥 DESCARGAR REPORTE VRI (RESULTADOS + GRÁFICO)",
            data=st.session_state.pdf_bytes,
            file_name="Reporte_VRI_UNI.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        if st.button("Hacer un nuevo cálculo", use_container_width=True):
            st.session_state.mostrar_formulario = False
            st.session_state.otp_enviado = False
            st.session_state.pdf_listo = False
            st.rerun()
