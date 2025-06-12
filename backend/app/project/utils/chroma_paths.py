from pathlib import Path
from django.conf import settings
import shutil

class ChromaPathManager:
    @staticmethod
    def get_project_vector_path(project_id):
        path = settings.CHROMA_ROOT / f"project_{project_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def delete_project_vectors(project_id):
        path = settings.CHROMA_ROOT / f"project_{project_id}"
        if path.exists():
            shutil.rmtree(path)