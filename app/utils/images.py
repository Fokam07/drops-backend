# app/utils/images.py

def get_image_url(image_path: str | None) -> str | None:
    """
    Convertit un chemin local ou un lien externe en URL exploitable.
    - Corrige tous les doublons uploads/
    - Supprime les slashes en trop
    - Gère les URL externes
    """

    if not image_path:
        return None

    # URL externe → ne pas toucher
    if image_path.startswith(("http://", "https://")):
        return image_path

    # Normalisation
    image_path = image_path.replace("\\", "/").strip()

    # Supprimer les "/" au début
    image_path = image_path.lstrip("/")

    # Extraire la vraie partie à partir de "uploads/"
    if "uploads/" in image_path:
        image_path = image_path.split("uploads/", 1)[1]

    # Toujours commencer par uploads/
    image_path = "uploads/" + image_path

    # Nettoyer doublons
    while "uploads/uploads/" in image_path:
        image_path = image_path.replace("uploads/uploads/", "uploads/")

    while "//" in image_path:
        image_path = image_path.replace("//", "/")

    return f"http://localhost:8000/{image_path}"
