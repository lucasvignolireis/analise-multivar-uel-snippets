#script a ser rodado só da primeira vez, para instalar os pacotes só pro seu projeto

renv::init() # inicializa o gerenciador de pacotes

# lista de pacotes que vão ser utilizados nesse script
packages <- c(
  "readr",    # para importar csv
  "readxl",   # para arquivos do excel
  "ggplot2",  # para plotagem
  "magrittr",
  "tidyr"
)

renv::install(packages)
renv::snapshot()
