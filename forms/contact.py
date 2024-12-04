import streamlit as st
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import pandas as pd
import os
from PIL import Image
import stripe
from typing import Optional
from datetime import datetime
import asyncio
from key_config import API_KEY_STRIPE, URL_BASE, STRIPE_WEBHOOK_SECRET
from config_handler import add_client_to_config
from decouple import config


WEBHOOK_URL = config("WEBHOOK_URL")

app = FastAPI()


# Modelo de Cliente
class Cliente(BaseModel):
    name: str  # Nome do cliente
    email: EmailStr  # Validação do e-mail
    cpf_cnpj: str  # CPF ou CNPJ
    whatsapp: Optional[str] = None  # WhatsApp é opcional
    endereco: str
    cep: str  # O CEP deve ser uma string para incluir zeros à esquerda
    bairro: str
    cidade: str
    role: str
    username: str  # Adicionando o atributo 'username'
    password: str  # Adicionando o atributo 'password'

class ClienteResponse(BaseModel):
    id: str
    name: str
    email: str
    cpf_cnpj: str
    whatsapp: Optional[str]  # WhatsApp é opcional na resposta
    endereco: str
    cep: str
    bairro: str
    cidade: str
    role: str
    username: str  # Incluindo o atributo 'username' na resposta
    password: str  # Incluindo o atributo 'password' na resposta

async def create_customer(cliente: Cliente):
    try:
        # Verifique se os campos obrigatórios não estão vazios
        if not all([cliente.name, cliente.email, cliente.cpf_cnpj, cliente.endereco,
                    cliente.cep, cliente.bairro, cliente.cidade, cliente.role, cliente.username, cliente.password]):
            raise ValueError("Todos os campos são obrigatórios.")

        # Criação do cliente no Stripe
        customer = stripe.Customer.create(
            name=cliente.name,  # O campo 'name' é aceito pela API do Stripe
            email=cliente.email,
            metadata={
                "cpf_cnpj": cliente.cpf_cnpj,
                "whatsapp": cliente.whatsapp,
                "endereco": cliente.endereco,
                "cep": cliente.cep,
                "bairro": cliente.bairro,
                "cidade": cliente.cidade,
                "role": cliente.role,
                "username": cliente.username,  # Adicionando o 'username' aos metadados
                "password": cliente.password  # Adicionando o 'password' aos metadados
            }
        )

        # Verifique se o campo 'name' está na resposta do Stripe
        if 'name' not in customer:
            raise ValueError("O campo 'name' não foi retornado na resposta do Stripe.")

        return ClienteResponse(
            id=customer['id'],
            name=customer['name'],  # Certifique-se de que 'name' está correto
            email=customer['email'],
            cpf_cnpj=cliente.cpf_cnpj,
            whatsapp=cliente.whatsapp,
            endereco=cliente.endereco,
            cep=cliente.cep,
            bairro=cliente.bairro,
            cidade=cliente.cidade,
            role=cliente.role,
            username=cliente.username,  # Incluindo o 'username' na resposta
            password=cliente.password,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/customers", response_model=ClienteResponse)
async def api_create_customer(cliente: Cliente):
    return await create_customer(cliente)


def save_profile_image(uploaded_file, email):
    if uploaded_file is None:
        return None

    directory = "src/img/cliente"
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_extension = os.path.splitext(uploaded_file.name)[1]
    file_path = os.path.join(directory, f"{email}{file_extension}")

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


async def handle_create_customer(cliente):
    resultado = None  # Inicializa resultado com None
    try:
        resultado = await create_customer(cliente)  # Aguarda a conclusão da tarefa
        st.success(f"Cliente {resultado.name} criado com sucesso!")

        # Limpa os campos do formulário
        for key in st.session_state.keys():
            st.session_state[key] = ""  # Reseta todos os campos do session_state

    except Exception as e:
        # Verifica se resultado foi definido antes de usá-lo
        if resultado is not None:
            st.info(f'Parabéns {resultado.name} acesso seu: {resultado.email} que acabei de enviar a confirmação de seu cadastro'
                     f' ,em alguns segundos vou enviar o link de pagamento para seu acesso ao sistema.')
        else:
            st.error("Ocorreu um erro ao criar o cliente. Por favor, tente novamente.")
            # Você pode também registrar o erro para depuração
            st.error(f"Erro: {str(e)}")


@st.dialog("cadastro")
def cadastrar_cliente():
    st.title("sistema flash pagamentos")

    # seção para criar um novo cliente
    st.header("criar novo cliente")

    # inicializa os campos no session_state se não existirem
    if 'name' not in st.session_state:
        st.session_state.name = ""
    if 'documento' not in st.session_state:
        st.session_state.documento = ""
    if 'email' not in st.session_state:
        st.session_state.email = ""
    if 'whatsapp' not in st.session_state:
        st.session_state.whatsapp = ""
    if 'endereco' not in st.session_state:
        st.session_state.endereco = ""
    if 'cep' not in st.session_state:
        st.session_state.cep = ""
    if 'bairro' not in st.session_state:
        st.session_state.bairro = ""
    if 'cidade' not in st.session_state:
        st.session_state.cidade = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'password' not in st.session_state:
        st.session_state.password = ""
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'image' not in st.session_state:
        st.session_state.image = None  # inicializa como None

    # formulário para cadastro de cliente
    with st.form(key='form_cliente'):
        # cria colunas para organizar os campos
        col1, col2 = st.columns(2)  # colunas para name e whatsapp/email
        col3, col4 = st.columns(2)  # colunas para endereço e bairro/cep

        # coleta de dados do cliente
        with col1:
            name = st.text_input("nome:", value=st.session_state.name)
            documento = st.text_input("cpf/cnpj", value=st.session_state.documento)
        with col2:
            email = st.text_input("e-mail", value=st.session_state.email)
            whatsapp = st.text_input(label="whatsapp", placeholder='exemplo: 31900001111', value=st.session_state.whatsapp)

        with col3:
            endereco = st.text_input("endereço", value=st.session_state.get("endereco", ""))
            bairro = st.text_input("bairro", value=st.session_state.get("bairro", ""))
            password = st.text_input("digite uma senha:", type="password", value=st.session_state.get("password", ""))
            uploaded_file = st.file_uploader("escolha uma imagem de perfil", type=["jpg", "jpeg", "png"])

            if uploaded_file is not None:
                st.session_state.image = uploaded_file  # armazena o arquivo de imagem no session_state

                # salva a imagem com o nome de usuário
                username = st.session_state.username  # certifique-se de que o username está previamente definido
                if username:
                    directory = "./src/img/cliente"
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    # salva a imagem no formato desejado
                    image_path = os.path.join(directory, f"{username}.png")  # ou .jpg, conforme necessário
                    image = Image.open(uploaded_file)  # Corrigido de 'image' para 'Image'
                    image.save(image_path)

                    st.success(f"imagem salva em: {image_path}")
                else:
                    st.warning("por favor, insira um nome de usuário antes de fazer o upload da imagem.")

        with col4:
            cep = st.text_input("cep", value=st.session_state.cep)
            cidade = st.text_input("cidade:", value=st.session_state.cidade)
            role = st.selectbox(
                "tipo de usuário",
                options=["cliente", "parceiro", "admin"],
                index=0 if not st.session_state.role else ["cliente", "parceiro", "admin"].index(st.session_state.role))
            username = st.text_input("usuário:", value=st.session_state.username)

        # botão para enviar os dados do formulário
        submit_button = st.form_submit_button("criar cliente!")

        if submit_button:
            # atualiza o session_state após a coleta dos dados
            st.session_state.name = name
            st.session_state.documento = documento
            st.session_state.email = email
            st.session_state.whatsapp = whatsapp
            st.session_state.endereco = endereco
            st.session_state.cep = cep
            st.session_state.bairro = bairro
            st.session_state.cidade = cidade
            st.session_state.role = role
            st.session_state.username = username
            st.session_state.password = password

            cliente = cliente(
                name=st.session_state.name,
                email=st.session_state.email,
                cpf_cnpj=st.session_state.documento,
                whatsapp=st.session_state.whatsapp,
                endereco=st.session_state.endereco,
                cep=st.session_state.cep,
                bairro=st.session_state.bairro,
                cidade=st.session_state.cidade,
                role=st.session_state.role,
                username=st.session_state.username,
                password=st.session_state.password,
                image=st.session_state.image,
            )

            # adiciona o cliente ao arquivo config.yaml
            client_data = {
                'name': st.session_state.name,
                'email': st.session_state.email,
                'cpf_cnpj': st.session_state.documento,
                'whatsapp': st.session_state.whatsapp,
                'endereco': st.session_state.endereco,
                'cep': st.session_state.cep,
                'bairro': st.session_state.bairro,
                'cidade': st.session_state.cidade,
                'role': st.session_state.role,
                'username': st.session_state.username,
                'password': st.session_state.password,
            }

            # validação dos dados do cliente
            try:
                # verifique se todos os campos obrigatórios estão preenchidos
                for field in ['name', 'email', 'cpf_cnpj', 'whatsapp', 'endereco', 'cep', 'bairro', 'cidade', 'username', 'password']:
                    if not client_data[field]:
                        raise ValueError(f"o campo {field} é obrigatório.")

                # adicione outras validações específicas, como verificação do formato do email e cpf/cnpj
                # (implementação das funções de validação não mostrada aqui)

                add_client_to_config(client_data)  # chama a função para adicionar os dados ao config.yaml

            except ValueError as ve:
                st.error(str(ve))  # exibe um erro de validação ao usuário
            except Exception as e:
                st.error("ocorreu um erro ao adicionar o cliente. por favor, tente novamente.")  # tratamento genérico de erro

            # verifica se a imagem foi carregada
            if st.session_state.image is not None:
                diretorio = 'src/img/cliente'
                if not os.path.exists(diretorio):
                    os.makedirs(diretorio)

                # inclui o diretório no caminho da imagem
                image_path = os.path.join(diretorio, f'{cliente.username}.png')  # use a extensão correta
                with open(image_path, "wb") as f:
                    f.write(st.session_state.image.getbuffer())  # escreve o conteúdo do arquivo
            else:
                st.warning("nenhuma imagem foi carregada.")

        try:
            asyncio.create_task(handle_create_customer(cliente))
        except Exception as e:
            # aqui você pode registrar o erro em um log ou apenas ignorá-lo
            pass  # não exibe o erro na tela


def is_valid_email(email):
    # Basic regex pattern for email validation
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_pattern, email) is not None


def is_valid_email(email):
    # Basic regex pattern for email validation
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_pattern, email) is not None


def contact_form():
    with st.form("contact_form"):
        name = st.text_input("Nome e Sobrenome")
        email = st.text_input("E-mail")
        message = st.text_area("Envie uma mensagem")
        submit_button = st.form_submit_button("ENVIAR")

    if submit_button:
        if not WEBHOOK_URL:
            st.error("Email service is not set up. Please try again later.", icon="📧")
            st.stop()

        if not name:
            st.error("Please provide your name.", icon="🧑")
            st.stop()

        if not email:
            st.error("Please provide your email address.", icon="📨")
            st.stop()

        if not is_valid_email(email):
            st.error("Please provide a valid email address.", icon="📧")
            st.stop()

        if not message:
            st.error("Please provide a message.", icon="💬")
            st.stop()

        # Prepare the data payload and send it to the specified webhook URL
        data = {"email": email, "name": name, "message": message}
        response = requests.post(WEBHOOK_URL, json=data)

        if response.status_code == 200:
            st.success("A sua mensagem foi enviada com sucesso! 🎉", icon="🚀")
        else:
            st.error("Desculpe-me, parece que houve um problema no envio da sua mensagem", icon="😨")


@st.dialog("Agendamento")
def agendar_reuniao():
    global is_in_scheduling
    is_in_scheduling = True

    st.title('Agendar Reunião')
    with st.form("cadastro_reuniao"):
        name = st.text_input("Nome:")
        whatsapp = st.text_input("WhatsApp:")
        email = st.text_input("E-mail:")
        endereco = st.text_input("Endereço:")
        message = st.text_area("Mensagem:")
        submit_button = st.form_submit_button("ENVIAR")

    if submit_button:
        if not WEBHOOK_URL:
            st.error("O Webhook deverá ser configurado", icon="📧")
            st.stop()

        if not name:
            st.error("Qual o seu nome?", icon="🧑")
            st.stop()

        if not whatsapp:
            st.error("Digite seu WhatsApp.", icon="📨")
            st.stop()

        if not email:
            st.error("Digite seu e-mail.", icon="📨")
            st.stop()

        if not endereco:
            st.error("Digite seu endereço com o nome do bairro.", icon="📨")
            st.stop()

        if not message:
            st.error("Deixe sua mensagem.", icon="💬")
            st.stop()

        # Prepare the data payload and send it to the specified webhook URL
        data = {"Nome": name, "WhatsApp": whatsapp, "Email": email, "Endereço": endereco, "Mensagem": message}
        response = requests.post(WEBHOOK_URL, json=data)

        if response.status_code == 200:
            st.success("A sua mensagem foi enviada, o Alan entrará em contato! 🎉", icon="🚀")
        else:
            st.error("Desculpe-me, parece que houve um problema no envio da sua mensagem", icon="😨")
