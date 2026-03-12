import streamlit as st
from supabase import create_client

# 1. Configuração base
st.set_page_config(page_title="Avalia System", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

# 2. CONEXÃO COM O SUPABASE
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

# 3. Variáveis de Sessão
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'nome_usuario' not in st.session_state:
    st.session_state.nome_usuario = None
if 'componente' not in st.session_state:
    st.session_state.componente = None

# 4. TELA DE LOGIN SIMPLES E BLINDADA
if not st.session_state.usuario_logado:
    st.markdown("""<style>[data-testid="collapsedControl"] {display: none;} [data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>📚 Avalia System</h2>", unsafe_allow_html=True)
            st.divider()
            with st.form("login_form"):
                usuario_input = st.text_input("Usuário de Acesso")
                senha_input = st.text_input("Senha", type="password")
                
                if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                    usuario_input = usuario_input.strip().lower()
                    
                    if usuario_input and senha_input:
                        with st.spinner("Autenticando..."):
                            try:
                                # Vai no banco verificar as credenciais
                                resposta = supabase.table("usuarios").select("*").eq("usuario", usuario_input).eq("senha", senha_input).eq("ativo", True).execute()
                                
                                if len(resposta.data) > 0:
                                    dados_user = resposta.data[0]
                                    
                                    # Grava os dados na memória (Sessão)
                                    st.session_state.usuario_logado = True
                                    st.session_state.perfil = dados_user['perfil']
                                    st.session_state.nome_usuario = dados_user['usuario']
                                    st.session_state.componente = dados_user.get('componente', 'Todos') # Puxa a matéria direto do banco!
                                    
                                    st.rerun()
                                else:
                                    st.error("❌ Usuário ou senha incorretos, ou conta desativada.")
                            except Exception as e:
                                st.error(f"Erro de conexão: {e}")
                    else:
                        st.warning("Preencha o usuário e a senha.")
    st.stop()

# 5. MENU LATERAL HIERÁRQUICO
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.nome_usuario.title()}**")
    
    # Mostra qual a disciplina do professor no menu
    texto_perfil = f"Perfil: {st.session_state.perfil}"
    if st.session_state.perfil == "Elaborador":
        texto_perfil += f" ({st.session_state.componente})"
    st.caption(texto_perfil)
    
    st.divider()
    
    # Link comum a todos
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    
    # Links EXCLUSIVOS do Administrador
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
        st.page_link("pages/3_Gestao_Usuarios.py", label="Gestão de Usuários", icon="👥")
        
    # Links Operacionais (Ambos acessam)
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.page_link("pages/4_Banco_Questoes.py", label="Banco de Questões", icon="🗄️")
    
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 6. DASHBOARD (Visão de Acordo com o Perfil)
st.header("📊 Dashboard do Ciclo Avaliativo")

try:
    total_matrizes = len(supabase.table("matrizes").select("id").execute().data)
    
    if st.session_state.perfil == "Administrador":
        st.write("Visão Global: Total de itens na rede.")
        total_questoes = len(supabase.table("questoes").select("id").execute().data)
    else:
        st.write(f"Visão Isolada: Mostrando seu progresso em **{st.session_state.componente}**.")
        total_questoes = len(supabase.table("questoes").select("id").eq("autor", st.session_state.nome_usuario).execute().data)
        
except Exception as e:
    total_matrizes, total_questoes = 0, 0

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.metric("Suas Questões" if st.session_state.perfil == "Elaborador" else "Total de Questões (Rede)", f"{total_questoes} itens")
with col2:
    with st.container(border=True):
        st.metric("Matrizes Carregadas", f"{total_matrizes} habilidades")
