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
from forms.contact import cadastrar_cliente, agendar_reuniao 

import replicate
from langchain.llms import Replicate

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

    if "image" not in st.session_state:
        st.session_state.image = None
    
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

    is_in_registration = False
    is_in_scheduling = False


    # Função para verificar se a pergunta está relacionada a cadastro
    def is_health_question(prompt):
        keywords = ["cadastrar", "inscrição", "quero me cadastrar", "gostaria de me registrar",
                    "desejo me cadastrar", "quero fazer o cadastro", "quero me registrar", "quero me increver",
                    "desejo me registrar", "desejo me inscrever","eu quero me cadastrar", "eu desejo me cadastrar",
                    "eu desejo me registrar", "eu desejo me inscrever", "eu quero me registrar", "eu desejo me registrar",
                    "eu quero me inscrever"]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

    #Função que analisa desejo de agendar uma reunião
    def is_schedule_meeting_question(prompt):
        keywords = [
            "agendar reunião", "quero agendar uma reunião", "gostaria de agendar uma reunião",
            "desejo agendar uma reunião", "quero marcar uma reunião", "gostaria de marcar uma reunião",
            "desejo marcar uma reunião", "posso agendar uma reunião", "posso marcar uma reunião",
            "Eu gostaria de agendar uma reuniao", "eu quero agendar", "eu quero agendar uma reunião,",
            "quero reunião"
        ]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

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

    st.markdown(
        """
        <style>
        .highlight-creme {
            background: linear-gradient(90deg, #f5f5dc, gold);  /* Gradiente do creme para dourado */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .highlight-dourado {
            background: linear-gradient(90deg, gold, #f5f5dc);  /* Gradiente do dourado para creme */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Título da página
    st.markdown(
        f"<h1 class='title'>Estude com o <span class='highlight-creme'>DOUTOR</span> <span class='highlight-dourado'>MED</span></h1>",
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
    img_path = "./src/img/perfil-doutor.png
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
            "role": "assistant", "content": '🌟 Bem-vindo ao Doutor Med! Seu analista de dados médicos.'}]

    # Dicionário de ícones
    icons = {
        "assistant": "./src/img/perfil-doutor.png",  # Ícone padrão do assistente
        "user": "./src/img/perfil-usuario.png"            # Ícone padrão do usuário
    }
    
    # Caminho para a imagem padrão
    default_avatar_path = "./src/img/perfil-usuario.png"
    
     # Exibição das mensagens
    for message in st.session_state.messages:
        if message["role"] == "user":
            # Verifica se a imagem do usuário existe
            avatar_image = st.session_state.image if "image" in st.session_state and st.session_state.image else default_avatar_path
        else:
            avatar_image = icons["assistant"]  # Ícone padrão do assistente
    
        with st.chat_message(message["role"], avatar=avatar_image):
            st.write(message["content"])


    def clear_chat_history():
        st.session_state.messages = [{
            "role": "assistant", "content": '🌟 Bem-vindo ao Doutor Med! Seu analista de dados médicos.'}]


    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history, key='limpar_conversa')

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

        if is_health_question(prompt_str):
            cadastrar_cliente()


        if is_schedule_meeting_question(prompt_str):
            agendar_reuniao()

        for event in replicate.stream(
                "meta/meta-llama-3.1-405b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 1,
                    "prompt": prompt_str,
                    "temperature": 0.1,
                    "system_prompt": system_prompt,
                    "length_penalty": 1,
                    "max_new_tokens": 8000,
                },
        ):
            yield str(event)


    def get_avatar_image():
        """Retorna a imagem do usuário ou a imagem padrão se não houver imagem cadastrada."""
        if st.session_state.image is not None:
            return st.session_state.image  # Retorna a imagem cadastrada
        else:
            return default_avatar_path  # Retorna a imagem padrão
    
    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
    
        # Chama a função para obter a imagem correta
        avatar_image = get_avatar_image()
    
        with st.chat_message("user", avatar=avatar_image):
            st.write(prompt)
    
    # Generate a new response if last message is not from assistant
    if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-doutor.png"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)


