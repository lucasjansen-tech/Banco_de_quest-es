import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestão de Matrizes", page_icon="⚙️")

# --- VERIFICAÇÃO DE SEGURANÇA ---
# Impede que alguém acesse a página direto pelo link sem logar
if not st.session_state.get('usuario_logado'):
    st.warning("⚠️ Por favor, faça o login na página inicial para acessar o sistema.")
    st.stop()

# Impede que elaboradores editem as matrizes
if st.session_state.get('perfil') != "Administrador":
    st.error("⛔ Acesso negado. Apenas Administradores podem configurar as matrizes.")
    st.stop()

# --- INICIALIZAÇÃO DE DADOS (MEMÓRIA TEMPORÁRIA) ---
if 'anos_ensino' not in st.session_state:
    st.session_state.anos_ensino = ["1º Ano", "2º Ano", "3º Ano"]
if 'habilidades' not in st.session_state:
    st.session_state.habilidades = []

st.title("⚙️ Configuração de Matrizes")
st.write("Alimente o sistema com os Anos de Ensino e Habilidades. Estes dados alimentarão as listas suspensas da tela de elaboração de provas.")

# --- SEÇÃO 1: ANOS DE ENSINO ---
st.subheader("📚 Anos de Ensino")
col_ano1, col_ano2 = st.columns([2, 1])

with col_ano1:
    novo_ano = st.text_input("Adicionar novo Ano/Série (Ex: 4º Ano, 9º Ano)")
with col_ano2:
    st.write("") # Espaço para alinhar o botão
    st.write("")
    if st.button("➕ Adicionar Ano", use_container_width=True):
        if novo_ano and novo_ano not in st.session_state.anos_ensino:
            st.session_state.anos_ensino.append(novo_ano)
            st.success(f"'{novo_ano}' adicionado com sucesso!")
        elif novo_ano in st.session_state.anos_ensino:
            st.warning("Este ano já está cadastrado.")

# Mostra os anos cadastrados
st.caption(f"Anos atuais no sistema: {', '.join(st.session_state.anos_ensino)}")

st.divider()

# --- SEÇÃO 2: HABILIDADES E DESCRITORES ---
st.subheader("🎯 Cadastro de Habilidades (Descritores)")

with st.form("form_habilidades", clear_on_submit=True):
    col_hab1, col_hab2 = st.columns(2)
    
    with col_hab1:
        codigo = st.text_input("Código da Habilidade (Ex: D01, EF01MA02)*")
        componente = st.selectbox("Componente Curricular*", ["Língua Portuguesa", "Matemática"])
        
    with col_hab2:
        ano_vinculado = st.selectbox("Vincular a qual Ano?*", st.session_state.anos_ensino)
        
    descricao = st.text_area("Descrição completa da habilidade*")
    
    submit_hab = st.form_submit_button("💾 Salvar Habilidade no Banco")
    
    if submit_hab:
        if codigo and descricao:
            nova_hab = {
                "Código": codigo,
                "Componente": componente,
                "Ano": ano_vinculado,
                "Descrição": descricao
            }
            st.session_state.habilidades.append(nova_hab)
            st.success(f"Habilidade {codigo} cadastrada com sucesso!")
        else:
            st.error("Preencha os campos obrigatórios (*).")

# --- TABELA DE HABILIDADES CADASTRADAS ---
if st.session_state.habilidades:
    st.write("**Habilidades já cadastradas na sessão atual:**")
    df_hab = pd.DataFrame(st.session_state.habilidades)
    st.dataframe(df_hab, use_container_width=True, hide_index=True)
