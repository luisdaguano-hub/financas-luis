import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças do Luis", layout="wide")

# Estilo Azul e Roxo
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 2px solid #6D28D9; }
    .stButton>button { background-color: #6D28D9; color: white; border-radius: 8px; width: 100%; }
    h1, h2, h3 { color: #A78BFA; }
    [data-testid="stMetricValue"] { color: #8B5CF6; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO GOOGLE SHEETS ---
def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet"]["id"])

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        senha_input = st.text_input("Chave de Segurança", type="password")
        if st.button("Entrar"):
            if senha_input == "5507(ISFhjc":
                st.session_state['autenticado'] = True
                st.rerun()
    st.stop()

# --- APP PRINCIPAL ---
try:
    sh = conectar()
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_atual = meses[datetime.now().month - 1]
    
    st.title("📊 Painel Financeiro Luis")
    mes_sel = st.selectbox("Selecione o Mês", meses, index=meses.index(mes_atual))
    
    # Carregar aba
    worksheet = sh.worksheet(mes_sel)
    dados = worksheet.get_all_records()
    df = pd.DataFrame(dados)

    # --- FORMULÁRIO NA LATERAL ---
    with st.sidebar:
        st.header("📝 Novo Registro")
        with st.form("add_form", clear_on_submit=True):
            f_data = st.date_input("Data", datetime.now()).strftime('%d/%m/%Y')
            f_cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Salário", "Outros"])
            f_desc = st.text_input("Descrição")
            f_val = st.number_input("Valor", min_value=0.0, step=0.01)
            f_tipo = st.radio("Tipo", ["Saída", "Entrada"])
            
            if st.form_submit_button("Salvar na Planilha"):
                worksheet.append_row([f_data, f_cat, f_desc, f_val, f_tipo])
                st.success("Dados salvos!")
                st.rerun()
        
        if st.button("Sair"):
            st.session_state['autenticado'] = False
            st.rerun()

    # --- DASHBOARD ---
    if not df.empty:
        df['Valor'] = pd.to_numeric(df['Valor']).fillna(0)
        entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Saídas", f"R$ {saidas:,.2f}")
        c3.metric("Saldo", f"R$ {(entradas - saidas):,.2f}")

        st.divider()
        
        # Gráfico e Tabela
        saidas_df = df[df['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.table(saidas_df)
        with col2:
            fig, ax = plt.subplots(facecolor='#0E1117')
            ax.pie(saidas_df['Valor'], labels=saidas_df['Categoria'], autopct='%1.1f%%', textprops={'color':"w"})
            st.pyplot(fig)

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para este mês.")

except Exception as e:
    st.error(f"Erro: {e}. Verifique se a aba '{mes_sel}' existe na planilha.")
