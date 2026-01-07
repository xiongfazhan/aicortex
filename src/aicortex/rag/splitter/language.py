"""Language-specific separators for text splitting.

Corresponds to src/rag/splitter/language.rs in the Rust implementation.
"""

from enum import Enum


class Language(Enum):
    """Programming and markup languages for text splitting."""

    CPP = "cpp"
    GO = "go"
    JAVA = "java"
    JS = "js"
    PHP = "php"
    PROTO = "proto"
    PYTHON = "python"
    RST = "rst"
    RUBY = "ruby"
    RUST = "rust"
    SCALA = "scala"
    SWIFT = "swift"
    MARKDOWN = "markdown"
    LATEX = "latex"
    HTML = "html"
    SOL = "sol"

    def separators(self) -> list[str]:
        """Get language-specific separators for text splitting.

        Returns:
            List of separator strings in priority order
        """
        match self:
            case Language.CPP:
                return [
                    "\nclass ",
                    "\nvoid ",
                    "\nint ",
                    "\nfloat ",
                    "\ndouble ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\nswitch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.GO:
                return [
                    "\nfunc ",
                    "\nvar ",
                    "\nconst ",
                    "\ntype ",
                    "\nif ",
                    "\nfor ",
                    "\nswitch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.JAVA:
                return [
                    "\nclass ",
                    "\npublic ",
                    "\nprotected ",
                    "\nprivate ",
                    "\nstatic ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\nswitch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.JS:
                return [
                    "\nfunction ",
                    "\nconst ",
                    "\nlet ",
                    "\nvar ",
                    "\nclass ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\nswitch ",
                    "\ncase ",
                    "\ndefault ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.PHP:
                return [
                    "\nfunction ",
                    "\nclass ",
                    "\nif ",
                    "\nforeach ",
                    "\nwhile ",
                    "\ndo ",
                    "\nswitch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.PROTO:
                return [
                    "\nmessage ",
                    "\nservice ",
                    "\nenum ",
                    "\noption ",
                    "\nimport ",
                    "\nsyntax ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.PYTHON:
                return ["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""]
            case Language.RST:
                return ["\n===\n", "\n---\n", "\n***\n", "\n.. ", "\n\n", "\n", " ", ""]
            case Language.RUBY:
                return [
                    "\ndef ",
                    "\nclass ",
                    "\nif ",
                    "\nunless ",
                    "\nwhile ",
                    "\nfor ",
                    "\ndo ",
                    "\nbegin ",
                    "\nrescue ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.RUST:
                return [
                    "\nfn ",
                    "\nconst ",
                    "\nlet ",
                    "\nif ",
                    "\nwhile ",
                    "\nfor ",
                    "\nloop ",
                    "\nmatch ",
                    "\nconst ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.SCALA:
                return [
                    "\nclass ",
                    "\nobject ",
                    "\ndef ",
                    "\nval ",
                    "\nvar ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\nmatch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.SWIFT:
                return [
                    "\nfunc ",
                    "\nclass ",
                    "\nstruct ",
                    "\nenum ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\ndo ",
                    "\nswitch ",
                    "\ncase ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.MARKDOWN:
                return [
                    "\n## ",
                    "\n### ",
                    "\n#### ",
                    "\n##### ",
                    "\n###### ",
                    "```\n\n",
                    "\n\n***\n\n",
                    "\n\n---\n\n",
                    "\n\n___\n\n",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.LATEX:
                return [
                    "\n\\chapter{",
                    "\n\\section{",
                    "\n\\subsection{",
                    "\n\\subsubsection{",
                    "\n\\begin{enumerate}",
                    "\n\\begin{itemize}",
                    "\n\\begin{description}",
                    "\n\\begin{list}",
                    "\n\\begin{quote}",
                    "\n\\begin{quotation}",
                    "\n\\begin{verse}",
                    "\n\\begin{verbatim}",
                    "\n\\begin{align}",
                    "$$",
                    "$",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]
            case Language.HTML:
                return [
                    "<body>",
                    "<div>",
                    "<p>",
                    "<br>",
                    "<li>",
                    "<h1>",
                    "<h2>",
                    "<h3>",
                    "<h4>",
                    "<h5>",
                    "<h6>",
                    "<span>",
                    "<table>",
                    "<tr>",
                    "<td>",
                    "<th>",
                    "<ul>",
                    "<ol>",
                    "<header>",
                    "<footer>",
                    "<nav>",
                    "<head>",
                    "<style>",
                    "<script>",
                    "<meta>",
                    "<title>",
                    " ",
                    "",
                ]
            case Language.SOL:
                return [
                    "\npragma ",
                    "\nusing ",
                    "\ncontract ",
                    "\ninterface ",
                    "\nlibrary ",
                    "\nconstructor ",
                    "\ntype ",
                    "\nfunction ",
                    "\nevent ",
                    "\nmodifier ",
                    "\nerror ",
                    "\nstruct ",
                    "\nenum ",
                    "\nif ",
                    "\nfor ",
                    "\nwhile ",
                    "\ndo while ",
                    "\nassembly ",
                    "\n\n",
                    "\n",
                    " ",
                    "",
                ]


# Default separators for unknown file types
DEFAULT_SEPARATORS = ["\n\n", "\n", " ", ""]


def get_language(extension: str) -> Language:
    """Get Language enum from file extension.

    Args:
        extension: File extension (e.g., "py", "js", "md")

    Returns:
        Language enum value
    """
    mapping = {
        "c": Language.CPP,
        "cc": Language.CPP,
        "cpp": Language.CPP,
        "go": Language.GO,
        "java": Language.JAVA,
        "js": Language.JS,
        "mjs": Language.JS,
        "cjs": Language.JS,
        "php": Language.PHP,
        "proto": Language.PROTO,
        "py": Language.PYTHON,
        "rst": Language.RST,
        "rb": Language.RUBY,
        "rs": Language.RUST,
        "scala": Language.SCALA,
        "swift": Language.SWIFT,
        "md": Language.MARKDOWN,
        "mkd": Language.MARKDOWN,
        "tex": Language.LATEX,
        "htm": Language.HTML,
        "html": Language.HTML,
        "sol": Language.SOL,
    }
    return mapping.get(extension.lower(), None)


__all__ = ["Language", "DEFAULT_SEPARATORS", "get_language"]
