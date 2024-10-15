from fireblocks_sdk import FireblocksSDK, VAULT_ACCOUNT, PagedVaultAccountsRequestFilters
import json
from decouple import config

api_secret = open('./config/fireblocks_secret.key', 'r').read()
api_key = config('FIREBLOCK_SANDBOX_API_KEY')
api_url = config('FIREBLOCK_SANDBOX_API_URL')

fireblocks = FireblocksSDK(api_secret, api_key, api_base_url=api_url)


## Create wallet using FireBlock
def Create_Wallet(vault_name: str, asset: str):

    vault_id = fireblocks.create_vault_account(name=vault_name)["id"]

    wallet = fireblocks.create_vault_asset(
        vault_account_id = vault_id,
        asset_id = asset
    )

    return wallet