from fastapi import FastAPI, Request, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import stripe
from views.key_config import  URL_BASE, STRIPE_WEBHOOK_SECRET, API_KEY_STRIPE
from decouple import config
from core.configs import settings


# Configurações do Stripe
stripe.api_key = API_KEY_STRIPE

app = FastAPI()


# Modelo de exemplo
class Subscription(Base):
    __tablename__ = "assinaturas"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    subscription_id = Column(String)

Base.metadata.create_all(bind=engine)


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    # Verificação da assinatura
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Processar o evento
    if event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        # Salvar a nova assinatura no banco de dados
        db = SessionLocal()
        new_subscription = Subscription(
            status=subscription["status"],
            subscription_id=subscription["id"]
        )
        db.add(new_subscription)
        db.commit()
        db.close()

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice["subscription"]

        # Atualizar o status da assinatura no banco de dados
        db = SessionLocal()
        subscription = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
        if subscription:
            subscription.status = "active"  # ou outro status que você queira definir
            db.commit()
        db.close()

    return {"status": "success"}


# Função para buscar assinaturas pagas
def get_paid_subscriptions():
    db = SessionLocal()
    subscriptions = db.query(Subscription).filter(Subscription.status == "active").all()
    db.close()
    return subscriptions

def showAssinatura():
    # Interface do Streamlit
    st.title("Lista de Assinaturas Pagas")

    # Buscar assinaturas pagas
    paid_subscriptions = get_paid_subscriptions()

    if paid_subscriptions:
        # Exibir as assinaturas em uma tabela
        st.write("Assinaturas Pagas:")
        for subscription in paid_subscriptions:
            st.write(f"ID da Assinatura: {subscription.subscription_id}, Status: {subscription.status}")
    else:
        st.write("Nenhuma assinatura paga encontrada.")
