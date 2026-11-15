"""Cut an OKF bundle into chunks: one per header section of each live concept, with numbered sentences."""

import hashlib
import json
import pathlib as plb
import re
from collections.abc import Generator, Iterable
from typing import cast

import frontmatter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pydantic import BaseModel, Field

HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]
CORRECTION_PREFIXES = ("Correction", "Amended")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\[(*\"'/])")
_FENCE = re.compile(r"(```.*?```)", re.DOTALL)
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_BLANK_LINE = re.compile(r"\n\s*\n")
_NOT_SLUG = re.compile(r"[^a-z0-9]+")


class Chunk(BaseModel):
    """One header section of one concept, as the extractor sees it."""

    id: str = Field(description="The concept id plus the slug of its header path.")
    concept: str = Field(description="The concept id: its path in the bundle without .md.")
    type: str = Field(description="The concept's type front-matter field.")
    status: str | None = Field(description="The concept's status front-matter field.")
    title: str = Field(description="The concept's title front-matter field.")
    section: str = Field(description="The header path, joined with ' > '.")
    sentences: list[str] = Field(description="The units a claim can cite, in order.")
    corrections: str = Field(description="The record's correction sections as context; empty for a correction itself.")
    key: str = Field(description="A hash of the header path, sentences, corrections and concept type.")
    earlier: str = Field(default="", description="Earlier sections' sentences, each labelled [s.n].")
    earlier_ids: list[str] = Field(default_factory=list, description="The chunk id of each earlier section s, from 1.")
    is_correction: bool = Field(default=False, description="Whether the section corrects or amends the record.")

    @property
    def cache_key(self) -> str:
        """The key plus a hash of the earlier sections: everything the extractor sees."""
        return self.key + ("-" + hashlib.sha256(self.earlier.encode()).hexdigest()[:8] if self.earlier else "")

    @property
    def extraction_key(self) -> str:
        """A hash of everything one extraction depends on: the cache key plus the ids, title and status.

        The model sees the concept id, title and status, and a claim's ``refers_to`` names chunk ids, so a
        renamed concept with the same text must not reuse a stored result.
        """
        content = [self.cache_key, self.id, self.concept, self.title, self.status, self.earlier_ids]
        return hashlib.sha256(json.dumps(content).encode()).hexdigest()[:16]

    def numbered_sentences(self) -> str:
        """Return the sentences one per line, each prefixed with ``[n]`` from 1."""
        return "\n".join(f"[{number}] {sentence}" for number, sentence in enumerate(self.sentences, 1))


class Section(BaseModel):
    """One header section of a concept's body."""

    name: str = Field(description="The header path, joined with ' > '.")
    body: str = Field(description="The text under that header.")

    @property
    def last_header(self) -> str:
        """The innermost header of the section."""
        return self.name.rsplit(" > ", 1)[-1]

    @property
    def is_correction(self) -> bool:
        """Whether the section is a correction or amendment to the record."""
        return self.last_header.startswith(CORRECTION_PREFIXES)


class SentenceSplitter:
    """Split a section's text into the units a claim can cite.

    A code block or table is one unit, a list item is split by sentence, and a
    fragment of two words or fewer (a list number, a bold label) joins the
    sentence after it.
    """

    def split(self, text: str) -> list[str]:
        """Return the section's non-empty units, in order."""
        units: list[str] = []
        for index, part in enumerate(_FENCE.split(text)):
            if index % 2 == 1:  # a fenced code block
                units.append(part.strip())
            else:
                units.extend(self._split_prose(part))
        return [unit for unit in units if unit]

    def _split_prose(self, text: str) -> list[str]:
        """Split text outside code blocks into units, block by block."""
        units: list[str] = []
        for block in _BLANK_LINE.split(text.strip()):
            tables, items = self._collect_tables_and_items(block.splitlines())
            units.extend(tables)
            for item in items:
                units.extend(self._split_item(item))
        return units

    @staticmethod
    def _collect_tables_and_items(lines: list[str]) -> tuple[list[str], list[str]]:
        """Group a block's lines into tables and list items; a line that starts no item continues the last one."""
        tables: list[str] = []
        items: list[str] = []
        table: list[str] = []
        for line in lines:
            if line.lstrip().startswith("|"):
                table.append(line.strip())
                continue
            if table:
                tables.append("\n".join(table))
                table = []
            if _BULLET.match(line) or not items:
                items.append(line.strip())
            else:
                items[-1] += " " + line.strip()
        if table:
            tables.append("\n".join(table))
        return tables, items

    @staticmethod
    def _split_item(item: str) -> list[str]:
        """Split one list item into sentences, joining short fragments to the next one."""
        units: list[str] = []
        pending = ""
        for part in _SENTENCE_END.split(item):
            sentence = (pending + " " + part).strip() if pending else part.strip()
            is_whole_item = sentence is item
            if len(sentence.split()) <= 2 and not is_whole_item:
                pending = sentence
                continue
            pending = ""
            if sentence:
                units.append(sentence)
        if pending:
            units.append(pending)
        return units


class BundleChunker:
    """Turn every live concept in an OKF bundle into chunks.

    Skips reserved names (``index.md``, ``log.md``), skipped folders and
    deprecated concepts.

    Parameters
    ----------
    splitter :
        Splits each section's body into the sentences a claim can cite.
    skip_names :
        File names that are not concepts.
    skip_dirs :
        Bundle folders not to chunk.
    earlier_sentences :
        How many sentences of earlier sections each chunk carries as context.
    """

    def __init__(
        self,
        splitter: SentenceSplitter,
        skip_names: Iterable[str] = ("index.md", "log.md"),
        skip_dirs: Iterable[str] = ("prototypes",),
        earlier_sentences: int = 40,
    ) -> None:
        self._splitter = splitter
        self._header_splitter = MarkdownHeaderTextSplitter(HEADERS)
        self._skip_names = set(skip_names)
        self._skip_dirs = set(skip_dirs)
        self._earlier_sentences = earlier_sentences

    def chunks(self, bundle: plb.Path, only: Iterable[plb.Path] | None = None) -> Generator[Chunk, None, None]:
        """Yield one chunk per non-empty header section of every live concept, in path order.

        Parameters
        ----------
        bundle :
            The bundle's root folder; concept ids are paths relative to it.
        only :
            Chunk just these concept files, still skipping deprecated ones; None for the whole bundle.
        """
        paths = sorted(p.resolve() for p in only) if only is not None else self._concept_paths(bundle)
        bundle = bundle.resolve()
        for path in paths:
            post = frontmatter.loads(path.read_text())
            if post.get("status") == "deprecated":
                continue
            yield from self._concept_chunks(bundle, path, post)

    def _concept_paths(self, bundle: plb.Path) -> Generator[plb.Path, None, None]:
        """Yield the bundle's concept files in sorted order, minus reserved names and skipped folders."""
        for path in sorted(bundle.resolve().rglob("*.md")):
            if path.name in self._skip_names or self._skip_dirs & set(path.relative_to(bundle).parts):
                continue
            yield path

    def _concept_chunks(self, bundle: plb.Path, path: plb.Path, post: frontmatter.Post) -> Generator[Chunk, None, None]:
        """Yield one chunk per section of a concept that holds any sentence."""
        concept = path.relative_to(bundle).with_suffix("").as_posix()
        sections = self._sections(post)
        corrections = self._corrections(sections)
        seen: dict[str, int] = {}
        earlier: list[tuple[str, list[str]]] = []
        earlier_ids: list[str] = []
        for section in sections:
            sentences = self._splitter.split(section.body)
            if not sentences:
                continue
            context = "" if section.is_correction else corrections
            chunk_id = self._chunk_id(concept, section, seen)
            yield Chunk(
                id=chunk_id,
                concept=concept,
                type=str(post.get("type", "")),
                status=cast(str | None, post.get("status")),
                title=str(post.get("title", "")),
                section=section.name,
                sentences=sentences,
                corrections=context,
                key=self._key(section, sentences, context, post),
                earlier=self._earlier(earlier),
                earlier_ids=list(earlier_ids),
                is_correction=section.is_correction,
            )
            if not section.is_correction:
                earlier.append((section.name, sentences))
                earlier_ids.append(chunk_id)

    def _earlier(self, earlier: list[tuple[str, list[str]]]) -> str:
        """The earlier sections' sentences, labelled [s.n], keeping the last ``earlier_sentences``."""
        lines = []
        for s, (name, sentences) in enumerate(earlier, 1):
            lines.append(f"{name}:")
            lines.extend(f"[{s}.{n}] {sentence}" for n, sentence in enumerate(sentences, 1))
        labelled = [line for line in lines if line.startswith("[")]
        kept = set(labelled[-self._earlier_sentences :]) if self._earlier_sentences else set()
        return "\n".join(line for line in lines if not line.startswith("[") or line in kept)

    def _sections(self, post: frontmatter.Post) -> list[Section]:
        """Split a concept's body by its headers."""
        return [
            Section(name=" > ".join(document.metadata.values()), body=document.page_content)
            for document in self._header_splitter.split_text(post.content)
        ]

    @staticmethod
    def _corrections(sections: list[Section]) -> str:
        """Join a record's correction sections, each headed by its header path."""
        return "\n\n".join(f"{s.name}\n{s.body}" for s in sections if s.is_correction)

    @staticmethod
    def _chunk_id(concept: str, section: Section, seen: dict[str, int]) -> str:
        """Build a chunk id from the concept and its header path below the top header; a repeat gets ``-2``, ``-3``."""
        below_top = section.name.split(" > ", 1)[-1]
        slug = _NOT_SLUG.sub("-", below_top.lower()).strip("-") or "top"
        seen[slug] = seen.get(slug, 0) + 1
        return f"{concept}#{slug}-{seen[slug]}" if seen[slug] > 1 else f"{concept}#{slug}"

    @staticmethod
    def _key(section: Section, sentences: list[str], context: str, post: frontmatter.Post) -> str:
        """Hash the header path, sentences, corrections and concept type into a 16-character key."""
        content = [section.name, sentences, context, str(post.get("type"))]
        return hashlib.sha256(json.dumps(content).encode()).hexdigest()[:16]
