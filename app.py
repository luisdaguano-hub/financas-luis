import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Finanças do Luis", layout="wide")

# Função para formatar números para o padrão brasileiro (R$ 1.234,56)
def formatar_br(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_dados():
    try:
        # Carrega o arquivo e pula a linha de cabeçalho se ela estiver vindo como dado
        df = pd.read_excel('Planilha.xlsx').iloc[:, :5]
        df.columns = ['Data', 'Categoria', 'Descrição', 'Valor', 'Tipo']
        
        # Filtro para remover linhas onde a coluna Data repete a palavra "Data"
        df = df[df['Data'].astype(str) != 'Data']
        
        # Limpeza e conversão
        df['Categoria'] = df['Categoria'].replace({'Laser': 'Lazer', 'Valentia': 'Venda'})
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0).round(2)
        return df
    except Exception as e:
        # Se der erro (arquivo faltando, etc), cria um DataFrame vazio com as colunas certas
        return pd.DataFrame(columns=['Data', 'Categoria', 'Descrição', 'Valor', 'Tipo'])

df = carregar_dados()

st.title("📊 Finanças do Luis")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📝 Novo Registro")
    with st.form("meu_form", clear_on_submit=True):
        st.date_input("Data", datetime.now())
        st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Contas", "Salário", "Outros"])
        st.text_input("Descrição")
        st.number_input("Valor", min_value=0.0, step=0.01)
        st.radio("Tipo", ["Saída", "Entrada"])
        if st.form_submit_button("Salvar"):
            st.success("Dados prontos!")

# --- MÉTRICAS ---
entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
gastos = df[df['Tipo'] == 'Saída']['Valor'].sum()
saldo = entradas - gastos

c1, c2, c3 = st.columns(3)
c1.metric("Total Entradas", formatar_br(entradas))
c2.metric("Total Gastos", formatar_br(gastos))
c3.metric("Saldo Atual", formatar_br(saldo))

st.divider()

# --- GRÁFICO E RESUMO ---
gastos_df = df[df['Tipo'] == 'Saída']
if not gastos_df.empty:
    resumo = gastos_df.groupby('Categoria')['Valor'].sum().reset_index()
    col_tab, col_pie = st.columns([1, 1])
    with col_tab:
        st.subheader("Valores por Categoria")
        resumo_view = resumo.copy()
        resumo_view['Valor'] = resumo_view['Valor'].apply(formatar_br)
        st.table(resumo_view)
    with col_pie:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(resumo['Valor'], labels=resumo['Categoria'], autopct='%1.1f%%', startangle=140)
        st.pyplot(fig)

st.divider()
st.subheader("📋 Histórico Completo")

df_visual = df.copy()
df_visual['Valor'] = df_visual['Valor'].apply(formatar_br)

st.dataframe(
    df_visual.style.set_properties(**{'text-align': 'left'}), 
    use_container_width=True,
    hide_index=True
)
