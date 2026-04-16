from pathlib import Path
from typing import List, Optional

from pydantic import Field

from app.llm import LLM
from app.logger import logger
from app.schema import Message
from app.tool.base import BaseTool, ToolResult
from app.tool.web_search import WebSearch, SearchResult

# File extensions supported for local file RAG
SUPPORTED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".jsonl",
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
    ".html", ".htm", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".log", ".sql", ".sh", ".bat", ".ps1",
    ".rst", ".tex", ".r", ".go", ".rs", ".rb", ".php",
}


class RAGTool(BaseTool):
    """Retrieval-Augmented Generation (RAG) tool."""

    name: str = "rag_qa"
    description: str = (
        "Answer a user query by retrieving relevant documents (web search or local docs) "
        "and then generating a grounded response with the LLM."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language question to answer.",
            },
            "num_search_results": {
                "type": "integer",
                "description": "Number of search results to collect when using web search.",
                "default": 5,
            },
            "top_k": {
                "type": "integer",
                "description": "Number of top documents to use in the generation prompt.",
                "default": 3,
            },
            "include_page_content": {
                "type": "boolean",
                "description": "Whether to fetch full web page content for each result.",
                "default": False,
            },
            "local_documents": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional local documents (raw text) to use instead of web search results.",
            },
            "local_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional list of local file paths to read and use as RAG documents. "
                    "Supports text files (.txt, .md, .csv, .json, .py, .html, etc.) and .pdf files. "
                    "Can also be a directory path to load all supported files from it."
                ),
            },
        },
        "required": ["query"],
    }

    @staticmethod
    def _read_file(file_path: str) -> Optional[str]:
        """Read a single file and return its text content, or None on failure."""
        path = Path(file_path).resolve()
        if not path.is_file():
            logger.warning(f"Skipping non-existent file: {path}")
            return None

        ext = path.suffix.lower()

        # PDF support via PyPDF2 or pdfplumber (best-effort)
        if ext == ".pdf":
            return RAGTool._read_pdf(path)

        if ext not in SUPPORTED_TEXT_EXTENSIONS:
            logger.warning(f"Skipping unsupported file type '{ext}': {path}")
            return None

        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None

    @staticmethod
    def _read_pdf(path: Path) -> Optional[str]:
        """Extract text from a PDF file."""
        # Try PyPDF2 first
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {path}: {e}")

        # Fallback to pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfplumber failed for {path}: {e}")

        logger.warning(
            f"Cannot read PDF {path}: install PyPDF2 or pdfplumber (`pip install PyPDF2` or `pip install pdfplumber`)"
        )
        return None

    @staticmethod
    def _collect_files_from_path(file_path: str) -> List[str]:
        """Given a path, return a list of supported file paths (expanding directories)."""
        path = Path(file_path).resolve()
        if path.is_file():
            return [str(path)]
        if path.is_dir():
            collected = []
            for child in sorted(path.rglob("*")):
                if child.is_file() and (
                    child.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS
                    or child.suffix.lower() == ".pdf"
                ):
                    collected.append(str(child))
            return collected
        logger.warning(f"Path does not exist: {path}")
        return []

    async def execute(
        self,
        query: str,
        num_search_results: int = 5,
        top_k: int = 3,
        include_page_content: bool = False,
        local_documents: Optional[List[str]] = None,
        local_files: Optional[List[str]] = None,
    ) -> ToolResult:
        """Execute the RAG workflow."""
        if not query.strip():
            return self.fail_response("query must not be empty")

        documents: List[str] = []
        sources: List[str] = []

        # Load documents from local files
        if local_files:
            for file_entry in local_files:
                for fpath in self._collect_files_from_path(file_entry):
                    content = self._read_file(fpath)
                    if content:
                        documents.append(content)
                        sources.append(fpath)
            if not documents:
                return self.fail_response(
                    "No readable files found in the provided local_files paths."
                )
            logger.info(f"Loaded {len(documents)} file(s) for RAG retrieval")

        # Use local documents when provided, else perform web search
        elif local_documents:
            documents = [doc.strip() for doc in local_documents if doc and doc.strip()]
            sources = [f"local_doc_{i+1}" for i in range(len(documents))]
            logger.info("Using local documents for RAG retrieval")
        else:
            logger.info("Performing web search for RAG retrieval")
            web_search = WebSearch()
            try:
                search_result = await web_search.execute(
                    query=query,
                    num_results=num_search_results,
                    fetch_content=include_page_content,
                )
            except Exception as e:
                logger.exception(f"Web search failed: {e}")
                return self.fail_response(f"Web search failed: {e}")

            if search_result.error:
                return self.fail_response(f"Web search error: {search_result.error}")

            if not search_result.results:
                return self.fail_response("No search results found for query")

            for result in search_result.results:
                title = result.title or result.url
                text = []
                if result.description:
                    text.append(f"Description: {result.description}")
                if include_page_content and result.raw_content:
                    text.append(f"Content: {result.raw_content}")
                documents.append("\n".join(text) if text else title)
                sources.append(result.url)

        if not documents:
            return self.fail_response("No documents available to answer the query")

        # simple relevance ranking by query-token overlap for local docs/files
        if local_documents or local_files:
            query_tokens = set(query.lower().split())

            def score_doc(doc_text: str) -> float:
                return len(query_tokens & set(doc_text.lower().split()))

            ranked = sorted(
                zip(documents, sources), key=lambda ds: score_doc(ds[0]), reverse=True
            )
            documents, sources = zip(*ranked) if ranked else (documents, sources)
            documents = list(documents)
            sources = list(sources)

        # choose top_k docs
        top_k = max(1, min(top_k, len(documents)))
        docs_for_prompt = documents[:top_k]
        source_for_prompt = sources[:top_k]

        context_text = []
        for i, (doc_text, src) in enumerate(
            zip(docs_for_prompt, source_for_prompt), start=1
        ):
            context_text.append(
                f"[Document {i}] Source: {src}\n{doc_text if doc_text else 'No content available.'}"
            )

        dag_prompt = f"""
You are a retrieval-augmented generation assistant. Use only the provided documents to answer the question.
If the answer is not present in the documents, say you cannot find a definitive answer.
Cite the source for each fact in brackets, like [Document 1].

Question: {query}

Retrieved Documents:
{chr(10).join(context_text)}

Answer:"""

        llm = LLM()
        try:
            response = await llm.ask(
                messages=[Message.user_message(dag_prompt)],
                stream=False,
                temperature=0.0,
            )
        except Exception as e:
            logger.exception(f"LLM generation failed: {e}")
            return self.fail_response(f"LLM generation failed: {e}")

        output = (
            f"RAG Answer:\n{response}\n\n"
            f"Sources used: {', '.join(source_for_prompt)}"
        )

        return self.success_response(output)
