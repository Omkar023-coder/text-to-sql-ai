"""
test_frontend_serving.py

Tests for static file serving introduced in Phase 9.1.

Strategy:
- Pre-build tests confirm the existing API endpoints still work
  and that /schema is accessible before the frontend is built.
- Post-build tests (marked with @pytest.mark.skipif) confirm
  that GET / and static assets are served correctly after
  `npm run build` has been executed in frontend/.

These tests must never break the existing 54 Phase 8 tests.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app, _FRONTEND_DIST


client = TestClient(app)

# ============================================================
# Helper
# ============================================================

DIST_EXISTS = _FRONTEND_DIST.exists()

skip_if_no_build = pytest.mark.skipif(
    not DIST_EXISTS,
    reason="frontend/dist/ not built yet — run: cd frontend && npm run build"
)


# ============================================================
# Pre-build: existing API endpoints must still be reachable
# ============================================================

class TestExistingEndpointsUnchanged:
    """
    Confirm Phase 8 endpoints are unaffected by Phase 9.1
    changes to main.py. These run regardless of build state.
    """

    def test_health_still_returns_200(self):
        """GET /health returns 200 after Phase 9.1 changes."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "model" in data

    def test_schema_returns_200_without_build(self):
        """GET /schema returns 200 regardless of build state."""
        response = client.get("/schema")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert len(data["tables"]) > 0

    def test_ask_endpoint_still_reachable(self):
        """POST /ask with invalid input still returns 422 (not 404)."""
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422

    def test_execute_endpoint_still_reachable(self):
        """POST /execute with dangerous SQL still returns 400."""
        response = client.post(
            "/execute",
            json={"sql": "DROP TABLE customers"}
        )
        assert response.status_code == 400


# ============================================================
# Pre-build: / should not 404 but may not serve HTML yet
# ============================================================

class TestRootBeforeBuild:

    def test_root_does_not_crash_server(self):
        """
        GET / must not cause a 500 error regardless of
        whether the frontend has been built.
        """
        response = client.get("/")
        # Either 200 (built) or 404 (not built) — never 500
        assert response.status_code in (200, 404)


# ============================================================
# Post-build: static file serving
# (skipped until npm run build has been executed)
# ============================================================

class TestFrontendServingAfterBuild:

    @skip_if_no_build
    def test_root_returns_200(self):
        """GET / returns HTTP 200 after build."""
        response = client.get("/")
        assert response.status_code == 200

    @skip_if_no_build
    def test_root_returns_html(self):
        """GET / returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    @skip_if_no_build
    def test_root_html_contains_react_root(self):
        """The served HTML includes the React mount point."""
        response = client.get("/")
        assert response.status_code == 200
        assert b'id="root"' in response.content

    @skip_if_no_build
    def test_root_html_contains_script_tag(self):
        """The served HTML includes a script tag pointing to the JS bundle."""
        response = client.get("/")
        assert b"<script" in response.content

    @skip_if_no_build
    def test_assets_directory_is_served(self):
        """
        The /assets/ mount returns a JS file from the build.
        Finds the first .js file in dist/assets/ and requests it.
        """
        js_files = list(_FRONTEND_DIST.glob("assets/*.js"))
        assert len(js_files) > 0, "No JS files found in frontend/dist/assets/"

        js_filename = js_files[0].name
        response = client.get(f"/assets/{js_filename}")
        assert response.status_code == 200

    @skip_if_no_build
    def test_assets_js_content_type(self):
        """JS assets are served with JavaScript content type."""
        js_files = list(_FRONTEND_DIST.glob("assets/*.js"))
        assert len(js_files) > 0

        js_filename = js_files[0].name
        response = client.get(f"/assets/{js_filename}")
        content_type = response.headers.get("content-type", "")
        assert "javascript" in content_type

    @skip_if_no_build
    def test_dist_index_html_exists(self):
        """frontend/dist/index.html exists after build."""
        index = _FRONTEND_DIST / "index.html"
        assert index.exists(), "frontend/dist/index.html not found"

    @skip_if_no_build
    def test_schema_still_works_after_build(self):
        """
        GET /schema returns correct data even after static
        files are mounted — confirms route ordering is correct.
        """
        response = client.get("/schema")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
