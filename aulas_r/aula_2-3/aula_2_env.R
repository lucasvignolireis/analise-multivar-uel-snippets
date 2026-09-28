#script a ser rodado só da primeira vez, para instalar os pacotes só pro seu projeto

renv::init() # inicializa o gerenciador de pacotes

# lista de pacotes que vão ser utilizados nesse script
packages <- c(
  "fBasics",
  "readr",
  "fields",
  "dplyr",
  "readxl",
  "tidyr",
  "magrittr",
  "stats"
)

renv::install(packages)
renv::snapshot()
