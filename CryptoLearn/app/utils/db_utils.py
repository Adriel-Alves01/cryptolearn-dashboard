import sqlite3
import os

# Caminho do banco (dentro da pasta /app/db)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'cripto.db')

# Função para conectar ao banco
def conectar():
    return sqlite3.connect(DB_PATH)

# Função para criar a tabela caso não exista
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cripto_dados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            nome TEXT NOT NULL,
            preco REAL,
            market_cap REAL,
            volume_24h REAL,
            variacao_24h REAL
        )
    ''')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carteira (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        moeda TEXT NOT NULL,
        quantidade REAL NOT NULL,
        data_compra TEXT NOT NULL,
        preco_compra REAL NOT NULL
    )
""")

    conn.commit()
    conn.close()
    print("✅ Banco e tabela inicializados com sucesso!")