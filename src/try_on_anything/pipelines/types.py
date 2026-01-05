from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class VLModelParsedResult(BaseModel):
    accessory_type: Optional[str] = None
    person_position: Optional[str] = None
    detail_bbox: Optional[Dict[str, float]] = None
    parse_errors: List[str] = []