import streamlit as st

# 1. Configuração base da página (Obrigatório ser a primeira linha do Streamlit)
st.set_page_config(
    page_title="Sistema de Avaliação - COTED",
    page_icon="📚",
    layout="wide"
)

# 2. Inicialização de Variáveis de Sessão (O nosso banco de dados temporário)
# Isso mantém os dados vivos enquanto navegamos pelas telas
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'perfil' not in st.session_state:
    st.session_state.perfil = None

# 3. Tela de Autenticação (Login Simples)
def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("📚 Avalia System")
        st.subheader("Acesso ao Banco de Questões")
        
        with st.form("login_form"):
            email = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                # Simulação de perfis para testarmos a interface depois
                if email == "admin" and senha == "admin":
                    st.session_state.usuario_logado = True
                    st.session_state.perfil = "Administrador"
                    st.rerun()
                elif email == "prof" and senha == "prof":
                    st.session_state.usuario_logado = True
                    st.session_state.perfil = "Elaborador"
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Tente admin/admin ou prof/prof.")

# 4. Dashboard Principal (O que o usuário vê após logar)
def tela_dashboard():
    # Controle da barra lateral
    st.sidebar.success(f"Logado como: {st.session_state.perfil}")
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.rerun()

    st.title("📊 Visão Geral do Sistema")
    st.write("Bem-vindo ao sistema central de estruturação de itens de avaliação.")
    
    # Métricas de exemplo focadas nos componentes estruturais
    col1, col2, col3 = st.columns(3)
    col1.metric("Questões de Língua Portuguesa", "215", "+5 cadastradas hoje")
    col2.metric("Questões de Matemática", "142", "+12 cadastradas hoje")
    col3.metric("Matrizes de Referência", "3", "Em atualização")
    
    st.divider()
    
    st.info("👈 Utilize o menu lateral para navegar entre o cadastro de habilidades, elaboração de questões e montagem do ciclo avaliativo.")
    
    # Exemplo de indicador visual para o ciclo de correção/elaboração
    st.subheader("Progresso do Ciclo Atual")
    st.progress(60, text="Meta de elaboração para o 1º Bimestre (60%)")

# 5. Lógica de Roteamento Principal
if not st.session_state.usuario_logado:
    tela_login()
else:
    tela_dashboard()
