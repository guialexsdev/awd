# AWD - Detector Automático de Cachoeiras

## Requisitos e dependências

- Versão mínima do QGis: 3.0
- Dependência: o plugin QuickOSM precisa estar previamente instalado

## Breve tutorial

### Baixe o plugin

Vá em Plugin -> Manage and install plugins... -> Procure por AWD e instale-o.

### Executando o algoritmo

Para usar o plugin, vá em Plugins -> AWD -> Detect Waterfalls.

### Tutorial

Este algoritmo utiliza lógica fuzzy para a detectar cachoeiras, entregando ao usuário uma camada vetorial contendo pontos onde a existência de cachoeiras é provável. Cada feature da camada vetorial possui um campo m_value, que varia entre 0 e 1 e indica o quão "provável" é a existência da queda d'água. Quanto mais próximo de 1, mais provável. Dados OSM são utilizados para elevar o m_value, caso uma detecção esteja num raio de até 250 metros de uma marcação de cachoeira do OSM.

Em geral, o mais indicado é que apenas detecções com m_value > 0.5 sejam utilizadas, mas o usuário pode, através do campo Alpha Cut, trazer resultados com valores menores. Considere abaixar o Alpha Cut quando o resultado não estiver trazendo muitas detecções, mas entenda que abaixo de 0.3 as marcações podem conter muitos erros.

É importante entender que tanto o DEM (modelo de elevação) quanto o raster de Flow Accumulation não são perfeitos e inserem erros importantes no processo de detecção. O algoritmo desse plugin tenta minimizar os erros, mas não consegue eliminá-los. De forma que:

- Uma detecção com m_value = 1 nem sempre garante a existência de cachoeiras;
- O algoritmo nem sempre detecta ou atribui m_value alto para uma cachoeiras cuja existência é sabida;
- Uma detecção com bom m_value não necessariamente está no local exato marcado... pode ser que esteja nas redondezas.

Segue abaixo uma descrição dos campos a serem preenchidos pelo usuário.

### Parâmetros de Entrada
#### DEM
Modelo de elevação. É recomendado usar um raster com resolução de 30m ou menos. Copernicus 30m é uma boa escolha.
#### Flow Accumulation
Raster contendo as drenagens. A unidade de acumulação precisa estar em "Número de células". Fluxo recomendado para a geração desse raster: Algoritmo de Breaching -> Fill Sinks -> Flow Accumulation (D8). O algoritmo de breaching implementado por John B. Lindsay é altamente recomendável já que oferece uma performance significativamente maior. Esse algoritmo pode ser encontrado no plugin WhiteBoxTools para o QGis.
#### Minimum Flow Accumulation
Minimum accumulation (in number of cells) that a drainage must have to be considered a river or stream eligible for analysis.
Acumulação mínima (em número de células) que a drenagem deve ter para ser considerada um rio ou córrego elegível para análise.
#### Minimum Slope
Inclinação mínima (em graus) que uma potencial cachoeiras deve possuir para ser considerada válida. Lembre-se que cachoeiras são objetos pequenos, quando vistos de uma imagem de satélite, e portanto contém erros significativos na medida da inclinação. É recomendado deixar o valor desse campo abaixo de 40, de preferência entre 10 e 20.
#### Alpha Cut
Todas as detecções com m_value abaixo do valor especificado nesse campo serão descartadas. Valores menores que 0.3 não são recomendados.
