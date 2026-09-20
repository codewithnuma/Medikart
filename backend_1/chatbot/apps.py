import os
import sys

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot"

    def ready(self):
        """
        Preload heavy resources once, when Django initializes the
        application, so the FIRST real request (semantic-cache
        lookup, or the first RAG/handbook question) never pays the
        setup cost itself.

        Two independent preloads:

        1. Semantic cache embedding model (sentence-transformers)
           used by the `general` route's cache.

        2. RAG resources for the `handbook` route: the Hugging
           Face RAG model, the embedding model, and — the
           expensive one — the FAISS vectorstore (which chunks
           the PDF and builds the index from scratch if
           faiss_index_fast/ doesn't exist yet, or just loads it
           if it does) plus the BM25 index and section-neighbor
           lookup built on top of it.

        Both are wrapped in their own try/except so a failure in
        one (e.g. a missing API key) never blocks the other, and
        never prevents the Django app itself from starting up.

        RUNSERVER AUTORELOAD GUARD:
        `manage.py runserver` (with the default autoreloader) calls
        ready() TWICE:
          - once in the parent "watcher" process (no RUN_MAIN set)
          - once in the actual child process that serves requests
            (RUN_MAIN="true")
        Without this guard, the expensive FAISS build/load would
        run twice every time you start or autoreload the dev
        server. The condition below means:
          - production (gunicorn/uwsgi, no "runserver" in argv):
            RUN_MAIN is never set, but "runserver" isn't in argv
            either, so this always runs — correct.
          - `runserver` child process: RUN_MAIN == "true" -> runs.
          - `runserver` parent/watcher process: "runserver" is in
            argv AND RUN_MAIN isn't "true" -> skipped.
        """

        is_runserver_parent_watcher = (
            "runserver" in sys.argv
            and os.environ.get("RUN_MAIN") != "true"
        )

        if is_runserver_parent_watcher:
            return

        try:
            from .chatbot import preload_semantic_cache_model

            preload_semantic_cache_model()

        except Exception as exc:
            print(
                "Semantic model preload skipped:",
                type(exc).__name__,
                str(exc),
            )

        try:
            from .C_rag import preload_rag_resources

            preload_rag_resources()

        except Exception as exc:
            print(
                "RAG resource preload skipped:",
                type(exc).__name__,
                str(exc),
            )