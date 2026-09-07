class TranscriptStructureError(ValueError):
    """Ingestion cannot continue with the extracted transcript facts."""

    def __init__(self, issue):
        from models.transcript_extraction import ExtractionIssue
        from services.transcript_presentation import issue_message
        self.issue = issue if isinstance(issue, ExtractionIssue) else None
        super().__init__(issue_message(issue) if self.issue else issue)
