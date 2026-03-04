import streamlit as st

# 1. Configuração base da página
st.set_page_config(
    page_title="Avalia System - COTED",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed" # Começa com a barra fechada
)

# 2. Inicialização de Variáveis de Sessão
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None

# 3. TELA DE LOGIN (UI Moderna)
def tela_login():
    # CSS para esconder completamente a barra lateral na tela de login
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Usamos colunas para centralizar o formulário
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True) # Dá um espaço do topo
        
        # Cria um visual de "Cartão" com borda sutil
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>📚 Avalia System</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Central de Gestão de Avaliações</p>", unsafe_allow_html=True)
            st.divider()
            
            with st.form("login_form"):
                email = st.text_input("Usuário", placeholder="Digite seu usuário (ex: admin)")
                senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                
                # Botão com a cor primária (type="primary")
                submit = st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary")
                
                if submit:
                    if email == "admin" and senha == "admin":
                        st.session_state.usuario_logado = True
                        st.session_state.perfil = "Administrador"
                        st.rerun()
                    elif email == "prof" and senha == "prof":
                        st.session_state.usuario_logado = True
                        st.session_state.perfil = "Elaborador"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")

# 4. SISTEMA LOGADO (Dashboard e Menu Customizado)
def sistema_logado():
    # --- CONSTRUÇÃO DO NOSSO PRÓPRIO MENU LATERAL ---
    with st.sidebar:
        st.title("📚 Avalia System")
        st.markdown(f"**👤 Olá, {st.session_state.perfil}**")
        st.divider()
        
        st.markdown("### 📌 Navegação")
        # Links de navegação modernos (Substituem o padrão do Streamlit)
        st.page_link("app.py", label="Dashboard Principal", icon="📊")
        
        if st.session_state.perfil == "Administrador":
            st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
        
        # Quando criarmos a tela de elaboração, descomentamos a linha abaixo:
        # st.page_link("pages/2_Elaborar_Questoes.py", label="Elaborar Questões", icon="📝")
        
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.usuario_logado = False
            st.session_state.perfil = None
            st.rerun()

    # --- CONTEÚDO DO DASHBOARD ---
    st.header("📊 Visão Geral do Sistema")
    st.write("Acompanhe o volume de itens disponíveis para o ciclo avaliativo.")
    
    col1, col2, col3 = st.columns(3)
    # Criando cards de métricas usando containers para ficar mais elegante
    with col1:
        with st.container(border=True):
            st.metric("Língua Portuguesa", "215 itens", "+5 na semana")
    with col2:
        with st.container(border=True):
            st.metric("Matemática", "142 itens", "+12 na semana")
    with col3:
        with st.container(border=True):
            st.metric("Matrizes de Referência", "3 cadastradas", "Em revisão")
    
    st.divider()
    st.info("👈 Utilize o menu lateral para navegar pelas funcionalidades do sistema.")

# 5. ROTEAMENTO
if not st.session_state.usuario_logado:
    tela_login()
else:
    sistema_logado()
