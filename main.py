import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Configuração da página para aproveitar o espaço da tela
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
    
   
    peso_respostas = {
        "Determinante": 4,
        "Muito Relevante": 3,
        "Relevante": 2,
        "Pouco Relevante": 1,
        "Indiferente": 0
    }
    return df, peso_respostas

df, pesos = load_data()


coluna_campus = next((col for col in df.columns if "campus" in col.lower()), None)

if not coluna_campus:
    st.error("Coluna de Campus não encontrada. Verifique os títulos do arquivo CSV.")
    st.stop()


st.sidebar.header("Configurações da Análise")
campi = df[coluna_campus].unique()
campus_selecionado = st.sidebar.selectbox("Selecione o Campus para filtrar:", campi)


cols_desistencia = [c for c in df.columns if "desistirem" in c]

# Extrai o nome amigável do fator (o texto dentro dos colchetes)
labels = []
for c in cols_desistencia:
    try:
        labels.append(c.split('[')[1].split(']')[0])
    except IndexError:
        labels.append(c)

# Filtrar dados específicos do campus
df_campus = df[df[coluna_campus] == campus_selecionado]
total_alunos = len(df_campus)

if not df_campus.empty:
    # --- Card de Entendimento (O que é o Fator de Relevância) ---
    with st.expander(" O que significa o Índice de Relevância?", expanded=True):
        st.markdown("""
        ###  Como ler este gráfico
        Este índice representa a **média das opiniões** dos alunos do campus selecionado. 
        Quanto mais próximo de **4.0**, mais crítico é o fator para a permanência dos estudantes.
        
        | Nível | Impacto na Evasão |
        | :--- | :--- |
        | **4.0** | **Determinante:** Causa principal da desistência. |
        | **3.0** | **Muito Relevante:** Impacto forte na decisão. |
        | **2.0** | **Relevante:** Influência moderada. |
        | **1.0** | **Pouco Relevante:** Baixo impacto. |
        | **0.0** | **Indiferente:** Não influenciou. |
        """)

    
    df_numerico = df_campus[cols_desistencia].replace(pesos)
    for col in df_numerico.columns:
        df_numerico[col] = pd.to_numeric(df_numerico[col], errors='coerce')
    
 
    media_fatores = df_numerico.mean().fillna(0)
    df_plot = pd.DataFrame({
        'Fator': labels,
        'Nivel': media_fatores.values
    }).sort_values(by='Nivel', ascending=False)

   
    c1, c2 = st.columns(2)
    c1.metric("Campus Atual", campus_selecionado)
    c2.metric("Amostragem", f"{total_alunos} alunos")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    
    palette = sns.color_palette("Reds_r", n_colors=len(df_plot))
    
    sns.barplot(data=df_plot, x='Nivel', y='Fator', palette=palette, ax=ax)

   
    for i in ax.containers:
        ax.bar_label(i, fmt='%.1f', padding=8, fontsize=11, fontweight='bold')

   
    ax.set_title(f"Principais Causas de Evasão - {campus_selecionado}", fontsize=18, pad=20, fontweight='bold')
    ax.set_xlabel("Índice de Relevância Médio (0 a 4)", fontsize=12)
    ax.set_ylabel("")
    ax.set_xlim(0, 4.5) 
    
    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    st.pyplot(fig)
    

    top_fator = df_plot.iloc[0]['Fator']
    impacto = df_plot.iloc[0]['Nivel']
    st.success(f" **Conclusão:** No campus **{campus_selecionado}**, o fator **'{top_fator}'** é a maior preocupação, com impacto médio de **{impacto:.1f}**.")

else:
    st.warning(f"Não existem dados cadastrados para o campus: {campus_selecionado}")