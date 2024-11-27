import asyncio

import streamlit as st
from transformers import AutoTokenizer
import base64
import pandas as pd
import io
from fastapi import FastAPI
import stripe
from util import carregar_arquivos
import os
import glob
from forms.contact import cadastrar_cliente


import replicate
from langchain.llms import Replicate


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from key_config import API_KEY_STRIPE, URL_BASE
from decouple import config


app = FastAPI()


# --- Verifica se o token da API está nos segredos ---
if 'REPLICATE_API_TOKEN':
    replicate_api = config('REPLICATE_API_TOKEN')
else:
    # Se a chave não está nos segredos, define um valor padrão ou continua sem o token
    replicate_api = None

# Essa parte será executada se você precisar do token em algum lugar do seu código
if replicate_api is None:
    # Se você quiser fazer algo específico quando não há token, você pode gerenciar isso aqui
    # Por exemplo, configurar uma lógica padrão ou deixar o aplicativo continuar sem mostrar nenhuma mensagem:
    st.warning('Um token de API é necessário para determinados recursos.', icon='⚠️')


#######################################################################################################################

def show_chat_demo():
    # Carregar apenas a aba "Dados" do arquivo Excel
    #df_dados = pd.read_excel('./conhecimento/medicos_dados_e_links.xlsx', sheet_name='Dados')

    # Converter o DataFrame para um arquivo de texto, por exemplo, CSV
    #df_dados.to_csv('./conhecimento/medicos_dados_e_links.txt', sep=' ', index=False, header=True)

    # Se preferir usar tabulações como delimitador, substitua sep=' ' por sep='\t'
    # df_dados.to_csv('./conhecimento/CatalogoMed_Sudeste_Dados.txt', sep='\t', index=False, header=True)

    # Especifica o caminho para o arquivo .txt
    #caminho_arquivo = './conhecimento/medicos_dados_e_links.txt'

    # Abre o arquivo no modo de leitura ('r')
    #with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        # Lê todo o conteúdo do arquivo e armazena na variável conteudo
        #info = arquivo.read()

    # Exibe o conteúdo do arquivo
    #df_txt = info

    def ler_arquivos_txt(pasta):
        """
        Lê todos os arquivos .txt na pasta especificada e retorna uma lista com o conteúdo de cada arquivo.

        Args:
            pasta (str): O caminho da pasta onde os arquivos .txt estão localizados.

        Returns:
            list: Uma lista contendo o conteúdo de cada arquivo .txt.
        """
        conteudos = []  # Lista para armazenar o conteúdo dos arquivos

        # Cria o caminho para buscar arquivos .txt na pasta especificada
        caminho_arquivos = os.path.join(pasta, '*.txt')

        # Usa glob para encontrar todos os arquivos .txt na pasta
        arquivos_txt = glob.glob(caminho_arquivos)

        # Lê o conteúdo de cada arquivo .txt encontrado
        for arquivo in arquivos_txt:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()  # Lê o conteúdo do arquivo
                conteudos.append(conteudo)  # Adiciona o conteúdo à lista

        return conteudos  # Retorna a lista de conteúdos

    # Exemplo de uso da função
    pasta_conhecimento = './conhecimento'  # Caminho da pasta onde os arquivos .txt estão localizados
    conteudos_txt = ler_arquivos_txt(pasta_conhecimento)

    processar_docs = carregar_arquivos()

    # Atualizando o system_prompt
    system_prompt = f'''
    "Você é o Doutor Med (DM), um profissional com formação acadêmica em Farmácia (Bacharelado, Mestrado em Ciências Farmacêuticas e Doutorado em Farmacologia) e especialização em análise de dados médicos. Sua função é ler e analisar os dados fornecidos: {conteudos_txt}, oferecendo informações precisas e detalhadas.

    1. **Formato de Resposta:** Apresente suas análises preferencialmente em formato de planilha. Se o usuário solicitar, você pode fornecer as informações em texto normal.

    2. **Foco nas Respostas:** Responda apenas ao que foi perguntado, mantendo as respostas concisas e objetivas. Evite informações adicionais desnecessárias.

    3. **Informações sobre Suplementos e Remédios:** Forneça informações pertinentes se o usuário solicitar sobre suplementos ou medicamentos.

    4. **Suporte ao Programador:** Se o usuário desejar entrar em contato com o programador responsável, forneça o link do WhatsApp: [https://wa.me/5531996011180](https://wa.me/5531996011180). Não ofereça este link a menos que solicitado.

    5. **Cadastro e Agendamento:**
       - Se o usuário estiver com o status de cadastro {is_in_registration} ou agendamento {is_in_scheduling}, informe que não enviará mais informações até que finalize o cadastro. Use uma resposta padrão que diga: "Aguardo a finalização do seu cadastro para continuar."

    6. **Opção de Cadastro e Agendamento:**
       - Se o usuário enviar {is_health_question} ou {is_schedule_meeting_question}, responda que está aguardando o preenchimento completo do formulário. 
       - Mantenha a mesma resposta enquanto ele não finalizar o cadastro.
       - Se o status do cadastro estiver {is_in_scheduling} ou {is_in_registration} mantenha a mesma resposta enquanto
       ele não finalizar o cadastro.
       
    7. **Link de Assinatura:**
       - Se o usuário quiser fazer a assinatura para o sistema de análise Oráculo Med envie o link:
       https://buy.stripe.com/test_7sIdUDaYNcCEalidQR
       
    8. **Programador:**
       - Se o usuário quiser conversar com o programador envie o link do WhatsApp:
       https://wa.me/+5531996011180

    9. **Agenda Reuniões:** Você agenda apenas reuniões para usuários interessados no ORÁCULO MED ou que desejam saber mais sobre o sistema.

    10. **Orientação durante o Cadastro:** Lembre-se de orientar o usuário a completar o formulário antes de qualquer nova interação.
    
    '''


    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-doutor.png", "user": "./src/img/perfil-usuario.png"}


    st.markdown(
        """
        <h1 style='text-align: center;'>Doctor Med</h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Rounded corners */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to convert image to base64
    def img_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    st.sidebar.markdown("---")

    # Load and display sidebar image with glowing effect
    img_path = "./src/img/perfil-doutor.png"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )


    # Inicializar o modelo da Replicate
    llm = Replicate(
        model="meta/meta-llama-3.1-405b-instruct",
        api_token=replicate_api
    )

    # Store LLM-generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{
            "role": "assistant", "content": 'Sou reconhecido como o Doutor Med, fui programado para demonstrar a você '
            'o poder e a velocidade que analiso seus dados.'}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])


    def clear_chat_history():
        st.session_state.messages = [{
            "role": "assistant", "content": 'Sou reconhecido como o Doutor Med, fui programado para demonstrar a você '
            'o poder e a velocidade que analiso seus dados.'}]


    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history, key='limpar_conversa')
    st.sidebar.caption(
        'Built by [Snowflake](https://snowflake.com/) to demonstrate [Snowflake Arctic](https://www.snowflake.com/blog/arctic-open-and-efficient-foundation-language-models-snowflake). App hosted on [Streamlit Community Cloud](https://streamlit.io/cloud). Model hosted by [Replicate](https://replicate.com/snowflake/snowflake-arctic-instruct).')
    st.sidebar.caption(
        'Build your own app powered by Arctic and [enter to win](https://arctic-streamlit-hackathon.devpost.com/) $10k in prizes.')
    st.sidebar.markdown("Desenvolvido por [WILLIAM EUSTÁQUIO](https://www.instagram.com/flashdigital.tech/)")

    @st.cache_resource(show_spinner=False)
    def get_tokenizer():
        """Get a tokenizer to make sure we're not sending too much text
        text to the Model. Eventually we will replace this with ArcticTokenizer
        """
        return AutoTokenizer.from_pretrained("huggyllama/llama-7b")


    def get_num_tokens(prompt):
        """Get the number of tokens in a given prompt"""
        tokenizer = get_tokenizer()
        tokens = tokenizer.tokenize(prompt)
        return len(tokens)


    def check_safety(disable=False) -> bool:
        if disable:
            return True

        deployment = get_llamaguard_deployment()
        conversation_history = st.session_state.messages
        user_question = conversation_history[-1]  # pegar a última mensagem do usuário

        prediction = deployment.predictions.create(
            input=template)
        prediction.wait()
        output = prediction.output

        if output is not None and "unsafe" in output:
            return False
        else:
            return True

    # Function for generating Snowflake Arctic response
    def generate_arctic_response():

        prompt = []
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
            else:
                prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")

        prompt.append("<|im_start|>assistant")
        prompt.append("")
        prompt_str = "\n".join(prompt)


        if get_num_tokens(prompt_str) >= 500:  # padrão 3072
            st.write("Você atingiu o limite de tokens. Para continuar, clique no link abaixo para ter 1 mês de análise.")

            if st.button("Clique aqui para solicitar seu acesso"):
                st.markdown(f"[ADQUIRIR ACESSO](https://buy.stripe.com/test_fZeg2L7MBcCE9heeUY)")

            st.stop()  # Interrompe a execução do script aqui


        else:
            for event in replicate.stream(
                    "meta/meta-llama-3.1-405b-instruct",
                    input={
                        "top_k": 50,
                        "top_p": 0.01,
                        "prompt": prompt_str,
                        "temperature": 0.1,
                        "system_prompt": system_prompt,
                        "length_penalty": 1,
                        "max_new_tokens": 2048,
                    },
            ):
                yield str(event)


    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api, key='prompt_user'):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Verifica se o usuário tem uma imagem de perfil
        if st.session_state.image is not None:
            # Se o usuário tiver uma imagem, usa a imagem carregada
            avatar_path = st.session_state.image
        else:
            # Caso contrário, usa uma imagem padrão
            avatar_path = "./src/img/perfil-usuario.png"  # Caminho da imagem padrão

        with st.chat_message("user", avatar=avatar_path):
            st.write(prompt)


    # Gera uma nova resposta se a última mensagem não for do assistente
    try:
        # Verifica se a lista de mensagens não está vazia
        if st.session_state.messages and "role" in st.session_state.messages[-1]:
            if st.session_state.messages[-1]["role"] != "assistant":
                with st.chat_message("assistant", avatar="./src/img/perfil-doutor.png"):
                    response = generate_arctic_response()
                    full_response = st.write_stream(response)
                message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(message)
        else:
            st.warning("Não há mensagens disponíveis ou a estrutura da última mensagem está incorreta.")
    except IndexError:
        st.warning("Ocorreu um erro ao acessar a última mensagem: lista vazia.")
    except KeyError as ke:
        st.warning(f"Ocorreu um erro: {str(ke)}. A estrutura da mensagem pode estar incorreta.")



