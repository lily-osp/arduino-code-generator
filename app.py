from flask import Flask, request, render_template, jsonify
from functools import wraps
import json
import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv  # Import the load_dotenv function

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# Configuration
class Config:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_NAME = "mixtral-8x7b-32768"
    DEBUG_MODE = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    DEBUG_LOG_FILE = "debug_ai_response.json"
    DEFAULT_VALUE = "choose the best one"


# System Prompt for Arduino Code Generation
SYSTEM_PROMPT = """You are an Arduino expert specializing in generating complete, functional, and well-documented code for Arduino projects. For each request, follow these steps:

1. **Analyze Requirements**: Carefully evaluate the provided project requirements.
2. **Generate Code**: Create complete, properly structured, and functional code files.
3. **Documentation**: Include detailed comments in the code and provide clear, concise documentation.
4. **Best Practices**: Adhere to Arduino development best practices, including efficient memory usage, modularity, and readability.

**Output Format**:
- Return ONLY a JSON object containing the generated files.
- Do not include any explanations or text outside the JSON structure.

**Required Files**:
1. `code.ino`: The main Arduino sketch with complete `setup()` and `loop()` functions.
2. `README.md`: Project documentation, including wiring instructions (in simple written form) and a usage guide.
3. `config.h` (if needed): A header file for project-specific constants and configurations.

**Example Input**:
```json
{
  "Project name": "smart garden monitor",
  "Definition/use case": "monitor soil moisture and control irrigation",
  "Sensors": ["soil moisture", "DHT11"],
  "Actuators": ["water pump", "LCD"],
  "MCU": "Arduino Nano",
  "Other parameters": {
    "communication": "Serial",
    "control": "automatic",
    "timing": ["every 6 hours", "instant on low moisture"]
  }
}
```

**Expected Output Format**:
```json
{
  "code.ino": "// Complete Arduino code here...",
  "README.md": "# Project Documentation...",
  "config.h": "// Configuration constants..."
}
```

**Handling Ambiguity**:
- If any input parameters are missing or set to "choose the best one," use your expertise to select the most appropriate options based on the project requirements.
- Ensure the generated code is functional, efficient, and adheres to Arduino best practices.
"""


def require_api_key(f):
    """Decorator to check if API key is configured"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.GROQ_API_KEY:
            return jsonify(
                {
                    "error": "GROQ_API_KEY not configured. Please set the environment variable."
                }
            ), 500
        return f(*args, **kwargs)

    return decorated_function


def clean_input_value(value):
    """Clean input value, replacing None, empty strings, or 'null' with default value"""
    if value is None or value == "" or value == "null":
        return Config.DEFAULT_VALUE
    return value


def clean_list_value(value_list):
    """Clean list values, replacing empty lists with default value"""
    if not value_list or all(not item for item in value_list):
        return [Config.DEFAULT_VALUE]
    return [clean_input_value(item) for item in value_list if item]


def process_input_data(data):
    """Process and clean input data, replacing null/empty values with defaults"""
    cleaned_data = {
        "Project name": clean_input_value(data.get("Project name")),
        "Definition/use case": clean_input_value(data.get("Definition/use case")),
        "MCU": clean_input_value(data.get("MCU")),
        "Sensors": clean_list_value(data.get("Sensors", [])),
        "Actuators": clean_list_value(data.get("Actuators", [])),
        "Other parameters": {
            "communication": clean_input_value(
                data.get("Other parameters", {}).get("communication")
            ),
            "control": clean_input_value(
                data.get("Other parameters", {}).get("control")
            ),
            "timing": clean_list_value(
                data.get("Other parameters", {}).get("timing", [])
            ),
        },
    }
    return cleaned_data


def validate_input(data):
    """Validate the input data structure"""
    required_fields = ["Project name", "Definition/use case", "MCU"]

    for field in required_fields:
        if not data.get(field):
            data[field] = Config.DEFAULT_VALUE

    if not isinstance(data.get("Sensors", []), list):
        data["Sensors"] = [Config.DEFAULT_VALUE]

    if not isinstance(data.get("Actuators", []), list):
        data["Actuators"] = [Config.DEFAULT_VALUE]

    other_params = data.get("Other parameters", {})
    if not isinstance(other_params, dict):
        data["Other parameters"] = {
            "communication": Config.DEFAULT_VALUE,
            "control": Config.DEFAULT_VALUE,
            "timing": [Config.DEFAULT_VALUE],
        }


def log_debug_response(response_text):
    """Log API response for debugging"""
    if Config.DEBUG_MODE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.DEBUG_LOG_FILE}.{timestamp}"
        with open(filename, "w") as f:
            f.write(response_text)
        logger.debug(f"Debug response logged to {filename}")


@app.route("/")
def index():
    return render_template("index.html")


def clean_json_string(s):
    """Clean JSON string by properly escaping characters"""
    # First replace any invalid escapes
    s = s.replace("\\", "\\\\")  # Double up backslashes
    s = s.replace("\n", "\\n")  # Handle newlines
    s = s.replace("\r", "\\r")  # Handle carriage returns
    s = s.replace("\t", "\\t")  # Handle tabs
    s = s.replace('"', '\\"')  # Handle quotes
    return s


@app.route("/generate", methods=["POST"])
@require_api_key
def generate_code():
    try:
        user_input = request.json

        # Clean and process input data
        cleaned_input = process_input_data(user_input)
        validate_input(cleaned_input)

        logger.info(f"Processed input: {cleaned_input}")

        # Construct the API request payload
        payload = {
            "model": Config.MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(cleaned_input)},
            ],
        }

        # Headers for API request
        headers = {
            "Authorization": f"Bearer {Config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        # Make the API request
        logger.info(
            f"Making API request for project: {cleaned_input.get('Project name')}"
        )
        response = requests.post(
            Config.GROQ_API_URL, headers=headers, json=payload, timeout=30
        )

        response_text = response.text
        log_debug_response(response_text)

        # Handle API errors
        response.raise_for_status()

        # Parse response
        response_json = response.json()

        if "choices" not in response_json or not response_json["choices"]:
            raise ValueError("Invalid API response structure")

        ai_response = response_json["choices"][0]["message"]["content"]

        # Parse the AI response as JSON
        try:
            generated_files = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            raise ValueError("Unable to parse AI response as JSON")

        # Validate generated files
        if not isinstance(generated_files, dict) or not generated_files:
            raise ValueError("Invalid generated files structure")

        logger.info(
            f"Successfully generated code for project: {cleaned_input.get('Project name')}"
        )
        return jsonify(generated_files)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify(
            {"error": "Invalid JSON format in request or response", "details": str(e)}
        ), 400

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400

    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return jsonify(
            {"error": "Failed to communicate with the AI service", "details": str(e)}
        ), 503

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify(
            {
                "error": "An unexpected error occurred",
                "details": str(e) if Config.DEBUG_MODE else None,
            }
        ), 500


if __name__ == "__main__":
    # Log startup configuration
    logger.info(f"Starting application with debug mode: {Config.DEBUG_MODE}")
    logger.info(f"Using model: {Config.MODEL_NAME}")
    logger.info(
        f"GROQ_API_KEY: {'*' * len(Config.GROQ_API_KEY) if Config.GROQ_API_KEY else 'Not Configured'}"
    )

    app.run(
        debug=Config.DEBUG_MODE,
        host="0.0.0.0" if not Config.DEBUG_MODE else "127.0.0.1",
    )
