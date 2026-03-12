import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import json

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
modelo_ia = None
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if '1.5' in m.name or modelo_ia is None:
                modelo_ia = genai.GenerativeModel(m.name)
except Exception as e:
    st.error(f"Erro de IA: {e}")

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

st.title("📝 Estúdio de Criação em Blocos")

# --- 3. LÓGICA DE EDIÇÃO/CLONAGEM ---
origem = None
modo_atual = "novo"

if 'edit_mode' in st.session_state:
    origem = st.session_state.edit_mode
    modo_atual = "edicao"
    st.info("🔄 **Modo de Edição:** Alterando a questão original.")
    if st.button("❌ Cancelar Edição"):
        del st.session_state.edit_mode
        st.rerun()
elif 'clone_mode' in st.session_state:
    origem = st.session_state.clone_mode
    modo_atual = "clone"
    st.warning(f"🐑 **Modo Clonagem:** Usando item de '{origem['autor']}' como base.")
    if st.button("❌ Cancelar Clonagem"):
        del st.session_state.clone_mode
        st.rerun()

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
    st.error("⛔ Matrizes não carregadas.")
    st.stop()

# --- 5. PARÂMETROS E CATÁLOGO ---
with st.expander("⚙️ Parâmetros Curriculares e Ferramentas", expanded=False):
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1: componente_sel = st.selectbox("Componente", df_matriz['componente'].unique().tolist())
    with col_p2: ano_sel = st.selectbox("Ano de Ensino", df_matriz[df_matriz['componente'] == componente_sel]['ano'].unique().tolist())
    with col_p3:
        habs_filtradas = df_matriz[(df_matriz['componente'] == componente_sel) & (df_matriz['ano'] == ano_sel)]
        lista_codigos = habs_filtradas['codigo_habilidade'].tolist()
        habilidade_sel = st.selectbox("Habilidade", lista_codigos)
        linha_hab = habs_filtradas[habs_filtradas['codigo_habilidade'] == habilidade_sel].iloc[0]
        id_habilidade_banco = linha_hab['id']
    st.caption(f"**Matriz:** {linha_hab['descricao']}")

    st.divider()
    st.markdown("🧮 **Catálogo LaTeX:** Copie e cole: `\\frac{1}{2}`, `\\sqrt{x}`, `\\pi`, `\\alpha`")

opcoes_niveis = ["Fácil", "Intermediária", "Complexa"]
if modo_atual == "clone" and origem:
    opcoes_permitidas = opcoes_niveis[opcoes_niveis.index(origem.get('complexidade', 'Fácil')):]
else:
    opcoes_permitidas = opcoes_niveis

# --- 6. O EDITOR EM BLOCOS ---
col_editor, col_preview = st.columns([1.2, 1])

with col_editor:
    col_m1, col_m2 = st.columns(2)
    with col_m1: complexidade = st.select_slider("Nível", options=opcoes_permitidas)
    with col_m2: tags = st.text_input("Tags", value=val_tags)

    # ==========================================
    # BLOCO 1: CONTEXTO E COMANDO
    # ==========================================
    with st.container(border=True):
        st.markdown("### 1️⃣ Bloco de Contexto")
        texto_base_input = st.text_area("Texto Base (Leitura de apoio)", value=val_texto_base, height=100)
        img_apoio = st.file_uploader("Imagem do Enunciado", type=['png', 'jpg'], key="img_base")
        enunciado_input = st.text_area("Enunciado (A Pergunta)*", value=val_enunciado, height=100)
        
        if st.button("✨ Revisar Contexto e Imagem", use_container_width=True):
            with st.spinner("Analisando alinhamento do texto e necessidade visual..."):
                tem_imagem = "Sim" if img_apoio else "Não"
                prompt_ctx = f"""
                Atue como um coordenador pedagógico.
                Texto Base: {texto_base_input}
                Enunciado: {enunciado_input}
                A questão possui uma imagem anexada? {tem_imagem}.
                
                1. Melhore a clareza, gramática e adequação do texto base e do enunciado.
                2. Gere um 'aviso_imagem' curto. Se houver imagem, alerte o que ela DEVE ter para o enunciado fazer sentido (ex: legendas visíveis, escala correta). Se não houver, avalie se uma imagem seria necessária e avise.
                
                Retorne ESTRITAMENTE em JSON:
                {{"texto_base": "novo texto", "enunciado": "novo enunciado", "aviso_imagem": "seu alerta aqui"}}
                """
                try:
                    res = modelo_ia.generate_content(prompt_ctx)
                    dados_ctx = json.loads(res.text.replace("```json", "").replace("```", "").strip())
                    
                    # Atualiza os estados na tela (Streamlit recarrega o form com esses valores)
                    st.session_state['ctx_txt'] = dados_ctx.get('texto_base', texto_base_input)
                    st.session_state['ctx_enu'] = dados_ctx.get('enunciado', enunciado_input)
                    
                    st.success("Revisão concluída! Aplique as mudanças abaixo se concordar.")
                    st.info(f"🖼️ **Parecer sobre a Imagem:** {dados_ctx.get('aviso_imagem', 'Ok')}")
                    
                    # Mostra caixas para o usuário copiar/colar se quiser
                    st.text_area("Sugestão Texto Base", value=dados_ctx.get('texto_base', ''), height=100)
                    st.text_area("Sugestão Enunciado", value=dados_ctx.get('enunciado', ''), height=100)
                    
                except Exception as e:
                    st.error("Erro ao formatar a revisão da IA.")

    # ==========================================
    # BLOCO 2: ALTERNATIVAS E DISTRATORES
    # ==========================================
    with st.container(border=True):
        st.markdown("### 2️⃣ Bloco de Alternativas")
        
        lista_gabarito = ["A", "B", "C", "D"]
        idx_gab = lista_gabarito.index(val_gabarito) if val_gabarito in lista_gabarito else 0
        gabarito = st.selectbox("Qual é a alternativa correta?*", lista_gabarito, index=idx_gab)
        
        alt_A = st.text_area("A)", value=val_alt_a, height=68)
        alt_B = st.text_area("B)", value=val_alt_b, height=68)
        alt_C = st.text_area("C)", value=val_alt_c, height=68)
        alt_D = st.text_area("D)", value=val_alt_d, height=68)
        
        if st.button("✨ Validar Distratores Pedagógicos", use_container_width=True):
            with st.spinner("Avaliando se as alternativas induzem o aluno ao erro corretamente..."):
                prompt_dist = f"""
                Atue como especialista em Teoria de Resposta ao Item (TRI).
                Enunciado: {enunciado_input}
                Gabarito: {gabarito}
                A: {alt_A} | B: {alt_B} | C: {alt_C} | D: {alt_D}
                
                1. Verifique se há duas opções muito parecidas ou respostas corretas duplicadas.
                2. Melhore a redação das opções erradas (distratores) baseando-se em erros comuns.
                
                Retorne ESTRITAMENTE em JSON:
                {{"A": "...", "B": "...", "C": "...", "D": "...", "parecer": "Seu feedback crítico aqui"}}
                """
                try:
                    res_dist = modelo_ia.generate_content(prompt_dist)
                    dados_dist = json.loads(res_dist.text.replace("```json", "").replace("```", "").strip())
                    
                    st.success("Validação concluída!")
                    st.warning(f"📊 **Parecer TRI:** {dados_dist.get('parecer', 'Ok')}")
                    
                    c1, c2 = st.columns(2)
                    with c1: st.text_area("Sugestão A", value=dados_dist.get('A', ''), height=68)
                    with c1: st.text_area("Sugestão C", value=dados_dist.get('C', ''), height=68)
                    with c2: st.text_area("Sugestão B", value=dados_dist.get('B', ''), height=68)
                    with c2: st.text_area("Sugestão D", value=dados_dist.get('D', ''), height=68)
                except Exception as e:
                    st.error("Erro ao validar alternativas.")

with col_preview:
    with st.container(border=True):
        st.markdown("### 👀 Visualização do Caderno")
        st.divider()
        if texto_base_input: st.markdown(f"*{texto_base_input}*")
        if img_apoio: st.image(img_apoio, use_container_width=True)
        if enunciado_input: st.markdown(f"**Questão:** {enunciado_input}")
        st.markdown("---")
        if alt_A: st.markdown(f"**A)** {alt_A}")
        if alt_B: st.markdown(f"**B)** {alt_B}")
        if alt_C: st.markdown(f"**C)** {alt_C}")
        if alt_D: st.markdown(f"**D)** {alt_D}")

st.divider()

# --- 7. GRAVAÇÃO NO BANCO ---
texto_botao = "🔄 Atualizar Questão" if modo_atual == "edicao" else "💾 Salvar Nova Questão"

if st.button(texto_botao, use_container_width=True, type="primary"):
    if enunciado_input and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Gravando no banco oficial..."):
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": False},
                "B": {"texto": alt_B, "tem_imagem": False},
                "C": {"texto": alt_C, "tem_imagem": False},
                "D": {"texto": alt_D, "tem_imagem": False}
            }
            
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "autor": st.session_state.nome_usuario,
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_base": texto_base_input,
                "enunciado": enunciado_input,
                "imagem_url": None, 
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "tags": tags
            }
            
            try:
                if modo_atual == "edicao" and origem:
                    supabase.table("questoes").update(nova_questao).eq("id", origem['id']).execute()
                    st.success("✅ Questão atualizada!")
                    del st.session_state.edit_mode
                else:
                    supabase.table("questoes").insert(nova_questao).execute()
                    st.success("✅ Nova questão salva!")
                    if 'clone_mode' in st.session_state:
                        del st.session_state.clone_mode
            except Exception as e:
                st.error(f"Erro no banco: {e}")
    else:
        st.error("Preencha todos os campos obrigatórios.")
