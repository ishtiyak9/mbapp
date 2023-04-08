from rest_framework_simplejwt.tokens import RefreshToken
from django.core.signing import Signer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


def code_is_valid(email, verification_code):
    signer = Signer()
    full_code = email + ':' + verification_code

    try:
        signer.unsign(full_code)
        return True
    except:
        return False
