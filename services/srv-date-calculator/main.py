from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI(title="Business Date Calculator Microservice", version="1.0.0")

class DateCalcRequest(BaseModel):
    start_date: str # YYYY-MM-DD
    business_days_to_add: int

class DateCalcResponse(BaseModel):
    start_date: str
    due_date: str
    business_days_added: int
    calculated_at: str

@app.post("/api/v1/calculate", response_model=DateCalcResponse)
def calculate_due_date(req: DateCalcRequest):
    """
    Microservicio para cálculo de plazos de vigencia excluyendo fines de semana.
    """
    start = datetime.strptime(req.start_date, "%Y-%m-%d")
    current = start
    added = 0
    while added < req.business_days_to_add:
        current += timedelta(days=1)
        if current.weekday() < 5: # Lunes a Viernes
            added += 1

    return DateCalcResponse(
        start_date=req.start_date,
        due_date=current.strftime("%Y-%m-%d"),
        business_days_added=req.business_days_to_add,
        calculated_at=datetime.utcnow().isoformat()
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "srv-date-calculator"}
