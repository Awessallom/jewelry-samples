from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import engine, get_db
from sqlalchemy import func

models.Base.metadata.create_all(bind=engine)  # создаём таблицы

app = FastAPI(title="Jewelry Samples API")

@app.post("/samples", response_model=schemas.SampleResponse, status_code=201)
def create_sample(sample: schemas.SampleCreate, db: Session = Depends(get_db)):
    db_sample = models.Sample(
        sample_code=sample.sample_code,
        weight=sample.weight,
        operator=sample.operator,
        status="created"  # явно устанавливаем
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample

@app.get("/samples", response_model=list[schemas.SampleResponse])
def get_samples(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    samples = db.query(models.Sample).offset(skip).limit(limit).all()
    return samples

@app.get("/samples/{sample_id}", response_model=schemas.SampleResponse)
def get_sample(sample_id: int, db: Session = Depends(get_db)):
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if sample is None:
        raise HTTPException(status_code=404, detail="Проба не найдена")
    return sample

@app.patch("/samples/{sample_id}/status", response_model=schemas.SampleResponse)
def update_sample_status(
    sample_id: int, 
    status_update: schemas.SampleStatusUpdate, 
    db: Session = Depends(get_db)
):
    # 1. Находим пробу в БД
    sample = db.query(models.Sample).filter(models.Sample.id == sample_id).first()
    if sample is None:
        raise HTTPException(status_code=404, detail="Проба не найдена")
    
    # 2. Обновляем статус
    sample.status = status_update.status
    
    # 3. Сохраняем изменения
    db.commit()
    db.refresh(sample)
    
    # 4. Возвращаем обновлённую пробу
    return sample

@app.get("/reports/summary")
def get_summary_report(db: Session = Depends(get_db)):
    # 1. Общая статистика по всем пробам
    total_count = db.query(func.count(models.Sample.id)).scalar()
    avg_weight = db.query(func.avg(models.Sample.weight)).scalar()
    min_weight = db.query(func.min(models.Sample.weight)).scalar()
    max_weight = db.query(func.max(models.Sample.weight)).scalar()
    
    # 2. Статистика по статусам (группировка)
    status_counts = db.query(
        models.Sample.status, 
        func.count(models.Sample.id).label("count")
    ).group_by(models.Sample.status).all()
    
    # 3. Преобразуем результат группировки в словарь
    status_count_dict = {status: count for status, count in status_counts}
    
    # 4. Формируем итоговый отчёт
    report = {
        "total_samples": total_count or 0,
        "average_weight": round(avg_weight, 2) if avg_weight else 0,
        "min_weight": min_weight or 0,
        "max_weight": max_weight or 0,
        "status_breakdown": status_count_dict
    }
    
    return report