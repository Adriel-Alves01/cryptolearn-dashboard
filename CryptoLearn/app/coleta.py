import requests
import pandas as pd
from datetime import datetime, timedelta
from utils.db_utils import conectar, inicializar_banco

# Inicializa o banco e tabela
inicializar_banco()

MOEDAS = ["bitcoin", "ethereum"]
VS_CURRENCY = "usd"


# FUNÇÃO: salvar no banco 
def salvar_no_banco(dados):
    conn = conectar()
    cursor = conn.cursor()

    for dado in dados:
        cursor.execute("""
            INSERT INTO cripto_dados (timestamp, nome, preco, market_cap, volume_24h, variacao_24h)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            dado["timestamp"],
            dado["nome"],
            dado["preco"],
            dado["market_cap"],
            dado["volume_24h"],
            dado["variacao_24h"]
        ))
    conn.commit()
    conn.close()


# FUNÇÃO: coletar dados atuais 
def coletar_dados_atuais():
    """Coleta os dados mais recentes das moedas e salva no banco."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": VS_CURRENCY, 
              "ids": ",".join(MOEDAS),
              "interval": "daily" }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        registros = []

        for moeda in data:
            registros.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "nome": moeda["name"],
                "preco": moeda["current_price"],
                "market_cap": moeda["market_cap"],
                "volume_24h": moeda["total_volume"],
                "variacao_24h": moeda["price_change_percentage_24h"]
            })

        salvar_no_banco(registros)
        print(f"✅ Coleta feita às {datetime.now().strftime('%H:%M:%S')}")
    else:
        print(f"❌ Erro ao acessar API (atuais): {response.status_code}")


# coletar histórico (últimos 12 meses) 
def coletar_historico():
    """Coleta dados diários dos últimos 12 meses (365 dias) para cada moeda."""
    registros = []

    for moeda in MOEDAS:
        print(f"📊 Coletando histórico de {moeda.capitalize()} (últimos 12 meses)...")
        url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart"
        params = {"vs_currency": VS_CURRENCY, "days": "365"}  

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for preco, market_cap, volume in zip(data["prices"], data["market_caps"], data["total_volumes"]):
                ts = datetime.fromtimestamp(preco[0] / 1000)
                registros.append({
                    "timestamp": ts.strftime("%Y-%m-%d"),
                    "nome": moeda,
                    "preco": preco[1],
                    "market_cap": market_cap[1],
                    "volume_24h": volume[1],
                    "variacao_24h": None
                })
        else:
            print(f"❌ Erro ao coletar histórico de {moeda}: {response.status_code}")

    salvar_no_banco(registros)
    print("✅ Histórico dos últimos 12 meses salvo com sucesso!")

def atualizar_tudo():
    coletar_historico()      # últimos 365 dias
    coletar_dados_atuais()   # dados atuais
    
# PROGRAMA PRINCIPAL 
if __name__ == "__main__":
    coletar_historico()     # Executa uma vez 
    coletar_dados_atuais()  # Coleta dados atuais uma vez


