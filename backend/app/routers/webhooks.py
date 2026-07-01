import hashlib
import hmac
import json
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select
from app.database import async_session
from app.models.auth import Organization, User, OrgMembership
from app.config import get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_svix_signature(payload: bytes, headers: dict) -> bool:
    """Basic Svix webhook signature check. In production you'd use the svix library,
    but this keeps the dependency lighter for now."""
    secret = get_settings().clerk_webhook_secret
    if not secret:
        return True  # skip verification if no secret configured (dev mode)

    svix_id = headers.get("svix-id", "")
    svix_timestamp = headers.get("svix-timestamp", "")
    svix_signature = headers.get("svix-signature", "")

    if not all([svix_id, svix_timestamp, svix_signature]):
        return False

    # Svix signs: "{msg_id}.{timestamp}.{body}"
    to_sign = f"{svix_id}.{svix_timestamp}.{payload.decode()}"

    # The secret from Clerk is prefixed with "whsec_" and base64-encoded
    import base64
    secret_bytes = base64.b64decode(secret.replace("whsec_", ""))
    expected = hmac.new(secret_bytes, to_sign.encode(), hashlib.sha256).digest()
    expected_b64 = base64.b64encode(expected).decode()

    # svix-signature can contain multiple signatures separated by spaces
    for sig in svix_signature.split(" "):
        sig_value = sig.split(",", 1)[-1] if "," in sig else sig
        if hmac.compare_digest(sig_value, expected_b64):
            return True
    return False


@router.post("/clerk")
async def clerk_webhook(request: Request):
    body = await request.body()
    if not verify_svix_signature(body, dict(request.headers)):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event = json.loads(body)
    event_type = event.get("type", "")
    data = event.get("data", {})

    async with async_session() as session:
        if event_type == "user.created" or event_type == "user.updated":
            clerk_id = data.get("id", "")
            email = ""
            if data.get("email_addresses"):
                email = data["email_addresses"][0].get("email_address", "")
            name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()

            existing = await session.execute(
                select(User).where(User.clerk_user_id == clerk_id)
            )
            user = existing.scalar_one_or_none()
            if user:
                user.email = email
                user.name = name
            else:
                session.add(User(clerk_user_id=clerk_id, email=email, name=name))
            await session.commit()

        elif event_type == "organization.created" or event_type == "organization.updated":
            clerk_org_id = data.get("id", "")
            org_name = data.get("name", "")

            existing = await session.execute(
                select(Organization).where(Organization.clerk_org_id == clerk_org_id)
            )
            org = existing.scalar_one_or_none()
            if org:
                org.name = org_name
            else:
                session.add(Organization(clerk_org_id=clerk_org_id, name=org_name))
            await session.commit()

        elif event_type == "organizationMembership.created":
            clerk_org_id = data.get("organization", {}).get("id", "")
            clerk_user_id = data.get("public_user_data", {}).get("user_id", "")
            role = data.get("role", "viewer")
            # Normalize Clerk's role format
            if "admin" in role:
                role = "analyst"
            else:
                role = "viewer"

            org_result = await session.execute(
                select(Organization).where(Organization.clerk_org_id == clerk_org_id)
            )
            org = org_result.scalar_one_or_none()
            user_result = await session.execute(
                select(User).where(User.clerk_user_id == clerk_user_id)
            )
            user = user_result.scalar_one_or_none()

            if org and user:
                session.add(OrgMembership(user_id=user.id, org_id=org.id, role=role))
                await session.commit()

    return {"status": "ok"}
