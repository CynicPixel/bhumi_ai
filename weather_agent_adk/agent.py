import asyncio
import httpx
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field


class WeatherLocation(BaseModel):
    """Location information for weather queries"""
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location") 
    name: str = Field(..., description="Name of the location")


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
    "mumbai": WeatherLocation(latitude=19.0760, longitude=72.8777, name="Mumbai"),
    "bangalore": WeatherLocation(latitude=12.9716, longitude=77.5946, name="Bangalore"),
    "hyderabad": WeatherLocation(latitude=17.3850, longitude=78.4867, name="Hyderabad"),
    "chennai": WeatherLocation(latitude=13.0827, longitude=80.2707, name="Chennai"),
    "kolkata": WeatherLocation(latitude=22.5726, longitude=88.3639, name="Kolkata"),
}


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


def create_agent() -> LlmAgent:
    """Creates the Weather Agent specialized for Indian farmers."""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Weather_Agent",
        instruction="""
            **Role:** You are a specialized weather assistant for Indian farmers, providing 
            comprehensive weather information and agricultural guidance using real-time data 
            from Open-Meteo API.

            **Core Capabilities:**
            • Current weather conditions with farming insights
            • Weather forecasts for agricultural planning (1-16 days)
            • Soil temperature and moisture conditions for planting decisions
            • Optimal spraying conditions for pesticides/herbicides
            • Historical weather data for comparison and planning
            • Coverage of all major Indian agricultural regions

            **Key Responsibilities:**
            • Provide weather data specifically relevant to farming activities
            • Offer actionable agricultural insights based on weather conditions
            • Help farmers plan field operations, irrigation, spraying, and harvesting
            • Warn about adverse weather conditions that could affect crops
            • Suggest optimal timing for various farming activities

            **Supported Regions:** All major Indian states and agricultural areas including
            Punjab, Haryana, Uttar Pradesh, Bihar, West Bengal, Maharashtra, Karnataka,
            Andhra Pradesh, Telangana, Tamil Nadu, Kerala, Gujarat, Rajasthan, and more.

            **Communication Style:**
            • Use clear, practical language suitable for farmers
            • Include relevant emojis and icons for better readability
            • Provide specific, actionable recommendations
            • Focus on agricultural implications of weather data
            • Be concise but comprehensive in responses

            **Tools Available:**
            • get_current_weather_conditions: Real-time weather with farming insights
            • get_weather_forecast: Multi-day forecasts for planning
            • get_soil_conditions: Soil temperature and moisture analysis
            • get_spraying_conditions: Optimal timing for pesticide application
            • get_historical_weather: Past weather data for reference

            Always use appropriate tools to provide accurate, real-time weather information.
            If asked about weather for farming, always prioritize agricultural relevance in your responses.
        """,
        tools=[
            get_current_weather_conditions,
            get_weather_forecast,
            get_soil_conditions,
            get_spraying_conditions,
            get_historical_weather,
        ],
    )
