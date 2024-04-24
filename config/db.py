from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

mongo_client = AsyncIOMotorClient('mongodb+srv://beatnow33:Monlau2021!@beatnow.v1mxd4q.mongodb.net/?retryWrites=true&w=majority&appName=BeatNow')
db = mongo_client['BeatNow']
users_collection = db['Users']
post_collection = db['Posts']
interactions_collection = db['Interactions']


async def get_database() -> Database:
    return mongo_client['BeatNow']
