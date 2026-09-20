import time
import logfire
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings

BATCH_SIZE = 50
_GEMINI_DIM = 3072
_FALLBACK_DIM = 768 


_active_model =  None
_model_type: str | None = None


def _probe_gemini():
    """Try one embed call to verify Gemini is reachable. Returns model or None"""
    try:
        model = GoogleGenerativeAIEmbeddings(model="models/gemini-embeddings-2-preview",google_api_key=settings.GOOGLE_API_KEY)
        model.embed_query("probe")
        logfire.info("Gemini embeddings ready (gemini-embedding-2-preview,3072-dim).")
        return model
    except Exception as e:
        logfire.warning(f"Failed to probe Gemini embeddings: {e}")
        return None



def _load_fallback():
    from sentence_transformers import SentenceTransformer
    logfire.info("Loading sentence-transformers fallback (all-mpnet-base-v2,768-dim)")
    return SentenceTransformer("all-mpnet-base-v2")

def     _init():
    global _active_model, _model_type

    if not _active_model:
        _active_model = _probe_gemini()
        if _active_model:
            _model_type = "gemini"
        else:
            _active_model = _load_fallback()
            _model_type = "fallback"
    return

def get_embedding_dim() -> int:
    """Return the vector dimension for the active model. Call after _init()"""
    _init()
    return _GEMINI_DIM if _model_type == "gemini" else _FALLBACK_DIM

def _embed_batch(batch:list[str]) -> list[list[float]]:
    """Embed a batch of texts using the active model. Returns a list of vectors."""
    if _model_type == "gemini":
        for attempt in range(4):
            try:
                return _active_model.embed_query(batch)
            except Exception as e:
                err = str(e).lower()
                is_rate_limit = any(x in err for x in ("429","rate","quota","resource_exhausted"))
                if is_rate_limit and attempt < 3:
                    wait = 2 ** attempt
                    logfire.warning(f"Gemini Rate limit hit - retrying in {wait} seconds..."
                                    f"(Attempt {attempt+1}/4).")
                    time.sleep(wait)
                else:
                    logfire.error(f"Gemini embedding model failed: {e}")
                    raise 
        raise RuntimeError("Gemini embedding model failed after 4 attempts.")
    else:
        return _active_model.encode(batch,show_progress_bar=False).tolist()
                    


def embed_query(query:str)->list[float]:
    _init()
    if _model_type == "gemini":
        return _active_model.embed_query([query])
    return _embed_batch([query])[0].tolist()


def embed_texts(texts: list[str])-> list[list[float]]:
    _init()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        with logfire.span("Embed batch",model=_model_type,start=i, size=len(batch)):
            all_embeddings.extend(_embed_batch(batch))
    return all_embeddings