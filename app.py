import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestão de Matrizes", page_icon="⚙️")

# --- VERIFICAÇÃO DE SEGURANÇA ---
if not st.session_state.get('usuario_logado'):
    st.warning("⚠️ Por favor, faça o login na página inicial para acessar o sistema.")
    st.stop()

if st.session_state.get('perfil') != "Administrador":
    st.error("⛔ Acesso negado. Apenas Administradores podem configurar as matrizes.")
    st.stop()

# --- INICIALIZAÇÃO DE DADOS ---
if 'anos_ensino' not in st.session_state:
    st.session_state.anos_ensino = ["1º Ano", "2º Ano", "3º Ano"]
if 'habilidades' not in st.session_state:
    st.session_state.habilidades = []

st.title("⚙️ Configuração de Matrizes")

# Criamos as abas. A primeira lista na array é a que abre por padrão.
aba1, aba2 = st.tabs(["✍️ Cadastro Manual", "📤 Importar Planilha (Google Sheets)"])

# --- ABA 1: CADASTRO MANUAL ---
with aba1:
    st.write("Cadastre habilidades pontuais ou crie novos anos de ensino.")
    
    col_ano1, col_ano2 = st.columns([2, 1])
    with col_ano1:
        novo_ano = st.text_input("Adicionar novo Ano/Série (Ex: 4º Ano)")
    with col_ano2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar Ano", use_container_width=True):
            if novo_ano and novo_ano not in st.session_state.anos_ensino:
                st.session_state.anos_ensino.append(novo_ano)
                st.success(f"'{novo_ano}' adicionado!")

    st.divider()

    with st.form("form_habilidades", clear_on_submit=True):
        st.subheader("Cadastrar Habilidade Única")
        col_hab1, col_hab2 = st.columns(2)
        with col_hab1:
            codigo = st.text_input("Código (Ex: 2AP1.1)*")
            componente = st.selectbox("Componente Curricular*", ["LÍNGUA PORTUGUESA", "MATEMÁTICA"])
        with col_hab2:
            ano_vinculado = st.selectbox("Ano de Ensino*", st.session_state.anos_ensino)
            
        descricao = st.text_area("Descrição da habilidade*")
        
        if st.form_submit_button("💾 Salvar Habilidade"):
            if codigo and descricao:
                st.session_state.habilidades.append({"Código": codigo, "Componente": componente, "Ano": ano_vinculado, "Descrição": descricao})
                st.success("Habilidade cadastrada!")


# --- ABA 2: IMPORTADOR MÁGICO (Configurado para sua planilha) ---
with aba2:
    st.subheader("Importação em Lote")
    st.write("Faça o upload da planilha com as colunas: **ANO, HABILIDADE, DESCRIÇÃO e COMPONENTE**.")
    
    arquivo_upload = st.file_uploader("Arraste sua planilha (.csv ou .xlsx)", type=['csv', 'xlsx'])
    
    if arquivo_upload is not None:
        try:
            # Lê o arquivo
            if arquivo_upload.name.endswith('.csv'):
                df_importado = pd.read_csv(arquivo_upload)
            else:
                df_importado = pd.read_excel(arquivo_upload)
            
            # Força o nome das colunas a ficarem em maiúsculo e sem espaços extras para evitar erros
            df_importado.columns = df_importado.columns.str.upper().str.strip()
            
            st.write("👀 Prévia dos dados lidos da sua planilha:")
            st.dataframe(df_importado.head(3), use_container_width=True)
            
            if st.button("✅ Confirmar e Importar para o Sistema", type="primary"):
                contador = 0
                for index, linha in df_importado.iterrows():
                    
                    # Faz o DE-PARA lendo exatamente os nomes das suas colunas
                    nova_hab = {
                        "Código": linha.get('HABILIDADE', f"Sem Código {index}"),
                        "Componente": linha.get('COMPONENTE', 'Não definido'),
                        "Ano": linha.get('ANO', 'Não definido'),
                        "Descrição": linha.get('DESCRIÇÃO', 'Sem descrição')
                    }
                    
                    # Adiciona a habilidade
                    st.session_state.habilidades.append(nova_hab)
                    contador += 1
                    
                    # BÔNUS: Se a planilha tiver um 'Ano' que o sistema ainda não tem, ele adiciona sozinho!
                    ano_planilha = str(linha.get('ANO', '')).strip()
                    if ano_planilha and ano_planilha not in st.session_state.anos_ensino:
                        st.session_state.anos_ensino.append(ano_planilha)
                        
                st.success(f"🎉 Sucesso! {contador} habilidades foram importadas para o banco temporário.")
                
        except Exception as e:
            st.error(f"Erro ao processar a planilha. Tem certeza que ela possui as colunas ANO, HABILIDADE, DESCRIÇÃO e COMPONENTE? Erro técnico: {e}")

# --- TABELA DE HABILIDADES GERAIS ---
if st.session_state.habilidades:
    st.divider()
    st.write("**📚 Banco de Habilidades Atual:**")
    df_hab = pd.DataFrame(st.session_state.habilidades)
    st.dataframe(df_hab, use_container_width=True, hide_index=True)
