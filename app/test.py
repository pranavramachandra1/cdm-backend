from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.server_api import ServerApi

import os

if __name__ == "__main__":
    mongo_password = os.getenv("MONGO_DB_PASSWORD")
    mongo_username = os.getenv("MONGO_DB_USERNAME")

    # grab mongo client & db
    mongo_url = MongoClient(
        f"mongodb+srv://{mongo_username}:{mongo_password}@cluster0.3qeyv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
        server_api=ServerApi("1"),
    )
    db = mongo_url.todov2

    # breakpoint()
