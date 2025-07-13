"""
Universal content sharing API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..db.database import get_db
from ..models import User, ContentShare, Book, TVShow, Movie, RecipeV2
from ..models.content import ContentType
from ..core.auth_service import get_current_user
from ..schemas.sharing import (
    ContentShareCreate, ContentShareResponse, SharedContentResponse,
    UserProfileResponse, PublicUserProfile
)

router = APIRouter()


@router.post("/share", response_model=ContentShareResponse)
async def share_content(
    share_data: ContentShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share content with another user"""
    
    # Find the target user
    target_user = db.query(User).filter(User.email == share_data.shared_with_email).first()
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Prevent self-sharing
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot share content with yourself"
        )
    
    # Verify content ownership and exists
    content_item = None
    if share_data.content_type == ContentType.RECIPE:
        content_item = db.query(RecipeV2).filter(
            and_(RecipeV2.id == share_data.content_id, RecipeV2.user_id == current_user.id)
        ).first()
    elif share_data.content_type == ContentType.BOOK:
        content_item = db.query(Book).filter(
            and_(Book.id == share_data.content_id, Book.user_id == current_user.id)
        ).first()
    elif share_data.content_type == ContentType.TV_SHOW:
        content_item = db.query(TVShow).filter(
            and_(TVShow.id == share_data.content_id, TVShow.user_id == current_user.id)
        ).first()
    elif share_data.content_type == ContentType.MOVIE:
        content_item = db.query(Movie).filter(
            and_(Movie.id == share_data.content_id, Movie.user_id == current_user.id)
        ).first()
    
    if not content_item:
        raise HTTPException(
            status_code=404,
            detail="Content not found or you don't have permission to share it"
        )
    
    # Check if already shared with this user
    existing_share = db.query(ContentShare).filter(
        and_(
            ContentShare.shared_by_user_id == current_user.id,
            ContentShare.shared_with_user_id == target_user.id,
            ContentShare.content_type == share_data.content_type,
            getattr(ContentShare, f"{share_data.content_type.value}_id") == share_data.content_id,
            ContentShare.is_active == True
        )
    ).first()
    
    if existing_share:
        raise HTTPException(
            status_code=400,
            detail="Content already shared with this user"
        )
    
    # Create the share
    content_share = ContentShare(
        shared_by_user_id=current_user.id,
        shared_with_user_id=target_user.id,
        content_type=share_data.content_type,
        share_message=share_data.message
    )
    
    # Set the appropriate content ID
    if share_data.content_type == ContentType.RECIPE:
        content_share.recipe_id = share_data.content_id
    elif share_data.content_type == ContentType.BOOK:
        content_share.book_id = share_data.content_id
    elif share_data.content_type == ContentType.TV_SHOW:
        content_share.tv_show_id = share_data.content_id
    elif share_data.content_type == ContentType.MOVIE:
        content_share.movie_id = share_data.content_id
    
    db.add(content_share)
    db.commit()
    db.refresh(content_share)
    
    return ContentShareResponse(
        id=content_share.id,
        content_type=content_share.content_type,
        content_id=share_data.content_id,
        shared_by_user_email=current_user.email,
        shared_with_user_email=target_user.email,
        share_message=content_share.share_message,
        created_at=content_share.created_at,
        is_active=content_share.is_active
    )


@router.get("/shared-with-me", response_model=List[SharedContentResponse])
async def get_shared_content(
    content_type: Optional[ContentType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content shared with the current user"""
    
    query = db.query(ContentShare).filter(
        and_(
            ContentShare.shared_with_user_id == current_user.id,
            ContentShare.is_active == True
        )
    )
    
    if content_type:
        query = query.filter(ContentShare.content_type == content_type)
    
    shares = query.all()
    
    shared_content = []
    for share in shares:
        # Get the actual content item
        content_item = None
        content_title = ""
        content_description = ""
        
        if share.content_type == ContentType.RECIPE:
            content_item = db.query(RecipeV2).filter(RecipeV2.id == share.recipe_id).first()
            if content_item:
                content_title = content_item.name
                content_description = content_item.description or ""
        elif share.content_type == ContentType.BOOK:
            content_item = db.query(Book).filter(Book.id == share.book_id).first()
            if content_item:
                content_title = content_item.title
                content_description = content_item.description or ""
        elif share.content_type == ContentType.TV_SHOW:
            content_item = db.query(TVShow).filter(TVShow.id == share.tv_show_id).first()
            if content_item:
                content_title = content_item.title
                content_description = content_item.description or ""
        elif share.content_type == ContentType.MOVIE:
            content_item = db.query(Movie).filter(Movie.id == share.movie_id).first()
            if content_item:
                content_title = content_item.title
                content_description = content_item.description or ""
        
        if content_item:
            # Get sharer info
            shared_by_user = db.query(User).filter(User.id == share.shared_by_user_id).first()
            
            shared_content.append(SharedContentResponse(
                share_id=share.id,
                content_type=share.content_type,
                content_id=getattr(share, f"{share.content_type.value}_id"),
                content_title=content_title,
                content_description=content_description,
                shared_by_user_name=shared_by_user.name or shared_by_user.email,
                shared_by_user_email=shared_by_user.email,
                share_message=share.share_message,
                shared_at=share.created_at
            ))
    
    return shared_content


@router.get("/my-shares", response_model=List[ContentShareResponse])
async def get_my_shares(
    content_type: Optional[ContentType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content shared by the current user"""
    
    query = db.query(ContentShare).filter(
        and_(
            ContentShare.shared_by_user_id == current_user.id,
            ContentShare.is_active == True
        )
    )
    
    if content_type:
        query = query.filter(ContentShare.content_type == content_type)
    
    shares = query.all()
    
    my_shares = []
    for share in shares:
        # Get shared with user info
        shared_with_user = db.query(User).filter(User.id == share.shared_with_user_id).first()
        
        content_id = getattr(share, f"{share.content_type.value}_id")
        
        my_shares.append(ContentShareResponse(
            id=share.id,
            content_type=share.content_type,
            content_id=content_id,
            shared_by_user_email=current_user.email,
            shared_with_user_email=shared_with_user.email,
            share_message=share.share_message,
            created_at=share.created_at,
            is_active=share.is_active
        ))
    
    return my_shares


@router.delete("/revoke/{share_id}")
async def revoke_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a content share"""
    
    share = db.query(ContentShare).filter(
        and_(
            ContentShare.id == share_id,
            ContentShare.shared_by_user_id == current_user.id,
            ContentShare.is_active == True
        )
    ).first()
    
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found or you don't have permission to revoke it"
        )
    
    share.is_active = False
    db.commit()
    
    return {"message": "Share revoked successfully"}


@router.post("/add-to-my-list")
async def add_shared_content_to_my_list(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add shared content to user's personal list"""
    
    # Get the share
    share = db.query(ContentShare).filter(
        and_(
            ContentShare.id == share_id,
            ContentShare.shared_with_user_id == current_user.id,
            ContentShare.is_active == True
        )
    ).first()
    
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found"
        )
    
    # Get the original content item
    original_content = None
    if share.content_type == ContentType.RECIPE:
        original_content = db.query(RecipeV2).filter(RecipeV2.id == share.recipe_id).first()
    elif share.content_type == ContentType.BOOK:
        original_content = db.query(Book).filter(Book.id == share.book_id).first()
    elif share.content_type == ContentType.TV_SHOW:
        original_content = db.query(TVShow).filter(TVShow.id == share.tv_show_id).first()
    elif share.content_type == ContentType.MOVIE:
        original_content = db.query(Movie).filter(Movie.id == share.movie_id).first()
    
    if not original_content:
        raise HTTPException(
            status_code=404,
            detail="Original content not found"
        )
    
    # Check if user already has this content
    existing_content = None
    if share.content_type == ContentType.BOOK:
        existing_content = db.query(Book).filter(
            and_(
                Book.user_id == current_user.id,
                Book.title == original_content.title,
                Book.author == original_content.author
            )
        ).first()
    elif share.content_type == ContentType.TV_SHOW:
        existing_content = db.query(TVShow).filter(
            and_(
                TVShow.user_id == current_user.id,
                TVShow.title == original_content.title
            )
        ).first()
    elif share.content_type == ContentType.MOVIE:
        existing_content = db.query(Movie).filter(
            and_(
                Movie.user_id == current_user.id,
                Movie.title == original_content.title
            )
        ).first()
    
    if existing_content:
        raise HTTPException(
            status_code=400,
            detail="You already have this content in your list"
        )
    
    # Create a copy for the user
    new_content = None
    if share.content_type == ContentType.BOOK:
        new_content = Book(
            user_id=current_user.id,
            title=original_content.title,
            author=original_content.author,
            description=original_content.description,
            genre=original_content.genre,
            isbn=original_content.isbn,
            pages=original_content.pages,
            publication_year=original_content.publication_year,
            cover_image_url=original_content.cover_image_url,
            google_books_id=original_content.google_books_id,
            open_library_id=original_content.open_library_id,
            reading_status="want_to_read",  # Default status for shared content
            source="shared"
        )
    elif share.content_type == ContentType.TV_SHOW:
        new_content = TVShow(
            user_id=current_user.id,
            title=original_content.title,
            description=original_content.description,
            genre=original_content.genre,
            network=original_content.network,
            total_seasons=original_content.total_seasons,
            total_episodes=original_content.total_episodes,
            status=original_content.status,
            first_air_date=original_content.first_air_date,
            last_air_date=original_content.last_air_date,
            poster_image_url=original_content.poster_image_url,
            tmdb_id=original_content.tmdb_id,
            tvmaze_id=original_content.tvmaze_id,
            imdb_id=original_content.imdb_id,
            viewing_status="want_to_watch",  # Default status for shared content
            source="shared"
        )
    elif share.content_type == ContentType.MOVIE:
        new_content = Movie(
            user_id=current_user.id,
            title=original_content.title,
            description=original_content.description,
            genre=original_content.genre,
            director=original_content.director,
            release_year=original_content.release_year,
            runtime=original_content.runtime,
            poster_image_url=original_content.poster_image_url,
            tmdb_id=original_content.tmdb_id,
            imdb_id=original_content.imdb_id,
            omdb_id=original_content.omdb_id,
            viewing_status="want_to_watch",  # Default status for shared content
            source="shared"
        )
    
    if new_content:
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        
        return {
            "message": f"{share.content_type.value.replace('_', ' ').title()} added to your list successfully",
            "content_id": new_content.id
        }
    
    raise HTTPException(
        status_code=400,
        detail="Unable to add content to your list"
    )


@router.get("/public-profile/{user_email}", response_model=PublicUserProfile)
async def get_public_user_profile(
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get a user's public profile with their shared content"""
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Get user's content counts (for public profile stats)
    books_count = db.query(Book).filter(Book.user_id == user.id).count()
    tv_shows_count = db.query(TVShow).filter(TVShow.user_id == user.id).count()
    movies_count = db.query(Movie).filter(Movie.user_id == user.id).count()
    recipes_count = db.query(RecipeV2).filter(RecipeV2.user_id == user.id).count()
    
    return PublicUserProfile(
        name=user.name or user.email,
        email=user.email,
        books_count=books_count,
        tv_shows_count=tv_shows_count,
        movies_count=movies_count,
        recipes_count=recipes_count,
        member_since=user.created_at
    )