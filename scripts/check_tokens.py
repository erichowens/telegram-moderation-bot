#!/usr/bin/env python3
"""
Pre-commit hook to check for hardcoded tokens and secrets.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns that might indicate hardcoded secrets
SECRET_PATTERNS = [
    # Telegram bot tokens
    (r'\d{9,10}:[A-Za-z0-9_-]{35}', 'Telegram Bot Token'),
    
    # Generic API keys
    (r'api[_-]?key\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']', 'API Key'),
    (r'secret[_-]?key\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']', 'Secret Key'),
    
    # AWS
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'aws[_-]?secret[_-]?access[_-]?key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']', 'AWS Secret Key'),
    
    # GitHub
    (r'ghp_[A-Za-z0-9]{36}', 'GitHub Personal Token'),
    (r'gho_[A-Za-z0-9]{36}', 'GitHub OAuth Token'),
    
    # Generic passwords
    (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded Password'),
    
    # Private keys
    (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', 'Private Key'),
]

# Files to exclude from checking
EXCLUDE_PATTERNS = [
    '*.pyc',
    '__pycache__',
    '.git',
    '.env.example',
    'test_*',
    '*_test.py',
]

def check_file(filepath: Path) -> List[Tuple[int, str, str]]:
    """Check a file for potential secrets."""
    violations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for pattern, description in SECRET_PATTERNS:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if it's not a comment or example
                        if not line.strip().startswith('#') and 'example' not in line.lower():
                            violations.append((i, description, line.strip()))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return violations

def main():
    """Main function to check all Python and config files."""
    violations_found = False
    
    # Get all Python and config files
    patterns = ['**/*.py', '**/*.yaml', '**/*.yml', '**/*.json', '**/*.env']
    files_to_check = []
    
    for pattern in patterns:
        files_to_check.extend(Path('.').glob(pattern))
    
    # Filter out excluded files
    files_to_check = [
        f for f in files_to_check 
        if not any(f.match(exclude) for exclude in EXCLUDE_PATTERNS)
    ]
    
    # Check each file
    for filepath in files_to_check:
        violations = check_file(filepath)
        
        if violations:
            violations_found = True
            print(f"\n❌ Potential secrets found in {filepath}:")
            for line_num, secret_type, line_content in violations:
                print(f"  Line {line_num}: {secret_type}")
                print(f"    {line_content[:100]}...")
    
    if violations_found:
        print("\n⚠️  Please remove hardcoded secrets and use environment variables instead!")
        print("Example: Use os.environ.get('TELEGRAM_BOT_TOKEN') instead of hardcoding the token.")
        sys.exit(1)
    else:
        print("✅ No hardcoded secrets detected")
        sys.exit(0)

if __name__ == "__main__":
    main()