#script para testes estatisticos - JV
library(readr)#para importar csv
library(readxl)#para arquivos do excel
library(magrittr)
library(stats)


#definindo diretorio
setwd("D:/MESTRADO/tutoriais R/dados para aulas")

#importando dados (variaveis devem estar nas colunas e nomes nas linhas)
dados <- read.csv('dados arroio boavista.CSV',sep  = ";") #se os dados forem .scv
dados <- read_excel("dados arroio boavista.xlsx") %>% as.data.frame() #se os dados forem no formato de planilhas do excel

#vamos utilizar uma funcao nativa do R para o teste t.
#ela se chama t.test

help("t.test")#para ler a respeito

#Existem dois tipos principais de testes de hipótese t de Student:

#1 -Teste t para uma amostra: Este teste é usado quando se deseja testar se a média de uma única amostra é igual a um determinado valor de referência. 
#É usado quando a variável em questão segue uma distribuição normal ou quando o tamanho da amostra é grande o suficiente para que o teorema do limite central possa ser aplicado. 
#O teste é chamado de teste t de uma amostra porque a média da amostra é comparada com um valor fixo, ao contrário do teste t de duas amostras, onde as médias de duas amostras são comparadas entre si.

#2 - Teste t para duas amostras: Este teste é usado para determinar se as médias de duas amostras são iguais ou diferentes. 
#Pode ser usado em casos onde se quer comparar duas amostras independentes para verificar se elas foram tiradas da mesma população ou para verificar se uma intervenção (tratamento) teve algum efeito em um grupo em relação ao outro. 
#O teste t para duas amostras pode ser aplicado quando as amostras são independentes ou pareadas (emparelhadas), como no caso de amostras antes e depois de um tratamento.


#Para realizar um teste t para uma amostra
#Use a função t.test() no objeto da amostra, especificando o valor de referência que você deseja testar com o argumento mu.
#por exemplo, para testar se a média das concentrações de Silicio é igual a 34.5

t.test(dados$Si, conf.level = 0.95, mu=30.0)
#a hipótese nula é que a média de dados é igual 34.5. 
#A hipótese alternativa é que é diferente
print("Se o pvalor for maior que 0.05 (95% de confianca) aceitamos a hipotese nula de que a media é igual a 34.5. Caso contrario, rejeitamos. A mesma analise pode ser feita agora comparando o tcalculado com o ttabelado, se tcalculado <tatbelado, aceitamos a hipotese nula. Caso contrario, rejeitamos")

#o teste que o R roda por padrao e o bicaudal, ou seja, tem como hipotese alternativa que as medias sao diferentes, mas nao estabelece uma direcao para essas diferencas.
#para testes unicaudais vamos adicionar mais um comando a funcao, o alternative = "greater" ou "less"
#greater para quando eu quero dizer que a média da minha amostra é maior que o valor de mu.less quando o inverso acontece.


#Para realizar um teste t para duas amostras (médias). 
#Use a função t.test() nos objetos das amostras, especificando que se trata de um teste t para duas amostras com o argumento paired (para amostras pareadas) ou var.equal = TRUE (para amostras independentes com variâncias iguais) ou var.equal = FALSE (para amostras independentes com variâncias diferentes)
#por padrao, a hipótese nula é de que as médias sao iguais

t.test(dados$Fe,dados$Si, conf.level = 0.95, var.equal=TRUE)
print("Se o pvalor for maior que 0.05 (95% de confianca) aceitamos a hipotese nula de que as media sao iguais. Caso contrario, rejeitamos. A mesma analise pode ser feita agora comparando o tcalculado com o ttabelado, se tcalculado <tatbelado, aceitamos a hipotese nula. Caso contrario, rejeitamos")

boxplot(dados$K, ylab="K (%)")

#o ~ indica que eu quero que a coluna de Fe seja separada pela coluna Cultura. Poderia tambem utilizar manejo. 
#o teste t pode ser usado para comparar grupos com variancia homogenea (iguais) ou heterogeneas (diferentes)
#var.equal = TRUE indica que as vari?ncias de cada grupo de amostras segundo o manejo ? igual (estatisticamente)
#var.equal = FALSE quando as variancias nao forem iguais
#df indica os graus de liberdade (nesse caso perdemos 2 gl por isso de 20 valores temos 18 g.l.)
#o teste t tem sempre a hipotese que a media do grupo A e igual do B (ou seja, a media da concentracao de Fe nas amostras de aveia e igual a de Tabaco)
#a hipotese alternativa e que ha diferenca entre os grupos (95%)
#a 95% de confianca o teste t. tambem fornece o intervalo.
#o comando paired = TRUE é usado para testes t-pareado. 


#teste F para comparacao de variancias. 
#vamos utilizar a razao entre as variancias A e B, se for = 1 elas sao iguais (hipotese nula)
#se a razao for diferente  de 1 elas sao diferentes (hipotese alternartiva)
#vamos mais uma vez verificar o pvalor. Se ele for maior que 0.05 (para 95% de conf) a hipotese nula e aceita. 
#vamos utilizar mais uma funcao nativa do R, a var.test

help("var.test")
#vamos testar se a variancia dos valores da concentra??o de Fe ? iguais aos de Al

var.test(dados$Fe,dados$Al, conf.level = 0.95)
print("Se o pvalor for maior que 0.05 (95% de confian?a) aceitamos a hipotese nula de que as medias sao iguais. Caso contrario, rejeitamos.A mesma analise pode ser feita agora comparando o Fcalculado com o Ftabelado, se Fcalculado < Ftabelado, aceitamos a hipotese nula. Caso contrario, rejeitamos")

#ou tambem, se F-calculado < F-tabelado, aceitamos a hipotese nula
#dessa forma, toda vez que formos fazer um teste t e conveniente considerar primeiro o teste F para testar a igualdade das variancias.

################################### 2 parte ##########################################################

#teste shapiro wilk para verificar se os dados seguem uma distribuicao normal
#hipotese nula = dados seguem a distribuicao normal
#hip altern = dados nao seguem a dist normal

shapiro.test(dados$Si)
#Estatística de teste (W): é o valor da estatística de teste calculada pelo teste de Shapiro-Wilk.
#Valor p (p-value): é o valor da probabilidade de obter um valor de estatística de teste tão extremo ou mais extremo que o observado, assumindo que a hipótese nula (de que a amostra segue uma distribuição normal) é verdadeira.
#se p valor >0.05 - dados normais no nivel de 95%
#se p valor >0.01 - dados normais no nivel de 99% e etc...


install.packages("devtools")
devtools::install_github("cardiomoon/webr")
#clica em no se aparecer para instalar o webr por "sources"

library(webr)
#agora é só plotar

#outliers

install.packages("outliers")#para o teste de grubbs
library(outliers)

#testando se os valores extremos da coluna Si são outliers

grubbs.test(dados$Si, opposite = TRUE)
#Isso retornará uma saída que inclui o valor do teste de Grubbs (G), o valor crítico (U) e o valor p.
#a hipótese nula do teste é que o valor nao é um outlier significativo
print("Se o valor p for menor que 0.05, o valor extremo será considerado um outlier significativo, pois estaremos rejeitando a hipotese nula. Se for maior, aceitamos a hipotese nula e nao o consideramos um outlier")

dixon.test(dados$Si)
#Isso retornará uma saída que inclui os valores dos testes de Dixon e se há um outlier significativo (pvalor). 
#O argumento "opposite = TRUE" é usado para indicar que o teste deve ser feito para encontrar o maior outlier em vez do menor. 
print("Se o valor p for menor que 0.05, o valor extremo será considerado um outlier significativo, pois estaremos rejeitando a hipotese nula. Se for maior, aceitamos a hipotese nula e nao o consideramos um outlier")
