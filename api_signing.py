from __future__ import annotations
import os
import time
import hashlib
from typing import Tuple, Optional

def make_signature(api_key: str, secret: str, ts: Optional[int] = None) -> Tuple[str, int]:
    if not api_key:
        raise ValueError("api_key is required for signature")
    if not secret:
        raise ValueError("secret is required for signature")
    ts_used = int(ts if ts is not None else time.time())
    material = f"{api_key}{secret}{ts_used}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return digest, ts_used