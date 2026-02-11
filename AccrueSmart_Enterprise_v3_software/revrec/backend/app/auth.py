# Dummy auth.py to allow the application to start without a real authentication system.

def require(perms: list):
    def decorator(func):
        return func
    return decorator

async def build_principal(request):
    """
    Dummy function to mock a principal.
    In a real app, this would decode a JWT from the request header.
    """
    return {"sub": "mock_user_id", "email": "test@example.com"}
