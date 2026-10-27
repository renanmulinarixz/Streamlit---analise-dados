
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Cuidados",
    layout="wide",
    page_icon="🧹"
)


@st.cache_data
def carregar_dados(caminho_arquivo):
    xls = pd.ExcelFile(caminho_arquivo)

    abas_anos = [
        sheet for sheet in xls.sheet_names
        if "(CV)" not in sheet
    ]

    dados_totais = []

    for ano in abas_anos:
        df_raw = pd.read_excel(xls, sheet_name=ano)

        # Localiza a linha onde começa Brasil
        linhas_brasil = df_raw.index[
            df_raw.iloc[:, 0].astype(str).str.strip() == "Brasil"
        ]

        if len(linhas_brasil) == 0:
            continue

        start_idx = linhas_brasil[0]

        # Seleciona todas as linhas a partir de Brasil
        df_ano = df_raw.iloc[
            start_idx:, [0, 1, 2, 3]
        ].copy()

        # Padroniza os nomes das colunas
        df_ano.columns = [
            "Localidade", "Total", "Homem", "Mulher"
        ]

        # Remove linhas sem localidade
        df_ano = df_ano.dropna(subset=["Localidade"])

        df_ano["Localidade"] = (
            df_ano["Localidade"].astype(str).str.strip()
        )

        df_ano = df_ano[
            df_ano["Localidade"] != ""
        ]

        # Converte os valores numéricos
        for col in ["Total", "Homem", "Mulher"]:
            df_ano[col] = pd.to_numeric(
                df_ano[col], errors="coerce"
            )

        # Registra o ano da aba
        df_ano["Ano"] = str(ano)

        dados_totais.append(df_ano)

    if not dados_totais:
        raise ValueError(
            "Nenhuma aba válida com a localidade Brasil foi encontrada."
        )

    df_completo = pd.concat(
        dados_totais, ignore_index=True
    )

    return df_completo


caminho_arquivo = r"H:\streamlit_projeto\Tabela 1.1.2.xls"


try:
    df = carregar_dados(caminho_arquivo)

    # Barra lateral
    st.sidebar.header("🔍 Filtros")

    anos_disponiveis = df["Ano"].drop_duplicates().tolist()

    ano_selecionado = st.sidebar.selectbox(
        "Selecione o ano:",
        options=anos_disponiveis
    )

    localidades_disponiveis = (
        df["Localidade"].drop_duplicates().tolist()
    )

    localidades_padrao = [
        local for local in [
            "Brasil", "Norte", "Nordeste",
            "Sudeste", "Sul", "Centro-Oeste"
        ]
        if local in localidades_disponiveis
    ]

    localidades_selecionadas = st.sidebar.multiselect(
        "Selecione as regiões/UFs:",
        options=localidades_disponiveis,
        default=localidades_padrao
    )

    # Título
    st.title(
        "Horas dedicadas a cuidados e afazeres domésticos"
    )

    st.markdown(
        "Análise da média de horas semanais dedicadas "
        "por pessoas ocupadas de 14 anos ou mais, por sexo."
    )

    # Filtra os dados
    df_filtrado = df[
        (df["Ano"] == ano_selecionado)
        & (
            df["Localidade"].isin(
                localidades_selecionadas
            )
        )
    ]

    if not df_filtrado.empty:

        # Tabela
        st.subheader(f"Dados do ano {ano_selecionado}")

        st.dataframe(
            df_filtrado[
                ["Localidade", "Total", "Homem", "Mulher"]
            ].reset_index(drop=True),
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("📊 Gráficos comparativos")

        col1, col2 = st.columns(2)

        # Gráfico de barras
        with col1:
            df_melted = df_filtrado.melt(
                id_vars=["Localidade"],
                value_vars=["Homem", "Mulher"],
                var_name="Gênero",
                value_name="Horas semanais"
            )

            fig_bar = px.bar(
                df_melted,
                x="Localidade",
                y="Horas semanais",
                color="Gênero",
                barmode="group",
                title=(
                    f"Média de horas por gênero "
                    f"({ano_selecionado})"
                ),
                color_discrete_sequence=[
                    "#1f77b4", "#e377c2"
                ],
                labels={
                    "Horas semanais": "Horas/semana",
                    "Localidade": "Região / UF"
                }
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        # Gráfico de evolução temporal
        with col2:
            df_historico = df[
                df["Localidade"].isin(
                    localidades_selecionadas
                )
            ].copy()

            df_historico["Ano"] = pd.Categorical(
                df_historico["Ano"],
                categories=anos_disponiveis,
                ordered=True
            )

            fig_line = px.line(
                df_historico,
                x="Ano",
                y="Total",
                color="Localidade",
                markers=True,
                title=(
                    "Evolução temporal do total "
                    "de horas dedicadas"
                ),
                labels={
                    "Total": "Horas/semana",
                    "Ano": "Ano",
                    "Localidade": "Região / UF"
                }
            )

            st.plotly_chart(
                fig_line,
                use_container_width=True
            )

    else:
        st.warning(
            "Nenhum dado encontrado para os filtros selecionados."
        )

except Exception as e:
    st.error(f"Erro ao carregar ou processar o arquivo: {e}")

    st.info(
        "Verifique se o arquivo existe no caminho informado, "
        "se as abas do Excel possuem os dados esperados e "
        "se as dependências estão instaladas."
    )
