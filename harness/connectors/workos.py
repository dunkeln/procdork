from __future__ import annotations

import jwt
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from jwt import PyJWKClient


class WorkOSTokenVerifier:
    def __init__(self, issuer: str, audience: str) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks = PyJWKClient(f"{self.issuer}/oauth2/jwks")

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.PyJWTError:
            return None

        scopes = claims.get("scope") or ""
        return AccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("azp") or "",
            scopes=scopes.split() if isinstance(scopes, str) else scopes,
            expires_at=claims.get("exp"),
            resource=self.audience,
            subject=claims.get("sub"),
            claims=claims,
        )


def workos_auth(issuer: str | None, resource: str | None) -> dict[str, object]:
    if not issuer and not resource:
        return {}
    if not issuer or not resource:
        raise RuntimeError(
            "WORKOS_AUTHKIT_DOMAIN and MCP_RESOURCE_URL must be configured together"
        )
    return {
        "token_verifier": WorkOSTokenVerifier(issuer, resource),
        "auth": AuthSettings(issuer_url=issuer, resource_server_url=resource),
    }
