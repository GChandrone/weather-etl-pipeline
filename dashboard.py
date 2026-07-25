"""
Painel do Tempo — Joinville, SC
Dashboard "Aurora Glassmorphism": Máximo Impacto Visual com Ícones Vetoriais Premium
"""
from datetime import datetime
import altair as alt
import pandas as pd
import streamlit as st
import logging
import re

from src.load_data import engine, TABLE_NAME_DEFAULT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuração da Página
st.set_page_config(
    page_title="Joinville Weather | Live ETL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS Extremo: Glassmorphism, Gradientes Animados e Glow Effects
# ---------------------------------------------------------------------------
def inject_css() -> None:
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    /* Fundo Escuro com Textura de Malha Radial */
    .stApp {
        background: radial-gradient(circle at 15% 50%, rgba(20, 30, 48, 1), rgba(36, 59, 85, 0) 50%),
                    radial-gradient(circle at 85% 30%, rgba(0, 198, 255, 0.05), rgba(0, 114, 255, 0) 50%),
                    #0B0C10;
        font-family: 'Outfit', sans-serif;
        color: #FFFFFF;
    }
    
    #MainMenu, header, footer {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }

    /* Container Principal */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 24px;
        margin-bottom: 24px;
    }

    /* Estilo "Glassmorphism" Base */
    .glass-card {
        background: rgba(17, 25, 40, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        border-color: rgba(0, 242, 254, 0.3);
        box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.1);
        transform: translateY(-4px);
    }

    /* Brilho Animado no Hero */
    .hero-glow {
        grid-column: span 12;
        background: linear-gradient(135deg, rgba(0, 198, 255, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%);
        border-left: 4px solid #00F2FE;
        display: flex; justify-content: space-between; align-items: center;
    }

    .side-card { grid-column: span 4; }
    
    @media (max-width: 1000px) {
        .side-card { grid-column: span 6; }
    }
    @media (max-width: 650px) {
        .side-card { grid-column: span 12; }
        .hero-glow { flex-direction: column; text-align: center; gap: 20px; }
    }

    /* Tipografia e Gradientes */
    .text-gradient {
        background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .hero-temp { font-size: 86px; line-height: 1; letter-spacing: -2px; margin: 10px 0; }
    .hero-title { font-size: 28px; font-weight: 600; color: #E0E0E0; }
    .hero-desc { font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #00F2FE; text-transform: uppercase; letter-spacing: 2px; }

    .card-title { font-size: 14px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
    .card-value { font-size: 42px; font-weight: 700; color: #FFFFFF; line-height: 1; }
    .card-unit { font-size: 18px; color: #6B7280; font-weight: 400; }
    .card-footer { font-size: 13px; color: #6B7280; margin-top: 8px; }

    /* Barra de Progresso CSS */
    .progress-container { width: 100%; background-color: rgba(255, 255, 255, 0.05); border-radius: 99px; height: 8px; margin-top: 16px; overflow: hidden; }
    .progress-bar { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #00F2FE, #4FACFE); position: relative; }
    .progress-glow { position: absolute; top: 0; right: 0; bottom: 0; width: 20px; box-shadow: 0 0 10px 2px #00F2FE; border-radius: 50%; }

    /* Distintivo Pulsante ETL */
    .etl-badge {
        display: flex; align-items: center; gap: 8px; padding: 8px 16px;
        background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.3);
        border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #00F2FE;
    }
    .pulse-dot { width: 8px; height: 8px; background-color: #00F2FE; border-radius: 50%; animation: pulse-cyan 2s infinite; }
    
    @keyframes pulse-cyan { 0% { box-shadow: 0 0 0 0 rgba(0, 242, 254, 0.6); } 70% { box-shadow: 0 0 0 8px rgba(0, 242, 254, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 242, 254, 0); } }

    /* Chart Container */
    .chart-box { grid-column: span 12; padding: 32px; margin-top: 8px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Lógica de Dados
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data(table_name: str) -> pd.DataFrame:
    logging.info(f"Lendo dados da tabela {table_name}")
    query = f"SELECT * FROM {table_name} ORDER BY datetime ASC"
    df = pd.read_sql(query, con=engine, parse_dates=["datetime", "sunrise", "sunset"])
    return df

def format_date(dt: pd.Timestamp) -> str:
    dias = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    return f"{dias[(dt.weekday() + 1) % 7]}, {dt.day:02d} {meses[dt.month - 1]} {dt.year}"

# ---------------------------------------------------------------------------
# Renderização do Dashboard
# ---------------------------------------------------------------------------
def render_dashboard(df: pd.DataFrame):
    latest = df.iloc[-1]
    
    # Variáveis Extraídas
    dt = latest["datetime"]
    date_str = format_date(dt)
    temp = float(latest.get("temperature", 0))
    feels = float(latest.get("feels_like", 0))
    tmin = float(latest.get("temp_min", 0))
    tmax = float(latest.get("temp_max", 0))
    
    # Apenas formata a string, pois já chega traduzida do banco
    desc = str(latest.get("weather_description", "—")).title()
    
    icon_code = latest.get("weather_icon", "01d")
    icon_url = f"https://openweathermap.org/img/wn/{icon_code}@4x.png"
    
    wind = float(latest.get("wind_speed", 0))
    humidity = float(latest.get("humidity", 0))
    pressure = float(latest.get("pressure", 0))
    clouds = float(latest.get("clouds", 0))
    
    sunrise = latest["sunrise"].strftime("%H:%M") if pd.notna(latest.get("sunrise")) else "--:--"
    sunset = latest["sunset"].strftime("%H:%M") if pd.notna(latest.get("sunset")) else "--:--"

    # HTML com Ícones Vetoriais (SVG) puros
    html_content = f"""
    <div class="dashboard-grid">
        
        <!-- MAIN HERO CARD -->
        <div class="glass-card hero-glow">
            <div style="display: flex; align-items: center; gap: 24px;">
                <img src="{icon_url}" style="width: 160px; height: 160px; filter: drop-shadow(0 0 20px rgba(0, 242, 254, 0.4));" alt="Weather Icon">
                <div>
                    <div class="hero-desc">📍 Joinville, Santa Catarina</div>
                    <div class="hero-temp text-gradient">{temp:.0f}°C</div>
                    <div class="hero-title">{desc}</div>
                </div>
            </div>
            
            <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 24px; padding-top: 20px;">
                <div style="display: flex; gap: 32px; text-align: center;">
                    <div>
                        <div style="font-size: 12px; color: #9CA3AF; text-transform: uppercase;">Sensação</div>
                        <div style="font-size: 24px; font-weight: 700; color: #FFF;">{feels:.0f}°</div>
                    </div>
                    <div>
                        <div style="font-size: 12px; color: #9CA3AF; text-transform: uppercase;">Mín / Máx</div>
                        <div style="font-size: 24px; font-weight: 700; color: #FFF;">{tmin:.0f}° <span style="color:#6B7280">|</span> {tmax:.0f}°</div>
                    </div>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #6B7280;">Atualizado às {dt.strftime("%H:%M")}</div>
            </div>
        </div>

        <!-- UMIDADE COM SVG E BARRA DE PROGRESSO -->
        <div class="glass-card side-card">
            <div class="card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                Umidade Relativa
            </div>
            <div class="card-value">{humidity:.0f}<span class="card-unit">%</span></div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {humidity}%;"><div class="progress-glow"></div></div>
            </div>
            <div class="card-footer">Volume de saturação atual</div>
        </div>

        <!-- VENTO COM SVG -->
        <div class="glass-card side-card">
            <div class="card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>
                Velocidade do Vento
            </div>
            <div class="card-value">{wind:.1f}<span class="card-unit"> m/s</span></div>
            <div class="card-footer">Dinâmica atmosférica em tempo real</div>
        </div>

        <!-- NUVENS COM SVG E BARRA DE PROGRESSO -->
        <div class="glass-card side-card">
            <div class="card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>
                Cobertura de Nuvens
            </div>
            <div class="card-value">{clouds:.0f}<span class="card-unit">%</span></div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {clouds}%;"><div class="progress-glow"></div></div>
            </div>
            <div class="card-footer">Densidade espacial projetada</div>
        </div>

        <!-- PRESSÃO COM SVG -->
        <div class="glass-card side-card">
            <div class="card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 14v4M12 2v4M22 12h-4M6 12H2M19.07 4.93l-2.83 2.83M7.76 16.24l-2.83 2.83M19.07 19.07l-2.83-2.83M7.76 7.76 4.93 4.93M12 12m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0"/></svg>
                Pressão Atmosférica
            </div>
            <div class="card-value">{pressure:.0f}<span class="card-unit"> hPa</span></div>
            <div class="card-footer">Medição ao nível do mar</div>
        </div>

        <!-- SOL E DATA -->
        <div class="glass-card side-card" style="grid-column: span 8; display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;">
                <div class="card-title" style="justify-content: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v6"/><path d="M4.22 10.22l1.42 1.42"/><path d="M19.78 10.22l-1.42 1.42"/><path d="M22 22H2"/><path d="M8 6l4-4 4 4"/><path d="M16 18a4 4 0 0 0-8 0"/></svg>
                    Nascer do Sol
                </div>
                <div class="card-value text-gradient">{sunrise}</div>
            </div>
            <div style="height: 60px; width: 1px; background: rgba(255,255,255,0.1);"></div>
            <div style="text-align: center;">
                <div class="card-title" style="justify-content: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 10V2"/><path d="M4.22 10.22l1.42 1.42"/><path d="M19.78 10.22l-1.42 1.42"/><path d="M22 22H2"/><path d="M16 6l-4 4-4-4"/><path d="M16 18a4 4 0 0 0-8 0"/></svg>
                    Pôr do Sol
                </div>
                <div class="card-value text-gradient">{sunset}</div>
            </div>
            <div style="height: 60px; width: 1px; background: rgba(255,255,255,0.1);"></div>
            <div style="text-align: center;">
                <div class="card-title" style="justify-content: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00F2FE" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    Data da Leitura
                </div>
                <div style="font-size: 22px; font-weight: 600; color: #FFF; margin-top: 10px;">{date_str}</div>
            </div>
        </div>

    </div>
    """
    
    clean_html = re.sub(r'\n\s*', '', html_content)
    st.markdown(clean_html, unsafe_allow_html=True)

    # GRÁFICO ALTAIR NEON
    if len(df) >= 3:
        st.markdown('<div class="glass-card chart-box"><div class="card-title" style="font-size:16px;">📈 Tendência Térmica (Últimas 48h)</div>', unsafe_allow_html=True)
        recent_df = df.tail(48)
        
        chart = (
            alt.Chart(recent_df)
            .mark_area(
                line={'color': '#00F2FE', 'strokeWidth': 4},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='rgba(0, 242, 254, 0.6)', offset=0),
                        alt.GradientStop(color='rgba(79, 172, 254, 0.0)', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                interpolate='monotone'
            )
            .encode(
                x=alt.X("datetime:T", title="", axis=alt.Axis(format="%H:%M", labelColor="#9CA3AF", grid=True, gridColor="rgba(255,255,255,0.05)", domainColor="transparent")),
                y=alt.Y("temperature:Q", title="", scale=alt.Scale(zero=False), axis=alt.Axis(labelColor="#9CA3AF", gridColor="rgba(255,255,255,0.05)", domainColor="transparent")),
                tooltip=[alt.Tooltip("datetime:T", title="Horário", format="%d/%m %H:%M"), alt.Tooltip("temperature:Q", title="°C")]
            )
            .properties(height=260, background="transparent")
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Execução Principal
# ---------------------------------------------------------------------------
def main() -> None:
    inject_css()

    try:
        df = load_data(TABLE_NAME_DEFAULT)
    except Exception as exc:
        logging.error(f"Erro DB: {exc}")
        st.error("Falha de conexão: O fluxo de dados do Neon DB foi interrompido.")
        st.stop()

    if df.empty:
        st.info("Aguardando inserção de dados pelo script Airflow...")
        st.stop()

    render_dashboard(df)

if __name__ == "__main__":
    main()