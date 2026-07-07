# Dados brutos

## Dataset real (Kaggle)

O projeto usa o dataset **World Bank: Education Data (BigQuery Dataset)**:
https://www.kaggle.com/datasets/theworldbank/world-bank-intl-education

Para baixar (requer conta Kaggle + API token configurado em `~/.kaggle/kaggle.json`):

```bash
pip install kaggle --break-system-packages
kaggle datasets download -d theworldbank/world-bank-intl-education -p data/raw --unzip
```

O arquivo principal da tabela `international_education` deve ser salvo
como `data/raw/international_education.csv`, com as colunas:

| coluna          | tipo   | descrição                                   |
|-----------------|--------|----------------------------------------------|
| country_name    | texto  | nome do país                                  |
| country_code    | texto  | código ISO3 do país                           |
| indicator_name  | texto  | nome do indicador                             |
| indicator_code  | texto  | código oficial do indicador (World Bank)      |
| year            | número | ano do dado                                   |
| value           | número | valor do indicador                            |

> Se o nome do arquivo baixado for diferente, renomeie para
> `international_education.csv` ou ajuste `RAW_DATA_FILE_REAL` em
> `src/config.py`.

## Dataset de amostra (incluso no repositório)

Como nem todo ambiente de execução (ex: CI, avaliação automática) tem
acesso ao Kaggle, o repositório inclui `sample_education_data.csv`: um
dataset sintético, mas com o **mesmo schema** do dataset real, cobrindo
10 países e 6 indicadores educacionais entre 2010–2022, incluindo valores
ausentes propositalmente (para exercitar o tratamento de dados faltantes).

O pipeline (`src/data_loader.py`) usa automaticamente o arquivo real se
ele existir em `data/raw/international_education.csv`; caso contrário,
usa o arquivo de amostra e avisa isso no log.
