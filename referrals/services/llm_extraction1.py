import json
import os

from collections.abc import Mapping, Sequence
from typing import Any

from groq import Groq


class GroqExtractionError(RuntimeError):
    """Raised when Groq cannot return a usable intake extraction."""


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "age": {
            "anyOf": [
                {"type": "integer", "minimum": 0},
                {"type": "null"},
            ]
        },
        "county": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "city": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "preferred_language": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "insurance_type": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "wheelchair": {
            "anyOf": [{"type": "boolean"}, {"type": "null"}]
        },
        "needs": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "food",
                    "food_delivery",
                    "healthcare",
                    "housing",
                    "transportation",
                ],
            },
        },
        "healthcare_specialties": {
            "type": "array",
            "items": {"type": "string"},
        },
        "population_context": {
            "type": "array",
            "items": {"type": "string"},
        },
        "service_modalities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "program_purposes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "age",
        "county",
        "city",
        "preferred_language",
        "insurance_type",
        "wheelchair",
        "needs",
        "healthcare_specialties",
        "population_context",
        "service_modalities",
        "program_purposes",
    ],
    "additionalProperties": False,
}