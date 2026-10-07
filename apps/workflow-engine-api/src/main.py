from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.routers import workflows, executions, catalog

app = FastAPI(
    title="Multi-Tenant Workflow Engine Platform",
    description="Motor de Workflows Configurables, Multi-Tenant, con Roles de Editor/Revisor, Rollback y Catálogo de Microservicios.",
    version="1.0.0"
)

# CORS para comunicación con el Web Builder (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar tablas al arrancar
@app.on_event("startup")
def on_startup():
    init_db()

# Registrar Routers
app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(catalog.router)

@app.get("/health", tags=["Monitoring"])
def health_check():
    return {"status": "ok", "service": "workflow-engine-core"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
