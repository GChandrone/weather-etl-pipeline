from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

env_path = Path(__file__).resolve().parent.parent / 'config' / '.env'
load_dotenv(env_path)


def _get_secret(key: str, default: str | None = None) -> str | None:
    """
    Busca uma credencial em duas fontes, nessa ordem:
    1. st.secrets — usado quando o app roda no Streamlit Community Cloud.
    2. Variável de ambiente / config/.env — usado localmente e pelo Airflow.
    """
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


user = _get_secret('DB_USER')
password = _get_secret('DB_PASSWORD')
database = _get_secret('DB_NAME')
host = _get_secret('DB_HOST')
port = _get_secret('DB_PORT', '5432')

# Nome padrão da tabela de destino, reutilizado por main.py, pela DAG e pelo dashboard.
TABLE_NAME_DEFAULT = 'joinville_weather'

def get_engine():
    logging.info(f"Conectando em {host}:{port}/{database}")
    return create_engine(
        f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}"
        f"?sslmode=require"
    )

engine = get_engine()

def load_weather_data(table_name:str, df: pd.DataFrame):
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists='append',
        index=False
    )

    logging.info("Dados carregados com sucesso!")

    df_check = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
    logging.info(f"Total de registros na tabela: {len(df_check)}")