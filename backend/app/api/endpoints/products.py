from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Product
from ...schemas import ProductCreate, ProductUpdate, ProductResponse, ProductList

router = APIRouter()


@router.get("/", response_model=ProductList)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista todos los productos Louder con paginación.
    """
    query = db.query(Product)
    
    # Filtros opcionales
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if category:
        query = query.filter(Product.category == category)
    
    # Total count
    total = query.count()
    
    # Paginación
    products = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return ProductList(
        total=total,
        page=page,
        page_size=page_size,
        products=products
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un producto por ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo producto Louder.
    """
    # Verificar que el SKU no exista
    existing = db.query(Product).filter(Product.sku == product_data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{product_data.sku}' already exists")
    
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """
    Actualiza un producto existente.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Actualizar solo los campos proporcionados
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Elimina (desactiva) un producto.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    return None


@router.post("/{product_id}/scan", status_code=202)
async def trigger_product_scan(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger un scan on-demand para un producto específico.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # TODO: Implement Celery task trigger
    # from ...tasks import scan_single_product
    # task = scan_single_product.delay(product_id)
    
    return {
        "message": f"Scan triggered for product {product.name}",
        "product_id": product_id,
        # "task_id": task.id
    }
