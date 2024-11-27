import streamlit as st
import streamlit_authenticator as stauth

# Definindo as credenciais dos usuários
credentials = {
    'eduarda': {'name': 'Eduarda', 'password': 'admin123', 'email': 'eduarda@example.com'},
    'regiane': {'name': 'Regiane', 'password': 'parceiro456', 'email': 'regiane@example.com'},
    'jony': {'name': 'Jony', 'password': 'cliente789', 'email': 'jony@example.com'}
}

# Configuração do authenticator
authenticator = stauth.Authenticate(
    names=[user['name'] for user in credentials.values()],
    usernames=list(credentials.keys()),
    passwords=[user['password'] for user in credentials.values()],
    emails=[user['email'] for user in credentials.values()],
    cookie_name='some_cookie_name',
    key='some_key',
    cookie_expiry_days=30
)

# Formulário de login
st.title("Formulário de Login")
with st.form(key='login_form'):
    username_input = st.text_input("Nome de usuário")
    password_input = st.text_input("Senha", type='password')
    email_input = st.text_input("E-mail do usuário")
    submit_button = st.form_submit_button("Login")

# Verificando se o botão de envio foi pressionado
if submit_button:
    name, authentication_status = authenticator.login(username_input, 'main', password=password_input)
    if authentication_status:
        st.success(f'Login bem-sucedido para {name}!')
    else:
        st.error('Falha no login.')

# Testando acessos
# Este bloco não é necessário no contexto de um formulário de login, mas se você quiser,
# pode incluir um loop para testar todas as credenciais definidas.
for username in credentials.keys():
    password = credentials[username]['password']
    result = simulate_login(username, password)  # Passando strings para a função
    st.write(result)

# Testando com dados incorretos
incorrect_username = 'wrong_user'
incorrect_password = 'wrong_password'
result = simulate_login(incorrect_username, incorrect_password)
st.write(result)
