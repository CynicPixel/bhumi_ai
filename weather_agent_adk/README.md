# Weather Agent for Indian Farmers

A specialized weather agent built with Google ADK that provides comprehensive weather information tailored for Indian farmers using the Open-Meteo API.

## Features

- Current weather conditions
- Weather forecasts (up to 16 days)
- Historical weather data
- Agricultural-specific insights:
  - Soil temperature and moisture
  - Solar radiation for crop growth
  - Wind conditions for pesticide spraying
  - Precipitation forecasts for irrigation planning
  - Frost warnings
  - Heat stress indicators

## Setup

1. Install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv install
```

2. Run the agent:
```bash
uv run .
```

The agent will be running on `http://localhost:10005`.

## Usage

The agent responds to natural language queries about weather conditions for farming. Examples:

- "What's the current weather in Delhi for farming?"
- "Will it rain in the next 3 days in Punjab?"
- "What's the soil temperature forecast for Maharashtra?"
- "Is it safe to spray pesticides tomorrow in Karnataka?"

## API Integration

This agent uses the Open-Meteo API which provides:
- Free access for non-commercial use
- Global weather data
- Multiple weather models
- High-resolution forecasts
- Historical data access
