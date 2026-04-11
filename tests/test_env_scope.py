"""Tests for envoy.env_scope."""
import pytest
from envoy.env_scope import EnvScope, ScopeResult


@pytest.fixture
def scope() -> EnvScope:
    return EnvScope(
        scopes={
            "backend": ["DB_", "REDIS_", "SECRET_KEY"],
            "frontend": ["NEXT_PUBLIC_", "REACT_APP_"],
        }
    )


@pytest.fixture
def sample_vars() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "supersecret",
        "NEXT_PUBLIC_API_URL": "https://api.example.com",
        "REACT_APP_THEME": "dark",
        "LOG_LEVEL": "info",
        "PORT": "8080",
    }


class TestScopeResult:
    def test_repr(self):
        r = ScopeResult(scope="backend", included={"DB_HOST": "x"}, excluded_keys=["PORT"])
        assert "backend" in repr(r)
        assert "included=1" in repr(r)
        assert "excluded=1" in repr(r)


class TestEnvScope:
    def test_apply_backend_scope(self, scope, sample_vars):
        result = scope.apply(sample_vars, "backend")
        assert "DB_HOST" in result.included
        assert "DB_PORT" in result.included
        assert "REDIS_URL" in result.included
        assert "SECRET_KEY" in result.included
        assert "NEXT_PUBLIC_API_URL" not in result.included
        assert result.scope == "backend"

    def test_apply_frontend_scope(self, scope, sample_vars):
        result = scope.apply(sample_vars, "frontend")
        assert "NEXT_PUBLIC_API_URL" in result.included
        assert "REACT_APP_THEME" in result.included
        assert "DB_HOST" not in result.included

    def test_excluded_keys_are_populated(self, scope, sample_vars):
        result = scope.apply(sample_vars, "frontend")
        assert "DB_HOST" in result.excluded_keys
        assert "LOG_LEVEL" in result.excluded_keys

    def test_unknown_scope_returns_all_excluded(self, scope, sample_vars):
        result = scope.apply(sample_vars, "nonexistent")
        assert result.included == {}
        assert set(result.excluded_keys) == set(sample_vars.keys())

    def test_keys_for_scope(self, scope, sample_vars):
        keys = scope.keys_for_scope(sample_vars, "backend")
        assert "DB_HOST" in keys
        assert "NEXT_PUBLIC_API_URL" not in keys

    def test_unscoped_returns_ungrouped_vars(self, scope, sample_vars):
        unscoped = scope.unscoped(sample_vars)
        assert "LOG_LEVEL" in unscoped
        assert "PORT" in unscoped
        assert "DB_HOST" not in unscoped
        assert "NEXT_PUBLIC_API_URL" not in unscoped

    def test_register_new_scope(self, scope, sample_vars):
        scope.register("infra", ["LOG_", "PORT"])
        result = scope.apply(sample_vars, "infra")
        assert "LOG_LEVEL" in result.included
        assert "PORT" in result.included

    def test_list_scopes(self, scope):
        scopes = scope.list_scopes()
        assert "backend" in scopes
        assert "frontend" in scopes

    def test_exact_key_match(self):
        s = EnvScope(scopes={"auth": ["JWT_SECRET"]})
        vars = {"JWT_SECRET": "abc", "JWT_ALGO": "HS256"}
        result = s.apply(vars, "auth")
        assert "JWT_SECRET" in result.included
        assert "JWT_ALGO" not in result.included

    def test_empty_vars(self, scope):
        result = scope.apply({}, "backend")
        assert result.included == {}
        assert result.excluded_keys == []
