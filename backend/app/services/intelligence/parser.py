"""Resume parser: PDF/DOCX → structured JSON.

Extracts contact info, summary, work experience, education, skills,
and projects from uploaded resume files. Adapted from Resume-Matcher's
parser.py (32KB) with async wrapper.
"""

from __future__ import annotations

import io
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Section header patterns for detecting resume sections
_SECTION_PATTERNS: dict[str, list[str]] = {
    "summary": ["summary", "objective", "profile", "about me", "professional summary"],
    "workExperience": ["experience", "work history", "employment", "professional experience", "work experience"],
    "education": ["education", "academic", "degree", "qualification", "academic background"],
    "skills": ["skills", "technologies", "competencies", "technical skills", "tools", "tech stack"],
    "projects": ["projects", "personal projects", "portfolio", "side projects"],
    "certifications": ["certifications", "licenses", "credentials"],
}

# Contact extraction patterns
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?")
_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?")


async def parse_resume_file(content: bytes, file_type: str) -> dict[str, Any]:
    """Parse a resume file into structured JSON.

    Args:
        content: Raw file bytes.
        file_type: 'pdf' or 'docx'.

    Returns:
        {
            "structured": { contact, summary, workExperience, education, skills, projects },
            "markdown": str,
            "raw_text": str,
        }
    """
    if file_type == "pdf":
        raw_text = _extract_text_from_pdf(content)
    elif file_type == "docx":
        raw_text = _extract_text_from_docx(content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    structured = _parse_text_to_structured(raw_text)
    markdown = _structured_to_markdown(structured)

    return {
        "structured": structured,
        "markdown": markdown,
        "raw_text": raw_text,
    }


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())
    return "\n".join(paragraphs)


def _extract_contact(text: str) -> dict[str, Any]:
    """Extract contact information from resume text."""
    lines = text.split("\n")
    contact: dict[str, Any] = {}

    # Name is typically the first non-empty line
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) < 60 and not _EMAIL_RE.search(stripped):
            contact["name"] = stripped
            break

    email_match = _EMAIL_RE.search(text)
    if email_match:
        contact["email"] = email_match.group()

    phone_match = _PHONE_RE.search(text)
    if phone_match:
        contact["phone"] = phone_match.group()

    linkedin_match = _LINKEDIN_RE.search(text)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group()

    github_match = _GITHUB_RE.search(text)
    if github_match:
        contact["github"] = github_match.group()

    return contact


def _detect_section(line: str) -> str | None:
    """Detect if a line is a section header. Returns the section key or None."""
    cleaned = line.strip().lower()
    # Remove common decorations
    cleaned = re.sub(r"^[─━═▬\-_*#]+\s*", "", cleaned)
    cleaned = re.sub(r"\s*[─━═▬\-_*#]+$", "", cleaned)
    cleaned = cleaned.strip(": ")

    if not cleaned or len(cleaned) > 40:
        return None

    for section_key, patterns in _SECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern in cleaned:
                return section_key
    return None


def _parse_text_to_structured(text: str) -> dict[str, Any]:
    """Parse raw resume text into structured sections."""
    contact = _extract_contact(text)
    lines = text.split("\n")

    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in lines:
        detected = _detect_section(line)
        if detected:
            # Save the previous section
            if current_section and current_lines:
                sections[current_section] = current_lines
            current_section = detected
            current_lines = []
        elif current_section:
            if line.strip():
                current_lines.append(line.strip())

    # Save the last section
    if current_section and current_lines:
        sections[current_section] = current_lines

    # Build structured output
    structured: dict[str, Any] = {"contact": contact}

    if "summary" in sections:
        structured["summary"] = " ".join(sections["summary"])

    if "workExperience" in sections:
        structured["workExperience"] = _parse_experience_entries(sections["workExperience"])

    if "education" in sections:
        structured["education"] = _parse_education_entries(sections["education"])

    if "skills" in sections:
        structured["skills"] = _parse_skills(sections["skills"])

    if "projects" in sections:
        structured["projects"] = _parse_project_entries(sections["projects"])

    if "certifications" in sections:
        structured["certifications"] = sections["certifications"]

    return structured


def _parse_experience_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Parse work experience lines into structured entries."""
    entries: list[dict[str, Any]] = []
    current_entry: dict[str, Any] | None = None

    for line in lines:
        # Heuristic: lines with dates or all-caps are likely new entries
        if _looks_like_entry_header(line):
            if current_entry:
                entries.append(current_entry)
            current_entry = {"title": line, "bullets": []}
        elif current_entry:
            # Check if it's a bullet point
            cleaned = re.sub(r"^\s*[•\-*]\s*", "", line)
            if cleaned:
                current_entry.setdefault("bullets", []).append(cleaned)

    if current_entry:
        entries.append(current_entry)

    return entries


def _parse_education_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Parse education lines into structured entries."""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in lines:
        if _looks_like_entry_header(line):
            if current:
                entries.append(current)
            current = {"text": line}
        elif current:
            current["text"] += f" {line}"

    if current:
        entries.append(current)

    return entries if entries else [{"text": " ".join(lines)}]


def _parse_skills(lines: list[str]) -> list[str]:
    """Parse skills into a flat list."""
    skills: list[str] = []
    for line in lines:
        # Split on common delimiters
        parts = re.split(r"[,;|•·]", line)
        for part in parts:
            cleaned = part.strip().strip("-•* ")
            if cleaned and len(cleaned) < 50:
                skills.append(cleaned)
    return skills


def _parse_project_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Parse project entries."""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in lines:
        if _looks_like_entry_header(line):
            if current:
                entries.append(current)
            current = {"name": line, "bullets": []}
        elif current:
            cleaned = re.sub(r"^\s*[•\-*]\s*", "", line)
            if cleaned:
                current.setdefault("bullets", []).append(cleaned)

    if current:
        entries.append(current)
    return entries


def _looks_like_entry_header(line: str) -> bool:
    """Heuristic: is this line an entry header (company/title/date)?"""
    stripped = line.strip()
    if not stripped:
        return False
    # Contains a year
    if re.search(r"\b(19|20)\d{2}\b", stripped):
        return True
    # Short line with title-case (likely a company or position)
    if len(stripped) < 80 and stripped[0].isupper() and "|" in stripped:
        return True
    # Starts with bullet → not a header
    if stripped[0] in "•-*":
        return False
    return False


def _structured_to_markdown(structured: dict[str, Any]) -> str:
    """Convert structured resume data to Markdown."""
    parts: list[str] = []

    contact = structured.get("contact", {})
    if contact.get("name"):
        parts.append(f"# {contact['name']}\n")
    contact_items = []
    for key in ["email", "phone", "linkedin", "github"]:
        if contact.get(key):
            contact_items.append(contact[key])
    if contact_items:
        parts.append(" | ".join(contact_items) + "\n")

    if structured.get("summary"):
        parts.append(f"## Summary\n\n{structured['summary']}\n")

    if structured.get("workExperience"):
        parts.append("## Experience\n")
        for entry in structured["workExperience"]:
            parts.append(f"### {entry.get('title', '')}\n")
            for bullet in entry.get("bullets", []):
                parts.append(f"- {bullet}")
            parts.append("")

    if structured.get("education"):
        parts.append("## Education\n")
        for entry in structured["education"]:
            parts.append(f"- {entry.get('text', '')}")
        parts.append("")

    if structured.get("skills"):
        parts.append("## Skills\n")
        parts.append(", ".join(structured["skills"]))
        parts.append("")

    if structured.get("projects"):
        parts.append("## Projects\n")
        for entry in structured["projects"]:
            parts.append(f"### {entry.get('name', '')}\n")
            for bullet in entry.get("bullets", []):
                parts.append(f"- {bullet}")
            parts.append("")

    return "\n".join(parts)
