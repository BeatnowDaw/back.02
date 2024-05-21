
from bson import ObjectId
from config.db import interactions_collection, post_collection
# Change Stream to watch the interactions_collection
async def watch_changes():
    async with interactions_collection.watch() as stream:
        async for change in stream:
            if change["operationType"] == "insert":
                document = change["fullDocument"]
                post_id = document["post_id"]
                if "like_date" in document:
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"likes": 1}}
                    )
                if "saved_date" in document:
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"saves": 1}}
                    )
            elif change["operationType"] == "update":
                document_key = change["documentKey"]
                update_description = change["updateDescription"]
                interaction_id = document_key["_id"]

                # Recuperar el documento completo para obtener post_id
                interaction = await interactions_collection.find_one({"_id": interaction_id})
                post_id = interaction["post_id"]

                if "like_date" in update_description.get("updatedFields", {}):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"likes": 1}}
                    )
                if "like_date" in update_description.get("removedFields", []):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"likes": -1}}
                    )
                if "saved_date" in update_description.get("updatedFields", {}):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"saves": 1}}
                    )
                if "saved_date" in update_description.get("removedFields", []):
                    await post_collection.update_one(
                        {"_id": ObjectId(post_id)},
                        {"$inc": {"saves": -1}}
                    )