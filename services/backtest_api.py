from fastapi import APIRouter
router = APIRouter()

@router.get("/backtest/ping")
def ping():
    return {"ok": True}
