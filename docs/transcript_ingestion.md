# Transcript ingestion boundaries

The upload API keeps its existing response contract. The implementation separates
document facts, validation, application policy and presentation.

1. `parsers/pdf_layout.py` groups words into local reading-order blocks. It never
   crops a PDF page or imposes a page-wide column boundary. Parallel fragments
   require independent table evidence on each side and compatible nearby rows.
   Full-width headings and notes stay outside those local blocks. Every original
   word belongs to exactly one block.
2. `parsers/headers.py` describes column schemas. Explicit cell separators retain
   unknown and empty cells. Geometric gaps are retained as separators in PDF text.
   Plain text without reliable boundaries uses conservative header aliases and
   leaves ambiguous mappings unresolved. `T+U` is one hours field; it is never
   interpreted as local credit or added together for GPA weighting.
3. `parsers/rows.py` binds rows to schemas and semester context. With explicit
   code/name columns, identifiers are not restricted to a department regex.
   The text fallback still uses conservative recognition. Local parallel blocks
   use internal TABLE_BEGIN/NEXT/END markers to restore shared header/semester
   context between lanes. These markers are not included in API course data.
4. `parsers/document_parser.py::extract_transcript` returns `TranscriptExtraction`:
   source rows, extracted courses, numeric candidates and inferred field positions.
   It does not validate completeness, choose GPA weighting, request confirmation
   or format user messages. Incomplete rows remain available for inspection.
5. `validation/transcript_validation.py` returns structured issues with codes and
   source row indices. Validation does not mutate extraction or choose UI states.
   `validation/mapping_validation.py` separately raises `MappingValidationError`
   for invalid caller choices. Such errors never become document `ExtractionIssue`s.
6. `services/transcript_workflow.py::run_transcript_workflow` applies ingestion
   policy and returns an `IngestionDecision`. This decides whether mapping,
   weighting or review is needed. It does not create labels or API response flags.
7. `services/transcript_presentation.py` maps that decision and issue codes into
   the existing `ParseResult` contract, labels and messages. API serialization
   remains in `api/transcripts.py`.

`parsers/transcript_parser.py`, `parsers/credit_options.py` and the old weighting
option helper remain compatibility entry points for existing callers. New upload
processing calls the dedicated extraction/service modules directly.

`TranscriptExtraction.document` contains the structured semesters and official
summaries. `parsers/official_summary.py` reads explicitly labelled CGPA/GANO,
credits and ECTS from inline pairs or aligned header/value rows, including decimal
commas. Semester values stay separate from overall values. Unlabelled numbers are
not assigned semantic meaning. Printed observations retain their extracted-text
line indices; conflicting observations leave the scalar unset and produce a
validation warning. This metadata is read before GPA weighting and never replaces
the engines' calculated values. The document itself contains no validation state.

The analyze API includes `official_summary` and `semesters` at mapping, weighting
and completion stages. It distinguishes HTTP 400 errors with `error_type` values
`invalid_transcript` and `invalid_mapping_request`, plus a stable `code`; `detail`
remains a string for compatibility. PDF file validation retains its existing error
contract. Student identity fields and raw transcript text are not added to the API.

These are evidence-based heuristics, not universal document understanding. Unknown
headings without cell boundaries require mapping. Unknown grade scales and missing
required values remain validation errors; no grades or credits are invented.
Scanned pages still require OCR and are rejected rather than silently skipped.

Regression tests cover mixed full-width/parallel layouts, word preservation,
forbidden page cropping, shared semester context, geometric/explicit cells,
numeric identifiers, composite hours, unknown columns, and layer independence.
