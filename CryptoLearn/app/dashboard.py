import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
from coleta import atualizar_tudo  # Importa a função do coleta.py

# Caminho do banco dentro de app/db/
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "db", "cripto.db")

# Configuração da página
st.set_page_config(page_title="CryptoLearn - Dashboard", layout="wide")

# Mostrar caminho do banco
st.sidebar.info(f"📁 Banco usado: `{DB_PATH}`")


# Botão para atualizar histórico + dados atuais

if st.sidebar.button(" Atualizar "):
    st.info("⏳ Atualizando histórico e dados atuais, aguarde...")
    try:
        atualizar_tudo()
        st.success("✅ Dados atualizados com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao atualizar dados: {e}")


# CARREGAR O BANCO APÓS A ATUALIZAÇÃO

if not os.path.exists(DB_PATH):
    st.error("❌ Banco de dados não encontrado. Execute o coleta.py uma vez localmente.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM cripto_dados ORDER BY timestamp ASC", conn)
conn.close()

# INTERFACE PRINCIPAL DO DASHBOARD
st.title("📊 Dashboard de Criptomoedas - CryptoLearn")

if df.empty:
    st.warning("Nenhum dado encontrado no banco de dados.")
    st.stop()

# Ajuste do tempo
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

# Filtros
moedas = df["nome"].unique()
moeda_selecionada = st.sidebar.selectbox("Escolha a moeda", moedas)
dias = st.sidebar.slider("Quantidade de dias para exibir", 30, 365, 365)

df_filtrado = df[df["nome"] == moeda_selecionada].copy()
hoje = df_filtrado["timestamp"].max()
data_limite = hoje - pd.Timedelta(days=dias)
df_filtrado = df_filtrado[df_filtrado["timestamp"] >= data_limite]

# GRÁFICO PRINCIPAL
min_price = df_filtrado["preco"].min()
max_price = df_filtrado["preco"].max()
df_filtrado["media_movel"] = df_filtrado["preco"].rolling(window=7).mean()

fig = go.Figure()

for i in range(1, len(df_filtrado)):
    preco_anterior = df_filtrado["preco"].iloc[i - 1]
    preco_atual = df_filtrado["preco"].iloc[i]
    cor = f"rgba({255 - int(255 * (preco_atual - min_price) / (max_price - min_price))}, {int(255 * (preco_atual - min_price) / (max_price - min_price))}, 0, 0.9)"
    fig.add_trace(go.Scatter(
        x=df_filtrado["timestamp"].iloc[i-1:i+1],
        y=df_filtrado["preco"].iloc[i-1:i+1],
        mode="lines",
        line=dict(color=cor, width=3),
        showlegend=False
    ))

fig.add_trace(go.Scatter(
    x=df_filtrado["timestamp"],
    y=df_filtrado["preco"],
    mode="lines",
    name=f"Preço ({moeda_selecionada})",
    line=dict(width=1.5),
    opacity=0.3
))

fig.add_trace(go.Scatter(
    x=df_filtrado["timestamp"],
    y=df_filtrado["media_movel"],
    mode="lines",
    name="Média Móvel (7 dias)",
    line=dict(color="white", width=2, dash="dot")
))

fig.update_layout(
    title=f"Evolução do preço - {moeda_selecionada.upper()} (últimos {dias} dias)",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FFFFFF"),
    xaxis_title="Data",
    yaxis_title="Preço (USD)",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# MÉTRICAS
if len(df_filtrado) >= 2:
    preco_atual = df_filtrado["preco"].iloc[-1]
    preco_antigo = df_filtrado["preco"].iloc[0]
    variacao = ((preco_atual - preco_antigo) / preco_antigo) * 100
else:
    preco_atual = preco_antigo = variacao = None

col1, col2, col3 = st.columns(3)
col1.metric("💰 Preço Atual (USD)", f"${preco_atual:,.2f}" if preco_atual else "N/A")
col2.metric("📉 Preço no Início do Período", f"${preco_antigo:,.2f}" if preco_antigo else "N/A")
col3.metric("📈 Variação (%)", f"{variacao:.2f}%" if variacao else "N/A")


# GRÁFICOS ADICIONAIS

st.subheader("📊 Outros Indicadores")
col_a, col_b = st.columns(2)

with col_a:
    st.area_chart(df_filtrado.set_index("timestamp")["market_cap"])

with col_b:
    st.bar_chart(df_filtrado.set_index("timestamp")["volume_24h"])

# Tabela
st.subheader("📄 Dados recentes")
st.dataframe(df_filtrado)

st.caption("Desenvolvido para o TCC - Plataforma educativa de análise de criptomoedas.")
