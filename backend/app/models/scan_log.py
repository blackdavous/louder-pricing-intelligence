from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON
from sqlalchemy.sql import func

from ..database import Base


class ScanLog(Base):
    """
    Modelo para logs de ejecución de scans.
    Registra cada ejecución del sistema de monitoreo.
    """
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Tipo de scan
    scan_type = Column(String(50), index=True)  # 'full', 'priority', 'flash', 'on-demand'
    
    # Métricas
    products_scanned = Column(Integer)
    competitors_found = Column(Integer)
    errors = Column(JSON)  # Lista de errores encontrados
    duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20))  # 'success', 'partial', 'failed'
    
    # Timestamps
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)

    def __repr__(self):
        return f"<ScanLog(id={self.id}, type='{self.scan_type}', status='{self.status}', products={self.products_scanned})>"
