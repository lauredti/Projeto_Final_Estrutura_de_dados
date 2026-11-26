import sqlite3
from datetime import datetime

DB_NAME = "clinica_medica.db"


def conectar():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Especialidade (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            sigla TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'ATIVA' CHECK(status IN ('ATIVA', 'INATIVA'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK(perfil IN ('ADM', 'ESPECIALISTA'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Profissional_Consultorio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            nome_especialista TEXT NOT NULL,
            numero_consultorio TEXT UNIQUE NOT NULL,
            especialidade_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (especialidade_id) REFERENCES Especialidade(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Senha (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            categoria_prioridade TEXT NOT NULL,
            nivel_prioridade INTEGER NOT NULL,
            especialidade_id INTEGER NOT NULL,
            status TEXT DEFAULT 'AGUARDANDO',
            consultorio_destino TEXT,
            FOREIGN KEY (especialidade_id) REFERENCES Especialidade(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Historico_Atendimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            senha_codigo TEXT NOT NULL,
            especialidade_nome TEXT NOT NULL,
            categoria_prioridade TEXT NOT NULL,
            consultorio TEXT,
            horario_emissao TEXT NOT NULL,
            horario_chamada TEXT,
            horario_inicio TEXT,
            horario_fim TEXT,
            status_final TEXT DEFAULT 'AGUARDANDO'
        )
    """)

    especialidades_iniciais = [
        ("Clínica Geral", "CG"),
        ("Cardiologia", "CA"),
        ("Ortopedia", "OR")
    ]
    for nome, sigla in especialidades_iniciais:
        cursor.execute(
            "INSERT OR IGNORE INTO Especialidade (nome, sigla, status) VALUES (?, ?, 'ATIVA')",
            (nome, sigla)
        )

    cursor.execute(
        "INSERT OR IGNORE INTO Usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
        ("Administrador Padrão", "admin", "123", "ADM")
    )

    conn.commit()
    conn.close()


def agora():
    return datetime.now().strftime("%H:%M:%S")