def extract_fields(
    message: str,
    current_draft: dict,
    missing_fields: list[str],
) -> dict:
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[...],
        response_format={
            "type": "json_schema",
            "json_schema": {...},
        },
        reasoning_effort="low",
    )

    return json.loads(
        response.choices[0].message.content
    )