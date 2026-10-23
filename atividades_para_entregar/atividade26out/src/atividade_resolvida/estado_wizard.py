def estado_inicial_wizard():
    return {
        "etapa_atual": "carregamento",
        "ordem": ["carregamento", "tabela", "relatorio"],
        "passos": {
            "carregamento": {
                "titulo": "Carregamento dos dados",
                "estado": "vazio",   # vazio | em_processo | preenchido
                "conf": {
                    "path": "dados/",
                    "extensoes": ["csv", "tsv"],
                },
                "dados": {
                    "xvalid_path": None,
                    "xvalid_sep": ",",
                    "xcalib_path": None,
                    "xcalib_sep": ",",
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
                    "path_template": "",
                    "path_registro_automatico": None,
                },
                "dados": {
                    "arquivo_gerado": None,
                    "pronto_para_download": False,
                },
            },
        },
    }