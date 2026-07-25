# 🌤️ Pipeline ETL - Dados Climáticos de Joinville/SC

> Pipeline ETL automatizado para coleta, transformação e armazenamento de dados meteorológicos em tempo real da cidade de Joinville, Santa Catarina.

Projeto pessoal de estudo em Engenharia de Dados, construído do zero para praticar um fluxo real de ETL: coleta de dados de uma API pública, transformação com Pandas e persistência em banco de dados, com orquestração automatizada via Apache Airflow.

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura do Pipeline](#-arquitetura-do-pipeline)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Como Executar](#-como-executar)
- [Detalhamento das Etapas](#-detalhamento-das-etapas)
- [Desafios do Ambiente Windows](#-desafios-do-ambiente-windows)
- [Troubleshooting](#-troubleshooting)
- [Aprendizados e Próximos Passos](#-aprendizados-e-próximos-passos)

---

## 🎯 Sobre o Projeto

Este é meu primeiro pipeline ETL completo de Engenharia de Dados, criado como projeto de estudo prático. O objetivo foi sair da teoria e colocar a mão na massa em um fluxo real de dados: coletar informações meteorológicas de uma API pública, transformar esses dados em um formato estruturado e persistir tudo em um banco de dados relacional, com todo o processo orquestrado automaticamente pelo Apache Airflow.

O pipeline coleta dados meteorológicos da API do **OpenWeatherMap** para a cidade de **Joinville, Santa Catarina**, aplica transformações com Pandas e armazena os dados em um banco **PostgreSQL**, rodando em containers Docker.

Como desenvolvi o projeto em **Windows**, boa parte do trabalho envolveu também lidar com as particularidades desse ecossistema (PowerShell, Git Bash, gerenciamento de ambiente virtual, variáveis de ambiente, permissões, etc.) — o que acabou virando um aprendizado extra tão valioso quanto o pipeline em si.

---

## 🏗️ Arquitetura do Pipeline

```
OpenWeatherMap API
        │
        ▼
   [EXTRACT] ──> salva JSON bruto (data/weather_data.json)
        │
        ▼
  [TRANSFORM] ──> normaliza, limpa e converte com Pandas
        │
        ▼
     [LOAD] ──> grava na tabela joinville_weather (PostgreSQL)
```

Toda a orquestração é feita por uma DAG do Airflow, executada em intervalos regulares, com os serviços rodando em containers Docker (Airflow, PostgreSQL e Redis).

---

## 🛠️ Stack Tecnológica

### Core
- **Python 3.12+** — linguagem principal
- **Apache Airflow 3.1.7** — orquestração do pipeline
- **PostgreSQL** — banco de dados relacional
- **Docker & Docker Compose** — containerização

### Bibliotecas Python
- **pandas** — manipulação e transformação de dados
- **requests** — requisições HTTP para a API
- **SQLAlchemy** — ORM para interação com o banco de dados
- **psycopg2** — driver PostgreSQL
- **python-dotenv** — gerenciamento de variáveis de ambiente

### Ferramentas
- **uv** — gerenciador de pacotes e ambientes Python
- **Redis** — message broker para o Celery Executor do Airflow

---

## 📁 Estrutura do Projeto

```
pipeline_weather/
├── config/
│   └── .env                  # variáveis de ambiente (não versionado)
├── dags/
│   └── weather_pipeline.py   # definição da DAG do Airflow
├── data/
│   └── weather_data.json     # dados brutos extraídos da API
├── src/
│   ├── extract_data.py       # etapa de Extract
│   ├── transform_data.py     # etapa de Transform
│   └── load_data.py          # etapa de Load
├── docker-compose.yaml
└── README.md
```

---

## ✅ Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e funcionando (no Windows, ele usa o WSL2 como motor)
- Conta gratuita na [OpenWeatherMap](https://openweathermap.org/api) para gerar uma API Key
- [uv](https://docs.astral.sh/uv/) instalado, caso queira rodar o pipeline localmente sem o Airflow

> ⚠️ O Airflow completo via Docker consome bastante RAM (recomenda-se pelo menos 4-8GB livres). Veja a seção [Desafios do Ambiente Windows](#-desafios-do-ambiente-windows) para mais detalhes.

---

## 🚀 Instalação e Configuração

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/GChandrone/weather-etl-pipeline.git
cd weather-etl-pipeline
```

### 2️⃣ Obtenha sua API Key da OpenWeatherMap

1. Crie uma conta gratuita em [openweathermap.org](https://openweathermap.org/api)
2. Gere sua API Key no painel
3. Guarde a chave para o próximo passo

### 3️⃣ Configure as variáveis de ambiente

Crie um arquivo `.env` dentro da pasta `config/`:

```
# config/.env
API_KEY=sua_chave_api_aqui
user=airflow
password=airflow
database=airflow
```

> ⚠️ Nunca commite o arquivo `.env` — adicione a pasta `config/` (ou o arquivo `.env`) no `.gitignore`.

### 4️⃣ Suba os containers

```bash
docker compose up -d
```

Aguarde alguns minutos até todos os serviços ficarem saudáveis.

### 5️⃣ Verifique se tudo está rodando

```bash
docker ps
```

Você deve ver os serviços `airflow-apiserver`, `airflow-scheduler`, `airflow-worker`, `airflow-triggerer`, `airflow-dag-processor`, `postgres` e `redis`.

---

## 🎮 Como Executar

### 1️⃣ Acesse a interface do Airflow

```
http://127.0.0.1:8080
```

> No Windows, `localhost:8080` pode não resolver corretamente dependendo da configuração de rede — se isso acontecer, use `127.0.0.1:8080`.

**Credenciais padrão:** `airflow` / `airflow`

### 2️⃣ Ative a DAG

Localize a DAG `weather_pipeline` na interface e ative o toggle. Ela está configurada para rodar automaticamente a cada 1 hora.

---

## 🔍 Detalhamento das Etapas

### 📥 Extract — `src/extract_data.py`

Faz uma requisição HTTP GET para a API do OpenWeatherMap, valida o status da resposta e salva os dados brutos em `data/weather_data.json`.

### 🔄 Transform — `src/transform_data.py`

- Converte o JSON em DataFrame com `pandas`
- Normaliza a coluna `weather` (que vem como lista de dicionários)
- Remove colunas desnecessárias
- Renomeia colunas para nomes claros
- Converte timestamps Unix para datetime

### 💾 Load — `src/load_data.py`

Conecta ao PostgreSQL via SQLAlchemy e grava os dados transformados na tabela `joinville_weather`, usando `if_exists='append'` para acumular o histórico a cada execução.

---

## 🪟 Desafios do Ambiente Windows

Boa parte da documentação e das ferramentas do ecossistema de dados assume um ambiente Linux/macOS por padrão, então rodar esse projeto no Windows trouxe desafios específicos que valem registrar:

- **Ativação de ambiente virtual**: no Windows o `.venv` usa a pasta `Scripts` em vez de `bin` (`.venv\Scripts\Activate.ps1` no PowerShell, ou `source .venv/Scripts/activate` no Git Bash)
- **Docker Desktop depende do WSL2**: mesmo sem usar o WSL diretamente, o Docker Desktop no Windows utiliza o WSL2 como motor de virtualização por baixo dos panos
- **Consumo de RAM**: o Airflow completo (com Celery Executor, Redis, múltiplos containers) se mostrou bastante pesado para notebooks com pouca memória RAM, causando travamentos no Docker Desktop/WSL2 durante a subida dos containers
- **`localhost` vs `127.0.0.1`**: em alguns momentos `localhost:8080` não resolvia corretamente no navegador, sendo necessário usar `127.0.0.1:8080`
- **Diferenças de terminal**: comandos como `curl`, `source` e caminhos com `/` precisaram ser adaptados entre PowerShell, cmd e Git Bash

---

## 🐛 Troubleshooting

### DAG não aparece no Airflow
```bash
docker compose logs airflow-scheduler
docker compose restart
```

### Erro de conexão com o banco de dados
Verifique se o container do PostgreSQL está saudável:
```bash
docker compose ps postgres
```
E confirme se o host configurado é o nome do serviço no `docker-compose.yaml` (ex: `postgres`), e não `localhost`, quando o script roda dentro de outro container.

### API retorna erro 401
Confirme se o arquivo `config/.env` existe e se a variável `API_KEY` está correta.

### Docker travando por falta de memória
Crie/edite o arquivo `.wslconfig` em `C:\Users\<seu-usuario>\.wslconfig` para limitar o consumo do WSL2:
```ini
[wsl2]
memory=6GB
processors=4
```
Depois rode `wsl --shutdown` e reinicie o Docker Desktop.

---

## 📈 Aprendizados e Próximos Passos

Esse projeto foi meu primeiro contato prático com orquestração de pipelines via Airflow, containerização com Docker e todo o fluxo de ETL de ponta a ponta. Também serviu para entender, na prática, as diferenças de trabalhar com ferramentas de dados em um ambiente Windows.

Percebi que a arquitetura completa do Airflow via Docker é pesada demais para o meu notebook atual, então para os próximos projetos pretendo explorar alternativas mais leves, como o **Airflow em modo standalone** ou orquestradores mais leves como **Prefect** ou **Dagster**.
