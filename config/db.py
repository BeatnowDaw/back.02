from pymongo import MongoClient

mongo_client = MongoClient('mongodb+srv://beatnow33:Monlau2021!@beatnow.v1mxd4q.mongodb.net/?retryWrites=true&w=majority&appName=BeatNow')
db = mongo_client['BeatNow']
usuarios_collection = db['Users']