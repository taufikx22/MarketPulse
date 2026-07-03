from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.clerk_auth import ClerkUser, get_current_user, require_analyst
from app.models.auth import User, Organization, OrgMembership, Watchlist
from app.models.brand import Brand
from app.schemas import UserOut, WatchlistOut, WatchlistAdd, BrandOut

router = APIRouter(tags=["org"])


@router.get("/me", response_model=UserOut)
async def get_me(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.clerk_user_id == user.user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        from app.config import get_settings
        settings = get_settings()
        if not settings.clerk_jwks_url:
            db_user = User(clerk_user_id=user.user_id, email="mock@marketpulse.dev", name="Mock Analyst")
            db.add(db_user)
            await db.flush()
        else:
            raise HTTPException(status_code=404, detail="User not synced yet")
    return db_user


async def _resolve_org(user: ClerkUser, db: AsyncSession) -> Organization:
    if not user.org_id:
        raise HTTPException(status_code=400, detail="No organization selected")
    result = await db.execute(
        select(Organization).where(Organization.clerk_org_id == user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        from app.config import get_settings
        settings = get_settings()
        if not settings.clerk_jwks_url:
            org = Organization(clerk_org_id=user.org_id, name="Mock Workspace")
            db.add(org)
            await db.flush()
        else:
            raise HTTPException(status_code=404, detail="Organization not synced yet")
    return org



@router.get("/org/watchlist", response_model=list[BrandOut])
async def get_watchlist(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await _resolve_org(user, db)
    result = await db.execute(
        select(Brand)
        .join(Watchlist, Watchlist.brand_id == Brand.id)
        .where(Watchlist.org_id == org.id)
    )
    return result.scalars().all()


@router.post("/org/watchlist", response_model=WatchlistOut)
async def add_to_watchlist(
    body: WatchlistAdd,
    user: ClerkUser = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    org = await _resolve_org(user, db)
    brand = await db.get(Brand, body.brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    existing = await db.execute(
        select(Watchlist).where(Watchlist.org_id == org.id, Watchlist.brand_id == body.brand_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Brand already on watchlist")

    entry = Watchlist(org_id=org.id, brand_id=body.brand_id)
    db.add(entry)
    await db.flush()
    return entry


@router.delete("/org/watchlist/{brand_id}")
async def remove_from_watchlist(
    brand_id: int,
    user: ClerkUser = Depends(require_analyst),
    db: AsyncSession = Depends(get_db),
):
    org = await _resolve_org(user, db)
    result = await db.execute(
        select(Watchlist).where(Watchlist.org_id == org.id, Watchlist.brand_id == brand_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Not on watchlist")
    await db.delete(entry)
    return {"status": "removed"}
