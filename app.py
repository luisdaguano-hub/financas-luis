import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças do Luis - Pro", layout="wide")

# Estilo Personalizado (Azul Escuro e Roxo)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 2px solid #6D28D9; }
    .stButton>button { background-color: #6D28D9; color: white; border-radius: 8px; width: 100%; }
    h1, h2, h3 { color: #A78BFA; }
    [data-testid="stMetricValue"] { color: #8B5CF6; }
    .stTable { background-color: #1F2937; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def formatar_moeda(valor):
    """Transforma 1200.50 em R$ 1.200,50"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["spreadsheet"]["id"])

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        senha_input = st.text_input("Chave de Segurança", type="password")
        if st.button("Entrar no Sistema"):
            if senha_input == "5507(ISFhjc":
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Chave incorreta!")
    st.stop()

# --- APP PRINCIPAL (LOGADO) ---
try:
    sh = conectar()
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_atual = meses[datetime.now().month - 1]
    
    st.title("📊 Painel Financeiro - Luis Felipe")
    
    col_topo1, col_topo2 = st.columns([2, 1])
    with col_topo1:
        mes_sel = st.selectbox("Selecione o Mês de Referência", meses, index=meses.index(mes_atual))

    # Carregar dados da aba do Google Sheets
    worksheet = sh.worksheet(mes_sel)
    dados = worksheet.get_all_records()
    df = pd.DataFrame(dados)

    # --- BARRA LATERAL (CADASTRO E LOGOFF) ---
    with st.sidebar:
        st.header("📝 Novo Registro")
        with st.form("add_form", clear_on_submit=True):
            f_data = st.date_input("Data", datetime.now()).strftime('%d/%m/%Y')
            f_cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Educação", "Salário", "Outros"])
            f_desc = st.text_input("Descrição")
            f_val = st.number_input("Valor", min_value=0.0, step=0.01)
            f_tipo = st.radio("Tipo", ["Saída", "Entrada"])
            
            if st.form_submit_button("Salvar na Planilha"):
                # Salva no Google Sheets (valor puro para não dar erro depois)
                worksheet.append_row([f_data, f_cat, f_desc, f_val, f_tipo])
                st.success("Dados salvos com sucesso!")
                st.rerun()
        
        st.write("---")
        if st.button("Sair / Logoff"):
            st.session_state['autenticado'] = False
            st.rerun()

    # --- PROCESSAMENTO E EXIBIÇÃO DO DASHBOARD ---
    if not df.empty:
        # LIMPEZA DOS DADOS (Trata R$, pontos e vírgulas vindo da planilha)
        df['Valor'] = (
            df['Valor'].astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

        # Cálculos de Totais
        entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas

        # Cartões de Métricas (Com R$ e Vírgula)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", formatar_moeda(entradas))
        c2.metric("Total Saídas", formatar_moeda(saidas))
        c3.metric("Saldo Atual", formatar_moeda(saldo))

        st.divider()
        
        # Resumo por Categoria e Gráfico
        saidas_df = df[df['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Gastos por Categoria")
            # Exibição da tabela formatada
            exibir_resumo = saidas_df.copy()
            exibir_resumo['Valor'] = exibir_resumo['Valor'].apply(formatar_moeda)
            st.table(exibir_resumo)
            
        with col_graf2:
            st.subheader("Distribuição Percentual")
            if not saidas_df.empty:
                fig, ax = plt.subplots(facecolor='#0E1117')
                ax.set_facecolor('#0E1117')
                ax.pie(saidas_df['Valor'], labels=saidas_df['Categoria'], autopct='%1.1f%%', textprops={'color':"w"}, startangle=140)
                st.pyplot(fig)

        st.divider()
        st.subheader(f"📋 Histórico Detalhado - {mes_sel}")
        # Tabela completa formatada
        df_visual = df.copy()
        df_visual['Valor'] = df_visual['Valor'].apply(formatar_moeda)
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum dado encontrado para o mês de {mes_sel}. Adicione um registro na barra lateral!")

except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("Dica: Verifique se o ID da planilha nos Secrets está correto e se as abas dos meses existem.")
