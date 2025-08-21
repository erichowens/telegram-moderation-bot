"""
Natural language rule parser for custom moderation policies.
Converts admin-written rules into executable moderation logic.
"""

import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RuleDocumentParser:
    """Parses natural language rule documents into structured moderation rules."""
    
    def __init__(self):
        self.rule_patterns = {
            'keyword_block': [
                r"don't allow (?:messages with )?[\"']([^\"']+)[\"']",
                r"block (?:any )?[\"']([^\"']+)[\"']",
                r"remove (?:messages containing )?[\"']([^\"']+)[\"']",
                r"ban (?:the word )?[\"']([^\"']+)[\"']"
            ],
            'url_block': [
                r"don't allow links to ([^\s]+)",
                r"block (?:all )?links? (?:to )?([^\s]+)",
                r"no links? (?:to )?([^\s]+)"
            ],
            'length_limit': [
                r"messages? (?:can't be |cannot be |should not be )?(?:longer than |more than )(\d+) (?:characters?|chars?)",
                r"limit messages? to (\d+) (?:characters?|chars?)",
                r"max(?:imum)? (?:message )?length (?:is )?(\d+)"
            ],
            'caps_limit': [
                r"no (?:excessive )?(?:all )?caps?",
                r"don't allow (?:all )?caps?",
                r"block (?:messages in )?(?:all )?caps?"
            ],
            'repetition_limit': [
                r"don't allow (?:repeated|repetitive|spam) messages?",
                r"block (?:repeated|repetitive) (?:content|messages?)",
                r"no (?:spam|repetitive content)"
            ],
            'time_based': [
                r"no (?:messages? )?(?:after|during) (\d+):?(\d+)?\s*(?:am|pm)?",
                r"block (?:messages? )?(?:between|from) (\d+):?(\d+)?\s*(?:am|pm)? (?:to|and) (\d+):?(\d+)?\s*(?:am|pm)?"
            ],
            'user_based': [
                r"new users? (?:can't|cannot) (?:post|send messages?) for (\d+) (?:days?|hours?|minutes?)",
                r"(?:members?|users?) (?:must|need) (\d+) (?:messages?|posts?) before (?:posting|sending) (?:links?|images?|videos?)"
            ]
        }
    
    def parse_document(self, rule_text: str) -> List[Dict[str, Any]]:
        """Parse a rule document into structured rules."""
        rules = []
        
        # Split document into sentences/lines
        sentences = re.split(r'[.!?\n]+', rule_text.strip())
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            parsed_rules = self.parse_sentence(sentence)
            rules.extend(parsed_rules)
        
        return rules
    
    def parse_sentence(self, sentence: str) -> List[Dict[str, Any]]:
        """Parse a single sentence into rules."""
        sentence = sentence.lower().strip()
        rules = []
        
        # Check each rule pattern type
        for rule_type, patterns in self.rule_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, sentence)
                if match:
                    rule = self._create_rule(rule_type, match, sentence)
                    if rule:
                        rules.append(rule)
        
        return rules
    
    def _create_rule(self, rule_type: str, match: re.Match, original_sentence: str) -> Optional[Dict[str, Any]]:
        """Create a structured rule from a pattern match."""
        
        if rule_type == 'keyword_block':
            keywords = [match.group(1)]
            return {
                'type': 'keyword',
                'keywords': keywords,
                'action': 'delete',
                'reason': f'Blocked keyword: {keywords[0]}',
                'confidence': 0.9,
                'category': 'custom',
                'source': original_sentence
            }
        
        elif rule_type == 'url_block':
            domain = match.group(1)
            return {
                'type': 'url',
                'pattern': f'.*{re.escape(domain)}.*',
                'action': 'delete',
                'reason': f'Blocked domain: {domain}',
                'confidence': 0.95,
                'category': 'custom',
                'source': original_sentence
            }
        
        elif rule_type == 'length_limit':
            max_length = int(match.group(1))
            return {
                'type': 'length',
                'max_length': max_length,
                'action': 'warn',
                'reason': f'Message too long (max {max_length} characters)',
                'confidence': 0.8,
                'category': 'custom',
                'source': original_sentence
            }
        
        elif rule_type == 'caps_limit':
            return {
                'type': 'caps',
                'max_caps_ratio': 0.5,
                'action': 'warn',
                'reason': 'Excessive use of capital letters',
                'confidence': 0.7,
                'category': 'custom',
                'source': original_sentence
            }
        
        elif rule_type == 'repetition_limit':
            return {
                'type': 'repetition',
                'max_similarity': 0.8,
                'time_window': 300,  # 5 minutes
                'action': 'delete',
                'reason': 'Repetitive/spam content',
                'confidence': 0.8,
                'category': 'custom',
                'source': original_sentence
            }
        
        # Add more rule types as needed
        
        return None
    
    def validate_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean up parsed rules."""
        valid_rules = []
        
        for rule in rules:
            if self._is_valid_rule(rule):
                valid_rules.append(rule)
            else:
                logger.warning(f"Invalid rule skipped: {rule}")
        
        return valid_rules
    
    def _is_valid_rule(self, rule: Dict[str, Any]) -> bool:
        """Check if a rule is valid."""
        required_fields = ['type', 'action', 'reason', 'confidence', 'category']
        
        for field in required_fields:
            if field not in rule:
                return False
        
        # Type-specific validation
        rule_type = rule['type']
        
        if rule_type == 'keyword' and 'keywords' not in rule:
            return False
        
        if rule_type == 'url' and 'pattern' not in rule:
            return False
        
        if rule_type == 'length' and 'max_length' not in rule:
            return False
        
        # Confidence should be between 0 and 1
        if not (0 <= rule['confidence'] <= 1):
            return False
        
        return True
    
    def export_rules(self, rules: List[Dict[str, Any]], filename: str):
        """Export rules to JSON file."""
        try:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(rules, f, indent=2)
            logger.info(f"Exported {len(rules)} rules to {filename}")
        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
    
    def import_rules(self, filename: str) -> List[Dict[str, Any]]:
        """Import rules from JSON file."""
        try:
            with open(filename, 'r') as f:
                rules = json.load(f)
            logger.info(f"Imported {len(rules)} rules from {filename}")
            return self.validate_rules(rules)
        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            return []


class RuleExample:
    """Example rule documents and their expected outputs."""
    
    @staticmethod
    def get_gaming_server_rules() -> str:
        return '''
        Gaming Server Rules:
        
        Don't allow "buy cheap coins" or "get free vbucks" messages.
        Block all links to suspicious-gaming-site.com and free-coins.net.
        Messages can't be longer than 500 characters.
        No excessive all caps.
        Don't allow repetitive messages.
        New users can't post links for 7 days.
        '''
    
    @staticmethod
    def get_professional_group_rules() -> str:
        return '''
        Professional Group Guidelines:
        
        Block "work from home" and "make money fast" spam.
        Don't allow links to mlm-site.com or pyramid-scheme.org.
        Remove messages containing "guaranteed income".
        Limit messages to 1000 characters.
        No messages after 10:00 PM or before 6:00 AM.
        Users need 5 messages before posting links.
        '''
    
    @staticmethod
    def get_family_chat_rules() -> str:
        return '''
        Family Chat Rules:
        
        Don't allow "inappropriate content" or adult language.
        Block any links to dating sites.
        No excessive caps.
        Messages should not be longer than 300 characters.
        Don't allow repetitive spam messages.
        '''


# Example usage
if __name__ == "__main__":
    parser = RuleDocumentParser()
    
    # Parse gaming server rules
    gaming_rules_text = RuleExample.get_gaming_server_rules()
    gaming_rules = parser.parse_document(gaming_rules_text)
    
    print(f"Parsed {len(gaming_rules)} rules from gaming server document:")
    for rule in gaming_rules:
        print(f"- {rule['type']}: {rule['reason']}")
    
    # Export to file
    parser.export_rules(gaming_rules, "config/gaming_rules.json")