# Arduino Code Generator API

## Overview
This project is a Flask-based API that generates fully functional and well-documented Arduino code based on user-provided project requirements. The system utilizes an AI model to analyze input parameters and generate code files, including a `.ino` sketch, a `README.md` documentation file, and optionally, a `config.h` configuration file.

## Features
- **Automatic Code Generation**: Converts project specifications into complete Arduino code.
- **Supports Multiple Components**: Handles different sensors, actuators, and MCUs.
- **Smart Defaults**: Fills in missing values with the best options.
- **Well-Documented Output**: Generates comments and documentation for better understanding.
- **Error Handling & Logging**: Provides detailed error messages and logs responses for debugging.

## Tech Stack
- **Backend**: Python (Flask)
- **AI Model**: OpenAI-compatible model via Groq API
- **Environment Management**: dotenv
- **Logging**: Python logging module

## Setup Instructions
### 1. Clone the Repository
```sh
 git clone https://github.com/your-repo/arduino-code-generator.git
 cd arduino-code-generator
```

### 2. Install Dependencies
Ensure you have Python 3 installed, then install the required packages:
```sh
 pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root and set your Groq API key:
```ini
GROQ_API_KEY=your_api_key_here
FLASK_DEBUG=True  # Set to False in production
```

### 4. Run the Application
```sh
 python app.py
```
By default, the app runs on `http://127.0.0.1:5000/`.

## API Endpoints
### 1. **Generate Arduino Code**
**Endpoint:** `POST /generate`

**Request Body (JSON format):**
```json
{
  "Project name": "Smart Garden Monitor",
  "Definition/use case": "Monitor soil moisture and control irrigation",
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

**Response (Example):**
```json
{
  "code.ino": "// Arduino code here...",
  "README.md": "# Project Documentation...",
  "config.h": "// Configuration constants..."
}
```

## Logging & Debugging
- All logs are saved in `app.log`.
- If `FLASK_DEBUG=True`, API responses are also logged in `debug_ai_response.json`.

## Deployment
For production, run the Flask app using Gunicorn:
```sh
 gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## License
This project is licensed under the MIT License.

