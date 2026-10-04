"""LaTeX Resume Generator & Compiler (Feature #13 Upgrade).

Adapts logic from:
- 13_pdf_templates_and_ats_validator/generate-latex.mjs
- 13_pdf_templates_and_ats_validator/latex.md
- templates/cv-template.tex

Generates clean, ATS-compliant, recruiter-grade LaTeX code (.tex)
and compiles to PDF using pdflatex/xelatex/tectonic when installed on host.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters to ensure 100% compilation success."""
    if not text:
        return ""
    
    # Replace em-dashes and en-dashes
    clean = text.replace("—", " - ").replace("–", " - ")

    # Map of special LaTeX characters
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]

    for orig, repl in replacements:
        clean = clean.replace(orig, repl)

    return clean


def generate_latex_resume(resume: dict[str, Any]) -> str:
    """Generate professional, ATS-optimized LaTeX source document from structured resume."""
    contact = resume.get("contact", {})
    name = escape_latex(contact.get("name", "Candidate"))
    email = escape_latex(contact.get("email", ""))
    phone = escape_latex(contact.get("phone", ""))
    location = escape_latex(contact.get("location", ""))
    linkedin = escape_latex(contact.get("linkedin", ""))
    github = escape_latex(contact.get("github", ""))

    header_parts = []
    if email:
        header_parts.append(rf"\href{{mailto:{email}}}{{{email}}}")
    if phone:
        header_parts.append(phone)
    if location:
        header_parts.append(location)
    if linkedin:
        clean_li = linkedin.replace("https://www.", "").replace("https://", "").replace("www.", "")
        header_parts.append(rf"\href{{{linkedin}}}{{{clean_li}}}")
    if github:
        clean_gh = github.replace("https://www.", "").replace("https://", "").replace("www.", "")
        header_parts.append(rf"\href{{{github}}}{{{clean_gh}}}")

    contact_line = " $|$ ".join(header_parts)

    lines = [
        r"\documentclass[letterpaper,10pt]{article}",
        r"\usepackage[empty]{fullpage}",
        r"\usepackage{titlesec}",
        r"\usepackage{marvosym}",
        r"\usepackage[usenames,dvipsnames]{color}",
        r"\usepackage{verbatim}",
        r"\usepackage{enumitem}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{fancyhdr}",
        r"\usepackage[english]{babel}",
        r"\usepackage{tabularx}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\renewcommand{\headrulewidth}{0pt}",
        r"\renewcommand{\footrulewidth}{0pt}",
        r"\addtolength{\oddsidemargin}{-0.5in}",
        r"\addtolength{\evensidemargin}{-0.5in}",
        r"\addtolength{\textwidth}{1.0in}",
        r"\addtolength{\topmargin}{-0.5in}",
        r"\addtolength{\textheight}{1.0in}",
        r"\urlstyle{same}",
        r"\raggedbottom",
        r"\raggedright",
        r"\setlength{\tabcolsep}{0in}",
        r"",
        r"% Sections formatting",
        r"\titleformat{\section}{",
        r"  \vspace{-4pt}\scshape\raggedright\large\bfseries",
        r"}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]",
        r"",
        r"% Custom commands",
        r"\newcommand{\resumeItem}[1]{",
        r"  \item\small{",
        r"    {#1 \vspace{-2pt}}",
        r"  }",
        r"}",
        r"",
        r"\newcommand{\resumeSubheading}[4]{",
        r"  \vspace{-2pt}\item",
        r"    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}",
        r"      \textbf{#1} & #2 \\",
        r"      \textit{\small#3} & \textit{\small #4} \\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        r"",
        r"\newcommand{\resumeProjectHeading}[2]{",
        r"    \item",
        r"    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}",
        r"      \small#1 & #2 \\",
        r"    \end{tabular*}\vspace{-7pt}",
        r"}",
        r"",
        r"\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}",
        r"\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}",
        r"\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in]}",
        r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}",
        r"",
        r"\begin{document}",
        r"",
        r"% ── HEADING ──",
        r"\begin{center}",
        rf"    \textbf{{\Huge \scshape {name}}} \\ \vspace{{2pt}}",
        rf"    \small {contact_line}",
        r"\end{center}",
        r"",
    ]

    # Summary
    summary = resume.get("summary")
    if summary:
        lines.extend([
            r"\section{Professional Summary}",
            r"\small{",
            escape_latex(summary),
            r"}\vspace{-2pt}",
            r"",
        ])

    # Work Experience
    experience = resume.get("workExperience", [])
    if experience:
        lines.extend([
            r"\section{Work Experience}",
            r"\resumeSubHeadingListStart",
        ])
        for exp in experience:
            title = escape_latex(exp.get("title", ""))
            company = escape_latex(exp.get("company", ""))
            location_val = escape_latex(exp.get("location", ""))
            years = escape_latex(exp.get("years", ""))

            lines.append(
                rf"  \resumeSubheading{{{title}}}{{{years}}}{{{company}}}{{{location_val}}}"
            )
            bullets = exp.get("bullets", [])
            if bullets:
                lines.append(r"  \resumeItemListStart")
                for bullet in bullets:
                    lines.append(rf"    \resumeItem{{{escape_latex(bullet)}}}")
                lines.append(r"  \resumeItemListEnd")
        lines.extend([
            r"\resumeSubHeadingListEnd",
            r"",
        ])

    # Projects
    projects = resume.get("projects", [])
    if projects:
        lines.extend([
            r"\section{Projects}",
            r"\resumeSubHeadingListStart",
        ])
        for proj in projects:
            pname = escape_latex(proj.get("name", ""))
            prole = escape_latex(proj.get("role", ""))
            bullets = proj.get("bullets", [])
            heading_title = rf"\textbf{{{pname}}}" + (rf" $|$ \emph{{{prole}}}" if prole else "")
            lines.append(rf"  \resumeProjectHeading{{{heading_title}}}{{}}")
            if bullets:
                lines.append(r"  \resumeItemListStart")
                for bullet in bullets:
                    lines.append(rf"    \resumeItem{{{escape_latex(bullet)}}}")
                lines.append(r"  \resumeItemListEnd")
        lines.extend([
            r"\resumeSubHeadingListEnd",
            r"",
        ])

    # Technical Skills
    skills = resume.get("skills", [])
    if skills:
        skills_str = ", ".join([escape_latex(s) for s in skills if isinstance(s, str)])
        lines.extend([
            r"\section{Technical Skills}",
            r"\begin{itemize}[leftmargin=0.15in, label={}]",
            rf"  \small{{\item{{\textbf{{Core Competencies}}: {skills_str}}}}}",
            r"\end{itemize}",
            r"",
        ])

    # Education
    education = resume.get("education", [])
    if education:
        lines.extend([
            r"\section{Education}",
            r"\resumeSubHeadingListStart",
        ])
        for edu in education:
            if isinstance(edu, dict):
                inst = escape_latex(edu.get("institution", ""))
                deg = escape_latex(edu.get("degree", ""))
                yr = escape_latex(edu.get("years", ""))
                loc = escape_latex(edu.get("location", ""))
                lines.append(
                    rf"  \resumeSubheading{{{inst}}}{{{loc}}}{{{deg}}}{{{yr}}}"
                )
            else:
                lines.append(rf"  \item \small{{{escape_latex(str(edu))}}}")
        lines.extend([
            r"\resumeSubHeadingListEnd",
            r"",
        ])

    # Certifications
    certs = resume.get("certifications", [])
    if certs:
        lines.extend([
            r"\section{Certifications}",
            r"\begin{itemize}[leftmargin=0.15in, label={}]",
        ])
        for cert in certs:
            lines.append(rf"  \small{{\item{{$\bullet$ {escape_latex(cert)}}}}}")
        lines.extend([
            r"\end{itemize}",
            r"",
        ])

    lines.append(r"\end{document}")
    return "\n".join(lines)


def compile_latex_to_pdf(latex_source: str) -> tuple[bytes | None, str]:
    """Compile LaTeX source to PDF using local pdflatex, xelatex, or tectonic."""
    compiler = None
    for cand in ["pdflatex", "xelatex", "tectonic"]:
        if shutil.which(cand):
            compiler = cand
            break

    if not compiler:
        return None, "no_latex_compiler_found"

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "resume.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)

        try:
            if compiler == "tectonic":
                cmd = [compiler, tex_path]
            else:
                cmd = [compiler, "-interaction=nonstopmode", "-output-directory", temp_dir, tex_path]

            result = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True, timeout=30)
            pdf_path = os.path.join(temp_dir, "resume.pdf")

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read(), "success"
            else:
                logger.warning(f"LaTeX compile exited without PDF. Stderr: {result.stderr[:300]}")
                return None, f"compilation_failed: {result.stderr[:100]}"
        except Exception as e:
            logger.error(f"LaTeX compilation failed: {e}")
            return None, str(e)
