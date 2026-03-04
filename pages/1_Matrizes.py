import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestão de Matrizes", page_icon="⚙️", layout="wide")

if not st.session_state.get('usuario_logado') or st.session_state.get('perfil') != "Administrador":
    st.switch_page("app.py")

with st.sidebar:
    st.title("📚 Avalia System")
    st.page_link("app.py", label="Voltar ao Dashboard", icon="⬅️")

st.title("⚙️ Configuração de Matrizes")
st.write("Alimente o banco de dados principal importando a planilha oficial da rede.")

st.info("💡 Sua planilha deve conter exatamente as colunas: **ANO**, **HABILIDADE**, **DESCRIÇÃO** e **COMPONENTE**.")

arquivo_upload = st.file_uploader("Selecione sua planilha (.xlsx ou .csv)", type=['csv', 'xlsx'])

if arquivo_upload is not None:
    try:
        if arquivo_upload.name.endswith('.csv'):
            df = pd.read_csv(arquivo_upload)
        else:
            df = pd.read_excel(arquivo_upload)
            
        # Padroniza as colunas (maiúsculo e sem espaços)
        df.columns = df.columns.str.upper().str.strip()
        
        # Verifica se as colunas obrigatórias existem
        colunas_esperadas = ['ANO', 'HABILIDADE', 'DESCRIÇÃO', 'COMPONENTE']
        colunas_faltantes = [col for col in colunas_esperadas if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Erro: Faltam estas colunas na sua planilha: {', '.join(colunas_faltantes)}")
        else:
            st.success("✅ Planilha validada! Estrutura correta.")
            st.dataframe(df.head(5), use_container_width=True) # Mostra uma prévia
            
            if st.button("📥 Importar Dados para o Sistema", type="primary"):
                novas_habilidades = []
                novos_anos = set(st.session_state.anos_ensino)
                
                for _, linha in df.iterrows():
                    novas_habilidades.append({
                        "Ano": str(linha['ANO']).strip(),
                        "Código": str(linha['HABILIDADE']).strip(),
                        "Descrição": str(linha['DESCRIÇÃO']).strip(),
                        "Componente": str(linha['COMPONENTE']).strip().upper()
                    })
                    novos_anos.add(str(linha['ANO']).strip())
                
                # Salva no banco temporário
                st.session_state.habilidades = novas_habilidades
                st.session_state.anos_ensino = sorted(list(novos_anos))
                
                st.success(f"🎉 Matriz carregada com sucesso! {len(novas_habilidades)} habilidades registradas.")
                st.balloons()
                
    except Exception as e:
        st.error(f"Erro inesperado ao ler o arquivo: {e}")

# Mostra o banco atual se já existir
if len(st.session_state.habilidades) > 0:
    st.divider()
    st.subheader(f"🗄️ Banco de Matrizes Atual ({len(st.session_state.habilidades)} itens)")
    st.dataframe(pd.DataFrame(st.session_state.habilidades), use_container_width=True, hide_index=True)
