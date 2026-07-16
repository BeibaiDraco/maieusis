from .citation_extraction import (
    build_unresolved_cited_works,
    extract_citation_contexts,
    extract_raw_references,
)
from .cited_abstracts import build_paper_local_literature_context
from .external_lookup import (
    CrossrefLookupProvider,
    CrossrefSourceReferenceProvider,
    EuropePmcLookupProvider,
    ExternalLookupError,
    NullProcessedPaperLookupProvider,
    OpenAlexLookupProvider,
    OpenAlexSourceReferenceProvider,
    PmcBiocLookupProvider,
    ProcessedPaperLookupProvider,
    SourceReferenceProvider,
    merge_external_records,
)
from .extraction import (
    PaperCaseExtractionPipeline,
    PaperCaseExtractionResult,
    build_source_packet,
    build_source_spans,
)
from .local_literature_build import (
    PaperLocalLiteratureBuildConfig,
    PaperLocalLiteratureBuildItem,
    PaperLocalLiteratureBuildManifest,
    build_reviewed_paper_local_literature,
)
from .parsing import (
    AutoPdfParsingProvider,
    DoclingPdfProvider,
    PdfParsingError,
    PdfParsingProvider,
    PopplerTextPdfProvider,
    build_completeness_report,
    build_pdf_parser,
)
from .pipeline import PaperIngestPipeline, PaperIngestPipelineConfig
from .reference_resolution import resolve_cited_works
from .verifier import EvidenceSpanVerifier

__all__ = [
    "AutoPdfParsingProvider",
    "CrossrefLookupProvider",
    "CrossrefSourceReferenceProvider",
    "DoclingPdfProvider",
    "EuropePmcLookupProvider",
    "EvidenceSpanVerifier",
    "ExternalLookupError",
    "NullProcessedPaperLookupProvider",
    "OpenAlexLookupProvider",
    "OpenAlexSourceReferenceProvider",
    "PaperCaseExtractionPipeline",
    "PaperCaseExtractionResult",
    "PaperIngestPipeline",
    "PaperIngestPipelineConfig",
    "PaperLocalLiteratureBuildConfig",
    "PaperLocalLiteratureBuildItem",
    "PaperLocalLiteratureBuildManifest",
    "PdfParsingError",
    "PdfParsingProvider",
    "PmcBiocLookupProvider",
    "PopplerTextPdfProvider",
    "ProcessedPaperLookupProvider",
    "SourceReferenceProvider",
    "build_completeness_report",
    "build_paper_local_literature_context",
    "build_pdf_parser",
    "build_reviewed_paper_local_literature",
    "build_source_packet",
    "build_source_spans",
    "build_unresolved_cited_works",
    "extract_citation_contexts",
    "extract_raw_references",
    "merge_external_records",
    "resolve_cited_works",
]
