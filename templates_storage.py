import json
from typing import List
from models import Template

TEMPLATES_FILE = "templates.json"

def load_templates() -> List[Template]:
    """Load templates from JSON file."""
    try:
        with open(TEMPLATES_FILE, "r") as f:
            data = json.load(f)
            return [Template.from_dict(t) for t in data]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_templates(templates: List[Template]):
    """Save templates to JSON file."""
    with open(TEMPLATES_FILE, "w") as f:
        json.dump([t.to_dict() for t in templates], f, indent=2)

def get_template_by_alias(alias: str) -> Template:
    """Get a template by its alias."""
    templates = load_templates()
    for template in templates:
        if template.alias.lower() == alias.lower():
            return template
    return None
