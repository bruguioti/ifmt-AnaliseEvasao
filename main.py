import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Configuração da página
st.set_page_config(page_title="Análise IFMT - Evasão", layout="wide")

st.title(" Análise de Evasão e Retenção - IFMT")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("1.csv")
        if df.shape[1] <= 1:
            df = pd.read_csv("1.csv", sep=';')
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    df.columns = df.columns.str.strip()
    
    # Mapeamento para cálculo de média
    peso_respostas = {
        "Determinante": 4,
        "Muito Relevante": 3,
        "Relevante": 2,
        "Pouco Relevante": 1,
        "Indiferente": 0
    }
    return df, peso_respostas

df, pesos = load_data()

# Identificar coluna de campus
coluna_campus = next((col for col in df.columns if "campus" in col.lower()), None)

if not coluna_campus:
    st.error("Coluna de Campus não encontrada. Verifique os títulos do arquivo CSV.")
    st.stop()

# Sidebar
st.sidebar.header("Configurações da Análise")
# Convertemos para string e removemos valores nulos antes de ordenar
campi = sorted(df[coluna_campus].dropna().astype(str).unique())
campus_selecionado = st.sidebar.selectbox("Selecione o Campus para filtrar:", campi)

# Identificar colunas de desistência
cols_desistencia = [c for c in df.columns if "desistirem" in c]

# Extrair nomes amigáveis (labels)
labels_dict = {}
for c in cols_desistencia:
    try:
        labels_dict[c] = c.split('[')[1].split(']')[0]
    except IndexError:
        labels_dict[c] = c

# Filtrar dados
df_campus = df[df[coluna_campus] == campus_selecionado]
total_alunos = len(df_campus)

if not df_campus.empty:
    # --- Métricas Principais ---
    c1, c2 = st.columns(2)
    c1.metric("Campus Atual", campus_selecionado)
    c2.metric("Total de Alunos (Amostragem)", f"{total_alunos} alunos")

    # --- Expander de Ajuda ---
    with st.expander("ℹ O que significa o Índice de Relevância?", expanded=False):
        st.markdown("""
        Este índice representa a **média das opiniões**. Quanto mais próximo de **4.0**, mais crítico é o fator.
        
        | Peso | Nível | Impacto |
        | :--- | :--- | :--- |
        | 4 | **Determinante** | Causa principal da desistência. |
        | 3 | **Muito Relevante** | Impacto forte na decisão. |
        | 0 | **Indiferente** | Não influenciou em nada. |
        """)

    # --- Cálculo de Médias ---
    df_numerico = df_campus[cols_desistencia].replace(pesos)
    for col in df_numerico.columns:
        df_numerico[col] = pd.to_numeric(df_numerico[col], errors='coerce')
    
    media_fatores = df_numerico.mean().fillna(0)
    df_plot = pd.DataFrame({
        'Fator': [labels_dict[c] for c in cols_desistencia],
        'Nivel': media_fatores.values
    }).sort_values(by='Nivel', ascending=False)

    # --- Gráfico 1: Ranking por Média ---
    st.subheader(" Ranking de Fatores (Média de Impacto)")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    palette = sns.color_palette("Reds_r", n_colors=len(df_plot))
    sns.barplot(data=df_plot, x='Nivel', y='Fator', palette=palette, ax=ax)
    
    for i in ax.containers:
        ax.bar_label(i, fmt='%.1f', padding=8, fontweight='bold')
    
    ax.set_xlim(0, 4.5)
    ax.set_xlabel("Índice Médio (0 a 4)")
    ax.set_ylabel("")
    st.pyplot(fig)

    # --- SEÇÃO NOVA: CONTAGEM DE VOTOS ---
    st.markdown("---")
    st.subheader(" Detalhamento: Quantos alunos votaram em cada opção?")

    # Criar DataFrame de contagem
    # 1. Pegamos as colunas originais (texto) do campus selecionado
    df_votos = df_campus[cols_desistencia].copy()
    
    # 2. Renomeamos as colunas para os nomes curtos (labels)
    df_votos.columns = [labels_dict[c] for c in df_votos.columns]

    # 3. Contamos as ocorrências e organizamos a tabela
    contagem = df_votos.apply(pd.Series.value_counts).fillna(0).astype(int)
    
    # Reordenar as linhas para ordem lógica de importância
    ordem_logica = ["Determinante", "Muito Relevante", "Relevante", "Pouco Relevante", "Indiferente"]
    # Garante que só tentamos ordenar pelo que existe nos dados
    existentes = [nivel for nivel in ordem_logica if nivel in contagem.index]
    contagem = contagem.reindex(existentes)

    # Exibir Tabela Interativa
    st.write("Tabela de frequência (número de alunos):")
    st.dataframe(contagem.T, use_container_width=True)

    # Gráfico de Barras Empilhadas para Visualização Proporcional
    st.write("Visualização da Distribuição de Votos:")
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    contagem.T.plot(kind='barh', stacked=True, ax=ax2, colormap="RdYlGn_r")
    ax2.set_xlabel("Quantidade de Votos")
    ax2.legend(title="Resposta", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    st.pyplot(fig2)

    # Conclusão Final
    top_fator = df_plot.iloc[0]['Fator']
    st.success(f"**Insight:** O fator mais crítico em **{campus_selecionado}** é **'{top_fator}'**. Verifique na tabela acima a proporção de alunos que o classificaram como 'Determinante'.")

else:
    st.warning(f"Não existem dados cadastrados para o campus: {campus_selecionado}")