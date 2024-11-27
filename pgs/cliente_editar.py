import streamlit as st
import asyncio
import httpx
from pydantic import BaseModel
from configuracao import ASAAS_API_KEY, BASE_URL
from fastapi import FastAPI, HTTPException
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


async def update_customer(customer: Cliente):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f'{BASE_URL}/customers/{customer.id}',
            json=customer.dict(),
            headers={'access_token': ASAAS_API_KEY}
        )
        response.raise_for_status()
        return response.json()


async def show_edit_customer():
    st.title("Sistema Flash Pagamentos")
    st.header("Editar Cliente")

    customer_id = st.text_input("ID do Cliente")

    if st.button("Carregar Cliente"):
        if not customer_id:
            st.error("Por favor, insira um ID de cliente válido.")
            return

        try:
            cliente = await fetch_customer(customer_id)  # Usando await aqui
            if 'nome' not in cliente or 'email' not in cliente:
                st.error("Dados do cliente não encontrados. Verifique o ID.")
                return

            # Preenche os campos com os dados do cliente
            nome = st.text_input("Nome", value=cliente['nome'])
            email = st.text_input("E-mail", value=cliente['email'])
            cpf_cnpj = st.text_input("CPF/CNPJ", value=cliente['cpfCnpj'])
            whatsapp = st.text_input("WhatsApp", value=cliente['whatsapp'])
            endereco = st.text_input("Endereço", value=cliente['endereco'])
            cep = st.text_input("CEP", value=cliente['cep'])
            bairro = st.text_input("Bairro", value=cliente['bairro'])

            if st.button("Salvar Alterações"):
                updated_cliente = Cliente(
                    id=customer_id,
                    nome=nome,
                    email=email,
                    cpf_cnpj=cpf_cnpj,
                    whatsapp=whatsapp,
                    endereco=endereco,
                    cep=cep,
                    bairro=bairro
                )
                try:
                    resultado = await update_customer(updated_cliente)  # Usando await aqui
                    st.success(f"Cliente {resultado['nome']} atualizado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao atualizar cliente: {e}")

        except httpx.HTTPStatusError as e:
            st.error(f"Ocorreu um erro ao buscar o cliente: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            st.error(f"Erro ao carregar cliente: {e}")

# Chamada da função
if __name__ == "__main__":
    login()  # Esta linha também deve ser removida
