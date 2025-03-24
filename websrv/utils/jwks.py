# backend/utils/jwks.py

import requests
from jose import jwt
from jose.exceptions import JWTError

JWKS_URL = "https://dev-o057ijjrl6wtbm32.us.auth0.com/.well-known/jwks.json"
ISSUER = "https://dev-o057ijjrl6wtbm32.us.auth0.com/"
AUDIENCE = "https://billboard.local"

def get_signing_key(token):
    try:
        jwks = requests.get(JWKS_URL).json()
        unverified_header = jwt.get_unverified_header(token)

        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                return jwt.decode(
                    token,
                    key,
                    algorithms=["RS256"],
                    audience=AUDIENCE,
                    issuer=ISSUER,
                )
    except JWTError as e:
        raise Exception("JWT verification failed: " + str(e))
    except Exception as e:
        raise Exception("JWKS key error: " + str(e))
