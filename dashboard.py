"""
Painel do Tempo — Joinville, SC
--------------------------------
Lê a leitura mais recente (e o histórico) da tabela `joinville_weather`
no PostgreSQL e apresenta o clima atual em um painel visual.

Como rodar:
    uv run streamlit run dashboard.py
"""
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from src.load_data import engine, TABLE_NAME_DEFAULT

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ICON_URL = "https://openweathermap.org/img/wn/{icon}@4x.png"

st.set_page_config(
    page_title="Joinville · Painel do Tempo",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------
def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root{
            --bg:#12271F; --panel:#1B3428; --panel-2:#193024; --hair:#2E4C3D;
            --ink:#F3EFE1; --sage:#93A79A; --sage-dim:#5E7568;
            --brass:#D1AC5B; --brass-dim:#8A7643; --sky:#87B7C9;
        }
        html, body, [class*="css"] { font-family:'Inter', sans-serif; }
        .stApp{
            background:
              radial-gradient(ellipse 800px 480px at 50% -12%, rgba(209,172,91,.10), transparent 60%),
              var(--bg);
            color: var(--ink);
        }
        #MainMenu, footer, header {visibility:hidden;}
        .block-container{ max-width:640px; padding-top:2.6rem; }

        .eyebrow{
            font-family:'JetBrains Mono', monospace; font-size:11.5px; letter-spacing:2px;
            text-transform:uppercase; color: var(--sage); text-align:center;
        }
        .place{
            font-family:'Fraunces', serif; font-weight:500; font-size:22px;
            text-align:center; color:var(--ink); margin-top:2px;
        }
        .datestamp{
            font-family:'JetBrains Mono', monospace; font-size:11px; color: var(--sage-dim);
            text-align:center; margin-top:4px; letter-spacing:.4px;
        }

        .panel{
            background: linear-gradient(180deg, var(--panel), var(--panel-2));
            border:1px solid var(--hair); border-radius:22px;
            padding:34px 28px 26px; margin-top:26px;
            box-shadow: 0 30px 60px -30px rgba(0,0,0,.55);
        }

        /* dial */
        .dial-wrap{ display:flex; justify-content:center; margin:6px 0 6px; }
        .dial{
            width:216px; height:216px; border-radius:50%;
            background: conic-gradient(from 180deg, var(--brass) calc(var(--pct)*1%), rgba(255,255,255,.08) 0);
            padding:9px;
        }
        .dial-inner{
            width:100%; height:100%; border-radius:50%;
            background: radial-gradient(circle at 35% 30%, #20402F, #14281F 72%);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.08), inset 0 8px 24px rgba(0,0,0,.35);
            display:flex; flex-direction:column; align-items:center; justify-content:center;
        }
        .dial-icon{ width:58px; height:58px; margin-bottom:-6px; filter: drop-shadow(0 4px 10px rgba(0,0,0,.4)); }
        .dial-temp{ font-family:'Fraunces', serif; font-weight:500; font-size:52px; line-height:1; color:var(--ink); }
        .dial-temp sup{ font-size:20px; color:var(--brass); top:-22px; font-weight:400; }
        .dial-desc{ font-family:'Inter', sans-serif; font-size:12.5px; color:var(--sage); text-transform:capitalize; margin-top:2px; letter-spacing:.3px; }

        .range-row{ text-align:center; font-family:'JetBrains Mono', monospace; font-size:11.5px; color:var(--sage-dim); margin-top:16px; letter-spacing:.3px;}
        .range-row b{ color: var(--sage); }

        /* sun arc */
        .sun-row{ display:flex; align-items:center; gap:12px; margin-top:26px; }
        .sun-time{ font-family:'JetBrains Mono', monospace; font-size:11px; color:var(--sage-dim); white-space:nowrap; }
        .sun-track{ flex:1; height:2px; background: var(--hair); border-radius:2px; position:relative; }
        .sun-fill{ position:absolute; top:0; left:0; height:2px; background: linear-gradient(90deg, var(--brass-dim), var(--brass)); border-radius:2px; }
        .sun-dot{ position:absolute; top:50%; width:9px; height:9px; border-radius:50%; background:var(--brass);
                   box-shadow:0 0 10px rgba(209,172,91,.7); transform:translate(-50%,-50%); }

        /* readouts */
        .readouts{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--hair);
                    border:1px solid var(--hair); border-radius:14px; overflow:hidden; margin-top:26px; }
        .readout{ background:var(--panel-2); padding:14px 10px; text-align:center; }
        .readout .val{ font-family:'Fraunces', serif; font-size:19px; color:var(--ink); font-weight:500; }
        .readout .lbl{ font-family:'JetBrains Mono', monospace; font-size:9.5px; letter-spacing:.6px; text-transform:uppercase; color:var(--sage-dim); margin-top:3px; }

        .trend-title{ font-family:'JetBrains Mono', monospace; font-size:10.5px; letter-spacing:1.2px; text-transform:uppercase;
                       color:var(--sage-dim); margin:28px 0 6px 2px; }

        .footer-stamp{ text-align:center; font-family:'JetBrains Mono', monospace; font-size:10.5px; color:var(--sage-dim); margin-top:22px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner="Consultando o tempo em Joinville...")
def load_data(table_name: str) -> pd.DataFrame:
    logging.info(f"Lendo dados da tabela {table_name}")
    query = f"SELECT * FROM {table_name} ORDER BY datetime ASC"
    df = pd.read_sql(query, con=engine, parse_dates=["datetime", "sunrise", "sunset"])
    return df


_DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
_MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _data_pt_br(dt: pd.Timestamp) -> str:
    # Evita depender do locale do servidor (Streamlit Cloud roda em inglês por padrão,
    # o que faria %A/%B saírem em inglês mesmo com texto em português ao redor).
    return f"{_DIAS[dt.weekday()]}, {dt.day} de {_MESES[dt.month - 1]}"


def render_header(dt: pd.Timestamp) -> None:
    st.markdown('<div class="eyebrow">Painel do Tempo</div>', unsafe_allow_html=True)
    st.markdown('<div class="place">Joinville, Santa Catarina</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="datestamp">{_data_pt_br(dt)} · leitura das {dt:%H:%M}</div>', unsafe_allow_html=True)


def render_dial(latest: pd.Series) -> None:
    icon = latest.get("weather_icon", "01d")
    desc = latest.get("weather_description", "—")
    temp = float(latest.get("temperature", 0))
    feels = latest.get("feels_like")
    tmin = latest.get("temp_min")
    tmax = latest.get("temp_max")

    pct = max(0, min(100, (temp / 40) * 100))

    st.markdown(f'<div class="dial-wrap"><div class="dial" style="--pct:{pct:.0f};"><div class="dial-inner">'
                f'<img class="dial-icon" src="{ICON_URL.format(icon=icon)}"/>'
                f'<div class="dial-temp">{temp:.0f}<sup>°C</sup></div>'
                f'<div class="dial-desc">{desc}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True)

    st.markdown(
        f'<div class="range-row">sensação <b>{feels:.0f}°</b> &nbsp;·&nbsp; mín <b>{tmin:.0f}°</b> '
        f'&nbsp;·&nbsp; máx <b>{tmax:.0f}°</b></div>',
        unsafe_allow_html=True,
    )


def render_sun_arc(latest: pd.Series) -> None:
    sunrise, sunset, now = latest.get("sunrise"), latest.get("sunset"), latest.get("datetime")
    if pd.isna(sunrise) or pd.isna(sunset):
        return
    total = (sunset - sunrise).total_seconds()
    elapsed = (now - sunrise).total_seconds()
    frac = max(0.0, min(1.0, elapsed / total)) if total > 0 else 0.0

    st.markdown(
        f'<div class="sun-row">'
        f'<span class="sun-time">☾ {sunrise:%H:%M}</span>'
        f'<div class="sun-track">'
        f'<div class="sun-fill" style="width:{frac*100:.1f}%;"></div>'
        f'<div class="sun-dot" style="left:{frac*100:.1f}%;"></div>'
        f'</div>'
        f'<span class="sun-time">{sunset:%H:%M} ☾</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_readouts(latest: pd.Series) -> None:
    items = [
        (f'{latest.get("humidity", 0):.0f}%', "Umidade"),
        (f'{latest.get("pressure", 0):.0f}', "Pressão hPa"),
        (f'{latest.get("wind_speed", 0):.1f}', "Vento m/s"),
        (f'{latest.get("clouds", 0):.0f}%', "Nuvens"),
    ]
    html = '<div class="readouts">'
    for val, lbl in items:
        html += f'<div class="readout"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_trend(df: pd.DataFrame) -> None:
    if len(df) < 3:
        return
    recent = df.tail(48)
    st.markdown('<div class="trend-title">Temperatura recente</div>', unsafe_allow_html=True)
    chart = (
        alt.Chart(recent)
        .mark_line(color="#D1AC5B", strokeWidth=2, interpolate="monotone")
        .encode(
            x=alt.X("datetime:T", title=None, axis=alt.Axis(format="%d/%m %Hh", labelColor="#5E7568", domainColor="#2E4C3D", tickColor="#2E4C3D", gridColor="#1E3A2C")),
            y=alt.Y("temperature:Q", title=None, axis=alt.Axis(labelColor="#5E7568", gridColor="#1E3A2C")),
            tooltip=[alt.Tooltip("datetime:T", title="Data", format="%d/%m %H:%M"), alt.Tooltip("temperature:Q", title="°C")],
        )
        .properties(height=140, background="transparent")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    inject_css()

    try:
        df = load_data(TABLE_NAME_DEFAULT)
    except Exception as exc:
        logging.error(f"Erro ao conectar no banco: {exc}")
        st.error("Não foi possível carregar os dados do tempo agora.")
        st.stop()

    if df.empty:
        st.info("Ainda não há leituras registradas. Volte em instantes.")
        st.stop()

    latest = df.iloc[-1]

    render_header(latest["datetime"])

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    render_dial(latest)
    render_sun_arc(latest)
    render_readouts(latest)
    render_trend(df)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="footer-stamp">atualizado às {datetime.now():%H:%M}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()