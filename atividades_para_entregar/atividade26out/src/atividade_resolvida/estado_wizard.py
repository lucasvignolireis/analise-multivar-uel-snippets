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
                    "xvalid_path": "Xvalid.csv",
                    "xvalid_sep": ",",
                    "xcalib_path": "Xcalib.csv",
                    "xcalib_sep": ",",
                    "yvalid_path": "Yvalid.csv",
                    "yvalid_sep": ",",
                    "ycalib_path": "Ycalib.csv",
                    "ycalib_sep": ",",
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
                    "elemento_analisado": "V",
                    "amostras_excluir_calib": "32",
                    "pls": {
                        "agregar": False,
                        "n_lvs": 4,
                        "centragem": "media",
                        "autoescalonamento": True,
                    },
                    "analises": {
                        "a": {
                            "nome": "PCA A (sem agregação, sem autoescalonamento)",
                            "agregar": False,
                            "n_pcs": 2,
                            "centragem": "media",
                            "autoescalonamento": False,
                        },
                        "b": {
                            "nome": "PCA B (sem agregação, com autoescalonamento)",
                            "agregar": False,
                            "n_pcs": 4,
                            "centragem": "media",
                            "autoescalonamento": True,
                        },
                        "c": {
                            "nome": "PCA C (com agregação, sem autoescalonamento)",
                            "agregar": True,
                            "n_pcs": 2,
                            "centragem": "media",
                            "autoescalonamento": False,
                        },
                        "d": {
                            "nome": "PCA D (com agregação, com autoescalonamento)",
                            "agregar": True,
                            "n_pcs": 4,
                            "centragem": "media",
                            "autoescalonamento": True,
                        },
                    }
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