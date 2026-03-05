st.divider()

# --- BOTÃO DE SALVAMENTO ---
# Retirei o type="primary" apenas para garantir, mas com o novo config.toml ele ficaria azul.
if st.button("💾 Salvar Item no Banco de Dados", use_container_width=True):
    if enunciado and alt_A and alt_B and alt_C and alt_D:
        with st.spinner("Salvando na nuvem..."):
            dict_alternativas = {
                "A": {"texto": alt_A, "tem_imagem": True if img_A else False},
                "B": {"texto": alt_B, "tem_imagem": True if img_B else False},
                "C": {"texto": alt_C, "tem_imagem": True if img_C else False},
                "D": {"texto": alt_D, "tem_imagem": True if img_D else False}
            }
            
            # PACOTE CORRIGIDO: Exatamente com os nomes das colunas do banco de dados!
            nova_questao = {
                "id_habilidade": id_habilidade_banco,
                "autor": st.session_state.perfil,
                "status": "Concluída",
                "complexidade": complexidade,
                "texto_base": texto_base,
                "enunciado": enunciado,
                "imagem_url": None, # Corrigido: O banco espera 'imagem_url', não 'tem_imagem_apoio'
                "alternativas": dict_alternativas,
                "gabarito": gabarito,
                "tags": tags
            }
            
            try:
                supabase.table("questoes").insert(nova_questao).execute()
                st.success("✅ Questão com formatação avançada salva com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")
    else:
        st.error("Preencha o enunciado e o texto de todas as alternativas para salvar.")
