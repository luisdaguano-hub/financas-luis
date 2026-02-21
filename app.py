import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças do Luis - Pro", layout="wide")

# Estilo Personalizado
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 2px solid #6D28D9; }
    .stButton>button { background-color: #6D28D9; color: white; border-radius: 8px; width: 100%; }
    h1, h2, h3 { color: #A78BFA; }
    [data-testid="stMetricValue"] { color: #8B5CF6; }
    div[data-testid="stRadio"] > label { font-weight: bold; color: #A78BFA; }
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def formatar_moeda(valor):
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
    st.stop()

# --- APP PRINCIPAL ---
try:
    sh = conectar()
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_atual = meses[datetime.now().month - 1]
    
    st.title("📊 Painel Financeiro - Luis Felipe")
    mes_sel = st.selectbox("Selecione o Mês", meses, index=meses.index(mes_atual))

    worksheet = sh.worksheet(mes_sel)
    dados = worksheet.get_all_records()
    df = pd.DataFrame(dados)

    with st.sidebar:
        st.header("📝 Novo Registro")
        with st.form("add_form", clear_on_submit=True):
            f_data = st.date_input("Data", datetime.now()).strftime('%d/%m/%Y')
            st.write("**Selecione a Categoria:**")
            f_cat = st.radio(
                "Categoria", 
                ["Salário/Extra", "Moradia", "Transporte", "Alimentação", "Assinaturas/Internet", "Investimentos/Reserva", "Lazer", "Saúde", "Outros"],
                label_visibility="collapsed"
            )
            f_desc = st.text_input("Descrição")
            f_val_raw = st.text_input("Valor (Ex: 91.95)")
            f_tipo = st.radio("Tipo", ["Saída", "Entrada"])
            
            if st.form_submit_button("Salvar na Planilha"):
                try:
                    f_val = float(f_val_raw.replace(',', '.'))
                    worksheet.append_row([f_data, f_cat, f_desc, f_val, f_tipo])
                    st.success("Salvo!")
                    st.rerun()
                except ValueError:
                    st.error("Digite um valor válido.")
        
        if st.button("Sair / Logoff"):
            st.session_state['autenticado'] = False
            st.rerun()

    if not df.empty:
        df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

        entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", formatar_moeda(entradas))
        c2.metric("Total Saídas", formatar_moeda(saidas))
        c3.metric("Saldo Atual", formatar_moeda(entradas - saidas))

        st.divider()
        
        # --- COLUNAS PARA O RANKING E OS GRÁFICOS ---
        col_rank, col_pizza, col_barras = st.columns([1, 1, 1])
        
        df_gastos = df[(df['Tipo'] == 'Saída') & (df['Categoria'] != 'Salário/Extra')]
        saidas_resumo = df_gastos.groupby('Categoria')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=False)
        
        with col_rank:
            st.subheader("🏆 Top 3 Gastos")
            if not saidas_resumo.empty:
                top_3 = saidas_resumo.head(3).copy()
                top_3.insert(0, 'Ranking', ["1º 🥇", "2º 🥈", "3º 🥉"][:len(top_3)])
                top_3['Valor'] = top_3['Valor'].apply(formatar_moeda)
                st.table(top_3)
            else: st.info("Sem gastos.")
            
        with col_pizza:
            st.subheader("Distribuição")
            if not saidas_resumo.empty:
                fig_p, ax_p = plt.subplots(facecolor='#0E1117')
                ax_p.set_facecolor('#0E1117')
                ax_p.pie(saidas_resumo['Valor'], labels=saidas_resumo['Categoria'], autopct='%1.1f%%', textprops={'color':"w"}, startangle=140)
                st.pyplot(fig_p)

        # --- NOVO: GRÁFICO DE PRÉDIO (BARRAS) COMPARATIVO ---
        with col_barras:
            st.subheader("Entrada vs Saída")
            fig_b, ax_b = plt.subplots(facecolor='#0E1117')
            ax_b.set_facecolor('#0E1117')
            
            categorias_comp = ['Entradas', 'Saídas']
            valores_comp = [entradas, saidas]
            cores = ['#00FF00', '#FF4B4B'] # Verde para entrada, Vermelho para saída
            
            bars = ax_b.bar(categorias_comp, valores_comp, color=cores)
            ax_b.tick_params(axis='x', colors='white')
            ax_b.tick_params(axis='y', colors='white')
            # Remove bordas para ficar mais limpo
            for spine in ax_b.spines.values(): spine.set_visible(False)
            
            st.pyplot(fig_b)

        st.divider()
        st.subheader("📋 Histórico Detalhado")
        def colorir_tipo(valor):
            if valor == 'Entrada': return 'color: #00FF00; font-weight: bold'
            elif valor == 'Saída': return 'color: #FF4B4B; font-weight: bold'
            return ''
        df_visual = df.copy()
        df_visual['Valor'] = df_visual['Valor'].apply(formatar_moeda)
        st.dataframe(df_visual.style.applymap(colorir_tipo, subset=['Tipo']), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")
