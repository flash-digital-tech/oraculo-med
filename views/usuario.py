import streamlit as st
import asyncio
import pandas as pd
from sqlalchemy.future import select
from models.usuario_model import UsuarioModel, TipoUsuario
from core.configs import settings
from core.database import get_session


# Função para criar um novo usuário
async def create_user(username, name, email, password, whatsapp, user_type):
    async for session in get_session():  # Use async for para obter a sessão
        new_user = UsuarioModel(
            username=username,
            name=name,
            email=email,
            password=password,
            whatsapp=whatsapp,
            type_user=user_type
        )
        session.add(new_user)
        await session.commit()
        return new_user


# Função para listar usuários
async def list_users():
    async for session in get_session():  # Use async for para obter a sessão
        result = await session.execute(select(UsuarioModel))
        users = result.scalars().all()
        return users


# Streamlit Interface
def showUsuario():
    st.title("Sistema Flash Pagamentos - Cadastro de Usuários")

    # Seção para criar um novo usuário
    st.header("Criar Novo Usuário")

    # Inicializa os campos no session_state se não existirem
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'name' not in st.session_state:
        st.session_state.name = ""
    if 'email' not in st.session_state:
        st.session_state.email = ""
    if 'whatsapp' not in st.session_state:
        st.session_state.whatsapp = ""
    if 'password' not in st.session_state:
        st.session_state.password = ""
    if 'user_type' not in st.session_state:
        st.session_state.user_type = TipoUsuario.Cliente  # Valor padrão

    # Formulário para cadastro de usuário
    with st.form(key='form_usuario'):
        st.session_state.username = st.text_input("Nome de Usuário:", value=st.session_state.username)
        st.session_state.name = st.text_input("Nome Completo:", value=st.session_state.name)
        st.session_state.email = st.text_input("E-mail:", value=st.session_state.email)
        st.session_state.whatsapp = st.text_input("WhatsApp:", value=st.session_state.whatsapp)
        st.session_state.password = st.text_input("Senha:", type="password", value=st.session_state.password)

        # Seleção do tipo de usuário
        st.session_state.user_type = st.selectbox("Tipo de Usuário:", list(TipoUsuario ))

        # Botão para enviar os dados do formulário
        submit_button = st.form_submit_button("CRIAR USUÁRIO!")

        if submit_button:
            try:
                user = await create_user(
                    username=st.session_state.username,
                    name=st.session_state.name,
                    email=st.session_state.email,
                    password=st.session_state.password,
                    whatsapp=st.session_state.whatsapp,
                    user_type=st.session_state.user_type
                )
                st.success(f"Usuário {user.name} criado com sucesso!")

                # Limpa os campos do formulário
                st.session_state.username = ""
                st.session_state.name = ""
                st.session_state.email = ""
                st.session_state.whatsapp = ""
                st.session_state.password = ""

            except Exception as e:
                st.error(f"Erro ao criar usuário: {e}")

    # Seção para listar usuários
    st.header("Listar Usuários")
    if st.button("Carregar Lista de Usuários"):
        try:
            users = await list_users()
            if users:
                data = []
                for user in users:
                    data.append({
                        'ID': user.id,
                        'Nome de Usuário': user.username,
                        'Nome Completo': user.name,
                        'E-mail': user.email,
                        'WhatsApp': user.whatsapp,
                        'Tipo de Usuário': user.type_user.value,
                    })
                df = pd.DataFrame(data)
                st.dataframe(df)  # Exibe a tabela de usuários no Streamlit
            else:
                st.warning("Nenhum usuário encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {e}")
