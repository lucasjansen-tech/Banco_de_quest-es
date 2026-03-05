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
    st.error("⛔ Matrizes não carregadas. Retorne e faça a importação.")
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

# --- CATÁLOGO DE SÍMBOLOS MATEMÁTICOS COM PRÉ-VISUALIZAÇÃO ---
with st.expander("🧮 Catálogo de Fórmulas e Símbolos (Clique para abrir)"):
    st.write("Veja o símbolo, copie o código no botão superior direito do quadro negro e cole no seu texto.")
    aba_construtor, aba_geo, aba_grego, aba_conj = st.tabs(["🔨 Construtor Básico", "📐 Geometria", "α Letras Gregas", "⋃ Conjuntos"])
    
    with aba_construtor:
        st.write("Crie frações, raízes e potências dinamicamente:")
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1: num = st.text_input("Numerador", value="1")
        with col_f2: den = st.text_input("Denominador", value="2")
        with col_f3: 
            st.markdown(f"**Visualização:** $\\frac{{{num}}}{{{den}}}$")
            st.code(f"$\\frac{{{num}}}{{{den}}}$", language="latex")
        
        st.divider()
        col_r1, col_r2, col_r3 = st.columns([1, 1, 2])
        with col_r1: indice = st.text_input("Índice da Raiz", value="3")
        with col_r2: valor = st.text_input("Valor interno", value="x")
        with col_r3: 
            raiz_calc = f"$\\sqrt[{indice}]{{{valor}}}$" if indice else f"$\\sqrt{{{valor}}}$"
            st.markdown(f"**Visualização:** {raiz_calc}")
            st.code(raiz_calc, language="latex")

    with aba_geo:
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.markdown("Grau: $90^\\circ$")
            st.code("$90^\\circ$", language="latex")
        with c2: 
            st.markdown("Ângulo: $\\angle A$")
            st.code("$\\angle A$", language="latex")
        with c3: 
            st.markdown("Triângulo: $\\triangle ABC$")
            st.code("$\\triangle ABC$", language="latex")
        with c4: 
            st.markdown("Perpendicular: $\\perp$")
            st.code("$\\perp$", language="latex")
        
        c5, c6, c7, c8 = st.columns(4)
        with c5: 
            st.markdown("Paralelo: $\\parallel$")
            st.code("$\\parallel$", language="latex")
        with c6: 
            st.markdown("Congruente: $\\cong$")
            st.code("$\\cong$", language="latex")
        with c7: 
            st.markdown("Vetor: $\\vec{v}$")
            st.code("$\\vec{v}$", language="latex")
        with c8: 
            st.markdown("Pi: $\\pi$")
            st.code("$\\pi$", language="latex")

    with aba_grego:
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.markdown("Alfa: $\\alpha$")
            st.code("$\\alpha$", language="latex")
        with c2: 
            st.markdown("Beta: $\\beta$")
            st.code("$\\beta$", language="latex")
        with c3: 
            st.markdown("Teta: $\\theta$")
            st.code("$\\theta$", language="latex")
        with c4: 
            st.markdown("Gama: $\\gamma$")
            st.code("$\\gamma$", language="latex")
            
        c5, c6, c7, c8 = st.columns(4)
        with c5: 
            st.markdown("Delta: $\\Delta$")
            st.code("$\\Delta$", language="latex")
        with c6: 
            st.markdown("Sigma: $\\Sigma$")
            st.code("$\\Sigma$", language="latex")
        with c7: 
            st.markdown("Ômega: $\\Omega$")
            st.code("$\\Omega$", language="latex")
        with c8: 
            st.markdown("Mi (Micro): $\\mu$")
            st.code("$\\mu$", language="latex")

    with aba_conj:
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.markdown("Pertence: $\\in$")
            st.code("$\\in$", language="latex")
        with c2: 
            st.markdown("Não pertence: $\\notin$")
            st.code("$\\notin$", language="latex")
        with c3: 
            st.markdown("União: $\\cup$")
            st.code("$\\cup$", language="latex")
        with c4: 
            st.markdown("Interseção: $\\cap$")
            st.code("$\\cap$", language="latex")
            
        c5, c6, c7, c8 = st.columns(4)
        with c5: 
            st.markdown("Contido: $\\subset$")
            st.code("$\\subset$", language="latex")
        with c6: 
            st.markdown("Não contido: $\\not\\subset$")
            st.code("$\\not\\subset$", language="latex")
        with c7: 
            st.markdown("Contém: $\\supset$")
            st.code("$\\supset$", language="latex")
        with c8: 
            st.markdown("Vazio: $\\emptyset$")
            st.code("$\\emptyset$", language="latex")

st.divider()

# --- EDITOR ROBUSTO COM PREVIEW E PREPARAÇÃO PARA IA ---
st.subheader("2. Estrutura do Item")
col_meta1, col_meta2 = st.columns(2)
with col_meta1: complexidade = st.select_slider("Complexidade", options=["Fácil", "Intermediária", "Complexa"])
with col_meta2: tags = st.text_input("Tags", placeholder="Ex: Fração, Geometria, Cotidiano")

col_editor, col_preview = st.columns([1.2, 1])

with col_editor:
    with st.container(border=True):
        st.markdown("### ✍️ Edição")
        texto_base = st.text_area("Texto Base (Opcional)", height=100)
        
        img_apoio = st.file_uploader("Imagem do Enunciado", type=['png', 'jpg', 'jpeg'], key="img_base")
        if img_apoio:
            st.button("✨ Melhorar imagem com IA (Próxima Etapa)", disabled=True, use_container_width=True)
            
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

if st.button("💾 Salvar Item no Banco de Dados", use_container_width=True):
    if enunciado and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Salvando na nuvem..."):
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": True if img_A else False},
                "B": {"texto": alt_B, "tem_imagem": True if img_B else False},
                "C": {"texto": alt_C, "tem_imagem": True if img_C else False},
                "D": {"texto": alt_D, "tem_imagem": True if img_D else False}
            }
            
# Pacote de dados alinhado estritamente com o SQL criado no Supabase
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "autor": st.session_state.nome_usuario, # <--- AQUI ESTÁ A ALTERAÇÃO!
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_base": texto_base,
                "enunciado": enunciado,
                "imagem_url": None, 
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
