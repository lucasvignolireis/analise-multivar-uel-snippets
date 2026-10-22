def estado_inicial_wizard():
    return {
        "etapa_atual": "arquivo",

        "ordem": ["arquivo", "tabela", "relatorio"],
        "passos": {
            "arquivo": {
                "titulo": "Arquivo:",
                "estado": "vazio",   # vazio | em_processo | preenchido
                "conf": { # configuracoes do comportamento do script
                    "path": "dados/",
                    "extensoes": [
                        "csv",
                        "tsv"
                    ],
                },
                "dados": { # dados dinamicos, inclui preenchidos pelo usuário e também dados relevantes pro estado da interface específicos dessa etapa
                           # achei que não valia a pena subdividir ainda mais entre inputs do usuário e estado efemero da interface
                    "path_arquivo": None,
                    "separador": ",",
                },
            },
            "tabela": {
                "titulo": "Conferir os dados",
                "estado": "vazio",
                "conf": {},
                "dados": {
                    "cabecalho": [],
                    "n_linhas": 0, 
                    "colunas": [],
                },
            },
            "relatorio": {
                "titulo": "Relatório",
                "estado": "vazio",
                "conf": {
                    "path_template": "", # path de um template Typst (pensei em fazer algo com simples substituição de string com um dict)
                    "path_registro_automatico": None # preencher quando quiser que cada rodada seja registrada
                },
                "dados": {
                    "arquivo_gerado": None,
                    "pronto_para_download": False,
                },
            },
        },
    }