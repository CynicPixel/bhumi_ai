# Weather Agent for Indian Farmers

A sophisticated agricultural weather intelligence agent built with Google ADK that provides comprehensive weather analysis tailored specifically for Indian farmers using the Open-Meteo API with advanced agricultural insights.

## 🎯 **7 Advanced Agricultural Weather Skills**

### 1. **Comprehensive Farm Conditions Analysis**
Complete agricultural dashboard including current weather, soil conditions, forecasts, and farming recommendations for any location

### 2. **Advanced Spraying Analysis & Timing** 
Professional analysis of optimal conditions for pesticide and herbicide application with detailed timing recommendations

### 3. **Optimal Planting Window Analysis**
Analyze soil and weather conditions to determine the best planting dates for specific crops

### 4. **Precision Irrigation Scheduling**
Generate detailed irrigation schedules based on weather forecasts, soil moisture, and crop water requirements

### 5. **Crop Disease Risk Assessment**
Analyze weather conditions to assess disease risk and provide prevention recommendations for crops

### 6. **Agricultural Weather Forecasts**
Detailed weather forecasts with agricultural insights for farming planning (1-16 days)

### 7. **Historical Weather Analysis**
Historical weather data for comparison, trend analysis, and agricultural planning

## 🛠️ **11 Technical Tools Available**
- **Foundation**: `resolve_location` - Location resolution for accurate weather data
- **Comprehensive Workflows**: `get_comprehensive_farm_conditions`, `get_advanced_spraying_analysis`, `get_optimal_planting_window`, `get_irrigation_scheduling_recommendation`, `get_crop_disease_risk_analysis`
- **Atomic Data Tools**: `get_current_weather_data`, `get_hourly_forecast_data`, `get_daily_forecast_data`, `get_soil_data`, `get_evapotranspiration_data`
- **Context Tools**: `get_conversation_context`, `get_last_conversation`

## Features

### 🌾 Agricultural-Specific Intelligence
- **Soil Analysis**: Temperature and moisture monitoring at multiple depths
- **Spraying Conditions**: Wind speed/direction analysis for safe pesticide application
- **Disease Risk**: Weather-based disease risk assessment and prevention
- **Irrigation Timing**: Precision water management recommendations
- **Planting Windows**: Optimal timing for crop planting based on conditions
- **Harvest Planning**: Weather-based harvest timing recommendations

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
