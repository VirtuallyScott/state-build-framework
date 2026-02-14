"""
User management endpoints for the Build State API.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..core.auth import get_current_active_user, get_password_hash, create_api_token
from .. import models

router = APIRouter()


@router.post("/users", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users", response_model=List[models.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all users.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@router.get("/users/me", response_model=models.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Get the current logged-in user's profile.
    """
    return current_user


@router.get("/users/{user_id}", response_model=models.UserResponse)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific user by ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", response_model=models.UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_update: models.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Update a user's information.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Authorization: Allow users to update themselves, or admins to update anyone
    if db_user.id != current_user.id:
        # A more robust role/permission system would be better here
        # This is a placeholder for a real permission system
        pass
        # if not current_user.is_admin: # Assuming an is_admin flag
        #      raise HTTPException(status_code=403, detail="Not authorized to update this user")

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    else:
        update_data.pop("password", None)


    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete a user (soft delete).
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Authorization check (e.g., admin only)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete users")

    db_user.disabled = True
    db.add(db_user)
    db.commit()
    return


@router.post("/users/{user_id}/tokens", response_model=models.APITokenInfo, status_code=status.HTTP_201_CREATED)
def create_user_api_token(
    user_id: uuid.UUID,
    token_data: models.APITokenCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a new API token for a user. Users can create tokens for themselves, admins can create for any user.
    """
    scopes = get_user_scopes(current_user, db)
    if user_id != current_user.id and 'admin' not in scopes and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create tokens for this user")

    return create_api_token(db=db, user_id=user_id, token_data=token_data)


@router.get("/users/{user_id}/tokens", response_model=List[models.APITokenResponse])
def list_user_api_tokens(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    List all API tokens for a user.
    """
    if user_id != current_user.id:
        # Add admin check if necessary
        raise HTTPException(status_code=403, detail="Not authorized to view tokens for this user")

    return db.query(models.APIToken).filter(models.APIToken.user_id == user_id).all()


@router.delete("/users/{user_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api_token(
    user_id: uuid.UUID,
    token_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete a user's API token.
    """
    if user_id != current_user.id:
        # Add admin check if necessary
        raise HTTPException(status_code=403, detail="Not authorized to delete tokens for this user")

    db_token = db.query(models.APIToken).filter(
        models.APIToken.id == token_id,
        models.APIToken.user_id == user_id
    ).first()

    if db_token is None:
        raise HTTPException(status_code=404, detail="Token not found")

    db.delete(db_token)
    db.commit()
    return


@router.get("/users/me/profile", response_model=models.UserProfileResponse)
async def read_my_profile(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Get the current logged-in user's profile with tokens.
    """
    tokens = db.query(models.APIToken).filter(models.APIToken.user_id == current_user.id).all()
    user_profile = models.UserProfileResponse.from_orm(current_user)
    user_profile.tokens = tokens
    return user_profile

from ..dependencies import get_db
from ..core.auth import get_current_active_user, get_password_hash, create_api_token
from .. import models

router = APIRouter()


@router.post("/users", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users", response_model=List[models.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all users.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@router.get("/users/me", response_model=models.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Get the current logged-in user's profile.
    """
    return current_user


@router.get("/users/{user_id}", response_model=models.UserResponse)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific user by ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", response_model=models.UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_update: models.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Update a user's information.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Authorization: Allow users to update themselves, or admins to update anyone
    if db_user.id != current_user.id:
        # A more robust role/permission system would be better here
        if not current_user.is_admin: # Assuming an is_admin flag
             raise HTTPException(status_code=403, detail="Not authorized to update this user")

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete a user (soft delete).
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Authorization check (e.g., admin only)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete users")

    db_user.disabled = True
    db.add(db_user)
    db.commit()
    return


@router.post("/users/{user_id}/tokens", response_model=models.APITokenResponse, status_code=status.HTTP_201_CREATED)
def create_user_api_token(
    user_id: uuid.UUID,
    token_data: models.APITokenCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Create a new API token for a user.
    """
    if user_id != current_user.id:
        # Add admin check if necessary
        raise HTTPException(status_code=403, detail="Not authorized to create tokens for this user")

    return create_api_token(db=db, user_id=user_id, token_data=token_data)


@router.get("/users/{user_id}/tokens", response_model=List[models.APITokenResponse])
def list_user_api_tokens(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    List all API tokens for a user.
    """
    if user_id != current_user.id:
        # Add admin check if necessary
        raise HTTPException(status_code=403, detail="Not authorized to view tokens for this user")

    return db.query(models.APIToken).filter(models.APIToken.user_id == user_id).all()


@router.delete("/users/{user_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api_token(
    user_id: uuid.UUID,
    token_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Delete a user's API token.
    """
    if user_id != current_user.id:
        # Add admin check if necessary
        raise HTTPException(status_code=403, detail="Not authorized to delete tokens for this user")

    db_token = db.query(models.APIToken).filter(
        models.APIToken.id == token_id,
        models.APIToken.user_id == user_id
    ).first()

    if db_token is None:
        raise HTTPException(status_code=404, detail="Token not found")

    db.delete(db_token)
    db.commit()
    return


@router.get("/users/me/profile", response_model=models.UserProfileResponse)
async def read_my_profile(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Get the current logged-in user's profile with tokens.
    """
    tokens = db.query(models.APIToken).filter(models.APIToken.user_id == current_user.id).all()
    user_profile = models.UserProfileResponse.from_orm(current_user)
    user_profile.tokens = tokens
    return user_profile