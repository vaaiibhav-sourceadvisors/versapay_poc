import os, httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import parse_qs

app = FastAPI()

# 1. FIXED CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

GATEWAY_URL = "https://versapay.transactiongateway.com/api/transact.php"
QUERY_URL = "https://versapay.transactiongateway.com/api/query.php"
# !!! ROTATE YOUR KEY IN THE PORTAL - YOU POSTED IT PUBLICLY !!!
API_KEY = "" 

class VaultRequest(BaseModel):
    token: str
    first_name: str
    last_name: str

class PaymentRequest(BaseModel):
    vault_id: str
    amount: str

# STEP 1: VAULTING
@app.post("/api/vault")
async def vault_customer(req: VaultRequest):
    payload = {
        "security_key": API_KEY,
        "customer_vault": "add_customer",
        "payment_token": req.token,
        "firstname": req.first_name,
        "lastname": req.last_name,
        "test_mode": "1"
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(GATEWAY_URL, data=payload)
        data = {k: v[0] for k, v in parse_qs(res.text).items()}
        return data

# STEP 2: CHARGING
@app.post("/api/pay")
async def charge_customer(req: PaymentRequest):
    payload = {
        "security_key": API_KEY,
        "type": "sale",
        "amount": req.amount,
        "customer_vault_id": req.vault_id,
        "test_mode": "1"
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(GATEWAY_URL, data=payload)
        data = {k: v[0] for k, v in parse_qs(res.text).items()}
        return data

# STEP 3: CHECKING (Query API)
@app.get("/api/check/{trans_id}")
async def check_transaction(trans_id: str):
    # The Query API lets you see if a payment is 'complete' or 'failed'
    payload = {
        "security_key": API_KEY,
        "transaction_id": trans_id
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(QUERY_URL, data=payload)
        # Query API returns XML, but for a simple "is it there?" test, 
        # we can just check if the ID is in the response text.
        return {"raw_status": res.text}