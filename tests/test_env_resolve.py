"""Tests for envoy.env_resolve."""
import pytest
from envoy.env_resolve import EnvResolver, ResolveResult


@pytest.fixture
def resolver():
    return EnvResolver()


class TestResolveResult:
    def test_repr(self):
        r = ResolveResult(resolved={"A": "1"}, unresolved=["B"], expanded=["A"])
        assert "unresolved" in repr(r)
        assert "expanded" in repr(r)

    def test_is_clean_when_no_unresolved(self):
        r = ResolveResult(resolved={"A": "1"})
        assert r.is_clean is True

    def test_not_clean_when_unresolved(self):
        r = ResolveResult(resolved={}, unresolved=["MISSING"])
        assert r.is_clean is False


class TestEnvResolver:
    def test_no_references_unchanged(self, resolver):
        vars_ = {"HOST": "localhost", "PORT": "5432"}
        result = resolver.resolve(vars_)
        assert result.resolved == vars_
        assert result.unresolved == []
        assert result.expanded == []

    def test_dollar_brace_reference_expanded(self, resolver):
        vars_ = {"BASE": "http", "URL": "${BASE}://example.com"}
        result = resolver.resolve(vars_)
        assert result.resolved["URL"] == "http://example.com"
        assert "URL" in result.expanded

    def test_bare_dollar_reference_expanded(self, resolver):
        vars_ = {"HOST": "db", "DSN": "postgres://$HOST/mydb"}
        result = resolver.resolve(vars_)
        assert result.resolved["DSN"] == "postgres://db/mydb"

    def test_chained_references_resolved(self, resolver):
        vars_ = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
        result = resolver.resolve(vars_)
        assert result.resolved["C"] == "hello_world!"

    def test_unresolved_reference_reported(self, resolver):
        vars_ = {"URL": "${MISSING}/path"}
        result = resolver.resolve(vars_)
        assert "URL" in result.unresolved
        assert result.is_clean is False

    def test_external_context_used(self):
        r = EnvResolver(external={"BASE_URL": "https://api.example.com"})
        vars_ = {"ENDPOINT": "${BASE_URL}/v1"}
        result = r.resolve(vars_)
        assert result.resolved["ENDPOINT"] == "https://api.example.com/v1"
        assert result.is_clean is True

    def test_external_does_not_override_local(self):
        r = EnvResolver(external={"HOST": "remote"})
        vars_ = {"HOST": "local", "URL": "${HOST}:8080"}
        result = r.resolve(vars_)
        assert result.resolved["URL"] == "local:8080"

    def test_empty_vars_returns_empty_result(self, resolver):
        result = resolver.resolve({})
        assert result.resolved == {}
        assert result.unresolved == []
        assert result.expanded == []

    def test_multiple_refs_in_one_value(self, resolver):
        vars_ = {"PROTO": "https", "HOST": "example.com", "URL": "${PROTO}://${HOST}"}
        result = resolver.resolve(vars_)
        assert result.resolved["URL"] == "https://example.com"
