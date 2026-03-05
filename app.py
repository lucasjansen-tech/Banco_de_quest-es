import streamlit as st
from supabase import create_client

# 1. Configuração base
st.set_page_config(page_title="Avalia System", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

# 2. CONEXÃO COM O SUPABASE (O Banco Oficial)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 3. Variáveis de Sessão de Login
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None

# 4. TELA DE LOGIN OBRIGATÓRIA
if not st.session_state.usuario_logado:
    st.markdown("""<style>[data-testid="collapsedControl"] {display: none;} [data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>📚 Avalia System</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Autenticação Obrigatória</p>", unsafe_allow_html=True)
            st.divider()
            with st.form("login_form"):
                email = st.text_input("Usuário (admin ou prof)")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary"):
                    if email == "admin" and senha == "admin":
                        st.session_state.usuario_logado, st.session_state.perfil = True, "Administrador"
                        st.rerun()
                    elif email == "prof" and senha == "prof":
                        st.session_state.usuario_logado, st.session_state.perfil = True, "Elaborador"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
    st.stop()

# 5. MENU LATERAL
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.perfil}**")
    st.divider()
    st.markdown("### 📌 Navegação")
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.rerun()

# 6. A TRAVA DO BANCO DE DADOS (MOMENTO 0)
# Vamos perguntar ao Supabase se a tabela 'matrizes' tem dados
try:
    resposta = supabase.table("matrizes").select("id").limit(1).execute()
    banco_vazio = len(resposta.data) == 0
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")
    st.stop()

if banco_vazio:
    if st.session_state.perfil == "Administrador":
        st.warning("⚠️ Banco de Dados Vazio: Você precisa importar a planilha de Matrizes antes de iniciar o ciclo.")
        st.switch_page("pages/1_Matrizes.py") 
    else:
        st.error("⛔ O sistema ainda não foi inicializado pela coordenação. Matrizes não encontradas no Banco de Dados Oficial.")
        st.stop() 

# 7. DASHBOARD (Lendo do Banco Real)
st.header("📊 Dashboard do Ciclo Avaliativo")
st.write("Visão geral dos itens já estruturados no banco de dados oficial.")

try:
    total_matrizes = len(supabase.table("matrizes").select("id").execute().data)
    total_questoes = len(supabase.table("questoes").select("id").execute().data)
except:
    total_matrizes, total_questoes = 0, 0

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.metric("Total de Questões", f"{total_questoes} itens", "No banco de dados")
with col2:
    with st.container(border=True):
        st.metric("Matrizes Carregadas", f"{total_matrizes} habilidades", "Prontas para uso")
with col3:
    with st.container(border=True):
        st.metric("Status do Servidor", "Online", "Conectado ao Supabase")
