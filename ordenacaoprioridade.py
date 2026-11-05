import heapq
from collections import deque
from itertools import count

class GerenciadorFilas:
    def __init__(self):

        #Especialidades disponiveis

        self.especialidades = [
            "Clínica Geral",
            "Pediatria",
            "Ginecologia",
            "Cardiologia",
            "Psiquiatria"
        ]

        #Ordem das categorias prioritárias
        self.prioridades = {
            "Idoso 80+": 1,
            "Idoso": 2,
            "PCD": 3,
            "Gestante": 4,
            "Obeso": 5,
            "Criança de colo": 6
        }

        #Contador para manter a ordem de chegada
        self.contador = count()

        #Filas separadas para cada especialidade
        self.filas = {}

        for especialidade in self.especialidades:
            self.filas[especialidade] = {
                "prioritarios": [],
                "normais": deque()
            }

    #Adiciona o paciente a fila da especialidade
    def adicionar_senha(self, codigo, categoria, especialidade):
        if especialidade not in self.filas:
            raise ValueError("Especialidade inválida.")
    
        #Dados do paciente
        paciente = {
            "codigo": codigo,
            "categoria": categoria,
            "especialidade": especialidade,
            "status": "Aguardando"
        }

        fila = self.filas[especialidade]

        if categoria == "Normal":
            #Pacientes normais FIFO
            fila["normais"].append(paciente)

        elif categoria in self.prioridades:
            #Prioritários ordem de prioridade
            prioridade = self.prioridades[categoria]
            chegada = next(self.contador)

            heapq.heappush(
                fila["prioritarios"],
                (prioridade, chegada, paciente)
            )

        else:
            raise ValueError("Categoria de prioridade inválida.")

        return paciente

    #Chamada do próximo paciente da especialidade
    def chamar_proxima(self, especialidade):
        if especialidade not in self.filas:
            raise ValueError("Especialidade inválida.")

        fila = self.filas[especialidade]

        #Prioritários são chamados primeiro
        if fila["prioritarios"]:
            _, _, paciente = heapq.heappop(
                fila["prioritarios"]
            )

        #Se não houver prioritários, chama um normal
        elif fila["normais"]:
            paciente = fila["normais"].popleft()

        else:
            return None

        paciente["status"] = "Chamado"
        return paciente

    #Consulta os pacientes que ainda aguardam
    def consultar_fila(self, especialidade):
        if especialidade not in self.filas:
            raise ValueError("Especialidade inválida.")

        fila = self.filas[especialidade]

        prioritarios = [
            item[2]
            for item in sorted(fila["prioritarios"])
        ]

        normais = list(fila["normais"])

        return prioritarios + normais

    #Mostra a fila de uma especialidade
    def mostrar_fila(self, especialidade):
        pacientes = self.consultar_fila(especialidade)

        print(f"\n--- Fila de {especialidade} ---")

        if not pacientes:
            print("Não há pacientes aguardando.")
            return

        for posicao, paciente in enumerate(pacientes, start=1):
            print(
                f"{posicao}. Senha: {paciente['codigo']} | "
                f"Categoria: {paciente['categoria']} | "
                f"Status: {paciente['status']}"
            )