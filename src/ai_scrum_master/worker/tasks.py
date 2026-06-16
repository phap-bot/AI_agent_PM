import shutil
from pathlib import Path

from ai_scrum_master.worker.celery_app import celery_app
from ai_scrum_master.core.pipeline.orchestrator import generate_story_pipeline
from ai_scrum_master.ingestion.ingest import ingest_raw_docs


@celery_app.task(bind=True, name="generate_story_task")
def generate_story_task(self, requirement: str, n_results: int, allow_fallback: bool, forced_docs: list[str] | None = None, project_id: str | None = None):
    """Celery task to run the generation pipeline."""
    partial_result = {}
    task_id = self.request.id
    
    def progress_callback(stage: str, partial_data: dict):
        partial_result.update(partial_data)
        # Update celery state so API can poll progress.
        # Pass task_id explicitly because LangGraph runs this in a background thread.
        self.update_state(task_id=task_id, state='PROCESSING', meta={'stage': stage, 'partial_result': partial_result})

    result = generate_story_pipeline(
        requirement=requirement,
        n_results=n_results,
        allow_fallback_without_context=allow_fallback,
        forced_context_docs=forced_docs,
        progress_callback=progress_callback,
        project_id=project_id
    )
    return result


@celery_app.task(bind=True, name="ingest_docs_task")
def ingest_docs_task(self, source_dir_str: str | None, project_id: str | None = None):
    """Celery task to run the document ingestion."""
    source_dir = Path(source_dir_str) if source_dir_str else None
    
    try:
        result = ingest_raw_docs(raw_docs_dir=source_dir, project_id=project_id)
        return result
    finally:
        # Cleanup temp upload directory if needed
        if source_dir and source_dir.exists() and "tmp" in str(source_dir).lower():
            shutil.rmtree(source_dir, ignore_errors=True)
