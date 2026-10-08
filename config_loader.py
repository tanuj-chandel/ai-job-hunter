"""
Configuration loader for AI Job Hunter.
Loads profile_config.yaml if present, or falls back to profile_config.example.yaml.
"""
import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "profile_config.yaml")
EXAMPLE_CONFIG_FILE = os.path.join(BASE_DIR, "profile_config.example.yaml")

def load_profile_config():
    target = CONFIG_FILE if os.path.exists(CONFIG_FILE) else EXAMPLE_CONFIG_FILE
    if not os.path.exists(target):
        return {}
    with open(target, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

_config_cache = None

def get_config():
    global _config_cache
    if _config_cache is None:
        _config_cache = load_profile_config()
    return _config_cache

def get_candidate_info():
    return get_config().get("candidate", {})

def get_fit_score_tiers():
    return get_config().get("fit_score_tiers", {})

def get_search_queries(portal=None):
    queries = get_config().get("search_queries", {})
    if portal:
        return queries.get(portal, [])
    return queries
