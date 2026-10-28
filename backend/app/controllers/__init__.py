import os
import glob
import importlib

# Chaque controller doit exposer : ctrl = MonController(), avec ctrl.router
# étant un fastapi.APIRouter (voir AuthController : self.router = APIRouter(...)).
def register_all(app, url_prefix="/api"):
    folder = os.path.dirname(__file__)
    files = glob.glob(folder + "/*.py")

    for f in files:
        module_name = os.path.basename(f)[:-3]
        if module_name.startswith("_"):
            continue  # ignore __init__.py

        module = importlib.import_module(f"app.controllers.{module_name}")

        if hasattr(module, "ctrl"):
            # Le préfixe propre au controller (ex: "/auth") est déjà porté
            # par son APIRouter (voir AuthController : APIRouter(prefix="/auth", ...)).
            # url_prefix ("/api") s'ajoute par-dessus, sans le dupliquer ici.
            app.include_router(module.ctrl.router, prefix=url_prefix)
            print(f"[OK] Router '{module.ctrl.router.prefix}' enregistré sous {url_prefix}")