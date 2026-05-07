"""
TP1 - Exercice 1 : Structures de données Redis
Use Case : ShopFast - Gestion des produits, paniers et navigation
"""
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def store_product(r, product_id, product_data: dict):
    """
    Stocker un produit comme Hash Redis
    Clé : "product:{product_id}"
    Champs : name, price, category, stock
    
    >>> store_product(r, 1, {"name": "Samsung A54", "price": 65000, "category": "phones", "stock": 15})
    """
    # TODO: Implémenter avec HSET
    key = f"product:{product_id}"
    r.hset(key, mapping=product_data)


def get_product(r, product_id):
    """
    Récupérer un produit par son ID
    Retourner None si le produit n'existe pas
    """
    # TODO: Implémenter avec HGETALL
    key = f"product:{product_id}"
    data = r.hgetall(key)
    return data if data else None


def add_to_cart(r, user_id, product_id, quantity: int = 1):
    """
    Ajouter/incrémenter un produit dans le panier
    Clé : "cart:{user_id}"
    Champ : product_id → quantité
    """
    # TODO: Implémenter avec HINCRBY
    key = f"cart:{user_id}"
    r.hincrby(key, str(product_id), int(quantity))


def get_cart(r, user_id):
    """
    Récupérer tout le contenu du panier d'un utilisateur
    Retourner un dict {product_id: quantity}
    """
    # TODO
    key = f"cart:{user_id}"
    return r.hgetall(key)


def record_view(r, user_id, product_id, max_history: int = 10):
    """
    Enregistrer un produit vu par l'utilisateur
    Clé : "history:{user_id}" (List)
    Garder seulement les max_history derniers produits
    Astuce : LPUSH + LTRIM
    """
    # TODO
    key = f"history:{user_id}"
    r.lpush(key, str(product_id))
    r.ltrim(key, 0, max_history - 1)


def get_history(r, user_id):
    """Récupérer l'historique de navigation"""
    # TODO
    key = f"history:{user_id}"
    return r.lrange(key, 0, -1)


def add_product_to_category(r, category: str, product_id):
    """
    Associer un produit à une catégorie
    Clé : "category:{category}" (Set)
    """
    # TODO: Utiliser SADD
    key = f"category:{category}"
    r.sadd(key, str(product_id))


def get_products_in_categories(r, *categories):
    """
    Récupérer les produits appartenant à TOUTES les catégories données
    Ex: produits qui sont à la fois "electronics" ET "promo"
    Astuce : SINTER
    """
    # TODO
    keys = [f"category:{category}" for category in categories]
    if not keys:
        return set()
    return r.sinter(keys)


if __name__ == "__main__":
    # Test manuel
    r.flushdb()  # Nettoyer pour les tests
    
    # Stocker quelques produits
    store_product(r, 1, {"name": "Samsung A54", "price": "65000", "category": "phones", "stock": "15"})
    store_product(r, 2, {"name": "Laptop HP", "price": "120000", "category": "laptops", "stock": "8"})
    
    # Tester le panier
    add_to_cart(r, "user:42", 1, 2)
    add_to_cart(r, "user:42", 2, 1)
    print("Panier:", get_cart(r, "user:42"))
    
    # Tester l'historique
    for pid in [1, 2, 1, 3, 2]:
        record_view(r, "user:42", pid)
    print("Historique:", get_history(r, "user:42"))
