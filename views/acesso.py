import streamlit as st
from forms.contact import criar_cliente  # Certifique-se de que a função criar_cliente está importada corretamente
import json
from streamlit_lottie import st_lottie

# Streamlit Interface
def cadastrar_cliente():
    st.title("Cadastro Flash")

    # Seção para criar um novo cliente
    st.header("Cadastrar Cliente")

    # Inicializa os campos no session_state se não existirem
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
    if 'usuario' not in st.session_state:
        st.session_state.usuario = ""
    if 'senha' not in st.session_state:
        st.session_state.senha = ""

    # Formulário para cadastro de cliente
    with st.form(key='form_cliente'):
        # Cria colunas para organizar os campos
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        # Coleta de dados do cliente
        with col1:
            st.session_state.name = st.text_input("Nome:", value=st.session_state.name)
            st.session_state.documento = st.text_input("CPF/CNPJ", value=st.session_state.documento)
        with col2:
            st.session_state.email = st.text_input("E-mail", value=st.session_state.email)
            st.session_state.whatsapp = st.text_input(label="WhatsApp", placeholder='Exemplo: 31900001111', value=st.session_state.whatsapp)

        with col3:
            st.session_state.endereco = st.text_input("Endereço", value=st.session_state.endereco)
            st.session_state.bairro = st.text_input("Bairro", value=st.session_state.bairro)
        with col4:
            st.session_state.cep = st.text_input("CEP", value=st.session_state.cep)
            st.session_state.cidade = st.text_input("Cidade:", value=st.session_state.cidade)

        st.session_state.usuario = st.text_input("Usuário:", value=st.session_state.usuario)
        st.session_state.senha = st.text_input("Senha:", type="password", value=st.session_state.senha)

        submit_button = st.form_submit_button("CRIAR CLIENTE!")

        if submit_button:
            # Verifica se os campos obrigatórios estão preenchidos
            if not st.session_state.name or not st.session_state.email:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                cliente = Cliente(
                    name=st.session_state.name,
                    email=st.session_state.email,
                    cpf_cnpj=st.session_state.documento,
                    whatsapp=st.session_state.whatsapp,
                    endereco=st.session_state.endereco,
                    cep=st.session_state.cep,
                    bairro=st.session_state.bairro,
                    cidade=st.session_state.cidade,
                    usuario=st.session_state.usuario,
                    senha=st.session_state.senha
                )

                try:
                    print("Tentando criar cliente:", cliente.name)  # Log para depuração
                    criar_cliente(cliente)
                    st.success(f"Cliente {cliente.name} criado com sucesso!")

                    # Limpa os campos do formulário
                    for key in st.session_state.keys():
                        st.session_state[key] = ""

                except Exception as e:
                    st.error(f"Erro ao criar cliente: {e}")

# Chamada da função cadastrar_cliente()
def showhome():
    # --- HERO SECTION ---
    col1, col2, col3 = st.columns(3, gap="small", vertical_alignment="center")

    with col1:
        st.image("./src/img/oraculo-logo.png", width=230)

    with col2:
        with st.popover("SOLICITAR MEU ACESSO!"):
            st.write("Sistema super avançado de coleta de dados com inteligência artificial.")
            if st.button("✉SOLICITAR ACESSO"):
                cadastrar_cliente()  # Chamada da função cadastrar_cliente()

    with col3:
        def load_lottie_local(filepath):
            with open(filepath) as f:
                return json.load(f)
        lottie_animation = load_lottie_local("src/animations/animation_home.json")
        st_lottie(lottie_animation, speed=1, width=400, height=400, key="animation_home")


    # --- EXPERIENCE & QUALIFICATIONS ---
    st.write("\n")
    st.subheader("Experience & Qualifications", anchor=False)
    st.write(
        """
        - 7 Years experience extracting actionable insights from data
        - Strong hands-on experience and knowledge in Python and Excel
        - Good understanding of statistical principles and their respective applications
        - Excellent team-player and displaying a strong sense of initiative on tasks
        """
    )

    # --- SKILLS ---
    st.write("\n")
    st.subheader("Hard Skills", anchor=False)
    st.write(
        """
        - Programming: Python (Scikit-learn, Pandas), SQL, VBA
        - Data Visualization: PowerBi, MS Excel, Plotly
        - Modeling: Logistic regression, linear regression, decision trees
        - Databases: Postgres, MongoDB, MySQL
        """
    )
