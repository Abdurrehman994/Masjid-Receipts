
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import get_settings
from app.models.user import User, UserRole
from app.schemas.user import Token, UserCreate, User as UserSchema
from app.api.deps import get_current_user

router = APIRouter()

# Get app settings (DATABASE_URL, SECRET_KEY, etc.)
settings = get_settings()


@router.post("/register", response_model=UserSchema)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    ENDPOINT 1: USER REGISTRATION
    """
    
    # STEP 1: Check if username already taken
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # STEP 2: Check if email already taken
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Normalize role input to match UserRole enum
    role_value = user_data.role
    if isinstance(role_value, str):
        normalized = role_value.strip().lower().replace(" ", "_").replace("-", "_")
        try:
            role_enum = UserRole(normalized)
        except ValueError:
            try:
                role_enum = UserRole[normalized.upper()]
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid role. Allowed: imam, finance_secretary, auditor")
    else:
        role_enum = role_value

    # STEP 3: Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # STEP 4: Create new user object
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=role_enum,
        hashed_password=hashed_password 
    )
    
    # STEP 5: Save to database
    db.add(db_user)     
    db.commit()        
    db.refresh(db_user)  
    return db_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT 2: USER LOGIN
    """
    
    # STEP 1: Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # STEP 2 & 3: Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Don't reveal whether username or password was wrong (security)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # STEP 4: Create JWT access token
    # Token will expire after ACCESS_TOKEN_EXPIRE_MINUTES (default: 30 minutes)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create token with username as subject
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # STEP 5: Return token
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    ENDPOINT 3: GET CURRENT USER INFO

    """
    # Just return it
    return current_user
