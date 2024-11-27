import streamlit as st
from fastapi import FastAPI, HTTPException
import asyncio
import httpx
import pandas as pd
import time
from fastapi import FastAPI, HTTPException
from configuracao import ASAAS_API_KEY, BASE_URL  # Importando da configuração


app = FastAPI()


async def fetch_customers():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{BASE_URL}/customers',
            headers={'access_token': ASAAS_API_KEY}
        )
        response.raise_for_status()  # Levanta um erro se a resposta não for bem-sucedida
        return response.json()["data"]  # Retorna apenas os dados dos clientes


async def show_list_customers():
    st.title("Sistema Flash Pagamentos")
    st.write("Carregando lista de clientes...")

    my_bar = st.progress(0)  # Cria uma barra de carregamento
    for percent_complete in range(100):
        my_bar.progress(percent_complete + 1)  # Atualiza a barra de carregamento
        await asyncio.sleep(0.025)  # Aguarda 50ms para simular o tempo de carregamento

    try:
        # Executa a função assíncrona para buscar clientes
        clientes = await fetch_customers()

        if clientes:
            # Cria um DataFrame para organizar os dados
            df = pd.DataFrame(clientes)
            # Seleciona e renomeia as colunas para melhor visualização
            df = df[['id', 'name', 'email', 'cpfCnpj', 'phone']]  # Adapte conforme os campos da API
            df.columns = ['ID', 'Nome', 'E-mail', 'CPF/CNPJ', 'WhatsApp']
            st.write(df)
        else:
            st.write("Nenhum cliente encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")

if __name__ == "__app__":
    show_list_customers()
