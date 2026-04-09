"""Tests for the EnvParser module."""

import pytest
from envoy.parser import EnvParser


class TestEnvParser:
    """Test cases for EnvParser."""

    def test_parse_simple_variables(self):
        """Test parsing simple key=value pairs."""
        content = """DATABASE_URL=postgres://localhost/mydb
API_KEY=secret123
DEBUG=true"""
        
        result = EnvParser.parse(content)
        
        assert result == {
            'DATABASE_URL': 'postgres://localhost/mydb',
            'API_KEY': 'secret123',
            'DEBUG': 'true'
        }

    def test_parse_with_comments_and_empty_lines(self):
        """Test parsing with comments and empty lines."""
        content = """# Database configuration
DATABASE_URL=postgres://localhost/mydb

# API settings
API_KEY=secret123
"""
        
        result = EnvParser.parse(content)
        
        assert result == {
            'DATABASE_URL': 'postgres://localhost/mydb',
            'API_KEY': 'secret123'
        }

    def test_parse_quoted_values(self):
        """Test parsing quoted values."""
        content = '''MESSAGE="Hello World"
PATH='/usr/local/bin'
COMPLEX="value with spaces and #hash"'''
        
        result = EnvParser.parse(content)
        
        assert result == {
            'MESSAGE': 'Hello World',
            'PATH': '/usr/local/bin',
            'COMPLEX': 'value with spaces and #hash'
        }

    def test_parse_multiline_values(self):
        """Test parsing multi-line quoted values."""
        content = '''PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----"'''
        
        result = EnvParser.parse(content)
        
        assert 'PRIVATE_KEY' in result
        assert '\n' in result['PRIVATE_KEY']
        assert 'BEGIN RSA PRIVATE KEY' in result['PRIVATE_KEY']

    def test_serialize_simple_variables(self):
        """Test serializing simple variables."""
        env_vars = {
            'DATABASE_URL': 'postgres://localhost/mydb',
            'API_KEY': 'secret123',
            'DEBUG': 'true'
        }
        
        result = EnvParser.serialize(env_vars)
        
        assert 'API_KEY=secret123' in result
        assert 'DATABASE_URL=postgres://localhost/mydb' in result
        assert 'DEBUG=true' in result

    def test_serialize_special_characters(self):
        """Test serializing values with special characters."""
        env_vars = {
            'MESSAGE': 'Hello World',
            'COMMENT': 'value with #hash'
        }
        
        result = EnvParser.serialize(env_vars)
        
        assert 'MESSAGE="Hello World"' in result
        assert 'COMMENT="value with #hash"' in result

    def test_roundtrip_consistency(self):
        """Test that parse and serialize are consistent."""
        original = {
            'DATABASE_URL': 'postgres://localhost/mydb',
            'API_KEY': 'secret123',
            'MESSAGE': 'Hello World'
        }
        
        serialized = EnvParser.serialize(original)
        parsed = EnvParser.parse(serialized)
        
        assert parsed == original
