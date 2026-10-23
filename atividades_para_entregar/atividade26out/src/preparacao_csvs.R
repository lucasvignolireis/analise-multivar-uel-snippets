gerar_tabela <- function(arquivos, nomes_colunas, arquivo_saida) {
  colunas <- lapply(arquivos, function(f) read.csv(f, header = FALSE)[[1]])
  names(colunas) <- nomes_colunas
  
  # Completa com NA se os arquivos tiverem tamanhos diferentes
  n <- max(lengths(colunas))
  colunas <- lapply(colunas, function(x) { length(x) <- n; x })
  
  df <- as.data.frame(colunas)
  
  # Coluna Amostra: 1, 2, 3, ...
  df <- cbind(Amostra = seq_len(nrow(df)), df)
  
  write.csv(df, arquivo_saida, row.names = FALSE)
  return(df)
}

# Ordem desejada: V;Cr;Fe;Mo;W
nomes <- c("V", "Cr", "Fe", "Mo", "W")

# Calibração
arquivos_calib <- c("YcalibV.csv", "YcalibCr.csv", "YcalibFe.csv",
                    "YcalibMo.csv", "YcalibW.csv")
df_calib <- gerar_tabela(arquivos_calib, nomes, "Ycalib.csv")

# Validação
arquivos_valid <- c("YvalidV.csv", "YvalidCr.csv", "YvalidFe.csv",
                    "YvalidMo.csv", "YvalidW.csv")
df_valid <- gerar_tabela(arquivos_valid, nomes, "Yvalid.csv")