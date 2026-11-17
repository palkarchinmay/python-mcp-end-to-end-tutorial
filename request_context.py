from contextvars import ContextVar


correlation_id_var = ContextVar(
    "correlation_id",
    default=None,
)
role_var = ContextVar(
    "authenticated_role",
    default=None,
)