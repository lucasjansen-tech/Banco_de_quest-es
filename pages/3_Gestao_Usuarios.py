import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão de Usuários", page_icon="👥", layout="wide")

# --- SEGURANÇA MÁXIMA ---
# Apenas quem está logado E é Administrador pode ver esta tela
if not st.session_state.get('usuario_logado') or st.session_state.get('perfil') != "Administrador":
    st.error("Acesso negado. Apenas Administradores podem acessar este painel.")
    st.switch_page("app.py")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

# --- MENU LATERAL ---
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.nome_usuario.title()}**")
    st.caption(f"Perfil: {st.session_state.perfil}")
    st.divider()
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    st.page_link("pages/3_Gestao_Usuarios.py", label="Gestão de Usuários", icon="👥")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

st.title("👥 Gestão de Usuários e Acessos")
st.write("Crie contas para os elaboradores da sua rede e controle as permissões do sistema.")

aba_listar, aba_criar = st.tabs(["📋 Usuários Cadastrados", "➕ Cadastrar Novo Usuário"])

# --- ABA 1: CADASTRAR NOVO USUÁRIO ---
with aba_criar:
    with st.container(border=True):
        with st.form("form_novo_usuario", clear_on_submit=True):
            st.subheader("Dados do Novo Acesso")
            col1, col2, col3 = st.columns(3)
            with col1:
                novo_user = st.text_input("Login do Usuário*", placeholder="Ex: maria.matematica").strip().lower()
            with col2:
                nova_senha = st.text_input("Senha Inicial*", type="password")
            with col3:
                novo_perfil = st.selectbox("Perfil de Acesso*", ["Elaborador", "Administrador"])
            
            st.info("💡 Dica: O Elaborador só vê as próprias questões. O Administrador tem acesso total.")
            submit_user = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if submit_user:
                if novo_user and nova_senha:
                    try:
                        # Verifica se o usuário já existe para não dar erro feio na tela
                        checagem = supabase.table("usuarios").select("id").eq("usuario", novo_user).execute()
                        if len(checagem.data) > 0:
                            st.error(f"O usuário '{novo_user}' já existe no banco de dados!")
                        else:
                            supabase.table("usuarios").insert({
                                "usuario": novo_user,
                                "senha": nova_senha,
                                "perfil": novo_perfil,
                                "ativo": True
                            }).execute()
                            st.success(f"🎉 Usuário '{novo_user}' cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao criar usuário: {e}")
                else:
                    st.warning("Preencha o Login e a Senha para continuar.")

# --- ABA 2: LISTAR E GERENCIAR ---
with aba_listar:
    try:
        resposta = supabase.table("usuarios").select("id, usuario, perfil, ativo, created_at").execute()
        if len(resposta.data) > 0:
            df_users = pd.DataFrame(resposta.data)
            
            # Ajustando colunas para a tabela ficar bonita
            df_users['Status'] = df_users['ativo'].apply(lambda x: "🟢 Ativo" if x else "🔴 Bloqueado")
            df_users['Data de Criação'] = pd.to_datetime(df_users['created_at']).dt.strftime('%d/%m/%Y')
            df_users = df_users[['usuario', 'perfil', 'Status', 'Data de Criação']]
            df_users.rename(columns={'usuario': 'Login do Usuário', 'perfil': 'Perfil'}, inplace=True)
            
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("⚙️ Ações Rápidas")
            st.caption("Selecione um usuário para bloquear o acesso ou excluí-lo definitivamente.")
            
            col_acao1, col_acao2 = st.columns([1, 2])
            with col_acao1:
                lista_usuarios = df_users['Login do Usuário'].tolist()
                user_selecionado = st.selectbox("Usuário alvo:", lista_usuarios)
                
            with col_acao2:
                st.write("") # Espaçamento para alinhar os botões com o selectbox
                st.write("")
                c1, c2 = st.columns(2)
                
                # Descobre se o alvo está ativo ou não
                alvo_ativo = "🟢" in df_users[df_users['Login do Usuário'] == user_selecionado]['Status'].values[0]
                
                with c1:
                    texto_botao = "🔴 Bloqueio Temporário" if alvo_ativo else "🟢 Liberar Acesso"
                    if st.button(texto_botao, use_container_width=True):
                        if user_selecionado == "admin":
                            st.error("Acesso Negado: Você não pode bloquear o Administrador Master!")
                        else:
                            novo_status = not alvo_ativo
                            supabase.table("usuarios").update({"ativo": novo_status}).eq("usuario", user_selecionado).execute()
                            st.rerun()
                            
                with c2:
                    if st.button("🗑️ Excluir Definitivamente", use_container_width=True):
                        if user_selecionado == "admin":
                            st.error("Acesso Negado: O Administrador Master é vitalício e não pode ser apagado.")
                        else:
                            supabase.table("usuarios").delete().eq("usuario", user_selecionado).execute()
                            st.rerun()
        else:
            st.info("Apenas o Administrador Master está cadastrado.")
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
