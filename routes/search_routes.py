from model.post_shemas import SearchPost
from typing import List
from model.user_shemas import NewUser, UserInDB, UserSearch
from config.security import  get_current_user, get_user_id
from config.db import users_collection, db
from fastapi import HTTPException, Depends, APIRouter
from Levenshtein import distance as levenshtein_distance

# Iniciar router
router = APIRouter()

@router.post("/")
async def search_posts(current_user: NewUser = Depends(get_current_user), params: SearchPost = Depends()):
    user_id = await get_user_id(current_user.username)
    query = {"user_id": {"$ne": user_id}}  # Excluir posts del usuario actual

    or_conditions = []
    for field, value in params.dict(exclude={'none': True}).items():  # Excluir campos con None
        if value is not None and value != '':  # Comprobar adicionalmente por valores vacíos
            if field in ['genre', 'bpm', 'mood', 'key', 'title', 'description']:
                or_conditions.append({field: {"$regex": value, "$options": "i"}})
            elif field in ['instruments', 'tags']:
                or_conditions.append({field: {"$all": value}})

    if or_conditions:
        query["$or"] = or_conditions

    try:
        post_collection = db.post_collection
        cursor = post_collection.find(query)
        results = [document async for document in cursor]  # Asynchronous list comprehension
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    return results

@router.post("/user/", response_model=List[UserInDB])
async def search_user(params: UserSearch = Depends(), current_user: UserInDB = Depends(get_current_user)):
    query = {
        "$and": [
            {"username": {"$ne": current_user.username}},  # Excluye el usuario actual de la búsqueda.
            {"$or": [
                {"username": {"$regex": f"^{params.username}", "$options": "i"}},
                {"full_name": {"$regex": f"^{params.username}", "$options": "i"}} if params.username else {}
            ]}
        ]
    }

    try:
        cursor = users_collection.find(query).sort("username")
        results = await cursor.to_list(length=None)
        listusers = [UserInDB(**doc) for doc in results if "username" in doc]
        return sort_users_by_similarity(params.username, listusers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


# Función para ordenar usuarios por similitud de nombre de usuario y nombre completo
def sort_users_by_similarity(target: str, users: List[UserInDB]) -> List[UserInDB]:
    def similarity_score(user: UserInDB) -> tuple:
        # Calcula la similitud entre el target y el username
        username_similarity = levenshtein_distance(target.lower(), user.username.lower())
        # Calcula la similitud entre el target y el full_name
        fullname_similarity = levenshtein_distance(target.lower(), (user.full_name or "").lower())
        # Retorna una tupla que prioriza primero la similitud de username
        return (username_similarity, fullname_similarity)
    
    # Ordena los usuarios primero por username_similarity y luego por fullname_similarity
    users_sorted = sorted(users, key=similarity_score)
    return users_sorted