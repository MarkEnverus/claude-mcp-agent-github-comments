"""
Pattern-based intelligence for common PR comment issues

This module provides enhanced heuristics for recognizing and fixing
common issues without requiring LLM API calls.
"""

import re
from enum import Enum
from typing import Any


class FixPattern(str, Enum):
    """Common fix patterns we can handle automatically"""
    UNUSED_IMPORT = "unused_import"
    IMPORT_LOCATION = "import_location"
    DUPLICATE_IMPORT = "duplicate_import"
    MISSING_TYPE_HINT = "missing_type_hint"
    MISSING_DOCSTRING = "missing_docstring"
    PEP8_NAMING = "pep8_naming"
    UNNECESSARY_ELSE = "unnecessary_else"
    SIMPLIFY_BOOLEAN = "simplify_boolean"


# Common bot authors
COMMON_BOT_AUTHORS = [
    "github-copilot",
    "Copilot",
    "github-advanced-security",
    "github-code-quality[bot]",
    "dependabot",
    "dependabot[bot]",
    "snyk-bot",
    "codecov",
    "codecov-io",
    "renovate",
    "renovate[bot]",
    "deepsource-io[bot]",
    "sonarcloud[bot]",
]


class PatternMatcher:
    """Match comment text to known patterns"""

    # Unused import patterns
    UNUSED_IMPORT_PATTERNS = [
        r"[Ii]mport.*(?:not used|unused|never used)",
        r"[Uu]nused import",
        r"[Rr]emove.*unused.*import",
    ]

    # Import location patterns
    IMPORT_LOCATION_PATTERNS = [
        r"[Ii]mport.*should be (?:moved to|at) the top",
        r"[Mm]ove.*import.*to (?:top|module level)",
        r"PEP\s*8.*import",
        r"[Ll]ocal import.*should be",
    ]

    # Duplicate patterns
    DUPLICATE_PATTERNS = [
        r"[Dd]uplicate import",
        r"[Ii]mport.*already imported",
        r"[Rr]edundant import",
    ]

    # Type hint patterns
    TYPE_HINT_PATTERNS = [
        r"[Aa]dd type hint",
        r"[Mm]issing type annotation",
        r"[Ss]hould have.*type",
    ]

    # Docstring patterns
    DOCSTRING_PATTERNS = [
        r"[Aa]dd docstring",
        r"[Mm]issing docstring",
        r"[Dd]ocumentation.*missing",
    ]

    @classmethod
    def identify_pattern(cls, comment_body: str) -> FixPattern | None:
        """
        Identify which fix pattern matches the comment

        Args:
            comment_body: Comment text

        Returns:
            FixPattern if recognized, None otherwise
        """
        # Check unused imports
        for pattern in cls.UNUSED_IMPORT_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                return FixPattern.UNUSED_IMPORT

        # Check import location
        for pattern in cls.IMPORT_LOCATION_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                return FixPattern.IMPORT_LOCATION

        # Check duplicates
        for pattern in cls.DUPLICATE_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                return FixPattern.DUPLICATE_IMPORT

        # Check type hints
        for pattern in cls.TYPE_HINT_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                return FixPattern.MISSING_TYPE_HINT

        # Check docstrings
        for pattern in cls.DOCSTRING_PATTERNS:
            if re.search(pattern, comment_body, re.IGNORECASE):
                return FixPattern.MISSING_DOCSTRING

        return None

    @classmethod
    def extract_import_names(cls, comment_body: str) -> list[str]:
        """
        Extract import names mentioned in comment

        Examples:
            "Import of 'Optional' is not used" -> ["Optional"]
            "Remove unused imports: Optional, List" -> ["Optional", "List"]
        """
        imports = []

        # Look for quoted imports
        quoted = re.findall(r"['\"`]([A-Za-z_][A-Za-z0-9_]*)['\"`]", comment_body)
        imports.extend(quoted)

        # Look for code tags
        code_tagged = re.findall(r"<code>([A-Za-z_][A-Za-z0-9_]*)</code>", comment_body)
        imports.extend(code_tagged)

        return list(set(imports))  # Remove duplicates


class FixGenerator:
    """Generate fixes for common patterns"""

    @staticmethod
    def fix_unused_import(
        code_lines: list[str],
        line_number: int,
        unused_names: list[str]
    ) -> tuple[str, str]:
        """
        Generate fix for unused import

        Args:
            code_lines: List of code lines
            line_number: Line number (1-indexed)
            unused_names: List of unused import names

        Returns:
            (fixed_line, explanation)
        """
        line_idx = line_number - 1
        original_line = code_lines[line_idx]

        # Parse import statement
        # Handle: from typing import Optional, Tuple
        if "from" in original_line and "import" in original_line:
            match = re.match(r"^(\s*from\s+\S+\s+import\s+)(.+)$", original_line)
            if match:
                prefix = match.group(1)
                imports_part = match.group(2)

                # Split imports
                imports = [imp.strip() for imp in imports_part.split(",")]

                # Remove unused ones
                kept_imports = [imp for imp in imports if imp not in unused_names]

                if not kept_imports:
                    # All imports unused - remove entire line
                    return "", "Removed entire import (all imports unused)"
                else:
                    # Rebuild line
                    fixed_line = prefix + ", ".join(kept_imports)
                    return fixed_line, f"Removed unused import(s): {', '.join(unused_names)}"

        # Handle: import os, sys
        elif original_line.strip().startswith("import "):
            imports = original_line.replace("import", "").strip().split(",")
            imports = [imp.strip() for imp in imports]

            kept_imports = [imp for imp in imports if imp not in unused_names]

            if not kept_imports:
                return "", "Removed entire import (all imports unused)"
            else:
                indent = len(original_line) - len(original_line.lstrip())
                fixed_line = " " * indent + "import " + ", ".join(kept_imports)
                return fixed_line, f"Removed unused import(s): {', '.join(unused_names)}"

        return original_line, "Could not automatically fix"

    @staticmethod
    def fix_import_location(
        code_lines: list[str],
        line_number: int
    ) -> tuple[list[str], str]:
        """
        Generate fix for import in wrong location

        Args:
            code_lines: List of code lines
            line_number: Line number of misplaced import (1-indexed)

        Returns:
            (modified_lines, explanation)
        """
        line_idx = line_number - 1
        import_line = code_lines[line_idx].strip()

        # Find where imports should go (after docstring, before first code)
        insert_idx = 0

        # Skip shebang and encoding
        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if stripped.startswith("#!") or "coding:" in stripped or "encoding:" in stripped:
                insert_idx = i + 1
            else:
                break

        # Skip module docstring
        if insert_idx < len(code_lines):
            if code_lines[insert_idx].strip().startswith('"""') or code_lines[insert_idx].strip().startswith("'''"):
                # Find end of docstring
                quote = '"""' if '"""' in code_lines[insert_idx] else "'''"
                for i in range(insert_idx + 1, len(code_lines)):
                    if quote in code_lines[i]:
                        insert_idx = i + 1
                        break

        # Skip blank lines
        while insert_idx < len(code_lines) and not code_lines[insert_idx].strip():
            insert_idx += 1

        # Find last import statement at top
        last_import_idx = insert_idx
        for i in range(insert_idx, min(insert_idx + 50, len(code_lines))):
            stripped = code_lines[i].strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i
            elif stripped and not stripped.startswith("#"):
                break

        # Remove from current location
        modified = code_lines[:line_idx] + code_lines[line_idx + 1:]

        # Insert at top (after last import)
        insert_position = last_import_idx if last_import_idx >= insert_idx else insert_idx
        modified.insert(insert_position, import_line + "\n")

        return modified, f"Moved import from line {line_number} to module level (line {insert_position + 1})"


class ReplyTemplate:
    """Templates for common reply scenarios"""

    @staticmethod
    def unused_import(import_names: list[str], fixed: bool = True) -> str:
        """Reply for unused import fix"""
        names = ", ".join(f"`{name}`" for name in import_names)
        if fixed:
            return f"✅ Removed unused import(s): {names}. Thanks for catching this!"
        else:
            return f"Good catch! Will remove unused import(s): {names}"

    @staticmethod
    def import_location(from_line: int, to_line: int, fixed: bool = True) -> str:
        """Reply for import location fix"""
        if fixed:
            return f"✅ Moved import to module level (line {to_line}) per PEP 8. Thanks!"
        else:
            return f"Good point! Will move import from line {from_line} to module level per PEP 8."

    @staticmethod
    def duplicate_import(fixed: bool = True) -> str:
        """Reply for duplicate import"""
        if fixed:
            return "✅ Consolidated duplicate imports. Thanks!"
        else:
            return "Good catch! Will consolidate these duplicate imports."

    @staticmethod
    def already_fixed() -> str:
        """Reply when issue is already addressed"""
        return "This has already been addressed in the current code. Thanks for the review!"

    @staticmethod
    def will_address() -> str:
        """Generic acknowledgment"""
        return "Thanks for the suggestion! Will address this."

    @staticmethod
    def not_applicable(reason: str) -> str:
        """Reply when suggestion doesn't apply"""
        return f"Thanks for the review! {reason}"


class SmartAnalyzer:
    """Enhanced analysis using pattern matching"""

    def __init__(self):
        self.matcher = PatternMatcher()
        self.generator = FixGenerator()

    def analyze_with_patterns(
        self,
        comment_body: str,
        code_snippet: str,
        file_path: str,
        line_number: int
    ) -> dict[str, Any]:
        """
        Enhanced analysis using pattern recognition

        Args:
            comment_body: Comment text
            code_snippet: Code context
            file_path: Path to file
            line_number: Line number

        Returns:
            Enhanced analysis with fix suggestions
        """
        # Identify pattern
        pattern = self.matcher.identify_pattern(comment_body)

        if not pattern:
            return {
                "pattern_detected": None,
                "can_auto_fix": False,
                "confidence": 0.3,
                "status": "uncertain",
            }

        # Handle based on pattern
        if pattern == FixPattern.UNUSED_IMPORT:
            return self._analyze_unused_import(
                comment_body, code_snippet, line_number
            )

        elif pattern == FixPattern.IMPORT_LOCATION:
            return self._analyze_import_location(
                comment_body, code_snippet, line_number
            )

        elif pattern == FixPattern.DUPLICATE_IMPORT:
            return self._analyze_duplicate_import(
                comment_body, code_snippet
            )

        return {
            "pattern_detected": pattern.value,
            "can_auto_fix": False,
            "confidence": 0.6,
            "status": "needs_review",
        }

    def _analyze_unused_import(
        self, comment_body: str, code_snippet: str, line_number: int
    ) -> dict[str, Any]:
        """Analyze unused import"""
        unused_names = self.matcher.extract_import_names(comment_body)

        # Extract the import line from code snippet
        lines = code_snippet.split("\n")
        target_line = None
        for line in lines:
            if f"{line_number} |" in line or f">>> {line_number:4d}" in line:
                # Extract actual code (after line number)
                parts = line.split("|", 1)
                if len(parts) == 2:
                    target_line = parts[1]
                    break

        can_fix = False
        suggested_fix = None

        if target_line and unused_names:
            # Check if we can actually remove these imports
            code_lines = [target_line]
            try:
                fixed_line, explanation = self.generator.fix_unused_import(
                    code_lines, 1, unused_names
                )
                can_fix = True
                suggested_fix = {
                    "original": target_line.strip(),
                    "fixed": fixed_line.strip(),
                    "explanation": explanation
                }
            except Exception:
                pass

        return {
            "pattern_detected": "unused_import",
            "can_auto_fix": can_fix,
            "confidence": 0.85 if can_fix else 0.70,
            "status": "needs_fix",
            "is_valid": True,
            "reasoning": f"Unused import detected: {', '.join(unused_names)}",
            "suggested_action": "Remove unused imports",
            "suggested_fix": suggested_fix,
            "reply_template": ReplyTemplate.unused_import(unused_names, fixed=False),
        }

    def _analyze_import_location(
        self, comment_body: str, code_snippet: str, line_number: int
    ) -> dict[str, Any]:
        """Analyze import location issue"""
        # Check if it's actually an import statement
        is_import = "import " in code_snippet or "from " in code_snippet

        if not is_import:
            return {
                "pattern_detected": "import_location",
                "can_auto_fix": False,
                "confidence": 0.5,
                "status": "uncertain",
            }

        return {
            "pattern_detected": "import_location",
            "can_auto_fix": True,
            "confidence": 0.80,
            "status": "needs_fix",
            "is_valid": True,
            "reasoning": "Import statement found in method/function body. Should be at module level per PEP 8.",
            "suggested_action": "Move import to top of file",
            "reply_template": ReplyTemplate.import_location(line_number, 0, fixed=False),
        }

    def _analyze_duplicate_import(
        self, comment_body: str, code_snippet: str
    ) -> dict[str, Any]:
        """Analyze duplicate import"""
        return {
            "pattern_detected": "duplicate_import",
            "can_auto_fix": True,
            "confidence": 0.85,
            "status": "needs_fix",
            "is_valid": True,
            "reasoning": "Duplicate import detected. Should be consolidated.",
            "suggested_action": "Remove duplicate import",
            "reply_template": ReplyTemplate.duplicate_import(fixed=False),
        }
