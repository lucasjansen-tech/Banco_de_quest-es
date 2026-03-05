# 5. MENU LATERAL
with st.sidebar:
    st.title("📚 Avalia System")
    st.markdown(f"**👤 {st.session_state.perfil}**")
    st.divider()
    
    st.markdown("### 📌 Navegação")
    st.page_link("app.py", label="Dashboard Principal", icon="📊")
    
    # Matrizes só para o Admin
    if st.session_state.perfil == "Administrador":
        st.page_link("pages/1_Matrizes.py", label="Gestão de Matrizes", icon="⚙️")
        
    # O LINK QUE FALTAVA (Liberado para ambos os perfis)
    st.page_link("pages/2_Criar_Questao.py", label="Criar Questões", icon="📝")
    
    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.perfil = None
        st.rerun()
