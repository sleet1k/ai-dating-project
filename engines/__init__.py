from .base import BotEngine
from .leomatch import LeomatchEngine
from .blur import BlurEngine
from .bibinto import BibintoEngine

ENGINE_REGISTRY = {
    "1": LeomatchEngine(),
    "2": BibintoEngine(),
    "3": BlurEngine(),
}

def get_engine(service_id: str) -> BotEngine:
    return ENGINE_REGISTRY.get(service_id)
