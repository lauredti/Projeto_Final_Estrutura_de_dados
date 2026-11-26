import sqlite3
from banco_dados import conectar

# Regra de negócio: define o máximo de especialistas permitidos por especialidade
LIMITE_ESPECIALISTAS_POR_ESP = 3


def autenticar_usuario(usuario, senha, perfil_esperado):
    """Autentica um usuário pelo perfil esperado e retorna seus dados (e do consultório, se especialista)."""
    # Impede login com campos vazios ou contendo apenas espaços
    if not usuario.strip() or not senha.strip():
        raise ValueError("Preencha usuário e senha.")

    conexao = conectar()
    cursor = conexao.cursor()

    # Busca o usuário usando parâmetros (?) para prevenir SQL Injection
    cursor.execute(
        "SELECT * FROM Usuarios WHERE usuario = ? AND senha = ? AND perfil = ?",
        (usuario.strip(), senha.strip(), perfil_esperado)
    )
    registro_usuario = cursor.fetchone()

    if not registro_usuario:
        conexao.close()
        raise PermissionError("Credenciais inválidas ou perfil incorreto.")

    # Converte o registro do banco para dicionário para facilitar o acesso por chave
    dados = dict(registro_usuario)

    # Especialistas precisam ter vínculo ativo com um consultório e uma especialidade
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
    """Cadastra um novo especialista, cria seu usuário de acesso e vincula ao consultório."""
    if not all([nome.strip(), usuario.strip(), senha.strip(), numero_consultorio.strip()]):
        raise ValueError("Todos os campos são obrigatórios.")

    conexao = conectar()
    cursor = conexao.cursor()

    # Verifica se a especialidade já atingiu o limite máximo de profissionais
    cursor.execute(
        "SELECT COUNT(*) as total FROM Profissional_Consultorio WHERE especialidade_id = ?",
        (especialidade_id,)
    )
    total = cursor.fetchone()["total"]
    if total >= LIMITE_ESPECIALISTAS_POR_ESP:
        conexao.close()
        raise ValueError(f"Limite atingido: máximo de {LIMITE_ESPECIALISTAS_POR_ESP} especialistas nesta especialidade.")

    try:
        # 1. Cria o registro de login na tabela Usuarios
        cursor.execute(
            "INSERT INTO Usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, 'ESPECIALISTA')",
            (nome.strip(), usuario.strip(), senha.strip())
        )
        usuario_id = cursor.lastrowid  # Recupera o ID gerado para o novo usuário

        # 2. Cria o vínculo do especialista com o consultório e a especialidade
        cursor.execute("""
            INSERT INTO Profissional_Consultorio (usuario_id, nome_especialista, numero_consultorio, especialidade_id)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, nome.strip(), numero_consultorio.strip(), especialidade_id))

        # Confirma ambas as inserções juntas (transação atômica)
        conexao.commit()
    except sqlite3.IntegrityError as erro:
        # Desfaz qualquer alteração parcial caso ocorra violação de unicidade (UNIQUE)
        conexao.rollback()
        conexao.close()
        if "numero_consultorio" in str(erro):
            raise ValueError("Este consultório já está ocupado por outro especialista.")
        raise ValueError("Nome de usuário já está em uso.")

    conexao.close()


def atualizar_consultorio_especialista(profissional_id, novo_consultorio):
    """Atualiza o número ou nome do consultório atribuído a um especialista."""
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
    """Remove o vínculo do profissional e, se existir, exclui também seu usuário."""
    conexao = conectar()
    cursor = conexao.cursor()

    # Busca o usuario_id antes de apagar o registro de profissional
    cursor.execute("SELECT usuario_id FROM Profissional_Consultorio WHERE id = ?", (profissional_id,))
    linha = cursor.fetchone()

    if linha:
        cursor.execute("DELETE FROM Profissional_Consultorio WHERE id = ?", (profissional_id,))
        if linha["usuario_id"]:
            cursor.execute("DELETE FROM Usuarios WHERE id = ?", (linha["usuario_id"],))

    conexao.commit()
    conexao.close()


def cadastrar_adm(nome, usuario, senha):
    """Cadastra um novo usuário com perfil de administrador (ADM)."""
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
    """Cadastra uma nova especialidade com status inicial 'ATIVA' e sigla em maiúsculas."""
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
    """Alterna entre 'ATIVA' e 'INATIVA', bloqueando desativação se houver pacientes aguardando."""
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT status FROM Especialidade WHERE id = ?", (especialidade_id,))
    especialidade = cursor.fetchone()
    if not especialidade:
        conexao.close()
        raise ValueError("Especialidade não encontrada.")

    if especialidade["status"] == "ATIVA":
        # Evita deixar pacientes na fila sem atendimento ao desativar a especialidade
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
    """Lista especialidades ordenadas por ID, filtrando apenas as ativas por padrão."""
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
    """Lista os profissionais e seus consultórios junto ao nome da especialidade."""
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
    """Retorna os 30 registros mais recentes do histórico de atendimento."""
    conexao = conectar()
    cursor = conexao.cursor()
    # Ordena por ID decrescente para pegar os últimos atendimentos primeiro
    cursor.execute("SELECT * FROM Historico_Atendimento ORDER BY id DESC LIMIT 30")
    linhas = [dict(registro) for registro in cursor.fetchall()]
    conexao.close()
    return linhas