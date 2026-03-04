import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

st.set_page_config(page_title="Elaborador de Itens", page_icon="📝", layout="wide")

# --- 1. VERIFICAÇÃO DE SEGURANÇA E INTEGRIDADE ---
if not st.session_state.get('usuario_logado'):
    st.switch_page("app.py")

# Se de alguma forma o usuário burlar o app.py e chegar aqui sem matrizes, o sistema trava.
if len(st.session_state.get('habilidades', [])) == 0:
    st.error("⛔ As matrizes de referência ainda não foram carregadas pela coordenação. Acesso bloqueado.")
    st.stop()

# Inicializa o banco de questões na sessão (Nossa tabela 'Questoes')
if 'questoes_banco' not in st.session_state:
    st.session_state.questoes_banco = []

# --- MENU LATERAL ---
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.perfil}**")
    st.divider()
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("📝 Elaboração de Itens")
st.write("Estruture novas questões para o ciclo avaliativo. Todos os itens devem estar vinculados a uma habilidade válida.")

# --- 2. FILTROS DINÂMICOS (Lendo da Matriz Importada) ---
df_matriz = pd.DataFrame(st.session_state.habilidades)

st.subheader("1. Parâmetros Curriculares")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    # Puxa os componentes únicos que existem na matriz
    componentes_disponiveis = df_matriz['Componente'].unique().tolist()
    componente_sel = st.selectbox("Componente", componentes_disponiveis)

with col_p2:
    # Puxa os anos únicos vinculados ao componente selecionado
    anos_filtrados = df_matriz[df_matriz['Componente'] == componente_sel]['Ano'].unique().tolist()
    ano_sel = st.selectbox("Ano de Ensino", anos_filtrados)

with col_p3:
    # Filtra as habilidades exatas baseadas no Componente e Ano escolhidos!
    hab_filtradas = df_matriz[(df_matriz['Componente'] == componente_sel) & (df_matriz['Ano'] == ano_sel)]
    lista_codigos_hab = hab_filtradas['Código'].tolist()
    
    if len(lista_codigos_hab) > 0:
        habilidade_sel = st.selectbox("Habilidade (Descritor)", lista_codigos_hab)
        # Mostra a descrição da habilidade como dica para o professor
        desc_atual = hab_filtradas[hab_filtradas['Código'] == habilidade_sel]['Descrição'].values[0]
        st.caption(f"**Descrição:** {desc_atual}")
    else:
        st.error("Nenhuma habilidade cadastrada para este filtro.")
        st.stop()

st.divider()

# --- 3. EDITOR DA QUESTÃO ---
st.subheader("2. Estrutura do Item")

col_meta1, col_meta2 = st.columns(2)
with col_meta1:
    complexidade = st.select_slider("Complexidade Esperada (Neste Ano)", options=["Fácil", "Intermediária", "Complexa"])
with col_meta2:
    tipo_fonte = st.selectbox("Origem do Item", ["Própria (Inédita)", "Adaptada", "Externa (Cópia fiel)"])
    if tipo_fonte != "Própria (Inédita)":
        fonte_nome = st.text_input("Especifique a Fonte (Ex: SAEB 2023, Concurso Prefeitura...)")
    else:
        fonte_nome = "Autoria Própria"

# Abas para separar a edição manual da IA
aba_editor, aba_ia = st.tabs(["✍️ Editor Manual", "🤖 Assistente de IA (Gemini)"])

with aba_editor:
    with st.form("form_nova_questao", clear_on_submit=True):
        st.write("**Texto Base e Enunciado**")
        st.info("💡 Suporta equações matemáticas. Para frações, use a sintaxe LaTeX entre cifrões, ex: $\\frac{1}{2}$")
        
        texto_base = st.text_area(
            "Texto de Apoio / Contextualização (Opcional)", 
            height=150, 
            placeholder="Ex: Leia o texto sobre as marés no município da Raposa..."
        )
        
        imagem_apoio = st.file_uploader("Imagem de Apoio (Gráficos, Tirinhas)", type=['png', 'jpg', 'jpeg'])
        
        enunciado = st.text_area("Enunciado (A Pergunta)*", height=100)
        
        st.write("**Alternativas**")
        col_alt_a, col_alt_b = st.columns(2)
        with col_alt_a:
            alt_A = st.text_input("A)")
            alt_C = st.text_input("C)")
        with col_alt_b:
            alt_B = st.text_input("B)")
            alt_D = st.text_input("D)")
            
        gabarito = st.selectbox("Gabarito Correto*", ["A", "B", "C", "D"])
        
        submit_questao = st.form_submit_button("💾 Salvar Item no Banco de Questões", type="primary")
        
        if submit_questao:
            if enunciado and alt_A and alt_B and alt_C and alt_D:
                nova_questao = {
                    "ID": f"Q-{len(st.session_state.questoes_banco)+1}",
                    "Componente": componente_sel,
                    "Ano": ano_sel,
                    "Habilidade": habilidade_sel,
                    "Complexidade": complexidade,
                    "Fonte": f"{tipo_fonte} - {fonte_nome}",
                    "Texto Base": texto_base,
                    "Enunciado": enunciado,
                    "Alternativas": {"A": alt_A, "B": alt_B, "C": alt_C, "D": alt_D},
                    "Gabarito": gabarito,
                    "Tem_Imagem": True if imagem_apoio else False
                }
                st.session_state.questoes_banco.append(nova_questao)
                st.success("✅ Item salvo com sucesso no banco de dados!")
                st.balloons()
            else:
                st.error("Preencha o enunciado e todas as alternativas para salvar o item.")

with aba_ia:
    st.subheader("Gerador e Revisor Inteligente")
    st.write("Descreva o tema e a IA criará uma sugestão de questão focada na habilidade selecionada.")
    
    tema_ia = st.text_input("Qual o tema da questão?", placeholder="Ex: Equação de 1º grau envolvendo compra de materiais escolares.")
    
    if st.button("✨ Gerar Sugestão de Item"):
        # Aqui ficará a chamada real para a API do Gemini.
        # Por enquanto, mostramos um aviso visual de como a integração funcionará:
        st.info("🔄 Conectando ao motor Google Gemini...")
        st.markdown(f"""
        **Exemplo do que a IA retornaria com base no seu banco:**
        * **Habilidade Alvo:** {habilidade_sel} ({desc_atual})
        * **Enunciado Sugerido:** "Uma escola comprou 3 caixas de lápis e 5 cadernos, gastando um total de R$ 85,00..."
        * **Distratores Sugeridos:**
          * A) (Erro comum de sinal)
          * B) (Esqueceu de multiplicar a variável)
        """)
        st.caption("Nota: Para ativar a geração real, precisaremos configurar a chave secreta no arquivo .env na próxima etapa.")
