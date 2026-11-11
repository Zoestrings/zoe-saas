import inspect
import pytest
from pathlib import Path
from zoe.memory import views
from zoe.memory.views import CommunityMemoryView, OfficialKnowledgeView


@pytest.mark.automated
def test_community_memory_view_isolation() -> None:
    """Verify that CommunityMemoryView does not import official_stream or retriever."""
    source = inspect.getsource(views)

    # Must not contain imports of official_stream or retriever
    assert "official_stream" not in source, "views.py must not reference official_stream"
    assert "retriever" not in source, "views.py must not reference retriever"

    # Module namespace check
    assert not hasattr(views, "retriever"), "views module must not expose retriever"
    assert not hasattr(views, "official_stream"), "views module must not expose official_stream"

    # CommunityMemoryView methods check
    cmv_methods = [m for m, _ in inspect.getmembers(CommunityMemoryView, predicate=inspect.isfunction)]
    for m_name in cmv_methods:
        fn = getattr(CommunityMemoryView, m_name)
        fn_source = inspect.getsource(fn)
        assert "official_knowledge" not in fn_source, f"Method {m_name} must not access official_knowledge"

