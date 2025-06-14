
from pydantic import BaseModel
from typing import Any, Optional

class Service_Response_Model(BaseModel):
    data: Any
    message: Optional[str] = None
    status_code: Optional[int] = None
    is_success: bool
    