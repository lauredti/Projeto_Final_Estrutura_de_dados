## Projeto_Final_Estrutura_de_dados
Sistema desktop em Python (Tkinter e SQLite) para gerenciamento de filas e senhas médicas. Possui totem de autoatendimento com triagem por 7 níveis de prioridade, painel de chamadas com tempo médio de espera, área do especialista para controle de consultas e módulo administrativo para gestão de especialidades, consultórios e histórico.

---
<img src="imagens/inicial.png" alt="Tela Inicial do projeto" width="1000" style="display: block; margin: 0 auto;" />

# Clínica Médica UDF — Sistema de Gerenciamento de Senhas

Projeto desenvolvido para a disciplina de **Estrutura de Dados II** — Centro Universitário UDF.

## Integrantes do Grupo

* **Arthur** (`@lauredti`)
* **Juan Moreira Braz** (`@lauredti`)
* **Marcos Vinnicyus Araujo** (`@lauredti`)
* **Maria Laura Silva** (`@lauredti`)

---

## Objetivo do Projeto

> Informar o fluxo de recepção e triagem de uma clínica médica que atende múltiplas especialidades como: **Clínica Geral**, **Cardiologia**, **Ortopedia** com possibilidade de expansão futura. O sistema resolve o problema de organização de filas mistas aplicando na prática conceitos de **Filas FIFO** e **Filas de Prioridade**, garantindo que pacientes preferenciais sejam atendidos na ordem correta de urgência sem perder o controle da ordem de chegada.

<img src="imagens/senha.png" alt="Página de geração de senha" width="1000" style="display: block; margin: 0 auto;" />

## Funcionalidades Desenvolvidas

O sistema é dividido em quatro páginas principais acessíveis por abas na interface:

1. **Autoatendimento (Paciente):**
   * Escolha da especialidade médica ativa em 3 etapas simples.
   * Seleção entre atendimento **Geral / Normal** ou **Prioritário / Preferencial**, com escolha obrigatória do subgrupo prioritário.
   * Geração de senha unindo a sigla da especialidade e o contador sequencial (ex.: `CG-N001`, `CA-P001`, `OR-N002`).
   * Exibição imediata da posição atual na fila e do tempo estimado de espera.

2. **Painel de Espera:**
   * Destaque para a última senha chamada, o consultório de destino, a especialidade e a categoria.
   * Histórico das últimas senhas chamadas na tela.
   * Listagem em tempo real dos próximos pacientes na fila já organizados pela ordem de prioridade, exibindo o total de pacientes aguardando e o tempo estimado por especialidade.

3. **Área do Especialista:**
   * Tela de login e autocadastro para médicos/especialistas com limite de até 3 profissionais por especialidade e validação de consultório único.
   * Chamada automática da próxima senha da sua especialidade respeitando a fila de prioridade.
   * Controle do ciclo de atendimento: **Chamar Próxima Senha**, **Iniciar Atendimento**, **Finalizar Consulta** ou **Marcar Ausência**.

4. **Administração:**
   * Acesso restrito por login (usuário padrão inicial: `admin` / senha: `123`).
   * Cadastro e ativação/desativação de especialidades médicas (bloqueando a desativação caso existam pacientes aguardando naquela fila).
   * Gerenciamento de especialistas e alteração de consultórios.
   * Consulta ao histórico completo de atendimentos com horários de emissão, chamada, início, fim e status final.

---

## Estruturas de Dados Utilizadas

Para garantir desempenho e organização, o módulo `filas.py` combina as seguintes estruturas de dados:

* **Fila de Prioridade:**
  Cada especialidade possui sua própria fila de prioridade gerenciada por um *heap* mínimo. Como o `heapq` sempre remove o menor valor primeiro, pacientes com nível de prioridade menor (mais urgente) saem na frente.
* **Fila FIFO:**
  Utilizada para manter o controle estrito de ordem de chegada dos atendimentos normais por especialidade, permitindo inserção e remoção nas extremidades em tempo $O(1)$.
* **Tabelas Hash / Dicionários:**
  Usados para mapear cada especialidade pelo seu `id` e associar cada subgrupo ao seu peso numérico, garantindo acesso instantâneo aos dados de cada fila independente.

---

##  Regras de Prioridade e Cálculo de Espera

### Política de Atendimento Prioritário

O sistema implementa uma regra de prioridade em **7 níveis**, onde **1 é a maior prioridade** e **7 é o atendimento comum**:

| Nível | Categoria / Subgrupo | Tipo de Senha |
| :---: | :--- | :---: | 
| **1** | Idosos 80+ | Preferencial (`P`) |
| **2** | Idosos (60 a 79 anos) | Preferencial (`P`) |
| **3** | PCD (Pessoa com Deficiência) | Preferencial (`P`) | 
| **4** | Gestantes | Preferencial (`P`) | 
| **5** | Obesos | Preferencial (`P`) | 
| **6** | Crianças de colo | Preferencial (`P`) | 
| **7** | Geral / Normal | Normal (`N`) | 

**Como funciona o desempate:**
Quando dois ou mais pacientes possuem o **mesmo nível de prioridade**, o critério de desempate da tupla é o contador sequencial. Assim, quem chegou primeiro é atendido primeiro, preservando o comportamento **FIFO dentro de cada nível de prioridade**.

<img src="imagens/espera.png" alt="Sala de espera" width="1000" style="display: block; margin: 0 auto;" style="display: block; margin: 0 auto;" style="display: block; margin: 0 auto;" />

### Cálculo do Tempo Estimado de Espera

* O tempo médio adotado por consulta é de **30 minutos**.
* Quando uma senha é emitida, o sistema ordena a fila daquela especialidade conforme a regra de prioridade vigente e verifica quantos pacientes estão à frente daquela senha.
* **Hipótese de funcionamento:** Se não houver ninguém à frente, o tempo estimado é `0 minutos`. Caso chegue um paciente com prioridade mais alta posteriormente, as posições e estimativas no Painel de Espera são recalculadas automaticamente.

---

## Tratamento de Exceções e Validações

O sistema trata erros operacionais e entradas inválidas para evitar falhas durante o uso:

* **Fila vazia:** Impede a chamada de senha quando não há pacientes aguardando na especialidade, exibindo aviso amigável ao médico.
* **Atendimento em andamento:** Bloqueia o especialista de chamar uma nova senha antes de finalizar ou marcar ausência da senha atual.
* **Campos vazios ou inválidos:** Valida formulários de login, cadastro de especialistas, administradores e especialidades.
* **Duplicidade e limites:** Impede usuários repetidos, siglas de especialidades duplicadas, dois médicos no mesmo consultório e bloqueia o cadastro de mais de 3 especialistas na mesma especialidade.
* **Especialidade com fila ativa:** Impede que o administrador desative uma especialidade enquanto houver pacientes com status `AGUARDANDO`.

---


##  Instruções de Instalação e Execução

Siga o passo a passo abaixo para preparar o ambiente e executar o sistema localmente.

### 1. Pré-requisitos do Sistema

Antes de começar, verifique se você possui:

* **Python 3.8 ou superior** instalado na máquina.
  * Para conferir sua versão, abra o terminal (ou Prompt de Comando / PowerShell) e digite:
    ```bash
    python --version
    ```
    *(No Linux ou macOS, pode ser necessário usar `python3 --version`)*.
* **Tkinter** (biblioteca de interface gráfica nativa do Python):
  * **Windows e macOS:** Já vem instalado junto com o instalador oficial do Python.
  * **Linux (Ubuntu / Debian):** Caso não esteja instalado, execute:
    ```bash
    sudo apt update && sudo apt install python3-tk
    ```
---

##  Passo a Passo de Instalação

### Passo 1: Verifique se o Python está instalado
Abra o terminal ou Prompt de Comando / PowerShell e digite:
```bash
python --version
```
*(No Linux ou macOS, use `python3 --version`)*

### Passo 2: Entre na pasta do projeto
No terminal, vá até a pasta onde estão os arquivos `.py` do sistema:
```bash
cd caminho/da/pasta/do/projeto
```

### Passo 3: Instale a biblioteca Pillow
Digite o comando abaixo no terminal:
```bash
pip install pillow
```
*(Se usar Linux/macOS, pode ser `pip3 install pillow`).*

---

## Como Executar e Abrir a Interface

Com o terminal dentro da pasta do projeto, rode o arquivo principal:

* **No Windows:**
  ```bash
  python principal.py
  ```

* **No Linux / macOS:**
  ```bash
  python3 principal.py
  ```

Assim que você rodar esse comando:
1. O arquivo de banco de dados **`clinica_medica.db`** será criado automaticamente na pasta.
2. A janela principal do programa (**"Clínica Médica UDF — Sistema de Gerenciamento de Senhas"**) vai abrir na sua tela.

<img src="imagens/adm.png" alt="Painel do ADM" width="1000" style="display: block; margin: 0 auto;" />

---

## Estrutura de Arquivos do Projeto

```text
sistema-clinica-medica/
├── principal.py        # Ponto de entrada: inicializa o banco e abre a janela Tkinter
├── interface.py        # Interface gráfica completa 
├── filas.py            # Lógica das filas FIFO (deque), Min-Heap (heapq) e cálculo de espera
├── autenticador.py     # Login, cadastro e gerenciamento de especialistas, ADMs e especialidades
├── banco_dados.py      # Criação das tabelas SQLite, conexão e dados iniciais padrão
├── imagens/
│   └── logo.png        # Logotipo exibido no cabeçalho da aplicação
└── README.md           # Documentação do projeto