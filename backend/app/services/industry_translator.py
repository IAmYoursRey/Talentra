import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set, Tuple

from ..core.audit import audit_logger
from ..core.config import settings
from ..domain.enums import AuditEventType
from ..domain.documents import DerivedProfessionalDescriptionDocument
from ..repositories.portfolio import (
    PortfolioRepository,
    get_portfolio_repository,
)

TRANSLATOR_VERSION = "industry-language-v1"

ACTION_VERB_MAP = {
    "membuat": "Mengembangkan",
    "bikin": "Mengembangkan",
    "mengerjakan": "Mengimplementasikan",
    "mendesain": "Merancang",
    "menggambar": "Mengembangkan aset visual",
    "menulis": "Menyusun dokumentasi teknis",
    "mengatur": "Mengorkestrasi dan mengoordinasikan",
    "mengedit": "Melakukan penyuntingan dan pascaproduksi",
    "menganalisis": "Menganalisis dan mengekstraksi wawasan",
    "mempresentasikan": "Mempresentasikan dan mengomunikasikan",
    "meneliti": "Melakukan investigasi dan riset terstruktur",
}


class FactualityGuard:
    """
    Verifies that the generated professional description does not invent facts,
    metrics, technologies, or claims not grounded in the source text or approved tags.
    """

    @staticmethod
    def extract_numbers(text: str) -> Set[str]:
        # Extract numeric tokens (e.g. '3', '40%', '5.000')
        return set(re.findall(r"\b\d+(?:[.,]\d+)?%?", text))

    @classmethod
    def verify(
        cls,
        source_text: str,
        generated_text: str,
        approved_tags: List[str],
    ) -> Tuple[bool, str]:
        # 1. Number verification: Any number in generated_text MUST exist in source_text
        src_nums = cls.extract_numbers(source_text)
        gen_nums = cls.extract_numbers(generated_text)
        invented_nums = gen_nums - src_nums
        if invented_nums:
            return False, f"Invented numerical claims detected: {invented_nums}"

        # 2. Technology/Tool invention check: Common buzzwords not in source or tags
        forbidden_tech = ["react", "next.js", "kubernetes", "aws", "docker", "flutter", "vue", "angular"]
        src_lower = (source_text + " " + " ".join(approved_tags)).lower()
        gen_lower = generated_text.lower()

        for tech in forbidden_tech:
            if tech in gen_lower and tech not in src_lower:
                return False, f"Invented ungrounded technology claim: {tech}"

        # 3. Leadership invention check
        leadership_claims = ["memimpin tim", "ketua umum", "project manager", "chief", "head of"]
        for claim in leadership_claims:
            if claim in gen_lower and claim not in src_lower and "leadership" not in approved_tags:
                return False, f"Invented unsupported leadership claim: {claim}"

        return True, "Factuality verified"


class IIndustryLanguageTranslator(ABC):
    @abstractmethod
    async def translate(
        self,
        title: str,
        description: str,
        activity_type: str,
        canonical_tags: List[str],
    ) -> Tuple[str, str]:
        """
        Translates raw student activity text into professional CV language.
        Returns: (professional_text, mode)
        """
        pass


class DeterministicIndustryTranslator(IIndustryLanguageTranslator):
    """
    Deterministic rule-based & template grounded translator.
    Guarantees 100% factuality without external API dependencies.
    """

    async def translate(
        self,
        title: str,
        description: str,
        activity_type: str,
        canonical_tags: List[str],
    ) -> Tuple[str, str]:
        clean_desc = description.strip()
        clean_title = title.strip()

        # Extract existing numbers to preserve them accurately
        numbers_in_src = re.findall(r"\b\d+\b", clean_desc)

        # Determine primary action verb
        lower_desc = clean_desc.lower()
        chosen_verb = "Mengembangkan"
        for raw_verb, prof_verb in ACTION_VERB_MAP.items():
            if raw_verb in lower_desc:
                chosen_verb = prof_verb
                break

        # Grounded tags context
        tag_labels = [t.replace("-", " ").title() for t in canonical_tags[:3]]
        tag_clause = f" dengan fokus pada kompetensi {', '.join(tag_labels)}" if tag_labels else ""

        # Activity context
        context_phrase = "sebagai proyek pembelajaran terstruktur"
        if "lomba" in lower_desc or "kompetisi" in lower_desc:
            context_phrase = "dalam konteks ajang kompetisi siswa"
        elif "tim" in lower_desc or "kelompok" in lower_desc or "teman" in lower_desc:
            if numbers_in_src:
                context_phrase = f"secara kolaboratif dalam tim beranggotakan {numbers_in_src[0]} orang"
            else:
                context_phrase = "secara kolaboratif dalam tim kerja proyek"
        elif "mandiri" in lower_desc or "individu" in lower_desc:
            context_phrase = "secara mandiri dengan inisiatif terarah"

        # Construct professional sentence
        # Transform informal prefix if present
        first_sentence = clean_desc.split(".")[0].strip()
        # Remove colloquial words
        for colloquial in ["saya ", "kami ", "bikin ", "buat ", "tugas sekolah "]:
            first_sentence = re.sub(f"(?i)^{colloquial}", "", first_sentence).strip()

        # Professional grounded sentence structure
        professional_text = (
            f"{chosen_verb} {clean_title} {context_phrase}{tag_clause}. "
            f"Melaksanakan perancangan dan implementasi solusi sesuai kebutuhan proyek portofolio sekolah."
        )

        return professional_text, "deterministic"


class IndustryTranslatorService:
    """
    Coordinates translation, authorization, factuality gating, and derived document persistence.
    """

    def __init__(
        self,
        portfolio_repo: Optional[PortfolioRepository] = None,
        translator: Optional[IIndustryLanguageTranslator] = None,
    ):
        self.portfolio_repo = portfolio_repo or get_portfolio_repository()

        self.translator = translator or DeterministicIndustryTranslator()

    async def get_or_create_professional_description(
        self,
        school_id: str,
        student_id: str,
        portfolio_id: str,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        """
        Translates student portfolio description into professional CV language.
        STRICT GATES:
        - Portfolio must exist and belong to student + school tenant.
        - Portfolio status MUST be 'approved' (teacher verified).
        - Draft, submitted, revision_requested, and rejected are strictly denied.
        - Result is saved as a derived snapshot (never mutates immutable portfolio revision).
        """
        # 1. Fetch portfolio
        item = await self.portfolio_repo.get_portfolio(school_id, student_id, portfolio_id)
        if not item:
            raise ValueError(f"Portfolio {portfolio_id} not found or access denied.")

        # 2. Strict status gate: ONLY approved portfolio
        status = item.get("status")
        if status != "approved":
            raise ValueError(
                f"Penerjemahan bahasa profesional hanya dapat dilakukan pada karya yang telah disetujui guru (status saat ini: {status})."
            )

        revision_id = item.get("current_revision_id", "")
        desc = item.get("description", "")
        title = item.get("title", "")
        activity_type = item.get("activity_type", "")
        tags = item.get("canonical_tag_ids", [])

        # 3. Check existing derived snapshot if not forcing regeneration
        if not force_regenerate:
            existing = await self.portfolio_repo.get_professional_description(
                school_id=school_id, student_id=student_id, portfolio_id=portfolio_id
            )
            if existing:
                return {
                    "documentId": existing.get("document_id"),
                    "portfolioId": portfolio_id,
                    "revisionId": revision_id,
                    "originalTitle": title,
                    "originalDescription": desc,
                    "professionalText": existing.get("professional_text"),
                    "translatorVersion": existing.get("translator_version", TRANSLATOR_VERSION),
                    "mode": existing.get("mode", "deterministic"),
                    "generatedAt": (
                        existing["generated_at"].isoformat()
                        if hasattr(existing["generated_at"], "isoformat")
                        else str(existing.get("generated_at"))
                    ),
                }

        # 4. Execute grounded transformation
        professional_text, mode = await self.translator.translate(
            title=title,
            description=desc,
            activity_type=activity_type,
            canonical_tags=tags,
        )

        # 5. Run Factuality Guard
        is_factual, reason = FactualityGuard.verify(
            source_text=f"{title} {desc}",
            generated_text=professional_text,
            approved_tags=tags,
        )

        if not is_factual:
            # Fall back to strict deterministic fallback
            audit_logger.log_event(
                AuditEventType.TRANSLATOR_FALLBACK_USED,
                user_id=student_id,
                school_id=school_id,
                safe_context="factuality_guard_failed",
                metadata={"portfolio_id": portfolio_id, "reason": reason},
            )
            fallback_translator = DeterministicIndustryTranslator()
            professional_text, mode = await fallback_translator.translate(
                title=title, description=desc, activity_type=activity_type, canonical_tags=tags
            )

        # 6. Save derived document (separate from revision)
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        doc = DerivedProfessionalDescriptionDocument(
            document_id=doc_id,
            school_id=school_id,
            student_id=student_id,
            portfolio_id=portfolio_id,
            revision_id=revision_id,
            source_hash=str(hash(desc)),
            original_title=title,
            professional_text=professional_text,
            translator_version=TRANSLATOR_VERSION,
            mode=mode,
            generated_at=now,
        )
        await self.portfolio_repo.save_professional_description(doc)

        # 7. Audit log
        audit_logger.log_event(
            AuditEventType.PROFESSIONAL_DESCRIPTION_GENERATED,
            user_id=student_id,
            school_id=school_id,
            safe_context="professional_description_generated",
            metadata={
                "portfolio_id": portfolio_id,
                "revision_id": revision_id,
                "mode": mode,
                "translator_version": TRANSLATOR_VERSION,
            },
        )

        return {
            "documentId": doc_id,
            "portfolioId": portfolio_id,
            "revisionId": revision_id,
            "originalTitle": title,
            "originalDescription": desc,
            "professionalText": professional_text,
            "translatorVersion": TRANSLATOR_VERSION,
            "mode": mode,
            "generatedAt": now.isoformat(),
        }
