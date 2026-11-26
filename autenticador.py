import sqlite3
from banco_dados import conectar

LIMITE_ESPECIALISTAS_POR_ESP = 3


def autenticar_usuario(usuario, senha, perfil_esperado):
    if not usuario.strip() or not senha.strip():
        raise ValueError("Preencha usuário e senha.")

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT * FROM Usuarios WHERE usuario = ? AND senha = ? AND perfil = ?",
        (usuario.strip(), senha.strip(), perfil_esperado)
    )
    registro_usuario = cursor.fetchone()

    if not registro_usuario:
        conexao.close()
        raise PermissionError("Credenciais inválidas ou perfil incorreto.")

    dados = dict(registro_usuario)

    if perfil_esperado == "ESPECIALISTA":
        cursor.execute("""
            SELECT pc.*, e.nome as especialidade_nome, e.status as especialidade_status
            FROM Profissional_Consultorio pc
            JOIN Especialidade e ON pc.especialidade_id = e.id
            WHERE pc.usuario_id = ?
        """, (registro_usuario["id"],))
        registro_profissional = cursor.fetchone()
        if not registro_profissional:
            conexao.close()
            raise PermissionError("Especialista sem consultório vinculado.")
        dados["profissional"] = dict(registro_profissional)

    conexao.close()
    return dados


def cadastrar_especialista(nome, usuario, senha, numero_consultorio, especialidade_id):
    if not all([nome.strip(), usuario.strip(), senha.strip(), numero_consultorio.strip()]):
        raise ValueError("Todos os campos são obrigatórios.")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT COUNT(*) as total FROM Profissional_Consultorio WHERE especialidade_id = ?",
        (especialidade_id,)
    )
    total = cursor.fetchone()["total"]
    if total >= LIMITE_ESPECIALISTAS_POR_ESP:
        conexao.close()
        raise ValueError(f"Limite atingido: máximo de {LIMITE_ESPECIALISTAS_POR_ESP} especialistas nesta especialidade.")

    try:
        cursor.execute(
            "INSERT INTO Usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, 'ESPECIALISTA')",
            (nome.strip(), usuario.strip(), senha.strip())
        )
        usuario_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Profissional_Consultorio (usuario_id, nome_especialista, numero_consultorio, especialidade_id)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, nome.strip(), numero_consultorio.strip(), especialidade_id))

        conexao.commit()
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        conexao.close()
        if "numero_consultorio" in str(erro):
            raise ValueError("Este consultório já está ocupado por outro especialista.")
        raise ValueError("Nome de usuário já está em uso.")

    conexao.close()


def atualizar_consultorio_especialista(profissional_id, novo_consultorio):
    if not novo_consultorio.strip():
        raise ValueError("Informe o número ou nome do consultório.")

    conexao = conectar()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "UPDATE Profissional_Consultorio SET numero_consultorio = ? WHERE id = ?",
            (novo_consultorio.strip(), profissional_id)
        )
        conexao.commit()
    except sqlite3.IntegrityError:
        conexao.close()
        raise ValueError("Este consultório já está vinculado a outro profissional.")
    conexao.close()


def remover_especialista(profissional_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT usuario_id FROM Profissional_Consultorio WHERE id = ?", (profissional_id,))
    linha = cursor.fetchone()
    if linha:
        cursor.execute("DELETE FROM Profissional_Consultorio WHERE id = ?", (profissional_id,))
        if linha["usuario_id"]:
            cursor.execute("DELETE FROM Usuarios WHERE id = ?", (linha["usuario_id"],))
    conexao.commit()
    conexao.close()


def cadastrar_adm(nome, usuario, senha):
    if not all([nome.strip(), usuario.strip(), senha.strip()]):
        raise ValueError("Todos os campos são obrigatórios.")

    conexao = conectar()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "INSERT INTO Usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, 'ADM')",
            (nome.strip(), usuario.strip(), senha.strip())
        )
        conexao.commit()
    except sqlite3.IntegrityError:
        conexao.close()
        raise ValueError("Nome de usuário já está em uso.")
    conexao.close()


def cadastrar_especialidade(nome, sigla):
    if not nome.strip() or not sigla.strip():
        raise ValueError("Informe o nome e a sigla da especialidade.")

    conexao = conectar()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "INSERT INTO Especialidade (nome, sigla, status) VALUES (?, ?, 'ATIVA')",
            (nome.strip(), sigla.strip().upper())
        )
        conexao.commit()
    except sqlite3.IntegrityError:
        conexao.close()
        raise ValueError("Especialidade ou sigla já cadastrada.")
    conexao.close()


def alternar_status_especialidade(especialidade_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT status FROM Especialidade WHERE id = ?", (especialidade_id,))
    especialidade = cursor.fetchone()
    if not especialidade:
        conexao.close()
        raise ValueError("Especialidade não encontrada.")

    if especialidade["status"] == "ATIVA":
        cursor.execute(
            "SELECT COUNT(*) as qtd FROM Senha WHERE especialidade_id = ? AND status = 'AGUARDANDO'",
            (especialidade_id,)
        )
        if cursor.fetchone()["qtd"] > 0:
            conexao.close()
            raise ValueError("Não é possível desativar uma especialidade com pacientes aguardando na fila.")
        novo_status = "INATIVA"
    else:
        novo_status = "ATIVA"

    cursor.execute("UPDATE Especialidade SET status = ? WHERE id = ?", (novo_status, especialidade_id))
    conexao.commit()
    conexao.close()
    return novo_status


def listar_especialidades(apenas_ativas=True):
    conexao = conectar()
    cursor = conexao.cursor()
    if apenas_ativas:
        cursor.execute("SELECT * FROM Especialidade WHERE status = 'ATIVA' ORDER BY id")
    else:
        cursor.execute("SELECT * FROM Especialidade ORDER BY id")
    linhas = [dict(registro) for registro in cursor.fetchall()]
    conexao.close()
    return linhas


def listar_profissionais():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT pc.id, pc.nome_especialista, pc.numero_consultorio, e.nome as especialidade_nome
        FROM Profissional_Consultorio pc
        JOIN Especialidade e ON pc.especialidade_id = e.id
        ORDER BY e.nome, pc.numero_consultorio
    """)
    linhas = [dict(registro) for registro in cursor.fetchall()]
    conexao.close()
    return linhas


def listar_historico():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM Historico_Atendimento ORDER BY id DESC LIMIT 30")
    linhas = [dict(registro) for registro in cursor.fetchall()]
    conexao.close()
    return linhas