import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os


#Configuração da página
st.set_page_config(page_title="CryptoLearn - Dashboard", layout="wide")


#  Caminho fixo para o banco dentro de app/db/

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "db", "cripto.db")

st.sidebar.info(f"📁 Banco usado: `{DB_PATH}`")


#  Conexão e leitura do banco

if not os.path.exists(DB_PATH):
    st.error("❌ Banco de dados não encontrado. Execute o coleta.py primeiro.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM cripto_dados ORDER BY timestamp ASC", conn)
conn.close()


#  Estrutura principal
st.title("📊 Dashboard de Criptomoedas - CryptoLearn")

if df.empty:
    st.warning("Nenhum dado encontrado no banco de dados. Execute o coleta.py primeiro.")
else:
   
    # 🕒 Tratamento de tempo
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    
    # Filtros laterais
  
    moedas = df["nome"].unique()
    moeda_selecionada = st.sidebar.selectbox("Escolha a moeda", moedas)
    dias = st.sidebar.slider("Quantidade de dias para exibir", 30, 365, 365)

    df_filtrado = df[df["nome"] == moeda_selecionada].copy()
    hoje = df_filtrado["timestamp"].max()
    data_limite = hoje - pd.Timedelta(days=dias)
    df_filtrado = df_filtrado[df_filtrado["timestamp"] >= data_limite]

    
    # Gráfico principal - com gradiente e média móvel
   
    min_price = df_filtrado["preco"].min()
    max_price = df_filtrado["preco"].max()
    df_filtrado["media_movel"] = df_filtrado["preco"].rolling(window=7).mean()

    # Cria figura manualmente (para controle total)
    fig = go.Figure()

    # Linha principal colorida dinamicamente (gradiente visualizado via cor da linha)
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

    # Adiciona linha da média móvel
    fig.add_trace(go.Scatter(
        x=df_filtrado["timestamp"],
        y=df_filtrado["media_movel"],
        mode="lines",
        name="Média Móvel (7 dias)",
        line=dict(color="white", width=2, dash="dot")
    ))

    # Picos (brilho suave)
    pico_max = df_filtrado.loc[df_filtrado["preco"].idxmax()]
    pico_min = df_filtrado.loc[df_filtrado["preco"].idxmin()]

    fig.add_trace(go.Scatter(
        x=[pico_max["timestamp"]],
        y=[pico_max["preco"]],
        mode="markers",
        marker=dict(size=18, color="green", opacity=0.4),
        name="Pico Máximo"
    ))
    fig.add_trace(go.Scatter(
        x=[pico_min["timestamp"]],
        y=[pico_min["preco"]],
        mode="markers",
        marker=dict(size=18, color="red", opacity=0.4),
        name="Pico Mínimo"
    ))

    # Layout visual
    fig.update_layout(
        title=f"Evolução do preço - {moeda_selecionada.upper()} (últimos {dias} dias)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF"),
        xaxis_title="Data",
        yaxis_title="Preço (USD)",
        hovermode="x unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0)
    )

    st.plotly_chart(fig, use_container_width=True)

   
    # Métricas principais
  
    if len(df_filtrado) >= 2:
        preco_atual = df_filtrado["preco"].iloc[-1]
        preco_antigo = df_filtrado["preco"].iloc[0]
        variacao = ((preco_atual - preco_antigo) / preco_antigo) * 100
    else:
        preco_atual = preco_antigo = variacao = None

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Preço Atual (USD)", f"${preco_atual:,.2f}" if preco_atual else "N/A")
    col2.metric("📉 Preço Anterior", f"${preco_antigo:,.2f}" if preco_antigo else "N/A")
    col3.metric("📈 Variação (%)", f"{variacao:.2f}%" if variacao else "N/A")

    
    # Gráficos adicionais
 
    st.subheader("📊 Outros Indicadores")
    col_a, col_b = st.columns(2)

    with col_a:
        if "market_cap" in df_filtrado.columns:
            st.area_chart(df_filtrado.set_index("timestamp")["market_cap"], use_container_width=True)
        else:
            st.info("Market cap não disponível na tabela.")

    with col_b:
        if "volume_24h" in df_filtrado.columns:
            st.bar_chart(df_filtrado.set_index("timestamp")["volume_24h"], use_container_width=True)
        else:
            st.info("Volume 24h não disponível na tabela.")

    
    # Tabela de dados recentes
   
    st.subheader("📄 Dados recentes")
    st.dataframe(df_filtrado)

    st.caption("Desenvolvido para o TCC - Plataforma educativa de análise de criptomoedas.")