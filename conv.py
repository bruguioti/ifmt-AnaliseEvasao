import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar os dados
df = pd.read_csv("dados1.csv")

st.title("Análise de Dados - Pesquisa Tangará")

# Exemplo: Gráfico de contagem por Curso
st.subheader("Distribuição por Tipo de Curso")
fig_curso = px.pie(df, names='Curso', title="Percentagem de Estudantes por Curso")
st.plotly_chart(fig_curso)

# Exemplo: Analisar uma pergunta específica (ex: Pergunta 1)
st.subheader("Nível de Relevância - Pergunta 1")
contagem_p1 = df['Pergunta_1'].value_counts().reset_index()
fig_p1 = px.bar(contagem_p1, x='Pergunta_1', y='count', color='Pergunta_1', 
                labels={'count': 'Quantidade', 'Pergunta_1': 'Resposta'})
st.plotly_chart(fig_p1)