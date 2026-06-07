import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from app.database import engine, get_db

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# ==================================

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Jewelry Samples API")


@app.post("/samples", response_model=schemas.SampleResponse, status_code=201)
def create_sample(sample: schemas.SampleCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating sample: code={sample.sample_code}, weight={sample.weight}, operator={sample.operator}")
    
    db_sample = models.Sample(
        sample_code=sample.sample_code,
        weight=sample.weight,
        operator=sample.operator,
        status="created"
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    
    logger.info(f"Sample created: ID={db_sample.id}, code={db_sample.sample_code}")
    return db_sample


@app.get("/samples", response_model=list[schemas.SampleResponse])
def get_samples(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching samples: skip={skip}, limit={limit}")
    samples = db.query(models.Sample).offset(skip).limit(limit).all()
    logger.info(f"Returned {len(samples)} samples")
    return samples


@app.get("/samples/{sample_id}", response_model=schemas.SampleResponse)
def get_sample(sample_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching sample ID={sample_id}")
    
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if sample is None:
        logger.warning(f"Sample ID={sample_id} not found")
        raise HTTPException(status_code=404, detail="Проба не найдена")
    
    logger.info(f"Sample found: ID={sample_id}, code={sample.sample_code}")
    return sample


@app.patch("/samples/{sample_id}/status", response_model=schemas.SampleResponse)
def update_sample_status(
    sample_id: int, 
    status_update: schemas.SampleStatusUpdate, 
    db: Session = Depends(get_db)
):
    logger.info(f"Updating status: ID={sample_id}, new status={status_update.status}")
    
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if sample is None:
        logger.warning(f"Cannot update: sample ID={sample_id} not found")
        raise HTTPException(status_code=404, detail="Проба не найдена")
    
    old_status = sample.status
    sample.status = status_update.status
    db.commit()
    db.refresh(sample)
    
    logger.info(f"Status updated: ID={sample_id}, {old_status} → {sample.status}")
    return sample


@app.get("/reports/summary")
def get_summary_report(db: Session = Depends(get_db)):
    logger.info("Generating summary report")
    
    total_count = db.query(func.count(models.Sample.id)).scalar()
    avg_weight = db.query(func.avg(models.Sample.weight)).scalar()
    min_weight = db.query(func.min(models.Sample.weight)).scalar()
    max_weight = db.query(func.max(models.Sample.weight)).scalar()
    
    status_counts = db.query(
        models.Sample.status, 
        func.count(models.Sample.id).label("count")
    ).group_by(models.Sample.status).all()
    
    status_count_dict = {status: count for status, count in status_counts}
    
    report = {
        "total_samples": total_count or 0,
        "average_weight": round(avg_weight, 2) if avg_weight else 0,
        "min_weight": min_weight or 0,
        "max_weight": max_weight or 0,
        "status_breakdown": status_count_dict
    }
    
    logger.info(f"Report generated: total={report['total_samples']}, avg_weight={report['average_weight']}")
    return report
