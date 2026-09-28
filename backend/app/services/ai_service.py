"""All LLM access lives here. Every structured call is validated with Pydantic and retried once.

Supported providers (AI_PROVIDER):  anthropic  |  openai (any OpenAI-compatible API via AI_BASE_URL)
The AI is used for text understanding/generation only. It never computes mastery or learning debt.
"""
import json
import logging
import re

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.models.enums import Difficulty, QuestionType

logger = logging.getLogger(__name__)

_DIFFICULTY_ALIASES = {
    "basic": "BEGINNER", "easy": "BEGINNER", "introductory": "BEGINNER", "foundational": "BEGINNER",
    "medium": "INTERMEDIATE", "moderate": "INTERMEDIATE",
    "hard": "ADVANCED", "difficult": "ADVANCED", "expert": "ADVANCED",
}


def _normalise_difficulty(v):
    if isinstance(v, str):
        key = v.strip().lower()
        return _DIFFICULTY_ALIASES.get(key, key.upper())
    return v


# ------------------------------------------------------------------ schemas
class ConceptDraft(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    difficulty: Difficulty = Difficulty.BEGINNER
    prerequisites: list[str] = Field(default_factory=list)

    normalise_difficulty = field_validator("difficulty", mode="before")(_normalise_difficulty)


class SyllabusAnalysis(BaseModel):
    concepts: list[ConceptDraft] = Field(min_length=1, max_length=80)


class QuestionDraft(BaseModel):
    question_text: str = Field(min_length=5)
    options: list[str] = Field(min_length=2, max_length=6)
    correct_answer: str
    explanation: str = ""
    difficulty: Difficulty = Difficulty.BEGINNER
    question_type: QuestionType = QuestionType.CONCEPTUAL

    normalise_difficulty = field_validator("difficulty", mode="before")(_normalise_difficulty)

    @field_validator("question_type", mode="before")
    @classmethod
    def _qtype(cls, v):
        if isinstance(v, str):
            key = v.strip().upper().replace(" ", "_").replace("-", "_")
            return key if key in QuestionType.__members__ else "CONCEPTUAL"
        return v

    @field_validator("options", mode="before")
    @classmethod
    def _strip_options(cls, v):
        return [str(o).strip() for o in v] if isinstance(v, list) else v

    @model_validator(mode="after")
    def _answer_must_be_an_option(self):
        if len(set(o.lower() for o in self.options)) != len(self.options):
            raise ValueError("options must be unique")
        answer = self.correct_answer.strip()
        lowered = {o.lower(): o for o in self.options}
        if answer in self.options:
            self.correct_answer = answer
        elif answer.lower() in lowered:
            self.correct_answer = lowered[answer.lower()]
        else:
            m = re.fullmatch(r"\(?([A-Fa-f])[\).:]?", answer)  # "B", "B)", "(b)"
            idx = ord(m.group(1).upper()) - 65 if m else -1
            if 0 <= idx < len(self.options):
                self.correct_answer = self.options[idx]
            else:
                raise ValueError("correct_answer must match one of the options")
        return self


class QuestionBatch(BaseModel):
    questions: list[QuestionDraft] = Field(min_length=1, max_length=20)


class DebtExplanationDraft(BaseModel):
    summary: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    recommended_order: list[str] = Field(default_factory=list)


# --------------------------------------------------------------- LLM plumbing
def _call_llm(system: str, user: str, max_tokens: int = 4096) -> str:
    if not settings.ai_api_key or not settings.ai_model:
        raise AIServiceError("AI is not configured. Set AI_API_KEY and AI_MODEL in the server environment.")
    provider = settings.ai_provider.lower()
    try:
        with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
            if provider == "anthropic":
                resp = client.post(
                    (settings.ai_base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages",
                    headers={"x-api-key": settings.ai_api_key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": settings.ai_model, "max_tokens": max_tokens, "system": system,
                          "messages": [{"role": "user", "content": user}]},
                )
            elif provider == "openai":
                resp = client.post(
                    (settings.ai_base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                    json={"model": settings.ai_model, "max_tokens": max_tokens,
                          "response_format": {"type": "json_object"},
                          "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                )
            else:
                raise AIServiceError(f"Unsupported AI_PROVIDER '{settings.ai_provider}'. Use 'anthropic' or 'openai'.")
    except httpx.HTTPError as exc:
        logger.error("AI request failed: %s", type(exc).__name__)
        raise AIServiceError("The AI service could not be reached. Please try again.") from exc

    if resp.status_code >= 400:
        logger.error("AI provider error %s: %s", resp.status_code, resp.text[:500])
        raise AIServiceError(f"The AI provider returned an error (HTTP {resp.status_code}).")
    try:
        body = resp.json()
        if provider == "anthropic":
            return "".join(b.get("text", "") for b in body["content"] if b.get("type") == "text")
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        logger.error("Unexpected AI response shape: %s", resp.text[:500])
        raise AIServiceError("The AI provider returned an unexpected response.") from exc


def extract_json(raw: str) -> dict:
    """Pull a JSON object out of a model reply (tolerates ```json fences and stray prose)."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in AI reply")
    return json.loads(text[start:end + 1])


def _structured_call(system: str, user: str, model_cls: type[BaseModel], max_tokens: int = 4096) -> BaseModel:
    """Call the LLM, validate against `model_cls`, retry once with the error fed back."""
    last_error = ""
    for attempt in (1, 2):
        prompt = user if attempt == 1 else (
            f"{user}\n\nYour previous reply was rejected: {last_error}\n"
            "Reply again with ONLY one valid JSON object that follows the required schema exactly."
        )
        raw = _call_llm(system, prompt, max_tokens)
        try:
            return model_cls.model_validate(extract_json(raw))
        except ValueError as exc:  # JSONDecodeError and pydantic ValidationError are both ValueErrors
            last_error = str(exc)[:400]
            logger.warning("Invalid AI JSON (attempt %s): %s", attempt, last_error)
    raise AIServiceError("The AI returned an invalid response twice. Please try again.")


# ------------------------------------------------------------- public API
_SYLLABUS_SYSTEM = (
    "You are a curriculum analyst. You read a course syllabus and build a prerequisite concept map. "
    "Reply with ONLY a JSON object, no prose, no markdown."
)


def _fallback_analyze_syllabus(subject_name: str, text: str) -> SyllabusAnalysis:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    extracted: list[tuple[str, str]] = []
    seen: set[str] = set()
    for ln in lines:
        if re.match(r"^(unit|module|chapter|section|week|part)\s+\d+", ln, flags=re.I):
            continue
        if re.match(r"^(assessment|grading|evaluation|textbook|reference|course\s+syllabus)", ln, flags=re.I):
            continue
        cleaned = re.sub(r"^[-*•\d.)]+\s*", "", ln).strip()
        if not cleaned or len(cleaned) < 3:
            continue
        if ":" in cleaned:
            head, desc = cleaned.split(":", 1)
            name, desc = head.strip(), desc.strip()
        elif " - " in cleaned:
            head, desc = cleaned.split(" - ", 1)
            name, desc = head.strip(), desc.strip()
        else:
            words = cleaned.split()
            if len(words) > 6:
                continue
            name, desc = cleaned, f"Core concept in {subject_name}: {cleaned}."
        if 2 <= len(name) <= 80 and name.lower() not in seen:
            seen.add(name.lower())
            extracted.append((name, desc or f"Understanding and applying {name} in {subject_name}."))

    if not extracted:
        chunks = [c.strip() for c in re.split(r"[.;\n]+", text) if len(c.strip()) >= 4]
        for idx, ch in enumerate(chunks[:8], start=1):
            short = " ".join(ch.split()[:4]).strip(",:;-")
            name = short.title() if short else f"{subject_name} Topic {idx}"
            if name.lower() not in seen:
                seen.add(name.lower())
                extracted.append((name, ch[:200]))

    total = len(extracted)
    concepts: list[ConceptDraft] = []
    for idx, (name, desc) in enumerate(extracted[:40]):
        ratio = idx / max(1, total - 1)
        diff = Difficulty.BEGINNER if ratio < 0.4 else (Difficulty.INTERMEDIATE if ratio < 0.8 else Difficulty.ADVANCED)
        prereqs = [concepts[idx - 1].name] if idx > 0 else []
        concepts.append(ConceptDraft(name=name, description=desc, difficulty=diff, prerequisites=prereqs))
    return SyllabusAnalysis(concepts=concepts)


def analyze_syllabus(subject_name: str, syllabus_text: str) -> SyllabusAnalysis:
    text = syllabus_text[: settings.ai_max_input_chars]
    if not settings.ai_api_key or not settings.ai_model:
        logger.info("AI_API_KEY not set; using built-in curriculum parser for '%s'", subject_name)
        return _fallback_analyze_syllabus(subject_name, text)
    user = f"""Subject: {subject_name}

Extract the teachable concepts from the syllabus below (topics, concepts and important subtopics), in a sensible
teaching order. Rules:
- 5 to 40 concepts; short unique names (2-5 words); no duplicates.
- "difficulty" is one of: beginner, intermediate, advanced.
- "prerequisites" lists names of OTHER concepts from your own list that must be understood first.
  Only add genuine direct prerequisites. Never create circular dependencies. Foundational concepts have [].
- "description" is one clear sentence.

Return exactly this JSON shape:
{{"concepts": [{{"name": "...", "description": "...", "difficulty": "beginner", "prerequisites": ["..."]}}]}}

SYLLABUS:
\"\"\"
{text}
\"\"\""""
    result: SyllabusAnalysis = _structured_call(_SYLLABUS_SYSTEM, user, SyllabusAnalysis, max_tokens=6000)  # type: ignore[assignment]
    return result


_QUESTION_SYSTEM = (
    "You are an expert assessment writer. You write multiple-choice questions that test genuine understanding. "
    "Reply with ONLY a JSON object, no prose, no markdown."
)


def _fallback_generate_questions(
    subject_name: str,
    concept_name: str,
    concept_description: str | None,
    difficulty: Difficulty,
    count: int,
    prerequisite_names: list[str],
) -> list[QuestionDraft]:
    desc = (concept_description or f"core principles and usage of {concept_name} in {subject_name}").rstrip(".")
    prereq_str = ", ".join(prerequisite_names) if prerequisite_names else "foundational concepts"
    templates = [
        (
            f"What is the primary role of {concept_name} in {subject_name}?",
            [
                f"It provides {desc[:110].lower() if desc else f'structured mechanisms for {concept_name.lower()}'}",
                f"It bypasses all syntax and runtime checks in {subject_name}",
                f"It permanently disables {prereq_str} during execution",
                f"It is only used for hardware-level memory formatting",
            ],
            0,
            f"{concept_name} focuses on {desc}.",
            QuestionType.CONCEPTUAL,
        ),
        (
            f"When applying {concept_name} in a practical {subject_name} problem, which approach is most accurate?",
            [
                f"Follow the core rules of {concept_name} while building on {prereq_str}",
                f"Ignore {prereq_str} and rely on uninitialized state",
                f"Replace all logic with hardcoded string literals",
                f"Avoid testing edge cases when using {concept_name}",
            ],
            0,
            f"Correct application of {concept_name} builds upon {prereq_str}.",
            QuestionType.APPLICATION,
        ),
        (
            f"A student encounters unexpected behavior while working with {concept_name}. What is the best first step to diagnose it?",
            [
                f"Verify the assumptions and inputs related to {concept_name} and {prereq_str}",
                f"Delete the entire module without inspecting the error",
                f"Assume {concept_name} cannot handle standard inputs",
                f"Convert all expressions into comments",
            ],
            0,
            f"Checking inputs and prerequisite assumptions ({prereq_str}) isolates issues in {concept_name}.",
            QuestionType.SCENARIO,
        ),
        (
            f"Which common mistake should be avoided when working with {concept_name}?",
            [
                f"Misapplying {concept_name} without satisfying the rules of {prereq_str}",
                f"Writing clear, modular code that uses {concept_name}",
                f"Validating boundary conditions for {concept_name}",
                f"Documenting the expected behavior of {concept_name}",
            ],
            0,
            f"Violating prerequisite rules ({prereq_str}) is a frequent source of bugs in {concept_name}.",
            QuestionType.ERROR_SPOTTING,
        ),
        (
            f"How does {concept_name} relate to {prereq_str} in {subject_name}?",
            [
                f"{concept_name} directly builds upon and extends {prereq_str}",
                f"{concept_name} makes {prereq_str} completely obsolete",
                f"{concept_name} and {prereq_str} cannot be used in the same program",
                f"{concept_name} only runs when {prereq_str} fails",
            ],
            0,
            f"In {subject_name}, {concept_name} builds on {prereq_str}.",
            QuestionType.CONCEPTUAL,
        ),
    ]
    out: list[QuestionDraft] = []
    for i in range(count):
        qtext, opts, correct_idx, expl, qtype = templates[i % len(templates)]
        if i >= len(templates):
            qtext = f"[{i + 1}] {qtext}"
        out.append(
            QuestionDraft(
                question_text=qtext,
                options=opts,
                correct_answer=opts[correct_idx],
                explanation=expl,
                difficulty=difficulty,
                question_type=qtype,
            )
        )
    return out


def generate_questions(subject_name: str, concept_name: str, concept_description: str | None,
                       difficulty: Difficulty, count: int, prerequisite_names: list[str]) -> list[QuestionDraft]:
    if not settings.ai_api_key or not settings.ai_model:
        logger.info("AI_API_KEY not set; using built-in question generator for '%s'", concept_name)
        return _fallback_generate_questions(
            subject_name, concept_name, concept_description, difficulty, count, prerequisite_names
        )
    user = f"""Subject: {subject_name}
Concept: {concept_name}
Concept description: {concept_description or "n/a"}
Prerequisite concepts (context only): {", ".join(prerequisite_names) or "none"}
Target difficulty: {difficulty.value}

Write exactly {count} multiple-choice questions about ONLY the concept "{concept_name}".
Rules:
- Test understanding and application, not memorised definitions. Mix question types where possible:
  CONCEPTUAL, APPLICATION, SCENARIO, TRUE_FALSE, ERROR_SPOTTING.
- 4 options each (2 for TRUE_FALSE: "True" and "False"); exactly one correct; plausible distractors based on
  common misconceptions; options must be unique.
- "correct_answer" must be the exact text of one option.
- "explanation" says briefly why the answer is right.
- "difficulty" is beginner, intermediate or advanced.

Return exactly this JSON shape:
{{"questions": [{{"question_text": "...", "question_type": "CONCEPTUAL", "options": ["...", "...", "...", "..."],
"correct_answer": "...", "explanation": "...", "difficulty": "beginner"}}]}}"""
    batch: QuestionBatch = _structured_call(_QUESTION_SYSTEM, user, QuestionBatch, max_tokens=4096)  # type: ignore[assignment]
    return batch.questions[:count]


_EXPLAIN_SYSTEM = (
    "You are a supportive tutor. You explain a student's knowledge gap in plain, encouraging language. "
    "You must not change or question the numbers you are given. Reply with ONLY a JSON object."
)


def explain_learning_debt(payload: dict) -> DebtExplanationDraft:
    if not settings.ai_api_key or not settings.ai_model:
        weak = payload.get("weak_concept", "this concept")
        mastery = payload.get("mastery", 0)
        deps = payload.get("dependent_concepts") or []
        prereqs = payload.get("weak_prerequisites") or []
        order = prereqs + [weak] + deps
        summary = (
            f"Your current mastery in {weak} is {mastery}%. "
            + (
                f"Because {', '.join(prereqs)} is also weak, strengthening those foundations first will make {weak} much easier."
                if prereqs
                else f"{weak} is a root-cause foundational concept that you should focus on first."
            )
        )
        why = (
            f"Solidifying {weak} directly unlocks {', '.join(deps)}, which depend on it."
            if deps
            else f"Mastering {weak} will complete your understanding of this area of the course."
        )
        return DebtExplanationDraft(summary=summary, why_it_matters=why, recommended_order=order)

    user = f"""Student data (computed by the system; do not alter it):
{json.dumps(payload, indent=2)}

Explain to the student:
- what they are weak in,
- why it matters (which later concepts depend on it),
- what to learn first, and a simple recommendation.
"recommended_order" must use ONLY concept names that appear in the data, prerequisites before dependents.

Return exactly this JSON shape:
{{"summary": "...", "why_it_matters": "...", "recommended_order": ["..."]}}"""
    result: DebtExplanationDraft = _structured_call(_EXPLAIN_SYSTEM, user, DebtExplanationDraft, max_tokens=1200)  # type: ignore[assignment]
    return result

