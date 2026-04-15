"""
Mock Reltio MDM service.
Mirrors a subset of Reltio's REST API:
  POST /entities                            create
  GET  /entities/{uri}                      get
  PUT  /entities/{uri}                      update
  POST /entities/_search                    filter-based search
  GET  /entities/{uri}/_potentialMatches    duplicate candidates
  POST /entities/_matchProbe                score a hypothetical (pre-create) entity
  POST /entities/_merge                     merge two entities
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import entities
from app.store import store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not store.load():
        store.seed_if_empty()
        store.persist()
    yield


app = FastAPI(title="Mock Reltio MDM", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(entities.router)


@app.get("/health")
def health():
    return {"status": "ok", "entityCount": sum(1 for _ in store.all())}


@app.post("/_admin/reseed")
def reseed():
    store._entities.clear()
    store._merged.clear()
    store.seed_if_empty()
    store.persist()
    return {"status": "reseeded", "entityCount": sum(1 for _ in store.all())}
