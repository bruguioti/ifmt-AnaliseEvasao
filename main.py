import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io

# 1. Configuração da página
st.set_page_config(page_title="Análise IFMT - Evasão", layout="wide")

st.title(" Análise de Evasão e Retenção - IFMT")

# --- FUNÇÃO AUXILIAR PARA DOWNLOAD ---
def export_plot(fig):
    """Gera um buffer da imagem em alta resolução para download"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    return buf.getvalue()

@st.cache_data
def load_data():
    try:
        # Tenta ler com vírgula, se falhar ou ler apenas uma coluna, tenta ponto e vírgula
        df = pd.read_csv("1.csv")
        if df.shape[1] <= 1:
            df = pd.read_csv("1.csv", sep=';')
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    # Limpeza básica de nomes de colunas
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
    st.error("Coluna de Campus não encontrada no CSV. Verifique os títulos do arquivo.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("Filtros de Análise")
campi = sorted(df[coluna_campus].dropna().astype(str).unique())
campus_selecionado = st.sidebar.selectbox("Selecione o Campus:", campi)

# Identificar colunas que contêm as perguntas de desistência
cols_desistencia = [c for c in df.columns if "desistirem" in c]

# Extrair nomes curtos para os gráficos (texto entre colchetes)
labels_dict = {}
for c in cols_desistencia:
    try:
        labels_dict[c] = c.split('[')[1].split(']')[0]
    except IndexError:
        labels_dict[c] = c

# Filtrar dados pelo campus selecionado
df_campus = df[df[coluna_campus] == campus_selecionado].copy()
total_alunos = len(df_campus)

if not df_campus.empty:
    # --- MÉTRICAS PRINCIPAIS ---
    c1, c2 = st.columns(2)
    c1.metric("Campus selecionado", campus_selecionado)
    c2.metric("Total de Respondentes", f"{total_alunos} alunos")

    # --- AJUDA (EXPANDER) ---
    with st.expander("ℹ️ Entenda o que significa o Índice Médio", expanded=False):
        st.markdown("""
        O índice representa a **média ponderada** das opiniões dos alunos. 
        Quanto mais próximo de **4.0**, mais crítico é o fator para a evasão escolar.
        
        | Peso | Nível | Impacto no Aluno |
        | :--- | :--- | :--- |
        | 🔴 **4** | **Determinante** | Causa direta da desistência. |
        | 🟠 **3** | **Muito Relevante** | Forte influência na decisão. |
        | 🟡 **2** | **Relevante** | Contribuiu para a insatisfação. |
        | ⚪ **0** | **Indiferente** | Não teve impacto na decisão. |
        """)

    # --- PROCESSAMENTO DOS DADOS ---
    # Substituímos os textos pelos pesos numéricos
    df_numerico = df_campus[cols_desistencia].replace(pesos)
    for col in df_numerico.columns:
        df_numerico[col] = pd.to_numeric(df_numerico[col], errors='coerce')
    
    media_fatores = df_numerico.mean().fillna(0)
    df_plot = pd.DataFrame({
        'Fator': [labels_dict[c] for c in cols_desistencia],
        'Media': media_fatores.values
    }).sort_values(by='Media', ascending=False)

    # --- GRÁFICO 1: RANKING POR MÉDIA ---
    st.subheader(" Ranking de Fatores Críticos")
    
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    pal = sns.color_palette("Reds_r", n_colors=len(df_plot))
    sns.barplot(data=df_plot, x='Media', y='Fator', palette=pal, ax=ax1)
    
    # Adicionar os números das médias nas barras
    for i in ax1.containers:
        ax1.bar_label(i, fmt='%.1f', padding=5, fontweight='bold')
    
    ax1.set_xlim(0, 4.5)
    ax1.set_xlabel("Média de Impacto (0 a 4)")
    ax1.set_ylabel("")
    
    st.pyplot(fig1)
    
    # Botão de download do Gráfico 1
    st.download_button(
        label=" Baixar Ranking",
        data=export_plot(fig1),
        file_name=f"ranking_{campus_selecionado}.png",
        mime="image/png"
    )

    # --- SEÇÃO 2: DETALHAMENTO DE VOTOS ---
    st.markdown("---")
    st.subheader(" Distribuição Detalhada das Respostas")

    # Preparar dados de contagem
    df_votos = df_campus[cols_desistencia].copy()
    df_votos.columns = [labels_dict[c] for c in df_votos.columns]
    
    # Limpar espaços e contar ocorrências
    for col in df_votos.columns:
        df_votos[col] = df_votos[col].astype(str).str.strip()

    ordem_respostas = ["Determinante", "Muito Relevante", "Relevante", "Pouco Relevante", "Indiferente"]
    contagem = df_votos.apply(lambda x: x.value_counts()).reindex(ordem_respostas).fillna(0).astype(int)

    # Exibir Tabela de Dados
    st.write("Frequência absoluta (quantidade de alunos por resposta):")
    st.dataframe(contagem.T, use_container_width=True)

    # --- GRÁFICO 2: BARRAS EMPILHADAS ---
    st.write("Visualização Proporcional de Impacto:")
    
    cores_map = {
        "Determinante": "#d62728",      # Vermelho
        "Muito Relevante": "#ff7f0e",   # Laranja
        "Relevante": "#ffbb78",         # Amarelo claro
        "Pouco Relevante": "#bcbd22",   # Oliva
        "Indiferente": "#c7c7c7"        # Cinza
    }
    
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    contagem.T.plot(kind='barh', stacked=True, ax=ax2, color=[cores_map.get(x, '#333') for x in contagem.index])
    
    ax2.set_xlabel("Quantidade de Votos")
    ax2.legend(title="Grau de Impacto", bbox_to_anchor=(1.0, 1), loc='upper left')
    plt.tight_layout()
    
    st.pyplot(fig2)

    # Botão de download do Gráfico 2
    st.download_button(
        label=" Baixar Distribuição",
        data=export_plot(fig2),
        file_name=f"distribuicao_{campus_selecionado}.png",
        mime="image/png"
    )

    # --- CONCLUSÃO ---
    top_fator = df_plot.iloc[0]['Fator']
    valor_max = df_plot.iloc[0]['Media']
    st.info(f" **Insight Acadêmico:** No campus **{campus_selecionado}**, o fator de maior peso é **'{top_fator}'**, com média de **{valor_max:.1f}**. Recomenda-se atenção prioritária a este ponto nas políticas de retenção.")

else:
    st.warning(f"Não foram encontrados dados para o campus: {campus_selecionado}")