import json
import requests
from jose import jwt
from jose.exceptions import JWTError
from django.conf import settings
from rest_framework import authentication, exceptions
from types import SimpleNamespace

class Auth0JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization", None)
        if not auth:
            return None

        parts = auth.split()
        if parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed("Authorization header must start with Bearer.")
        elif len(parts) == 1:
            raise exceptions.AuthenticationFailed("Token not found.")
        elif len(parts) > 2:
            raise exceptions.AuthenticationFailed("Authorization header must be Bearer token.")

        token = parts[1]
        try:
            jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
            jwks = requests.get(jwks_url).json()
            unverified_header = jwt.get_unverified_header(token)

            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if not rsa_key:
                raise exceptions.AuthenticationFailed("RSA key not found.")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=settings.ALGORITHMS,
                audience=settings.API_IDENTIFIER,
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
        except JWTError as e:
            raise exceptions.AuthenticationFailed(f"JWT decode error: {str(e)}")

        # Wrap user info
        user = SimpleNamespace(
             is_authenticated=True,
            sub=payload.get("sub"),
            name=payload.get("name"),
            email=payload.get("email"),
        )
        return (user, None)
