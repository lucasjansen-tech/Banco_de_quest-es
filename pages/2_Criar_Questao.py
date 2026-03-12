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

st.title("📝 Estúdio de Criação Avançado")

# --- 3. LÓGICA DE EDIÇÃO/CLONAGEM ---
origem = None
modo_atual = "novo"

if 'edit_mode' in st.session_state:
    origem = st.session_state.edit_mode
    modo_atual = "edicao"
    st.info(f"🔄 **Modo de Edição:** Questão ID {origem.get('id', '')}")
    if st.button("❌ Cancelar Edição"):
        del st.session_state.edit_mode
        st.rerun()
elif 'clone_mode' in st.session_state:
    origem = st.session_state.clone_mode
    modo_atual = "clone"
    st.warning(f"🐑 **Modo Clonagem:** Base autor: {origem.get('autor', '')}")
    if st.button("❌ Cancelar Clonagem"):
        del st.session_state.clone_mode
        st.rerun()

val_enunciado = origem.get('enunciado', "") if origem else ""
val_resolucao = origem.get('resolucao', "") if origem else ""
val_tags = origem.get('tags', "") if origem else ""
val_gabarito = origem.get('gabarito', 'A') if origem else 'A'
val_id_texto_base = origem.get('id_texto_base', None) if origem else None

if origem and 'alternativas' in origem and origem['alternativas']:
    val_alt_a = origem['alternativas'].get('A', {}).get('texto', '')
    val_alt_b = origem['alternativas'].get('B', {}).get('texto', '')
    val_alt_c = origem['alternativas'].get('C', {}).get('texto', '')
    val_alt_d = origem['alternativas'].get('D', {}).get('texto', '')
else:
    val_alt_a, val_alt_b, val_alt_c, val_alt_d = "", "", "", ""

# --- 4. BUSCANDO DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_iniciais():
    matrizes = supabase.table("matrizes").select("id, ano, componente, codigo_habilidade, descricao").execute().data
    textos = supabase.table("textos_base").select("id, titulo, conteudo").execute().data
    return pd.DataFrame(matrizes), pd.DataFrame(textos)

df_matriz, df_textos = carregar_dados_iniciais()
if df_matriz.empty:
    st.error("⛔ Não há matrizes cadastradas no sistema. Acesse a Gestão de Matrizes.")
    st.stop()

# --- 5. PARÂMETROS E CATÁLOGO MATEMÁTICO ---
with st.expander("⚙️ Parâmetros Curriculares e Construtor de Fórmulas", expanded=True):
    col_p1, col_p2, col_p3 = st.columns(3)
    
    # BLINDAGEM ROBUSTA DE COMPONENTE
    todos_componentes = df_matriz['componente'].unique().tolist()
    if st.session_state.get('perfil') == "Elaborador":
        comp_prof = st.session_state.get('componente', '')
        match_comp = next((c for c in todos_componentes if str(c).strip().upper() == str(comp_prof).strip().upper()), None)
        
        if match_comp:
            lista_componentes = [match_comp]
        else:
            st.error(f"Sua disciplina é '{comp_prof}', mas não há matrizes para ela no banco. Fale com a Coordenação.")
            st.stop()
    else:
        lista_componentes = todos_componentes

    with col_p1: componente_sel = st.selectbox("Componente", lista_componentes)
    
    anos_disponiveis = df_matriz[df_matriz['componente'] == componente_sel]['ano'].unique().tolist()
    if not anos_disponiveis:
        st.warning(f"Nenhum ano escolar encontrado para {componente_sel}.")
        st.stop()
        
    with col_p2: ano_sel = st.selectbox("Ano de Ensino", anos_disponiveis)
    
    habs_filtradas = df_matriz[(df_matriz['componente'] == componente_sel) & (df_matriz['ano'] == ano_sel)]
    if habs_filtradas.empty:
        st.warning("Nenhuma habilidade cadastrada para este filtro.")
        st.stop()
        
    with col_p3:
        lista_codigos = habs_filtradas['codigo_habilidade'].tolist()
        habilidade_sel = st.selectbox("Habilidade", lista_codigos)
        linha_hab = habs_filtradas[habs_filtradas['codigo_habilidade'] == habilidade_sel].iloc[0]
        id_habilidade_banco = linha_hab['id']
        
    st.caption(f"**Matriz:** {linha_hab['descricao']}")

    st.divider()
    
    # --- NOVO CONSTRUTOR MATEMÁTICO VISUAL ---
    st.markdown("### 🧮 Construtor Matemático")
    st.info("💡 **Dica de Uso:** Ajuste os valores, veja a **Pré-visualização**, copie o código no quadro preto e cole no seu texto. Na caixa de digitação ele ficará como código, mas na Visualização Final (à direita) ele se transformará na fórmula!")
    
    t_frac, t_pot, t_raiz, t_trig, t_simb = st.tabs(["➗ Frações", "x² Potências", "√ Raízes", "📐 Geometria/Trig", "Ω Símbolos"])
    
    with t_frac:
        c1, c2 = st.columns(2)
        with c1: 
            num = st.text_input("Numerador (Parte de cima)", "1", key="num_f")
            den = st.text_input("Denominador (Parte de baixo)", "2", key="den_f")
        with c2: 
            st.write("**Pré-visualização Real:**")
            codigo_latex = f"\\frac{{{num}}}{{{den}}}"
            st.latex(codigo_latex)
            st.code(f"${codigo_latex}$", language="latex")
    
    with t_pot:
        c1, c2 = st.columns(2)
        with c1: 
            base = st.text_input("Base (Número principal)", "x", key="base_p")
            exp = st.text_input("Expoente (Número elevado)", "2", key="exp_p")
        with c2: 
            st.write("**Pré-visualização Real:**")
            codigo_latex = f"{base}^{{{exp}}}"
            st.latex(codigo_latex)
            st.code(f"${codigo_latex}$", language="latex")
            
    with t_raiz:
        c1, c2 = st.columns(2)
        with c1: 
            ind = st.text_input("Índice (Ex: 3 para cúbica. Deixe vazio para quadrada)", "", key="ind_r")
            val = st.text_input("Valor Interno", "x", key="val_r")
        with c2: 
            st.write("**Pré-visualização Real:**")
            codigo_latex = f"\\sqrt[{ind}]{{{val}}}" if ind else f"\\sqrt{{{val}}}"
            st.latex(codigo_latex)
            st.code(f"${codigo_latex}$", language="latex")
            
    with t_trig:
        st.write("**Pré-visualizações e Códigos Prontos:**")
        c1, c2, c3 = st.columns(3)
        with c1: 
            st.latex(r"\sin(\theta)"); st.code(r"$\sin(\theta)$", language="latex")
            st.latex(r"\cos(\theta)"); st.code(r"$\cos(\theta)$", language="latex")
        with c2: 
            st.latex(r"\tan(\theta)"); st.code(r"$\tan(\theta)$", language="latex")
            st.latex(r"\pi"); st.code(r"$\pi$", language="latex")
        with c3: 
            st.latex(r"90^\circ"); st.code(r"$90^\circ$", language="latex")
            st.latex(r"\triangle ABC"); st.code(r"$\triangle ABC$", language="latex")
            
    with t_simb:
        st.write("**Pré-visualizações e Códigos Prontos:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            st.latex(r"\alpha"); st.code(r"$\alpha$", language="latex")
            st.latex(r"\beta"); st.code(r"$\beta$", language="latex")
        with c2: 
            st.latex(r"\ge"); st.code(r"$\ge$", language="latex")
            st.latex(r"\le"); st.code(r"$\le$", language="latex")
        with c3: 
            st.latex(r"\in"); st.code(r"$\in$", language="latex")
            st.latex(r"\notin"); st.code(r"$\notin$", language="latex")
        with c4: 
            st.latex(r"\approx"); st.code(r"$\approx$", language="latex")
            st.latex(r"\neq"); st.code(r"$\neq$", language="latex")
# --- 6. O EDITOR EM BLOCOS ---
opcoes_niveis = ["Fácil", "Intermediária", "Complexa"]
opcoes_permitidas = opcoes_niveis[opcoes_niveis.index(origem.get('complexidade', 'Fácil')):] if modo_atual == "clone" and origem else opcoes_niveis

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
        
        st.write("**Texto de Apoio (Opcional)**")
        
        # Define o estado inicial do rádio botão com base no id existente
        idx_radio = 0
        if val_id_texto_base:
            idx_radio = 1 # "Selecionar do Acervo"
            
        tipo_texto = st.radio("Origem:", ["Nenhum", "Selecionar do Acervo", "Cadastrar Novo"], horizontal=True, index=idx_radio)
        
        texto_base_final = ""
        id_texto_final = val_id_texto_base
        titulo_novo = ""
        
        if tipo_texto == "Selecionar do Acervo":
            if not df_textos.empty:
                titulos_dict = dict(zip(df_textos.titulo, df_textos.id))
                opcoes_titulos = ["-- Selecione --"] + list(titulos_dict.keys())
                
                # Se estava editando/clonando, tenta achar o título atual para selecionar
                idx_selecionado = 0
                if id_texto_final in df_textos.id.values:
                    titulo_atual = df_textos[df_textos['id'] == id_texto_final]['titulo'].values[0]
                    if titulo_atual in opcoes_titulos:
                        idx_selecionado = opcoes_titulos.index(titulo_atual)
                        
                texto_selecionado = st.selectbox("Textos cadastrados:", opcoes_titulos, index=idx_selecionado)
                
                if texto_selecionado != "-- Selecione --":
                    id_texto_final = titulos_dict.get(texto_selecionado)
                    texto_base_final = df_textos[df_textos['id'] == id_texto_final]['conteudo'].values[0]
            else:
                st.warning("Nenhum texto cadastrado no acervo. Crie um novo.")
                tipo_texto = "Cadastrar Novo"
                
        if tipo_texto == "Cadastrar Novo":
            st.info("Este texto será salvo no acervo para futuras questões.")
            titulo_novo = st.text_input("Título do Novo Texto")
            texto_base_final = st.text_area("Conteúdo do Texto", height=100)

        img_apoio = st.file_uploader("Imagem do Enunciado", type=['png', 'jpg'])
        enunciado_input = st.text_area("Enunciado (A Pergunta)*", value=val_enunciado, height=100)
        
        if st.button("✨ Revisar Contexto e Imagem", use_container_width=True):
            with st.spinner("Analisando alinhamento..."):
                prompt_ctx = f"""Atue como revisor pedagógico. Revise a clareza deste enunciado escolar: '{enunciado_input}'. Texto base associado: '{texto_base_final}'. Avise se a imagem (se houver) precisa de elementos específicos para o enunciado fazer sentido. Retorne ESTRITAMENTE em formato JSON puro: {{"enunciado": "...", "aviso_imagem": "..."}}"""
                try:
                    res = modelo_ia.generate_content(prompt_ctx)
                    texto_json = res.text.replace("```json", "").replace("```", "").strip()
                    dados_ctx = json.loads(texto_json)
                    st.success("Revisão concluída!")
                    st.info(f"🖼️ **Parecer sobre a Imagem:** {dados_ctx.get('aviso_imagem', 'Ok')}")
                    st.text_area("Sugestão de Enunciado (Copie se gostar):", value=dados_ctx.get('enunciado', ''))
                except Exception as e:
                    st.error(f"Erro ao formatar a revisão da IA. Tente novamente.")

    # ==========================================
    # BLOCO 2: ALTERNATIVAS
    # ==========================================
    with st.container(border=True):
        st.markdown("### 2️⃣ Bloco de Alternativas")
        lista_gabarito = ["A", "B", "C", "D"]
        idx_gab = lista_gabarito.index(val_gabarito) if val_gabarito in lista_gabarito else 0
        gabarito = st.selectbox("Gabarito Oficial*", lista_gabarito, index=idx_gab)
        
        st.caption("⚠️ **Aviso de Imagens:** Suba imagens individuais (Apenas o gráfico da letra A, por exemplo).")
        
        alt_A = st.text_area("A)", value=val_alt_a, height=68)
        img_A = st.file_uploader("Img A", type=['png', 'jpg'], key="img_a")
        
        alt_B = st.text_area("B)", value=val_alt_b, height=68)
        img_B = st.file_uploader("Img B", type=['png', 'jpg'], key="img_b")
        
        alt_C = st.text_area("C)", value=val_alt_c, height=68)
        img_C = st.file_uploader("Img C", type=['png', 'jpg'], key="img_c")
        
        alt_D = st.text_area("D)", value=val_alt_d, height=68)
        img_D = st.file_uploader("Img D", type=['png', 'jpg'], key="img_d")

    # ==========================================
    # BLOCO 3: RESOLUÇÃO
    # ==========================================
    with st.container(border=True):
        st.markdown("### 3️⃣ Bloco de Resolução")
        resolucao_input = st.text_area("Passo a passo da resposta", value=val_resolucao, height=100)
        
        if st.button("✨ Gerar Resolução Passo a Passo com IA", use_container_width=True):
            if not enunciado_input or not alt_A:
                st.warning("Preencha o enunciado e as alternativas primeiro.")
            else:
                with st.spinner("Resolvendo a questão..."):
                    dicionario_alts = {"A": alt_A, "B": alt_B, "C": alt_C, "D": alt_D}
                    resposta_correta = dicionario_alts.get(gabarito, "")
                    prompt_res = f"Atue como professor. Resolva esta questão passo a passo, justificando a resposta correta '{gabarito}) {resposta_correta}'. Enunciado: {enunciado_input}. Seja direto e didático."
                    try:
                        res_resolucao = modelo_ia.generate_content(prompt_res)
                        st.success("Resolução gerada!")
                        st.info(res_resolucao.text)
                        st.caption("Copie a resolução acima e cole na caixa de texto para salvar.")
                    except:
                        st.error("Erro ao gerar resolução.")

with col_preview:
    with st.container(border=True):
        st.markdown("### 👀 Visualização Final")
        st.divider()
        if texto_base_final: st.markdown(f"*{texto_base_final}*")
        if img_apoio: st.image(img_apoio, use_container_width=True)
        if enunciado_input: st.markdown(f"**Questão:** {enunciado_input}")
        st.markdown("---")
        if alt_A or img_A: st.markdown(f"**A)** {alt_A}"); st.image(img_A, width=150) if img_A else None
        if alt_B or img_B: st.markdown(f"**B)** {alt_B}"); st.image(img_B, width=150) if img_B else None
        if alt_C or img_C: st.markdown(f"**C)** {alt_C}"); st.image(img_C, width=150) if img_C else None
        if alt_D or img_D: st.markdown(f"**D)** {alt_D}"); st.image(img_D, width=150) if img_D else None
        st.divider()
        if resolucao_input:
            st.markdown("**Resolução Esperada:**")
            st.caption(resolucao_input)

st.divider()

# --- 7. GRAVAÇÃO SEGURA NO BANCO ---
texto_botao = "🔄 Atualizar Questão" if modo_atual == "edicao" else "💾 Salvar Questão"

if st.button(texto_botao, use_container_width=True, type="primary"):
    if enunciado_input and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Gravando no banco oficial..."):
            
            # 1. Verifica Textos Base Novos
            if tipo_texto == "Cadastrar Novo" and titulo_novo and texto_base_final:
                novo_texto_db = {"titulo": titulo_novo, "conteudo": texto_base_final, "autor": st.session_state.nome_usuario}
                try:
                    res_texto = supabase.table("textos_base").insert(novo_texto_db).execute()
                    id_texto_final = res_texto.data[0]['id']
                except Exception as e:
                    st.error(f"Erro ao salvar texto base: {e}")
                    st.stop()
            elif tipo_texto == "Nenhum":
                id_texto_final = None
            
            # 2. Pacote da Questão
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": True if img_A else False},
                "B": {"texto": alt_B, "tem_imagem": True if img_B else False},
                "C": {"texto": alt_C, "tem_imagem": True if img_C else False},
                "D": {"texto": alt_D, "tem_imagem": True if img_D else False}
            }
            
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "id_texto_base": id_texto_final,
                "autor": st.session_state.nome_usuario,
                "status": "Concluída",
                "complexidade": complexidade,
                "enunciado": enunciado_input,
                "imagem_url": None, # Próximo passo: Conectar ao Storage do Supabase!
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "resolucao": resolucao_input,
                "tags": tags
            }
            
            # 3. Execução
            try:
                if modo_atual == "edicao" and origem:
                    supabase.table("questoes").update(nova_questao).eq("id", origem['id']).execute()
                    st.success("✅ Questão atualizada!")
                    if 'edit_mode' in st.session_state: del st.session_state.edit_mode
                else:
                    supabase.table("questoes").insert(nova_questao).execute()
                    st.success("✅ Nova questão salva!")
                    if 'clone_mode' in st.session_state: del st.session_state.clone_mode
                
                # Recarrega a página para limpar os campos após sucesso
                import time
                st.balloons()
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro no banco: {e}")
    else:
        st.error("Preencha o Enunciado e as 4 Alternativas para salvar.")
