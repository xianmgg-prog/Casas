import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="BrickVest — Inversión Inmobiliaria",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background-color: #0f1117; color: #e8eaf0; }

.hero {
    background: linear-gradient(135deg, #1a2332 0%, #0f1117 50%, #1a1f2e 100%);
    border: 1px solid #2a3441;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    margin-bottom: 32px;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #4f8ef7, #7c5cbf);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.hero p { color: #8892a4; font-size: 1.1rem; margin: 0; }

.metric-card {
    background: #1a2332;
    border: 1px solid #2a3441;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-card .label { color: #8892a4; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.metric-card .value { font-size: 1.6rem; font-weight: 700; color: #e8eaf0; }
.metric-card .value.green { color: #4caf82; }
.metric-card .value.red { color: #e05c5c; }
.metric-card .value.blue { color: #4f8ef7; }

.section-card {
    background: #1a2332;
    border: 1px solid #2a3441;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}

div[data-testid="stTabs"] button {
    font-weight: 500;
    font-size: 0.9rem;
}

.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background-color: #1a2332 !important;
    border: 1px solid #2a3441 !important;
    color: #e8eaf0 !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def calcular_cuota_hipoteca(principal, tasa_anual, anos):
    if tasa_anual == 0:
        return principal / (anos * 12)
    r = tasa_anual / 100 / 12
    n = anos * 12
    return principal * r * (1 + r)**n / ((1 + r)**n - 1)

def calcular_tir(flujos):
    from numpy import irr as np_irr
    try:
        return np.irr(flujos) * 12 * 100
    except Exception:
        # fallback manual
        tir = None
        for r in np.linspace(-0.5, 5.0, 10000):
            npv = sum(f / (1 + r/12)**i for i, f in enumerate(flujos))
            if abs(npv) < 100:
                tir = r * 12 * 100
                break
        return tir

def calcular_van(flujos, tasa_descuento_anual):
    r = tasa_descuento_anual / 100 / 12
    return sum(f / (1 + r)**i for i, f in enumerate(flujos))

def semaforo(valor, umbral_verde, umbral_amarillo):
    if valor >= umbral_verde:
        return "green"
    elif valor >= umbral_amarillo:
        return "#f0a500"
    else:
        return "red"

def metric_card(label, value, color="default", suffix=""):
    color_class = color if color in ["green", "red", "blue"] else ""
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value {color_class}">{value}{suffix}</div>
    </div>
    """

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>BrickVest</h1>
    <p>Plataforma profesional de análisis para inversión inmobiliaria</p>
</div>
""", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Compra para Alquilar",
    "Simulador de Hipoteca",
    "Reforma y Venta",
    "Alquiler Turístico",
    "Comparador",
    "Escenarios"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — COMPRA PARA ALQUILAR
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Compra para Alquilar")
    st.caption("Calcula la rentabilidad real de una inversión de alquiler residencial")

    col_izq, col_der = st.columns([1, 1], gap="large")

    with col_izq:
        st.markdown("**Adquisición**")
        precio_compra = st.number_input("Precio de compra (€)", value=180000, step=5000, key="c_precio")
        itp = st.number_input("ITP / AJD (%)", value=10.0, step=0.5, key="c_itp")
        gastos_notaria = st.number_input("Notaría + Registro (€)", value=2500, step=100, key="c_notaria")
        gastos_agencia = st.number_input("Agencia inmobiliaria (€)", value=3600, step=100, key="c_agencia")
        reforma_inicial = st.number_input("Reforma inicial (€)", value=0, step=1000, key="c_reforma")

        st.markdown("**Financiación**")
        entrada_pct = st.slider("Entrada (%)", 10, 100, 20, key="c_entrada")
        tasa_hipoteca = st.number_input("Tipo hipotecario anual (%)", value=3.2, step=0.1, key="c_tipo")
        plazo_hipoteca = st.number_input("Plazo hipoteca (años)", value=25, step=1, key="c_plazo")

    with col_der:
        st.markdown("**Ingresos**")
        alquiler_mensual = st.number_input("Alquiler mensual (€)", value=900, step=50, key="c_alquiler")
        ocupacion = st.slider("Ocupación estimada (%)", 50, 100, 92, key="c_ocup")

        st.markdown("**Gastos anuales**")
        ibi = st.number_input("IBI (€/año)", value=400, step=50, key="c_ibi")
        comunidad = st.number_input("Comunidad de propietarios (€/año)", value=600, step=50, key="c_com")
        seguro = st.number_input("Seguro del hogar (€/año)", value=250, step=50, key="c_seguro")
        mantenimiento = st.number_input("Mantenimiento estimado (€/año)", value=500, step=100, key="c_mant")
        gestion = st.slider("Gestoría / agencia alquiler (%)", 0, 15, 8, key="c_gest")

    # ── Cálculos ──
    gastos_adquisicion = precio_compra * itp / 100 + gastos_notaria + gastos_agencia + reforma_inicial
    coste_total = precio_compra + gastos_adquisicion

    entrada = precio_compra * entrada_pct / 100
    principal = precio_compra - entrada
    inversion_propia = entrada + gastos_adquisicion

    cuota_mensual = calcular_cuota_hipoteca(principal, tasa_hipoteca, int(plazo_hipoteca)) if principal > 0 else 0
    cuota_anual = cuota_mensual * 12

    ingresos_brutos = alquiler_mensual * 12 * ocupacion / 100
    gastos_gestion = ingresos_brutos * gestion / 100
    gastos_operativos = ibi + comunidad + seguro + mantenimiento + gastos_gestion
    noi = ingresos_brutos - gastos_operativos
    cash_flow_anual = noi - cuota_anual
    cash_flow_mensual = cash_flow_anual / 12

    rentabilidad_bruta = (alquiler_mensual * 12) / precio_compra * 100
    rentabilidad_neta = noi / coste_total * 100
    cap_rate = noi / precio_compra * 100
    cash_on_cash = cash_flow_anual / inversion_propia * 100 if inversion_propia > 0 else 0
    dscr = noi / cuota_anual if cuota_anual > 0 else 999

    # ── Métricas ──
    st.markdown("---")
    st.markdown("**Resultados**")
    cols = st.columns(4)
    metricas = [
        ("Rentabilidad Bruta", f"{rentabilidad_bruta:.2f}%", semaforo(rentabilidad_bruta, 6, 4)),
        ("Rentabilidad Neta", f"{rentabilidad_neta:.2f}%", semaforo(rentabilidad_neta, 4, 2.5)),
        ("Cash Flow Mensual", f"{cash_flow_mensual:,.0f} €", semaforo(cash_flow_mensual, 200, 0)),
        ("Cash-on-Cash", f"{cash_on_cash:.2f}%", semaforo(cash_on_cash, 5, 2)),
    ]
    for i, (label, val, color) in enumerate(metricas):
        with cols[i]:
            c = "green" if color == "green" else ("red" if color == "red" else "blue")
            st.markdown(metric_card(label, val, c), unsafe_allow_html=True)

    cols2 = st.columns(4)
    metricas2 = [
        ("Cap Rate", f"{cap_rate:.2f}%", "blue"),
        ("DSCR", f"{dscr:.2f}x", "blue"),
        ("Inversión Propia", f"{inversion_propia:,.0f} €", "default"),
        ("Coste Total", f"{coste_total:,.0f} €", "default"),
    ]
    for i, (label, val, color) in enumerate(metricas2):
        with cols2[i]:
            st.markdown(metric_card(label, val, color), unsafe_allow_html=True)

    # ── Evolución patrimonial ──
    st.markdown("---")
    st.markdown("**Evolución patrimonial (20 años)**")
    revalorizacion_anual = st.slider("Revalorización anual del inmueble (%)", 0.0, 5.0, 2.0, step=0.5, key="c_reval")

    anos_list = list(range(1, 21))
    capital_acumulado = []
    valor_inmueble = precio_compra
    deuda_pendiente = principal

    r_mensual = tasa_hipoteca / 100 / 12
    for ano in anos_list:
        valor_inmueble *= (1 + revalorizacion_anual / 100)
        if principal > 0 and r_mensual > 0:
            deuda_pendiente = principal * (1 + r_mensual)**(int(plazo_hipoteca)*12) - cuota_mensual * ((1 + r_mensual)**(ano*12) - 1) / r_mensual
            deuda_pendiente = max(0, deuda_pendiente)
        else:
            deuda_pendiente = 0
        patrimonio_neto = valor_inmueble - deuda_pendiente + cash_flow_anual * ano
        capital_acumulado.append(patrimonio_neto)

    fig_pat = go.Figure()
    fig_pat.add_trace(go.Scatter(x=anos_list, y=capital_acumulado, fill='tozeroy',
                                  line=dict(color='#4f8ef7', width=2),
                                  fillcolor='rgba(79,142,247,0.12)',
                                  name='Patrimonio Neto'))
    fig_pat.update_layout(
        template='plotly_dark', paper_bgcolor='#1a2332', plot_bgcolor='#1a2332',
        height=280, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Años", yaxis_title="€",
        showlegend=False
    )
    st.plotly_chart(fig_pat, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SIMULADOR DE HIPOTECA
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Simulador de Hipoteca")
    st.caption("Tabla de amortización completa y comparativa fijo vs. variable")

    col1, col2 = st.columns(2)
    with col1:
        h_principal = st.number_input("Capital a financiar (€)", value=144000, step=5000, key="h_cap")
        h_tasa_fijo = st.number_input("Tipo fijo anual (%)", value=3.2, step=0.1, key="h_fijo")
        h_anos = st.number_input("Plazo (años)", value=25, step=1, key="h_anos")
    with col2:
        h_euribor = st.number_input("Euríbor actual (%)", value=2.5, step=0.1, key="h_euribor")
        h_diferencial = st.number_input("Diferencial variable (%)", value=0.8, step=0.05, key="h_dif")
        h_amort_extra = st.number_input("Amortización anticipada anual (€)", value=0, step=500, key="h_amort")

    h_tasa_variable = h_euribor + h_diferencial

    cuota_fija = calcular_cuota_hipoteca(h_principal, h_tasa_fijo, int(h_anos))
    cuota_variable = calcular_cuota_hipoteca(h_principal, h_tasa_variable, int(h_anos))

    cols_h = st.columns(4)
    datos_h = [
        ("Cuota Mensual (Fijo)", f"{cuota_fija:,.2f} €", "blue"),
        ("Cuota Mensual (Variable)", f"{cuota_variable:,.2f} €", "blue"),
        ("Total Pagado (Fijo)", f"{cuota_fija*12*h_anos:,.0f} €", "default"),
        ("Intereses Totales (Fijo)", f"{cuota_fija*12*h_anos - h_principal:,.0f} €", "red"),
    ]
    for i, (l, v, c) in enumerate(datos_h):
        with cols_h[i]:
            st.markdown(metric_card(l, v, c), unsafe_allow_html=True)

    # Tabla de amortización
    st.markdown("---")
    st.markdown("**Tabla de amortización anual**")
    r = h_tasa_fijo / 100 / 12
    filas = []
    saldo = h_principal
    for ano in range(1, int(h_anos) + 1):
        interes_ano = 0
        amort_ano = 0
        for mes in range(12):
            interes_mes = saldo * r
            amort_mes = cuota_fija - interes_mes
            interes_ano += interes_mes
            amort_ano += amort_mes
            saldo -= amort_mes
        saldo -= h_amort_extra
        saldo = max(0, saldo)
        filas.append({
            "Año": ano,
            "Cuota Anual (€)": round(cuota_fija * 12, 2),
            "Intereses (€)": round(interes_ano, 2),
            "Capital Amortizado (€)": round(amort_ano + h_amort_extra, 2),
            "Saldo Pendiente (€)": round(saldo, 2)
        })

    df_hip = pd.DataFrame(filas)
   

    # Gráfico fijo vs variable
    st.markdown("**Comparativa fijo vs. variable**")
    fig_hip = go.Figure()
    fig_hip.add_trace(go.Bar(name='Fijo', x=df_hip["Año"], y=df_hip["Cuota Anual (€)"],
                              marker_color='#4f8ef7'))
    cuotas_var = [calcular_cuota_hipoteca(max(0, df_hip.loc[i,"Saldo Pendiente (€)"]),
                                  def color_saldo(val):
        max_val = h_principal
        pct = val / max_val if max_val > 0 else 0
        r = int(76 + (224 - 76) * pct)
        g = int(175 - (175 - 92) * pct)
        b = int(130 - (130 - 92) * pct)
        return f'background-color: rgb({r},{g},{b}); color: #0f1117'

    styled = df_hip.style\
        .format({
            "Cuota Anual (€)": "{:,.2f}",
            "Intereses (€)": "{:,.2f}",
            "Capital Amortizado (€)": "{:,.2f}",
            "Saldo Pendiente (€)": "{:,.2f}",
        }).map(color_saldo, subset=["Saldo Pendiente (€)"])

    st.dataframe(styled, use_container_width=True, height=350)            h_tasa_variable, int(h_anos) - i) * 12
                  for i in range(len(df_hip))]
    fig_hip.add_trace(go.Scatter(name='Variable', x=df_hip["Año"], y=cuotas_var,
                                  line=dict(color='#e05c5c', width=2)))
    fig_hip.update_layout(template='plotly_dark', paper_bgcolor='#1a2332',
                           plot_bgcolor='#1a2332', height=260,
                           margin=dict(l=10, r=10, t=10, b=10),
                           legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_hip, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REFORMA Y VENTA (FLIPPING)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Reforma y Venta (Flipping)")
    st.caption("Calcula el beneficio neto de comprar, reformar y vender")

    col1, col2 = st.columns(2)
    with col1:
        f_precio_compra = st.number_input("Precio de compra (€)", value=120000, step=5000, key="f_comp")
        f_itp = st.number_input("ITP (€)", value=12000, step=500, key="f_itp")
        f_notaria = st.number_input("Notaría + Registro (€)", value=2000, step=100, key="f_not")
        f_reforma = st.number_input("Coste de reforma (€)", value=30000, step=1000, key="f_ref")
        f_financiacion = st.number_input("Intereses de financiación (€)", value=3000, step=500, key="f_fin")
    with col2:
        f_precio_venta = st.number_input("Precio de venta objetivo (€)", value=210000, step=5000, key="f_venta")
        f_agencia_venta = st.number_input("Agencia (% sobre venta)", value=3.0, step=0.5, key="f_ag")
        f_plusvalia = st.number_input("Plusvalía municipal (€)", value=1500, step=100, key="f_plus")
        f_irpf = st.slider("Tipo IRPF sobre ganancia (%)", 19, 28, 21, key="f_irpf")
        f_meses = st.number_input("Duración del proyecto (meses)", value=9, step=1, key="f_meses")

    f_coste_total = f_precio_compra + f_itp + f_notaria + f_reforma + f_financiacion
    f_agencia_importe = f_precio_venta * f_agencia_venta / 100
    f_ganancia_bruta = f_precio_venta - f_coste_total - f_agencia_importe - f_plusvalia
    f_impuesto = f_ganancia_bruta * f_irpf / 100 if f_ganancia_bruta > 0 else 0
    f_ganancia_neta = f_ganancia_bruta - f_impuesto
    f_roi = f_ganancia_neta / f_coste_total * 100
    f_roi_anualizado = ((1 + f_roi/100) ** (12/f_meses) - 1) * 100 if f_meses > 0 else 0
    f_margen = f_ganancia_neta / f_precio_venta * 100

    st.markdown("---")
    cols_f = st.columns(4)
    datos_f = [
        ("Beneficio Neto", f"{f_ganancia_neta:,.0f} €", "green" if f_ganancia_neta > 0 else "red"),
        ("ROI", f"{f_roi:.1f}%", "green" if f_roi > 10 else "red"),
        ("ROI Anualizado", f"{f_roi_anualizado:.1f}%", "green" if f_roi_anualizado > 12 else "blue"),
        ("Margen sobre venta", f"{f_margen:.1f}%", "blue"),
    ]
    for i, (l, v, c) in enumerate(datos_f):
        with cols_f[i]:
            st.markdown(metric_card(l, v, c), unsafe_allow_html=True)

    # Waterfall de costes y beneficio
    st.markdown("---")
    st.markdown("**Desglose de la operación**")
    fig_wf = go.Figure(go.Waterfall(
        name="Operación",
        orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["Precio Compra", "ITP+Gastos", "Reforma", "Financiación", "Agencia Venta", "Plusvalía+IRPF", "Precio Venta", "BENEFICIO NETO"],
        y=[-f_precio_compra, -(f_itp+f_notaria), -f_reforma, -f_financiacion,
           -f_agencia_importe, -(f_plusvalia+f_impuesto), f_precio_venta, 0],
        connector=dict(line=dict(color="#2a3441")),
        decreasing=dict(marker=dict(color="#e05c5c")),
        increasing=dict(marker=dict(color="#4caf82")),
        totals=dict(marker=dict(color="#4f8ef7"))
    ))
    fig_wf.update_layout(template='plotly_dark', paper_bgcolor='#1a2332',
                          plot_bgcolor='#1a2332', height=320,
                          margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_wf, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ALQUILER TURÍSTICO
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Alquiler Turístico")
    st.caption("Compara el rendimiento de alquiler turístico frente al residencial")

    col1, col2 = st.columns(2)
    with col1:
        t_precio = st.number_input("Precio del inmueble (€)", value=200000, step=5000, key="t_precio")
        t_gastos_adq = st.number_input("Gastos de adquisición (€)", value=22000, step=500, key="t_gadq")
        t_precio_noche = st.number_input("Precio por noche (€)", value=95, step=5, key="t_noche")
        t_ocupacion_turistica = st.slider("Ocupación turística (%)", 30, 100, 65, key="t_ocup")
        t_estancia_media = st.number_input("Estancia media (noches)", value=4, step=1, key="t_est")
    with col2:
        t_plataforma_pct = st.number_input("Comisión plataforma (%)", value=15.0, step=0.5, key="t_plat")
        t_limpieza_por_estancia = st.number_input("Coste limpieza por estancia (€)", value=60, step=5, key="t_limp")
        t_suministros = st.number_input("Suministros anuales (€)", value=1800, step=100, key="t_sum")
        t_otros_gastos = st.number_input("Otros gastos anuales (€)", value=1200, step=100, key="t_otros")
        t_alquiler_residencial = st.number_input("Alquiler residencial equivalente (€/mes)", value=900, step=50, key="t_resid")

    noches_ano = 365 * t_ocupacion_turistica / 100
    estancias = noches_ano / t_estancia_media
    ingresos_brutos_t = t_precio_noche * noches_ano
    comision_plataforma = ingresos_brutos_t * t_plataforma_pct / 100
    gastos_limpieza = estancias * t_limpieza_por_estancia
    gastos_totales_t = comision_plataforma + gastos_limpieza + t_suministros + t_otros_gastos
    ingreso_neto_t = ingresos_brutos_t - gastos_totales_t
    rent_turistica = ingreso_neto_t / (t_precio + t_gastos_adq) * 100

    ingreso_neto_resid = t_alquiler_residencial * 12 * 0.85  # aprox neto
    rent_residencial = ingreso_neto_resid / (t_precio + t_gastos_adq) * 100

    st.markdown("---")
    cols_t = st.columns(4)
    datos_t = [
        ("Ingresos Brutos Turístico", f"{ingresos_brutos_t:,.0f} €/año", "blue"),
        ("Ingreso Neto Turístico", f"{ingreso_neto_t:,.0f} €/año", "green" if ingreso_neto_t > ingreso_neto_resid else "red"),
        ("Rentabilidad Turística", f"{rent_turistica:.2f}%", "green" if rent_turistica > rent_residencial else "red"),
        ("Rentabilidad Residencial", f"{rent_residencial:.2f}%", "blue"),
    ]
    for i, (l, v, c) in enumerate(datos_t):
        with cols_t[i]:
            st.markdown(metric_card(l, v, c), unsafe_allow_html=True)

    # Gráfico comparativo
    st.markdown("---")
    st.markdown("**Comparativa por modalidad de alquiler**")
    fig_comp = go.Figure()
    categorias = ["Ingresos Brutos", "Gastos", "Ingresos Netos"]
    vals_turistico = [ingresos_brutos_t, gastos_totales_t, ingreso_neto_t]
    vals_residencial = [t_alquiler_residencial * 12, t_alquiler_residencial * 12 * 0.15, ingreso_neto_resid]

    fig_comp.add_trace(go.Bar(name='Turístico', x=categorias, y=vals_turistico, marker_color='#4f8ef7'))
    fig_comp.add_trace(go.Bar(name='Residencial', x=categorias, y=vals_residencial, marker_color='#7c5cbf'))
    fig_comp.update_layout(template='plotly_dark', paper_bgcolor='#1a2332',
                            plot_bgcolor='#1a2332', height=280, barmode='group',
                            margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_comp, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — COMPARADOR DE ACTIVOS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Comparador de Oportunidades")
    st.caption("Compara hasta 4 inmuebles simultáneamente")

    n_activos = st.radio("Número de activos a comparar", [2, 3, 4], horizontal=True)

    activos = []
    cols_activos = st.columns(n_activos)
    for i in range(n_activos):
        with cols_activos[i]:
            st.markdown(f"**Activo {i+1}**")
            nombre = st.text_input("Nombre / Dirección", value=f"Inmueble {i+1}", key=f"comp_nom_{i}")
            precio_c = st.number_input("Precio compra (€)", value=150000 + i*30000, step=5000, key=f"comp_prec_{i}")
            alq = st.number_input("Alquiler mensual (€)", value=750 + i*100, step=50, key=f"comp_alq_{i}")
            gast = st.number_input("Gastos anuales (€)", value=3000 + i*200, step=100, key=f"comp_gast_{i}")
            itp_c = st.number_input("Gastos adquisición (€)", value=int(precio_c * 0.12), step=500, key=f"comp_itp_{i}")

            rent_b = alq * 12 / precio_c * 100
            noi_c = alq * 12 - gast
            rent_n = noi_c / (precio_c + itp_c) * 100
            activos.append({
                "Activo": nombre,
                "Precio (€)": precio_c,
                "Alquiler/mes (€)": alq,
                "Rent. Bruta (%)": round(rent_b, 2),
                "Rent. Neta (%)": round(rent_n, 2),
                "NOI Anual (€)": round(noi_c, 0),
                "Inversión Total (€)": precio_c + itp_c,
            })

    st.markdown("---")
    st.markdown("**Tabla comparativa**")
    df_comp = pd.DataFrame(activos).set_index("Activo")

    def color_mejor(col):
        colors = []
        for v in col:
            if v == col.max():
                colors.append('background-color: #1a3a2a; color: #4caf82; font-weight: 600')
            elif v == col.min():
                colors.append('background-color: #3a1a1a; color: #e05c5c')
            else:
                colors.append('')
        return colors

    styled = df_comp.style\
        .format("{:,.2f}", subset=["Rent. Bruta (%)", "Rent. Neta (%)"])\
        .format("{:,.0f}", subset=["Precio (€)", "Alquiler/mes (€)", "NOI Anual (€)", "Inversión Total (€)"])\
        .apply(color_mejor, subset=["Rent. Bruta (%)", "Rent. Neta (%)"])

    st.dataframe(styled, use_container_width=True)

    # Gráfico radar
    if len(activos) >= 2:
        st.markdown("**Análisis visual comparativo**")
        categorias_radar = ["Rent. Bruta (%)", "Rent. Neta (%)"]
        fig_bar = go.Figure()
        for a in activos:
            fig_bar.add_trace(go.Bar(
                name=a["Activo"],
                x=categorias_radar,
                y=[a["Rent. Bruta (%)"], a["Rent. Neta (%)"]],
            ))
        fig_bar.update_layout(template='plotly_dark', paper_bgcolor='#1a2332',
                               plot_bgcolor='#1a2332', height=260, barmode='group',
                               margin=dict(l=10, r=10, t=10, b=10),
                               legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_bar, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ANÁLISIS DE ESCENARIOS + TIR / VAN
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Análisis de Escenarios y TIR / VAN")
    st.caption("Proyección a largo plazo en escenarios pesimista, base y optimista")

    col1, col2 = st.columns(2)
    with col1:
        e_precio = st.number_input("Precio de compra (€)", value=180000, step=5000, key="e_prec")
        e_entrada = st.number_input("Entrada + gastos (€)", value=50000, step=1000, key="e_ent")
        e_alquiler = st.number_input("Alquiler mensual base (€)", value=900, step=50, key="e_alq")
        e_gastos = st.number_input("Gastos anuales (€)", value=3500, step=100, key="e_gast")
        e_cuota = st.number_input("Cuota hipoteca mensual (€)", value=620, step=10, key="e_cuota")
    with col2:
        e_anos = st.slider("Horizonte temporal (años)", 5, 30, 15, key="e_anos")
        e_tasa = st.number_input("Tasa de descuento (%) para VAN", value=7.0, step=0.5, key="e_tasa")

    escenarios = {
        "Pesimista": {"alq_crec": 0.5, "ocup": 85, "reval": 0.5, "color": "#e05c5c"},
        "Base":      {"alq_crec": 2.0, "ocup": 92, "reval": 2.0, "color": "#4f8ef7"},
        "Optimista": {"alq_crec": 3.5, "ocup": 97, "reval": 4.0, "color": "#4caf82"},
    }

    st.markdown("---")
    resultados_esc = {}
    fig_esc = go.Figure()

    for nombre_esc, params in escenarios.items():
        flujos = [-e_entrada]
        cf_acumulado = []
        alq_actual = e_alquiler
        precio_venta_final = e_precio

        for ano in range(1, int(e_anos) + 1):
            alq_actual *= (1 + params["alq_crec"] / 100)
            ingresos = alq_actual * 12 * params["ocup"] / 100
            cf = ingresos - e_gastos - e_cuota * 12
            flujos.append(cf)
            cf_acumulado.append(sum(flujos[1:]))
            precio_venta_final *= (1 + params["reval"] / 100)

        flujos[-1] += precio_venta_final  # venta al final
        tir = calcular_van(flujos, 0) # comprobación
        van = calcular_van(flujos, e_tasa)

        # TIR por aproximación
        tir_val = None
        for r_test in np.linspace(0.001, 2.0, 50000):
            npv_test = sum(f / (1 + r_test)**i for i, f in enumerate(flujos))
            if abs(npv_test) < 500:
                tir_val = r_test * 100
                break

        resultados_esc[nombre_esc] = {"VAN": van, "TIR": tir_val, "Precio Venta": precio_venta_final, "color": params["color"]}

        fig_esc.add_trace(go.Scatter(
            x=list(range(1, int(e_anos) + 1)),
            y=cf_acumulado,
            name=nombre_esc,
            line=dict(color=params["color"], width=2),
            fill='tozeroy' if nombre_esc == "Base" else None,
            fillcolor='rgba(79,142,247,0.06)' if nombre_esc == "Base" else None
        ))

    # Mostrar TIR y VAN
    cols_esc = st.columns(3)
    for i, (nombre_esc, res) in enumerate(resultados_esc.items()):
        with cols_esc[i]:
            c_van = "green" if res["VAN"] > 0 else "red"
            c_tir = "green" if (res["TIR"] or 0) > e_tasa else "red"
            st.markdown(f"<h4 style='color:{res['color']};text-align:center;margin-bottom:12px'>{nombre_esc}</h4>", unsafe_allow_html=True)
            st.markdown(metric_card("VAN", f"{res['VAN']:,.0f} €", c_van), unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            tir_str = f"{res['TIR']:.2f}%" if res['TIR'] else "N/D"
            st.markdown(metric_card("TIR Anual", tir_str, c_tir), unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown(metric_card("Precio Venta Est.", f"{res['Precio Venta']:,.0f} €", "blue"), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Evolución del Cash Flow acumulado por escenario**")
    fig_esc.update_layout(
        template='plotly_dark', paper_bgcolor='#1a2332', plot_bgcolor='#1a2332',
        height=300, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Años", yaxis_title="Cash Flow Acumulado (€)",
        legend=dict(orientation="h", y=1.12)
    )
    fig_esc.add_hline(y=0, line_dash="dash", line_color="#8892a4", opacity=0.5)
    st.plotly_chart(fig_esc, use_container_width=True)

# ─── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#4a5568; font-size:0.8rem; padding:16px 0'>
    BrickVest · Análisis profesional de inversión inmobiliaria · Solo para fines informativos
</div>
""", unsafe_allow_html=True)
