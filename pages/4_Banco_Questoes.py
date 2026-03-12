import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Banco de Questões", page_icon="🗄️", layout="wide")

# --- SEGURANÇA ---
if not st.session_state.get('usuario_logado'):
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
    if st.session_state.get('perfil') == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
        st.page_link("pages/3_Gestao_Usuarios.py", label="Gestão de Usuários", icon="👥")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.page_link("pages/4_Banco_Questoes.py", label="Banco de Questões", icon="🗄️")
    st.divider()
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.switch_page("app.py")

st.title("🗄️ Banco de Questões da Rede")
st.write("Explore, edite suas criações ou use questões de colegas como base.")

# --- FILTROS DE BUSCA ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_autor = st.selectbox("Filtrar por Autor", ["Todos", "Minhas Questões", "Outros Professores"])
    with col2:
        filtro_complex = st.multiselect("Complexidade", ["Fácil", "Intermediária", "Complexa"], default=["Fácil", "Intermediária", "Complexa"])
    with col3:
        busca_termo = st.text_input("Busca por termo (Enunciado/Tags)")

# --- BUSCA NO SUPABASE ---
query = supabase.table("questoes").select("*, matrizes(codigo_habilidade, ano, componente)").eq("ativo", True)

if filtro_autor == "Minhas Questões":
    query = query.eq("autor", st.session_state.nome_usuario)
elif filtro_autor == "Outros Professores":
    query = query.neq("autor", st.session_state.nome_usuario)

res = query.execute()
df_questoes = pd.DataFrame(res.data)

if df_questoes.empty:
    st.info("Nenhuma questão encontrada com esses filtros.")
else:
    # Lógica de renderização em Cards
    for _, item in df_questoes.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**Hab:** {item['matrizes']['codigo_habilidade']} | **Ano:** {item['matrizes']['ano']} | **Autor:** {item['autor'].title()}")
                st.markdown(f"**Enunciado:** {item['enunciado'][:150]}...")
                st.caption(f"Complexidade: {item['complexidade']} | Tags: {item['tags']}")
            
            with c2:
                # LÓGICA DE PERMISSÃO VISUAL
                if item['autor'] == st.session_state.nome_usuario:
                    st.write("🛠️ **Sua Questão**")
                    if st.button("✏️ Editar", key=f"edit_{item['id']}", use_container_width=True):
                        st.session_state.edit_mode = item
                        st.switch_page("pages/2_Criar_Questao.py")
                    
                    if st.button("🗑️ Excluir", key=f"del_{item['id']}", use_container_width=True):
                        supabase.table("questoes").update({"ativo": False}).eq("id", item['id']).execute()
                        st.rerun()
                else:
                    st.write("👥 **Colaboração**")
                    if st.button("➕ Clonar Base", key=f"clone_{item['id']}", use_container_width=True):
                        st.session_state.clone_mode = item
                        st.switch_page("pages/2_Criar_Questao.py")
