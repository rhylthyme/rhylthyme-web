#!/usr/bin/env python3
"""
Environment Icons Index

This module provides a mapping of environment types to appropriate FontAwesome icons
for use in visualizations and user interfaces.
"""

from typing import Dict, List, Optional

# Environment Types to FontAwesome Icons Mapping
ENVIRONMENT_ICONS: Dict[str, str] = {
    # Kitchen environments
    "kitchen": "fa-utensils",
    "home": "fa-house",
    "restaurant": "fa-utensils",
    "commercial-kitchen": "fa-fire-burner",

    # Laboratory environments
    "laboratory": "fa-flask",
    "lab": "fa-flask",
    "research": "fa-microscope",
    "biotech": "fa-dna",
    "pharma": "fa-pills",
    "medical": "fa-user-doctor",

    # Bakery environments
    "bakery": "fa-bread-slice",
    "artisan": "fa-wheat-awn",
    "pastry": "fa-cake-candles",

    # Airport environments
    "airport": "fa-plane",
    "aviation": "fa-plane-departure",
    "runway": "fa-plane-arrival",
    "terminal": "fa-building",

    # Event environments
    "event": "fa-calendar-days",
    "theater": "fa-masks-theater",
    "concert": "fa-music",
    "conference": "fa-users",
    "ceremony": "fa-award",

    # Additional environment types
    "manufacturing": "fa-industry",
    "warehouse": "fa-warehouse",
    "office": "fa-building",
    "hospital": "fa-hospital",
    "school": "fa-graduation-cap",
    "retail": "fa-store",
    "farm": "fa-tractor",
    "datacenter": "fa-server",
    "factory": "fa-gear",
    "workshop": "fa-screwdriver-wrench",
    "garage": "fa-car",
    "gym": "fa-dumbbell",
    "studio": "fa-microphone",
    "library": "fa-book",
    "garden": "fa-seedling",
    "greenhouse": "fa-leaf",
    "clinic": "fa-stethoscope",
    "spa": "fa-spa",
    "hotel": "fa-bed",
}

# Default icon for unknown environment types
DEFAULT_ENVIRONMENT_ICON = "fa-building"


def get_environment_icon(environment_type: str) -> str:
    """
    Get the FontAwesome icon class for a given environment type.

    Args:
        environment_type: The type of environment (e.g., 'kitchen', 'laboratory')

    Returns:
        FontAwesome icon class string (e.g., 'fa-utensils')
    """
    if not environment_type:
        return DEFAULT_ENVIRONMENT_ICON

    # Normalize the environment type (lowercase, handle common variations)
    normalized_type = environment_type.lower().strip()

    # Direct lookup
    if normalized_type in ENVIRONMENT_ICONS:
        return ENVIRONMENT_ICONS[normalized_type]

    # Try partial matches for compound names
    for env_type, icon in ENVIRONMENT_ICONS.items():
        if env_type in normalized_type or normalized_type in env_type:
            return icon

    # Return default if no match found
    return DEFAULT_ENVIRONMENT_ICON


def get_environment_icon_with_prefix(environment_type: str, prefix: str = "fas") -> str:
    """
    Get the complete FontAwesome icon class with prefix for a given environment type.

    Args:
        environment_type: The type of environment
        prefix: FontAwesome prefix (e.g., 'fas', 'far', 'fab')

    Returns:
        Complete FontAwesome icon class string (e.g., 'fas fa-utensils')
    """
    icon = get_environment_icon(environment_type)
    return f"{prefix} {icon}"
