import streamlit as st
from fastapi import FastAPI, HTTPException
import asyncio
import httpx
from pydantic import BaseModel
from configuracao import ASAAS_API_KEY, BASE_URL  # Importando da configuração
from acesso_autent import login




app = FastAPI()


# Modelo de Cliente
class Cliente(BaseModel):
    id: str
    nome: str
    email: str
    cpf_cnpj: str
    whatsapp: str
    endereco: str
    cep: str
    bairro: str


async def fetch_customer(customer_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{BASE_URL}/customers/{customer_id}',
            headers={'access_token': ASAAS_API_KEY}
        )
        response.raise_for_status()
        return response.json()


async def delete_customer(customer_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f'{BASE_URL}/customers/{customer_id}',
            headers={'access_token': ASAAS_API_KEY}
        )
        response.raise_for_status()
        return response.json()


async def show_delete_customer():
    st.title("Sistema Flash Pagamentos")
    st.header("Excluir Cliente")

    customer_id = st.text_input("ID do Cliente")

    if st.button("Carregar Cliente"):
        if not customer_id:
            st.error("Por favor, insira um ID de cliente válido.")
            return

        try:
            cliente = await fetch_customer(customer_id)
            if 'nome' not in cliente or 'email' not in cliente:
                st.error("Dados do cliente não encontrados. Verifique o ID.")
                return

            # Exibindo os dados do cliente que será excluído
            st.write("Nome:", cliente['nome'])
            st.write("E-mail:", cliente['email'])
            st.write("CPF/CNPJ:", cliente['cpfCnpj'])
            st.write("WhatsApp:", cliente['whatsapp'])
            st.write("Endereço:", cliente['endereco'])
            st.write("CEP:", cliente['cep'])
            st.write("Bairro:", cliente['bairro'])

            if st.button("Confirmar Exclusão"):
                resultado = await delete_customer(customer_id)
                st.success(f"Cliente {resultado['nome']} excluído com sucesso!")

        except httpx.HTTPStatusError as e:
            st.error(f"Ocorreu um erro ao buscar o cliente: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            st.error(f"Erro ao carregar cliente: {e}")

if __name__ == "__main__":
    login()
