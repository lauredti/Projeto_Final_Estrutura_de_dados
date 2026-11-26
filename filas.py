import heapq
from collections import deque
from banco_dados import conectar, agora

NIVEIS_PRIORIDADE = {
    "Urgente": 1,
    "Preferencial": 2,
    "Normal": 3
}

TEMPO_MEDIO_MINUTOS = 30


def classificar_paciente(genero, idade, gestante=False, lactante=False, pcd=False, obesidade=False):
    if not isinstance(idade, int) or idade < 0 or idade > 130:
        raise ValueError("Informe uma idade válida entre 0 e 130 anos.")

    if genero not in ("Masculino", "Feminino", "Outro"):
        raise ValueError("Selecione um gênero válido.")

    if genero != "Feminino":
        gestante = False
        lactante = False

    if idade > 80:
        return "Urgente", "Idoso 80+ (Urgente)"

    condicoes = []
    if gestante:
        condicoes.append("Gestante")
    if lactante:
        condicoes.append("Lactante")
    if pcd:
        condicoes.append("Necessidade Especial")
    if obesidade:
        condicoes.append("Obesidade")
    if genero == "Feminino" and idade >= 60:
        condicoes.append("Mulher 60+")
    elif genero == "Masculino" and idade >= 65:
        condicoes.append("Homem 65+")

    if condicoes:
        return "Preferencial", ", ".join(condicoes)

    return "Normal", "Geral / Normal"


class GerenciadorFilas:
    def __init__(self):
        self.filas_prioridade = {}
        self.filas_normais = {}
        self.contadores_u = {}
        self.contadores_p = {}
        self.contadores_n = {}
        self.ordem_global = 0
        self.ultima_chamada = None
        self.carregar_estado_banco()

    def _garantir_especialidade(self, especialidade_id):
        if especialidade_id not in self.filas_prioridade:
            self.filas_prioridade[especialidade_id] = []
            self.filas_normais[especialidade_id] = deque()
            self.contadores_u[especialidade_id] = 0
            self.contadores_p[especialidade_id] = 0
            self.contadores_n[especialidade_id] = 0

    def carregar_estado_banco(self):
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM Especialidade WHERE status = 'ATIVA'")
        for linha in cursor.fetchall():
            self._garantir_especialidade(linha["id"])

        cursor.execute("SELECT especialidade_id, tipo FROM Senha")
        for linha in cursor.fetchall():
            especialidade_id = linha["especialidade_id"]
            self._garantir_especialidade(especialidade_id)
            if linha["tipo"] == "Urgente":
                self.contadores_u[especialidade_id] += 1
            elif linha["tipo"] == "Preferencial":
                self.contadores_p[especialidade_id] += 1
            else:
                self.contadores_n[especialidade_id] += 1

        cursor.execute("""
            SELECT s.*, e.nome as esp_nome, e.sigla as esp_sigla
            FROM Senha s
            JOIN Especialidade e ON s.especialidade_id = e.id
            WHERE s.status = 'AGUARDANDO'
            ORDER BY s.id ASC
        """)
        for linha in cursor.fetchall():
            especialidade_id = linha["especialidade_id"]
            self._garantir_especialidade(especialidade_id)
            self.ordem_global += 1
            item = {
                "codigo": linha["codigo"],
                "tipo": linha["tipo"],
                "categoria": linha["categoria_prioridade"],
                "nivel": linha["nivel_prioridade"],
                "especialidade_id": especialidade_id,
                "especialidade_nome": linha["esp_nome"],
                "ordem": self.ordem_global
            }
            heapq.heappush(self.filas_prioridade[especialidade_id], (item["nivel"], item["ordem"], item))
            if item["tipo"] == "Normal":
                self.filas_normais[especialidade_id].append(item)

        conexao.close()

    def emitir_senha(self, especialidade_id, genero, idade, gestante=False, lactante=False, pcd=False, obesidade=False):
        tipo, motivo_prioridade = classificar_paciente(genero, idade, gestante, lactante, pcd, obesidade)

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT nome, sigla, status FROM Especialidade WHERE id = ?", (especialidade_id,))
        especialidade = cursor.fetchone()

        if not especialidade or especialidade["status"] != "ATIVA":
            conexao.close()
            raise ValueError("Especialidade inválida ou inativa.")

        self._garantir_especialidade(especialidade_id)

        if tipo == "Urgente":
            self.contadores_u[especialidade_id] += 1
            numero = self.contadores_u[especialidade_id]
            codigo = f"{especialidade['sigla']}-U{numero:03d}"
        elif tipo == "Preferencial":
            self.contadores_p[especialidade_id] += 1
            numero = self.contadores_p[especialidade_id]
            codigo = f"{especialidade['sigla']}-P{numero:03d}"
        else:
            self.contadores_n[especialidade_id] += 1
            numero = self.contadores_n[especialidade_id]
            codigo = f"{especialidade['sigla']}-N{numero:03d}"

        nivel = NIVEIS_PRIORIDADE[tipo]
        self.ordem_global += 1

        dados_senha = {
            "codigo": codigo,
            "tipo": tipo,
            "categoria": motivo_prioridade,
            "nivel": nivel,
            "especialidade_id": especialidade_id,
            "especialidade_nome": especialidade["nome"],
            "ordem": self.ordem_global
        }

        heapq.heappush(self.filas_prioridade[especialidade_id], (nivel, self.ordem_global, dados_senha))
        if tipo == "Normal":
            self.filas_normais[especialidade_id].append(dados_senha)

        cursor.execute("""
            INSERT INTO Senha (codigo, tipo, categoria_prioridade, nivel_prioridade, especialidade_id, status)
            VALUES (?, ?, ?, ?, ?, 'AGUARDANDO')
        """, (codigo, tipo, motivo_prioridade, nivel, especialidade_id))

        cursor.execute("""
            INSERT INTO Historico_Atendimento (senha_codigo, especialidade_nome, categoria_prioridade, horario_emissao, status_final)
            VALUES (?, ?, ?, ?, 'AGUARDANDO')
        """, (codigo, especialidade["nome"], motivo_prioridade, agora()))

        conexao.commit()
        conexao.close()

        posicao = self.obter_posicao_senha(especialidade_id, codigo)
        tempo_estimado = (posicao - 1) * TEMPO_MEDIO_MINUTOS

        return dados_senha, posicao, tempo_estimado

    def consultar_proxima(self, especialidade_id):
        self._garantir_especialidade(especialidade_id)
        if not self.filas_prioridade[especialidade_id]:
            return None
        return self.filas_prioridade[especialidade_id][0][2]

    def chamar_proxima(self, especialidade_id, consultorio):
        self._garantir_especialidade(especialidade_id)

        if not self.filas_prioridade[especialidade_id]:
            raise IndexError("Não há pacientes aguardando na fila desta especialidade.")

        _, _, senha_chamada = heapq.heappop(self.filas_prioridade[especialidade_id])

        if senha_chamada["tipo"] == "Normal" and self.filas_normais[especialidade_id]:
            self.filas_normais[especialidade_id].popleft()

        senha_chamada["consultorio"] = consultorio
        self.ultima_chamada = senha_chamada

        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE Senha
            SET status = 'CHAMADA', consultorio_destino = ?
            WHERE codigo = ?
        """, (consultorio, senha_chamada["codigo"]))

        cursor.execute("""
            UPDATE Historico_Atendimento
            SET consultorio = ?, horario_chamada = ?, status_final = 'CHAMADA'
            WHERE senha_codigo = ?
        """, (consultorio, agora(), senha_chamada["codigo"]))

        conexao.commit()
        conexao.close()

        return senha_chamada

    def atualizar_status_atendimento(self, codigo_senha, novo_status):
        conexao = conectar()
        cursor = conexao.cursor()
        hora_atual = agora()

        cursor.execute("UPDATE Senha SET status = ? WHERE codigo = ?", (novo_status, codigo_senha))

        if novo_status == "EM_ATENDIMENTO":
            cursor.execute("""
                UPDATE Historico_Atendimento
                SET horario_inicio = ?, status_final = ?
                WHERE senha_codigo = ?
            """, (hora_atual, novo_status, codigo_senha))
        elif novo_status in ("FINALIZADO", "AUSENTE"):
            cursor.execute("""
                UPDATE Historico_Atendimento
                SET horario_fim = ?, status_final = ?
                WHERE senha_codigo = ?
            """, (hora_atual, novo_status, codigo_senha))

        conexao.commit()
        conexao.close()

    def listar_fila_ordenada(self, especialidade_id):
        self._garantir_especialidade(especialidade_id)
        ordenados = sorted(self.filas_prioridade[especialidade_id], key=lambda item: (item[0], item[1]))
        return [item[2] for item in ordenados]

    def contar_por_categoria(self):
        contagem = {"Urgente": 0, "Preferencial": 0, "Normal": 0}
        for fila in self.filas_prioridade.values():
            for _, _, senha in fila:
                if senha["tipo"] in contagem:
                    contagem[senha["tipo"]] += 1
        return contagem

    def obter_posicao_senha(self, especialidade_id, codigo_senha):
        fila = self.listar_fila_ordenada(especialidade_id)
        for indice, senha in enumerate(fila, start=1):
            if senha["codigo"] == codigo_senha:
                return indice
        return 0

    def calcular_tempo_espera_fila(self, especialidade_id):
        fila = self.listar_fila_ordenada(especialidade_id)
        return len(fila) * TEMPO_MEDIO_MINUTOS