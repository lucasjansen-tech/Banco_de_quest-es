import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai

st.set_page_config(page_title="Elaborador de Itens", page_icon="📝", layout="wide")

# --- 1. SEGURANÇA E CONEXÃO ---
if not st.session_state.get('usuario_logado'):
    st.switch_page("app.py")

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

# --- CONFIGURAÇÃO DA IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
modelo_ia = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. MENU LATERAL ---
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.get('nome_usuario', 'Usuário').title()}**")
    st.divider()
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    if st.session_state.get('perfil') == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
        st.page_link("pages/3_Gestao_Usuarios.py", label="Gestão de Usuários", icon="👥")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.page_link("pages/4_Banco_Questoes.py", label="Banco de Questões", icon="🗄️")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

st.title("📝 Estúdio de Criação Avançado")

# --- 3. LÓGICA DE EDIÇÃO E CLONAGEM ---
origem = None
modo_atual = "novo"

if 'edit_mode' in st.session_state:
    origem = st.session_state.edit_mode
    modo_atual = "edicao"
    st.info(f"🔄 **Modo de Edição:** Alterando a questão original.")
    if st.button("❌ Cancelar Edição"):
        del st.session_state.edit_mode
        st.rerun()
elif 'clone_mode' in st.session_state:
    origem = st.session_state.clone_mode
    modo_atual = "clone"
    st.warning(f"🐑 **Modo Clonagem:** Você está usando um item de '{origem['autor']}' como base.")
    if st.button("❌ Cancelar Clonagem"):
        del st.session_state.clone_mode
        st.rerun()

# Preenchimento das variáveis se vier de uma edição/clonagem
val_texto_base = origem.get('texto_base', "") if origem else ""
val_enunciado = origem.get('enunciado', "") if origem else ""
val_tags = origem.get('tags', "") if origem else ""
val_gabarito = origem.get('gabarito', 'A') if origem else 'A'

if origem and 'alternativas' in origem and origem['alternativas']:
    val_alt_a = origem['alternativas'].get('A', {}).get('texto', '')
    val_alt_b = origem['alternativas'].get('B', {}).get('texto', '')
    val_alt_c = origem['alternativas'].get('C', {}).get('texto', '')
    val_alt_d = origem['alternativas'].get('D', {}).get('texto', '')
else:
    val_alt_a, val_alt_b, val_alt_c, val_alt_d = "", "", "", ""

# --- 4. BUSCANDO MATRIZES ---
@st.cache_data(ttl=600)
def carregar_matrizes():
    resposta = supabase.table("matrizes").select("id, ano, componente, codigo_habilidade, descricao").execute()
    return pd.DataFrame(resposta.data)

df_matriz = carregar_matrizes()
if df_matriz.empty:
    st.error("⛔ Matrizes não carregadas. Retorne e faça a importação.")
    st.stop()

# --- 5. FILTROS DINÂMICOS ---
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

# --- 6. CATÁLOGO DE SÍMBOLOS MATEMÁTICOS ---
with st.expander("🧮 Catálogo de Fórmulas e Símbolos (Clique para abrir)"):
    aba_construtor, aba_geo, aba_grego, aba_conj = st.tabs(["🔨 Construtor Básico", "📐 Geometria", "α Letras Gregas", "⋃ Conjuntos"])
    
    with aba_construtor:
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1: num = st.text_input("Numerador", value="1")
        with col_f2: den = st.text_input("Denominador", value="2")
        with col_f3: 
            st.markdown(f"**Visualização:** $\\frac{{{num}}}{{{den}}}$")
            st.code(f"$\\frac{{{num}}}{{{den}}}$", language="latex")
        
        col_r1, col_r2, col_r3 = st.columns([1, 1, 2])
        with col_r1: indice = st.text_input("Índice da Raiz", value="3")
        with col_r2: valor = st.text_input("Valor interno", value="x")
        with col_r3: 
            raiz_calc = f"$\\sqrt[{indice}]{{{valor}}}$" if indice else f"$\\sqrt{{{valor}}}$"
            st.markdown(f"**Visualização:** {raiz_calc}")
            st.code(raiz_calc, language="latex")

    with aba_geo:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown("Grau: $90^\\circ$"); st.code("$90^\\circ$", language="latex")
        with c2: st.markdown("Ângulo: $\\angle A$"); st.code("$\\angle A$", language="latex")
        with c3: st.markdown("Triângulo: $\\triangle ABC$"); st.code("$\\triangle ABC$", language="latex")
        with c4: st.markdown("Pi: $\\pi$"); st.code("$\\pi$", language="latex")

    with aba_grego:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown("Alfa: $\\alpha$"); st.code("$\\alpha$", language="latex")
        with c2: st.markdown("Beta: $\\beta$"); st.code("$\\beta$", language="latex")
        with c3: st.markdown("Teta: $\\theta$"); st.code("$\\theta$", language="latex")
        with c4: st.markdown("Delta: $\\Delta$"); st.code("$\\Delta$", language="latex")

    with aba_conj:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown("Pertence: $\\in$"); st.code("$\\in$", language="latex")
        with c2: st.markdown("Não pertence: $\\notin$"); st.code("$\\notin$", language="latex")
        with c3: st.markdown("União: $\\cup$"); st.code("$\\cup$", language="latex")
        with c4: st.markdown("Interseção: $\\cap$"); st.code("$\\cap$", language="latex")

st.divider()

# --- 7. EDITOR ROBUSTO COM IA ---
st.subheader("2. Estrutura do Item")
col_meta1, col_meta2 = st.columns(2)

# Regra de complexidade para clonagem (não pode baixar o nível)
opcoes_niveis = ["Fácil", "Intermediária", "Complexa"]
if modo_atual == "clone" and origem:
    idx_min = opcoes_niveis.index(origem.get('complexidade', 'Fácil'))
    opcoes_permitidas = opcoes_niveis[idx_min:]
else:
    opcoes_permitidas = opcoes_niveis

with col_meta1: 
    complexidade = st.select_slider("Complexidade", options=opcoes_permitidas)
with col_meta2: 
    tags = st.text_input("Tags", value=val_tags, placeholder="Ex: Fração, Geometria")

col_editor, col_preview = st.columns([1.2, 1])

# Funções da IA
def melhorar_enunciado(texto_atual):
    if not texto_atual: return "Erro: Escreva um rascunho."
    prompt = f"Melhore a clareza deste enunciado para uma prova escolar. Retorne APENAS o texto melhorado:\n\n{texto_atual}"
    return modelo_ia.generate_content(prompt).text

def gerar_distratores(enunciado, alt_correta):
    if not enunciado or not alt_correta: return "Erro: Preencha Enunciado e Letra A."
    prompt = f"Questão: '{enunciado}'. Correta: '{alt_correta}'. Crie 3 alternativas INCORRETAS baseadas em erros comuns. Retorne as 3 separadas por um traço (-), sem as letras A, B, C."
    return modelo_ia.generate_content(prompt).text

with col_editor:
    with st.container(border=True):
        st.markdown("### ✍️ Edição")
        texto_base = st.text_area("Texto Base (Opcional)", value=val_texto_base, height=80)
        
        st.markdown("**Enunciado da Questão***")
        enunciado_input = st.text_area("Digite o enunciado", value=val_enunciado, height=100, key="input_enunciado")
        
        if st.button("✨ Melhorar Enunciado com IA"):
            with st.spinner("Analisando..."):
                st.info(f"**Sugestão IA:**\n{melhorar_enunciado(enunciado_input)}")
        
        st.markdown("---")
        alt_A = st.text_area("A) *Resposta Correta*", value=val_alt_a, height=68, key="txt_a")
        
        if st.button("✨ Gerar Alternativas Erradas (IA)"):
            with st.spinner("Criando distratores..."):
                st.warning(f"**Sugestão IA:**\n{gerar_distratores(enunciado_input, alt_A)}")
        
        alt_B = st.text_area("B)*", value=val_alt_b, height=68, key="txt_b")
        alt_C = st.text_area("C)*", value=val_alt_c, height=68, key="txt_c")
        alt_D = st.text_area("D)*", value=val_alt_d, height=68, key="txt_d")
        
        lista_gabarito = ["A", "B", "C", "D"]
        idx_gab = lista_gabarito.index(val_gabarito) if val_gabarito in lista_gabarito else 0
        gabarito = st.selectbox("Gabarito*", lista_gabarito, index=idx_gab)

with col_preview:
    with st.container(border=True):
        st.markdown("### 👀 Visualização Final")
        st.divider()
        if texto_base: st.markdown(texto_base)
        if enunciado_input: st.markdown(f"**Questão:** {enunciado_input}")
        st.markdown("---")
        if alt_A: st.markdown(f"**A)** {alt_A}")
        if alt_B: st.markdown(f"**B)** {alt_B}")
        if alt_C: st.markdown(f"**C)** {alt_C}")
        if alt_D: st.markdown(f"**D)** {alt_D}")

st.divider()

# --- 8. BOTÃO INTELIGENTE DE SALVAMENTO ---
texto_botao = "🔄 Atualizar Questão" if modo_atual == "edicao" else "💾 Salvar Nova Questão"

if st.button(texto_botao, use_container_width=True):
    if enunciado_input and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Gravando no banco de dados..."):
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": False},
                "B": {"texto": alt_B, "tem_imagem": False},
                "C": {"texto": alt_C, "tem_imagem": False},
                "D": {"texto": alt_D, "tem_imagem": False}
            }
            
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "autor": st.session_state.nome_usuario, # Fica no nome de quem está salvando
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_base": texto_base,
                "enunciado": enunciado_input,
                "imagem_url": None, 
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "tags": tags
            }
            
            try:
                if modo_atual == "edicao" and origem:
                    # ATUALIZA o registro existente
                    supabase.table("questoes").update(nova_questao).eq("id", origem['id']).execute()
                    st.success("✅ Questão atualizada com sucesso!")
                    del st.session_state.edit_mode
                else:
                    # CRIA um novo registro (seja do zero ou de um clone)
                    supabase.table("questoes").insert(nova_questao).execute()
                    st.success("✅ Nova questão salva com sucesso!")
                    if 'clone_mode' in st.session_state:
                        del st.session_state.clone_mode
                
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    else:
        st.error("Preencha o enunciado e o texto de todas as alternativas para salvar.")
