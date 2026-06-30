# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()
RAW_DATA_PATH = "data/raw/patients_raw.csv"
ANONYMIZED_DATA_PATH = "data/processed/patients_anonymized.csv"


def _load_patient_data() -> pd.DataFrame:
    try:
        return pd.read_csv(
            RAW_DATA_PATH,
            dtype={"cccd": str, "so_dien_thoai": str},
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Patient dataset not found. Generate data before calling the API.",
        ) from exc

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = _load_patient_data()
    return JSONResponse(content=df.head(10).to_dict(orient="records"))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = _load_patient_data()
    df_anon = anonymizer.anonymize_dataframe(df)
    df_anon.to_csv(ANONYMIZED_DATA_PATH, index=False)
    return JSONResponse(content=df_anon.head(10).to_dict(orient="records"))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = _load_patient_data()
    metrics = (
        df.groupby("benh")
        .agg(
            patient_count=("patient_id", "count"),
            avg_lab_result=("ket_qua_xet_nghiem", "mean"),
        )
        .reset_index()
    )
    metrics["avg_lab_result"] = metrics["avg_lab_result"].round(2)
    return JSONResponse(content=metrics.to_dict(orient="records"))

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    TODO: Chỉ admin được xóa. Các role khác nhận 403.
    """
    df = _load_patient_data()
    if patient_id not in set(df["patient_id"].astype(str)):
        raise HTTPException(status_code=404, detail="Patient not found")

    updated_df = df[df["patient_id"].astype(str) != patient_id]
    updated_df.to_csv(RAW_DATA_PATH, index=False)

    return {
        "status": "deleted",
        "patient_id": patient_id,
        "remaining_records": len(updated_df),
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
