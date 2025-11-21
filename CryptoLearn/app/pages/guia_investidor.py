import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# GUIA DO INVESTIDOR INICIANTE


st.title("📘 Guia do Investidor Iniciante")
st.write("Uma introdução simples, objetiva e totalmente educativa para aprender os conceitos fundamentais de criptomoedas e análise de carteira.")

st.markdown("---")
st.header(" 1. O que é Volatilidade?")
st.write("""
Volatilidade é o quanto o preço de um ativo oscila ao longo do tempo.  
Quanto mais rápido ele sobe e desce, **mais volátil** ele é.

- Criptomoedas → **alta volatilidade**
- Tesouro Direto → **baixa volatilidade**

Quanto maior a volatilidade, maior o risco — mas também maior o potencial de retorno.
""")

# Gráfico demonstrativo de volatilidade
dias = pd.date_range("2023-01-01", periods=60)
volatil_baixa = np.random.normal(0, 1, 60).cumsum() + 100
volatil_alta = np.random.normal(0, 5, 60).cumsum() + 100

df_vol = pd.DataFrame({
    "Data": dias,
    "Baixa Volatilidade": volatil_baixa,
    "Alta Volatilidade": volatil_alta
})

fig_vol = px.line(df_vol, x="Data", y=["Baixa Volatilidade", "Alta Volatilidade"],
                  title="Exemplo de Volatilidade Alta vs Baixa")
st.plotly_chart(fig_vol, use_container_width=True)

st.markdown("---")
st.header(" 3. O que é ROI? (Retorno %) ")

st.write("""
O **ROI (Retorno Sobre o Investimento)** é uma medida usada para entender se um investimento
**deu lucro ou prejuízo**. Ele compara o valor que você colocou no início com o valor que ele vale agora.

O ROI serve para responder perguntas como:

- Meu investimento vale mais ou menos do que quando comprei?
- Esse investimento está indo bem?
- Qual das moedas da minha carteira teve o melhor desempenho?
- Valeu a pena investir nesse ativo em vez de outro?

Ele não prevê o futuro — apenas mostra o **resultado acumulado até agora**.
""")

st.write("""
### Como interpretar o ROI?
- **ROI positivo** →  teve lucro.  
- **ROI negativo** →  teve prejuízo.  
- **ROI zero** →  está empatado.

O ROI permite comparar investimentos diferentes.  
Por exemplo:  
um ativo que rendeu 20% é melhor (percentualmente) do que outro que rendeu 5%, mesmo que o valor investido tenha sido menor.

É por isso que o ROI é tão usado em carteiras, fundos e relatórios.
""")

# -------------------------------------------------------------------------

st.markdown("---")
st.header(" 4. Como Ler um Gráfico de Criptomoeda")

st.write("""
Muitas pessoas olham gráficos e acham que tem que "advinhar", mas na verdade os gráficos mostram
**o comportamento do preço ao longo do tempo**. Interpretá-los ajuda a entender:

- se o preço está subindo ou caindo
- se está estável
- se teve movimentos bruscos
- se está se recuperando depois de uma queda
- se está próximo de preços importantes do passado

Você não precisa ser analista profissional para interpretar o básico.
""")

st.write("""
###  Pontos principais que um iniciante deve observar:
- **Tendência**: Se o preço está subindo, descendo ou andando de lado.  
- **Picos e quedas**: Mudanças bruscas que podem indicar volatilidade alta.  
- **Regiões repetidas**: Quando o preço frequentemente “para” em um certo nível.
""")

# -------------------------------------------------------------------------

st.markdown("---")
st.header(" 5. Tendências: Como entender para tomar decisões melhores")

st.write("""
A “tendência” é o comportamento geral do preço.

Mesmo que o gráfico tenha pequenos movimentos para cima e para baixo, a tendência mostra a direção predominante.
""")

st.write("""
###  Tendência de Alta
- O preço sobe ao longo do tempo.  
- Mesmo com pequenas quedas, os picos continuam ficando mais altos.  
- Indica momento favorável.

### Tendência de Baixa
- O preço cai ao longo do tempo.  
- Os topos ficam cada vez mais baixos.  
- Indica momento de maior risco.

###  Tendência Lateral
- O preço fica preso entre duas faixas.  
- Mercado indeciso, sem direção clara.  
""")

# -------------------------------------------------------------------------

st.markdown("---")
st.header(" 6. Boas Práticas Essenciais para Investidores Iniciantes")

st.write("""
Investir em criptomoedas envolve risco, mas você pode reduzir muito esses riscos seguindo
algumas práticas recomendadas por especialistas:
""")

st.write("""
###  -Invista apenas o que não compromete sua vida financeira  
Criptos são voláteis. É normal ver oscilações de 5% a 15% em um dia.

###  -Não tome decisões impulsivas  
Notícias, redes sociais e “gurus” influenciam muito. Analise bem antes.

###  -Faça aportes regulares  
Comprar aos poucos reduz o impacto das grandes variações — técnica chamada de DCA.

###  -Tenha objetivos claros  
Investir sem objetivo aumenta o risco de vender no pior momento.

###  -Registre suas operações  
Isso te ajuda a aprender com erros e acertos. """)
          



# -------------------------------------------------------------------------

st.markdown("---")
st.header(" 7. Principais Riscos ao Investir em Cripto")

st.write("""
Mesmo sendo uma tecnologia promissora, criptomoedas possuem riscos importantes:

- **Alta volatilidade**: preços podem subir ou cair rapidamente.  
- **Influência de notícias**: eventos mundiais, falas de empresas e governos afetam o preço.  
- **Ataques hacker e golpes**: muito comuns no universo cripto.  
- **Perda de chaves privadas**: perda de acesso irreversível.  
- **Liquidez baixa em moedas menores**: pode ser difícil vender.

Entender esses riscos torna o investidor mais preparado e consciente.
""")

