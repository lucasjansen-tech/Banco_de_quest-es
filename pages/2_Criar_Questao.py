import streamlit as st
import pandas as pd
from supabase import create_client
import google.generativeai as genai
import json
import io
import uuid
from PIL import Image
import time

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

# --- FUNÇÃO NINJA DE COMPRESSÃO E UPLOAD DE IMAGENS ---
def processar_e_subir_imagem(arquivo_upload, prefixo):
    if arquivo_upload is None:
        return None
    try:
        imagem = Image.open(arquivo_upload)
        if imagem.mode in ("RGBA", "P"): 
            imagem = imagem.convert("RGB") 
            
        imagem.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        imagem.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()
        
        nome_arquivo = f"{prefixo}_{uuid.uuid4().hex[:8]}.jpg"
        
        supabase.storage.from_("imagens_questoes").upload(
            file=img_bytes, 
            path=nome_arquivo, 
            file_options={"content-type": "image/jpeg"}
        )
        
        return supabase.storage.from_("imagens_questoes").get_public_url(nome_arquivo)
        
    except Exception as e:
        st.error(f"Erro ao salvar a imagem {prefixo}: {e}")
        return None

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

# --- 3. LÓGICA DE EDIÇÃO/CLONAGEM E LOTE ---
origem = None
modo_atual = "novo"

# Memória para Criação em Sequência (Lote)
if 'modo_lote_id' not in st.session_state:
    st.session_state.modo_lote_id = None

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

val_id_texto_base = origem.get('id_texto_base', None) if origem else None
val_texto_suporte = origem.get('texto_suporte', "") if origem else ""
val_enunciado = origem.get('enunciado', "") if origem else ""
val_resolucao = origem.get('resolucao', "") if origem else ""
val_tags = origem.get('tags', "") if origem else ""
val_gabarito = origem.get('gabarito', 'A') if origem else 'A'

if origem and 'alternativas' in origem and origem['alternativas']:
    val_alt_a = origem['alternativas'].get('A', {}).get('texto', '')
    val_alt_b = origem['alternativas'].get('B', {}).get('texto', '')
    val_alt_c = origem['alternativas'].get('C', {}).get('texto', '')
    val_alt_d = origem['alternativas'].get('D', {}).get('texto', '')
else:
    val_alt_a, val_alt_b, val_alt_c, val_alt_d = "", "", "", ""

# A MÁGICA DO LOTE: Trava o Nível 1 se estiver criando várias questões do mesmo texto
if st.session_state.modo_lote_id and modo_atual == "novo":
    val_id_texto_base = st.session_state.modo_lote_id
    st.success("🔗 **Modo Sequência Ativo:** O Acervo (Nível 1) está travado para você criar a próxima questão da bateria.")
    if st.button("❌ Encerrar Sequência e Limpar Texto", size="small"):
        st.session_state.modo_lote_id = None
        st.rerun()

# --- 4. BUSCANDO DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_iniciais():
    matrizes = supabase.table("matrizes").select("id, ano, componente, codigo_habilidade, descricao").execute().data
    textos = supabase.table("textos_base").select("id, titulo, conteudo, imagem_url").execute().data
    return pd.DataFrame(matrizes), pd.DataFrame(textos)

df_matriz, df_textos = carregar_dados_iniciais()
if df_matriz.empty:
    st.error("⛔ Não há matrizes cadastradas no sistema. Acesse a Gestão de Matrizes.")
    st.stop()

# --- 5. PARÂMETROS E CATÁLOGO MATEMÁTICO ---
with st.expander("⚙️ Parâmetros Curriculares e Construtor de Fórmulas", expanded=True):
    col_p1, col_p2, col_p3 = st.columns(3)
    
    todos_componentes = df_matriz['componente'].unique().tolist()
    if st.session_state.get('perfil') == "Elaborador":
        comp_prof = st.session_state.get('componente', '')
        match_comp = next((c for c in todos_componentes if str(c).strip().upper() == str(comp_prof).strip().upper()), None)
        if match_comp:
            lista_componentes = [match_comp]
        else:
            st.error(f"Sua disciplina é '{comp_prof}', mas não há matrizes para ela no banco.")
            st.stop()
    else:
        lista_componentes = todos_componentes

    with col_p1: componente_sel = st.selectbox("Componente", lista_componentes)
    
    anos_disponiveis = df_matriz[df_matriz['componente'] == componente_sel]['ano'].unique().tolist()
    if not anos_disponiveis:
        st.stop()
        
    with col_p2: ano_sel = st.selectbox("Ano de Ensino", anos_disponiveis)
    
    habs_filtradas = df_matriz[(df_matriz['componente'] == componente_sel) & (df_matriz['ano'] == ano_sel)]
    if habs_filtradas.empty:
        st.stop()
        
    with col_p3:
        lista_codigos = habs_filtradas['codigo_habilidade'].tolist()
        habilidade_sel = st.selectbox("Habilidade", lista_codigos)
        linha_hab = habs_filtradas[habs_filtradas['codigo_habilidade'] == habilidade_sel].iloc[0]
        id_habilidade_banco = linha_hab['id']
        
    st.caption(f"**Matriz:** {linha_hab['descricao']}")

    st.divider()
    
    st.markdown("### 🧮 Construtor Matemático")
    t_frac, t_pot, t_raiz, t_trig, t_simb = st.tabs(["➗ Frações", "x² Potências", "√ Raízes", "📐 Geometria/Trig", "Ω Símbolos"])
    
    with t_frac:
        c1, c2 = st.columns(2)
        with c1: 
            num = st.text_input("Numerador", "1", key="num_f")
            den = st.text_input("Denominador", "2", key="den_f")
        with c2: 
            codigo_latex = f"\\frac{{{num}}}{{{den}}}"
            st.latex(codigo_latex); st.code(f"${codigo_latex}$", language="latex")
    with t_pot:
        c1, c2 = st.columns(2)
        with c1: 
            base = st.text_input("Base", "x", key="base_p")
            exp = st.text_input("Expoente", "2", key="exp_p")
        with c2: 
            codigo_latex = f"{base}^{{{exp}}}"
            st.latex(codigo_latex); st.code(f"${codigo_latex}$", language="latex")
    with t_raiz:
        c1, c2 = st.columns(2)
        with c1: 
            ind = st.text_input("Índice", "", key="ind_r")
            val = st.text_input("Valor Interno", "x", key="val_r")
        with c2: 
            codigo_latex = f"\\sqrt[{ind}]{{{val}}}" if ind else f"\\sqrt{{{val}}}"
            st.latex(codigo_latex); st.code(f"${codigo_latex}$", language="latex")
    with t_trig:
        c1, c2, c3 = st.columns(3)
        with c1: st.latex(r"\sin(\theta)"); st.code(r"$\sin(\theta)$", language="latex")
        with c2: st.latex(r"\tan(\theta)"); st.code(r"$\tan(\theta)$", language="latex")
        with c3: st.latex(r"90^\circ"); st.code(r"$90^\circ$", language="latex")
    with t_simb:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.latex(r"\alpha"); st.code(r"$\alpha$", language="latex")
        with c2: st.latex(r"\ge"); st.code(r"$\ge$", language="latex")
        with c3: st.latex(r"\in"); st.code(r"$\in$", language="latex")
        with c4: st.latex(r"\approx"); st.code(r"$\approx$", language="latex")

# --- 6. O EDITOR EM 3 NÍVEIS ---
opcoes_niveis = ["Fácil", "Intermediária", "Complexa"]
opcoes_permitidas = opcoes_niveis[opcoes_niveis.index(origem.get('complexidade', 'Fácil')):] if modo_atual == "clone" and origem else opcoes_niveis

col_editor, col_preview = st.columns([1.2, 1])

with col_editor:
    col_m1, col_m2 = st.columns(2)
    with col_m1: complexidade = st.select_slider("Nível", options=opcoes_permitidas)
    with col_m2: tags = st.text_input("Tags", value=val_tags)

    # ==========================================
    # BLOCO 1: ARQUITETURA DE CONTEXTO EM 3 NÍVEIS
    # ==========================================
    with st.container(border=True):
        st.markdown("### 1️⃣ Bloco de Contexto (3 Níveis)")
        
        # --- NÍVEL 1: ACERVO ---
        st.markdown("#### 📚 Nível 1: Acervo Compartilhado")
        st.caption("Textos ou imagens base que servem para várias questões.")
        
        idx_radio = 1 if val_id_texto_base else 0
        tipo_texto = st.radio("Origem:", ["Nenhum", "Selecionar do Acervo", "Cadastrar Novo"], horizontal=True, index=idx_radio)
        
        texto_base_final = ""
        url_img_acervo_existente = None
        id_texto_final = val_id_texto_base
        titulo_novo = ""
        img_acervo_nova = None
        
        if tipo_texto == "Selecionar do Acervo":
            if not df_textos.empty:
                titulos_dict = dict(zip(df_textos.titulo, df_textos.id))
                opcoes_titulos = ["-- Selecione --"] + list(titulos_dict.keys())
                
                idx_selecionado = 0
                if id_texto_final in df_textos.id.values:
                    titulo_atual = df_textos[df_textos['id'] == id_texto_final]['titulo'].values[0]
                    if titulo_atual in opcoes_titulos:
                        idx_selecionado = opcoes_titulos.index(titulo_atual)
                        
                texto_selecionado = st.selectbox("Textos cadastrados:", opcoes_titulos, index=idx_selecionado)
                
                if texto_selecionado != "-- Selecione --":
                    id_texto_final = titulos_dict.get(texto_selecionado)
                    linha_texto = df_textos[df_textos['id'] == id_texto_final].iloc[0]
                    texto_base_final = linha_texto['conteudo']
                    url_img_acervo_existente = linha_texto.get('imagem_url')
            else:
                st.warning("Nenhum texto cadastrado no acervo. Crie um novo.")
                tipo_texto = "Cadastrar Novo"
                
        if tipo_texto == "Cadastrar Novo":
            st.info("Este material será salvo no acervo para futuras questões.")
            titulo_novo = st.text_input("Título do Material")
            texto_base_final = st.text_area("Conteúdo (Texto I, Texto II, etc)", height=100)
            img_acervo_nova = st.file_uploader("Imagem Compartilhada (Opcional)", type=['png', 'jpg', 'jpeg'], key="up_img_acervo")

        # --- NÍVEL 2: SUPORTE ISOLADO ---
        st.divider()
        st.markdown("#### 🧩 Nível 2: Suporte Isolado")
        st.caption("Trecho ou imagem Específica APENAS para esta questão (Ex: 'Observe o recorte...').")
        texto_suporte_input = st.text_area("Texto Específico (Opcional)", value=val_texto_suporte, height=68)
        img_suporte_input = st.file_uploader("Imagem Específica (Opcional)", type=['png', 'jpg', 'jpeg'], key="up_img_suporte")

        # --- NÍVEL 3: COMANDO ---
        st.divider()
        st.markdown("#### 🎯 Nível 3: Comando da Questão")
        enunciado_input = st.text_area("Enunciado (A Pergunta Direta)*", value=val_enunciado, height=100)
        
        if st.button("✨ Revisar Alinhamento de Contexto", use_container_width=True):
            with st.spinner("Lendo todos os níveis de contexto..."):
                prompt_ctx = f"""Atue como revisor pedagógico. Analise se a pergunta faz sentido com os textos de apoio.
                Acervo (Nível 1): '{texto_base_final}'. 
                Suporte (Nível 2): '{texto_suporte_input}'. 
                Comando (Nível 3): '{enunciado_input}'.
                ATENÇÃO: Se houver fórmulas matemáticas (com $), preserve-as EXATAMENTE como estão (use duplo escape \\\\frac).
                Retorne ESTRITAMENTE em JSON: {{"parecer": "Sua análise breve aqui", "sugestao_comando": "Novo texto do comando melhorado, se necessário"}}"""
                try:
                    res = modelo_ia.generate_content(prompt_ctx)
                    texto_json = res.text.replace("```json", "").replace("```", "").strip()
                    dados_ctx = json.loads(texto_json)
                    st.success("Revisão concluída!")
                    st.info(f"📊 **Parecer:** {dados_ctx.get('parecer', 'Ok')}")
                    st.text_area("Sugestão de Comando (Copie se gostar):", value=dados_ctx.get('sugestao_comando', ''))
                except Exception as e:
                    st.error(f"Erro ao formatar a revisão da IA.")

    # ==========================================
    # BLOCO 2: ALTERNATIVAS
    # ==========================================
    with st.container(border=True):
        st.markdown("### 2️⃣ Bloco de Alternativas")
        lista_gabarito = ["A", "B", "C", "D"]
        idx_gab = lista_gabarito.index(val_gabarito) if val_gabarito in lista_gabarito else 0
        gabarito = st.selectbox("Gabarito Oficial*", lista_gabarito, index=idx_gab)
        
        alt_A = st.text_area("A)", value=val_alt_a, height=68)
        img_A = st.file_uploader("Img A", type=['png', 'jpg', 'jpeg'], key="up_img_a")
        
        alt_B = st.text_area("B)", value=val_alt_b, height=68)
        img_B = st.file_uploader("Img B", type=['png', 'jpg', 'jpeg'], key="up_img_b")
        
        alt_C = st.text_area("C)", value=val_alt_c, height=68)
        img_C = st.file_uploader("Img C", type=['png', 'jpg', 'jpeg'], key="up_img_c")
        
        alt_D = st.text_area("D)", value=val_alt_d, height=68)
        img_D = st.file_uploader("Img D", type=['png', 'jpg', 'jpeg'], key="up_img_d")

    # ==========================================
    # BLOCO 3: RESOLUÇÃO
    # ==========================================
    with st.container(border=True):
        st.markdown("### 3️⃣ Bloco de Resolução")
        resolucao_input = st.text_area("Passo a passo da resposta", value=val_resolucao, height=100)
        
        if st.button("✨ Gerar Resolução Passo a Passo", use_container_width=True):
            if not enunciado_input:
                st.warning("Preencha o comando primeiro.")
            else:
                with st.spinner("Resolvendo..."):
                    dicionario_alts = {"A": alt_A, "B": alt_B, "C": alt_C, "D": alt_D}
                    resposta_correta = dicionario_alts.get(gabarito, "")
                    prompt_res = f"""Atue como professor. Resolva justificando a resposta correta '{gabarito}) {resposta_correta}'. Nível 1: {texto_base_final}. Nível 2: {texto_suporte_input}. Comando: {enunciado_input}. Use formatação LaTeX entre sinais de cifrão para matemática."""
                    try:
                        res_resolucao = modelo_ia.generate_content(prompt_res)
                        st.success("Resolução gerada!")
                        st.info(res_resolucao.text)
                    except:
                        st.error("Erro ao gerar resolução.")

with col_preview:
    with st.container(border=True):
        st.markdown("### 👀 Visualização do Caderno")
        st.divider()
        
        # Renderiza Nível 1
        if texto_base_final: st.markdown(f"*{texto_base_final}*")
        if url_img_acervo_existente: st.image(url_img_acervo_existente, use_container_width=True)
        if img_acervo_nova: st.image(img_acervo_nova, use_container_width=True)
        
        # Renderiza Nível 2
        if texto_suporte_input or img_suporte_input:
            st.markdown("<br>", unsafe_allow_html=True)
            if texto_suporte_input: st.markdown(f"{texto_suporte_input}")
            if img_suporte_input: st.image(img_suporte_input, use_container_width=True)
            elif origem and origem.get('imagem_suporte_url'): st.image(origem.get('imagem_suporte_url'), use_container_width=True)
        
        # Renderiza Nível 3
        if enunciado_input: st.markdown(f"**{enunciado_input}**")
        
        st.markdown("---")
        
        # Renderiza Alternativas
        def render_alt(letra, texto, img_upload, chave_dict):
            if texto or img_upload or (origem and origem.get('alternativas', {}).get(chave_dict, {}).get('imagem_url')):
                st.markdown(f"**{letra})** {texto}")
                if img_upload: 
                    st.image(img_upload, width=150)
                elif origem and origem.get('alternativas', {}).get(chave_dict, {}).get('imagem_url'):
                    st.image(origem['alternativas'][chave_dict]['imagem_url'], width=150)

        render_alt("A", alt_A, img_A, "A")
        render_alt("B", alt_B, img_B, "B")
        render_alt("C", alt_C, img_C, "C")
        render_alt("D", alt_D, img_D, "D")
        
        st.divider()
        if resolucao_input:
            st.markdown("**Resolução Esperada:**")
            st.caption(resolucao_input)

st.divider()

# --- 7. GRAVAÇÃO SEGURA NO BANCO E NO STORAGE ---
def obter_url_final(upload_novo, prefixo, chave_alt=None):
    url_nova = processar_e_subir_imagem(upload_novo, prefixo)
    if url_nova: 
        return url_nova
    if modo_atual in ["edicao", "clone"] and origem:
        if chave_alt:
            return origem.get('alternativas', {}).get(chave_alt, {}).get('imagem_url')
        elif prefixo == "suporte":
            return origem.get('imagem_suporte_url')
    return None

st.markdown("### 💾 Finalizar Questão")
c_btn1, c_btn2 = st.columns(2)

if modo_atual == "edicao":
    btn_acionado = c_btn1.button("🔄 Atualizar Questão", use_container_width=True, type="primary")
    manter_lote = False
else:
    btn_acionado = c_btn1.button("💾 Salvar e Limpar Tela", use_container_width=True)
    btn_lote_acionado = c_btn2.button("➕ Salvar e Criar Próxima com o Mesmo Texto", type="primary", use_container_width=True)
    if btn_lote_acionado:
        btn_acionado = True
        manter_lote = True
    else:
        manter_lote = False

if btn_acionado:
    if enunciado_input and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Processando dados e salvando na nuvem..."):
            
            # 1. Trata o Nível 1 (Acervo)
            if tipo_texto == "Cadastrar Novo" and titulo_novo:
                url_img_acervo = processar_e_subir_imagem(img_acervo_nova, "acervo")
                novo_texto_db = {
                    "titulo": titulo_novo, 
                    "conteudo": texto_base_final, 
                    "autor": st.session_state.nome_usuario,
                    "imagem_url": url_img_acervo
                }
                try:
                    res_texto = supabase.table("textos_base").insert(novo_texto_db).execute()
                    id_texto_final = res_texto.data[0]['id']
                except Exception as e:
                    st.error(f"Erro ao salvar Acervo: {e}")
                    st.stop()
            elif tipo_texto == "Nenhum":
                id_texto_final = None
            
            # 2. Uploads do Nível 2 e Alternativas
            url_img_suporte = obter_url_final(img_suporte_input, "suporte")
            url_img_A = obter_url_final(img_A, "altA", "A")
            url_img_B = obter_url_final(img_B, "altB", "B")
            url_img_C = obter_url_final(img_C, "altC", "C")
            url_img_D = obter_url_final(img_D, "altD", "D")
            
            # 3. Pacote da Questão
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": bool(url_img_A), "imagem_url": url_img_A},
                "B": {"texto": alt_B, "tem_imagem": bool(url_img_B), "imagem_url": url_img_B},
                "C": {"texto": alt_C, "tem_imagem": bool(url_img_C), "imagem_url": url_img_C},
                "D": {"texto": alt_D, "tem_imagem": bool(url_img_D), "imagem_url": url_img_D}
            }
            
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "id_texto_base": id_texto_final,
                "autor": st.session_state.nome_usuario,
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_suporte": texto_suporte_input,
                "imagem_suporte_url": url_img_suporte,
                "enunciado": enunciado_input,
                "imagem_url": None, 
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "resolucao": resolucao_input,
                "tags": tags
            }
            
            # 4. Execução no Banco
            try:
                if modo_atual == "edicao" and origem:
                    supabase.table("questoes").update(nova_questao).eq("id", origem['id']).execute()
                    st.success("✅ Questão atualizada!")
                    if 'edit_mode' in st.session_state: del st.session_state.edit_mode
                else:
                    supabase.table("questoes").insert(nova_questao).execute()
                    st.success("✅ Questão salva com sucesso!")
                    if 'clone_mode' in st.session_state: del st.session_state.clone_mode
                    
                    # GERENCIAMENTO DO MODO LOTE (Trava da Memória)
                    if manter_lote and id_texto_final:
                        st.session_state.modo_lote_id = id_texto_final
                    else:
                        st.session_state.modo_lote_id = None
                
                st.balloons()
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro no banco: {e}")
    else:
        st.error("Preencha o Comando (Enunciado) e as 4 Alternativas para salvar.")
