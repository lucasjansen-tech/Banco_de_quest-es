import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Gestão de Matrizes", page_icon="⚙️", layout="wide")

if not st.session_state.get('usuario_logado') or st.session_state.get('perfil') != "Administrador":
    st.switch_page("app.py")

# CONEXÃO SUPABASE
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_connection()

with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.get('perfil', 'Usuário')}**")
    st.divider()
    st.page_link("app.py", label="Voltar ao Dashboard", icon="⬅️")
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.switch_page("app.py")

st.title("⚙️ Configuração de Matrizes")
st.write("Alimente o **Banco de Dados Oficial** importando a planilha da rede.")

arquivo_upload = st.file_uploader("Selecione sua planilha (.xlsx ou .csv)", type=['csv', 'xlsx'])

if arquivo_upload is not None:
    try:
        if arquivo_upload.name.endswith('.csv'):
            df = pd.read_csv(arquivo_upload)
        else:
            df = pd.read_excel(arquivo_upload)
            
        df.columns = df.columns.str.upper().str.strip()
        colunas_esperadas = ['ANO', 'HABILIDADE', 'DESCRIÇÃO', 'COMPONENTE']
        colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Erro: Faltam as colunas: {', '.join(colunas_faltantes)}")
        else:
            st.success("✅ Planilha validada! Estrutura correta.")
            st.dataframe(df.head(3), use_container_width=True)
            
            if st.button("📥 Gravar no Banco de Dados Supabase", type="primary"):
                with st.spinner("Salvando na nuvem..."):
                    # Prepara a lista de dicionários para o Supabase baseada no nosso SQL
                    dados_para_inserir = []
                    for _, linha in df.iterrows():
                        dados_para_inserir.append({
                            "ano": str(linha['ANO']).strip(),
                            "codigo_habilidade": str(linha['HABILIDADE']).strip(),
                            "descricao": str(linha['DESCRIÇÃO']).strip(),
                            "componente": str(linha['COMPONENTE']).strip().upper()
                        })
                    
                    # Dispara o comando de INSERT
                    resposta = supabase.table("matrizes").insert(dados_para_inserir).execute()
                    
                    st.success(f"🎉 Sucesso! {len(resposta.data)} habilidades foram salvas permanentemente.")
                    st.balloons()
                    
    except Exception as e:
        st.error(f"Erro inesperado: {e}")

st.divider()

# --- BUSCANDO DO BANCO DE DADOS REAL PARA EXIBIR ---
st.subheader("🗄️ Matrizes Salvas no Supabase")

try:
    # Faz um SELECT na tabela matrizes
    resposta_banco = supabase.table("matrizes").select("*").execute()
    
    if len(resposta_banco.data) > 0:
        df_banco = pd.DataFrame(resposta_banco.data)
        # Organiza a ordem das colunas para visualização
        df_banco = df_banco[['ano', 'componente', 'codigo_habilidade', 'descricao', 'created_at']]
        st.dataframe(df_banco, use_container_width=True, hide_index=True)
    else:
        st.info("O banco de dados oficial está vazio. Faça a primeira importação acima.")
except Exception as e:
    st.error(f"Erro ao buscar matrizes do banco: {e}")
