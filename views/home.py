import streamlit as st
from streamlit_lottie import st_lottie
import requests
import json
from forms.contact import cadastrar_cliente  # Importando a função de cadastro


def showHome():
    # Adicionando Font Awesome para ícones e a nova fonte
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
        .title {
            text-align: center;
            font-size: 50px;
            font-family: 'Poppins', sans-serif;
        }
        .highlight {
            color: #6A0DAD; /* Lilás escuro */
        }
        .subheader {
            text-align: center;
            font-size: 30px;
            font-family: 'Poppins', sans-serif;
        }
        .benefits {
            font-size: 20px;
            font-family: 'Poppins', sans-serif;
            margin: 20px 0;
        }
        .icon {
            color: #6A0DAD; /* Lilás escuro */
            font-size: 24px;
            margin-right: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Título da página
    st.markdown(
        f"<h1 class='title'>Bem-vindo ao <span class='highlight'>Chat Med</span></h1>",
        unsafe_allow_html=True
    )

    # Apresentação do Chat Med
    st.write("O Chat Med é a sua inteligência artificial para análise e pesquisa de grandes bancos de dados na indústria farmacêutica. Ele transforma a maneira como você acessa informações críticas, oferecendo respostas rápidas e precisas.")

    # Exibindo a imagem do Chat Med
    st.image("./src/img/oraculo-logo.png", width=230)

    # --- BENEFÍCIOS DO CHAT MED ---
    st.subheader("Benefícios do Chat Med", anchor=False)
    st.write(
        """
        <div class='benefits'>
            <i class="fas fa-clock icon"></i> **Eficiência na Análise de Dados:** O Chat Med processa milhões de dados em segundos, economizando tempo valioso.
        </div>
        <div class='benefits'>
            <i class="fas fa-check-circle icon"></i> **Respostas Precisas:** Pergunte qualquer informação e receba respostas detalhadas instantaneamente.
        </div>
        <div class='benefits'>
            <i class="fas fa-dollar-sign icon"></i> **Redução de Custos:** Elimine gastos com pesquisas manuais e obtenha resultados rápidos com uma ferramenta acessível.
        </div>
        <div class='benefits'>
            <i class="fas fa-share-alt icon"></i> **Integração de Dados:** Obtenha uma visão abrangente ao integrar informações de diversas fontes.
        </div>
        <div class='benefits'>
            <i class="fas fa-user-graduate icon"></i> **Facilidade de Uso:** Interface intuitiva que permite que qualquer profissional utilize a ferramenta sem treinamento extenso.
        </div>
        <div class='benefits'>
            <i class="fas fa-sync-alt icon"></i> **Atualização Contínua:** Acesso a informações sempre atualizadas para decisões mais informadas.
        </div>
        <div class='benefits'>
            <i class="fas fa-lightbulb icon"></i> **Suporte à Tomada de Decisão:** Insights rápidos que capacitam os gestores a tomarem decisões baseadas em dados em tempo real.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- CHAMADA À AÇÃO ---
    st.write("\n")
    st.markdown(
        f"<h2 class='subheader'>Pronto para transformar sua maneira de acessar informações?</h2>",
        unsafe_allow_html=True
    )
    st.write("Experimente o Chat Med e veja a diferença na sua pesquisa e análise de dados!")

    # --- BOTÃO DE INSCRIÇÃO ---
    if st.button("✉️ INSCREVA-SE AGORA"):
        # Chama a função de cadastro que contém o modal
        nome, whatsapp, endereco = cadastrar_cliente()  # Modifique a função para retornar os valores

        # Verifica se os campos foram preenchidos
        if nome and whatsapp and endereco:
            # Se todos os campos foram preenchidos, exibe a mensagem de sucesso
            st.success("Cadastro feito com sucesso!!!")
        else:
            # Se algum campo estiver vazio, exibe uma mensagem de erro
            st.error("Por favor, preencha todos os campos antes de confirmar o cadastro.")
