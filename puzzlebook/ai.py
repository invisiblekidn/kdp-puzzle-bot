"""Cloudflare Workers AI: texts and pictures for a theme the author types.

Free plan: 10,000 "neurons" a day (resets at 00:00 UTC), enough for several themes. Keys live in .env:
CF_ACCOUNT_ID (the account id from the Cloudflare dashboard) and CF_API_TOKEN (a token from the "Workers AI"
template). FLUX.1 [schnell] is Apache 2.0, so its pictures may be used in books for sale.
"""
import base64
import io
import json
import os
import re

import httpx
from PIL import Image

TEXT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"


class AIError(RuntimeError):
    """Something the author should read (in Russian)."""


class LimitReached(AIError):
    pass


def _keys():
    acc = os.getenv("CF_ACCOUNT_ID", "").strip()
    tok = os.getenv("CF_API_TOKEN", "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{32}", acc) or len(tok) < 20:
        return None
    return acc, tok


def configured():
    return _keys() is not None


def _run(model, payload, timeout=120):
    keys = _keys()
    if not keys:
        raise AIError("Нейросеть не подключена: в файле .env нет CF_ACCOUNT_ID и CF_API_TOKEN.")
    acc, tok = keys
    url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{model}"
    try:
        r = httpx.post(url, headers={"Authorization": f"Bearer {tok}"}, json=payload, timeout=timeout)
    except httpx.HTTPError as e:
        raise AIError(f"Нет связи с Cloudflare ({type(e).__name__}). Проверьте интернет и попробуйте ещё раз.")
    try:
        data = r.json()
    except ValueError:
        data = {}
    errors = data.get("errors") or []
    text = " ".join(str(e.get("message", "")) for e in errors).lower()
    if r.status_code == 429 or "neurons" in text or any(e.get("code") in (4006, 3036) for e in errors):
        raise LimitReached("Бесплатный дневной лимит нейросети Cloudflare закончился. "
                           "Он обновится в 00:00 по UTC (03:00 по Москве).")
    if r.status_code in (401, 403) or any(e.get("code") in (10000, 9109) for e in errors):
        raise AIError("Cloudflare не принял ключ. Проверьте CF_ACCOUNT_ID и CF_API_TOKEN в .env "
                      "(токен из шаблона «Workers AI»).")
    if r.status_code >= 400 or not data.get("success", False):
        raise AIError(f"Cloudflare вернул ошибку {r.status_code}: {text[:200] or r.text[:200]}")
    return data["result"]


def _json_from(reply):
    if isinstance(reply, dict):
        return reply
    m = re.search(r"\{.*\}", str(reply), re.S)
    if not m:
        raise AIError("Нейросеть ответила не в том формате. Попробуйте ещё раз.")
    try:
        return json.loads(m.group(0))
    except ValueError:
        raise AIError("Нейросеть ответила не в том формате. Попробуйте ещё раз.")


def chat_json(system, user, max_tokens=2500):
    payload = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "max_tokens": max_tokens, "temperature": 0.7, "response_format": {"type": "json_object"}}
    try:
        result = _run(TEXT_MODEL, payload)
    except AIError as e:
        if isinstance(e, LimitReached) or "ключ" in str(e) or "связи" in str(e):
            raise
        payload.pop("response_format")                  # JSON mode refused: ask for plain text with JSON inside
        result = _run(TEXT_MODEL, payload)
    return _json_from(result.get("response", result))


def picture(prompt, seed, steps=6):
    try:
        result = _run(IMAGE_MODEL, {"prompt": prompt, "steps": steps, "seed": seed}, timeout=180)
    except AIError as e:
        if isinstance(e, LimitReached) or "ключ" in str(e) or "связи" in str(e):
            raise
        result = _run(IMAGE_MODEL, {"prompt": prompt, "steps": steps}, timeout=180)
    try:
        return Image.open(io.BytesIO(base64.b64decode(result["image"]))).convert("RGB")
    except (KeyError, ValueError, OSError):
        raise AIError("Нейросеть не прислала картинку. Попробуйте ещё раз.")
