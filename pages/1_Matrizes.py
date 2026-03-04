import streamlit as st
import pandas as pd

# ... (código anterior de segurança e inicialização) ...

st.title("⚙️ Configuração de Matrizes")

# Criamos abas (Tabs) para separar o Cadastro Manual da Importação Rápida
aba1, aba2 = st.tabs(["✍️ Cadastro Manual", "📤 Importar Planilha (Google Sheets/Excel)"])

# --- ABA 1: O cadastro manual que já tínhamos ---
with aba1:
    st.write("Cadastre habilidades pontuais.")
    # (Aqui entra aquele formulário que criamos na mensagem anterior)

# --- ABA 2: O IMPORTADOR MÁGICO ---
with aba2:
    st.subheader("Importação em Lote")
    st.write("Faça o upload da sua planilha do Google Sheets (baixe como .xlsx ou .csv).")
    st.info("💡 A sua planilha deve ter colunas com nomes parecidos com: Código, Componente, Ano e Descrição.")
    
    arquivo_upload = st.file_uploader("Arraste sua planilha aqui", type=['csv', 'xlsx'])
    
    if arquivo_upload is not None:
        # O Pandas lê o arquivo mágico
        try:
            if arquivo_upload.name.endswith('.csv'):
                df_importado = pd.read_csv(arquivo_upload)
            else:
                df_importado = pd.read_excel(arquivo_upload)
            
            # Mostra uma prévia para o ADM conferir antes de salvar
            st.write("👀 Prévia dos dados encontrados:")
            st.dataframe(df_importado.head(5), use_container_width=True)
            
            # Botão de confirmação
            if st.button("✅ Confirmar e Importar para o Sistema", type="primary"):
                # Aqui, no futuro, faremos o insert no Supabase.
                # Por enquanto, salvamos na sessão de testes:
                for index, linha in df_importado.iterrows():
                    nova_hab = {
                        "Código": linha.get('Código', f"Auto-{index}"),
                        "Componente": linha.get('Componente', 'Não definido'),
                        "Ano": linha.get('Ano', 'Não definido'),
                        "Descrição": linha.get('Descrição', 'Sem descrição')
                    }
                    st.session_state.habilidades.append(nova_hab)
                st.success(f"{len(df_importado)} habilidades importadas com sucesso!")
                
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
