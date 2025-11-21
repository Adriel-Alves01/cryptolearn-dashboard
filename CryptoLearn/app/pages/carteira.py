import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date
from io import BytesIO


# Configurações iniciais

st.set_page_config(page_title="CryptoLearn - Carteira Virtual", layout="wide")

# Caminho absoluto para raiz do app
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # volta para /app
DB_PATH = os.path.join(ROOT_DIR, "db", "cripto.db")


# Helpers de BD

def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def carregar_dados_cripto():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM cripto_dados ORDER BY timestamp ASC", conn)
    conn.close()
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["nome"] = df["nome"].astype(str)
    return df

def salvar_transacao(moeda, quantidade, data, preco):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO carteira (moeda, quantidade, data_compra, preco_compra)
        VALUES (?, ?, ?, ?)
    """, (moeda, float(quantidade), data, float(preco)))
    conn.commit()
    conn.close()

def carregar_carteira():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM carteira ORDER BY id ASC", conn)
    conn.close()
    return df

def deletar_transacao(trans_id):
    conn = conectar()
    cur = conn.cursor()
    
    # Deleta a transação
    cur.execute("DELETE FROM carteira WHERE id = ?", (trans_id,))
    conn.commit()

    # Verifica se a tabela ficou vazia
    cur.execute("SELECT COUNT(*) FROM carteira")
    total = cur.fetchone()[0]

    # Se a tabela estiver vazia, resetar autoincremento
    if total == 0:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='carteira'")
        conn.commit()

    conn.close()


# Funções utilitárias

def preco_por_data(df_cripto, moeda, data):
    series = df_cripto[df_cripto["nome"] == moeda].copy()
    if series.empty:
        return None
    series["date_only"] = series["timestamp"].dt.date
    exact = series[series["date_only"] == data]
    if not exact.empty:
        return float(exact["preco"].iloc[0])
    before = series[series["date_only"] <= data]
    if not before.empty:
        return float(before.iloc[-1]["preco"])
    return float(series["preco"].iloc[0])

def series_preco_por_moeda(df_cripto, moeda):
    s = df_cripto[df_cripto["nome"] == moeda].copy()
    if s.empty:
        return pd.Series(dtype=float)
    s = s.set_index(s["timestamp"].dt.date)["preco"].sort_index()
    s = s[~s.index.duplicated(keep='first')]
    s = s.asfreq(pd.infer_freq(pd.Index(s.index)) if len(s) > 1 else 'D', method=None)
    s = s.ffill().bfill()
    return s

def gerar_evolucao_carteira(df_cripto, df_carteira):
    if df_carteira.empty:
        return pd.DataFrame()
    df_cripto["date_only"] = df_cripto["timestamp"].dt.date
    min_date = min(pd.to_datetime(df_carteira["data_compra"]).dt.date.min(), df_cripto["date_only"].min())
    max_date = df_cripto["date_only"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D").date
    resultados = []
    for d in all_dates:
        total = 0.0
        for _, trans in df_carteira.iterrows():
            moeda = trans["moeda"]
            qtd = float(trans["quantidade"])
            data_compra = pd.to_datetime(trans["data_compra"]).date()
            if d >= data_compra:
                preco_on_date = preco_por_data(df_cripto, moeda, d)
                if preco_on_date is None:
                    preco_on_date = 0.0
                total += qtd * preco_on_date
        resultados.append({"date": d, "valor_total": total})
    df_evo = pd.DataFrame(resultados)
    df_evo["date"] = pd.to_datetime(df_evo["date"])
    return df_evo


# Layout / Menu lateral

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Ir para:", ["Registrar Compra", "Transações", "Evolução da Carteira", "Relatórios", "Alertas"])


# Carrega dados

df_cripto = carregar_dados_cripto()
if df_cripto is None:
    df_cripto = pd.DataFrame()

if df_cripto.empty:
    st.error("Nenhum dado de criptomoeda encontrado. Execute o coleta.py primeiro para popular o banco.")
    st.stop()

moedas = df_cripto["nome"].unique().tolist()


# Página: Registrar Compra (Simulação por valor em USD) 

if pagina == "Registrar Compra":
    st.title("🪙 Simulação de Compra por Valor (USD)")
    col1, col2, col3 = st.columns(3)

    # moeda
    with col1:
        moeda = st.selectbox("Moeda", moedas)

    # inicializa estado
    if "valor_usd" not in st.session_state:
        st.session_state.valor_usd = 0.0

    if "valor_text" not in st.session_state:
        st.session_state.valor_text = "0"

    # callback do input
    def _on_change_text():
        txt = st.session_state.valor_text.replace(" ", "").replace(".", "").replace(",", ".")
        try:
            st.session_state.valor_usd = float(txt)
        except:
            pass

    with col2:
        st.write("Valor a investir (USD):")

        b1, b2, b3 = st.columns(3)
        if b1.button("+10"):
            st.session_state.valor_usd += 10
            st.session_state.valor_text = f"{st.session_state.valor_usd:.2f}"

        if b2.button("+50"):
            st.session_state.valor_usd += 50
            st.session_state.valor_text = f"{st.session_state.valor_usd:.2f}"

        if b3.button("+100"):
            st.session_state.valor_usd += 100
            st.session_state.valor_text = f"{st.session_state.valor_usd:.2f}"

        st.text_input(
            "Digite o valor (aceita ponto ou vírgula):",
            key="valor_text",
            on_change=_on_change_text
        )

        st.info(f"Valor selecionado: ${st.session_state.valor_usd:,.2f}")

    with col3:
        data_compra = st.date_input("Data da compra", value=date.today())

    preco_no_dia = preco_por_data(df_cripto, moeda, data_compra)
    quantidade = (st.session_state.valor_usd / preco_no_dia) if preco_no_dia else 0
    st.success(f"Você está comprando aproximadamente {quantidade:.8f} {moeda}")

    if st.button("Registrar compra", key="registrar_compra"):
        if preco_no_dia is None:
            st.error("Não há preço disponível nessa data.")
        elif st.session_state.valor_usd <= 0:
            st.error("Digite um valor maior que 0.")
        else:
            salvar_transacao(moeda, quantidade, data_compra.isoformat(), preco_no_dia)
            st.success("Compra registrada com sucesso!")

            # marca para reset da próxima execução
            st.session_state.valor_usd = 0.0
            st.session_state.resetar_valor = True

            st.rerun()
# -----------------------
# Página: Transações

elif pagina == "Transações":
    st.title("📄 Histórico de Transações")

    df_carteira = carregar_carteira()

    if df_carteira.empty:
        st.info("Nenhuma transação registrada ainda.")
    else:
        st.subheader("🧾 Transações Registradas")

        
        df_formatado = df_carteira.rename(columns={
            "id": "ID",
            "moeda": "Moeda",
            "quantidade": "Quantidade",
            "data_compra": "Data",
            "preco_compra": "Preço da Moeda"
        })

        # Remover coluna de índice vazio se existir
        df_formatado = df_formatado.loc[:, ~df_formatado.columns.str.contains('^Unnamed')]

        # Formatar quantidade e preço
        df_formatado["Quantidade"] = df_formatado["Quantidade"].astype(float).round(8)
        df_formatado["Preço da Moeda"] = df_formatado["Preço da Moeda"].astype(float).round(4)

        # tabela formatada
        st.dataframe(df_formatado, use_container_width=True)

        st.markdown("---")

        # ======== Excluir transação =========
        st.subheader("Excluir transação")

        ids = df_carteira["id"].tolist()
        escolha = st.selectbox("Selecione o ID da transação a ser excluída:", ids)

        if st.button("Excluir transação selecionada", key="btn_excluir_trans"):
            deletar_transacao(int(escolha))
            st.success("Transação excluída com sucesso!")
            st.rerun()
elif pagina == "Evolução da Carteira":
    st.title("📈 Evolução da Carteira")

    df_carteira = carregar_carteira()

    if df_carteira.empty:
        st.info("Nenhuma transação registrada ainda.")
        st.stop()

    
    # MÉTRICAS GERAIS
   
    df_carteira["investido"] = df_carteira["quantidade"] * df_carteira["preco_compra"]
    valor_investido = df_carteira["investido"].sum()

    # valor atual por moeda
    valor_atual = 0
    for _, row in df_carteira.iterrows():
        moeda = row["moeda"]
        qtd = float(row["quantidade"])
        preco_atual = float(df_cripto[df_cripto["nome"] == moeda]["preco"].iloc[-1])
        valor_atual += qtd * preco_atual

    retorno = valor_atual - valor_investido
    retorno_pct = (retorno / valor_investido) * 100 if valor_investido > 0 else 0

    colA, colB, colC = st.columns(3)
    colA.metric("💰 Valor Investido", f"${valor_investido:,.2f}")
    colB.metric("📈 Valor Atual", f"${valor_atual:,.2f}")
    colC.metric("📊 Retorno (%)", f"{retorno_pct:.2f}%")

    
    # TABELA DE TRANSACÕES
    
    st.subheader("🧾 Histórico de Transações")
    st.dataframe(
        df_carteira[["id", "moeda", "quantidade", "data_compra", "preco_compra"]],
        use_container_width=True
    )

   
    # EVOLUÇÃO INDIVIDUAL DE CADA COMPRA
   
    st.markdown("---")
    st.subheader("📈 Evolução Individual das Compras")

    df_carteira["descricao"] = df_carteira.apply(
        lambda row: f"[{row['id']}] {row['moeda'].upper()} — {row['data_compra']} — ${row['quantidade'] * row['preco_compra']:.2f}",
        axis=1
    )

    escolha = st.selectbox(
        "Selecione uma compra para visualizar a evolução:",
        df_carteira["descricao"].tolist()
    )

    trans_id = int(escolha.split("]")[0].replace("[", ""))
    trans = df_carteira[df_carteira["id"] == trans_id].iloc[0]

    moeda = trans["moeda"]
    qtd = float(trans["quantidade"])
    data_compra = pd.to_datetime(trans["data_compra"]).date()
    preco_compra = float(trans["preco_compra"])

    df_moeda = df_cripto[df_cripto["nome"] == moeda].copy()
    df_moeda["date_only"] = df_moeda["timestamp"].dt.date
    df_moeda = df_moeda[df_moeda["date_only"] >= data_compra].copy()

    if df_moeda.empty:
        st.warning("Sem dados suficientes para gerar a evolução desta compra.")
    else:
        df_moeda["valor"] = df_moeda["preco"] * qtd

        import plotly.express as px

        fig_ind = px.line(
            df_moeda,
            x="date_only",
            y="valor",
            title=f"Evolução da compra #{trans_id} — {moeda.upper()}",
            markers=True
        )

        fig_ind.update_layout(
            xaxis_title="Data",
            yaxis_title="Valor",
            title_font=dict(size=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
            template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
        )

        st.plotly_chart(fig_ind, use_container_width=True)

        preco_atual = float(df_moeda["preco"].iloc[-1])
        valor_atual = preco_atual * qtd
        valor_inv = qtd * preco_compra
        lucro = valor_atual - valor_inv
        retorno_pct = (lucro / valor_inv) * 100 if valor_inv > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Valor Investido", f"${valor_inv:,.2f}")
        col2.metric("Valor Atual", f"${valor_atual:,.2f}")
        col3.metric("Retorno (%)", f"{retorno_pct:.2f}%")

# Página: Relatórios (Resumo da Carteira)

elif pagina == "Relatórios":
    st.title(" Relatórios da Carteira")

    df_carteira = carregar_carteira()

    if df_carteira.empty:
        st.info("Nenhuma transação para gerar relatório.")
        st.stop()

    
    # 1) Cálculo dos dados
    
    resultados = []
    for _, row in df_carteira.iterrows():
        moeda = row["moeda"]
        qtd = float(row["quantidade"])
        preco_compra = float(row["preco_compra"])

        df_mo = df_cripto[df_cripto["nome"] == moeda]
        preco_atual = float(df_mo["preco"].iloc[-1])

        investido = qtd * preco_compra
        atual = qtd * preco_atual
        lucro = atual - investido
        variacao = (lucro / investido) * 100 if investido > 0 else 0

        resultados.append({
            "id": int(row["id"]),
            "moeda": moeda,
            "quantidade": qtd,
            "preco_compra": preco_compra,
            "preco_atual": preco_atual,
            "investido": investido,
            "atual": atual,
            "lucro": lucro,
            "variacao_pct": variacao
        })

    df_result = pd.DataFrame(resultados)

  
    # 2) Resumo geral
   
    st.markdown("## Resumo Geral da Carteira:")

    valor_investido = df_result["investido"].sum()
    valor_atual = df_result["atual"].sum()
    lucro_total = valor_atual - valor_investido
    retorno_pct = (lucro_total / valor_investido * 100) if valor_investido > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Investido", f"${valor_investido:,.2f}")
    col2.metric("Valor Atual", f"${valor_atual:,.2f}")
    col3.metric("Lucro/Prejuízo", f"${lucro_total:,.2f}")
    col4.metric("Retorno (%)", f"{retorno_pct:.2f}%")

    st.markdown("---")

    
    # 3) Gráfico de Pizza: Distribuição da carteira
    
    st.markdown(" ## Distribuição da Carteira por Moeda:")
    df_pizza = df_result.groupby("moeda")["atual"].sum().reset_index()

    import plotly.express as px
    fig_pizza = px.pie(df_pizza, names="moeda", values="atual", title="Distribuição Atual por Moeda")
    st.plotly_chart(fig_pizza, use_container_width=True)

    st.markdown("---")

  
    # 4) Tabela por moeda (detalhada)

    st.markdown("## 📄 Desempenho por Moeda")
    df_exibir = df_result.copy()

    df_exibir.rename(columns={
        "id": "ID",
        "moeda": "Moeda",
        "quantidade": "Quantidade",
        "preco_compra": "Preço Compra",
        "preco_atual": "Preço Atual",
        "investido": "Total Investido",
        "atual": "Valor Atual",
        "lucro": "Lucro",
        "variacao_pct": "Variação (%)"
    }, inplace=True)

    st.dataframe(df_exibir, use_container_width=True)

    st.markdown("---")

    
    # 5) Lista de transações
   
    st.markdown("## 🧾 Histórico Completo de Transações")

    df_hist = df_carteira.copy()
    df_hist.rename(columns={
        "id": "ID",
        "moeda": "Moeda",
        "quantidade": "Quantidade",
        "data_compra": "Data",
        "preco_compra": "Preço Compra"
    }, inplace=True)

    st.dataframe(df_hist, use_container_width=True)

    st.markdown("---")

   
    # 6) Download CSV
  
    st.subheader("📥 Exportar CSV")
    csv_bytes = df_result.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        data=csv_bytes,
        file_name="relatorio_carteira.csv",
        mime="text/csv"
    )

   
    # 7) Exportação em PDF
   
    st.subheader("📄 Gerar PDF resumo")

    pdf_name = f"relatorio_carteira_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 1*inch, "Relatório - Carteira Virtual - CryptoLearn")

        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 1.3*inch, f"Gerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(1*inch, height - 1.6*inch, f"Total Investido: ${valor_investido:,.2f}")
        c.drawString(1*inch, height - 1.8*inch, f"Valor Atual: ${valor_atual:,.2f}")
        c.drawString(1*inch, height - 2.0*inch, f"Retorno: {retorno_pct:.2f}%")

        y = height - 2.5*inch
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1*inch, y, "ID | Moeda | Quantidade | Compra | Atual | Lucro")
        y -= 0.2*inch
        c.setFont("Helvetica", 9)

        for _, r in df_result.iterrows():
            if y < 1*inch:
                c.showPage()
                y = height - 1*inch

            linha = (
                f"{int(r['id'])} | {r['moeda']} | "
                f"{r['quantidade']:.6f} | "
                f"${r['preco_compra']:.2f} | "
                f"${r['preco_atual']:.2f} | "
                f"${r['lucro']:.2f}"
            )
            c.drawString(1*inch, y, linha)
            y -= 0.18*inch

        c.save()
        buffer.seek(0)

        st.download_button(
            "Download PDF",
            data=buffer,
            file_name=pdf_name,
            mime="application/pdf"
        )

    except Exception as e:
        st.error("Não foi possível gerar PDF. Verifique se reportlab está instalado.")
        st.info("Você pode instalar com: pip install reportlab")

# Página: Alertas

elif pagina == "Alertas":
    st.title("🔔 Alertas Educativos")
    st.write("Configure o limiar de variação (%) para ser notificado sobre movimentos bruscos.")
    limiar = st.slider("Limiar de variação (%)", 1, 50, 5)
    ultimos = []
    for moeda in moedas:
        df_m = df_cripto[df_cripto["nome"] == moeda].copy()
        if df_m.shape[0] < 2:
            continue
        preco_atual = df_m["preco"].iloc[-1]
        prev = df_m[df_m["timestamp"] < df_m["timestamp"].iloc[-1]]
        if prev.empty:
            continue
        preco_anterior = prev["preco"].iloc[-1]
        var_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        ultimos.append({"moeda": moeda, "var_pct": var_pct, "preco_atual": preco_atual})
    if not ultimos:
        st.info("Dados insuficientes para gerar alertas.")
    else:
        for item in ultimos:
            nome = item["moeda"]
            var_pct = item["var_pct"]
            preco_atual = item["preco_atual"]
            if abs(var_pct) >= limiar:
                if var_pct > 0:
                    st.success(f"{nome}: alta de {var_pct:.2f}% (preço atual ${preco_atual:.2f})")
                    st.info("Interpretação: movimento relevante de alta. Considere fatores como notícias, adoção ou movimentos de grandes carteiras.")
                else:
                    st.warning(f"{nome}: queda de {var_pct:.2f}% (preço atual ${preco_atual:.2f})")
                    st.info("Interpretação: movimento relevante de queda. Verifique liquidez, notícias e risco de mercado.")
        st.markdown("---")
        st.write("Os alertas acima são educativos: não representam recomendação financeira. Eles servem para demonstrar como variações significativas podem ocorrer e como interpreta-las de maneira prática.")
