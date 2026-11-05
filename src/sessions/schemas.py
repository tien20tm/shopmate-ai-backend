from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    path: str = Field(
        max_length=200,
        pattern=r"^/[\x21-\x7e]*$",
    )

    # Hostname only. An empty value means the visitor came in directly.
    referrer: str = Field(
        default="",
        max_length=253,
        pattern=r"^[a-zA-Z0-9.-]*$",
    )
