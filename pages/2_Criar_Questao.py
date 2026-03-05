import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Elaborador de Itens", page_icon="📝", layout="wide")

# --- SEGURANÇA E CONEXÃO ---
if not st.session_state.get('usuario_logado'):
    st.switch_page("app.py")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

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

st.title("📝 Estúdio de Criação Avançado")

# --- BUSCANDO MATRIZES ---
@st.cache_data(ttl=600)
def carregar_matrizes():
    resposta = supabase.table("matrizes").select("id, ano, componente, codigo_habilidade, descricao").execute()
    return pd.DataFrame(resposta.data)

df_matriz = carregar_matrizes()
if df_matriz.empty:
    st.error("⛔ Matrizes não carregadas.")
    st.stop()

# --- FILTROS DINÂMICOS ---
st.subheader("1. Parâmetros Curriculares")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    componente_sel = st.selectbox("Componente", df_matriz['componente'].unique().tolist())
with col_p2:
    ano_sel = st.selectbox("Ano de Ensino", df_matriz[df_matriz['componente'] == componente_sel]['ano'].unique().tolist())
with col_p3:
    habs_filtradas = df_matriz[(df_matriz['componente'] == componente_sel) & (df_matriz['ano'] == ano_sel)]
    lista_codigos = habs_filtradas['codigo_habilidade'].tolist()
    if lista_codigos:
        habilidade_sel = st.selectbox("Habilidade", lista_codigos)
        linha_hab = habs_filtradas[habs_filtradas['codigo_habilidade'] == habilidade_sel].iloc[0]
        id_habilidade_banco = linha_hab['id']
        st.caption(f"**Descrição:** {linha_hab['descricao']}")
    else:
        st.warning("Nenhuma habilidade para este filtro.")
        st.stop()

st.divider()

# --- CONSTRUTOR VISUAL DE FÓRMULAS (O "Pulo do Gato" para os professores) ---
with st.expander("🧮 Construtor Visual de Fórmulas (Clique aqui se precisar de Matemática)"):
    st.write("Não sabe usar códigos? Preencha os campos abaixo, copie o bloquinho gerado e cole no seu texto!")
    aba_frac, aba_raiz, aba_pot, aba_simb = st.tabs(["➗ Frações", "√ Raízes", "x² Potências", "Ω Símbolos Úteis"])
    
    with aba_frac:
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1: num = st.text_input("Numerador (Cima)", value="1")
        with col_f2: den = st.text_input("Denominador (Baixo)", value="2")
        with col_f3:
            st.markdown("**Resultado Visual:**")
            st.markdown(f"$\\frac{{{num}}}{{{den}}}$")
            st.code(f"$\\frac{{{num}}}{{{den}}}$", language="latex")
            
    with aba_raiz:
        col_r1, col_r2, col_r3 = st.columns([1, 1, 2])
        with col_r1: indice = st.text_input("Índice (Ex: 3 para cúbica, vazio para quadrada)", value="")
        with col_r2: valor = st.text_input("Valor interno", value="x")
        with col_r3:
            st.markdown("**Resultado Visual:**")
            raiz_code = f"$\\sqrt[{indice}]{{{valor}}}$" if indice else f"$\\sqrt{{{valor}}}$"
            st.markdown(raiz_code)
            st.code(raiz_code, language="latex")
            
    with aba_pot:
        col_p1, col_p2, col_p3 = st.columns([1, 1, 2])
        with col_p1: base = st.text_input("Base", value="x")
        with col_p2: expoente = st.text_input("Expoente", value="2")
        with col_p3:
            st.markdown("**Resultado Visual:**")
            st.markdown(f"${base}^{{{expoente}}}$")
            st.code(f"${base}^{{{expoente}}}$", language="latex")

    with aba_simb:
        st.write("Apenas clique no ícone de copiar no canto do quadro negro e cole no texto:")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1: st.code("$\\pi$", language="latex") # Pi
        with col_s2: st.code("$\\in$", language="latex") # Pertence
        with col_s3: st.code("$\\neq$", language="latex") # Diferente
        with col_s4: st.code("$\\ge$", language="latex") # Maior ou igual

st.divider()

# --- EDITOR ROBUSTO COM PREVIEW ---
st.subheader("2. Estrutura do Item")
col_meta1, col_meta2 = st.columns(2)
with col_meta1: complexidade = st.select_slider("Complexidade", options=["Fácil", "Intermediária", "Complexa"])
with col_meta2: tags = st.text_input("Tags", placeholder="Ex: Fração, Geometria")

col_editor, col_preview = st.columns([1.2, 1])

with col_editor:
    with st.container(border=True):
        st.markdown("### ✍️ Edição")
        texto_base = st.text_area("Texto Base (Opcional)", height=100)
        img_apoio = st.file_uploader("Imagem do Enunciado", type=['png', 'jpg', 'jpeg'], key="img_base")
        enunciado = st.text_area("Enunciado*", height=100)
        
        st.markdown("#### Alternativas")
        alt_A = st.text_area("A)*", height=68, key="txt_a")
        img_A = st.file_uploader("Imagem A", type=['png', 'jpg'], key="img_a")
        
        alt_B = st.text_area("B)*", height=68, key="txt_b")
        img_B = st.file_uploader("Imagem B", type=['png', 'jpg'], key="img_b")
        
        alt_C = st.text_area("C)*", height=68, key="txt_c")
        img_C = st.file_uploader("Imagem C", type=['png', 'jpg'], key="img_c")
        
        alt_D = st.text_area("D)*", height=68, key="txt_d")
        img_D = st.file_uploader("Imagem D", type=['png', 'jpg'], key="img_d")
        
        gabarito = st.selectbox("Gabarito*", ["A", "B", "C", "D"])

with col_preview:
    with st.container(border=True):
        st.markdown("### 👀 Visualização Final")
        st.divider()
        if texto_base: st.markdown(texto_base)
        if img_apoio: st.image(img_apoio, use_container_width=True)
        if enunciado: st.markdown(f"**Questão:** {enunciado}")
        st.markdown("---")
        if alt_A or img_A:
            st.markdown(f"**A)** {alt_A}")
            if img_A: st.image(img_A, width=150)
        if alt_B or img_B:
            st.markdown(f"**B)** {alt_B}")
            if img_B: st.image(img_B, width=150)
        if alt_C or img_C:
            st.markdown(f"**C)** {alt_C}")
            if img_C: st.image(img_C, width=150)
        if alt_D or img_D:
            st.markdown(f"**D)** {alt_D}")
            if img_D: st.image(img_D, width=150)

st.divider()

if st.button("💾 Salvar Item no Banco de Dados", type="primary", use_container_width=True):
    if enunciado and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Salvando na nuvem..."):
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": True if img_A else False},
                "B": {"texto": alt_B, "tem_imagem": True if img_B else False},
                "C": {"texto": alt_C, "tem_imagem": True if img_C else False},
                "D": {"texto": alt_D, "tem_imagem": True if img_D else False}
            }
            
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "autor": st.session_state.perfil,
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_base": texto_base,
                "enunciado": enunciado,
                "tem_imagem_apoio": True if img_apoio else False,
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "tags": tags
            }
            
            try:
                supabase.table("questoes").insert(nova_questao).execute()
                st.success("✅ Questão com formatação avançada salva com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")
    else:
        st.error("Preencha o enunciado e o texto de todas as alternativas para salvar.")
