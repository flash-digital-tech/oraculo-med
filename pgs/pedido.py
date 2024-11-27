import streamlit as st
import os
from transformers import AutoTokenizer
import base64
from forms.contact import cadastro_pedido
import asyncio

import replicate
from langchain.llms import Replicate

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


async def showPedido():

    # --- Verifica se o token da API está nos segredos ---
    if 'REPLICATE_API_TOKEN' in st.secrets:
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
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
            email = st.session_state.user_data["email"]
            whatsapp = st.session_state.user_data["whatsapp"]
            endereco = st.session_state.user_data["endereco"]

            # Construindo o corpo do e-mail
            corpo_email = f"""
            Olá {nome},
    
            Segue a confirmação dos dados:
            - Nome: {nome}
            - E-mail: {email}
            - WhatsApp: {whatsapp}
            - Endereço: {endereco}
    
            Obrigado pela confirmação!
            """

            # Enviando o e-mail
            enviar_email(email, "Confirmação de dados", corpo_email)


    #######################################################################################################################

    system_prompt = f'''
    Você é o Chef Mantiqueira especialista em vendas online e conhece todos os tipos de carne e cortes, você também é formado como chef de cozinha e sabe instruir com excelência como preparar pratos e temperos. Faça a saudação ao cliente antes de iniciar o atendimento e se apresente.
    Sua respostas serão no máximo 300 tokens completando a resposta sem ter cortes. Seja curto e claro nas respostas sem prolongar. Somente na apresentação das opções de tipos de carne e tipos de corte que você poderá ultrapassar os 300 tokens.
    Você seguirá o passo a passo para atendimento aos clientes:
    
    Todos os pedidos não poderá ser feito se o cliente escolher menos de 1kg.
    Se tiver produtos com nomes iguais pergunte ao cliente qual ele deseja, por exemplo:
    Fanta PET
    Fanta de 2L PET
    Lata de Coca-Cola de 350ml
    Lata de Fanta de 350ml
    
    1. Saber o que o cliente deseja.
    2. Apresentar os produtos que ele deseja, sempre em tópicos numerados e em ordem alfabética.
    3. Se ele escolher um tipo de carne apresente todos os tipos de cortes que tem da carne que ele escolheu.
    4. Após ele escolher o produto informe o preço do produto e pergunte quanto ele deseja comprar.
    5. Se o cliente escolher bebida apresente o valor da unidade e pergunte quantos unidaes deseja comprar.
    6. Apresente o total que ele deseja comprar e sempre pergunte se deseja mais alguma coisa.
    7. Sempre pergunte ao cliente se deseja adicionar mais algum produto ao pedido.
    8. Se ele disser que sim pergunte qual seria.
    9. Apresente as opções deste segundo produto ao cliente para adicionar ao pedido.
    10. Independente de qual produto ele escolher sempre informe o valor deste segundo e sempre pergunte quanto ele deseja comprar antes de fazer a soma total.
    11. Se ele disser que não tem interesse em adicionar mais produto ao pedido, informe o total do pedido e diga que deverá pegar alguns dados bem rápido para finalizar o pedido.
    12. Após o cliente escolher todos os produtos do pedido você iniciará o cadastro dele aqui: 
    
    
    13. Assim que apresentar o pedido com todos os dados do tópico anterior pergunte se ele tem alguma observação a fazer.
    14. Se ele responder que sim, pergunte qual seria a observação e anote no campo "OBSERVAÇÃO" do pedido.
    15. Se ele disser que não tem nenhuma observação a fazer cite o nome dele e informe que o pagamento é feito pela chave do PIX: 31983352900 e que assim que o sistema confirmar o pagamento será preparado o pedido e entregue.
    26. Se ele disser "ok", "tudo bem", "muito obrigado" ou qualquer frase positiva finalize a conversa agradecendo por ter dado a preferência ao Frigorífico Mantiqueira e que qualquer coisa estaremos à disposição.
    
    A FAC será uma referencia para suas respostas:
    
    - Sim. Fazemos entrega num raio de 5km do nosso açougue.
    - A taxa de entrega é de R$6,00 dentro do raio de 5km.
    - Recebemos pagamento via PIX + a taxa de entrega R$6,00 através da chave: 31983352900.
    - Clique no link para ver a nossa localização exata: [localização](https://maps.app.goo.gl/YLJxnEchmZpPv4qb7).
    - Temos: BOI, PORCO, FRANGO, LINGUIÇA, PEIXE, KITS.
    - Para a carne de boi temos:
      *Grelha (Contra filé, Alcatra, Chã de dentro, Maçã de Peito, Fraldão)
      *Bife (Contra filé, Alcatra, Chã de dentro, chã de fora, Miolo de pá, Patinho)
      *Cozinhar (Miolo de Acém, Acém, Músculo Dianteiro, Músculo Traseiro, Pá, Maçã de Peito)
      *Moída (Miolo de Acém, Acém, Músculo Dianteiro, Músculo Traseiro, Pá, Maçã de Peito)
      *Estrogonofe (Contra filé, Alcatra, Chã de dentro, chã de fora, Miolo de pá, Patinho)
      *Peças inteiras (Contra filé, Alcatra completa, Alcatra Aparada, Chã de dentro, chã de fora, patinho, miolo de acém, maçã de peito, pá completa)
      *Picanhas
      *Filé Mignon (com cordão, sem cordão)
      *Rabada
      *Dobradinha
      *Coração
      *Mocotó
      *Fígado
      *Ossobuco
      *Cupim
      *Fraldinha
      *Fraldão Tradicional
      *Fraldão Grill
      *Costela para cozinhar
      *Costela para Assar
      *Costela inteira.
    - As formas são: BIFE, GRELHA, ESPETO, CUBOS, STROGONOFE, MOÍDO, INTEIRO.
    - O preço da Fanta PET de 200ml é R$ 2,99.
    - A Coca-Cola PET de 200ml custa R$ 2,99.
    - A Fanta de 2L PET custa R$ 9,99.
    - O refrigerante retornável de 2L custa R$ 7,50.
    - A Coca Zero de 600ml custa R$ 6,99.
    - O Suco Del Vale de 290ml custa R$ 4,99.
    - A lata de Coca-Cola de 350ml custa R$ 4,99.
    - A lata de Fanta de 350ml custa R$ 4,99.
    - O Powerade custa R$ 4,99.
    - A água sem gás de 500ml custa R$ 3,00.
    - A água com gás de 500ml custa R$ 3,00.
    - O preço da Bisteca é R$ 16,99.
    - O Tomahawk suíno custa R$ 21,99.
    - A Pazinha PC custa R$ 15,99.
    - A Pazinha custa R$ 16,99.
    - A Pazinha com pele e osso custa R$ 14,99.
    - A Pazinha com pele sem osso custa R$ 15,99.
    - A Pazinha defumada custa R$ 29,99.
    - O Pernil PC custa R$ 16,99.
    - O Pernil custa R$ 18,99.
    - O Pernil com osso sem pele custa R$ 18,99.
    - O Pernil com pele e osso custa R$ 18,99.
    - O Pernil recheado custa R$ 21,99.
    - O Lombo PC custa R$ 18,99.
    - O Lombo custa R$ 19,99.
    - O Lombo com pele custa R$ 18,99.
    - O Lombo defumado custa R$ 29,99.
    - O Lombo recheado custa R$ 23,99.
    - A Copa lombo custa R$ 21,99.
    - O Lombinho custa R$ 21,99.
    - A Picanha suína custa R$ 26,99.
    - A Costelinha com lombo custa R$ 20,99.
    - A Costelinha aparada custa R$ 24,99.
    - A Costelinha com lombo e pele custa R$ 16,99.
    - A Costelinha aparada com pele custa R$ 21,99.
    - A Costelinha defumada custa R$ 34,99.
    - A Costelinha suadali custa R$ 24,99.
    - O Pezinho/Orelha custa R$ 9,99.
    - O Rabinho custa R$ 21,99.
    - O Toucinho comum custa R$ 9,99.
    - O Toucinho picado custa R$ 16,99.
    - O Toucinho papada custa R$ 18,99.
    - O Toucinho especial custa R$ 21,99.
    - A Banha custa R$ 11,99.
    - A Suã comum custa R$ 4,99.
    - A Suã especial custa R$ 16,99.
    - O Coração e língua custa R$ 11,99.
    - O preço da alcatra em peça é R$ 32,99 por kg.
    - O contra filé em peça custa R$ 34,99 por kg.
    - O chã dentro em peça custa R$ 28,99 por kg.
    - O patinho em peça custa R$ 27,99 por kg.
    - O chá fora em peça custa R$ 29,99 por kg.
    - A pa completa em peça custa R$ 24,99 por kg.
    - O miolo de acém em peça custa R$ 24,99 por kg.
    - A maca peito em peça custa R$ 24,99 por kg.
    - A picanha premiata custa R$ 79,99 por kg.
    - O filé mignon com cordão custa R$ 49,99 por kg.
    - A picanha pul dia a dia custa R$ 49,99 por kg.
    - A alcatra em kg custa R$ 36,99.
    - O contra filé em kg custa R$ 37,99.
    - O chá dentro em kg custa R$ 33,99.
    - O patinho em kg custa R$ 33,99.
    - O chá fora em kg custa R$ 33,99.
    - O lagarto custa R$ 33,99 por kg.
    - O lagarto recheado custa R$ 34,99 por kg.
    - A maminha custa R$ 37,99 por kg.
    - O miolo de alcatra custa R$ 39,99 por kg.
    - O preço da carne de sol de 2ª é R$ 34,99 por kg.
    - O lagartinho custa R$ 33,99 por kg.
    - O garrão custa R$ 29,99 por kg.
    - O acém custa R$ 24,99 por kg.
    - O miolo de acém custa R$ 29,99 por kg.
    - A pa/paleta custa R$ 29,99 por kg.
    - A maca peito custa R$ 29,99 por kg.
    - A capa de filé custa R$ 29,99 por kg.
    - O músculo dianteiro custa R$ 29,99 por kg.
    - A fraldinha custa R$ 34,99 por kg.
    - O músculo traseiro custa R$ 29,99 por kg.
    - O fraldão custa R$ 39,99 por kg.
    - O cupim custa R$ 35,99 por kg.
    - O costelão de boi inteiro custa R$ 24,99 por kg.
    - A costela de boi custa R$ 19,99 por kg.
    - A costela gaúcha custa R$ 19,99 por kg.
    - O costelão especial custa R$ 21,99 por kg.
    - A costela recheada custa R$ 34,99 por kg.
    - A costela desossada custa R$ 49,99 por kg.
    - O acém com osso custa R$ 24,99 por kg.
    - A maçã de peito com osso custa R$ 24,99 por kg.
    - O dianteiro de boi custa R$ 19,99 por kg.
    - A chãzinha custa R$ 29,99 por kg.
    - A carne de indústria custa R$ 19,99 por kg.
    - A moída promoção custa R$ 19,99 por kg.
    - O acém bovino promocional custa R$ 19,99 por kg.
    - O coração de boi custa R$ 9,99 por kg.
    - O fígado de boi (bife) custa R$ 14,99 por kg.
    - O fígado de boi (pedaço) custa R$ 14,99 por kg.
    - A língua de boi custa R$ 16,99 por kg.
    - A língua de boi recheada custa R$ 24,99 por kg.
    - A dobradinha custa R$ 15,99 por kg.
    - A dobradinha colméia custa R$ 24,99 por kg.
    - A rabada custa R$ 35,99 por kg.
    - O mocotó custa R$ 10,99 por kg.
    - Os ossos/muxibas custam R$ 4,99 por kg.
    - O coração de porco custa R$ 9,99 por kg.
    - A língua de porco custa R$ 9,99 por kg.
    - O dorso custa R$ 4,49 por kg.
    - O pezinho de frango custa R$ 7,99 por kg.
    - O frango resfriado custa R$ 10,99 por kg.
    - A coxa e sobrecoxa custam R$ 9,99 por kg.
    - O peito de frango custa R$ 14,99 por kg.
    - A asa de frango custa R$ 14,99 por kg.
    - O joelho de porco custa R$ 29,99 por kg.
    - O bacon custa R$ 29,99 por kg.
    - O baconil custa R$ 24,99 por kg.
    - O bacon papada custa R$ 24,99 por kg.
    - A salsicha Pif Paf custa R$ 10,99 por kg.
    - A salsicha Perdigão custa R$ 11,99 por kg.
    - O salsichão custa R$ 13,99 por kg.
    - O salaminho custa R$ 16,99 por kg.
    - A calabresa custa R$ 22,99 por kg.
    - A calabresinha custa R$ 22,99 por kg.
    - A linguiça toscana FM custa R$ 14,99 por kg.
    - A linguiça defumada custa R$ 19,99 por kg.
    - A linguiça de frango gomo custa R$ 21,99 por kg.
    - A linguiça de frango fina custa R$ 24,99 por kg.
    - A linguiça de frango com bacon e milho custa R$ 19,99 por kg.
    - A linguiça pernil fina custa R$ 24,99 por kg.
    - A linguiça ciacarne custa R$ 22,99 por kg.
    - A linguiça saudali custa R$ 17,99 por kg.
    - A linguiça de costela custa R$ 24,99 por kg.
    - A linguiça defumada coquetel custa R$ 29,99 por kg.
    - A linguiça lombo defumada custa R$ 29,99 por kg.
    - A linguiça caseira custa R$ 19,99 por kg.
    - A linguiça pernil com ervas custa R$ 19,99 por kg.
    - A linguiça pernil com bacon custa R$ 19,99 por kg.
    - A linguiça pernil com biquinho custa R$ 19,99 por kg.
    - A linguiça pernil com malagueta custa R$ 19,99 por kg.
    - A linguiça pernil com alho poró custa R$ 19,99 por kg.
    - A linguiça pernil com jiló custa R$ 19,99 por kg.
    - A linguiça pernil com azeitona custa R$ 19,99 por kg.
    - A linguiça caipira custa R$ 24,99 por kg.
    - O lombo defumado custa R$ 29,99 por kg.
    - A orelha defumada custa R$ 14,99 por kg.
    - O pezinho defumado custa R$ 14,99 por kg.
    - O rabinho defumado custa R$ 29,99 por kg.
    - A pazinha defumada custa R$ 29,99 por kg.
    - A costelinha defumada custa R$ 34,99 por kg.
    - A papada defumada custa R$ 24,99 por kg.
    - A pele suína defumada custa R$ 14,99 por kg.
    - A almôndega de boi (patinho) custa R$ 34,99 por kg.
    - A almôndega de boi (miolo de acém) custa R$ 29,99 por kg.
    - A almôndega de frango custa R$ 29,99 por kg.
    - A almôndega de porco custa R$ 29,99 por kg.
    - O medalhão custa R$ 32,99 por kg.
    - O hambúrguer de frango custa R$ 29,99 por kg.
    - O hambúrguer de boi custa R$ 29,99 por kg.
    - O hambúrguer de patinho custa R$ 33,99 por kg.
    - O Pão de Alho Shamara custa R$ 9,99 por unidade.
    - O Pão de Alho Recheado do Zé do Espeto custa R$ 21,99 por unidade.
    - O Pão de Alho Recheado da Dona Beth custa R$ 21,99 por unidade.
    - O carvão de 3 kg custa R$ 14,99 por unidade.
    - O carvão de 10 kg custa R$ 39,99 por unidade.
    - O sal grosso custa R$ 2,99 por unidade.
    - O tempero em pote de 300g custa R$ 4,99 por unidade.
    - O molho de 150ml custa R$ 3,99 por unidade.
    - O torresmo pré-frito custa R$ 44,90 por kg.
    - O torresmo semi pronto D’Abadia custa R$ 10,99 por unidade.
    - O torresmo pré-pronto Santa Fé custa R$ 10,99 por unidade.
    - A banha de 900ml custa R$ 16,99 por unidade.
    Aqui estão todos os kits de churrasco disponíveis no Frigorífico Mantiqueira, com suas descrições e preços:
    - KIT CHURRASCO DIAMANTE R$ 229,99
       - 1 picanha Grill (aprox.: 1,3kg a 1,5kg)
       - 1 kg lombo
       - 1kg asa
       - 1kg linguiça gourmet
       - 1 carvão de 3kg
       - 1 pão de alho Zé do Espeto
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT CHURRASCO GOLD+ R$ 169,99
       - 1 picanha Grill (aprox.: 1kg)
       - 1 kg lombo/copa lombo
       - 1kg asa/coxinha da asa
       - 1kg linguiça gourmet
       - 1 carvão de 3kg
       - 1 pão de alho Zé do Espeto
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT CHURRASCO GOLD R$ 149,99
       - 1 picanha Grill (aprox.: 1kg)
       - 1 kg lombo/copa lombo
       - 1kg asa/coxinha da asa
       - 1kg linguiça gourmet
       - 1 carvão de 3kg
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT CHURRASCO PRATA+ R$ 149,99
       - 1kg Ancho ou Chorizo
       - 1 kg pernil/copa lombo
       - 1kg asa/coxinha da asa
       - 1kg linguiça gourmet
       - 1 carvão de 3kg
       - 1 pão de alho Zé do Espeto
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT CHURRASCO PRATA R$ 129,99
       - 1kg Ancho ou Chorizo
       - 1 kg pernil/copa lombo
       - 1kg asa/coxinha da asa
       - 1kg linguiça gourmet
       - 1 carvão de 3kg
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT BRONZE R$ 99,99
       - 1kg Chã de Dentro
       - 1kg de Pernil
       - 1kg de Asa
       - 1kg de Linguiça Toscana Mista
       - 1 carvão de 3kg
       - *Obs: Serve aproximadamente 10 pessoas*
    
    - KIT ECONOMIA R$ 109,99
       - 1kg Frango a Passarinho
       - 1kg carne para cozinhar
       - 1kg moída promocional
       - 1kg linguiça toscana mista
       - 1kg bife de pernil
       - 1kg bisteca
       - *Obs: Serve aproximadamente 10 pessoas
       
    Os modelos e preços de peixe:
    A Cavalinha custa R$ 10,99 por kg
    A Sardinha custa R$ 14,99 por kg
    O Filé de Merluza custa R$ 39,99 por kg
    O Cascudo custa R$ 17,99 por kg
    O Filé de Tilápia - R$ 49,99 por kg
    
    '''

    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-chat1.png", "user": "./src/img/cliente.png"}

    # Replicate Credentials
    with st.sidebar:
        st.markdown(
            """
            <h1 style='text-align: center;'>Chef Mantiqueira</h1>
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
        img_path = "./src/img/chef1.jpeg"
        img_base64 = img_to_base64(img_path)
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("---")
        st.info("Faça seu pedido com o Chef Mantiqueira , suas perguntas deverão ser somente sobre o Frigorífico Mantiqueira "
                "ou sobre qualquer tipo de assunto sobre carnes. Interaja com ele pedindo ajuda de como temperar, como "
                "preparar algum tipo de carne para churrasco ou como fazer algum tipo de comida. Lembre ele é o CHEF MANTIQUEIRA.")

        st.sidebar.markdown("---")

    # Inicializar o modelo da Replicate
    llm = Replicate(
        model="meta/meta-llama-3-70b-instruct",
        api_token=replicate_api
    )

    # Store LLM-generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": 'Olá!Sou o Chef Mantiqueira, digite abaixo oque você deseja comprar'
                                                                      ' hoje?'}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": 'Olá!Sou o Chef Mantiqueira, digite abaixo oque você deseja comprar'
                                                                      ' hoje?'}]

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

        if get_num_tokens(prompt_str) >= 3500:  # padrão3072
            if cadastro_pedido in system_prompt:
                @st.dialog("DADOS PARA PEDIDO")
                def show_contact_form():
                    cadastro_pedido()

        for event in replicate.stream(
                "meta/meta-llama-3-70b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 1,
                    "prompt": prompt_str,
                    "temperature": 0.1,
                    "system_prompt": system_prompt,
                    "length_penalty": 1,
                    "max_new_tokens": 3500,

                },
        ):
            yield str(event)

    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="./src/img/cliente.png"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil.png"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



