import streamlit as st
import pandas as pd
from supabase import create_client
import json

st.set_page_config(page_title="Elaborador de Itens", page_icon="📝", layout="wide")

# --- 1. SEGURANÇA E CONEXÃO ---
if not st.session_state.get('usuario_logado'):
    st.switch_page("app.py")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

# --- MENU LATERAL ---
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.get('perfil', 'Usuário')}**")
    st.divider()
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.switch_page("app.py")

st.title("📝 Estúdio de Criação de Itens")
st.write("Elabore novas questões alinhadas às matrizes oficiais da rede.")

# --- 2. BUSCANDO MATRIZES DO SUPABASE ---
@st.cache_data(ttl=600) # Faz cache por 10 min para não pesar o banco
def carregar_matrizes():
    resposta = supabase.table("matrizes").select("id, ano, componente, codigo_habilidade, descricao").execute()
    return pd.DataFrame(resposta.data)

df_matriz = carregar_matrizes()

if df_matriz.empty:
    st.error("⛔ As matrizes de referência ainda não foram carregadas. Acesso bloqueado.")
    st.stop()

# --- 3. FILTROS DINÂMICOS ---
st.subheader("1. Parâmetros Curriculares")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    componentes = df_matriz['componente'].unique().tolist()
    componente_sel = st.selectbox("Componente Curricular", componentes)

with col_p2:
    anos = df_matriz[df_matriz['componente'] == componente_sel]['ano'].unique().tolist()
    ano_sel = st.selectbox("Ano de Ensino", anos)

with col_p3:
    habs_filtradas = df_matriz[(df_matriz['componente'] == componente_sel) & (df_matriz['ano'] == ano_sel)]
    lista_codigos = habs_filtradas['codigo_habilidade'].tolist()
    
    if lista_codigos:
        habilidade_sel = st.selectbox("Habilidade (Descritor)", lista_codigos)
        
        # Pega o ID e a Descrição da habilidade selecionada
        linha_hab = habs_filtradas[habs_filtradas['codigo_habilidade'] == habilidade_sel].iloc[0]
        id_habilidade_banco = linha_hab['id']
        st.caption(f"**Descrição:** {linha_hab['descricao']}")
    else:
        st.warning("Nenhuma habilidade cadastrada para este filtro.")
        st.stop()

st.divider()

# --- 4. EDITOR DA QUESTÃO ---
st.subheader("2. Estrutura do Item")

col_meta1, col_meta2 = st.columns(2)
with col_meta1:
    complexidade = st.select_slider("Complexidade Esperada", options=["Fácil", "Intermediária", "Complexa"])
with col_meta2:
    tags = st.text_input("Tags de Busca (Opcional, separe por vírgula)", placeholder="Ex: Geometria, Frações, Interpretação")

aba_editor, aba_ia = st.tabs(["✍️ Editor Manual", "🤖 Assistente de IA (Em breve)"])

with aba_editor:
    with st.form("form_nova_questao", clear_on_submit=True):
        st.info("💡 Suporta equações matemáticas. Para frações, use a sintaxe LaTeX entre cifrões, ex: $\\frac{1}{2}$")
        
        texto_base = st.text_area("Texto de Apoio / Contextualização (Opcional)", height=150)
        enunciado = st.text_area("Enunciado (A Pergunta)*", height=100)
        
        st.write("**Alternativas**")
        col_alt_a, col_alt_b = st.columns(2)
        with col_alt_a:
            alt_A = st.text_input("A)*")
            alt_C = st.text_input("C)*")
        with col_alt_b:
            alt_B = st.text_input("B)*")
            alt_D = st.text_input("D)*")
            
        gabarito = st.selectbox("Gabarito Correto*", ["A", "B", "C", "D"])
        status_salvamento = st.radio("Salvar como:", ["Concluída", "Rascunho"], horizontal=True)
        
        submit_questao = st.form_submit_button("💾 Salvar Item no Banco de Dados", type="primary")
        
        if submit_questao:
            if enunciado and alt_A and alt_B and alt_C and alt_D:
                with st.spinner("Salvando na nuvem..."):
                    # Prepara o JSON das alternativas
                    dict_alternativas = {"A": alt_A, "B": alt_B, "C": alt_C, "D": alt_D}
                    
                    # Monta o pacote de dados para o Supabase
                    nova_questao = {
                        "id_habilidade": id_habilidade_banco,
                        "autor": st.session_state.perfil,
                        "status": status_salvamento,
                        "complexidade": complexidade,
                        "texto_base": texto_base,
                        "enunciado": enunciado,
                        "alternativas": dict_alternativas, # O Supabase entende JSON automaticamente
                        "gabarito": gabarito,
                        "tags": tags
                    }
                    
                    try:
                        # Executa o INSERT no Supabase
                        resposta = supabase.table("questoes").insert(nova_questao).execute()
                        st.success("✅ Item salvo com sucesso no banco oficial!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
            else:
                st.error("Preencha o enunciado e todas as alternativas para salvar.")

with aba_ia:
    st.subheader("Gerador e Revisor Inteligente")
    st.write("A conexão com o Google Gemini será ativada aqui no próximo passo.")
