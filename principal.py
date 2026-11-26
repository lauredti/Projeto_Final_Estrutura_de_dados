import tkinter as tk
from banco_dados import inicializar_banco
from interface import AplicacaoClinica


def principal():
    inicializar_banco()
    janela_principal = tk.Tk()
    aplicacao = AplicacaoClinica(janela_principal)
    janela_principal.mainloop()


if __name__ == "__main__":
    principal()