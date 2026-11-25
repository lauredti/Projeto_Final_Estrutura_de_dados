import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk

# Importa a lógica de filas e as funções de banco/autenticação
from filas import GerenciadorFilas, NIVEIS_PRIORIDADE
from autenticador import (
    autenticar_usuario,
    cadastrar_especialista,
    atualizar_consultorio_especialista,
    remover_especialista,
    cadastrar_adm,
    cadastrar_especialidade,
    alternar_status_especialidade,
    listar_especialidades,
    listar_profissionais,
    listar_historico
)

# Paleta de cores usada em toda a interface
COR_FUNDO = "#F0F4F8"
COR_CARD = "#FFFFFF"
COR_BORDA = "#90CAF9"
COR_AZUL_ESCURO = "#0D47A1"
COR_AZUL_PRIMARIO = "#1565C0"
COR_AZUL_MEDIO = "#1976D2"
COR_AZUL_VIBRANTE = "#42A5F5"
COR_AZUL_CLARO = "#E3F2FD"
COR_ABA_INATIVA = "#DCE6F2"
COR_TEXTO_PRINCIPAL = "#333333"
COR_TEXTO_SUAVE = "#555555"
COR_DOURADO_BG = "#FEF3C7"
COR_DOURADO_TXT = "#92400E"
COR_DESTAQUE_OURO = "#FFEB3B"
COR_PERIGO = "#D32F2F"


class AplicacaoClinica:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Clínica Médica UDF — Sistema de Gerenciamento de Senhas")
        
        # Define o tamanho da janela e centraliza na tela
        largura, altura = 1150, 740
        pos_x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = max(10, (self.janela.winfo_screenheight() // 2) - (altura // 2) - 20)
        self.janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.janela.minsize(1024, 680)
        self.janela.configure(bg=COR_FUNDO)

        # Inicializa o controlador das filas e as variáveis de estado da sessão
        self.gerenciador = GerenciadorFilas()
        self.especialista_logado = None
        self.senha_em_atendimento = None
        self.adm_logado = None
        self.especialidade_selecionada_paciente = None
        self.ultimas_chamadas_painel = []

        # Dicionários para controlar as abas e seus botões
        self.botoes_abas = {}
        self.quadros_abas = {}

        # Configura visual, monta os componentes e carrega os dados iniciais
        self._configurar_estilos()
        self._construir_interface()
        self.atualizar_tudo()

    def _configurar_estilos(self):
        # Personaliza tabelas e caixas de seleção do ttk
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background=COR_CARD,
            foreground=COR_TEXTO_PRINCIPAL,
            fieldbackground=COR_CARD,
            rowheight=32,
            font=("Arial", 11),
            borderwidth=0
        )
        estilo.configure(
            "Treeview.Heading",
            background=COR_AZUL_CLARO,
            foreground=COR_AZUL_ESCURO,
            font=("Arial", 11, "bold"),
            relief="flat",
            padding=[6, 6]
        )
        estilo.map(
            "Treeview",
            background=[("selected", COR_AZUL_CLARO)],
            foreground=[("selected", COR_AZUL_ESCURO)]
        )

        estilo.configure(
            "TCombobox",
            fieldbackground=COR_CARD,
            background=COR_AZUL_CLARO,
            foreground=COR_TEXTO_PRINCIPAL,
            padding=6
        )

    def _criar_cartao(self, pai, **kwargs):
        # Cria um container branco com borda azul clara
        return tk.Frame(
            pai,
            bg=COR_CARD,
            highlightbackground=COR_BORDA,
            highlightthickness=2,
            bd=0,
            **kwargs
        )

    def _construir_interface(self):
        # Barra superior 
        topo = tk.Frame(self.janela, bg=COR_AZUL_ESCURO, height=66)
        topo.pack(fill="x")
        topo.pack_propagate(False)

        conteudo_topo = tk.Frame(topo, bg=COR_AZUL_ESCURO)
        conteudo_topo.pack(fill="both", expand=True, padx=24)

        # Localiza e carrega a logo da clínica
        pasta_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_logo = os.path.join(pasta_atual, "imagens", "logo.png")
        
        if not os.path.exists(caminho_logo):
            caminho_logo = os.path.join(pasta_atual, "..", "imagens", "logo.png")

        if os.path.exists(caminho_logo):
            try:
                # Usa Pillow para redimensionar com alta nitidez
                imagem_original = Image.open(caminho_logo).convert("RGBA")
                imagem_suave = imagem_original.resize((42, 42), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(imagem_suave)
            except Exception:
                # Fallback nativo do Tkinter caso o Pillow falhe
                img_nativa = tk.PhotoImage(file=caminho_logo)
                fator = max(1, img_nativa.height() // 42)
                self.logo_img = img_nativa.subsample(fator, fator)

            tk.Label(
                conteudo_topo,
                image=self.logo_img,
                bg=COR_AZUL_ESCURO
            ).pack(side="left", pady=12, padx=(0, 12))

        tk.Label(
            conteudo_topo,
            text="Clínica Médica UDF",
            font=("Arial", 19, "bold"),
            bg=COR_AZUL_ESCURO,
            fg="white"
        ).pack(side="left", pady=16)

        tk.Label(
            conteudo_topo,
            text="Sistema de Autoatendimento & Controle de Filas",
            font=("Arial", 11),
            bg=COR_AZUL_ESCURO,
            fg="#BBDEFB"
        ).pack(side="right", pady=18)

        # Barra de navegação das 4 abas principais
        barra_abas = tk.Frame(self.janela, bg=COR_FUNDO)
        barra_abas.pack(fill="x", padx=20, pady=(12, 0))

        definicoes_abas = [
            ("paciente", "1. Autoatendimento"),
            ("painel", "2. Painel de Espera"),
            ("especialista", "3. Área do Especialista"),
            ("adm", "4. Administração")
        ]

        for chave, texto in definicoes_abas:
            btn = tk.Button(
                barra_abas,
                text=texto,
                font=("Arial", 11, "bold"),
                width=22,
                height=2,
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda c=chave: self._selecionar_aba(c)
            )
            btn.pack(side="left", padx=(0, 6))
            self.botoes_abas[chave] = btn

        # Área central onde o conteúdo de cada aba será exibido
        self.container_principal = tk.Frame(self.janela, bg=COR_FUNDO)
        self.container_principal.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.aba_paciente = tk.Frame(self.container_principal, bg=COR_FUNDO)
        self.aba_painel = tk.Frame(self.container_principal, bg=COR_FUNDO)
        self.aba_especialista = tk.Frame(self.container_principal, bg=COR_FUNDO)
        self.aba_adm = tk.Frame(self.container_principal, bg=COR_FUNDO)

        self.quadros_abas = {
            "paciente": self.aba_paciente,
            "painel": self.aba_painel,
            "especialista": self.aba_especialista,
            "adm": self.aba_adm
        }

        # Constrói o conteúdo interno de todas as abas
        self._montar_aba_paciente()
        self._montar_aba_painel()
        self._montar_aba_especialista()
        self._montar_aba_adm()

        # Abre o sistema na aba de autoatendimento
        self._selecionar_aba("paciente")

    def _selecionar_aba(self, chave_ativa):
        # Mostra apenas a aba clicada e destaca o botão correspondente
        for chave, quadro in self.quadros_abas.items():
            if chave == chave_ativa:
                quadro.pack(fill="both", expand=True)
                self.botoes_abas[chave].config(
                    bg=COR_AZUL_PRIMARIO,
                    fg="white",
                    activebackground=COR_AZUL_PRIMARIO,
                    activeforeground="white"
                )
            else:
                quadro.pack_forget()
                self.botoes_abas[chave].config(
                    bg=COR_ABA_INATIVA,
                    fg=COR_AZUL_ESCURO,
                    activebackground="#C8D8EC",
                    activeforeground=COR_AZUL_ESCURO
                )

    # AUTOATENDIMENTO 

    def _montar_aba_paciente(self):
        centralizador = tk.Frame(self.aba_paciente, bg=COR_FUNDO)
        centralizador.pack(fill="both", expand=True)

        # Cartão central fixo onde as 3 etapas se alternam
        self.recipiente_paciente = self._criar_cartao(centralizador, width=760, height=540)
        self.recipiente_paciente.place(relx=0.5, rely=0.5, anchor="center")
        self.recipiente_paciente.pack_propagate(False)

        # Etapa 1: Escolha da especialidade 
        self.quadro_etapa1 = tk.Frame(self.recipiente_paciente, bg=COR_CARD, padx=45, pady=28)
        tk.Label(
            self.quadro_etapa1,
            text="ETAPA 1 DE 3",
            font=("Arial", 10, "bold"),
            bg=COR_AZUL_CLARO,
            fg=COR_AZUL_ESCURO,
            padx=14,
            pady=5
        ).pack(pady=(4, 10))

        tk.Label(
            self.quadro_etapa1,
            text="Bem-vindo!",
            font=("Arial", 24, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_MEDIO
        ).pack(pady=(0, 6))

        tk.Label(
            self.quadro_etapa1,
            text="Selecione a especialidade desejada para iniciar seu atendimento:",
            font=("Arial", 12),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(pady=(0, 20))

        # Container preenchido dinamicamente com os botões das especialidades ativas
        self.quadro_botoes_esp = tk.Frame(self.quadro_etapa1, bg=COR_CARD)
        self.quadro_botoes_esp.pack(fill="both", expand=True)

        # Etapa 2: Escolha entre Normal ou Preferencial 
        self.quadro_etapa2 = tk.Frame(self.recipiente_paciente, bg=COR_CARD, padx=45, pady=28)
        tk.Label(
            self.quadro_etapa2,
            text="ETAPA 2 DE 3",
            font=("Arial", 10, "bold"),
            bg=COR_AZUL_CLARO,
            fg=COR_AZUL_ESCURO,
            padx=14,
            pady=5
        ).pack(pady=(4, 10))

        tk.Label(
            self.quadro_etapa2,
            text="Tipo de Atendimento",
            font=("Arial", 22, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(0, 4))

        self.rotulo_esp_escolhida = tk.Label(
            self.quadro_etapa2,
            text="Especialidade: ---",
            font=("Arial", 12, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_MEDIO
        )
        self.rotulo_esp_escolhida.pack(pady=(0, 14))

        self.var_tipo_atendimento = tk.StringVar(value="Normal")
        caixa_opcoes = tk.Frame(
            self.quadro_etapa2,
            bg=COR_FUNDO,
            highlightbackground=COR_BORDA,
            highlightthickness=2,
            padx=20,
            pady=14
        )
        caixa_opcoes.pack(fill="x", pady=6)

        tk.Label(
            caixa_opcoes,
            text="Selecione a categoria de atendimento:",
            font=("Arial", 11, "bold"),
            bg=COR_FUNDO,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 8))

        tk.Radiobutton(
            caixa_opcoes,
            text="Atendimento Geral / Normal (N)",
            variable=self.var_tipo_atendimento,
            value="Normal",
            font=("Arial", 12, "bold"),
            bg=COR_FUNDO,
            fg=COR_TEXTO_PRINCIPAL,
            activebackground=COR_FUNDO,
            selectcolor=COR_CARD,
            command=self._alternar_subgrupo
        ).pack(anchor="w", pady=4)

        tk.Radiobutton(
            caixa_opcoes,
            text="Atendimento Prioritário / Preferencial (P)",
            variable=self.var_tipo_atendimento,
            value="Preferencial",
            font=("Arial", 12, "bold"),
            bg=COR_FUNDO,
            fg=COR_TEXTO_PRINCIPAL,
            activebackground=COR_FUNDO,
            selectcolor=COR_CARD,
            command=self._alternar_subgrupo
        ).pack(anchor="w", pady=4)

        tk.Label(
            self.quadro_etapa2,
            text="Subgrupo de Prioridade (obrigatório caso seja Prioritário):",
            font=("Arial", 11, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(14, 6))

        # Lista os níveis de prioridade
        subgrupos = [chave for chave in NIVEIS_PRIORIDADE.keys() if chave != "Geral / Normal"]
        self.seletor_subgrupo = ttk.Combobox(
            self.quadro_etapa2,
            values=subgrupos,
            state="disabled",
            font=("Arial", 12)
        )
        self.seletor_subgrupo.set("Idosos 80+")
        self.seletor_subgrupo.pack(fill="x", pady=(0, 20))

        botoes_etapa2 = tk.Frame(self.quadro_etapa2, bg=COR_CARD)
        botoes_etapa2.pack(fill="x", pady=6)

        tk.Button(
            botoes_etapa2,
            text="← Voltar",
            font=("Arial", 12, "bold"),
            bg=COR_ABA_INATIVA,
            fg=COR_AZUL_ESCURO,
            activebackground="#BBDEFB",
            relief="flat",
            padx=22,
            pady=11,
            cursor="hand2",
            command=self._ir_etapa1
        ).pack(side="left")

        tk.Button(
            botoes_etapa2,
            text="Emitir Senha →",
            font=("Arial", 12, "bold"),
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            activebackground=COR_AZUL_ESCURO,
            activeforeground="white",
            relief="flat",
            padx=28,
            pady=11,
            cursor="hand2",
            command=self._acao_gerar_senha
        ).pack(side="right")

        # Etapa 3: Comprovante da senha gerada 
        self.quadro_etapa3 = tk.Frame(self.recipiente_paciente, bg=COR_CARD, padx=45, pady=24)
        tk.Label(
            self.quadro_etapa3,
            text="SENHA EMITIDA!",
            font=("Arial", 10, "bold"),
            bg=COR_AZUL_CLARO,
            fg=COR_AZUL_ESCURO,
            padx=14,
            pady=5
        ).pack(pady=(2, 8))

        tk.Label(
            self.quadro_etapa3,
            text="Sua senha foi gerada com sucesso",
            font=("Arial", 20, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(0, 10))

        self.rotulo_bilhete_codigo = tk.Label(
            self.quadro_etapa3,
            text="---",
            font=("Arial", 46, "bold"),
            bg=COR_AZUL_MEDIO,
            fg="white",
            padx=42,
            pady=12
        )
        self.rotulo_bilhete_codigo.pack(pady=8)

        self.rotulo_bilhete_info = tk.Label(
            self.quadro_etapa3,
            text="",
            font=("Arial", 12),
            bg=COR_CARD,
            fg=COR_TEXTO_PRINCIPAL,
            justify="center"
        )
        self.rotulo_bilhete_info.pack(pady=10)

        self.rotulo_bilhete_espera = tk.Label(
            self.quadro_etapa3,
            text="",
            font=("Arial", 11, "bold"),
            bg=COR_DOURADO_BG,
            fg=COR_DOURADO_TXT,
            padx=16,
            pady=10
        )
        self.rotulo_bilhete_espera.pack(pady=8, fill="x")

        botoes_etapa3 = tk.Frame(self.quadro_etapa3, bg=COR_CARD)
        botoes_etapa3.pack(pady=14)

        tk.Button(
            botoes_etapa3,
            text="Emitir Nova Senha",
            font=("Arial", 12, "bold"),
            bg=COR_ABA_INATIVA,
            fg=COR_AZUL_ESCURO,
            relief="flat",
            padx=20,
            pady=11,
            cursor="hand2",
            command=self._ir_etapa1
        ).pack(side="left", padx=10)

        tk.Button(
            botoes_etapa3,
            text="Ir para o Painel de Espera",
            font=("Arial", 12, "bold"),
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            activebackground=COR_AZUL_ESCURO,
            relief="flat",
            padx=20,
            pady=11,
            cursor="hand2",
            command=lambda: self._selecionar_aba("painel")
        ).pack(side="right", padx=10)

        self._ir_etapa1()

    def _ir_etapa1(self):
        # Volta para a tela inicial de escolha da especialidade
        self.quadro_etapa2.pack_forget()
        self.quadro_etapa3.pack_forget()
        self.quadro_etapa1.pack(fill="both", expand=True)

    def _selecionar_especialidade_paciente(self, esp_nome):
        # Guarda a especialidade clicada e avança para a Etapa 2
        self.especialidade_selecionada_paciente = esp_nome
        self.rotulo_esp_escolhida.config(text=f"Especialidade selecionada: {esp_nome}")
        self.var_tipo_atendimento.set("Normal")
        self._alternar_subgrupo()
        self.quadro_etapa1.pack_forget()
        self.quadro_etapa2.pack(fill="both", expand=True)

    def _alternar_subgrupo(self):
        # Habilita o seletor de prioridade apenas se "Preferencial" estiver marcado
        if self.var_tipo_atendimento.get() == "Preferencial":
            self.seletor_subgrupo.config(state="readonly")
        else:
            self.seletor_subgrupo.config(state="disabled")

    def _acao_gerar_senha(self):
        # Emite a senha no gerenciador de filas e exibe o comprovante na Etapa 3
        esp_nome = self.especialidade_selecionada_paciente
        if not esp_nome or esp_nome not in self.mapa_especialidades:
            messagebox.showwarning("Atenção", "Selecione uma especialidade médica ativa.")
            self._ir_etapa1()
            return

        esp_id = self.mapa_especialidades[esp_nome]
        tipo = self.var_tipo_atendimento.get()
        categoria = self.seletor_subgrupo.get() if tipo == "Preferencial" else "Geral / Normal"

        try:
            dados_senha, posicao, tempo_min = self.gerenciador.emitir_senha(esp_id, tipo, categoria)
            self.rotulo_bilhete_codigo.config(text=dados_senha["codigo"])
            self.rotulo_bilhete_info.config(
                text=f"Especialidade: {dados_senha['especialidade_nome']}\n"
                     f"Categoria: {dados_senha['categoria']} (Prioridade Nível {dados_senha['nivel']})\n"
                     f"Posição atual na fila: {posicao}º"
            )
            self.rotulo_bilhete_espera.config(
                text=f"Tempo médio estimado de espera: {tempo_min} minutos (Base: 30 min por paciente à frente)"
            )
            self.quadro_etapa2.pack_forget()
            self.quadro_etapa3.pack(fill="both", expand=True)
            self.atualizar_tudo()
        except Exception as erro:
            messagebox.showerror("Erro ao emitir senha", str(erro))

    # PAINEL DE ESPERA 

    def _montar_aba_painel(self):
        # Barra superior com resumo de pacientes aguardando e tempo por especialidade
        quadro_tempos = self._criar_cartao(self.aba_painel, padx=18, pady=10)
        quadro_tempos.pack(fill="x", pady=(10, 10))

        self.rotulo_total_aguardando = tk.Label(
            quadro_tempos,
            text="Total de pacientes aguardando: 0",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        )
        self.rotulo_total_aguardando.pack()

        self.rotulo_quadro_tempos = tk.Label(
            quadro_tempos,
            text="",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        )
        self.rotulo_quadro_tempos.pack(pady=(4, 0))

        corpo = tk.Frame(self.aba_painel, bg=COR_FUNDO)
        corpo.pack(fill="both", expand=True, pady=(0, 4))

        # Coluna esquerda: destaca a senha atual e o consultório
        coluna_esquerda = tk.Frame(corpo, bg=COR_AZUL_ESCURO, padx=22, pady=20)
        coluna_esquerda.place(relx=0.0, rely=0.0, relwidth=0.41, relheight=1.0)

        self.rotulo_alerta_chamada = tk.Label(
            coluna_esquerda,
            text="AGUARDANDO CHAMADA",
            font=("Arial", 10, "bold"),
            bg=COR_AZUL_PRIMARIO,
            fg="#BBDEFB",
            padx=14,
            pady=6
        )
        self.rotulo_alerta_chamada.pack(pady=(6, 12))

        tk.Label(
            coluna_esquerda,
            text="Última Senha Chamada",
            font=("Arial", 17, "bold"),
            bg=COR_AZUL_ESCURO,
            fg="white"
        ).pack(pady=(2, 6))

        self.rotulo_painel_senha = tk.Label(
            coluna_esquerda,
            text="--",
            font=("Arial", 58, "bold"),
            bg=COR_AZUL_ESCURO,
            fg=COR_DESTAQUE_OURO
        )
        self.rotulo_painel_senha.pack(pady=10)

        self.rotulo_painel_consultorio = tk.Label(
            coluna_esquerda,
            text="Consultório: --",
            font=("Arial", 15, "bold"),
            bg="#082E6B",
            fg="white",
            padx=16,
            pady=10
        )
        self.rotulo_painel_consultorio.pack(fill="x", pady=10)

        self.rotulo_painel_destino = tk.Label(
            coluna_esquerda,
            text="Especialidade: --\nCategoria: --",
            font=("Arial", 12),
            bg=COR_AZUL_ESCURO,
            fg="#E3F2FD",
            justify="center"
        )
        self.rotulo_painel_destino.pack(pady=8)

        tk.Button(
            coluna_esquerda,
            text="+ Novo Autoatendimento",
            font=("Arial", 11, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO,
            activebackground=COR_AZUL_CLARO,
            relief="flat",
            pady=11,
            cursor="hand2",
            command=lambda: [self._ir_etapa1(), self._selecionar_aba("paciente")]
        ).pack(side="bottom", fill="x", pady=4)

        # Coluna direita: tabelas com histórico recente de chamadas e próximos da fila
        coluna_direita = tk.Frame(corpo, bg=COR_FUNDO)
        coluna_direita.place(relx=0.43, rely=0.0, relwidth=0.57, relheight=1.0)

        caixa_ultimas = self._criar_cartao(coluna_direita, padx=14, pady=10)
        caixa_ultimas.pack(fill="x", pady=(0, 10))

        tk.Label(
            caixa_ultimas,
            text="Últimas Chamadas",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 6))

        self.tabela_ultimas = ttk.Treeview(
            caixa_ultimas,
            columns=("senha", "cons", "esp", "cat"),
            show="headings",
            height=3
        )
        self.tabela_ultimas.heading("senha", text="Senha")
        self.tabela_ultimas.heading("cons", text="Consultório")
        self.tabela_ultimas.heading("esp", text="Especialidade")
        self.tabela_ultimas.heading("cat", text="Categoria")
        for coluna in ("senha", "cons", "esp", "cat"):
            self.tabela_ultimas.column(coluna, anchor="center", width=130)
        self.tabela_ultimas.pack(fill="x")

        caixa_espera = self._criar_cartao(coluna_direita, padx=14, pady=10)
        caixa_espera.pack(fill="both", expand=True)

        tk.Label(
            caixa_espera,
            text="Próximos na Fila (Ordem de Prioridade)",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 6))

        colunas = ("codigo", "especialidade", "tipo", "categoria", "espera")
        self.tabela_espera = ttk.Treeview(caixa_espera, columns=colunas, show="headings", height=6)
        self.tabela_espera.heading("codigo", text="Senha")
        self.tabela_espera.heading("especialidade", text="Especialidade")
        self.tabela_espera.heading("tipo", text="Tipo")
        self.tabela_espera.heading("categoria", text="Prioridade")
        self.tabela_espera.heading("espera", text="Espera Est.")
        for coluna in colunas:
            self.tabela_espera.column(coluna, anchor="center", width=110)
        self.tabela_espera.pack(fill="both", expand=True)

    # ÁREA DO ESPECIALISTA 

    def _montar_aba_especialista(self):
        self.quadro_esp_autenticacao = tk.Frame(self.aba_especialista, bg=COR_FUNDO)
        self.quadro_esp_autenticacao.pack(fill="both", expand=True)

        # Cartão de Login do Especialista
        self.caixa_login_esp = self._criar_cartao(self.quadro_esp_autenticacao, width=480, height=440, padx=36, pady=30)
        self.caixa_login_esp.pack_propagate(False)

        tk.Label(
            self.caixa_login_esp,
            text="Acesso ao Consultório",
            font=("Arial", 20, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(6, 4))

        tk.Label(
            self.caixa_login_esp,
            text="Entre com suas credenciais médicas para chamar pacientes.",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(pady=(0, 22))

        tk.Label(self.caixa_login_esp, text="Usuário", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 4))
        self.campo_esp_usuario = tk.Entry(self.caixa_login_esp, font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_esp_usuario.pack(fill="x", ipady=7, pady=(0, 14))

        tk.Label(self.caixa_login_esp, text="Senha", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 4))
        self.campo_esp_senha = tk.Entry(self.caixa_login_esp, show="*", font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_esp_senha.pack(fill="x", ipady=7, pady=(0, 22))

        tk.Button(
            self.caixa_login_esp,
            text="Entrar no Consultório",
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            activebackground=COR_AZUL_ESCURO,
            font=("Arial", 12, "bold"),
            relief="flat",
            pady=12,
            cursor="hand2",
            command=self._login_especialista
        ).pack(fill="x")

        rodape_login_esp = tk.Frame(self.caixa_login_esp, bg=COR_CARD)
        rodape_login_esp.pack(pady=(20, 0))

        tk.Label(
            rodape_login_esp,
            text="Ainda não tem cadastro?",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(side="left")

        tk.Button(
            rodape_login_esp,
            text="Clique aqui para cadastrar",
            font=("Arial", 11, "bold", "underline"),
            bg=COR_CARD,
            fg=COR_AZUL_PRIMARIO,
            activebackground=COR_CARD,
            activeforeground=COR_AZUL_ESCURO,
            bd=0,
            cursor="hand2",
            command=self._mostrar_cadastro_esp
        ).pack(side="left", padx=(4, 0))

        # Cartão de Cadastro de Novo Especialista 
        self.caixa_cadastro_esp = self._criar_cartao(self.quadro_esp_autenticacao, width=500, height=580, padx=36, pady=20)
        self.caixa_cadastro_esp.pack_propagate(False)

        tk.Label(
            self.caixa_cadastro_esp,
            text="Novo Especialista",
            font=("Arial", 19, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(2, 2))

        tk.Label(
            self.caixa_cadastro_esp,
            text="Limite de até 3 profissionais por especialidade.",
            font=("Arial", 10),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(pady=(0, 12))

        tk.Label(self.caixa_cadastro_esp, text="Nome Completo", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.campo_cad_esp_nome = tk.Entry(self.caixa_cadastro_esp, font=("Arial", 11), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_esp_nome.pack(fill="x", ipady=5, pady=(2, 8))

        tk.Label(self.caixa_cadastro_esp, text="Usuário de Acesso", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.campo_cad_esp_usuario = tk.Entry(self.caixa_cadastro_esp, font=("Arial", 11), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_esp_usuario.pack(fill="x", ipady=5, pady=(2, 8))

        tk.Label(self.caixa_cadastro_esp, text="Senha", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.campo_cad_esp_senha = tk.Entry(self.caixa_cadastro_esp, show="*", font=("Arial", 11), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_esp_senha.pack(fill="x", ipady=5, pady=(2, 8))

        tk.Label(self.caixa_cadastro_esp, text="Consultório (Ex: Consultório 01)", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.campo_cad_esp_consultorio = tk.Entry(self.caixa_cadastro_esp, font=("Arial", 11), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_esp_consultorio.pack(fill="x", ipady=5, pady=(2, 8))

        tk.Label(self.caixa_cadastro_esp, text="Especialidade", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 10, "bold")).pack(anchor="w")
        self.seletor_cad_esp = ttk.Combobox(self.caixa_cadastro_esp, state="readonly", font=("Arial", 11))
        self.seletor_cad_esp.pack(fill="x", pady=(2, 14))

        tk.Button(
            self.caixa_cadastro_esp,
            text="Concluir Cadastro",
            bg=COR_AZUL_ESCURO,
            fg="white",
            activebackground=COR_AZUL_MEDIO,
            font=("Arial", 12, "bold"),
            relief="flat",
            pady=11,
            cursor="hand2",
            command=self._cadastrar_novo_especialista
        ).pack(fill="x")

        rodape_cad_esp = tk.Frame(self.caixa_cadastro_esp, bg=COR_CARD)
        rodape_cad_esp.pack(pady=(14, 0))

        tk.Label(
            rodape_cad_esp,
            text="Já possui cadastro?",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(side="left")

        tk.Button(
            rodape_cad_esp,
            text="Voltar para o login",
            font=("Arial", 11, "bold", "underline"),
            bg=COR_CARD,
            fg=COR_AZUL_PRIMARIO,
            activebackground=COR_CARD,
            activeforeground=COR_AZUL_ESCURO,
            bd=0,
            cursor="hand2",
            command=self._mostrar_login_esp
        ).pack(side="left", padx=(4, 0))

        self._mostrar_login_esp()

        # Frame que será exibido após o especialista fazer login
        self.quadro_esp_trabalho = tk.Frame(self.aba_especialista, bg=COR_FUNDO)

    def _mostrar_login_esp(self):
        self.caixa_cadastro_esp.place_forget()
        self.caixa_login_esp.place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_cadastro_esp(self):
        self.caixa_login_esp.place_forget()
        self.caixa_cadastro_esp.place(relx=0.5, rely=0.5, anchor="center")

    def _montar_painel_trabalho_especialista(self):
        # Limpa e monta a tela de atendimento do médico logado
        for componente in self.quadro_esp_trabalho.winfo_children():
            componente.destroy()

        profissional = self.especialista_logado["profissional"]
        cabecalho = self._criar_cartao(self.quadro_esp_trabalho, padx=22, pady=14)
        cabecalho.pack(fill="x", pady=(10, 12))

        tk.Label(
            cabecalho,
            text=f"Dr(a). {profissional['nome_especialista']}",
            font=("Arial", 15, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(side="left")

        tk.Label(
            cabecalho,
            text=f"   •   {profissional['especialidade_nome']}   •   {profissional['numero_consultorio']}",
            font=("Arial", 12),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(side="left")

        tk.Button(
            cabecalho,
            text="Encerrar Sessão",
            bg=COR_PERIGO,
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._logout_especialista
        ).pack(side="right")

        corpo = self._criar_cartao(self.quadro_esp_trabalho, padx=30, pady=28)
        corpo.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(
            corpo,
            text="SALA DE ATENDIMENTO ATIVA",
            font=("Arial", 10, "bold"),
            bg=COR_AZUL_CLARO,
            fg=COR_AZUL_ESCURO,
            padx=14,
            pady=5
        ).pack(pady=(10, 16))

        self.rotulo_esp_senha_atual = tk.Label(
            corpo,
            text="Nenhuma senha chamada no momento",
            font=("Arial", 24, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        )
        self.rotulo_esp_senha_atual.pack(pady=14)

        self.rotulo_esp_status_atual = tk.Label(
            corpo,
            text="Status: Aguardando chamada",
            font=("Arial", 13),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        )
        self.rotulo_esp_status_atual.pack(pady=(0, 30))

        # Botões de controle do fluxo da consulta
        botoes = tk.Frame(corpo, bg=COR_CARD)
        botoes.pack(pady=10)

        tk.Button(
            botoes,
            text="1. Chamar Próxima Senha",
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=18,
            pady=14,
            cursor="hand2",
            command=self._esp_chamar_proxima
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            botoes,
            text="2. Iniciar Atendimento",
            bg=COR_AZUL_MEDIO,
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=18,
            pady=14,
            cursor="hand2",
            command=lambda: self._esp_mudar_status("EM_ATENDIMENTO")
        ).grid(row=0, column=1, padx=8)

        tk.Button(
            botoes,
            text="3. Finalizar Consulta",
            bg=COR_AZUL_ESCURO,
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=18,
            pady=14,
            cursor="hand2",
            command=lambda: self._esp_mudar_status("FINALIZADO")
        ).grid(row=0, column=2, padx=8)

        tk.Button(
            botoes,
            text="Marcar Ausência",
            bg=COR_PERIGO,
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=18,
            pady=14,
            cursor="hand2",
            command=lambda: self._esp_mudar_status("AUSENTE")
        ).grid(row=0, column=3, padx=8)

    def _login_especialista(self):
        # Valida usuário/senha e abre a sala de atendimento
        try:
            usuario = autenticar_usuario(self.campo_esp_usuario.get(), self.campo_esp_senha.get(), "ESPECIALISTA")
            self.especialista_logado = usuario
            self.quadro_esp_autenticacao.pack_forget()
            self._montar_painel_trabalho_especialista()
            self.quadro_esp_trabalho.pack(fill="both", expand=True)
        except Exception as erro:
            messagebox.showerror("Erro de Autenticação", str(erro))

    def _logout_especialista(self):
        # Encerra a sessão do médico e volta para a tela de login
        self.especialista_logado = None
        self.senha_em_atendimento = None
        self.quadro_esp_trabalho.pack_forget()
        self._mostrar_login_esp()
        self.quadro_esp_autenticacao.pack(fill="both", expand=True)

    def _cadastrar_novo_especialista(self):
        # Salva um novo médico no banco e limpa os campos do formulário
        esp_nome = self.seletor_cad_esp.get()
        if not esp_nome:
            messagebox.showwarning("Aviso", "Selecione uma especialidade.")
            return
        try:
            cadastrar_especialista(
                self.campo_cad_esp_nome.get(),
                self.campo_cad_esp_usuario.get(),
                self.campo_cad_esp_senha.get(),
                self.campo_cad_esp_consultorio.get(),
                self.mapa_especialidades[esp_nome]
            )
            messagebox.showinfo("Sucesso", "Especialista cadastrado! Agora você já pode fazer login.")
            self.campo_cad_esp_nome.delete(0, tk.END)
            self.campo_cad_esp_usuario.delete(0, tk.END)
            self.campo_cad_esp_senha.delete(0, tk.END)
            self.campo_cad_esp_consultorio.delete(0, tk.END)
            self.atualizar_tudo()
            self._mostrar_login_esp()
        except Exception as erro:
            messagebox.showerror("Erro no Cadastro", str(erro))

    def _esp_chamar_proxima(self):
        # Puxa o paciente mais prioritário da especialidade do médico
        if self.senha_em_atendimento:
            messagebox.showwarning("Atendimento em curso", "Finalize ou marque ausência da senha atual antes de chamar a próxima.")
            return
        profissional = self.especialista_logado["profissional"]
        try:
            chamada = self.gerenciador.chamar_proxima(profissional["especialidade_id"], profissional["numero_consultorio"])
            self.senha_em_atendimento = chamada
            self.ultimas_chamadas_painel.insert(0, chamada)
            self.ultimas_chamadas_painel = self.ultimas_chamadas_painel[:7]
            self.rotulo_esp_senha_atual.config(text=f"Senha: {chamada['codigo']} ({chamada['categoria']})")
            self.rotulo_esp_status_atual.config(text="Status: CHAMADA — Aguardando paciente entrar no consultório")
            self.atualizar_tudo()
            messagebox.showinfo("Chamada Realizada", f"Senha {chamada['codigo']} encaminhada para {profissional['numero_consultorio']}.")
        except IndexError as erro:
            messagebox.showinfo("Fila Vazia", str(erro))
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    def _esp_mudar_status(self, status):
        # Atualiza a etapa do atendimento 
        if not self.senha_em_atendimento:
            messagebox.showwarning("Aviso", "Nenhuma senha foi chamada ainda.")
            return
        codigo = self.senha_em_atendimento["codigo"]
        self.gerenciador.atualizar_status_atendimento(codigo, status)
        if status == "EM_ATENDIMENTO":
            self.rotulo_esp_status_atual.config(text="Status: EM ATENDIMENTO")
        else:
            self.rotulo_esp_senha_atual.config(text="Nenhuma senha chamada no momento")
            self.rotulo_esp_status_atual.config(text=f"Última senha ({codigo}) marcada como {status}.")
            self.senha_em_atendimento = None
        self.atualizar_tudo()

    # ADMINISTRAÇÃO 

    def _montar_aba_adm(self):
        self.quadro_adm_autenticacao = tk.Frame(self.aba_adm, bg=COR_FUNDO)
        self.quadro_adm_autenticacao.pack(fill="both", expand=True)

        # Cartão de Login do Administrador
        self.caixa_login_adm = self._criar_cartao(self.quadro_adm_autenticacao, width=480, height=440, padx=36, pady=30)
        self.caixa_login_adm.pack_propagate(False)

        tk.Label(
            self.caixa_login_adm,
            text="Acesso Administrativo",
            font=("Arial", 20, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(6, 4))

        tk.Label(
            self.caixa_login_adm,
            text="Padrão de primeiro acesso: admin / 123",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(pady=(0, 22))

        tk.Label(self.caixa_login_adm, text="Usuário ADM", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 4))
        self.campo_adm_usuario = tk.Entry(self.caixa_login_adm, font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_adm_usuario.pack(fill="x", ipady=7, pady=(0, 14))

        tk.Label(self.caixa_login_adm, text="Senha", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 4))
        self.campo_adm_senha = tk.Entry(self.caixa_login_adm, show="*", font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_adm_senha.pack(fill="x", ipady=7, pady=(0, 22))

        tk.Button(
            self.caixa_login_adm,
            text="Acessar Painel ADM",
            bg=COR_AZUL_ESCURO,
            fg="white",
            activebackground=COR_AZUL_MEDIO,
            font=("Arial", 12, "bold"),
            relief="flat",
            pady=12,
            cursor="hand2",
            command=self._login_adm
        ).pack(fill="x")

        rodape_login_adm = tk.Frame(self.caixa_login_adm, bg=COR_CARD)
        rodape_login_adm.pack(pady=(20, 0))

        tk.Label(
            rodape_login_adm,
            text="Ainda não tem cadastro?",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(side="left")

        tk.Button(
            rodape_login_adm,
            text="Cadastrar novo gestor",
            font=("Arial", 11, "bold", "underline"),
            bg=COR_CARD,
            fg=COR_AZUL_PRIMARIO,
            activebackground=COR_CARD,
            activeforeground=COR_AZUL_ESCURO,
            bd=0,
            cursor="hand2",
            command=self._mostrar_cadastro_adm
        ).pack(side="left", padx=(4, 0))

        # Cartão de Cadastro de Novo Administrador
        self.caixa_cadastro_adm = self._criar_cartao(self.quadro_adm_autenticacao, width=480, height=515, padx=36, pady=24)
        self.caixa_cadastro_adm.pack_propagate(False)

        tk.Label(
            self.caixa_cadastro_adm,
            text="Novo Administrador",
            font=("Arial", 20, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(pady=(4, 4))

        tk.Label(
            self.caixa_cadastro_adm,
            text="Cadastre outros gestores para administrar a clínica.",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(pady=(0, 18))

        tk.Label(self.caixa_cadastro_adm, text="Nome Completo", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w")
        self.campo_cad_adm_nome = tk.Entry(self.caixa_cadastro_adm, font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_adm_nome.pack(fill="x", ipady=6, pady=(2, 12))

        tk.Label(self.caixa_cadastro_adm, text="Usuário", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w")
        self.campo_cad_adm_usuario = tk.Entry(self.caixa_cadastro_adm, font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_adm_usuario.pack(fill="x", ipady=6, pady=(2, 12))

        tk.Label(self.caixa_cadastro_adm, text="Senha", bg=COR_CARD, fg=COR_AZUL_ESCURO, font=("Arial", 11, "bold")).pack(anchor="w")
        self.campo_cad_adm_senha = tk.Entry(self.caixa_cadastro_adm, show="*", font=("Arial", 12), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        self.campo_cad_adm_senha.pack(fill="x", ipady=6, pady=(2, 20))

        tk.Button(
            self.caixa_cadastro_adm,
            text="Concluir Cadastro",
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            activebackground=COR_AZUL_ESCURO,
            font=("Arial", 12, "bold"),
            relief="flat",
            pady=12,
            cursor="hand2",
            command=self._cadastrar_novo_adm
        ).pack(fill="x")

        rodape_cad_adm = tk.Frame(self.caixa_cadastro_adm, bg=COR_CARD)
        rodape_cad_adm.pack(pady=(16, 0))

        tk.Label(
            rodape_cad_adm,
            text="Já possui cadastro?",
            font=("Arial", 11),
            bg=COR_CARD,
            fg=COR_TEXTO_SUAVE
        ).pack(side="left")

        tk.Button(
            rodape_cad_adm,
            text="Voltar para o login",
            font=("Arial", 11, "bold", "underline"),
            bg=COR_CARD,
            fg=COR_AZUL_PRIMARIO,
            activebackground=COR_CARD,
            activeforeground=COR_AZUL_ESCURO,
            bd=0,
            cursor="hand2",
            command=self._mostrar_login_adm
        ).pack(side="left", padx=(4, 0))

        self._mostrar_login_adm()

        # Frame que será exibido após o administrador fazer login
        self.quadro_adm_painel = tk.Frame(self.aba_adm, bg=COR_FUNDO)

    def _mostrar_login_adm(self):
        self.caixa_cadastro_adm.place_forget()
        self.caixa_login_adm.place(relx=0.5, rely=0.5, anchor="center")

    def _mostrar_cadastro_adm(self):
        self.caixa_login_adm.place_forget()
        self.caixa_cadastro_adm.place(relx=0.5, rely=0.5, anchor="center")

    def _montar_painel_gestao_adm(self):
        # Reconstrói as tabelas administrativas com os dados atualizados do banco
        for componente in self.quadro_adm_painel.winfo_children():
            componente.destroy()

        topo = self._criar_cartao(self.quadro_adm_painel, padx=18, pady=10)
        topo.pack(fill="x", pady=(10, 8))

        tk.Label(
            topo,
            text=f"Gestão da Clínica — Olá, {self.adm_logado['nome']}",
            font=("Arial", 14, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(side="left")

        tk.Button(
            topo,
            text="Sair",
            bg=COR_PERIGO,
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=16,
            pady=5,
            cursor="hand2",
            command=self._logout_adm
        ).pack(side="right")

        meio = tk.Frame(self.quadro_adm_painel, bg=COR_FUNDO)
        meio.pack(fill="both", expand=True, pady=4)

        # Bloco esquerdo: cadastro e ativação/desativação de especialidades
        caixa_esp = self._criar_cartao(meio, padx=14, pady=10)
        caixa_esp.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            caixa_esp,
            text="Especialidades Médicas",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 8))

        formulario_esp = tk.Frame(caixa_esp, bg=COR_CARD)
        formulario_esp.pack(fill="x", pady=(0, 8))

        tk.Label(formulario_esp, text="Nome:", bg=COR_CARD, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=2)
        campo_nova_esp = tk.Entry(formulario_esp, width=16, font=("Arial", 10), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        campo_nova_esp.grid(row=0, column=1, ipady=3, padx=4)

        tk.Label(formulario_esp, text="Sigla:", bg=COR_CARD, font=("Arial", 10, "bold")).grid(row=0, column=2, padx=2)
        campo_nova_sigla = tk.Entry(formulario_esp, width=5, font=("Arial", 10), bg=COR_FUNDO, relief="flat", highlightbackground=COR_BORDA, highlightthickness=2)
        campo_nova_sigla.grid(row=0, column=3, ipady=3, padx=4)

        def salvar_esp():
            try:
                cadastrar_especialidade(campo_nova_esp.get(), campo_nova_sigla.get())
                campo_nova_esp.delete(0, tk.END)
                campo_nova_sigla.delete(0, tk.END)
                self.atualizar_tudo()
                messagebox.showinfo("Sucesso", "Especialidade cadastrada!")
            except Exception as erro:
                messagebox.showerror("Erro", str(erro))

        tk.Button(
            formulario_esp,
            text="+ Adicionar",
            bg=COR_AZUL_PRIMARIO,
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=salvar_esp
        ).grid(row=0, column=4, padx=4)

        tabela_esp = ttk.Treeview(caixa_esp, columns=("id", "nome", "sigla", "status"), show="headings", height=3)
        tabela_esp.heading("id", text="ID")
        tabela_esp.heading("nome", text="Especialidade")
        tabela_esp.heading("sigla", text="Sigla")
        tabela_esp.heading("status", text="Status")
        tabela_esp.column("id", width=40, anchor="center")
        tabela_esp.column("nome", width=145, anchor="center")
        tabela_esp.column("sigla", width=55, anchor="center")
        tabela_esp.column("status", width=80, anchor="center")
        tabela_esp.pack(fill="both", expand=True)

        for esp in listar_especialidades(apenas_ativas=False):
            tabela_esp.insert("", tk.END, values=(esp["id"], esp["nome"], esp["sigla"], esp["status"]))

        def alternar_esp():
            selecao = tabela_esp.selection()
            if not selecao:
                messagebox.showwarning("Aviso", "Selecione uma especialidade na tabela.")
                return
            esp_id = tabela_esp.item(selecao[0])["values"][0]
            try:
                alternar_status_especialidade(esp_id)
                self.atualizar_tudo()
            except Exception as erro:
                messagebox.showerror("Erro", str(erro))

        tk.Button(
            caixa_esp,
            text="Ativar / Desativar Selecionada",
            bg=COR_AZUL_CLARO,
            fg=COR_AZUL_ESCURO,
            font=("Arial", 10, "bold"),
            relief="flat",
            pady=7,
            cursor="hand2",
            command=alternar_esp
        ).pack(fill="x", pady=(8, 0))

        # Bloco direito: gerenciamento de médicos e seus consultórios
        caixa_prof = self._criar_cartao(meio, padx=14, pady=10)
        caixa_prof.pack(side="right", fill="both", expand=True, padx=(6, 0))

        tk.Label(
            caixa_prof,
            text="Consultórios e Especialistas (Máx. 3 / Esp.)",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 8))

        tabela_prof = ttk.Treeview(caixa_prof, columns=("id", "esp", "nome", "cons"), show="headings", height=4)
        tabela_prof.heading("id", text="ID")
        tabela_prof.heading("esp", text="Especialidade")
        tabela_prof.heading("nome", text="Especialista")
        tabela_prof.heading("cons", text="Consultório")
        tabela_prof.column("id", width=40, anchor="center")
        tabela_prof.column("esp", width=130, anchor="center")
        tabela_prof.column("nome", width=140, anchor="center")
        tabela_prof.column("cons", width=110, anchor="center")
        tabela_prof.pack(fill="both", expand=True)

        for prof in listar_profissionais():
            tabela_prof.insert("", tk.END, values=(prof["id"], prof["especialidade_nome"], prof["nome_especialista"], prof["numero_consultorio"]))

        botoes_prof = tk.Frame(caixa_prof, bg=COR_CARD)
        botoes_prof.pack(fill="x", pady=(8, 0))

        def editar_cons():
            selecao = tabela_prof.selection()
            if not selecao:
                messagebox.showwarning("Aviso", "Selecione um especialista na tabela.")
                return
            valores = tabela_prof.item(selecao[0])["values"]
            novo = simpledialog.askstring("Alterar Consultório", f"Novo consultório para {valores[2]}:", initialvalue=valores[3])
            if novo:
                try:
                    atualizar_consultorio_especialista(valores[0], novo)
                    self.atualizar_tudo()
                except Exception as erro:
                    messagebox.showerror("Erro", str(erro))

        def excluir_prof():
            selecao = tabela_prof.selection()
            if not selecao:
                messagebox.showwarning("Aviso", "Selecione um especialista na tabela.")
                return
            valores = tabela_prof.item(selecao[0])["values"]
            if messagebox.askyesno("Confirmar", f"Remover {valores[2]} ({valores[3]})?"):
                remover_especialista(valores[0])
                self.atualizar_tudo()

        tk.Button(
            botoes_prof,
            text="Alterar Consultório",
            bg=COR_AZUL_MEDIO,
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            pady=7,
            cursor="hand2",
            command=editar_cons
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            botoes_prof,
            text="Remover Especialista",
            bg=COR_PERIGO,
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            pady=7,
            cursor="hand2",
            command=excluir_prof
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        # Parte inferior: log completo dos atendimentos realizados
        caixa_historico = self._criar_cartao(self.quadro_adm_painel, padx=14, pady=10)
        caixa_historico.pack(fill="both", expand=True, pady=(6, 4))

        tk.Label(
            caixa_historico,
            text="Histórico Recente de Atendimentos",
            font=("Arial", 13, "bold"),
            bg=COR_CARD,
            fg=COR_AZUL_ESCURO
        ).pack(anchor="w", pady=(0, 6))

        tabela_historico = ttk.Treeview(
            caixa_historico,
            columns=("senha", "esp", "cat", "cons", "emissao", "chamada", "inicio", "fim", "status"),
            show="headings",
            height=4
        )
        cabecalhos = {
            "senha": "Senha", "esp": "Especialidade", "cat": "Prioridade",
            "cons": "Consultório", "emissao": "Emissão", "chamada": "Chamada",
            "inicio": "Início", "fim": "Fim", "status": "Status"
        }
        for chave, titulo in cabecalhos.items():
            tabela_historico.heading(chave, text=titulo)
            tabela_historico.column(chave, anchor="center", width=105)
        tabela_historico.pack(fill="both", expand=True)

        for registro in listar_historico():
            tabela_historico.insert("", tk.END, values=(
                registro["senha_codigo"], registro["especialidade_nome"], registro["categoria_prioridade"],
                registro["consultorio"] or "-", registro["horario_emissao"], registro["horario_chamada"] or "-",
                registro["horario_inicio"] or "-", registro["horario_fim"] or "-", registro["status_final"]
            ))

    def _login_adm(self):
        # Valida acesso do administrador e abre o painel de gestão
        try:
            self.adm_logado = autenticar_usuario(self.campo_adm_usuario.get(), self.campo_adm_senha.get(), "ADM")
            self.quadro_adm_autenticacao.pack_forget()
            self._montar_painel_gestao_adm()
            self.quadro_adm_painel.pack(fill="both", expand=True)
        except Exception as erro:
            messagebox.showerror("Erro de Login", str(erro))

    def _logout_adm(self):
        # Sai do painel administrativo e volta para a tela de login
        self.adm_logado = None
        self.quadro_adm_painel.pack_forget()
        self._mostrar_login_adm()
        self.quadro_adm_autenticacao.pack(fill="both", expand=True)

    def _cadastrar_novo_adm(self):
        # Cadastra um novo gestor no sistema
        try:
            cadastrar_adm(self.campo_cad_adm_nome.get(), self.campo_cad_adm_usuario.get(), self.campo_cad_adm_senha.get())
            messagebox.showinfo("Sucesso", "Novo administrador cadastrado! Agora você já pode fazer login.")
            self.campo_cad_adm_nome.delete(0, tk.END)
            self.campo_cad_adm_usuario.delete(0, tk.END)
            self.campo_cad_adm_senha.delete(0, tk.END)
            self._mostrar_login_adm()
        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    # ATUALIZAÇÃO GLOBAL DA INTERFACE
    
    def atualizar_tudo(self):
        # Busca especialidades ativas e recria os botões do autoatendimento
        especialidades = listar_especialidades(apenas_ativas=True)
        self.mapa_especialidades = {esp["nome"]: esp["id"] for esp in especialidades}
        nomes_esp = list(self.mapa_especialidades.keys())

        for componente in self.quadro_botoes_esp.winfo_children():
            componente.destroy()
        for esp in especialidades:
            tk.Button(
                self.quadro_botoes_esp,
                text=f"{esp['nome']}   →",
                font=("Arial", 13, "bold"),
                bg=COR_AZUL_MEDIO,
                fg="white",
                activebackground="#125CA1",
                activeforeground="white",
                relief="flat",
                pady=14,
                cursor="hand2",
                command=lambda nome=esp["nome"]: self._selecionar_especialidade_paciente(nome)
            ).pack(fill="x", pady=6)

        # Atualiza a lista de especialidades no cadastro de especialistas
        self.seletor_cad_esp["values"] = nomes_esp
        if nomes_esp and self.seletor_cad_esp.get() not in nomes_esp:
            self.seletor_cad_esp.set(nomes_esp[0])

        # Atualiza o destaque principal do Painel de Espera com a última senha chamada
        if self.gerenciador.ultima_chamada:
            ultima = self.gerenciador.ultima_chamada
            self.rotulo_alerta_chamada.config(
                text="NOVA SENHA CHAMADA — DIRIJA-SE AO CONSULTÓRIO",
                bg=COR_AZUL_VIBRANTE,
                fg=COR_AZUL_ESCURO
            )
            self.rotulo_painel_senha.config(text=ultima["codigo"])
            self.rotulo_painel_consultorio.config(text=f"Destino: {ultima['consultorio']}")
            self.rotulo_painel_destino.config(
                text=f"Especialidade: {ultima['especialidade_nome']}\nCategoria: {ultima['categoria']}"
            )

        # Atualiza a tabela de últimas senhas chamadas
        for item in self.tabela_ultimas.get_children():
            self.tabela_ultimas.delete(item)
        for chamada in self.ultimas_chamadas_painel[1:7]:
            self.tabela_ultimas.insert("", tk.END, values=(chamada["codigo"], chamada["consultorio"], chamada["especialidade_nome"], chamada["categoria"]))

        # Recalcula o total de pacientes na fila e o tempo estimado de espera
        resumos_tempo = []
        total_geral = 0
        for esp in especialidades:
            tempo = self.gerenciador.calcular_tempo_espera_fila(esp["id"])
            qtd = len(self.gerenciador.listar_fila_ordenada(esp["id"]))
            total_geral += qtd
            resumos_tempo.append(f"{esp['nome']}: {qtd} aguardando (~{tempo} min)")

        self.rotulo_total_aguardando.config(text=f"Total de pacientes aguardando na clínica: {total_geral}")
        self.rotulo_quadro_tempos.config(text="   •   ".join(resumos_tempo))

        # Atualiza a tabela de próximos pacientes ordenados por prioridade
        for item in self.tabela_espera.get_children():
            self.tabela_espera.delete(item)

        for esp in especialidades:
            fila_ordenada = self.gerenciador.listar_fila_ordenada(esp["id"])
            for indice, senha in enumerate(fila_ordenada):
                espera_min = indice * 30
                self.tabela_espera.insert("", tk.END, values=(
                    senha["codigo"],
                    senha["especialidade_nome"],
                    senha["tipo"],
                    senha["categoria"],
                    f"{espera_min} min"
                ))

        # Se o admin estiver logado, recarrega as tabelas administrativas também
        if self.adm_logado:
            self._montar_painel_gestao_adm()