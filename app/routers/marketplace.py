from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.models.marketplace import MarketplaceItem
from app.schemas.marketplace import (
    MarketplaceItemCreate,
    MarketplaceItemResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/marketplace", tags=["Agricultural Marketplace"])

@router.get("/items", response_model=List[MarketplaceItemResponse])
def list_marketplace_items(
    category: Optional[str] = Query(None, description="Category filter (seeds, fertilizer, machinery, wheat_grain)"),
    district: Optional[str] = Query(None, description="District filter"),
    search: Optional[str] = Query(None, description="Search keyword in title/description"),
    min_price: Optional[float] = Query(None, description="Minimum price PKR"),
    max_price: Optional[float] = Query(None, description="Maximum price PKR"),
    show_sold: bool = Query(False, description="Include items marked as sold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Browse agricultural items for sale in the marketplace."""
    query = db.query(MarketplaceItem)
    if not show_sold:
        query = query.filter(MarketplaceItem.is_sold == False)
    if category and category != "all":
        query = query.filter(MarketplaceItem.category == category)
    if district and district != "all":
        query = query.filter(MarketplaceItem.district.ilike(f"%{district}%"))
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (MarketplaceItem.title.ilike(search_filter)) |
            (MarketplaceItem.description.ilike(search_filter))
        )
    if min_price is not None:
        query = query.filter(MarketplaceItem.price_pkr >= min_price)
    if max_price is not None:
        query = query.filter(MarketplaceItem.price_pkr <= max_price)

    items = query.order_by(MarketplaceItem.created_at.desc()).all()
    return [
        MarketplaceItemResponse(
            item_id=i.item_id,
            seller_id=i.seller_id,
            seller_name=i.seller_name,
            seller_phone=i.seller_phone,
            title=i.title,
            category=i.category,
            price_pkr=float(i.price_pkr),
            condition=i.condition,
            district=i.district,
            location_address=i.location_address,
            description=i.description,
            image_url=i.image_url,
            is_sold=i.is_sold,
            created_at=i.created_at
        ) for i in items
    ]

@router.post("/items", response_model=MarketplaceItemResponse, status_code=status.HTTP_201_CREATED)
def create_marketplace_item(
    req: MarketplaceItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post an agricultural product, machinery, or harvest for sale."""
    item_id = f"item_{uuid.uuid4().hex[:8]}"
    item = MarketplaceItem(
        item_id=item_id,
        seller_id=current_user.user_id,
        seller_name=current_user.full_name,
        seller_phone=req.contact_phone,
        title=req.title,
        category=req.category,
        price_pkr=req.price_pkr,
        condition=req.condition,
        district=req.district,
        location_address=req.location_address,
        description=req.description,
        image_url=req.image_url,
        is_sold=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MarketplaceItemResponse(
        item_id=item.item_id,
        seller_id=item.seller_id,
        seller_name=item.seller_name,
        seller_phone=item.seller_phone,
        title=item.title,
        category=item.category,
        price_pkr=float(item.price_pkr),
        condition=item.condition,
        district=item.district,
        location_address=item.location_address,
        description=item.description,
        image_url=item.image_url,
        is_sold=item.is_sold,
        created_at=item.created_at
    )

@router.get("/items/{item_id}", response_model=MarketplaceItemResponse)
def get_marketplace_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single marketplace listing."""
    item = db.query(MarketplaceItem).filter(MarketplaceItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return MarketplaceItemResponse(
        item_id=item.item_id,
        seller_id=item.seller_id,
        seller_name=item.seller_name,
        seller_phone=item.seller_phone,
        title=item.title,
        category=item.category,
        price_pkr=float(item.price_pkr),
        condition=item.condition,
        district=item.district,
        location_address=item.location_address,
        description=item.description,
        image_url=item.image_url,
        is_sold=item.is_sold,
        created_at=item.created_at
    )

@router.patch("/items/{item_id}/sold", response_model=MarketplaceItemResponse)
def toggle_item_sold(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle sold status for an item owned by current user."""
    item = db.query(MarketplaceItem).filter(
        MarketplaceItem.item_id == item_id,
        MarketplaceItem.seller_id == current_user.user_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized.")
    
    item.is_sold = not item.is_sold
    db.commit()
    db.refresh(item)
    return MarketplaceItemResponse(
        item_id=item.item_id,
        seller_id=item.seller_id,
        seller_name=item.seller_name,
        seller_phone=item.seller_phone,
        title=item.title,
        category=item.category,
        price_pkr=float(item.price_pkr),
        condition=item.condition,
        district=item.district,
        location_address=item.location_address,
        description=item.description,
        image_url=item.image_url,
        is_sold=item.is_sold,
        created_at=item.created_at
    )

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marketplace_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an item owned by current user."""
    item = db.query(MarketplaceItem).filter(
        MarketplaceItem.item_id == item_id,
        MarketplaceItem.seller_id == current_user.user_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized.")
    db.delete(item)
    db.commit()
    return None

@router.get("/user/my-items", response_model=List[MarketplaceItemResponse])
def get_my_marketplace_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List marketplace listings posted by the current user."""
    items = db.query(MarketplaceItem).filter(MarketplaceItem.seller_id == current_user.user_id).order_by(MarketplaceItem.created_at.desc()).all()
    return [
        MarketplaceItemResponse(
            item_id=i.item_id,
            seller_id=i.seller_id,
            seller_name=i.seller_name,
            seller_phone=i.seller_phone,
            title=i.title,
            category=i.category,
            price_pkr=float(i.price_pkr),
            condition=i.condition,
            district=i.district,
            location_address=i.location_address,
            description=i.description,
            image_url=i.image_url,
            is_sold=i.is_sold,
            created_at=i.created_at
        ) for i in items
    ]
