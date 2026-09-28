#script para plotagem de gráficos utilizando o ggplot2
library(readr)#para importar csv
library(readxl)#para arquivos do excel
library(ggplot2)#para plotagem
library(magrittr)
library(tidyr)

#definindo o diretório
setwd("D:/DOUTORADO/estagio/dados")

#importar o espectro com o nome as amostras na primeira linha e as variaveis nas colunas
#dados <- read.csv("nome do arquivo.CSV", sep=";")
dados <- read_excel("dados arroio boavista.xlsx") %>% as.data.frame() #se os dados forem no formato de planilhas do excel

#plotando gráficos com o ggplot2
#manipulando os dados

Classe_Cultura = dados[,1] 
Classe_Cultura

dados = dados[,-1]

############################GRÁFICOS DE DISPERSÃO####################################################################

ggplot(dados, aes(x=Sr, y=Zr)) +
  geom_point(aes(colour=Classe_Cultura, shape=Classe_Cultura), size=5) +
  scale_shape_manual(values = c(17,18)) +
  scale_color_manual(values = c("red", "blue")) +
  theme_classic( )+
  theme(legend.position = "bottom", 
        text = element_text(size=18, 
                            family = "serif")) +
  labs(x="Sr (%)", y="Zr (%)")


###########################BOX_PLOT####################################################################

g1 = ggplot(dados, aes(x=Classe_Cultura, y=Fe)) + 
  geom_boxplot(size = 2, 
               color="black", 
               fill = "pink", 
               alpha = 1,
               outlier.shape = NA) + 
  theme_classic() +
  theme(text = element_text(size=18)) +
  labs(x="Boxplots", y= "Fe(%)") + 
  stat_summary(fun.y = "mean", shape=4, size = 2.5, color = "white") + 
  scale_y_continuous(breaks = seq(1, 8, by =0.5))
  

#scale_y_continuous(breaks = seq(1, 8, by =0.5))
#stat_summary(fun.y = "mean", shape=4, size = 2.5, color = "white")
#stat_boxplot(geom = "errorbar", size=1)
#alpha transparencia
#A funcao geom_boxplot utiliza o criterio de Tukey para identificar outliers. 
#Este criterio define um outlier como um valor que e maior do que o intervalo Q3 + 1.5 * IQR (onde IQR e o intervalo interquartil) ou menor do que Q1 - 1.5 * IQR. 
#Valores que sao identificados como outliers sao representados como pontos fora da caixa do grafico de caixa.
#para removêlos do gráfico vamos usar o outlier.shape = NA

g2 = ggplot(dados, aes(x=Classe_Cultura, y=Fe))+
  geom_boxplot(size = 1, color="black", fill = "lightblue", 
               alpha =0.6, outlier.shape = NA) + 
  theme_bw() +
  theme(text = element_text(size=18)) +
  labs(x="Boxplots", y= "Fe(%)")


ggplot(dados, aes(x=Classe_Cultura, y=Al))+
  geom_boxplot(size = 1, color="black", fill = "lightblue", 
               alpha =0.6, outlier.shape = NA) + 
  theme_bw() +
  theme(text = element_text(size=18),
        axis.line = element_line(colour = "black"),
        axis.text.x = element_text(color = "black"), 
        axis.text.y = element_text(color = "black")) +
  labs(x="Boxplots", y= "Al(%)")


#pode ser que seja interessante plotar os gráficos lado a lado.
#podemos fazer isso com o pacote pacthwork
install.packages("patchwork")#para instalar
library(patchwork)#para habilitar

g1 / g2

#plot_layout()


###########################GRAFICO_DE_BARRAS####################################################################

ggplot(dados, aes(x=Classe_Cultura, y =Fe, fill=Classe_Cultura)) + 
  geom_bar(stat = "identity", 
           position="dodge", 
           width = 0.8) +
  scale_fill_manual(values = c("red", "darkblue")) + 
  theme_bw( )+
  theme(legend.position ="top", 
        text = element_text(size=19, family = "serif")) +
  labs(y="Concentração de Fe(%)", 
       x=NULL) + 
  geom_hline(yintercept = 0, 
             linetype="dashed")

#Para um gráfico com todos os elementos, primeiro derreta os dados de várias colunas em uma única coluna de valor e outra de nomes. 
#você pode fazer isso usando a função tidyr::gather():
dados_long <- gather(dados[], key = "Elementos", value = "Concentracao")

#Além disso, para as classes, vamos criar um data.frame chamado classes para poder dividor os dados na plotagem
Cultura <- data.frame(Cultura = rep(NA, 160))
Cultura[1:160,] <- Classe_Cultura 
Cultura <- as.matrix(Cultura)

#plotando

ggplot(dados_long, 
       aes(x = Elementos, y =Concentracao, fill=Cultura)) + 
  geom_bar(stat = "identity", 
           position="fill", 
           width = 0.8) +
  scale_fill_manual(values = c("red", "darkblue")) + 
  theme_classic( )+
  theme(legend.position ="top", 
        text = element_text(size=25, family = "serif")) +
  labs(y="Concentração (%)", x=NULL) + 
  geom_hline(yintercept = 0, 
             linetype="dashed")

#position = dodge ou fill
############################GRÁFICOS DE LINHA(ESPECTROS)####################################################################

espectros <- read_excel("espectros_poisson.xlsx") %>% as.data.frame()#nao indiquei o caminho pq ja defini o diretório, o arquivo está nele  

ggplot(espectros, 
       aes(x=Energia)) +
  geom_line(aes(y=Espec15, colour="15kV"), size=0.9)+
  geom_line(aes(y=Espec50, colour="50kV"), size=0.9)+
  scale_color_manual(values = c("red", "darkblue"))+
  theme_classic( ) +
  theme(legend.position = "bottom", 
        text = element_text(size=18, family = "serif"),
        legend.title = element_blank(),
        plot.title = element_text(size = 25, 
                                  face = "bold", 
                                  hjust = 0.5)) +
  labs(x="Energia (keV)", 
       y= "Intensidade (cps/µA)") + 
  scale_x_continuous(breaks = seq(0, 30, by = 1), 
                     limits = c(1,16)) +
  scale_y_continuous(breaks = seq(0, 40, by = 5), 
                     limits = c(0,20)) + 
  ggtitle("Espec 15 e 50 kV")

ggsave("Espectros_900dpi.png", 
       width=15, 
       height=9.5, 
       units = "cm", 
       limitsize = FALSE,
       dpi=900)
