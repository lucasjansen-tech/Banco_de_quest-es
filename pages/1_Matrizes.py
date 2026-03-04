import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestão de Matrizes", page_icon="⚙️", layout="wide")

# --- VERIFICAÇÃO DE SEGURANÇA ---
if not st.session_state.get('usuario_logado'):
    st.warning("⚠️ Por favor, faça o login na página inicial para acessar o sistema.")
    st.stop()

if st.session_state.get('perfil') != "Administrador":
    st.error("⛔ Acesso negado. Apenas Administradores podem configurar as matrizes.")
    st.stop()

# --- REPLICANDO O MENU LATERAL AQUI ---
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 Olá, {st.session_state.perfil}**")
    st.divider()
    
    st.markdown("### 📌 Navegação")
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.switch_page("app.py") # Comando novo para forçar a volta pro Login

# --- INICIALIZAÇÃO DE DADOS ---
if 'anos_ensino' not in st.session_state:
    st.session_state.anos_ensino = ["1º Ano", "2º Ano", "3º Ano"]
if 'habilidades' not in st.session_state:
    st.session_state.habilidades = []

st.title("⚙️ Configuração de Matrizes")

# ... (O restante do código das abas e importador continua igual daqui para baixo) ...
