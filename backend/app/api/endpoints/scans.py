from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import ScanLog
from ...schemas import ScanLogResponse, ScanTrigger

router = APIRouter()


@router.get("/", response_model=List[ScanLogResponse])
async def list_scans(
    limit: int = Query(50, ge=1, le=200),
    scan_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista los logs de scans ejecutados.
    """
    query = db.query(ScanLog).order_by(ScanLog.started_at.desc())
    
    if scan_type:
        query = query.filter(ScanLog.scan_type == scan_type)
    if status:
        query = query.filter(ScanLog.status == status)
    
    scans = query.limit(limit).all()
    return scans


@router.get("/{scan_id}", response_model=ScanLogResponse)
async def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene los detalles de un scan específico.
    """
    scan = db.query(ScanLog).filter(ScanLog.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/trigger", status_code=202)
async def trigger_scan(
    scan_data: ScanTrigger,
    db: Session = Depends(get_db),
):
    """
    Trigger un scan manual.
    """
    # TODO: Implement Celery task
    # from ...tasks import run_scan
    # task = run_scan.delay(scan_data.scan_type, scan_data.product_ids)
    
    return {
        "message": f"Scan of type '{scan_data.scan_type}' triggered successfully",
        "scan_type": scan_data.scan_type,
        "product_ids": scan_data.product_ids,
        # "task_id": task.id
    }
