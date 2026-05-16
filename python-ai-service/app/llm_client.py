from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.config import settings


class LLMClient:
    """DashScope OpenAI-compatible LLM client.

    Uses the official `OpenAI` SDK in compatible-mode and returns a review
    object compatible with the backend's existing response schema.
    """

    def __init__(self):
        self.enabled = bool(settings.external_ai_enabled)
        self.base_url = settings.external_ai_base_url
        self.api_key = settings.external_ai_api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = settings.external_ai_model
        self.enable_thinking = settings.external_ai_enable_thinking
        self.provider = settings.external_ai_provider
        self.client = None
        if self.enabled and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _build_prompt(self, application: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> str:
        knowledge_lines = []
        for idx, hit in enumerate(knowledge_hits, start=1):
            content = str(hit.get("content", ""))
            knowledge_lines.append(f"[{idx}] {content[:500]}")

        knowledge_text = "\n".join(knowledge_lines) if knowledge_lines else "无"

        return (
            "你是涉水审批智能审核助手。请严格输出 JSON，不要输出 markdown。\\n"
            "JSON 字段要求：\\n"
            "- status: APPROVED 或 REJECTED\\n"
            "- message: 简要结论\\n"
            "- suggestions: 字符串数组\\n"
            "- details: 对象，至少包含 regulation_basis(数组) 与 reasoning(字符串)\\n\\n"
            f"申请数据：{json.dumps(application, ensure_ascii=False)}\\n"
            f"法规片段：{knowledge_text}\\n"
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    def _normalize_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        status = str(payload.get("status", "PENDING")).upper()
        if status not in {"APPROVED", "REJECTED", "PENDING", "ERROR"}:
            status = "PENDING"

        suggestions = payload.get("suggestions")
        if not isinstance(suggestions, list):
            suggestions = []

        details = payload.get("details")
        if not isinstance(details, dict):
            details = {}

        return {
            "status": status,
            "message": str(payload.get("message", "外部AI已返回结果")),
            "suggestions": [str(item) for item in suggestions],
            "details": details,
        }

    def generate_review(self, application: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Call external AI and return normalized review schema.

        Returns None if external AI is disabled or not configured.
        Returns {"error": ...} when call/parsing fails.
        """
        if not self.enabled:
            return None
        if not self.client:
            return {"error": "external ai enabled but missing api key (set EXTERNAL_AI_API_KEY or DASHSCOPE_API_KEY)"}

        try:
            prompt = self._build_prompt(application, knowledge_hits)
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": bool(self.enable_thinking)},
                stream=False,
            )

            text = ""
            if completion and completion.choices:
                message = completion.choices[0].message
                text = message.content or ""

            parsed = self._extract_json(text)
            if not parsed:
                return {
                    "error": "external ai response is not valid JSON",
                    "raw": text,
                }

            return self._normalize_result(parsed)
        except Exception as e:
            return {"error": str(e)}


llm_client = LLMClient()
