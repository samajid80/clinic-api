import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# DefaultAzureCredential automatically picks the right auth method:
#   - In Azure (App Service / Functions): uses Managed Identity
#   - On your local machine: uses your Azure CLI login (az login)
#   - Never needs a password or API key

VAULT_URL = os.environ.get(
    "KEY_VAULT_URL",
    "https://clinic-vault-yourname.vault.azure.net/"
)

def get_secret(secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value