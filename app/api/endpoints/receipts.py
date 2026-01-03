
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import shutil
from app.core.database import get_db
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.receipt import Receipt, PaymentMode
from app.models.tag import Tag
from app.schemas.receipt import (
    Receipt as ReceiptSchema,
    ReceiptWithUploader
)
from app.api.deps import get_current_user, require_role


def _parse_payment_mode(pm_str: Optional[str]) -> Optional[PaymentMode]:
    if pm_str is None:
        return None
    if isinstance(pm_str, PaymentMode):
        return pm_str
    s = pm_str.strip()
    for mode in PaymentMode:
        if s.lower() == mode.value.lower() or s.upper() == mode.name:
            return mode
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid payment_mode: {pm_str}. Expected one of: {', '.join([m.value for m in PaymentMode])}"
    )

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=ReceiptSchema, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    amount: float = Form(...),
    category: str = Form(...),
    payment_mode: PaymentMode = Form(...),
    note: Optional[str] = Form(None),
    store_name: Optional[str] = Form(None),
    receipt_date: Optional[str] = Form(None),  
    image: UploadFile = File(default=None),  
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: UPLOAD RECEIPT
    
    WHO CAN USE: Anyone authenticated (Imam, Finance Secretary, Auditor)

    """
    
    # STEP 1: Save image file if provided
    image_path = None
    if image:
        # Validate file size by checking the underlying file object
        try:
            image.file.seek(0, os.SEEK_END)
            file_size = image.file.tell()
            image.file.seek(0)
        except Exception:
            file_size = None

        if file_size is not None and file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes (5MB)"
            )
        
        # Validate file type (only images)
        if image.content_type and not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed (jpg, png, gif)"
            )
        
        # Create uploads directory if doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"{current_user.username}_{timestamp}_{image.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file to disk
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_path = file_path
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save image: {str(e)}"
            )
        

    parsed_date = None
    if receipt_date:
        try:
            parsed_date = datetime.fromisoformat(receipt_date)
        except:
            parsed_date = datetime.utcnow()
    else:
        parsed_date = datetime.utcnow()
    
    # STEP 2: Create receipt in database
    db_receipt = Receipt(
        amount=amount,
        category=category,
        payment_mode=payment_mode,
        note=note,
        store_name=store_name,
        receipt_date=parsed_date,
        image_path=image_path,
        uploaded_by=current_user.id
    )
    
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)
    
    return db_receipt


@router.get("/", response_model=List[ReceiptWithUploader])
def get_receipts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    payment_mode: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: GET RECEIPTS
    
    WHO CAN USE:
    - Imam: Only sees their own receipts
    - Finance Secretary: Sees ALL receipts
    - Auditor: Sees ALL receipts
    """
    
    # Build query
    query = db.query(Receipt)
    
    # ROLE-BASED ACCESS CONTROL
    if current_user.role == UserRole.IMAM:
        query = query.filter(Receipt.uploaded_by == current_user.id)
    
    # Apply filters
    if category:
        query = query.filter(Receipt.category == category)
    if payment_mode:
        pm_enum = _parse_payment_mode(payment_mode)
        query = query.filter(Receipt.payment_mode == pm_enum)
    if uploaded_by:
        query = query.filter(Receipt.uploaded_by == uploaded_by)
    
    # Execute query with pagination
    receipts = query.offset(skip).limit(limit).all()
    
    # Add uploader names
    result = []
    for receipt in receipts:
        receipt_dict = receipt.__dict__.copy()
        receipt_dict["uploader_name"] = receipt.uploader.full_name
        result.append(receipt_dict)
    
    return result


@router.get("/search", response_model=List[ReceiptWithUploader])
def search_receipts(
    store_name: Optional[str] = Query(None, description="Search by store name"),
    category: Optional[str] = Query(None, description="Search by category"),
    tag_name: Optional[str] = Query(None, description="Search by tag name"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    payment_mode: Optional[str] = Query(None, description="Payment mode"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    BONUS FEATURE 1: ADVANCED SEARCH
    
    WHO CAN USE: Anyone authenticated

    """
    
    # Start with base query
    query = db.query(Receipt)
    
    # ROLE-BASED ACCESS: Imam only sees own receipts
    if current_user.role == UserRole.IMAM:
        query = query.filter(Receipt.uploaded_by == current_user.id)
    
    # Apply search filters
    if store_name:
        query = query.filter(Receipt.store_name.ilike(f"%{store_name}%"))
    
    if category:
        query = query.filter(Receipt.category.ilike(f"%{category}%"))
    
    if tag_name:
        tag = db.query(Tag).filter(Tag.name.ilike(f"%{tag_name}%")).first()
        if tag:
            query = query.filter(Receipt.tags.contains(tag))
    
    if min_amount is not None:
        query = query.filter(Receipt.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Receipt.amount <= max_amount)
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Receipt.receipt_date >= start)
        except:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Receipt.receipt_date <= end)
        except:
            pass
    
    if payment_mode:
        pm_enum = _parse_payment_mode(payment_mode)
        query = query.filter(Receipt.payment_mode == pm_enum)
    
    # Execute query
    receipts = query.all()
    
    # Add uploader names
    result = []
    for receipt in receipts:
        receipt_dict = receipt.__dict__.copy()
        receipt_dict["uploader_name"] = receipt.uploader.full_name
        result.append(receipt_dict)
    
    return result


@router.get("/{receipt_id}", response_model=ReceiptWithUploader)
def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: GET SINGLE RECEIPT
    
    WHO CAN USE:
    - Imam: Only their own receipts
    - Finance Secretary: Any receipt
    - Auditor: Any receipt
    
    """
    
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Imam can only view their own receipts
    if current_user.role == UserRole.IMAM and receipt.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own receipts"
        )
    
    # Add uploader name
    result = receipt.__dict__.copy()
    result["uploader_name"] = receipt.uploader.full_name
    
    return result


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_receipt(
    receipt_id: int,
    current_user: User = Depends(require_role(UserRole.FINANCE_SECRETARY)),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: DELETE RECEIPT
    
    WHO CAN USE: Only Finance Secretary
    """
    
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Delete image file if exists
    if receipt.image_path and os.path.exists(receipt.image_path):
        try:
            os.remove(receipt.image_path)
        except Exception as e:
            # Log error but don't fail the deletion
            print(f"Warning: Failed to delete image file: {e}")
    
    db.delete(receipt)
    db.commit()
    
    return None
