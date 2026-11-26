#importa a biblioteca tkinter para criar a interface gráfica do usuário
import tkinter as tk
# importa a função inicializar_banco do arquivo banco_dados
from banco_dados import inicializar_banco
# importa a classe AplicacaoClinica do arquivo interface
from interface import AplicacaoClinica

# Define a função principal que inicializa o banco de dados, cria a janela principal da aplicação e inicia o loop principal do tkinter
def principal():
    # Inicializa o banco de dados
    inicializar_banco()
    # Cria a janela principal do tkinter
    janela_principal = tk.Tk()
    # Cria uma instância da classe AplicacaoClinica, passando a janela principal como argumento
    aplicacao = AplicacaoClinica(janela_principal)
    # Inicia o loop principal do tkinter, que mantém a janela aberta e responde a eventos
    janela_principal.mainloop()

# Verifica se o script está sendo executado diretamente 
if __name__ == "__main__":
    principal()