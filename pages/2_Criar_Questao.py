# --- LÓGICA DE EDIÇÃO/CLONAGEM ---
origem = None
if 'edit_mode' in st.session_state:
    origem = st.session_state.edit_mode
    st.info(f"🔄 **Modo de Edição:** Alterando questão de ID {origem['id']}")
elif 'clone_mode' in st.session_state:
    origem = st.session_state.clone_mode
    st.warning(f"🐑 **Modo Clonagem:** Criando baseada no item de {origem['autor']}")

# Preenchimento automático dos campos
val_enunciado = origem['enunciado'] if origem else ""
val_alt_a = origem['alternativas']['A']['texto'] if origem else ""
# ... fazer o mesmo para B, C, D e Texto Base ...

# REGRA DE COMPLEXIDADE NA CLONAGEM
if 'clone_mode' in st.session_state:
    niveis = ["Fácil", "Intermediária", "Complexa"]
    index_minimo = niveis.index(origem['complexidade'])
    opcoes_permitidas = niveis[index_minimo:] # Corta os níveis inferiores
else:
    opcoes_permitidas = ["Fácil", "Intermediária", "Complexa"]

complexidade = st.select_slider("Complexidade", options=opcoes_permitidas)
