import streamlit as st
from transformers import AutoTokenizer
import base64
import pandas as pd
import io
from PIL import Image
from fastapi import FastAPI
import stripe
from util import carregar_arquivos
import os
import glob
from forms.contact import cadastrar_cliente, agendar_reuniao

import replicate
from langchain.llms import Replicate

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config



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




################################################# ENVIO DE E-MAIL ####################################################
############################################# PARA CONFIRMAÇÃO DE DADOS ##############################################

# Função para enviar o e-mail
def enviar_email(destinatario, assunto, corpo):
    remetente = "mensagem@flashdigital.tech"  # Insira seu endereço de e-mail
    senha = "sua_senha"  # Insira sua senha de e-mail

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('mail.flashdigital.tech', 587)
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        st.success("E-mail enviado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")

    # Enviando o e-mail ao pressionar o botão de confirmação
    if st.button("DADOS CONFIRMADO"):
        # Obter os dados salvos em st.session_state
        nome = st.session_state.user_data["name"]
        whatsapp = st.session_state.user_data["whatsapp"]
        email = st.session_state.user_data["email"]

        # Construindo o corpo do e-mail
        corpo_email = f"""
        Olá {nome},

        Segue a confirmação dos dados:
        - Nome: {nome}
        - WhatsApp: {whatsapp}
        - E-mail: {email}
        - Agendamento : {dias} e {turnos}

        Obrigado pela confirmação!
        """

        # Enviando o e-mail
        enviar_email(email, "Confirmação de dados", corpo_email)


#######################################################################################################################

def show_chat_med():

    if 'image' not in st.session_state:
        st.session_state.image = None  # Inicializa como None

    # Verifica se o usuário acabou de se cadastrar e inicializa o chat
    if 'first_message' not in st.session_state:
        st.session_state.first_message = True

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

    system_prompt = f'''
    "Você é o Doutor Med (DM), um profissional com formação acadêmica em Farmácia (Bacharelado, Mestrado em Ciências Farmacêuticas e Doutorado em Farmacologia) e especialização em análise de dados médicos. Sua função é ler e analisar os dados fornecidos: {conteudos_txt}, oferecendo informações precisas e detalhadas.

    1. **Formato de Resposta:** Apresente suas análises preferencialmente em formato de planilha. Se o usuário solicitar, você pode fornecer as informações em texto normal.

    2. **Foco nas Respostas:** Responda apenas ao que foi perguntado, mantendo as respostas concisas e objetivas. Evite informações adicionais desnecessárias.

    3. **Informações sobre Suplementos e Remédios:** Forneça informações pertinentes se o usuário solicitar sobre suplementos ou medicamentos.

    4. **Suporte ao Programador:** Se o usuário desejar entrar em contato com o programador responsável, forneça o link do WhatsApp: [https://wa.me/5531996011180](https://wa.me/5531996011180). Não ofereça este link a menos que solicitado.

    5. **Cadastro e Agendamento:**
       - Se o usuário estiver com o status de cadastro {is_in_registration} ou agendamento {is_in_scheduling}, 
       informe que não enviará mais informações até que finalize o cadastro. Use uma resposta padrão que diga: 
       "Aguardo a finalização do seu cadastro para continuar."

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

    # Função para gerar o PDF
    def create_pdf(messages):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for message in messages:
            role = message["role"].capitalize()
            content = message["content"]
            pdf.cell(200, 10, txt=f"{role}: {content}", ln=True)

        return pdf.output(dest='S').encode('latin1')


    # Função para gerar o Excel
    def create_excel(messages):
        df = pd.DataFrame(messages)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()


    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-doutor.png", "user": "./src/img/perfil-usuario.png"}


    # Replicate Credentials
    with st.sidebar:
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


        # Load and display sidebar image with glowing effect
        img_path = "./src/img/perfil-doutor.png"
        img_base64 = img_to_base64(img_path)
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )

        st.sidebar.markdown("---")

    # Inicializar o modelo da Replicate
    llm = Replicate(
        model="meta/meta-llama-3.1-405b-instruct",
        api_token=replicate_api
    )

    # Store LLM-generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{
            "role": "assistant", "content": 'Sou reconhecido como o Doutor Med, fui programado para te responder com uma '
                                            'velocidade extraordinária e passar informações sobre médicos, especialidades,'
                                            'consultas e orientações sobre suplementos e saúde.'}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])


    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": 'Sou reconhecido como o Doutor Med, fui programado para te responder com uma '
                                            'velocidade extraordinária e passar informações sobre médicos, especialidades,'
                                            'consultas e orientações sobre suplementos e saúde.'}]


    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history)
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
        if is_in_registration or is_in_scheduling:
            return "Por favor, complete o formulário de cadastro antes de continuar."

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


        elif get_num_tokens(prompt_str) >= 8000:  # padrão3072
            st.error(
                "Poxa, você já atingiu seu limite de demostração, mas pode ficar tranquilo. Clique no botão abaixo para "
                "pedir seu acesso.")
            st.button('PEDIR ACESSO', on_click=clear_chat_history, key="clear_chat_history")
            excel_bytes = create_excel(st.session_state.messages)
            pdf_bytes = create_pdf(st.session_state.messages)
            formato_arquivo = st.selectbox("Escolha como deseja baixar sua conversa:", ["PDF", "Excel"])
            if formato_arquivo == "PDF":
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name="conversa.pdf",
                    mime="application/pdf",
                )
            else:
                st.download_button(
                    label="Baixar Excel",
                    data=excel_bytes,
                    file_name="conversa.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.stop()


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


    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Verifica se a imagem do usuário está no session state
        if st.session_state.image is not None:
            # Converte a imagem do session state para um formato que o Streamlit pode usar
            image = Image.open(st.session_state.image)
            image_path = f"./src/img/cliente/{st.session_state.image.name}"
            image.save(image_path)  # Salva a imagem para uso posterior
            with st.chat_message("user", avatar=image_path):
                st.write(prompt)
        else:
            with st.chat_message("user", avatar="./src/img/perfil-usuario.png"):
                st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-doutor.png"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



