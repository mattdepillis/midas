import os
from dotenv import load_dotenv # type: ignore
from coinbase import jwt_generator

load_dotenv()

def get_coinbase_holdings():
    api_key = os.getenv("COINBASE_API_KEY")
    key_path = os.getenv("COINBASE_API_SECRET_PATH")

    with open(key_path, 'r') as f:
        api_secret = f.read()

    print(api_key, api_secret)

    request_method = "GET"
    request_path = "/v2/accounts"

    jwt_uri = jwt_generator.format_jwt_uri(request_method, request_path)
    jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, api_secret)
    print(f"export JWT={jwt_token}")


    # accounts = client.get_accounts()
    # portfolio = []

    # for account in accounts:
    #     balance = float(account['balance'])
    #     if balance > 0:
    #         portfolio.append({
    #             "currency": account["currency"],
    #             "balance": balance
    #         })

    # return portfolio
