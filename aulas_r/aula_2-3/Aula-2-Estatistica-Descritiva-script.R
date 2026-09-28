#script para Estatistica Descritiva - JV
install.packages("fields")
install.packages("fBasics")
library(fBasics)
library(readr)
library(fields)
library(dplyr)
library(readxl)
library(xlsx)
library(tidyr)
library(magrittr)

#definindo diretorio
setwd("D:/MESTRADO/tutoriais R/dados para aulas")

#importando dados (variaveis devem estar nas colunas e nomes nas linhas)
dados <- read.csv("dados arroio boavista.CSV",sep  = ";") #se os dados forem .scv
#dados <- read_excel("dados arroio boavista.xlsx") %>% as.data.frame() #se os dados forem no formato de planilhas do excel

#vamos utilizar o pacote dplyr para obter a estatistica descritiva
#come?aremos definindo agrupamentos selecionados pela fun??o group_by

EstDisc <- group_by(dados, Cultura)

#agrupando mudamos a classe dos dados, agora s?o do tipo tibble
#essa fun??o nao muda os dados, apenas faz uma marca??o segundo as variaveis
#os parametros estatisticos serao calculados pela fun??o summarise

#mean quer dizer a media, basta entao escolher a variavel. Nesse caso vamos ter a m?dia das amostras agrupadas segundo o manejo e a cultura
#isso foi definido pela fun??o group_by
#basta fazer o mesmo para os demais parametros de estatistica descritiva

Resumo <- summarise(EstDisc, Media=mean(Fe), 
                    Mediana=median((Fe)),
                    Variancia=var((Fe)),
                    DesvPad = sd((Fe)),
                    Maximo=max((Fe)),
                    Minimo=min(((Fe))),
                    Q25=quantile((Fe), probs = 0.25),
                    Q75=quantile((Fe), probs = 0.75),
                    Curtose=kurtosis((Fe)), 
                    Assimetria = skewness((Fe)))

#para obter a esatistica descritiva de todas as colunas em um unico comando, vamos usar a função across
#A função across() permite que você especifique quais colunas deseja aplicar uma mesma função.

Resumo <- EstDisc %>% summarise(across(everything(), 
                                       list(Media=mean, 
                                            Mediana=median,
                                            Variancia=var,
                                            DesvPad = sd,
                                            Maximo=max,
                                            Minimo=min,
                                            Q25 = ~quantile(., probs = 0.25), 
                                            Q75 = ~quantile(., probs = 0.75),
                                            Curtose=kurtosis, 
                                            Assimetria = skewness))) 

#para melhor organizar, vamos transpor o data.frame Resumo
Resumo <- t(Resumo) %>% as.data.frame()

View(Resumo)
#Ja podemos exportar para o diret?rio o arquivo em formato .csv

write.table(Resumo, file = "Resumo Estatistico.csv", sep = ";")#para salvar em .csc
write.xlsx(Resumo, "Resumo Estatistico.xlsx")#para salvar em xlsx

#correlação e covariância
# você pode calcular a covariância e a correlação entre duas variáveis usando as funções "cov()" e "cor()".

cov(dados$Al,dados$Fe)#covariancia entre as concentrações de aluminio e de ferro
cor(dados$Al,dados$Fe)#correlação entre as concentrações de aluminio e de ferro
