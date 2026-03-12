import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão de Usuários", page_icon="👥", layout="wide")

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
    st.divider()
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    st.page_link("pages/3_Gestao_Usuarios.py", label="Gestão de Usuários", icon="👥")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.page_link("pages/4_Banco_Questoes.py", label="Banco de Questões", icon="🗄️")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

st.title("👥 Gestão de Usuários e Acessos")

# Lista oficial de componentes da sua rede
componentes_rede = ["Língua Portuguesa", "Matemática", "Ciências", "História", "Geografia", "Inglês", "Arte", "Educação Física"]

aba_listar, aba_criar, aba_editar = st.tabs(["📋 Listar e Gerenciar", "➕ Novo Usuário", "✏️ Editar Usuário"])

# --- ABA 1: LISTAR E GERENCIAR ---
with aba_listar:
    try:
        # PROTEÇÃO MASTER: Oculta o usuário 'admin' da visão de outros administradores
        query = supabase.table("usuarios").select("id, usuario, perfil, componente, ativo")
        if st.session_state.nome_usuario != "admin":
            query = query.neq("usuario", "admin")
            
        resposta = query.execute()
        
        if len(resposta.data) > 0:
            df_users = pd.DataFrame(resposta.data)
            df_users['Status'] = df_users['ativo'].apply(lambda x: "🟢 Ativo" if x else "🔴 Bloqueado")
            df_users = df_users[['usuario', 'perfil', 'componente', 'Status']]
            df_users.rename(columns={'usuario': 'Login', 'perfil': 'Perfil', 'componente': 'Disciplina'}, inplace=True)
            
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("⚙️ Ações Rápidas (Bloqueio / Exclusão)")
            
            col_acao1, col_acao2 = st.columns([1, 2])
            with col_acao1:
                lista_usuarios = df_users['Login'].tolist()
                user_selecionado = st.selectbox("Usuário alvo para ação:", lista_usuarios)
                
            with col_acao2:
                st.write("<br><br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                alvo_ativo = "🟢" in df_users[df_users['Login'] == user_selecionado]['Status'].values[0]
                
                with c1:
                    texto_botao = "🔴 Bloquear Acesso" if alvo_ativo else "🟢 Liberar Acesso"
                    if st.button(texto_botao, use_container_width=True):
                        if user_selecionado == "admin":
                            st.error("Proteção Ativa: Impossível bloquear o Master.")
                        else:
                            supabase.table("usuarios").update({"ativo": not alvo_ativo}).eq("usuario", user_selecionado).execute()
                            st.rerun()
                            
                with c2:
                    if st.button("🗑️ Excluir Definitivamente", use_container_width=True):
                        if user_selecionado == "admin":
                            st.error("Proteção Ativa: Impossível excluir o Master.")
                        else:
                            supabase.table("usuarios").delete().eq("usuario", user_selecionado).execute()
                            st.rerun()
    except Exception as e:
        st.info("Nenhum usuário encontrado ou erro de conexão.")

# --- ABA 2: CADASTRAR NOVO USUÁRIO ---
with aba_criar:
    with st.container(border=True):
        st.subheader("Dados do Novo Acesso")
        novo_user = st.text_input("Login do Usuário*", placeholder="Ex: joao.mat")
        nova_senha = st.text_input("Senha Inicial*", type="password")
        
        c1, c2 = st.columns(2)
        with c1: novo_perfil = st.selectbox("Perfil de Acesso*", ["Elaborador", "Administrador"])
        with c2: 
            # Se for Admin, não precisa travar em uma matéria
            novo_comp = st.selectbox("Componente Curricular*", componentes_rede, disabled=(novo_perfil == "Administrador"))
        
        if st.button("💾 Cadastrar Conta", type="primary"):
            if novo_user and nova_senha:
                checagem = supabase.table("usuarios").select("id").eq("usuario", novo_user).execute()
                if len(checagem.data) > 0:
                    st.error("Este login já existe!")
                else:
                    supabase.table("usuarios").insert({
                        "usuario": novo_user.strip().lower(),
                        "senha": nova_senha,
                        "perfil": novo_perfil,
                        "componente": novo_comp if novo_perfil == "Elaborador" else "Todos",
                        "ativo": True
                    }).execute()
                    st.success(f"🎉 Conta '{novo_user}' criada com sucesso!")
            else:
                st.warning("Preencha Login e Senha.")

# --- ABA 3: EDITAR USUÁRIO ---
with aba_editar:
    with st.container(border=True):
        st.subheader("Atualizar Dados do Profissional")
        try:
            busca_edicao = supabase.table("usuarios").select("*")
            if st.session_state.nome_usuario != "admin":
                busca_edicao = busca_edicao.neq("usuario", "admin")
            dados_edicao = busca_edicao.execute().data
            
            if dados_edicao:
                lista_edicao = [d['usuario'] for d in dados_edicao]
                user_editar = st.selectbox("Selecione o usuário para alterar:", lista_edicao)
                
                if user_editar:
                    # Puxa os dados atuais do usuário selecionado para preencher os campos
                    dados_alvo = next(item for item in dados_edicao if item["usuario"] == user_editar)
                    
                    edit_senha = st.text_input("Nova Senha (Deixe em branco para manter a atual)", type="password")
                    
                    c_edit1, c_edit2 = st.columns(2)
                    with c_edit1: 
                        edit_perfil = st.selectbox("Alterar Perfil", ["Elaborador", "Administrador"], index=["Elaborador", "Administrador"].index(dados_alvo['perfil']))
                    with c_edit2: 
                        comp_atual = dados_alvo.get('componente', 'Língua Portuguesa')
                        idx_comp = componentes_rede.index(comp_atual) if comp_atual in componentes_rede else 0
                        edit_comp = st.selectbox("Alterar Componente", componentes_rede, index=idx_comp, disabled=(edit_perfil == "Administrador"))
                    
                    if st.button("🔄 Salvar Alterações", use_container_width=True):
                        pacote_atualizacao = {
                            "perfil": edit_perfil,
                            "componente": edit_comp if edit_perfil == "Elaborador" else "Todos"
                        }
                        if edit_senha:
                            pacote_atualizacao["senha"] = edit_senha
                            
                        supabase.table("usuarios").update(pacote_atualizacao).eq("usuario", user_editar).execute()
                        st.success("✅ Dados atualizados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar edição: {e}")
