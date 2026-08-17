"""Model-facing schema for the Curupira Hermes plugin."""

CURUPIRA_LINT = {
    "name": "curupira_lint",
    "description": (
        "Run the local, deterministic Curupira preflight on changed Markdown or TXT files. "
        "Call this before declaring documentation work complete. Returns a structured "
        "preflight_completed event with input hashes, diagnostics, rules, versions, timing, "
        "and operational errors. This tool never calls semantic-review or a remote service."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "paths": {
                "type": "array",
                "description": "Changed file paths to classify and lint.",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 100,
                "uniqueItems": True,
            },
            "config_path": {
                "type": "string",
                "description": "Optional explicit Curupira TOML configuration path.",
            },
        },
        "required": ["paths"],
        "additionalProperties": False,
    },
}
