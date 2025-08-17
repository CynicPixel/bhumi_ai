import asyncio
import httpx
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from conversation_helper import get_conversation_helper
from request_context import request_context


class WeatherLocation(BaseModel):
    """Location information for weather queries"""
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location") 
    name: str = Field(..., description="Name of the location")


@dataclass
class EnhancedWeatherLocation:
    """Enhanced location model with full geographic data"""
    name: str
    latitude: float
    longitude: float
    elevation: float
    timezone: str
    country: str
    admin1: Optional[str] = None  # State/Province
    admin2: Optional[str] = None  # District/County


@dataclass
class WeatherData:
    """Structured weather data container"""
    current: Dict[str, Any]
    hourly: Dict[str, Any]
    daily: Dict[str, Any]
    timezone: str
    location: EnhancedWeatherLocation


@dataclass
class SoilData:
    """Soil conditions data"""
    temperature_0cm: List[float]
    temperature_6cm: List[float]
    moisture_0_1cm: List[float]
    moisture_1_3cm: List[float]
    timestamps: List[str]


class LocationService:
    """Handles location resolution using OpenMeteo Geocoding API"""
    
    @staticmethod
    async def resolve_location(query: str) -> EnhancedWeatherLocation:
        """Convert natural language location to precise coordinates using OpenMeteo Geocoding API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": query, 
                        "count": 5,  # Get multiple results for better matching
                        "language": "en", 
                        "format": "json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("results"):
                    # Use the first (best) result from the geocoding API
                    result = data["results"][0]
                    return EnhancedWeatherLocation(
                        name=result["name"],
                        latitude=result["latitude"],
                        longitude=result["longitude"],
                        elevation=result.get("elevation", 0.0),
                        timezone=result.get("timezone", "Asia/Kolkata"),
                        country=result.get("country", ""),
                        admin1=result.get("admin1"),
                        admin2=result.get("admin2")
                    )
                else:
                    raise ValueError(f"Location '{query}' not found in OpenMeteo Geocoding API")
                    
        except httpx.RequestError as e:
            raise ValueError(f"Error connecting to OpenMeteo Geocoding API: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"OpenMeteo Geocoding API returned error {e.response.status_code}")
        except ValueError:
            # Re-raise ValueError (location not found)
            raise
        except Exception as e:
            raise ValueError(f"Unexpected error resolving location '{query}': {str(e)}")


class OpenMeteoClient:
    """Centralized client for OpenMeteo API calls"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @staticmethod
    async def get_forecast_data(latitude: float, longitude: float, 
                               timezone: str, **params) -> Dict[str, Any]:
        """Generic forecast data fetcher"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            all_params = {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
                **params
            }
            response = await client.get(OpenMeteoClient.BASE_URL, params=all_params)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_historical_data(latitude: float, longitude: float,
                                 start_date: str, end_date: str,
                                 timezone: str, **params) -> Dict[str, Any]:
        """Generic historical data fetcher"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            all_params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "timezone": timezone,
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
                **params
            }
            response = await client.get(OpenMeteoClient.HISTORICAL_URL, params=all_params)
            response.raise_for_status()
            return response.json()


# Major Indian agricultural regions with coordinates
INDIAN_AGRICULTURAL_REGIONS = {
    "punjab": WeatherLocation(latitude=30.7333, longitude=76.7794, name="Punjab"),
    "haryana": WeatherLocation(latitude=29.0588, longitude=76.0856, name="Haryana"),
    "uttar pradesh": WeatherLocation(latitude=26.8467, longitude=80.9462, name="Uttar Pradesh"),
    "bihar": WeatherLocation(latitude=25.0961, longitude=85.3131, name="Bihar"),
    "west bengal": WeatherLocation(latitude=22.9868, longitude=87.8550, name="West Bengal"),
    "maharashtra": WeatherLocation(latitude=19.7515, longitude=75.7139, name="Maharashtra"),
    "karnataka": WeatherLocation(latitude=15.3173, longitude=75.7139, name="Karnataka"),
    "andhra pradesh": WeatherLocation(latitude=15.9129, longitude=79.7400, name="Andhra Pradesh"),
    "telangana": WeatherLocation(latitude=18.1124, longitude=79.0193, name="Telangana"),
    "tamil nadu": WeatherLocation(latitude=11.1271, longitude=78.6569, name="Tamil Nadu"),
    "kerala": WeatherLocation(latitude=10.8505, longitude=76.2711, name="Kerala"),
    "gujarat": WeatherLocation(latitude=22.2587, longitude=71.1924, name="Gujarat"),
    "rajasthan": WeatherLocation(latitude=27.0238, longitude=74.2179, name="Rajasthan"),
    "madhya pradesh": WeatherLocation(latitude=22.9734, longitude=78.6569, name="Madhya Pradesh"),
    "odisha": WeatherLocation(latitude=20.9517, longitude=85.0985, name="Odisha"),
    "jharkhand": WeatherLocation(latitude=23.6102, longitude=85.2799, name="Jharkhand"),
    "chhattisgarh": WeatherLocation(latitude=21.2787, longitude=81.8661, name="Chhattisgarh"),
    "assam": WeatherLocation(latitude=26.2006, longitude=92.9376, name="Assam"),
    "delhi": WeatherLocation(latitude=28.7041, longitude=77.1025, name="Delhi"),
    "chandigarh": WeatherLocation(latitude=30.7333, longitude=76.7794, name="Chandigarh"),
    "mumbai": WeatherLocation(latitude=19.0760, longitude=72.8777, name="Mumbai"),
    "bangalore": WeatherLocation(latitude=12.9716, longitude=77.5946, name="Bangalore"),
    "hyderabad": WeatherLocation(latitude=17.3850, longitude=78.4867, name="Hyderabad"),
    "chennai": WeatherLocation(latitude=13.0827, longitude=80.2707, name="Chennai"),
    "kolkata": WeatherLocation(latitude=22.5726, longitude=88.3639, name="Kolkata"),
}


def get_weather_description(weather_code: int) -> str:
    """Enhanced weather code mapping with agricultural context"""
    weather_codes = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Fog 🌫️",
        48: "Depositing rime fog 🌫️❄️",
        51: "Light drizzle 🌦️",
        53: "Moderate drizzle 🌦️",
        55: "Dense drizzle 🌧️",
        56: "Light freezing drizzle 🧊🌦️",
        57: "Dense freezing drizzle 🧊🌧️",
        61: "Slight rain 🌧️",
        63: "Moderate rain 🌧️",
        65: "Heavy rain ⛈️",
        66: "Light freezing rain 🧊🌧️",
        67: "Heavy freezing rain 🧊⛈️",
        71: "Slight snow ❄️",
        73: "Moderate snow ❄️",
        75: "Heavy snow ❄️",
        77: "Snow grains ❄️",
        80: "Slight rain showers 🌦️",
        81: "Moderate rain showers 🌧️",
        82: "Violent rain showers ⛈️",
        85: "Slight snow showers ❄️",
        86: "Heavy snow showers ❄️",
        95: "Thunderstorm ⛈️",
        96: "Thunderstorm with slight hail ⛈️🧊",
        99: "Thunderstorm with heavy hail ⛈️🧊"
    }
    return weather_codes.get(weather_code, f"Unknown weather (code: {weather_code})")


def parse_location(location_query: str) -> WeatherLocation:
    """Parse location from user query and return coordinates"""
    location_lower = location_query.lower().strip()
    
    # Check if it's a known region
    for region_key, region_data in INDIAN_AGRICULTURAL_REGIONS.items():
        if region_key in location_lower or region_data.name.lower() in location_lower:
            return region_data
    
    # Default to Delhi if location not found
    return INDIAN_AGRICULTURAL_REGIONS["delhi"]


async def get_current_weather_conditions(location: str) -> str:
    """
    Get current weather conditions suitable for farming activities.
    
    Args:
        location: Name of the location (Indian state/city)
    
    Returns:
        Current weather information formatted for farmers
    """
    try:
        loc = parse_location(location)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get current weather with all relevant farming parameters
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "current": [
                    "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                    "precipitation", "rain", "weather_code", "cloud_cover",
                    "surface_pressure", "wind_speed_10m", "wind_direction_10m",
                    "wind_gusts_10m", "is_day"
                ],
                "timezone": "Asia/Kolkata",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data["current"]
            
            # Format weather conditions for farmers
            weather_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with hail"
            }
            
            weather_desc = weather_codes.get(current["weather_code"], "Unknown")
            day_night = "Day" if current["is_day"] else "Night"
            
            # Agricultural insights
            insights = []
            
            # Temperature insights
            temp = current["temperature_2m"]
            if temp > 35:
                insights.append("🌡️ High temperature - Consider heat stress protection for crops and livestock")
            elif temp < 10:
                insights.append("❄️ Low temperature - Risk of frost damage to sensitive crops")
            
            # Humidity insights
            humidity = current["relative_humidity_2m"]
            if humidity > 85:
                insights.append("💧 High humidity - Increased risk of fungal diseases")
            elif humidity < 30:
                insights.append("🏜️ Low humidity - Crops may need additional irrigation")
            
            # Wind insights
            wind_speed = current["wind_speed_10m"]
            if wind_speed > 25:
                insights.append("💨 Strong winds - Not suitable for pesticide/herbicide spraying")
            elif wind_speed < 5:
                insights.append("🌱 Low wind - Good conditions for spraying, but check for temperature inversions")
            
            # Precipitation insights
            if current["precipitation"] > 0:
                insights.append("🌧️ Current precipitation - Field work may be limited")
            
            result = f"""📍 Current Weather for {loc.name}:

🌡️ Temperature: {temp}°C (Feels like: {current['apparent_temperature']}°C)
💧 Humidity: {humidity}%
🌤️ Conditions: {weather_desc} ({day_night})
☁️ Cloud Cover: {current['cloud_cover']}%
🌬️ Wind: {wind_speed} km/h from {current['wind_direction_10m']}°
💨 Wind Gusts: {current['wind_gusts_10m']} km/h
🌧️ Precipitation: {current['precipitation']} mm
🔧 Pressure: {current['surface_pressure']} hPa

🌾 Agricultural Insights:
""" + "\n".join(f"• {insight}" for insight in insights) if insights else "• Weather conditions are generally suitable for normal farming activities"
            
            return result
            
    except Exception as e:
        return f"❌ Error getting current weather for {location}: {str(e)}"


async def get_weather_forecast(location: str, days: int = 7) -> str:
    """
    Get weather forecast for farming planning.
    
    Args:
        location: Name of the location (Indian state/city)
        days: Number of days to forecast (1-16)
    
    Returns:
        Weather forecast formatted for agricultural planning
    """
    try:
        loc = parse_location(location)
        days = min(max(days, 1), 16)  # Limit between 1-16 days
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "daily": [
                    "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                    "rain_sum", "weather_code", "wind_speed_10m_max", "wind_gusts_10m_max",
                    "sunshine_duration", "precipitation_probability_max", "uv_index_max"
                ],
                "forecast_days": days,
                "timezone": "Asia/Kolkata",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data["daily"]
            
            result = f"📊 {days}-Day Weather Forecast for {loc.name}:\n\n"
            
            for i in range(len(daily["time"])):
                date_str = daily["time"][i]
                date_obj = datetime.fromisoformat(date_str).date()
                day_name = date_obj.strftime("%A")
                
                max_temp = daily["temperature_2m_max"][i]
                min_temp = daily["temperature_2m_min"][i]
                precip = daily["precipitation_sum"][i]
                rain = daily["rain_sum"][i]
                precip_prob = daily["precipitation_probability_max"][i]
                wind_max = daily["wind_speed_10m_max"][i]
                sunshine = daily["sunshine_duration"][i] / 3600  # Convert to hours
                uv_index = daily["uv_index_max"][i]
                
                # Agricultural recommendations
                recommendations = []
                
                if precip > 10:
                    recommendations.append("Heavy rain expected - postpone field operations")
                elif precip_prob > 70:
                    recommendations.append("High chance of rain - plan indoor activities")
                elif precip_prob < 20 and precip < 1:
                    recommendations.append("Dry conditions - consider irrigation")
                
                if max_temp > 35:
                    recommendations.append("Hot day - provide shade for livestock")
                elif min_temp < 10:
                    recommendations.append("Cold night - protect sensitive crops")
                
                if wind_max > 20:
                    recommendations.append("Windy conditions - avoid spraying")
                else:
                    recommendations.append("Good conditions for spraying")
                
                if sunshine > 8:
                    recommendations.append("Excellent sunshine for crop growth")
                elif sunshine < 4:
                    recommendations.append("Limited sunshine - monitor plant health")
                
                result += f"""📅 {day_name}, {date_obj.strftime('%B %d')}:
   🌡️ {min_temp}°C - {max_temp}°C | 🌧️ {precip}mm ({precip_prob}% chance)
   🌬️ Wind: {wind_max} km/h | ☀️ Sunshine: {sunshine:.1f}h | 🌞 UV: {uv_index}
   🌾 Tips: {' | '.join(recommendations)}

"""
            
            return result
            
    except Exception as e:
        return f"❌ Error getting forecast for {location}: {str(e)}"


async def get_soil_conditions(location: str, days: int = 3) -> str:
    """
    Get soil temperature and moisture conditions for planting decisions.
    
    Args:
        location: Name of the location (Indian state/city)
        days: Number of days to forecast (1-7)
    
    Returns:
        Soil conditions formatted for planting and cultivation decisions
    """
    try:
        loc = parse_location(location)
        days = min(max(days, 1), 7)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "hourly": [
                    "soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm",
                    "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm"
                ],
                "forecast_days": days,
                "timezone": "Asia/Kolkata",
                "temperature_unit": "celsius"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            hourly = data["hourly"]
            
            # Calculate daily averages
            hours_per_day = 24
            result = f"🌱 Soil Conditions for {loc.name} (Next {days} days):\n\n"
            
            for day in range(days):
                start_idx = day * hours_per_day
                end_idx = start_idx + hours_per_day
                
                # Calculate averages for the day
                soil_temp_0cm = sum(hourly["soil_temperature_0cm"][start_idx:end_idx]) / hours_per_day
                soil_temp_6cm = sum(hourly["soil_temperature_6cm"][start_idx:end_idx]) / hours_per_day
                soil_temp_18cm = sum(hourly["soil_temperature_18cm"][start_idx:end_idx]) / hours_per_day
                
                soil_moisture_0_1cm = sum(hourly["soil_moisture_0_to_1cm"][start_idx:end_idx]) / hours_per_day
                soil_moisture_1_3cm = sum(hourly["soil_moisture_1_to_3cm"][start_idx:end_idx]) / hours_per_day
                soil_moisture_3_9cm = sum(hourly["soil_moisture_3_to_9cm"][start_idx:end_idx]) / hours_per_day
                
                date_obj = datetime.fromisoformat(hourly["time"][start_idx]).date()
                day_name = date_obj.strftime("%A, %B %d")
                
                # Soil analysis for farming
                analysis = []
                
                # Temperature analysis
                if soil_temp_0cm < 15:
                    analysis.append("Soil too cold for most seed germination")
                elif soil_temp_0cm > 30:
                    analysis.append("Soil may be too hot for some crops")
                else:
                    analysis.append("Good soil temperature for planting")
                
                # Moisture analysis
                if soil_moisture_0_1cm < 0.1:
                    analysis.append("Surface soil very dry - irrigation needed")
                elif soil_moisture_0_1cm > 0.4:
                    analysis.append("Surface soil saturated - may need drainage")
                else:
                    analysis.append("Good surface soil moisture")
                
                if soil_moisture_3_9cm < 0.2:
                    analysis.append("Root zone soil dry - deep irrigation recommended")
                elif soil_moisture_3_9cm > 0.45:
                    analysis.append("Root zone saturated - avoid heavy machinery")
                
                result += f"""📅 {day_name}:
   🌡️ Soil Temperature:
      Surface (0cm): {soil_temp_0cm:.1f}°C
      Shallow (6cm): {soil_temp_6cm:.1f}°C  
      Medium (18cm): {soil_temp_18cm:.1f}°C
   
   💧 Soil Moisture:
      Surface (0-1cm): {soil_moisture_0_1cm:.3f} m³/m³
      Shallow (1-3cm): {soil_moisture_1_3cm:.3f} m³/m³
      Root zone (3-9cm): {soil_moisture_3_9cm:.3f} m³/m³
   
   🌾 Analysis: {' | '.join(analysis)}

"""
            
            return result
            
    except Exception as e:
        return f"❌ Error getting soil conditions for {location}: {str(e)}"


async def get_spraying_conditions(location: str, hours: int = 24) -> str:
    """
    Get detailed conditions for pesticide/herbicide spraying decisions.
    
    Args:
        location: Name of the location (Indian state/city)
        hours: Number of hours to forecast (1-72)
    
    Returns:
        Spraying conditions and recommendations
    """
    try:
        loc = parse_location(location)
        hours = min(max(hours, 1), 72)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "hourly": [
                    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                    "wind_direction_10m", "wind_gusts_10m", "precipitation",
                    "precipitation_probability", "is_day"
                ],
                "forecast_hours": hours,
                "timezone": "Asia/Kolkata",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            hourly = data["hourly"]
            
            result = f"🚁 Spraying Conditions for {loc.name} (Next {hours} hours):\n\n"
            
            # Find optimal spraying windows
            optimal_hours = []
            good_hours = []
            poor_hours = []
            
            for i in range(len(hourly["time"])):
                time_str = hourly["time"][i]
                dt = datetime.fromisoformat(time_str)
                
                temp = hourly["temperature_2m"][i]
                humidity = hourly["relative_humidity_2m"][i]
                wind_speed = hourly["wind_speed_10m"][i]
                wind_gusts = hourly["wind_gusts_10m"][i]
                precip = hourly["precipitation"][i]
                precip_prob = hourly["precipitation_probability"][i]
                is_day = hourly["is_day"][i]
                
                # Scoring criteria for spraying - adapted for Indian climate reality
                score = 0
                reasons = []
                
                # --- REVISED TEMPERATURE LOGIC ---
                # Tiered risk assessment for practical, actionable advice in India
                if temp < 29:
                    score += 2  # Good conditions
                elif 29 <= temp <= 35:
                    score -= 1  # Caution Zone
                    reasons.append(f"🌡️ High Temp ({temp}°C): Risk of evaporation. Spray only during coolest hours (early morning/late evening)")
                else:  # temp > 35°C
                    score -= 3  # High-Risk Zone
                    reasons.append(f"🌡️ VERY High Temp ({temp}°C): Spraying not recommended due to severe evaporation risk")
                
                # Humidity (still important, especially when hot)
                if humidity < 40:
                    score -= 2
                    reasons.append(f"💧 Low Humidity ({humidity}%): Further increases evaporation. Avoid spraying")
                elif humidity < 50:
                    reasons.append(f"💧 Humidity ({humidity}%) is low, increasing evaporation risk")
                elif 50 <= humidity <= 85:
                    score += 1  # Good humidity range
                else:  # humidity > 85
                    score -= 1
                    reasons.append(f"💧 High Humidity ({humidity}%): Risk of fungal disease spread")
                
                # Wind speed (remains a critical factor for drift)
                if 3 <= wind_speed <= 15:
                    score += 2
                elif wind_speed < 3:
                    reasons.append(f"🌬️ Low Wind ({wind_speed} km/h): Risk of temperature inversion. Be cautious")
                else:  # wind_speed > 15
                    score -= 2
                    reasons.append(f"🌬️ High Wind ({wind_speed} km/h): High risk of drift")
                
                # Wind gusts
                if wind_gusts > 20:
                    score -= 2
                    reasons.append(f"Strong gusts {wind_gusts} km/h")
                
                # Time of Day (Crucial for managing high temperatures)
                if 11 <= dt.hour <= 16:  # Hottest part of the day
                    score -= 2
                    reasons.append("☀️ Midday: Avoid spraying during the hottest hours")
                elif dt.hour <= 10 or dt.hour >= 17:  # Early morning or late evening
                    score += 1
                
                # Precipitation
                if precip > 0:
                    score -= 4  # Increased penalty
                    reasons.append("🌧️ Raining Now: Do not spray")
                elif precip_prob > 50:
                    score -= 1
                    reasons.append(f"🌧️ {precip_prob}% rain chance later")
                
                # Day/night preference
                if is_day:
                    if 6 <= dt.hour <= 10 or 16 <= dt.hour <= 19:
                        score += 1  # Early morning or evening
                    elif 11 <= dt.hour <= 15:
                        score -= 1  # Hot midday
                        reasons.append("Midday - evaporation risk")
                else:
                    score -= 1
                    reasons.append("Night spraying")
                
                hour_info = {
                    'time': dt.strftime("%a %H:%M"),
                    'score': score,
                    'temp': temp,
                    'humidity': humidity,
                    'wind': wind_speed,
                    'gusts': wind_gusts,
                    'precip_prob': precip_prob,
                    'reasons': reasons
                }
                
                if score >= 3:
                    optimal_hours.append(hour_info)
                elif score >= 0:
                    good_hours.append(hour_info)
                else:
                    poor_hours.append(hour_info)
            
            # Report optimal windows
            if optimal_hours:
                result += "✅ OPTIMAL Spraying Times:\n"
                for hour in optimal_hours[:6]:  # Show first 6
                    result += f"   🕐 {hour['time']}: {hour['temp']}°C, {hour['humidity']}%, {hour['wind']} km/h wind\n"
                result += "\n"
            
            if good_hours:
                result += "⚠️ ACCEPTABLE Spraying Times:\n"
                for hour in good_hours[:4]:  # Show first 4
                    issues = ", ".join(hour['reasons']) if hour['reasons'] else "Minor issues"
                    result += f"   🕐 {hour['time']}: {hour['temp']}°C, {hour['humidity']}%, {hour['wind']} km/h - {issues}\n"
                result += "\n"
            
            result += "🚫 AVOID Spraying During:\n"
            for hour in poor_hours[:3]:  # Show first 3 poor conditions
                issues = ", ".join(hour['reasons'])
                result += f"   ❌ {hour['time']}: {issues}\n"
            
            result += f"\n💡 General Recommendations for Indian Conditions:\n"
            result += f"• Best spraying: Early morning (6-10 AM) or late evening (5-8 PM) to avoid heat\n"
            result += f"• In hot weather (>29°C), use nozzles that create larger droplets and consider using an adjuvant to reduce evaporation\n"
            result += f"• Avoid spraying in winds above 15 km/h to prevent drift\n"
            result += f"• Never spray during rain or when rain is imminent\n"
            result += f"• Check wind direction to avoid drift to sensitive areas\n"
            
            return result
            
    except Exception as e:
        return f"❌ Error getting spraying conditions for {location}: {str(e)}"


async def get_historical_weather(location: str, start_date: str, end_date: str) -> str:
    """
    Get historical weather data for comparison and planning.
    
    Args:
        location: Name of the location (Indian state/city)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Historical weather summary for agricultural reference
    """
    try:
        loc = parse_location(location)
        
        # Validate dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_dt >= end_dt:
            return "❌ Start date must be before end date"
        
        if end_dt >= date.today():
            return "❌ End date must be in the past for historical data"
        
        # Limit to 1 year of data to avoid huge responses
        if (end_dt - start_dt).days > 365:
            return "❌ Date range too large. Please limit to 1 year maximum"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = "https://archive-api.open-meteo.com/v1/era5"
            params = {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "start_date": start_date,
                "end_date": end_date,
                "daily": [
                    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
                    "precipitation_sum", "rain_sum", "sunshine_duration",
                    "wind_speed_10m_max", "et0_fao_evapotranspiration"
                ],
                "timezone": "Asia/Kolkata",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data["daily"]
            
            # Calculate statistics
            temps_max = daily["temperature_2m_max"]
            temps_min = daily["temperature_2m_min"]
            temps_mean = daily["temperature_2m_mean"]
            precip = daily["precipitation_sum"]
            rain = daily["rain_sum"]
            sunshine = [s / 3600 for s in daily["sunshine_duration"]]  # Convert to hours
            wind_max = daily["wind_speed_10m_max"]
            et0 = daily["et0_fao_evapotranspiration"]
            
            # Statistics
            avg_temp_max = sum(temps_max) / len(temps_max)
            avg_temp_min = sum(temps_min) / len(temps_min)
            avg_temp_mean = sum(temps_mean) / len(temps_mean)
            total_precip = sum(precip)
            total_rain = sum(rain)
            avg_sunshine = sum(sunshine) / len(sunshine)
            avg_wind = sum(wind_max) / len(wind_max)
            total_et0 = sum(et0)
            
            rainy_days = len([p for p in precip if p > 1])
            dry_days = len(precip) - rainy_days
            
            result = f"""📊 Historical Weather Summary for {loc.name}
📅 Period: {start_date} to {end_date} ({len(daily['time'])} days)

🌡️ TEMPERATURE:
   • Average Maximum: {avg_temp_max:.1f}°C
   • Average Minimum: {avg_temp_min:.1f}°C  
   • Average Daily: {avg_temp_mean:.1f}°C
   • Highest: {max(temps_max):.1f}°C
   • Lowest: {min(temps_min):.1f}°C

🌧️ PRECIPITATION:
   • Total Precipitation: {total_precip:.1f} mm
   • Total Rainfall: {total_rain:.1f} mm
   • Rainy Days (>1mm): {rainy_days} days
   • Dry Days: {dry_days} days
   • Average per rainy day: {total_rain/rainy_days if rainy_days > 0 else 0:.1f} mm

☀️ SUNSHINE & WIND:
   • Average Daily Sunshine: {avg_sunshine:.1f} hours
   • Average Max Wind Speed: {avg_wind:.1f} km/h

💧 EVAPOTRANSPIRATION:
   • Total ET₀: {total_et0:.1f} mm
   • Daily Average ET₀: {total_et0/len(et0):.1f} mm

🌾 AGRICULTURAL INSIGHTS:
"""
            
            # Agricultural insights based on historical data
            insights = []
            
            if avg_temp_mean > 25:
                insights.append("• High average temperatures - heat-tolerant crops recommended")
            elif avg_temp_mean < 15:
                insights.append("• Cool period - suitable for cool-season crops")
            else:
                insights.append("• Moderate temperatures - suitable for most crops")
            
            if total_precip < 200:
                insights.append("• Low precipitation period - irrigation was likely essential")
            elif total_precip > 1000:
                insights.append("• High precipitation period - drainage may have been needed")
            else:
                insights.append("• Moderate precipitation - generally good for rain-fed crops")
            
            if avg_sunshine > 8:
                insights.append("• Excellent sunshine duration - good for photosynthesis")
            elif avg_sunshine < 5:
                insights.append("• Limited sunshine - may have affected crop growth")
            
            if total_et0 > 500:
                insights.append("• High evapotranspiration - crops needed significant water")
            elif total_et0 < 200:
                insights.append("• Low evapotranspiration - water requirements were minimal")
            
            result += "\n".join(insights)
            
            return result
            
    except ValueError as e:
        return f"❌ Invalid date format. Please use YYYY-MM-DD format: {str(e)}"
    except Exception as e:
        return f"❌ Error getting historical weather for {location}: {str(e)}"


async def get_last_conversation(limit: int = 5) -> str:
    """
    Get the last N conversations for the current user and session to provide context.
    
    Args:
        limit: Maximum number of recent conversations to retrieve (default: 5)
    
    Returns:
        Formatted conversation history for context
    """
    try:
        # Get user_id and session_id from the current request context
        user_id = request_context.get_user_id()
        session_id = request_context.get_session_id()
        
        if not user_id or not session_id:
            return "📝 No user or session context available for conversation history."
        
        helper = get_conversation_helper()
        
        # Get last conversations
        conversations = helper.get_last_conversations(user_id, session_id, limit)
        
        if not conversations:
            return "📝 No previous conversation history found for this session."
        
        # Format conversations in a clear, readable way
        result = f"📚 Last {len(conversations)} Conversations for User: {user_id}, Session: {session_id}\n"
        result += "=" * 70 + "\n\n"
        
        for i, conv in enumerate(conversations, 1):
            timestamp = conv.get('timestamp', 'Unknown time')
            
            # Format timestamp if it's a datetime object
            if hasattr(timestamp, 'strftime'):
                formatted_time = timestamp.strftime("%H:%M")
            else:
                formatted_time = str(timestamp)
            
            if conv['role'] == 'user':
                # User message
                message_text = conv.get('message_text', 'No message content')
                result += f"{i}. 👤 **User** ({formatted_time}):\n"
                result += f"   \"{message_text}\"\n"
            else:
                # AI response
                response_text = conv.get('response_text', 'No response content')
                # Truncate long responses for readability
                if len(response_text) > 200:
                    response_text = response_text[:200] + "..."
                result += f"{i}. 🤖 **AI** ({formatted_time}):\n"
                result += f"   {response_text}\n"
            
            result += "\n"
        
        result += "💡 **Context**: Use this conversation history to provide more relevant and contextual responses."
        
        return result
        
    except Exception as e:
        return f"❌ Error retrieving conversation history: {str(e)}"


async def get_conversation_context(location: str = "", topic: str = "") -> str:
    """
    Get conversation context based on location or topic for better responses.
    
    Args:
        location: Location name (e.g., "kolkata", "punjab")
        topic: Topic of interest (e.g., "weather", "soil", "spraying")
    
    Returns:
        Context information for better responses
    """
    try:
        if not location and not topic:
            return "📝 Please provide either a location or topic to get conversation context."
        
        result = "💡 **Conversation Context Available:**\n\n"
        
        if location and location.strip():
            result += f"📍 **Location**: {location.title()}\n"
            result += "   • You can ask about current weather, forecasts, soil conditions\n"
            result += "   • Agricultural insights specific to this region\n"
            result += "   • Optimal timing for farming activities\n\n"
        
        if topic and topic.strip():
            result += f"🌾 **Topic**: {topic.title()}\n"
            if topic.lower() in ["weather", "forecast"]:
                result += "   • Current conditions and predictions\n"
                result += "   • Farming recommendations based on weather\n"
            elif topic.lower() in ["soil", "planting"]:
                result += "   • Soil temperature and moisture analysis\n"
                result += "   • Best planting times and conditions\n"
            elif topic.lower() in ["spraying", "pesticide"]:
                result += "   • Optimal spraying conditions\n"
                result += "   • Wind, temperature, and humidity analysis\n"
            else:
                result += "   • General agricultural guidance\n"
        
        result += "\n💬 **Previous Context**: While I don't have access to your specific conversation history, "
        result += "I can provide comprehensive, location-specific weather and agricultural information "
        result += "tailored to Indian farming conditions."
        
        return result
        
    except Exception as e:
        return f"❌ Error getting conversation context: {str(e)}"


# =================== ATOMIC TOOLS (Direct API Access) ===================

async def resolve_location(query: str) -> str:
    """
    Resolves a natural language location query into precise geographic coordinates.
    Essential first step for any location-based weather query.
    
    Args:
        query: Location name (e.g., "Kharagpur", "West Bengal", "Punjab")
    
    Returns:
        JSON string with location details including coordinates, timezone, and elevation
    """
    try:
        location = await LocationService.resolve_location(query)
        return json.dumps({
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "elevation": location.elevation,
            "timezone": location.timezone,
            "country": location.country,
            "state": location.admin1,
            "district": location.admin2,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error resolving location '{query}': {str(e)}"
        }, indent=2)


async def get_current_weather_data(latitude: float, longitude: float, timezone: str) -> str:
    """
    Gets real-time current weather conditions as raw structured data.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate  
        timezone: Timezone (e.g., "Asia/Kolkata")
    
    Returns:
        JSON string with current weather parameters
    """
    try:
        data = await OpenMeteoClient.get_forecast_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            current=["temperature_2m", "relative_humidity_2m", "apparent_temperature",
                    "is_day", "precipitation", "rain", "showers", "snowfall",
                    "weather_code", "cloud_cover", "pressure_msl", "surface_pressure",
                    "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"]
        )
        result = data["current"].copy()
        result["status"] = "success"
        result["weather_description"] = get_weather_description(result["weather_code"])
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error fetching current weather: {str(e)}"
        }, indent=2)


async def get_hourly_forecast_data(latitude: float, longitude: float, timezone: str, 
                                  hours: int = 48, variables: Optional[List[str]] = None) -> str:
    """
    Gets detailed hourly weather forecast data for fine-grained planning.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timezone: Timezone string
        hours: Number of hours to forecast (default 48)
        variables: List of variables to include (if None, uses default set)
    
    Returns:
        JSON string with hourly forecast data
    """
    if variables is None:
        variables = ["temperature_2m", "precipitation_probability", "precipitation",
                    "weather_code", "wind_speed_10m", "relative_humidity_2m",
                    "wind_direction_10m", "wind_gusts_10m", "surface_pressure"]
    
    try:
        data = await OpenMeteoClient.get_forecast_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            hourly=variables,
            forecast_days=min(16, (hours + 23) // 24)  # OpenMeteo max is 16 days
        )
        
        # Limit to requested hours
        hourly_data = data["hourly"].copy()
        for key in hourly_data:
            if isinstance(hourly_data[key], list):
                hourly_data[key] = hourly_data[key][:hours]
        
        hourly_data["status"] = "success"
        hourly_data["hours_returned"] = len(hourly_data.get("time", []))
        
        return json.dumps(hourly_data, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error fetching hourly forecast: {str(e)}"
        }, indent=2)


async def get_daily_forecast_data(latitude: float, longitude: float, timezone: str,
                                 days: int = 7, variables: Optional[List[str]] = None) -> str:
    """
    Gets daily aggregated weather forecast for longer-term planning.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timezone: Timezone string
        days: Number of days to forecast (default 7)
        variables: List of daily variables to include
    
    Returns:
        JSON string with daily forecast data
    """
    if variables is None:
        variables = ["weather_code", "temperature_2m_max", "temperature_2m_min",
                    "precipitation_sum", "precipitation_probability_max",
                    "wind_speed_10m_max", "wind_gusts_10m_max", "sunshine_duration",
                    "uv_index_max"]
    
    try:
        data = await OpenMeteoClient.get_forecast_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            daily=variables,
            forecast_days=min(16, days)
        )
        result = data["daily"].copy()
        result["status"] = "success"
        result["days_returned"] = len(result.get("time", []))
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error fetching daily forecast: {str(e)}"
        }, indent=2)


async def get_soil_data(latitude: float, longitude: float, timezone: str, hours: int = 72) -> str:
    """
    Gets hourly soil temperature and moisture forecasts at multiple depths.
    Essential for planting and irrigation decisions.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timezone: Timezone string
        hours: Number of hours of soil data (default 72)
    
    Returns:
        JSON string with soil data at different depths
    """
    try:
        data = await OpenMeteoClient.get_forecast_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            hourly=["soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm",
                   "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm"],
            forecast_days=min(16, (hours + 23) // 24)
        )
        
        # Limit to requested hours
        hourly_data = data["hourly"].copy()
        for key in hourly_data:
            if isinstance(hourly_data[key], list):
                hourly_data[key] = hourly_data[key][:hours]
        
        hourly_data["status"] = "success"
        hourly_data["hours_returned"] = len(hourly_data.get("time", []))
        
        return json.dumps(hourly_data, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error fetching soil data: {str(e)}"
        }, indent=2)


async def get_evapotranspiration_data(latitude: float, longitude: float, timezone: str, hours: int = 72) -> str:
    """
    Gets hourly evapotranspiration data for crop water requirement calculations.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timezone: Timezone string
        hours: Number of hours of ET data (default 72)
    
    Returns:
        JSON string with evapotranspiration data
    """
    try:
        data = await OpenMeteoClient.get_forecast_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            hourly=["et0_fao_evapotranspiration"],
            forecast_days=min(16, (hours + 23) // 24)
        )
        
        # Limit to requested hours
        hourly_data = data["hourly"].copy()
        for key in hourly_data:
            if isinstance(hourly_data[key], list):
                hourly_data[key] = hourly_data[key][:hours]
        
        hourly_data["status"] = "success"
        hourly_data["hours_returned"] = len(hourly_data.get("time", []))
        
        return json.dumps(hourly_data, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error", 
            "message": f"Error fetching evapotranspiration data: {str(e)}"
        }, indent=2)


# =================== CHAINED WORKFLOW TOOLS (Complex Agricultural Insights) ===================

async def get_comprehensive_farm_conditions(location: str, analysis_days: int = 7) -> str:
    """
    Provides a complete farming conditions dashboard for a location.
    Best tool for general "how is the weather for my farm?" queries.
    
    Workflow:
    1. Resolve location to coordinates
    2. Get current weather conditions
    3. Get daily forecast outlook
    4. Get soil conditions
    5. Synthesize into actionable farm report
    
    Args:
        location: Location name (e.g., "Kharagpur", "Punjab")
        analysis_days: Number of days to analyze (default 7)
    
    Returns:
        Comprehensive formatted farm conditions report
    """
    try:
        # Step 1: Resolve location
        location_obj = await LocationService.resolve_location(location)
        
        # Step 2: Get current conditions
        current_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            current=["temperature_2m", "relative_humidity_2m", "precipitation",
                    "weather_code", "wind_speed_10m", "pressure_msl", "apparent_temperature"]
        )
        
        # Step 3: Get daily forecast
        forecast_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            daily=["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                   "precipitation_probability_max", "weather_code", "wind_speed_10m_max"],
            forecast_days=analysis_days
        )
        
        # Step 4: Get soil data
        soil_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            hourly=["soil_temperature_0cm", "soil_moisture_0_1cm"],
            forecast_days=2
        )
        
        # Step 5: Synthesize report
        current = current_data["current"]
        daily = forecast_data["daily"]
        soil = soil_data["hourly"]
        
        # Current conditions analysis
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        rain = current["precipitation"]
        wind = current["wind_speed_10m"]
        weather_desc = get_weather_description(current["weather_code"])
        
        # Soil analysis
        soil_temp = soil["soil_temperature_0cm"][0] if soil["soil_temperature_0cm"] and len(soil["soil_temperature_0cm"]) > 0 else 0
        soil_moisture = soil["soil_moisture_0_1cm"][0] if soil["soil_moisture_0_1cm"] and len(soil["soil_moisture_0_1cm"]) > 0 else 0
        
        # Weekly outlook
        analysis_range = min(analysis_days, len(daily["temperature_2m_max"]))
        avg_max_temp = sum(daily["temperature_2m_max"][:analysis_range]) / analysis_range if analysis_range > 0 else 0
        total_rain = sum(daily["precipitation_sum"][:analysis_range])
        rainy_days = sum(1 for rain_day in daily["precipitation_sum"][:analysis_range] if rain_day > 1.0)
        
        report = f"""🌾 **COMPREHENSIVE FARM CONDITIONS REPORT**
📍 **Location:** {location_obj.name}, {location_obj.country}
📅 **Analysis Period:** {analysis_days} days
⏰ **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🌡️ **CURRENT CONDITIONS**
• Temperature: {temp}°C (Feels like: {current.get('apparent_temperature', temp)}°C)
• Humidity: {humidity}%
• Weather: {weather_desc}
• Wind Speed: {wind} km/h
• Precipitation: {rain} mm
• Soil Temperature: {soil_temp:.1f}°C
• Soil Moisture: {soil_moisture:.3f} m³/m³

📊 **{analysis_days}-DAY OUTLOOK**
• Average High: {avg_max_temp:.1f}°C
• Total Expected Rainfall: {total_rain:.1f} mm
• Rainy Days Expected: {rainy_days}
• Soil Status: {'🟢 Good' if soil_moisture > 0.2 else '🟡 Monitor' if soil_moisture > 0.1 else '🔴 Dry'}

🚜 **FARMING RECOMMENDATIONS**
"""
        
        # Add specific recommendations based on conditions
        recommendations = []
        
        if temp > 35:
            recommendations.append("⚠️ High temperature alert - consider irrigation and shade for livestock")
        if humidity < 30:
            recommendations.append("💧 Low humidity - increase watering frequency")
        if wind > 15:
            recommendations.append("🌪️ High winds - avoid spraying pesticides")
        if total_rain < 5:
            recommendations.append("🏜️ Dry week ahead - plan irrigation schedule")
        if rainy_days > 4:
            recommendations.append("🌧️ Wet week expected - check drainage systems")
        
        # Soil-based recommendations
        if soil_moisture < 0.1:
            recommendations.append("🌱 Soil is dry - consider immediate watering")
        elif soil_moisture > 0.4:
            recommendations.append("💦 Soil is very wet - avoid heavy machinery")
        
        if 20 <= temp <= 30 and humidity > 40 and wind < 10:
            recommendations.append("✅ Excellent conditions for most farm activities")
        
        if not recommendations:
            recommendations.append("✅ Weather conditions are generally suitable for normal farming activities")
        
        for rec in recommendations:
            report += f"• {rec}\n"
        
        return report
        
    except Exception as e:
        return f"❌ Error generating farm conditions report: {str(e)}"


async def get_advanced_spraying_analysis(location: str, hours: int = 48) -> str:
    """
    Generates professional hour-by-hour spraying suitability analysis.
    Definitive tool for "when should I spray?" questions.
    
    Workflow:
    1. Resolve location to coordinates
    2. Get detailed hourly weather data
    3. Analyze each hour for spraying suitability
    4. Generate formatted spraying schedule
    
    Args:
        location: Location name
        hours: Number of hours to analyze (default 48)
    
    Returns:
        Detailed spraying analysis with optimal windows
    """
    try:
        # Step 1: Resolve location
        location_obj = await LocationService.resolve_location(location)
        
        # Step 2: Get detailed hourly data
        data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            hourly=["temperature_2m", "relative_humidity_2m", "wind_speed_10m", 
                   "wind_gusts_10m", "precipitation_probability", "precipitation"],
            forecast_days=min(16, (hours + 23) // 24)
        )
        
        hourly = data["hourly"]
        timestamps = hourly["time"][:hours]
        temps = hourly["temperature_2m"][:hours]
        humidity = hourly["relative_humidity_2m"][:hours]
        wind_speed = hourly["wind_speed_10m"][:hours]
        wind_gusts = hourly["wind_gusts_10m"][:hours]
        rain_prob = hourly["precipitation_probability"][:hours]
        precipitation = hourly["precipitation"][:hours]
        
        # Step 3: Analyze spraying conditions
        spray_analysis = []
        for i in range(len(timestamps)):
            score = 0
            factors = []
            
            # Temperature analysis (optimal 15-25°C, modified for Indian conditions)
            if 15 <= temps[i] <= 29:
                score += 30
                factors.append("✅ Good temperature")
            elif 10 <= temps[i] < 15 or 29 < temps[i] <= 35:
                score += 15
                factors.append("⚠️ Acceptable temperature")
            else:
                factors.append("❌ Poor temperature for spraying")
            
            # Humidity analysis (optimal 40-70%)
            if 40 <= humidity[i] <= 70:
                score += 25
                factors.append("✅ Good humidity")
            elif 30 <= humidity[i] < 40 or 70 < humidity[i] <= 80:
                score += 15
                factors.append("⚠️ Acceptable humidity")
            else:
                factors.append("❌ Poor humidity level")
            
            # Wind analysis (optimal 3-15 km/h)
            if 3 <= wind_speed[i] <= 15 and wind_gusts[i] < 20:
                score += 25
                factors.append("✅ Good wind conditions")
            elif wind_speed[i] < 3:
                score += 10
                factors.append("⚠️ Very light wind - check for inversion")
            else:
                factors.append("❌ Too windy for safe spraying")
            
            # Rain analysis
            if rain_prob[i] < 10 and precipitation[i] < 0.1:
                score += 20
                factors.append("✅ No rain expected")
            elif rain_prob[i] < 30:
                score += 10
                factors.append("⚠️ Low rain chance")
            else:
                factors.append("❌ Rain likely - avoid spraying")
            
            # Time of day considerations
            dt = datetime.fromisoformat(timestamps[i])
            if dt.hour <= 10 or dt.hour >= 17:
                score += 5  # Early morning or evening bonus
            elif 11 <= dt.hour <= 16:
                score -= 5  # Midday penalty for Indian conditions
            
            # Categorize condition
            if score >= 80:
                condition = "🟢 EXCELLENT"
            elif score >= 60:
                condition = "🟡 GOOD"
            elif score >= 40:
                condition = "🟠 FAIR"
            else:
                condition = "🔴 POOR"
            
            spray_analysis.append({
                "time": timestamps[i],
                "score": score,
                "condition": condition,
                "factors": factors,
                "temp": temps[i],
                "humidity": humidity[i],
                "wind": wind_speed[i],
                "rain_prob": rain_prob[i]
            })
        
        # Step 4: Generate report
        report = f"""🚿 **ADVANCED SPRAYING ANALYSIS**
📍 **Location:** {location_obj.name}
⏱️ **Analysis Period:** Next {hours} hours
📊 **Scoring:** Temperature(30) + Humidity(25) + Wind(25) + Rain(20) = 100 points

🎯 **OPTIMAL SPRAYING WINDOWS:**
"""
        
        # Find and report optimal windows
        excellent_hours = [h for h in spray_analysis if h["score"] >= 80]
        good_hours = [h for h in spray_analysis if 60 <= h["score"] < 80]
        
        if excellent_hours:
            report += "\n🟢 **EXCELLENT CONDITIONS (80+ points):**\n"
            for hour in excellent_hours[:10]:  # Show first 10 excellent hours
                dt = datetime.fromisoformat(hour["time"].replace('Z', '+00:00'))
                report += f"• {dt.strftime('%a %H:%M')} - Score: {hour['score']}/100 ({hour['temp']:.1f}°C, {hour['humidity']:.0f}% RH, {hour['wind']:.1f} km/h wind)\n"
        
        if good_hours and len(excellent_hours) < 5:
            report += "\n🟡 **GOOD CONDITIONS (60-79 points):**\n"
            for hour in good_hours[:8]:  # Show up to 8 good hours
                dt = datetime.fromisoformat(hour["time"].replace('Z', '+00:00'))
                report += f"• {dt.strftime('%a %H:%M')} - Score: {hour['score']}/100 ({hour['temp']:.1f}°C, {hour['humidity']:.0f}% RH, {hour['wind']:.1f} km/h wind)\n"
        
        # Add warnings for poor conditions
        poor_hours = [h for h in spray_analysis if h["score"] < 40]
        if poor_hours:
            report += f"\n⚠️ **AVOID SPRAYING:** {len(poor_hours)} hours with poor conditions\n"
        
        # Summary recommendations
        best_hour = excellent_hours[0] if excellent_hours else good_hours[0] if good_hours else None
        best_time = best_hour["time"] if best_hour else "No suitable windows found"
        
        report += f"""
📋 **SUMMARY RECOMMENDATIONS:**
• Total Excellent Hours: {len(excellent_hours)}
• Total Good Hours: {len(good_hours)}
• Hours to Avoid: {len(poor_hours)}
• Best Overall Window: {datetime.fromisoformat(best_time).strftime('%a %H:%M') if best_hour else "None"}

💡 **Indian Farming Tips:**
• Best spraying: Early morning (6-10 AM) or evening (5-8 PM)
• Avoid midday hours (11 AM - 4 PM) due to heat and evaporation
• Use drift-reducing nozzles in windy conditions
• Check wind direction to protect sensitive crops/areas
"""
        
        return report
        
    except Exception as e:
        return f"❌ Error generating spraying analysis: {str(e)}"


async def get_optimal_planting_window(location: str, window_days: int = 10, crop_type: str = "general") -> str:
    """
    Analyzes soil and weather forecasts to identify the best days for planting.
    
    Workflow:
    1. Resolve location to coordinates
    2. Get soil temperature and moisture data for next window_days
    3. Get daily weather forecast for window_days
    4. Analyze optimal planting conditions
    5. Return ranked planting recommendations
    
    Args:
        location: Location name
        window_days: Number of days to analyze (default 10)
        crop_type: Type of crop for specific recommendations (default "general")
    
    Returns:
        Formatted report ranking the best upcoming planting dates
    """
    try:
        # Step 1: Resolve location
        location_obj = await LocationService.resolve_location(location)
        
        # Step 2: Get soil data
        soil_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            hourly=["soil_temperature_0cm", "soil_temperature_6cm", "soil_moisture_0_1cm", "soil_moisture_1_3cm"],
            forecast_days=window_days
        )
        
        # Step 3: Get weather forecast
        weather_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            daily=["temperature_2m_max", "temperature_2m_min", "precipitation_sum", 
                   "precipitation_probability_max", "weather_code", "wind_speed_10m_max"],
            forecast_days=window_days
        )
        
        # Step 4: Analyze planting conditions
        daily_scores = []
        
        for day in range(min(window_days, len(weather_data["daily"]["time"]))):
            date_str = weather_data["daily"]["time"][day]
            date_obj = datetime.fromisoformat(date_str).date()
            
            # Daily weather
            max_temp = weather_data["daily"]["temperature_2m_max"][day]
            min_temp = weather_data["daily"]["temperature_2m_min"][day]
            precip = weather_data["daily"]["precipitation_sum"][day]
            precip_prob = weather_data["daily"]["precipitation_probability_max"][day]
            wind = weather_data["daily"]["wind_speed_10m_max"][day]
            
            # Average soil conditions for the day (take average of 24 hours)
            start_hour = day * 24
            end_hour = min(start_hour + 24, len(soil_data["hourly"]["soil_temperature_0cm"]))
            
            if end_hour > start_hour:
                avg_soil_temp = sum(soil_data["hourly"]["soil_temperature_0cm"][start_hour:end_hour]) / (end_hour - start_hour)
                avg_soil_moisture = sum(soil_data["hourly"]["soil_moisture_0_1cm"][start_hour:end_hour]) / (end_hour - start_hour)
            else:
                avg_soil_temp = 0
                avg_soil_moisture = 0
            
            # Scoring system for planting conditions
            score = 0
            factors = []
            
            # Soil temperature (optimal 15-25°C for most crops)
            if 15 <= avg_soil_temp <= 25:
                score += 30
                factors.append("✅ Optimal soil temperature")
            elif 10 <= avg_soil_temp < 15 or 25 < avg_soil_temp <= 30:
                score += 20
                factors.append("⚠️ Acceptable soil temperature")
            else:
                factors.append("❌ Poor soil temperature")
            
            # Soil moisture (optimal 0.2-0.4 m³/m³)
            if 0.2 <= avg_soil_moisture <= 0.4:
                score += 25
                factors.append("✅ Good soil moisture")
            elif 0.15 <= avg_soil_moisture < 0.2 or 0.4 < avg_soil_moisture <= 0.5:
                score += 15
                factors.append("⚠️ Acceptable soil moisture")
            else:
                if avg_soil_moisture < 0.15:
                    factors.append("❌ Soil too dry - irrigation needed")
                else:
                    factors.append("❌ Soil too wet - drainage needed")
            
            # Air temperature stability
            if 18 <= min_temp <= 25 and 25 <= max_temp <= 32:
                score += 20
                factors.append("✅ Good temperature range")
            elif min_temp >= 10 and max_temp <= 35:
                score += 10
                factors.append("⚠️ Acceptable temperature")
            else:
                factors.append("❌ Poor temperature conditions")
            
            # Precipitation (light rain good, heavy rain bad)
            if 1 <= precip <= 5:
                score += 15
                factors.append("✅ Light rain - good for planting")
            elif precip == 0 and precip_prob < 30:
                score += 10
                factors.append("✅ Dry conditions - plan irrigation")
            elif precip > 20 or precip_prob > 70:
                score -= 10
                factors.append("❌ Heavy rain expected - soil may be waterlogged")
            
            # Wind conditions
            if wind < 15:
                score += 10
                factors.append("✅ Calm conditions good for planting")
            else:
                factors.append("⚠️ Windy conditions")
            
            # Future weather stability (check next 3 days)
            stability_bonus = 0
            if day + 3 < len(weather_data["daily"]["precipitation_sum"]):
                future_rain = sum(weather_data["daily"]["precipitation_sum"][day+1:day+4])
                if future_rain < 10:
                    stability_bonus = 10
                    factors.append("✅ Stable weather ahead")
                elif future_rain > 30:
                    stability_bonus = -5
                    factors.append("⚠️ Heavy rain expected in coming days")
            
            score += stability_bonus
            
            daily_scores.append({
                "date": date_obj,
                "score": score,
                "factors": factors,
                "soil_temp": avg_soil_temp,
                "soil_moisture": avg_soil_moisture,
                "air_temp_range": f"{min_temp:.1f}-{max_temp:.1f}°C",
                "precipitation": precip
            })
        
        # Sort by score (best first)
        daily_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Step 5: Generate report
        report = f"""🌱 **OPTIMAL PLANTING WINDOW ANALYSIS**
📍 **Location:** {location_obj.name}, {location_obj.country}
🌾 **Crop Type:** {crop_type.title()}
📅 **Analysis Period:** Next {window_days} days
⏰ **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🏆 **RECOMMENDED PLANTING DATES (Ranked by Suitability):**

"""
        
        for i, day_info in enumerate(daily_scores[:5], 1):  # Show top 5 days
            score = day_info["score"]
            if score >= 70:
                rating = "🟢 EXCELLENT"
            elif score >= 50:
                rating = "🟡 GOOD"
            elif score >= 30:
                rating = "🟠 FAIR"
            else:
                rating = "🔴 POOR"
            
            report += f"""**#{i}. {day_info['date'].strftime('%A, %B %d')} - {rating} ({score}/100)**
   🌡️ Soil Temp: {day_info['soil_temp']:.1f}°C | Air Temp: {day_info['air_temp_range']}
   💧 Soil Moisture: {day_info['soil_moisture']:.3f} m³/m³ | Rain: {day_info['precipitation']:.1f}mm
   📝 Factors: {' | '.join(day_info['factors'][:3])}

"""
        
        # Crop-specific recommendations
        if crop_type.lower() in ["rice", "paddy"]:
            report += "🌾 **Rice-Specific Tips:** Ensure fields are properly flooded. Soil temperature above 20°C preferred.\n"
        elif crop_type.lower() in ["wheat", "barley"]:
            report += "🌾 **Wheat-Specific Tips:** Plant when soil temperature is 15-20°C. Avoid waterlogged conditions.\n"
        elif crop_type.lower() in ["cotton"]:
            report += "🌾 **Cotton-Specific Tips:** Soil temperature should be above 18°C. Ensure good drainage.\n"
        elif crop_type.lower() in ["sugarcane"]:
            report += "🌾 **Sugarcane-Specific Tips:** Plant when soil temperature is above 20°C. Good soil moisture essential.\n"
        else:
            report += "🌾 **General Tips:** Monitor soil temperature and moisture. Avoid planting before heavy rains.\n"
        
        return report
        
    except Exception as e:
        return f"❌ Error generating planting window analysis: {str(e)}"


async def get_irrigation_scheduling_recommendation(location: str, days: int = 7) -> str:
    """
    Provides precision irrigation schedule based on water balance model.
    Answers "how much should I water my crops?" with scientific precision.
    
    Workflow:
    1. Resolve location to coordinates
    2. Get evapotranspiration data (water demand)
    3. Get precipitation data (natural water supply)
    4. Calculate daily water balance
    5. Generate irrigation schedule with recommendations
    
    Args:
        location: Location name
        days: Number of days to analyze (default 7)
    
    Returns:
        Formatted irrigation schedule with water requirements
    """
    try:
        # Step 1: Resolve location
        location_obj = await LocationService.resolve_location(location)
        
        # Step 2: Get evapotranspiration data (crop water demand)
        et_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            daily=["et0_fao_evapotranspiration"],
            forecast_days=days
        )
        
        # Step 3: Get precipitation data (natural water supply)
        precip_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            daily=["precipitation_sum", "precipitation_probability_max"],
            forecast_days=days
        )
        
        # Step 4: Calculate water balance and irrigation needs
        irrigation_schedule = []
        cumulative_deficit = 0
        
        for day in range(min(days, len(et_data["daily"]["time"]))):
            date_str = et_data["daily"]["time"][day]
            date_obj = datetime.fromisoformat(date_str).date()
            
            # Water demand (ET0 = reference evapotranspiration)
            et0 = et_data["daily"]["et0_fao_evapotranspiration"][day]
            
            # Natural water supply
            precipitation = precip_data["daily"]["precipitation_sum"][day]
            precip_prob = precip_data["daily"]["precipitation_probability_max"][day]
            
            # Effective precipitation (accounting for runoff and inefficiency)
            if precipitation <= 5:
                effective_precip = precipitation * 0.8  # 80% efficiency for light rain
            elif precipitation <= 20:
                effective_precip = precipitation * 0.7  # 70% efficiency for moderate rain
            else:
                effective_precip = precipitation * 0.6  # 60% efficiency for heavy rain
            
            # Daily water balance
            daily_deficit = et0 - effective_precip
            cumulative_deficit += daily_deficit
            
            # Irrigation decision logic
            irrigation_needed = 0
            irrigation_priority = "Low"
            recommendations = []
            
            if cumulative_deficit > 15:  # Critical threshold
                irrigation_needed = cumulative_deficit
                irrigation_priority = "Critical"
                recommendations.append("🚨 Immediate irrigation required")
                cumulative_deficit = 0  # Reset after irrigation
            elif cumulative_deficit > 10:  # High threshold
                irrigation_needed = cumulative_deficit
                irrigation_priority = "High"
                recommendations.append("⚠️ Irrigation recommended today")
                cumulative_deficit = 0
            elif cumulative_deficit > 5 and precip_prob < 30:  # Moderate threshold with low rain chance
                irrigation_needed = cumulative_deficit
                irrigation_priority = "Moderate"
                recommendations.append("💧 Consider light irrigation")
                cumulative_deficit = 0
            else:
                if precipitation > 5:
                    recommendations.append("✅ Natural rainfall sufficient")
                elif precip_prob > 60:
                    recommendations.append("🌧️ Rain expected - delay irrigation")
                else:
                    recommendations.append("⏳ Monitor - may need irrigation soon")
            
            irrigation_schedule.append({
                "date": date_obj,
                "et0": et0,
                "precipitation": precipitation,
                "effective_precip": effective_precip,
                "daily_deficit": daily_deficit,
                "cumulative_deficit": cumulative_deficit + daily_deficit if irrigation_needed == 0 else 0,
                "irrigation_needed": irrigation_needed,
                "priority": irrigation_priority,
                "recommendations": recommendations
            })
        
        # Step 5: Generate irrigation schedule report
        report = f"""💧 **PRECISION IRRIGATION SCHEDULING**
📍 **Location:** {location_obj.name}, {location_obj.country}
📅 **Irrigation Period:** Next {days} days
⏰ **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔬 **Water Balance Model:**
• ET₀ (Crop Water Demand) vs Effective Precipitation
• Irrigation triggered when cumulative deficit > 10mm
• Efficiency factors applied to rainfall

📋 **DAILY IRRIGATION SCHEDULE:**

"""
        
        total_irrigation = 0
        irrigation_days = 0
        
        for day_info in irrigation_schedule:
            priority_icon = {
                "Critical": "🚨",
                "High": "⚠️", 
                "Moderate": "💧",
                "Low": "✅"
            }.get(day_info["priority"], "ℹ️")
            
            report += f"""📅 **{day_info['date'].strftime('%A, %B %d')}** {priority_icon}
   • Crop Water Need: {day_info['et0']:.1f}mm | Rainfall: {day_info['precipitation']:.1f}mm (Effective: {day_info['effective_precip']:.1f}mm)
   • Daily Deficit: {day_info['daily_deficit']:.1f}mm | Cumulative: {day_info['cumulative_deficit']:.1f}mm
   • Irrigation: {day_info['irrigation_needed']:.1f}mm ({day_info['priority']} Priority)
   • Action: {' | '.join(day_info['recommendations'])}

"""
            
            if day_info["irrigation_needed"] > 0:
                total_irrigation += day_info["irrigation_needed"]
                irrigation_days += 1
        
        # Summary and recommendations
        report += f"""📊 **IRRIGATION SUMMARY:**
• Total Irrigation Needed: {total_irrigation:.1f}mm over {irrigation_days} days
• Average per Irrigation Day: {total_irrigation/irrigation_days:.1f}mm (if {irrigation_days} > 0 else 0)
• Water Savings from Natural Rain: {sum(d['effective_precip'] for d in irrigation_schedule):.1f}mm

💡 **IRRIGATION BEST PRACTICES:**
• Early morning irrigation (5-8 AM) for minimal evaporation loss
• Deep, less frequent watering is better than shallow, frequent watering
• Monitor soil moisture at root depth (15-30cm) for validation
• Adjust for crop type, growth stage, and soil characteristics
• Use drip irrigation or sprinkler systems for water efficiency

🌱 **CROP-SPECIFIC ADJUSTMENTS:**
• Vegetable crops: Use 100% of calculated irrigation
• Field crops (wheat, rice): Use 80-90% of calculated irrigation  
• Tree crops: Use 70-80% of calculated irrigation
• Drought-tolerant crops: Use 60-70% of calculated irrigation
"""
        
        return report
        
    except Exception as e:
        return f"❌ Error generating irrigation schedule: {str(e)}"


async def get_crop_disease_risk_analysis(location: str, hours: int = 72) -> str:
    """
    Analyzes weather conditions for crop disease risk assessment.
    Focuses on temperature and humidity patterns that favor fungal/bacterial diseases.
    
    Workflow:
    1. Resolve location to coordinates
    2. Get detailed hourly weather data
    3. Analyze disease-favorable conditions
    4. Generate risk assessment and prevention recommendations
    
    Args:
        location: Location name
        hours: Number of hours to analyze (default 72)
    
    Returns:
        Disease risk assessment with prevention strategies
    """
    try:
        # Step 1: Resolve location
        location_obj = await LocationService.resolve_location(location)
        
        # Step 2: Get detailed hourly weather data
        weather_data = await OpenMeteoClient.get_forecast_data(
            latitude=location_obj.latitude,
            longitude=location_obj.longitude,
            timezone=location_obj.timezone,
            hourly=["temperature_2m", "relative_humidity_2m", "precipitation", 
                   "wind_speed_10m", "surface_pressure"],
            forecast_days=min(16, (hours + 23) // 24)
        )
        
        hourly = weather_data["hourly"]
        timestamps = hourly["time"][:hours]
        temps = hourly["temperature_2m"][:hours]
        humidity = hourly["relative_humidity_2m"][:hours]
        precipitation = hourly["precipitation"][:hours]
        wind_speed = hourly["wind_speed_10m"][:hours]
        
        # Step 3: Analyze disease risk conditions
        disease_risks = {
            "fungal_blight": {"hours": 0, "risk_periods": []},
            "powdery_mildew": {"hours": 0, "risk_periods": []},
            "bacterial_diseases": {"hours": 0, "risk_periods": []},
            "rust_diseases": {"hours": 0, "risk_periods": []}
        }
        
        high_risk_hours = []
        
        for i in range(len(timestamps)):
            dt = datetime.fromisoformat(timestamps[i])
            temp = temps[i]
            rh = humidity[i]
            rain = precipitation[i]
            wind = wind_speed[i]
            
            hour_risks = []
            
            # Fungal Blight Risk (warm, humid conditions)
            if 20 <= temp <= 30 and rh > 80 and rain > 0:
                disease_risks["fungal_blight"]["hours"] += 1
                hour_risks.append("🦠 High fungal blight risk")
                if len(disease_risks["fungal_blight"]["risk_periods"]) == 0 or \
                   disease_risks["fungal_blight"]["risk_periods"][-1]["end"] != i-1:
                    disease_risks["fungal_blight"]["risk_periods"].append({"start": i, "end": i})
                else:
                    disease_risks["fungal_blight"]["risk_periods"][-1]["end"] = i
            
            # Powdery Mildew Risk (moderate temp, high humidity, low wind)
            if 15 <= temp <= 25 and rh > 70 and wind < 5:
                disease_risks["powdery_mildew"]["hours"] += 1
                hour_risks.append("🍄 Powdery mildew risk")
                if len(disease_risks["powdery_mildew"]["risk_periods"]) == 0 or \
                   disease_risks["powdery_mildew"]["risk_periods"][-1]["end"] != i-1:
                    disease_risks["powdery_mildew"]["risk_periods"].append({"start": i, "end": i})
                else:
                    disease_risks["powdery_mildew"]["risk_periods"][-1]["end"] = i
            
            # Bacterial Disease Risk (warm, wet, low wind)
            if temp > 25 and rh > 85 and rain > 1 and wind < 10:
                disease_risks["bacterial_diseases"]["hours"] += 1
                hour_risks.append("🦠 Bacterial disease risk")
                if len(disease_risks["bacterial_diseases"]["risk_periods"]) == 0 or \
                   disease_risks["bacterial_diseases"]["risk_periods"][-1]["end"] != i-1:
                    disease_risks["bacterial_diseases"]["risk_periods"].append({"start": i, "end": i})
                else:
                    disease_risks["bacterial_diseases"]["risk_periods"][-1]["end"] = i
            
            # Rust Disease Risk (cool, humid mornings)
            if 10 <= temp <= 20 and rh > 90 and 5 <= dt.hour <= 10:
                disease_risks["rust_diseases"]["hours"] += 1
                hour_risks.append("🟤 Rust disease risk")
                if len(disease_risks["rust_diseases"]["risk_periods"]) == 0 or \
                   disease_risks["rust_diseases"]["risk_periods"][-1]["end"] != i-1:
                    disease_risks["rust_diseases"]["risk_periods"].append({"start": i, "end": i})
                else:
                    disease_risks["rust_diseases"]["risk_periods"][-1]["end"] = i
            
            if hour_risks:
                high_risk_hours.append({
                    "time": dt.strftime("%a %H:%M"),
                    "risks": hour_risks,
                    "temp": temp,
                    "humidity": rh,
                    "rain": rain
                })
        
        # Step 4: Generate risk assessment report
        report = f"""🦠 **CROP DISEASE RISK ANALYSIS**
📍 **Location:** {location_obj.name}, {location_obj.country}
⏰ **Analysis Period:** Next {hours} hours
📊 **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🚨 **DISEASE RISK SUMMARY:**

"""
        
        total_risk_hours = sum(risk["hours"] for risk in disease_risks.values())
        
        # Risk level assessment
        if total_risk_hours > hours * 0.4:
            risk_level = "🔴 HIGH RISK"
        elif total_risk_hours > hours * 0.2:
            risk_level = "🟡 MODERATE RISK"
        else:
            risk_level = "🟢 LOW RISK"
        
        report += f"**Overall Disease Pressure: {risk_level}**\n\n"
        
        # Individual disease risks
        for disease, data in disease_risks.items():
            risk_hours = data["hours"]
            risk_percentage = (risk_hours / hours) * 100
            
            disease_name = disease.replace("_", " ").title()
            
            if risk_percentage > 30:
                alert = "🔴 HIGH"
            elif risk_percentage > 15:
                alert = "🟡 MODERATE"  
            else:
                alert = "🟢 LOW"
            
            report += f"• **{disease_name}:** {alert} ({risk_hours}/{hours} hours, {risk_percentage:.1f}%)\n"
        
        report += f"\n⚠️ **HIGH-RISK PERIODS:**\n"
        
        if high_risk_hours:
            for hour_info in high_risk_hours[:10]:  # Show first 10 high-risk hours
                report += f"• {hour_info['time']}: {hour_info['temp']:.1f}°C, {hour_info['humidity']:.0f}% RH - {', '.join(hour_info['risks'])}\n"
        else:
            report += "• No high-risk periods identified in the forecast period\n"
        
        report += f"""
🛡️ **DISEASE PREVENTION STRATEGIES:**

**Immediate Actions:**
• Improve air circulation - prune dense foliage, increase plant spacing
• Apply preventive fungicides during high-risk periods
• Avoid overhead irrigation during humid conditions
• Remove plant debris and infected plant material

**Cultural Practices:**
• Plant disease-resistant varieties when possible
• Ensure proper drainage to avoid waterlogged conditions
• Rotate crops to break disease cycles
• Use drip irrigation instead of sprinkler systems

**Chemical Control:**
• Apply copper-based fungicides for bacterial diseases
• Use systemic fungicides for persistent fungal problems
• Time applications before predicted high-risk periods
• Follow label instructions and pre-harvest intervals

**Monitoring:**
• Scout fields daily during high-risk periods
• Focus on lower leaves and dense canopy areas
• Look for early symptoms: spots, discoloration, wilting
• Document disease pressure for future planning

💡 **Weather-Based Timing:**
• Apply preventive treatments 24-48 hours before high-risk periods
• Avoid spraying during rain or when leaves are wet
• Best application times: early morning or late evening
• Ensure good spray coverage, especially leaf undersides
"""
        
        return report
        
    except Exception as e:
        return f"❌ Error generating disease risk analysis: {str(e)}"


def create_agent() -> LlmAgent:
    """Creates the Weather Agent specialized for Indian farmers with atomic tools and workflow capabilities."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Weather_Agent",
        instruction="""
🌾 **ROLE:** You are an expert agricultural intelligence agent powered by the OpenMeteo API, 
specializing in weather analysis for global agriculture with deep Indian farming expertise.

🚨 **CRITICAL WORKFLOW RULES:**

1. **MANDATORY LOCATION RESOLUTION:** For ANY location-based query, you MUST:
   - First call `resolve_location` with the user's location string
   - Use the returned coordinates for ALL subsequent weather API calls
   - NEVER use hardcoded coordinates or make assumptions about locations

2. **PREFERRED TOOL HIERARCHY:**
   
   🎯 **PRIMARY TOOLS (Use These First):**
   • `get_comprehensive_farm_conditions` - Complete farm conditions dashboard
   • `get_advanced_spraying_analysis` - Professional spraying analysis and timing
   • `get_optimal_planting_window` - Best planting dates based on soil and weather
   • `get_irrigation_scheduling_recommendation` - Precision water management schedule
   • `get_crop_disease_risk_analysis` - Disease risk assessment and prevention
   
   🔧 **ATOMIC TOOLS (For Specific Data Only):**
   • `get_current_weather_data` - Raw current weather (requires lat, lon, timezone)
   • `get_hourly_forecast_data` - Detailed hourly forecasts (requires lat, lon, timezone)
   • `get_daily_forecast_data` - Daily aggregated data (requires lat, lon, timezone)
   • `get_soil_data` - Soil conditions (requires lat, lon, timezone)
   • `get_evapotranspiration_data` - Water requirements (requires lat, lon, timezone)

3. **EXAMPLE WORKFLOWS:**
   User: "Weather in Rio de Janeiro today"
   → Call `get_comprehensive_farm_conditions("Rio de Janeiro")`
   
   User: "When should I spray pesticides in Mumbai?"
   → Call `get_advanced_spraying_analysis("Mumbai")`
   
   User: "Best time to plant wheat in Punjab?"
   → Call `get_optimal_planting_window("Punjab", crop_type="wheat")`
   
   User: "Irrigation schedule for next week in Karnataka?"
   → Call `get_irrigation_scheduling_recommendation("Karnataka")`
   
   User: "Disease risk for my tomato crop in Maharashtra?"
   → Call `get_crop_disease_risk_analysis("Maharashtra")`

🌍 **GLOBAL COVERAGE:** You can provide weather analysis for any location worldwide,
but specialize in agricultural insights with particular expertise in:
- Indian monsoon patterns and agricultural cycles
- Regional crop calendars (Kharif, Rabi, Zaid seasons)
- Global farming practices and climate considerations

📋 **OUTPUT FORMAT:**
- Use clear headings with emojis
- Include specific numerical data and coordinates
- Provide actionable agricultural recommendations
- Consider safety, economic, and environmental factors
   • `get_weather_forecast` - Use daily forecast data instead
   • `get_soil_conditions` - Use soil data atomic tool instead
   • `get_spraying_conditions` - Use advanced spraying analysis instead

5. **CONTEXT TOOLS:** Always use for personalized responses:
   • `get_conversation_context` - Understand user's location and topic context
   • `get_last_conversation` - Access conversation history when available

🌍 **AGRICULTURAL EXPERTISE:** You have deep knowledge of:
• Indian monsoon patterns and regional variations
• Crop calendars (Kharif, Rabi, Zaid seasons)
• State-specific agricultural practices and challenges
• Crop-specific weather requirements and sensitivities
• Irrigation timing and water management strategies
• Pest and disease pressure related to weather conditions

📊 **DATA INTERPRETATION:** When using atomic tools:
• Raw JSON data requires your interpretation and analysis
• Combine multiple data sources for comprehensive insights
• Focus on agricultural implications of weather patterns
• Provide specific, actionable recommendations

📋 **OUTPUT FORMAT STANDARDS:**
• Use clear headings with relevant emojis (🌾🌡️💧🌧️☀️🌪️)
• Include specific numerical data with units
• Provide actionable recommendations with timeframes
• Consider both immediate and longer-term implications
• Format for easy reading on mobile devices
• Use bullet points and clear sections

🔄 **RESPONSE WORKFLOW:**
1. Call `get_conversation_context` to understand user needs
2. If available, call `get_last_conversation` for context
3. Use `resolve_location` for any location-based queries
4. Choose appropriate tools based on query complexity:
   - Simple current conditions → `get_comprehensive_farm_conditions`
   - Spraying timing → `get_advanced_spraying_analysis`
   - Specific data needs → Use relevant atomic tools
5. Synthesize data into farmer-friendly recommendations
6. Reference previous context when building responses

⚠️ **CRITICAL REMINDERS:**
• Indian farming context is paramount - consider local practices
• Weather safety is crucial - warn about dangerous conditions
• Economic efficiency matters - balance costs with benefits
• Seasonal timing is critical - respect crop calendars
• Regional variations exist - adapt advice to specific locations

Always prioritize actionable, location-specific agricultural guidance over generic weather information.
        """,
        tools=[
            # Foundation Tool (ALWAYS USE FIRST)
            resolve_location,
            
            # Comprehensive Workflow Tools (Primary Tools - Use These for Most Queries)
            get_comprehensive_farm_conditions,
            get_advanced_spraying_analysis,
            get_optimal_planting_window,
            get_irrigation_scheduling_recommendation,
            get_crop_disease_risk_analysis,
            
            # Atomic Data Tools (For Specific Data Needs Only)
            get_current_weather_data,
            get_hourly_forecast_data,
            get_daily_forecast_data,
            get_soil_data,
            get_evapotranspiration_data,
            
            # Context Tools
            get_conversation_context,
            get_last_conversation,
        ],
    )
