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

# --- NAVEGAÇÃO ---
with st.sidebar:
    st.title("🚀 Navegação")
    pagina = st.radio("Ir para:", ["Painel Mensal", "Evolução Anual"])
    st.divider()

# --- PÁGINA: PAINEL MENSAL ---
if pagina == "Painel Mensal":
    try:
        sh = conectar()
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_atual = meses[datetime.now().month - 1]
        
        st.title("📊 Painel Financeiro - Mensal")
        mes_sel = st.selectbox("Selecione o Mês", meses, index=meses.index(mes_atual))

        worksheet = sh.worksheet(mes_sel)
        dados = worksheet.get_all_records()
        df = pd.DataFrame(dados)

        with st.sidebar:
            st.header("📝 Novo Registro")
            with st.form("add_form", clear_on_submit=True):
                f_data = st.date_input("Data", datetime.now()).strftime('%d/%m/%Y')
                f_cat = st.radio("Categoria", ["Salário/Extra", "Moradia", "Transporte", "Alimentação", "Assinaturas/Internet", "Investimentos/Reserva", "Lazer", "Saúde", "Outros"], label_visibility="collapsed")
                f_desc = st.text_input("Descrição")
                f_val_raw = st.text_input("Valor (Ex: 91.95)")
                f_tipo = st.radio("Tipo", ["Saída", "Entrada"])
                
                if st.form_submit_button("Salvar na Planilha"):
                    try:
                        f_val = float(f_val_raw.replace(',', '.'))
                        worksheet.append_row([f_data, f_cat, f_desc, f_val, f_tipo])
                        st.success("Salvo!")
                        st.rerun()
                    except ValueError: st.error("Valor inválido.")
            
            if st.button("Sair / Logoff"):
                st.session_state['autenticado'] = False
                st.rerun()

        if not df.empty:
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').fillna(0)
            entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
            saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Entradas", formatar_moeda(entradas))
            c2.metric("Total Saídas", formatar_moeda(saidas))
            c3.metric("Saldo Atual", formatar_moeda(entradas - saidas))
            st.divider()
            
            col_rank, col_pizza, col_barras = st.columns(3)
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

            with col_barras:
                st.subheader("Entrada vs Saída")
                fig_b, ax_b = plt.subplots(facecolor='#0E1117')
                ax_b.set_facecolor('#0E1117')
                ax_b.bar(['Entradas', 'Saídas'], [entradas, saidas], color=['#00FF00', '#FF4B4B'])
                ax_b.tick_params(colors='white')
                st.pyplot(fig_b)

            st.divider()
            st.subheader("📋 Histórico Detalhado")
            df_visual = df.copy()
            df_visual['Valor'] = df_visual['Valor'].apply(formatar_moeda)
            st.dataframe(df_visual.style.applymap(lambda v: 'color: #00FF00' if v == 'Entrada' else 'color: #FF4B4B', subset=['Tipo']), use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- PÁGINA: EVOLUÇÃO ANUAL ---
elif pagina == "Evolução Anual":
    st.title("📈 Evolução Anual")
    st.write("Acompanhe o desempenho do seu dinheiro ao longo dos meses.")
    
    try:
        sh = conectar()
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        dados_ano = []

        # Coletando dados de cada aba
        for mes in meses:
            try:
                ws = sh.worksheet(mes)
                df_mes = pd.DataFrame(ws.get_all_records())
                if not df_mes.empty:
                    df_mes['Valor'] = pd.to_numeric(df_mes['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.'), errors='coerce').fillna(0)
                    ent = df_mes[df_mes['Tipo'] == 'Entrada']['Valor'].sum()
                    sai = df_mes[df_mes['Tipo'] == 'Saída']['Valor'].sum()
                    dados_ano.append({"Mês": mes, "Entradas": ent, "Saídas": sai, "Saldo": ent - sai})
            except: continue

        if dados_ano:
            df_ano = pd.DataFrame(dados_ano)
            
            # Gráfico de Evolução (Linha e Pontos)
            fig_ev, ax_ev = plt.subplots(figsize=(10, 5), facecolor='#0E1117')
            ax_ev.set_facecolor('#0E1117')
            
            ax_ev.plot(df_ano['Mês'], df_ano['Entradas'], marker='o', label='Entradas', color='#00FF00', linewidth=2)
            ax_ev.plot(df_ano['Mês'], df_ano['Saídas'], marker='o', label='Saídas', color='#FF4B4B', linewidth=2)
            ax_ev.plot(df_ano['Mês'], df_ano['Saldo'], marker='s', label='Saldo Líquido', color='#A78BFA', linestyle='--')
            
            ax_ev.tick_params(colors='white')
            ax_ev.legend()
            ax_ev.grid(True, alpha=0.1)
            st.pyplot(fig_ev)
            
            

            st.divider()
            st.subheader("Resumo Comparativo")
            df_ano_view = df_ano.copy()
            for col in ['Entradas', 'Saídas', 'Saldo']:
                df_ano_view[col] = df_ano_view[col].apply(formatar_moeda)
            st.table(df_ano_view)
        else:
            st.info("Ainda não há dados suficientes para gerar a evolução anual.")
            
    except Exception as e: st.error(f"Erro ao carregar evolução: {e}")
