"""
Unit tests for security module.
"""
import pytest
from backend.core.security import TokenManager, create_token_hash


class TestTokenManager:
    """Test TokenManager class."""
    
    def test_generate_token(self):
        """Test token generation produces valid hex string."""
        tm = TokenManager()
        token = tm.generate()
        
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789abcdef' for c in token)
    
    def test_generate_unique_tokens(self):
        """Test that generated tokens are unique."""
        tm = TokenManager()
        tokens = {tm.generate() for _ in range(100)}
        assert len(tokens) == 100
    
    def test_validate_correct_token(self):
        """Test validation of correct token."""
        tm = TokenManager()
        token = tm.generate()
        assert tm.validate(token) is True
    
    def test_validate_incorrect_token(self):
        """Test validation rejects incorrect token."""
        tm = TokenManager()
        token = tm.generate()
        assert tm.validate(token + "x") is False
        assert tm.validate("wrong") is False
        assert tm.validate("") is False
    
    def test_validate_empty_token(self):
        """Test validation rejects empty token."""
        tm = TokenManager()
        assert tm.validate("") is False
        assert tm.validate(None) is False
    
    def test_token_hash_creation(self):
        """Test token hash is deterministic."""
        token = "test-token-123"
        hash1 = create_token_hash(token)
        hash2 = create_token_hash(token)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex
    
    def test_token_manager_singleton_behavior(self):
        """Test TokenManager maintains state."""
        tm = TokenManager()
        token = tm.generate()
        assert tm._token == token
        assert tm._token_hash == create_token_hash(token)
        assert tm._created_at is not None


class TestCreateTokenHash:
    """Test create_token_hash function."""
    
    def test_deterministic(self):
        """Same input produces same hash."""
        h1 = create_token_hash("test")
        h2 = create_token_hash("test")
        assert h1 == h2
    
    def test_different_inputs_different_hashes(self):
        """Different inputs produce different hashes."""
        h1 = create_token_hash("test1")
        h2 = create_token_hash("test2")
        assert h1 != h2
    
    def test_hash_length(self):
        """Hash is 64 characters (SHA256 hex)."""
        h = create_token_hash("test")
        assert len(h) == 64
    
    def test_hex_characters_only(self):
        """Hash contains only hex characters."""
        h = create_token_hash("test")
        assert all(c in '0123456789abcdef' for c in h)