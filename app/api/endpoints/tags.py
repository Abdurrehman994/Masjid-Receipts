
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.tag import Tag
from app.models.receipt import Receipt
from app.schemas.tag import Tag as TagSchema, TagCreate, TagWithCount
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.post("/", response_model=TagSchema, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_role(UserRole.FINANCE_SECRETARY)),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: CREATE TAG
    
    WHO CAN USE: Finance Secretary ONLY
    """
    
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
    if existing_tag:
        raise HTTPException(
            status_code=400,
            detail=f"Tag '{tag_data.name}' already exists"
        )
    
    # Create tag
    db_tag = Tag(
        name=tag_data.name,
        description=tag_data.description
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return db_tag


@router.get("/", response_model=List[TagWithCount])
def get_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: GET ALL TAGS
    
    WHO CAN USE: Anyone authenticated
    """
    
    tags = db.query(Tag).all()
    
    # Add receipt count for each tag
    result = []
    for tag in tags:
        tag_dict = {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "receipt_count": len(tag.receipts)
        }
        result.append(tag_dict)
    
    return result


@router.get("/{tag_id}", response_model=TagSchema)
def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: GET SINGLE TAG
    
    WHO CAN USE: Anyone authenticated
    """
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag


@router.post("/assign/{receipt_id}/{tag_id}", status_code=status.HTTP_200_OK)
def assign_tag_to_receipt(
    receipt_id: int,
    tag_id: int,
    current_user: User = Depends(require_role(UserRole.FINANCE_SECRETARY)),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: ASSIGN TAG TO RECEIPT
    
    WHO CAN USE: Finance Secretary ONLY
    """
    
    # Find receipt
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Find tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if already assigned
    if tag in receipt.tags:
        raise HTTPException(
            status_code=400,
            detail=f"Tag '{tag.name}' is already assigned to this receipt"
        )
    
    # Assign tag
    receipt.tags.append(tag)
    db.commit()
    
    return {
        "message": f"Tag '{tag.name}' assigned to receipt #{receipt.id}"
    }


@router.delete("/unassign/{receipt_id}/{tag_id}", status_code=status.HTTP_200_OK)
def unassign_tag_from_receipt(
    receipt_id: int,
    tag_id: int,
    current_user: User = Depends(require_role(UserRole.FINANCE_SECRETARY)),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: REMOVE TAG FROM RECEIPT
    
    WHO CAN USE: Finance Secretary ONLY
    """
    
    # Find receipt
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Find tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if assigned
    if tag not in receipt.tags:
        raise HTTPException(
            status_code=400,
            detail=f"Tag '{tag.name}' is not assigned to this receipt"
        )
    
    # Remove tag
    receipt.tags.remove(tag)
    db.commit()
    
    return {
        "message": f"Tag '{tag.name}' removed from receipt #{receipt.id}"
    }


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    current_user: User = Depends(require_role(UserRole.FINANCE_SECRETARY)),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: DELETE TAG
    
    WHO CAN USE: Finance Secretary ONLY
    """
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
    
    return None