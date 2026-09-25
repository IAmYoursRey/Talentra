import io
import html
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as PlatypusImage,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm

from ..core.cv_security import derive_snapshot_fingerprint
from .qr_generator import VerificationQRGenerator


# Brand Color Palette
INDIGO_DARK = colors.HexColor("#1E1B4B")
INDIGO_PRIMARY = colors.HexColor("#312E81")
TEAL_PRIMARY = colors.HexColor("#0D9488")
SLATE_DARK = colors.HexColor("#1E293B")
SLATE_TEXT = colors.HexColor("#334155")
SLATE_MUTED = colors.HexColor("#64748B")
SLATE_BORDER = colors.HexColor("#CBD5E1")
BG_CARD = colors.HexColor("#F8FAFC")


class CVPdfRenderer:
    """
    Abstract interface for deterministic CV PDF rendering.
    """
    def render(
        self,
        snapshot: Dict[str, Any],
        display_code: str,
        verification_token: str,
        issued_date: str,
    ) -> bytes:
        raise NotImplementedError


class ReportLabCVRenderer(CVPdfRenderer):
    """
    Native Python PDF renderer generating real selectable, searchable, printable text.
    Implements clean A4 layout, TALENTRA brand styling, QR code embedding, and strict PII isolation.
    """

    def __init__(self, renderer_version: str = "cv-pdf-v1"):
        self.renderer_version = renderer_version

    def _sanitize(self, text: Any) -> str:
        if text is None:
            return ""
        return html.escape(str(text))

    def render(
        self,
        snapshot: Dict[str, Any],
        display_code: str,
        verification_token: str,
        issued_date: str,
    ) -> bytes:
        buf = io.BytesIO()

        # Page setup: A4 with 14mm margins
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title="TALENTRA Digital CV",
            author=self._sanitize(snapshot.get("profile", {}).get("display_name", "Siswa TALENTRA")),
            subject="Verified Student Portfolio",
        )

        styles = getSampleStyleSheet()

        # Custom Typography
        style_brand = ParagraphStyle(
            "BrandHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=TEAL_PRIMARY,
            spaceAfter=2,
        )

        style_title = ParagraphStyle(
            "StudentName",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=INDIGO_DARK,
            spaceAfter=3,
        )

        style_school = ParagraphStyle(
            "SchoolClass",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=SLATE_MUTED,
            spaceAfter=8,
        )

        style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=INDIGO_PRIMARY,
            spaceBefore=8,
            spaceAfter=4,
        )

        style_summary = ParagraphStyle(
            "SummaryText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=SLATE_TEXT,
            spaceAfter=6,
        )

        style_project_title = ParagraphStyle(
            "ProjectTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=INDIGO_DARK,
        )

        style_project_meta = ParagraphStyle(
            "ProjectMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=SLATE_MUTED,
        )

        style_project_desc = ParagraphStyle(
            "ProjectDesc",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=SLATE_TEXT,
        )

        style_tags = ParagraphStyle(
            "ProjectTags",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=TEAL_PRIMARY,
        )

        style_badge = ParagraphStyle(
            "SkillBadge",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=SLATE_DARK,
        )

        style_badge_sub = ParagraphStyle(
            "SkillBadgeSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=SLATE_MUTED,
        )

        style_verif_heading = ParagraphStyle(
            "VerifHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=INDIGO_PRIMARY,
        )

        style_verif_body = ParagraphStyle(
            "VerifBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=SLATE_TEXT,
        )

        style_verif_code = ParagraphStyle(
            "VerifCode",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=INDIGO_DARK,
        )

        story = []

        profile = snapshot.get("profile", {})
        display_name = self._sanitize(profile.get("display_name", "Siswa TALENTRA"))
        school_name = self._sanitize(profile.get("school_name", ""))
        class_name = self._sanitize(profile.get("class_name", ""))
        summary = self._sanitize(profile.get("professional_summary", ""))

        # 1. Header Banner
        story.append(Paragraph("TALENTRA.ID &bull; DIGITAL CV TERVALIDASI", style_brand))
        story.append(Paragraph(display_name, style_title))

        school_line = school_name
        if class_name:
            school_line = f"{school_name} &bull; Kelas {class_name}"
        if school_line:
            story.append(Paragraph(school_line, style_school))

        story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceBefore=2, spaceAfter=6))

        # 2. Ringkasan Profil (Professional Summary)
        if summary:
            story.append(Paragraph("Ringkasan Profil", style_section_heading))
            story.append(Paragraph(summary, style_summary))
            story.append(Spacer(1, 4))

        # 3. Keterampilan Tervalidasi (Approved Skills)
        skills: List[Dict[str, Any]] = snapshot.get("approved_skills", [])
        if skills:
            story.append(Paragraph("Keterampilan Tervalidasi", style_section_heading))

            # Group skills into 3 columns table
            skill_cells = []
            row = []
            for s in skills:
                name = self._sanitize(s.get("name") or s.get("dimension") or "")
                score = s.get("score", 0)
                level = self._sanitize(s.get("level") or f"Indeks Bukti: {score}")
                cell_p = [
                    Paragraph(f"<b>{name}</b>", style_badge),
                    Paragraph(level, style_badge_sub),
                ]
                row.append(cell_p)
                if len(row) == 3:
                    skill_cells.append(row)
                    row = []
            if row:
                while len(row) < 3:
                    row.append("")
                skill_cells.append(row)

            if skill_cells:
                avail_width = A4[0] - 28 * mm
                col_w = avail_width / 3.0
                skill_table = Table(skill_cells, colWidths=[col_w, col_w, col_w])
                skill_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
                        ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ])
                )
                story.append(skill_table)
                story.append(Spacer(1, 6))

        # 4. Rekam Jejak Karya Tervalidasi (Selected Portfolios)
        portfolios: List[Dict[str, Any]] = snapshot.get("selected_portfolios", [])
        if portfolios:
            story.append(Paragraph("Rekam Jejak Karya Tervalidasi", style_section_heading))

            for p in portfolios:
                p_title = self._sanitize(p.get("title", "Karya Tervalidasi"))
                p_type = self._sanitize(p.get("activity_type", ""))
                p_date = self._sanitize(p.get("activity_date", ""))
                p_desc = self._sanitize(
                    p.get("professional_description")
                    or p.get("description")
                    or ""
                )
                tags = [self._sanitize(t) for t in p.get("tags", []) if t]

                meta_text = p_type
                if p_date:
                    meta_text = f"{p_type} &bull; {p_date}" if meta_text else p_date

                p_flowables = [
                    Paragraph(f"&bull; <b>{p_title}</b>", style_project_title),
                ]
                if meta_text:
                    p_flowables.append(Paragraph(meta_text, style_project_meta))
                if p_desc:
                    p_flowables.append(Spacer(1, 2))
                    p_flowables.append(Paragraph(p_desc, style_project_desc))
                if tags:
                    tag_line = "Tag: " + " &bull; ".join(tags)
                    p_flowables.append(Paragraph(tag_line, style_tags))
                p_flowables.append(Spacer(1, 4))

                story.append(KeepTogether(p_flowables))

        # 5. Teacher-Validated Competencies (if present)
        teacher_comps: List[Dict[str, Any]] = snapshot.get("teacher_validated_competencies", [])
        if teacher_comps:
            story.append(Paragraph("Kompetensi Tervalidasi Guru", style_section_heading))
            comp_rows = []
            for tc in teacher_comps:
                dim_name = self._sanitize(tc.get("dimension", ""))
                score = tc.get("average_score") or tc.get("score") or ""
                summary_obs = self._sanitize(tc.get("summary") or tc.get("level") or "")
                comp_rows.append([
                    Paragraph(f"<b>{dim_name}</b>", style_badge),
                    Paragraph(f"Skor: {score}" if score != "" else "", style_badge_sub),
                    Paragraph(summary_obs, style_project_desc),
                ])
            avail_w = A4[0] - 28 * mm
            comp_table = Table(comp_rows, colWidths=[avail_w * 0.3, avail_w * 0.2, avail_w * 0.5])
            comp_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
                    ("BOX", (0, 0), (-1, -1), 0.5, SLATE_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(comp_table)
            story.append(Spacer(1, 6))

        # 6. Optional Exploration Summary (if opted in)
        exploration = snapshot.get("optional_exploration_summary")
        if exploration and isinstance(exploration, dict):
            story.append(Paragraph("Bidang yang Sedang Dieksplorasi", style_section_heading))
            story.append(Paragraph(
                "<i>Bidang eksplorasi berdasarkan karya tervalidasi:</i>",
                style_project_meta,
            ))
            career_items = [self._sanitize(c) for c in exploration.get("career_interests", []) if c]
            study_items = [self._sanitize(s) for s in exploration.get("study_interests", []) if s]

            expl_p = []
            if career_items:
                expl_p.append(f"<b>Karier:</b> {', '.join(career_items)}")
            if study_items:
                expl_p.append(f"<b>Pendidikan Lanjutan:</b> {', '.join(study_items)}")
            if expl_p:
                story.append(Paragraph(" &bull; ".join(expl_p), style_project_desc))
            story.append(Spacer(1, 6))

        # 7. Verification Banner & QR (Mandatory)
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1, color=TEAL_PRIMARY, spaceBefore=4, spaceAfter=4))

        # Generate QR PNG Bytes
        qr_bytes = VerificationQRGenerator.generate_qr_png_bytes(verification_token, box_size=4, border=1)
        qr_buf = io.BytesIO(qr_bytes)
        qr_img = PlatypusImage(qr_buf, width=2.5 * cm, height=2.5 * cm)

        content_digest = snapshot.get("content_digest", "")
        fingerprint = derive_snapshot_fingerprint(content_digest)

        verif_left_content = [
            Paragraph("VERIFIKASI KEASLIAN DOKUMEN &bull; TALENTRA.ID", style_verif_heading),
            Paragraph(
                "Dokumen ini diterbitkan dari rekam jejak karya yang telah divalidasi oleh pihak sekolah "
                "melalui platform TALENTRA.ID. Pindai QR code di sebelah kanan untuk memverifikasi keaslian "
                "dokumen secara publik.",
                style_verif_body,
            ),
            Spacer(1, 2),
            Paragraph(f"Kode Dokumen: <b>{self._sanitize(display_code)}</b>", style_verif_code),
            Paragraph(f"Tanggal Terbit: {self._sanitize(issued_date)} &bull; Sidik Jari Dokumen: <b>{fingerprint}</b>", style_verif_body),
        ]

        avail_width = A4[0] - 28 * mm
        verif_table = Table(
            [[verif_left_content, qr_img]],
            colWidths=[avail_width - 2.8 * cm, 2.8 * cm],
        )
        verif_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
                ("BOX", (0, 0), (-1, -1), 0.75, TEAL_PRIMARY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(KeepTogether([verif_table]))

        # Build PDF
        doc.build(story)
        return buf.getvalue()
