"""
Tests for the natural language rule parser.
Validates that plain English rules are correctly converted to structured policies.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rule_parser import RuleDocumentParser, RuleExample


class TestRuleDocumentParser:
    """Test the natural language rule parsing functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create a RuleDocumentParser instance."""
        return RuleDocumentParser()
    
    def test_parser_initialization(self, parser):
        """Test parser initialization and pattern loading."""
        assert hasattr(parser, 'rule_patterns')
        assert len(parser.rule_patterns) > 0
        
        # Check for expected pattern types
        expected_types = ['keyword_block', 'url_block', 'length_limit', 'caps_limit']
        for pattern_type in expected_types:
            assert pattern_type in parser.rule_patterns
            assert len(parser.rule_patterns[pattern_type]) > 0
    
    # Test keyword blocking rules
    
    def test_parse_keyword_blocking_simple(self, parser):
        """Test parsing simple keyword blocking rules."""
        test_cases = [
            "Don't allow 'spam messages'",
            "Block 'buy now'", 
            "Remove messages containing 'crypto scam'",
            "Ban the word 'forbidden'"
        ]
        
        for rule_text in test_cases:
            rules = parser.parse_sentence(rule_text)
            assert len(rules) >= 1
            
            rule = rules[0]
            assert rule['type'] == 'keyword'
            assert 'keywords' in rule
            assert len(rule['keywords']) > 0
            assert rule['action'] == 'delete'
            assert rule['confidence'] > 0
    
    def test_parse_keyword_blocking_multiple_quotes(self, parser):
        """Test parsing rules with multiple quoted keywords."""
        rule_text = "Don't allow 'spam' or 'scam' messages"
        rules = parser.parse_sentence(rule_text)
        
        # Should capture the first quoted keyword
        assert len(rules) >= 1
        rule = rules[0]
        assert rule['type'] == 'keyword'
        assert any('spam' in keyword.lower() for keyword in rule['keywords'])
    
    # Test URL blocking rules
    
    def test_parse_url_blocking(self, parser):
        """Test parsing URL blocking rules."""
        test_cases = [
            "Don't allow links to suspicious-site.com",
            "Block all links to scam-domain.net",
            "No links to malware-site.org"
        ]
        
        for rule_text in test_cases:
            rules = parser.parse_sentence(rule_text)
            assert len(rules) >= 1
            
            rule = rules[0]
            assert rule['type'] == 'url'
            assert 'pattern' in rule
            assert rule['confidence'] >= 0.9  # URL rules should be high confidence
    
    # Test length limit rules
    
    def test_parse_length_limits(self, parser):
        """Test parsing message length limit rules."""
        test_cases = [
            "Messages can't be longer than 500 characters",
            "Limit messages to 300 chars", 
            "Maximum message length is 1000",
            "Messages should not be more than 200 characters"
        ]
        
        for rule_text in test_cases:
            rules = parser.parse_sentence(rule_text)
            assert len(rules) >= 1
            
            rule = rules[0]
            assert rule['type'] == 'length'
            assert 'max_length' in rule
            assert isinstance(rule['max_length'], int)
            assert rule['max_length'] > 0
    
    # Test caps limit rules
    
    def test_parse_caps_limits(self, parser):
        """Test parsing excessive caps rules."""
        test_cases = [
            "No excessive caps",
            "Don't allow all caps",
            "Block messages in caps"
        ]
        
        for rule_text in test_cases:
            rules = parser.parse_sentence(rule_text)
            assert len(rules) >= 1
            
            rule = rules[0]
            assert rule['type'] == 'caps'
            assert 'max_caps_ratio' in rule
            assert 0 <= rule['max_caps_ratio'] <= 1
    
    # Test repetition rules
    
    def test_parse_repetition_rules(self, parser):
        """Test parsing anti-repetition rules."""
        test_cases = [
            "Don't allow repeated messages",
            "Block repetitive content",
            "No spam"
        ]
        
        for rule_text in test_cases:
            rules = parser.parse_sentence(rule_text)
            assert len(rules) >= 1
            
            rule = rules[0]
            assert rule['type'] == 'repetition'
            assert 'max_similarity' in rule or 'time_window' in rule
    
    # Test document parsing
    
    def test_parse_multi_sentence_document(self, parser):
        """Test parsing a document with multiple rules."""
        document = '''
        Community Rules:
        
        Don't allow "spam messages" or "buy crypto" content.
        Block all links to suspicious-site.com.
        Messages can't be longer than 500 characters.
        No excessive caps.
        '''
        
        rules = parser.parse_document(document)
        
        # Should parse multiple rules
        assert len(rules) >= 3
        
        # Check for different rule types
        rule_types = [rule['type'] for rule in rules]
        assert 'keyword' in rule_types
        assert 'url' in rule_types or 'length' in rule_types
    
    def test_parse_empty_document(self, parser):
        """Test parsing empty or whitespace-only documents."""
        empty_docs = ["", "   ", "\n\n\n", "   \t  \n  "]
        
        for doc in empty_docs:
            rules = parser.parse_document(doc)
            assert rules == []
    
    # Test rule validation
    
    def test_validate_valid_rules(self, parser):
        """Test validation of properly formed rules."""
        valid_rules = [
            {
                'type': 'keyword',
                'keywords': ['test'],
                'action': 'delete',
                'reason': 'Test rule',
                'confidence': 0.8,
                'category': 'custom'
            },
            {
                'type': 'url',
                'pattern': 'test.com',
                'action': 'warn',
                'reason': 'Blocked domain',
                'confidence': 0.9,
                'category': 'custom'
            }
        ]
        
        validated = parser.validate_rules(valid_rules)
        assert len(validated) == len(valid_rules)
        assert validated == valid_rules
    
    def test_validate_invalid_rules(self, parser):
        """Test validation rejection of malformed rules."""
        invalid_rules = [
            # Missing required fields
            {'type': 'keyword'},
            
            # Invalid confidence
            {
                'type': 'keyword',
                'keywords': ['test'],
                'action': 'delete',
                'reason': 'Test',
                'confidence': 1.5,  # Invalid
                'category': 'custom'
            },
            
            # Missing type-specific fields
            {
                'type': 'keyword',
                # Missing 'keywords' field
                'action': 'delete',
                'reason': 'Test',
                'confidence': 0.8,
                'category': 'custom'
            }
        ]
        
        validated = parser.validate_rules(invalid_rules)
        assert len(validated) == 0  # All rules should be rejected
    
    # Test file operations
    
    def test_export_and_import_rules(self, parser):
        """Test exporting and importing rules to/from files."""
        rules = [
            {
                'type': 'keyword',
                'keywords': ['test_export'],
                'action': 'delete',
                'reason': 'Test export rule',
                'confidence': 0.8,
                'category': 'custom',
                'source': 'test'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Test export
            parser.export_rules(rules, temp_file)
            assert Path(temp_file).exists()
            
            # Test import
            imported_rules = parser.import_rules(temp_file)
            assert len(imported_rules) == len(rules)
            assert imported_rules[0]['keywords'] == ['test_export']
        finally:
            # Cleanup
            if Path(temp_file).exists():
                Path(temp_file).unlink()
    
    def test_import_nonexistent_file(self, parser):
        """Test importing from a file that doesn't exist."""
        rules = parser.import_rules("nonexistent_file.json")
        assert rules == []
    
    def test_export_to_invalid_path(self, parser):
        """Test exporting to an invalid path."""
        rules = [{'type': 'test'}]
        
        # Should handle gracefully without raising exception
        parser.export_rules(rules, "/invalid/path/file.json")


class TestRuleExamples:
    """Test the predefined rule examples."""
    
    def test_gaming_server_rules(self):
        """Test gaming server rule example."""
        rules_text = RuleExample.get_gaming_server_rules()
        
        assert isinstance(rules_text, str)
        assert len(rules_text) > 0
        assert "gaming" in rules_text.lower() or "Gaming" in rules_text
    
    def test_professional_group_rules(self):
        """Test professional group rule example."""
        rules_text = RuleExample.get_professional_group_rules()
        
        assert isinstance(rules_text, str)
        assert len(rules_text) > 0
        assert "professional" in rules_text.lower() or "Professional" in rules_text
    
    def test_family_chat_rules(self):
        """Test family chat rule example."""
        rules_text = RuleExample.get_family_chat_rules()
        
        assert isinstance(rules_text, str)
        assert len(rules_text) > 0
        assert "family" in rules_text.lower() or "Family" in rules_text
    
    @pytest.fixture
    def parser(self):
        """Create parser for integration tests."""
        return RuleDocumentParser()
    
    def test_parse_gaming_example(self, parser):
        """Test parsing the gaming server example."""
        rules_text = RuleExample.get_gaming_server_rules()
        rules = parser.parse_document(rules_text)
        
        assert len(rules) > 0
        
        # Should contain various rule types
        rule_types = [rule['type'] for rule in rules]
        assert len(set(rule_types)) > 1  # Multiple different types
    
    def test_parse_professional_example(self, parser):
        """Test parsing the professional group example."""
        rules_text = RuleExample.get_professional_group_rules()
        rules = parser.parse_document(rules_text)
        
        assert len(rules) > 0
        
        # Professional rules should include MLM/spam detection
        rule_reasons = [rule.get('reason', '').lower() for rule in rules]
        combined_text = ' '.join(rule_reasons)
        assert any(keyword in combined_text for keyword in ['spam', 'mlm', 'pyramid', 'income'])


class TestRuleParserIntegration:
    """Integration tests for the complete rule parsing flow."""
    
    @pytest.fixture
    def parser(self):
        return RuleDocumentParser()
    
    def test_complex_rule_document(self, parser):
        """Test parsing a complex, realistic rule document."""
        complex_document = '''
        Community Moderation Guidelines
        
        Content Restrictions:
        - Don't allow "crypto investment" or "get rich quick" schemes
        - Block all links to suspicious-crypto-site.com and scam-domain.net
        - Remove messages containing "guaranteed profits"
        
        Message Limits:
        - Messages can't be longer than 2000 characters
        - No excessive all caps (shouting)
        - Don't allow repetitive spam messages
        
        Time-based Rules:
        - No messages after 11:00 PM
        - New users can't post links for 24 hours
        
        Special Cases:
        - Block any mention of "pyramid scheme"
        - Limit image posts to 5 per hour per user
        '''
        
        rules = parser.parse_document(complex_document)
        
        # Should extract multiple rules
        assert len(rules) >= 5
        
        # Verify different rule types are present
        rule_types = set(rule['type'] for rule in rules)
        assert 'keyword' in rule_types
        assert 'length' in rule_types or 'url' in rule_types
        
        # All rules should be valid
        validated_rules = parser.validate_rules(rules)
        assert len(validated_rules) == len(rules)
        
        # Test rule application logic
        for rule in rules:
            assert 'type' in rule
            assert 'reason' in rule
            assert 'confidence' in rule
            assert 0 <= rule['confidence'] <= 1
    
    def test_rule_parser_with_edge_cases(self, parser):
        """Test parser with edge cases and malformed input."""
        edge_cases = [
            "Don't allow messages with no quotes around keywords",
            "Block links without domain specified",
            "Messages can't be longer than invalid_number characters",
            "Random text that doesn't match any patterns",
            "Multiple 'quoted' words 'in' one 'sentence' should work",
            ""  # Empty string
        ]
        
        for case in edge_cases:
            # Should not raise exceptions
            rules = parser.parse_sentence(case)
            
            # Validate any extracted rules
            if rules:
                validated = parser.validate_rules(rules)
                # All extracted rules should be valid
                assert len(validated) == len(rules)
    
    def test_rule_parser_performance(self, parser):
        """Test parser performance with large documents."""
        # Create a large document with many rules
        large_document = "\n".join([
            f"Don't allow 'spam_{i}' messages" for i in range(100)
        ])
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        rules = parser.parse_document(large_document)
        end_time = time.time()
        
        # Should complete within 5 seconds
        assert end_time - start_time < 5.0
        
        # Should extract all rules
        assert len(rules) >= 50  # Should get most of them


if __name__ == "__main__":
    pytest.main([__file__, "-v"])