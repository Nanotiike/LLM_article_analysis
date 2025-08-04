import json
import re


def is_valid_json(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


def strip_openai_json(s):
    if is_valid_json(s):
        return s
    else:
        pattern = r"```json\s*\n(.*?)\n```"
        match = re.search(pattern, s, re.DOTALL)
        output = match.group(1).strip() if match else None

        # Check if the extracted output is valid JSON
        if output and is_valid_json(output):
            return output
        else:
            # Pattern to extract any JSON-like structure
            pattern = r'\{(?:[^{}"]|"[^"]*"|\d+|true|false|null)*\}'
            match = re.search(pattern, s, re.DOTALL)
            return match.group(0).strip() if match else None


def parse_json(s, m):
    try:
        if s:
            result = json.loads(s)
            return result
        else:
            return {"error": "Could not extract JSON from response", "raw_response": m}
    except json.JSONDecodeError as e:
        # Handle the case where the response isn't valid JSON
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {m}")
        print(f"Extracted JSON string: {s}")

        # Return a dictionary with error information
        return {"error": "Failed to parse response as JSON", "raw_response": m}
