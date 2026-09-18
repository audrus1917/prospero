"""Classify extracted document text using a configurable taxonomy."""

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CategoryMatch:
    """A taxonomy category supported by evidence from document text."""

    slug: str
    name: str
    confidence: float
    evidence: list[str]


class DocumentClassifier:
    """Normalize explicit skill aliases and classify documents by evidence."""

    version = "rules-1"

    def __init__(self, taxonomy: dict[str, object]) -> None:
        """Validate and load category definitions and skill aliases.

        Raises:
            ValueError: If required taxonomy sections are missing or malformed.
        """
        categories = taxonomy.get("categories")
        aliases = taxonomy.get("skill_aliases")
        if not isinstance(categories, list) or not isinstance(aliases, dict):
            raise ValueError("Document taxonomy must contain categories and skill_aliases")
        self._categories = categories
        self._aliases = {str(key).casefold(): str(value) for key, value in aliases.items()}

    @classmethod
    def from_file(cls, path: Path) -> "DocumentClassifier":
        """Load a document classifier from a JSON taxonomy file.

        Raises:
            ValueError: If the taxonomy root is not an object.
        """
        with path.open(encoding="utf-8") as taxonomy_file:
            payload = json.load(taxonomy_file)
        if not isinstance(payload, dict):
            raise ValueError("Document taxonomy must be an object")
        return cls(payload)

    def normalize_skills(self, extracted_text: str) -> list[str]:
        """Return canonical skills whose aliases occur in document text."""
        return sorted(
            {
                canonical
                for alias, canonical in self._aliases.items()
                if self._contains(extracted_text, alias)
            },
            key=str.casefold,
        )

    def classify(self, extracted_text: str) -> list[CategoryMatch]:
        """Return evidence-backed category matches ordered by confidence."""
        matches: list[CategoryMatch] = []
        for category in self._categories:
            if not isinstance(category, dict):
                continue
            keywords = category.get("keywords")
            slug = category.get("slug")
            name = category.get("name")
            if (
                not isinstance(keywords, list)
                or not isinstance(slug, str)
                or not isinstance(name, str)
            ):
                continue
            evidence = sorted(
                str(keyword) for keyword in keywords if self._contains(extracted_text, str(keyword))
            )
            if evidence:
                matches.append(
                    CategoryMatch(
                        slug=slug,
                        name=name,
                        confidence=round(min(1.0, 0.5 + 0.15 * (len(evidence) - 1)), 2),
                        evidence=evidence,
                    )
                )
        return sorted(matches, key=lambda match: (-match.confidence, match.slug))

    @staticmethod
    def _contains(text: str, term: str) -> bool:
        """Check whether text contains a case-insensitive, bounded term."""
        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.IGNORECASE) is not None
