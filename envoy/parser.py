"""Parser for .env files."""

import re
from typing import Dict, List, Tuple


class EnvParser:
    """Parse and serialize .env file content."""

    @staticmethod
    def parse(content: str) -> Dict[str, str]:
        """Parse .env file content into a dictionary.
        
        Args:
            content: Raw .env file content
            
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        lines = content.splitlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
            
            # Match KEY=VALUE pattern
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
            if not match:
                i += 1
                continue
            
            key, value = match.groups()
            
            # Handle quoted values
            if value.startswith('"'):
                # Multi-line quoted value
                if not value.endswith('"') or len(value) == 1:
                    full_value = value
                    i += 1
                    while i < len(lines):
                        full_value += '\n' + lines[i]
                        if lines[i].rstrip().endswith('"'):
                            break
                        i += 1
                    value = full_value
                
                # Remove quotes and unescape
                value = value.strip('"').replace('\\n', '\n').replace('\\"', '"')
            elif value.startswith("'"):
                value = value.strip("'")
            
            env_vars[key] = value
            i += 1
        
        return env_vars

    @staticmethod
    def serialize(env_vars: Dict[str, str]) -> str:
        """Serialize environment variables to .env format.
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            Formatted .env file content
        """
        lines = []
        
        for key, value in sorted(env_vars.items()):
            # Quote values that contain special characters or newlines
            if '\n' in value or ' ' in value or '#' in value:
                escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                lines.append(f'{key}="{escaped_value}"')
            else:
                lines.append(f'{key}={value}')
        
        return '\n'.join(lines) + '\n' if lines else ''
