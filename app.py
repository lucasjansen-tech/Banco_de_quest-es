import streamlit as st

# 1. Configuração base (Sempre a primeira linha)
st.set_page_config(page_title="Avalia System", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

# 2. Banco de Dados Temporário (Sessão)
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'habilidades' not in st.session_state:
    st.session_state.habilidades = [] # Simula a nossa Tabela 'Matrizes'
if 'anos_ensino' not in st.session_state:
    st.session_state.anos_ensino = []

# 3. TELA DE LOGIN OBRIGATÓRIA
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
                senha = st.text_input("Senha (admin ou prof)", type="password")
                if st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary"):
                    if email == "admin" and senha == "admin":
                        st.session_state.usuario_logado, st.session_state.perfil = True, "Administrador"
                        st.rerun()
                    elif email == "prof" and senha == "prof":
                        st.session_state.usuario_logado, st.session_state.perfil = True, "Elaborador"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
    st.stop() # Trava o código aqui se não logar

# 4. MENU LATERAL (Apenas para logados)
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.perfil}**")
    st.divider()
    
    st.markdown("### 📌 Navegação")
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    
    # Próximos passos (deixaremos comentados por enquanto)
    # st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    # st.page_link("pages/3_Buscar_Questoes.py", label="Banco de Questões", icon="🔍")
    
    st.divider()
        if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.rerun()

# 5. A TRAVA DE ARQUITETURA (O MOMENTO 0)
if len(st.session_state.habilidades) == 0:
    if st.session_state.perfil == "Administrador":
        st.warning("⚠️ Sistema Vazio: Você precisa importar a planilha de Matrizes antes de iniciar o ciclo.")
        st.switch_page("pages/1_Matrizes.py") # Força o admin a ir carregar os dados
    else:
        st.error("⛔ O sistema ainda não foi inicializado pela coordenação. Matrizes não encontradas.")
        st.stop() # Impede o professor de fazer qualquer coisa

# 6. DASHBOARD (Só chega aqui se tiver logado e se o Admin já tiver subido as matrizes)
st.header("📊 Dashboard do Ciclo Avaliativo")
st.write("Visão geral dos itens já estruturados no banco de dados.")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.metric("Língua Portuguesa", "0 itens", "Aguardando cadastro")
with col2:
    with st.container(border=True):
        st.metric("Matemática", "0 itens", "Aguardando cadastro")
with col3:
    with st.container(border=True):
        st.metric("Matrizes Carregadas", f"{len(st.session_state.habilidades)} habilidades", "Sistema Pronto")
