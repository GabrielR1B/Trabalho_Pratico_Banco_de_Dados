import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# Importando os dados
dados_uniao = pd.read_csv('minha_casa_minha_vida_uniao_definitivo.csv', delimiter='|')
dados_financiamento = pd.read_csv('minha_casa_minha_vida_financiado_definitivo.csv', delimiter='|')
paleta_verde_amarelo = sns.color_palette(["#008000", "#FFD700"])

# Tratando colunas relevantes
dados_uniao['val_contratado_total'] = dados_uniao['val_contratado_total'].str.replace(',', '').astype(float)
dados_uniao['val_desembolsado'] = dados_uniao['val_desembolsado'].str.replace(',', '').astype(float)

# Extraindo o ano da coluna dt_assinatura
dados_uniao['ano_assinatura'] = pd.to_datetime(dados_uniao['dt_assinatura'], format='%d/%m/%Y', errors='coerce').dt.year


def filtrar_dados(df, ano=None, regiao=None, estado=None):
    """Filtra os dados de acordo com os critérios fornecidos."""
    df_filtrado = df.copy()
    
    if ano:
        df_filtrado = df_filtrado[df_filtrado['data_referencia'].str.contains(str(ano))]
    if regiao:
        df_filtrado = df_filtrado[df_filtrado['txt_regiao'] == regiao]
    if estado:
        df_filtrado = df_filtrado[df_filtrado['txt_sigla_uf'] == estado]
    
    return df_filtrado

def gerar_grafico_pizza(dados, ano=None, regiao=None, estado=None):
    """
    Gera um gráfico de pizza baseado na coluna txt_modalidade, com filtros opcionais para ano, região e estado.
    """
    # Filtrando por ano
    if ano:
        dados['ano_assinatura'] = pd.to_datetime(dados['dt_assinatura'], format='%d/%m/%Y').dt.year
        dados = dados[dados['ano_assinatura'] == ano]

    # Filtrando por região
    if regiao:
        dados = dados[dados['txt_regiao'] == regiao]

    # Filtrando por estado
    if estado:
        dados = dados[dados['txt_sigla_uf'] == estado]

    # Verificando se há dados após os filtros
    if dados.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # Contagem por modalidade
    modalidade_counts = dados['txt_modalidade'].value_counts()

    # Gerar o gráfico
    fig, ax = plt.subplots(figsize=(3, 4))
    ax.pie(
        modalidade_counts.values,
        labels=modalidade_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=plt.cm.Paired.colors
    )
    ax.set_title("Distribuição de Modalidades de Empreendimentos")
    st.pyplot(fig)

def mostra_tabela(dataframe):
    """Mostra uma tabela filtrada por número de linhas."""
    qtd_linhas = st.sidebar.slider(
        'Selecione a quantidade de linhas para mostrar na tabela',
        min_value=1, max_value=len(dataframe), step=1
    )
    st.write(dataframe.head(qtd_linhas))

def grafico_municipios(base_escolhida, filtro_valor, filtro_tipo):
    """Gera o gráfico de municípios com maior quantidade de unidades habitacionais."""
    
    if base_escolhida == 'União':
        # Filtrar dados da União com base no filtro escolhido
        if filtro_tipo == 'Estado':
            dataframe = dados_uniao[dados_uniao['txt_sigla_uf'] == filtro_valor]
        elif filtro_tipo == 'Região':
            dataframe = dados_uniao[dados_uniao['txt_regiao'] == filtro_valor]
        coluna_uh = 'qtd_uh'
    elif base_escolhida == 'Financiado':
        # Filtrar dados de Financiamento com base no filtro escolhido
        dataframe = dados_financiamento[dados_financiamento['txt_sigla_uf'] == filtro_valor]
        coluna_uh = 'qtd_uh_financiadas'
    else:  # Ambas
        # Filtrar e agrupar dados de União e Financiado por município
        dataframe_uniao = dados_uniao[dados_uniao['txt_sigla_uf'] == filtro_valor]
        dataframe_financiamento = dados_financiamento[dados_financiamento['txt_sigla_uf'] == filtro_valor]
        dataframe_uniao = dataframe_uniao.groupby('txt_nome_municipio')['qtd_uh'].sum().reset_index()
        dataframe_financiamento = dataframe_financiamento.groupby('txt_nome_municipio')['qtd_uh_financiadas'].sum().reset_index()
        
        # Merge dos dois dataframes
        dataframe = pd.merge(
            dataframe_uniao, dataframe_financiamento,
            on='txt_nome_municipio', how='outer'
        ).fillna(0)
        
        # Criar a coluna total
        dataframe['qtd_total'] = dataframe['qtd_uh'] + dataframe['qtd_uh_financiadas']
        coluna_uh = 'qtd_total'

    # Agrupar por município e somar a coluna relevante
    dataframe = dataframe.groupby('txt_nome_municipio')[coluna_uh].sum().reset_index()
    
    # Ordenar e pegar os primeiros N municípios
    dataframe = dataframe.sort_values(by=coluna_uh, ascending=False)
    

    # Chamar a função para gerar o gráfico
    dataframe = dataframe.head(num_municipios)
    
    # Plotar o gráfico
    plt.figure(figsize=(12, 6))
    sns.barplot(data=dataframe, x='txt_nome_municipio', y=coluna_uh, palette='RdBu')
    plt.xticks(rotation=90)
    plt.xlabel('Município')
    plt.ylabel('Quantidade de Unidades Habitacionais')
    plt.title(f'Municípios com maiores quantidades de unidades habitacionais - {filtro_valor}')
    st.pyplot(plt)

def grafico_construtoras(filtro_tipo, filtro_valor):
    """Gera um gráfico de construtoras com maior atuação em municípios, estados ou regiões."""
    if filtro_tipo == 'Municípios':
        dataframe = dados_uniao.groupby('txt_nome_construtora_entidade')['txt_nome_municipio'].nunique().reset_index()
    elif filtro_tipo == 'Estados':
        dataframe = dados_uniao.groupby('txt_nome_construtora_entidade')['txt_sigla_uf'].nunique().reset_index()
    else:  # Regiões
        dataframe = dados_uniao.groupby('txt_nome_construtora_entidade')['txt_regiao'].nunique().reset_index()

    dataframe = dataframe.rename(columns={
        'txt_nome_municipio': 'quantidade',
        'txt_sigla_uf': 'quantidade',
        'txt_regiao': 'quantidade'
    })
    dataframe = dataframe.sort_values(by='quantidade', ascending=False).head(50)

    num_construtoras = st.slider('Selecione o número de construtoras para o gráfico', min_value=10, max_value=50, step=10)
    dataframe = dataframe.head(num_construtoras)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=dataframe, x='txt_nome_construtora_entidade', y='quantidade', palette=paleta_verde_amarelo)
    plt.xticks(rotation=90)
    plt.xlabel('Construtora')
    plt.ylabel('Quantidade de Atuação')
    plt.title(f'Construtoras com maior atuação em {filtro_tipo.lower()} - {filtro_valor}')
    st.pyplot(plt)

def grafico_por_mandato(base_escolhida):
    """Gera um gráfico de unidades habitacionais por mandato presidencial."""
    if base_escolhida == 'União':
        dataframe = dados_uniao.groupby('ano_assinatura')['qtd_uh'].sum().reset_index()
        coluna_uh = 'qtd_uh'
    elif base_escolhida == 'Financiado':
        dataframe = dados_financiamento.groupby('num_ano_financiamento')['qtd_uh_financiadas'].sum().reset_index()
        dataframe = dataframe.rename(columns={'num_ano_financiamento': 'ano_assinatura'})
        coluna_uh = 'qtd_uh_financiadas'
    else:  # Ambas
        dataframe_uniao = dados_uniao.groupby('ano_assinatura')['qtd_uh'].sum().reset_index()
        dataframe_financiamento = dados_financiamento.groupby('num_ano_financiamento')['qtd_uh_financiadas'].sum().reset_index()
        dataframe_financiamento = dataframe_financiamento.rename(columns={'num_ano_financiamento': 'ano_assinatura'})
        dataframe = pd.merge(
            dataframe_uniao, dataframe_financiamento,
            on='ano_assinatura', how='outer'
        ).fillna(0)
        dataframe['qtd_total'] = dataframe['qtd_uh'] + dataframe['qtd_uh_financiadas']
        coluna_uh = 'qtd_total'

    # Definindo os intervalos de mandatos presidenciais, começando pelo Lula 2
    mandatos = {
        'Lula 2': (2007, 2010),
        'Dilma 1': (2011, 2014),
        'Dilma 2': (2015, 2016),
        'Temer': (2016, 2018),
        'Bolsonaro': (2019, 2022),
        'Lula 3': (2023, 2024)
    }

    # Classificando os anos por mandato
    dataframe['mandato'] = pd.cut(
        dataframe['ano_assinatura'], 
        bins=[2006, 2010, 2014, 2016, 2018, 2022, 2024],  # Bins para cada mandato
        labels=['Lula 2', 'Dilma 1', 'Dilma 2', 'Temer', 'Bolsonaro', 'Lula 3'], 
        right=False
    )

    # Agrupando e somando por mandato
    dataframe_mandato = dataframe.groupby('mandato')[coluna_uh].sum().reset_index()

    # Convertendo para dezenas de milhar
    dataframe_mandato[coluna_uh] = dataframe_mandato[coluna_uh] / 10000  # Convertendo para dezenas de milhar

    # Plotando o gráfico de barras
    plt.figure(figsize=(12, 6))
    sns.barplot(data=dataframe_mandato, x='mandato', y=coluna_uh, palette=paleta_verde_amarelo)
    plt.xlabel('Mandato Presidencial')
    plt.ylabel('Quantidade de Unidades Habitacionais (em dezenas de milhar)')
    plt.title('Unidades Habitacionais Criadas por Mandato Presidencial')
    st.pyplot(plt)

def exibir_tabelas(base_escolhida):
    """Exibe e permite filtrar as tabelas dos imóveis da União e Financiados."""
    if base_escolhida == 'União':
        dataframe = dados_uniao.copy()
        coluna_ano = 'ano_assinatura'  # Nome correto da coluna para anos
    elif base_escolhida == 'Financiado':
        dataframe = dados_financiamento.copy()
        coluna_ano = 'num_ano_financiamento'  # Nome correto da coluna para anos
    else:
        st.warning("Opção inválida. Escolha entre União ou Financiado.")
        return

    # Filtros disponíveis
    filtro_opcoes = st.multiselect(
        'Escolha os filtros que deseja aplicar:',
        ['Município', 'Estado', 'Região', 'Ano']
    )

    if 'Município' in filtro_opcoes:
        municipios = dataframe['txt_nome_municipio'].dropna().unique()
        municipio_selecionado = st.selectbox('Selecione o município:', sorted(municipios))
        dataframe = dataframe[dataframe['txt_nome_municipio'] == municipio_selecionado]

    if 'Estado' in filtro_opcoes:
        estados = dataframe['txt_sigla_uf'].dropna().unique()
        estado_selecionado = st.selectbox('Selecione o estado:', sorted(estados))
        dataframe = dataframe[dataframe['txt_sigla_uf'] == estado_selecionado]

    if 'Região' in filtro_opcoes:
        regioes = dataframe['txt_regiao'].dropna().unique()
        regiao_selecionada = st.selectbox('Selecione a região:', sorted(regioes))
        dataframe = dataframe[dataframe['txt_regiao'] == regiao_selecionada]

    if 'Ano' in filtro_opcoes:
        dataframe = dataframe[dataframe[coluna_ano].between(2009, 2024)]
        ano_selecionado = st.slider('Selecione o ano:', min_value=2009, max_value=2024, step=1)
        dataframe = dataframe[dataframe[coluna_ano] == ano_selecionado]

    # Opção para remover colunas
    colunas_remover = st.multiselect(
        'Escolha as colunas que deseja remover:',
        dataframe.columns
    )
    dataframe = dataframe.drop(columns=colunas_remover)

    # Mostrar tabela com slider para quantidade de linhas
    qtd_linhas = st.slider(
        'Quantidade de linhas para exibir:',
        min_value=1, max_value=len(dataframe), value=min(10, len(dataframe))
    )
    st.write(dataframe.head(qtd_linhas))

    # Botão para download
    csv = dataframe.to_csv(index=False)
    st.download_button(
        label="Baixar tabela filtrada como CSV",
        data=csv,
        file_name=f'{base_escolhida.lower()}_filtrada.csv',
        mime='text/csv'
    )

def grafico_anos(base_escolhida):
    """Gera um gráfico de progressão por anos."""
    if base_escolhida == 'União':
        dataframe = dados_uniao.groupby('ano_assinatura')['qtd_uh'].sum().reset_index()
        coluna_uh = 'qtd_uh'
    elif base_escolhida == 'Financiado':
        dataframe = dados_financiamento.groupby('num_ano_financiamento')['qtd_uh_financiadas'].sum().reset_index()
        dataframe = dataframe.rename(columns={'num_ano_financiamento': 'ano_assinatura'})
        coluna_uh = 'qtd_uh_financiadas'
    else:  # Ambas
        dataframe_uniao = dados_uniao.groupby('ano_assinatura')['qtd_uh'].sum().reset_index()
        dataframe_financiamento = dados_financiamento.groupby('num_ano_financiamento')['qtd_uh_financiadas'].sum().reset_index()
        dataframe_financiamento = dataframe_financiamento.rename(columns={'num_ano_financiamento': 'ano_assinatura'})
        dataframe = pd.merge(
            dataframe_uniao, dataframe_financiamento,
            on='ano_assinatura', how='outer'
        ).fillna(0)
        dataframe['qtd_total'] = dataframe['qtd_uh'] + dataframe['qtd_uh_financiadas']
        coluna_uh = 'qtd_total'

    dataframe = dataframe[(dataframe['ano_assinatura'] >= 2009) & (dataframe['ano_assinatura'] <= 2024)]
    dataframe[coluna_uh] = dataframe[coluna_uh] / 10000  # Convertendo para dezenas de milhar

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=dataframe, x='ano_assinatura', y=coluna_uh, marker='o', color='#008000')
    plt.xlabel('Ano')
    plt.ylabel('Quantidade de Unidades Habitacionais (em dezenas de milhar)')
    plt.title('Progressão de Unidades Habitacionais por Ano (2009-2024)')
    st.pyplot(plt)

# Título da página
st.title('Minha Casa Minha Vida - Análise de Dados:house:')
st.write('Análise detalhada dos dados do programa de habitação popular no Brasil.')

# Permitir exibição das tabelas, independente do tipo de análise
st.sidebar.subheader("Exibir tabelas")
base_tabelas = st.sidebar.radio(
    'Escolha a base de dados para exibir:',
    ['União', 'Financiado']
)

if st.sidebar.checkbox('Mostrar tabela com filtros'):
    exibir_tabelas(base_tabelas)


# Escolha do tipo de análise
# Escolha do tipo de análise
tipo_analise = st.sidebar.radio('Escolha o tipo de análise:', ['Municípios', 'Construtoras', 'Anos', 'Variados'])

if tipo_analise == 'Municípios':
    # Seleção de base de dados
    base_escolhida = st.sidebar.radio(
        'Escolha a base de dados para análise:',
        ['União', 'Financiado', 'Ambas']
    )

    # Filtro para gráfico
    if st.sidebar.checkbox('Mostrar gráfico de municípios'):
        if base_escolhida in ['Financiado', 'Ambas']:
            filtro_tipo = 'Estado'
        else:
            filtro_tipo = st.sidebar.radio('Filtrar por:', ['Estado', 'Região'])

        if filtro_tipo == 'Estado':
            opcoes = list(dados_uniao['txt_sigla_uf'].dropna().unique() if base_escolhida != 'Financiado' else dados_financiamento['txt_sigla_uf'].dropna().unique())
        else:
            opcoes = list(dados_uniao['txt_regiao'].dropna().unique())

        filtro_valor = st.sidebar.selectbox(f'Selecione o {filtro_tipo.lower()} para o gráfico', options=opcoes)

        if filtro_valor:
            # Slider para selecionar o número de municípios
            num_municipios = st.slider('Selecione o número de municípios para o gráfico', min_value=10, max_value=50, step=10)

            # Chamar a função para gerar o gráfico
            grafico_municipios(base_escolhida, filtro_valor, filtro_tipo)


elif tipo_analise == 'Construtoras':
    # Filtro para construtoras
    filtro_tipo = st.sidebar.radio('Filtrar por:', ['Municípios', 'Estados', 'Regiões'])
    filtro_valor = 'Brasil'  # Para indicar uma visão geral nacional

    if st.sidebar.checkbox('Mostrar gráfico de construtoras'):
        grafico_construtoras(filtro_tipo, filtro_valor)

elif tipo_analise == 'Anos':
    base_escolhida = st.sidebar.radio(
        'Escolha a base de dados para análise:',
        ['União', 'Financiado', 'Ambas']
    )

    if st.sidebar.checkbox('Mostrar gráfico de anos'):
        grafico_anos(base_escolhida)

    if st.sidebar.checkbox('Mostrar gráfico por mandato presidencial'):
        grafico_por_mandato(base_escolhida)

elif tipo_analise == 'Variados':
    # Gráfico de pizza para modalidades
    st.sidebar.header('Análise de Modalidades')

    if st.sidebar.checkbox('Mostrar gráfico de modalidades'):
        ano = st.sidebar.number_input(
            'Selecione o ano:', 
            min_value=2009, max_value=2024, step=1, value=2014
        )
        regiao = st.sidebar.selectbox(
            'Selecione a região:', 
            options=['Todas'] + list(dados_uniao['txt_regiao'].dropna().unique())
        )
        estado = st.sidebar.selectbox(
            'Selecione o estado:', 
            options=['Todos'] + list(dados_uniao['txt_sigla_uf'].dropna().unique())
        )

        # Ajustando os filtros
        regiao = None if regiao == 'Todas' else regiao
        estado = None if estado == 'Todos' else estado

        # Gerar o gráfico de pizza para a base "União"
        gerar_grafico_pizza(dados_uniao, ano=ano, regiao=regiao, estado=estado)





