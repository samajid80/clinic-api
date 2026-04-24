import os
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

def get_container():
    client = CosmosClient.from_connection_string(
        os.environ["COSMOS_CONNECTION_STRING"]
    )
    database = client.get_database_client(
        os.environ["COSMOS_DATABASE"]
    )
    container = database.get_container_client(
        os.environ["COSMOS_CONTAINER"]
    )
    return container