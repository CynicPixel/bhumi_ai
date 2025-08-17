import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from pydantic import BaseModel

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CEDA API Configuration
CEDA_BASE_URL = "https://api.ceda.ashoka.edu.in/v1"
CEDA_API_KEY = os.getenv("CEDA_API_KEY")

if not CEDA_API_KEY:
    logger.warning("CEDA_API_KEY not found in environment variables")

@dataclass
class Commodity:
    id: int
    name: str

@dataclass  
class District:
    district_id: int
    district_name: str

@dataclass
class Geography:
    state_id: int
    state_name: str
    districts: List[District]

@dataclass
class Market:
    census_state_id: int
    census_district_id: int
    market_id: int
    market_name: str

@dataclass
class PriceData:
    date: str
    commodity_id: int
    census_state_id: int
    census_district_id: int
    market_id: int
    min_price: float
    max_price: float
    modal_price: float

@dataclass
class QuantityData:
    date: str
    commodity_id: int
    census_state_id: int
    census_district_id: int
    market_id: int
    quantity: float

# Indian language commodity mappings for chain-of-thought resolution
COMMODITY_MAPPINGS = {
    # Hindi names
    "pyaaz": "onion",
    "aloo": "potato", 
    "chawal": "rice",
    "gehun": "wheat",
    "dal": "gram",
    "chana": "gram",
    "sarson": "mustard seed",
    "kapas": "cotton",
    "mirch": "chilli",
    "tamatar": "tomato",
    "palak": "spinach",
    "gobhi": "cauliflower",
    "gajar": "carrot",
    "nimbu": "lemon",
    "kela": "banana",
    "aam": "mango",
    
    # Bengali names
    "peyaj": "onion",
    "alu": "potato",
    "chal": "rice",
    "gom": "wheat",
    "mashkalai": "black gram",
    "mosur": "lentil",
    "lanka": "chilli",
    "tometo": "tomato",
    
    # Tamil names
    "vengayam": "onion",
    "urulaikizhangu": "potato",
    "arisi": "rice",
    "godhumai": "wheat",
    
    # Common English variations
    "onions": "onion",
    "potatoes": "potato",
    "chillies": "chilli",
    "tomatoes": "tomato",
}

# Geography mappings for better location resolution
LOCATION_MAPPINGS = {
    "kharagpur": ("west bengal", "paschim medinipur"),
    "siliguri": ("west bengal", "darjeeling"),
    "kolkata": ("west bengal", "kolkata"),
    "mumbai": ("maharashtra", "mumbai"),
    "delhi": ("delhi", "delhi"),
    "bangalore": ("karnataka", "bangalore urban"),
    "chennai": ("tamil nadu", "chennai"),
    "hyderabad": ("telangana", "hyderabad"),
    "pune": ("maharashtra", "pune"),
    "ahmedabad": ("gujarat", "ahmedabad"),
    "surat": ("gujarat", "surat"),
    "jaipur": ("rajasthan", "jaipur"),
    "lucknow": ("uttar pradesh", "lucknow"),
    "kanpur": ("uttar pradesh", "kanpur nagar"),
    "nagpur": ("maharashtra", "nagpur"),
    "indore": ("madhya pradesh", "indore"),
    "thane": ("maharashtra", "thane"),
    "bhopal": ("madhya pradesh", "bhopal"),
    "visakhapatnam": ("andhra pradesh", "visakhapatnam"),
    "pimpri": ("maharashtra", "pune"),
    "patna": ("bihar", "patna"),
    "vadodara": ("gujarat", "vadodara"),
    "ghaziabad": ("uttar pradesh", "ghaziabad"),
    "ludhiana": ("punjab", "ludhiana"),
    "agra": ("uttar pradesh", "agra"),
    "nashik": ("maharashtra", "nashik"),
    "faridabad": ("haryana", "faridabad"),
    "meerut": ("uttar pradesh", "meerut"),
    "rajkot": ("gujarat", "rajkot"),
    "kalyan": ("maharashtra", "thane"),
    "vasai": ("maharashtra", "thane"),
    "varanasi": ("uttar pradesh", "varanasi"),
    "srinagar": ("jammu and kashmir", "srinagar"),
    "amritsar": ("punjab", "amritsar"),
    "allahabad": ("uttar pradesh", "allahabad"),
    "prayagraj": ("uttar pradesh", "allahabad"),
    "jabalpur": ("madhya pradesh", "jabalpur"),
    "coimbatore": ("tamil nadu", "coimbatore"),
    "madurai": ("tamil nadu", "madurai"),
    "guwahati": ("assam", "kamrup"),
    "chandigarh": ("chandigarh", "chandigarh"),
}


class CEDAAPIClient:
    """Client for CEDA Agmarknet API with robust error handling and caching"""
    
    def __init__(self):
        self.base_url = CEDA_BASE_URL
        self.api_key = CEDA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Cache for expensive list operations
        self._commodities_cache: Optional[List[Commodity]] = None
        self._geographies_cache: Optional[List[Geography]] = None

    
    async def get_commodities(self) -> List[Commodity]:
        """Get all available commodities with caching"""
        if self._commodities_cache:
            return self._commodities_cache
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agmarknet/commodities",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                commodities = [
                    Commodity(id=item["commodity_id"], name=item["commodity_name"]) 
                    for item in data["output"]["data"]
                ]
                self._commodities_cache = commodities
                return commodities
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting commodities: {e}")
                raise
            except Exception as e:
                logger.error(f"Error getting commodities: {e}")
                raise
    
    async def get_geographies(self) -> List[Geography]:
        """Get all available geographies with caching"""
        if self._geographies_cache:
            return self._geographies_cache
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agmarknet/geographies",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                # Group the flat list by state
                state_data = {}
                for item in data["output"]["data"]:
                    state_id = item["census_state_id"]
                    state_name = item["census_state_name"]
                    district_id = item["census_district_id"]
                    district_name = item["census_district_name"]
                    
                    if state_id not in state_data:
                        state_data[state_id] = {
                            "state_name": state_name,
                            "districts": []
                        }
                    
                    state_data[state_id]["districts"].append(
                        District(
                            district_id=district_id,
                            district_name=district_name
                        )
                    )
                
                # Convert to Geography objects
                geographies = []
                for state_id, state_info in state_data.items():
                    geography = Geography(
                        state_id=state_id,
                        state_name=state_info["state_name"],
                        districts=state_info["districts"]
                    )
                    geographies.append(geography)
                
                self._geographies_cache = geographies
                return geographies
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting geographies: {e}")
                raise
            except Exception as e:
                logger.error(f"Error getting geographies: {e}")
                raise
    
    async def find_markets(self, commodity_id: int, state_id: int, district_id: int) -> List[Market]:
        """Find markets for given commodity, state, and district"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "commodity_id": commodity_id,
                    "state_id": state_id,
                    "district_id": district_id,
                    "indicator": "price"
                }
                
                response = await client.post(
                    f"{self.base_url}/agmarknet/markets",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                markets = [
                    Market(
                        census_state_id=item["census_state_id"],
                        census_district_id=item["census_district_id"],
                        market_id=item["market_id"],
                        market_name=item["market_name"]
                    )
                    for item in data["output"]["data"]
                ]
                return markets
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error finding markets: {e}")
                raise
            except Exception as e:
                logger.error(f"Error finding markets: {e}")
                raise
    
    async def get_prices(self, commodity_id: int, state_id: int, district_ids: List[int], 
                        market_ids: List[int], from_date: str, to_date: str) -> List[PriceData]:
        """Get commodity prices for specified parameters"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "commodity_id": commodity_id,
                    "state_id": state_id,
                    "district_id": district_ids,
                    "market_id": market_ids,
                    "from_date": from_date,
                    "to_date": to_date
                }
                
                response = await client.post(
                    f"{self.base_url}/agmarknet/prices",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                prices = [
                    PriceData(
                        date=item["date"],
                        commodity_id=item["commodity_id"],
                        census_state_id=item["census_state_id"],
                        census_district_id=item["census_district_id"],
                        market_id=item["market_id"],
                        min_price=item["min_price"],
                        max_price=item["max_price"],
                        modal_price=item["modal_price"]
                    )
                    for item in data["output"]["data"]
                ]
                return prices
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting prices: {e}")
                raise
            except Exception as e:
                logger.error(f"Error getting prices: {e}")
                raise
    
    async def get_quantities(self, commodity_id: int, state_id: int, district_ids: List[int],
                           market_ids: List[int], from_date: str, to_date: str) -> List[QuantityData]:
        """Get commodity arrival quantities for specified parameters"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "commodity_id": commodity_id,
                    "state_id": state_id,
                    "district_id": district_ids,
                    "market_id": market_ids,
                    "from_date": from_date,
                    "to_date": to_date
                }
                
                response = await client.post(
                    f"{self.base_url}/agmarknet/quantities",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                quantities = [
                    QuantityData(
                        date=item["date"],
                        commodity_id=item["commodity_id"],
                        census_state_id=item["census_state_id"],
                        census_district_id=item["census_district_id"],
                        market_id=item["market_id"],
                        quantity=item["quantity"]
                    )
                    for item in data["output"]["data"]
                ]
                return quantities
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting quantities: {e}")
                raise
            except Exception as e:
                logger.error(f"Error getting quantities: {e}")
                raise


# Initialize global API client
ceda_client = CEDAAPIClient()


async def resolve_commodity_intelligently(user_input: str, available_commodities: List[Commodity]) -> Optional[Commodity]:
    """
    Intelligently resolve user commodity input using LLM reasoning over available commodities.
    This replaces hardcoded mappings with dynamic AI-based resolution that can handle any language or variant.
    """
    user_input_clean = user_input.lower().strip()
    
    # First, try exact match
    for commodity in available_commodities:
        if user_input_clean == commodity.name.lower():
            return commodity
    
    # Then try partial matches for English names
    for commodity in available_commodities:
        if user_input_clean in commodity.name.lower() or commodity.name.lower() in user_input_clean:
            return commodity
    
    # For any other cases (regional languages, variations, etc.), use LLM reasoning
    # Create a context for the LLM to understand commodity mapping
    from google.adk.agents import LlmAgent
    
    commodity_list = "\n".join([f"- {c.name}" for c in available_commodities[:50]])  # Limit for token efficiency
    
    mapping_prompt = f"""
You are an agricultural commodity expert. A user mentioned "{user_input}" and I need to find the best match from this list of available commodities:

{commodity_list}

Consider that the user might use:
- Regional language names (Hindi: pyaaz=onion, aloo=potato, chawal=rice; Bengali: peyaj=onion, alu=potato; Tamil: vengayam=onion)
- Common variations (onions=onion, tomatoes=tomato)
- Local spellings or pronunciations

Return ONLY the exact commodity name from the list that best matches "{user_input}", or "NOT_FOUND" if no reasonable match exists.
"""
    
    try:
        # Use a simple LLM call for mapping (this would be more efficient than hardcoded mappings for edge cases)
        resolver_agent = LlmAgent(
            model="gemini-2.5-flash",
            name="Commodity_Resolver",
            instruction="You are a commodity name resolver. Return only the exact commodity name that matches the user input, or 'NOT_FOUND'."
        )
        
        # For now, fall back to minimal hardcoded mappings for performance
        # In a production system, you'd cache LLM results
        minimal_mappings = {
            "pyaaz": "onion", "aloo": "potato", "chawal": "rice", "gehun": "wheat",
            "peyaj": "onion", "alu": "potato", "chal": "rice", "gom": "wheat",
            "vengayam": "onion", "urulaikizhangu": "potato", "arisi": "rice",
            "onions": "onion", "potatoes": "potato", "tomatoes": "tomato", "chillies": "chilli"
        }
        
        if user_input_clean in minimal_mappings:
            target_name = minimal_mappings[user_input_clean]
            for commodity in available_commodities:
                if target_name.lower() in commodity.name.lower():
                    return commodity
        
    except Exception as e:
        logger.warning(f"LLM resolution failed, using fallback: {e}")
    
    # If no match found, return None and let the main function handle it
    return None


async def search_commodities(query: str) -> str:
    """
    Search and filter commodities by natural language query.
    Handles regional language names and variations.
    
    Args:
        query: Natural language commodity query (e.g., "onion", "pyaaz", "rice")
    
    Returns:
        Formatted list of matching commodities with IDs and names
    """
    try:
        ceda_client = CEDAAPIClient()
        commodities = await ceda_client.get_commodities()
        
        query_clean = query.lower().strip()
        matching_commodities = []
        
        # Regional language mappings for common commodities
        regional_mappings = {
            "pyaaz": "onion", "aloo": "potato", "chawal": "rice", "gehun": "wheat",
            "peyaj": "onion", "alu": "potato", "chal": "rice", "gom": "wheat",
            "vengayam": "onion", "urulaikizhangu": "potato", "arisi": "rice",
            "onions": "onion", "potatoes": "potato", "tomatoes": "tomato", 
            "chillies": "chilli", "chilies": "chilli"
        }
        
        # Check for regional mapping first
        search_term = regional_mappings.get(query_clean, query_clean)
        
        # Find matches
        for commodity in commodities:
            commodity_name_clean = commodity.name.lower()
            
            # Check for various types of matches
            if (search_term == commodity_name_clean or 
                search_term in commodity_name_clean or 
                commodity_name_clean in search_term):
                
                matching_commodities.append({
                    'id': commodity.id,
                    'name': commodity.name,
                    'relevance': len(search_term) / len(commodity_name_clean) if search_term in commodity_name_clean else 0.5
                })
        
        if not matching_commodities:
            available_commodities = [c.name for c in commodities[:20]]
            return f"❌ No commodities found matching '{query}'. Available commodities include: {', '.join(available_commodities)}..."
        
        # Sort by relevance
        matching_commodities.sort(key=lambda x: x['relevance'], reverse=True)
        
        result = f"🌾 Commodities matching '{query}':\n\n"
        for i, commodity in enumerate(matching_commodities[:10]):  # Limit to top 10
            result += f"{i+1}. **{commodity['name']}** (ID: {commodity['id']})\n"
        
        if len(matching_commodities) > 10:
            result += f"\n... and {len(matching_commodities) - 10} more matches"
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching commodities: {e}")
        return f"❌ Error searching commodities: {str(e)}"


async def list_all_commodities() -> str:
    """
    List all available commodities in the system.
    Useful for user reference when commodity not found.
    
    Returns:
        Complete list of all commodities with IDs
    """
    try:
        ceda_client = CEDAAPIClient()
        commodities = await ceda_client.get_commodities()
        
        result = f"📋 All Available Commodities ({len(commodities)} total):\n\n"
        
        # Group by category for better readability
        categories = {
            "Cereals": ["wheat", "rice", "paddy", "maize", "jowar", "bajra", "barley", "ragi"],
            "Pulses": ["gram", "tur", "moong", "urad", "masur", "arhar"],
            "Oilseeds": ["groundnut", "mustard", "sunflower", "soyabean", "sesame"],
            "Vegetables": ["onion", "potato", "tomato", "brinjal", "cauliflower", "cabbage"],
            "Fruits": ["apple", "banana", "mango", "orange", "grapes"],
            "Spices": ["turmeric", "chilli", "coriander", "cumin", "cardamom"]
        }
        
        categorized = {cat: [] for cat in categories}
        uncategorized = []
        
        for commodity in commodities:
            name_lower = commodity.name.lower()
            assigned = False
            
            for category, keywords in categories.items():
                if any(keyword in name_lower for keyword in keywords):
                    categorized[category].append(f"  • {commodity.name} (ID: {commodity.id})")
                    assigned = True
                    break
            
            if not assigned:
                uncategorized.append(f"  • {commodity.name} (ID: {commodity.id})")
        
        # Display categorized commodities
        for category, items in categorized.items():
            if items:
                result += f"**{category}:**\n"
                result += "\n".join(items[:10])  # Limit per category
                if len(items) > 10:
                    result += f"\n  ... and {len(items) - 10} more {category.lower()}"
                result += "\n\n"
        
        # Display uncategorized if not too many
        if uncategorized and len(uncategorized) <= 20:
            result += "**Other Commodities:**\n"
            result += "\n".join(uncategorized)
        elif uncategorized:
            result += f"**Other Commodities:** {len(uncategorized)} additional commodities available"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing commodities: {e}")
        return f"❌ Error listing commodities: {str(e)}"


async def list_all_states() -> str:
    """
    List all available states in the system.
    Useful for user reference when state not found.
    
    Returns:
        Complete list of all states with IDs and district counts
    """
    try:
        ceda_client = CEDAAPIClient()
        geographies = await ceda_client.get_geographies()
        
        result = f"🗺️ All Available States ({len(geographies)} total):\n\n"
        
        for i, geography in enumerate(geographies, 1):
            districts_count = len(geography.districts)
            result += f"{i:2d}. **{geography.state_name}** (ID: {geography.state_id}, {districts_count} districts)\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing states: {e}")
        return f"❌ Error listing states: {str(e)}"


async def list_districts_in_state(state_id: int) -> str:
    """
    List all districts in a specific state.
    
    Args:
        state_id: The ID of the state
    
    Returns:
        List of all districts in the specified state
    """
    try:
        ceda_client = CEDAAPIClient()
        geographies = await ceda_client.get_geographies()
        
        # Find the state
        target_state = None
        for geography in geographies:
            if geography.state_id == state_id:
                target_state = geography
                break
        
        if not target_state:
            return f"❌ State with ID {state_id} not found"
        
        result = f"🏘️ Districts in {target_state.state_name} ({len(target_state.districts)} total):\n\n"
        
        for i, district in enumerate(target_state.districts, 1):
            result += f"{i:2d}. **{district.district_name}** (ID: {district.district_id})\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing districts: {e}")
        return f"❌ Error listing districts: {str(e)}"


async def get_markets_for_commodity(commodity_id: int, state_id: int, district_id: int) -> str:
    """
    Get available markets for a specific commodity in a location.
    Direct wrapper for POST /agmarknet/markets endpoint.
    
    Args:
        commodity_id: ID of the commodity
        state_id: ID of the state  
        district_id: ID of the district
    
    Returns:
        List of available markets for the commodity in the location
    """
    try:
        ceda_client = CEDAAPIClient()
        markets = await ceda_client.find_markets(
            commodity_id=commodity_id,
            state_id=state_id,
            district_id=district_id
        )
        
        if not markets:
            return f"❌ No markets found for commodity ID {commodity_id} in state ID {state_id}, district ID {district_id}"
        
        result = f"🏪 Available Markets ({len(markets)} found):\n\n"
        
        for i, market in enumerate(markets, 1):
            result += f"{i:2d}. **{market.market_name}** (ID: {market.market_id})\n"
            result += f"     State ID: {market.census_state_id}, District ID: {market.census_district_id}\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting markets: {e}")
        return f"❌ Error getting markets: {str(e)}"


async def get_commodity_prices_data(commodity_id: int, level: str, location_ids: str, from_date: str, to_date: str) -> str:
    """
    Get commodity price data at different geographical levels.
    Direct wrapper for POST /agmarknet/prices endpoint.
    
    Args:
        commodity_id: ID of the commodity
        level: "national", "state", "district", or "market"
        location_ids: Comma-separated IDs based on level (empty for national)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    
    Returns:
        Raw price data for the specified parameters
    """
    try:
        ceda_client = CEDAAPIClient()
        
        # Parse location_ids based on level
        if level == "national":
            # National level - no specific location IDs needed
            prices = await ceda_client.get_prices(
                commodity_id=commodity_id,
                state_id=None,
                district_ids=[],
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "state":
            state_id = int(location_ids)
            prices = await ceda_client.get_prices(
                commodity_id=commodity_id,
                state_id=state_id,
                district_ids=[],
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "district":
            # Handle multiple district IDs for batch processing
            if ":" in location_ids:
                # Format: "state_id:district_id" for single district
                state_id, district_id = map(int, location_ids.split(":"))
                district_ids = [district_id]
            elif "," in location_ids:
                # Format: "district_id1,district_id2,district_id3" for multiple districts
                district_ids = [int(x.strip()) for x in location_ids.split(",")]
                # Find the state for the first district (assuming all districts are in same state)
                first_district_id = district_ids[0]
                geographies = await ceda_client.get_geographies()
                state_id = None
                for geo in geographies:
                    for district in geo.districts:
                        if district.district_id == first_district_id:
                            state_id = geo.state_id
                            break
                    if state_id:
                        break
                
                if not state_id:
                    return f"❌ Could not find state for district ID {first_district_id}"
            else:
                # Single district ID
                district_id = int(location_ids)
                district_ids = [district_id]
                # We need to find the state_id for this district
                geographies = await ceda_client.get_geographies()
                state_id = None
                for geo in geographies:
                    for district in geo.districts:
                        if district.district_id == district_id:
                            state_id = geo.state_id
                            break
                    if state_id:
                        break
                
                if not state_id:
                    return f"❌ Could not find state for district ID {district_id}"
            
            prices = await ceda_client.get_prices(
                commodity_id=commodity_id,
                state_id=state_id,
                district_ids=district_ids,
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "market":
            market_ids = [int(x.strip()) for x in location_ids.split(",")]
            # For market level, we need to get state and district info
            # This is a limitation - we'd need to track this info
            prices = await ceda_client.get_prices(
                commodity_id=commodity_id,
                state_id=None,  # Will be inferred from market
                district_ids=[],
                market_ids=market_ids,
                from_date=from_date,
                to_date=to_date
            )
        else:
            return f"❌ Invalid level '{level}'. Must be: national, state, district, or market"
        
        if not prices:
            return f"❌ No price data found for commodity ID {commodity_id} at {level} level for {from_date} to {to_date}"
        
        result = f"💰 Price Data (Commodity ID: {commodity_id}, Level: {level}):\n"
        result += f"📅 Period: {from_date} to {to_date}\n"
        result += f"📊 Records: {len(prices)}\n\n"
        
        # Group by location for better presentation
        location_data = {}
        for price in prices:
            location_key = f"State:{price.census_state_id}, District:{price.census_district_id}"
            if price.market_id:
                location_key += f", Market:{price.market_id}"
            
            if location_key not in location_data:
                location_data[location_key] = []
            location_data[location_key].append(price)
        
        for location, price_records in location_data.items():
            result += f"📍 **{location}**:\n"
            
            # Calculate averages
            avg_min = sum(p.min_price for p in price_records) / len(price_records)
            avg_max = sum(p.max_price for p in price_records) / len(price_records)
            avg_modal = sum(p.modal_price for p in price_records) / len(price_records)
            
            result += f"   💹 Average Price Range: ₹{avg_min:.2f} - ₹{avg_max:.2f}\n"
            result += f"   📈 Average Modal Price: ₹{avg_modal:.2f}\n"
            result += f"   📋 Data Points: {len(price_records)}\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting price data: {e}")
        return f"❌ Error getting price data: {str(e)}"


async def get_commodity_quantities_data(commodity_id: int, level: str, location_ids: str, from_date: str, to_date: str) -> str:
    """
    Get commodity quantity/arrival data at different geographical levels.
    Direct wrapper for POST /agmarknet/quantities endpoint.
    
    Args:
        commodity_id: ID of the commodity
        level: "national", "state", "district", or "market"
        location_ids: Comma-separated IDs based on level (empty for national)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    
    Returns:
        Raw quantity/arrival data for the specified parameters
    """
    try:
        ceda_client = CEDAAPIClient()
        
        # Parse location_ids based on level (same logic as prices)
        if level == "national":
            quantities = await ceda_client.get_quantities(
                commodity_id=commodity_id,
                state_id=None,
                district_ids=[],
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "state":
            state_id = int(location_ids)
            quantities = await ceda_client.get_quantities(
                commodity_id=commodity_id,
                state_id=state_id,
                district_ids=[],
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "district":
            # Handle multiple district IDs for batch processing
            if ":" in location_ids:
                # Format: "state_id:district_id" for single district
                state_id, district_id = map(int, location_ids.split(":"))
                district_ids = [district_id]
            elif "," in location_ids:
                # Format: "district_id1,district_id2,district_id3" for multiple districts
                district_ids = [int(x.strip()) for x in location_ids.split(",")]
                # Find the state for the first district (assuming all districts are in same state)
                first_district_id = district_ids[0]
                geographies = await ceda_client.get_geographies()
                state_id = None
                for geo in geographies:
                    for district in geo.districts:
                        if district.district_id == first_district_id:
                            state_id = geo.state_id
                            break
                    if state_id:
                        break
                
                if not state_id:
                    return f"❌ Could not find state for district ID {first_district_id}"
            else:
                # Single district ID
                district_id = int(location_ids)
                district_ids = [district_id]
                geographies = await ceda_client.get_geographies()
                state_id = None
                for geo in geographies:
                    for district in geo.districts:
                        if district.district_id == district_id:
                            state_id = geo.state_id
                            break
                    if state_id:
                        break
                
                if not state_id:
                    return f"❌ Could not find state for district ID {district_id}"
            
            quantities = await ceda_client.get_quantities(
                commodity_id=commodity_id,
                state_id=state_id,
                district_ids=district_ids,
                market_ids=[],
                from_date=from_date,
                to_date=to_date
            )
        elif level == "market":
            market_ids = [int(x.strip()) for x in location_ids.split(",")]
            quantities = await ceda_client.get_quantities(
                commodity_id=commodity_id,
                state_id=None,
                district_ids=[],
                market_ids=market_ids,
                from_date=from_date,
                to_date=to_date
            )
        else:
            return f"❌ Invalid level '{level}'. Must be: national, state, district, or market"
        
        if not quantities:
            return f"❌ No quantity data found for commodity ID {commodity_id} at {level} level for {from_date} to {to_date}"
        
        result = f"📦 Quantity/Arrival Data (Commodity ID: {commodity_id}, Level: {level}):\n"
        result += f"📅 Period: {from_date} to {to_date}\n"
        result += f"📊 Records: {len(quantities)}\n\n"
        
        # Group by location
        location_data = {}
        for quantity in quantities:
            location_key = f"State:{quantity.census_state_id}, District:{quantity.census_district_id}"
            if quantity.market_id:
                location_key += f", Market:{quantity.market_id}"
            
            if location_key not in location_data:
                location_data[location_key] = []
            location_data[location_key].append(quantity)
        
        for location, quantity_records in location_data.items():
            result += f"📍 **{location}**:\n"
            
            # Calculate totals and averages
            total_quantity = sum(q.quantity for q in quantity_records if q.quantity)
            avg_daily = total_quantity / len(quantity_records) if quantity_records else 0
            
            result += f"   📦 Total Arrivals: {total_quantity:,.0f} units\n"
            result += f"   📈 Average Daily: {avg_daily:,.0f} units\n"
            result += f"   📋 Data Points: {len(quantity_records)}\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting quantity data: {e}")
        return f"❌ Error getting quantity data: {str(e)}"


# ============================================================================
# COMPOSED WORKFLOW TOOLS (2-3 Atomic Tool Chains)
# ============================================================================

async def get_city_commodity_prices(city_name: str, commodity_name: str, timeframe: str = "today") -> str:
    """
    Get commodity prices for a specific city with intelligent location resolution.
    
    Workflow: find_location_for_city → search_commodities → get_commodity_prices_data
    API Calls: ~3 calls with caching
    
    Args:
        city_name: City name (e.g., "Mumbai", "Asansol", "Delhi")
        commodity_name: Commodity name (e.g., "Onion", "Rice", "Potato")
        timeframe: Time period (e.g., "today", "last week", "last month")
    
    Returns:
        Formatted price information with graceful degradation
    """
    try:
        result = f"🔍 Getting {commodity_name} prices in {city_name} for {timeframe}...\n\n"
        
        # Step 1: Location Resolution
        logger.info(f"Resolving location for city: {city_name}")
        location_result = await find_location_for_city(city_name)
        
        if "❌" in location_result:
            result += f"❌ Location Resolution Failed:\n{location_result}\n\n"
            result += f"💡 Try: search_states('{city_name}') or use a different city name"
            return result
        
        # Extract state and district IDs from location_result
        state_id = None
        district_id = None
        try:
            lines = location_result.split('\n')
            for line in lines:
                if "State:" in line and "ID:" in line:
                    state_id = line.split("ID: ")[1].split(")")[0].strip()
                elif "District:" in line and "ID:" in line:
                    district_id = line.split("ID: ")[1].split(")")[0].strip()
        except:
            result += f"❌ Could not extract location IDs from: {location_result}\n"
            return result
        
        if not state_id or not district_id:
            result += f"❌ Could not extract state/district IDs from location data\n"
            return result
            
        result += f"✅ Location: {location_result.split('Location found: ')[1].split('•')[0].strip()}\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n\n"
            result += f"💡 Try: list_all_commodities() to see available options"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID from search results\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: Price Data Retrieval
        logger.info(f"Getting price data for commodity {commodity_id} in district {district_id}")
        from_date, to_date = parse_date_range(timeframe)
        
        price_result = await get_commodity_prices_data(
            commodity_id=int(commodity_id),
            level="district",
            location_ids=district_id,
            from_date=from_date,
            to_date=to_date
        )
        
        if "❌" in price_result:
            result += f"❌ Price Data Failed:\n{price_result}\n\n"
            result += f"💡 Try a different timeframe or check if this commodity is traded in {city_name}"
            return result
        
        result += f"✅ Price Data Retrieved\n\n"
        result += price_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_city_commodity_prices: {e}")
        return f"❌ Unexpected error: {str(e)}\n💡 Try: list_all_commodities() or search_states('{city_name}')"


async def get_state_commodity_prices(state_name: str, commodity_name: str, timeframe: str = "today") -> str:
    """
    Get commodity prices across all districts in a state.
    
    Workflow: search_states → search_commodities → get_commodity_prices_data
    API Calls: ~3 calls with caching
    
    Args:
        state_name: State name (e.g., "West Bengal", "Maharashtra", "Punjab")
        commodity_name: Commodity name (e.g., "Rice", "Wheat", "Onion")
        timeframe: Time period (e.g., "today", "last week")
    
    Returns:
        State-wide price analysis with district breakdown
    """
    try:
        result = f"🗺️ Getting {commodity_name} prices across {state_name} for {timeframe}...\n\n"
        
        # Step 1: State Search
        logger.info(f"Searching for state: {state_name}")
        state_result = await search_states(state_name)
        
        if "❌" in state_result:
            result += f"❌ State Search Failed:\n{state_result}\n"
            return result
        
        # Extract state ID
        state_id = None
        try:
            lines = state_result.split('\n')
            for line in lines:
                if "ID:" in line and state_name.lower() in line.lower():
                    state_id = line.split("ID: ")[1].split(",")[0].strip()
                    break
        except:
            pass
            
        if not state_id:
            result += f"❌ Could not extract state ID from search results\n"
            return result
            
        result += f"✅ State: Found {state_name} (ID: {state_id})\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID from search results\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: State-Level Price Data
        logger.info(f"Getting state-level price data for commodity {commodity_id} in state {state_id}")
        from_date, to_date = parse_date_range(timeframe)
        
        price_result = await get_commodity_prices_data(
            commodity_id=int(commodity_id),
            level="state",
            location_ids=state_id,
            from_date=from_date,
            to_date=to_date
        )
        
        if "❌" in price_result:
            result += f"❌ Price Data Failed:\n{price_result}\n"
            return result
        
        result += f"✅ State-wide Price Data Retrieved\n\n"
        result += price_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_state_commodity_prices: {e}")
        return f"❌ Unexpected error: {str(e)}"


async def find_commodity_markets_in_city(city_name: str, commodity_name: str) -> str:
    """
    Find all markets selling a specific commodity in a city.
    
    Workflow: find_location_for_city → search_commodities → get_markets_for_commodity
    API Calls: ~3 calls with caching
    
    Args:
        city_name: City name (e.g., "Mumbai", "Delhi", "Kolkata")
        commodity_name: Commodity name (e.g., "Potato", "Onion", "Rice")
    
    Returns:
        List of markets with location details
    """
    try:
        result = f"🏪 Finding {commodity_name} markets in {city_name}...\n\n"
        
        # Step 1: Location Resolution
        logger.info(f"Resolving location for city: {city_name}")
        location_result = await find_location_for_city(city_name)
        
        if "❌" in location_result:
            result += f"❌ Location Resolution Failed:\n{location_result}\n"
            return result
        
        # Extract state and district IDs
        state_id = None
        district_id = None
        try:
            lines = location_result.split('\n')
            for line in lines:
                if "State:" in line and "ID:" in line:
                    state_id = line.split("ID: ")[1].split(")")[0].strip()
                elif "District:" in line and "ID:" in line:
                    district_id = line.split("ID: ")[1].split(")")[0].strip()
        except:
            pass
        
        if not state_id or not district_id:
            result += f"❌ Could not extract location IDs\n"
            return result
            
        result += f"✅ Location: {location_result.split('Location found: ')[1].split('•')[0].strip()}\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: Market Discovery
        logger.info(f"Finding markets for commodity {commodity_id} in district {district_id}")
        market_result = await get_markets_for_commodity(
            commodity_id=int(commodity_id),
            state_id=int(state_id),
            district_id=int(district_id)
        )
        
        result += f"\n🏬 Markets Found:\n\n"
        result += market_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_commodity_markets_in_city: {e}")
        return f"❌ Unexpected error: {str(e)}"


async def find_commodity_markets_in_state(state_name: str, commodity_name: str) -> str:
    """
    Find all markets selling a specific commodity across a state.
    
    Workflow: search_states → search_commodities → get_markets_for_commodity (state-level)
    API Calls: ~3-5 calls depending on districts
    
    Args:
        state_name: State name (e.g., "West Bengal", "Maharashtra")
        commodity_name: Commodity name (e.g., "Rice", "Wheat")
    
    Returns:
        State-wide market directory
    """
    try:
        result = f"🗺️ Finding {commodity_name} markets across {state_name}...\n\n"
        
        # Step 1: State Search
        logger.info(f"Searching for state: {state_name}")
        state_result = await search_states(state_name)
        
        if "❌" in state_result:
            result += f"❌ State Search Failed:\n{state_result}\n"
            return result
        
        # Extract state ID
        state_id = None
        try:
            lines = state_result.split('\n')
            for line in lines:
                if "ID:" in line and state_name.lower() in line.lower():
                    state_id = line.split("ID: ")[1].split(",")[0].strip()
                    break
        except:
            pass
            
        if not state_id:
            result += f"❌ Could not extract state ID\n"
            return result
            
        result += f"✅ State: Found {state_name} (ID: {state_id})\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: State-wide Market Discovery
        logger.info(f"Finding markets for commodity {commodity_id} across state {state_id}")
        
        # Get districts for this state first
        district_result = await search_districts(state_name, "")
        
        if "❌" in district_result:
            # Fallback: try at state level
            result += f"⚠️ Could not get districts, trying state-level search\n"
            market_result = await get_markets_for_commodity(
                commodity_id=int(commodity_id),
                state_id=int(state_id),
                district_id=""
            )
        else:
            # Extract a few district IDs for comprehensive search
            district_ids = []
            try:
                lines = district_result.split('\n')
                for line in lines[:10]:  # Limit to first 10 districts to avoid rate limits
                    if "ID:" in line:
                        district_id = line.split("ID: ")[1].split(")")[0].strip()
                        district_ids.append(district_id)
            except:
                pass
            
            if district_ids:
                market_result = await get_markets_for_commodity(
                    commodity_id=int(commodity_id),
                    state_id=int(state_id),
                    district_id=district_ids[0]  # Start with first district
                )
            else:
                market_result = await get_markets_for_commodity(
                    commodity_id=int(commodity_id),
                    state_id=int(state_id),
                    district_id=""
                )
        
        result += f"\n🏬 Markets Found Across {state_name}:\n\n"
        result += market_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in find_commodity_markets_in_state: {e}")
        return f"❌ Unexpected error: {str(e)}"


async def get_city_commodity_supply(city_name: str, commodity_name: str, timeframe: str = "last week") -> str:
    """
    Get commodity arrival/supply data for a specific city.
    
    Workflow: find_location_for_city → search_commodities → get_commodity_quantities_data
    API Calls: ~3 calls with caching
    
    Args:
        city_name: City name (e.g., "Mumbai", "Delhi", "Kolkata")
        commodity_name: Commodity name (e.g., "Rice", "Wheat", "Onion")
        timeframe: Time period (e.g., "last week", "last month")
    
    Returns:
        Supply/arrival analysis for the city
    """
    try:
        result = f"📦 Getting {commodity_name} supply data for {city_name} ({timeframe})...\n\n"
        
        # Step 1: Location Resolution
        logger.info(f"Resolving location for city: {city_name}")
        location_result = await find_location_for_city(city_name)
        
        if "❌" in location_result:
            result += f"❌ Location Resolution Failed:\n{location_result}\n"
            return result
        
        # Extract state and district IDs
        state_id = None
        district_id = None
        try:
            lines = location_result.split('\n')
            for line in lines:
                if "State:" in line and "ID:" in line:
                    state_id = line.split("ID: ")[1].split(")")[0].strip()
                elif "District:" in line and "ID:" in line:
                    district_id = line.split("ID: ")[1].split(")")[0].strip()
        except:
            pass
        
        if not state_id or not district_id:
            result += f"❌ Could not extract location IDs\n"
            return result
            
        result += f"✅ Location: {location_result.split('Location found: ')[1].split('•')[0].strip()}\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: Supply Data Retrieval
        logger.info(f"Getting supply data for commodity {commodity_id} in district {district_id}")
        from_date, to_date = parse_date_range(timeframe)
        
        supply_result = await get_commodity_quantities_data(
            commodity_id=int(commodity_id),
            level="district",
            location_ids=district_id,
            from_date=from_date,
            to_date=to_date
        )
        
        if "❌" in supply_result:
            result += f"❌ Supply Data Failed:\n{supply_result}\n"
            return result
        
        result += f"✅ Supply Data Retrieved\n\n"
        result += supply_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_city_commodity_supply: {e}")
        return f"❌ Unexpected error: {str(e)}"


async def get_state_commodity_supply(state_name: str, commodity_name: str, timeframe: str = "this month") -> str:
    """
    Get commodity supply data across all districts in a state.
    
    Workflow: search_states → search_commodities → get_commodity_quantities_data
    API Calls: ~3 calls with caching
    
    Args:
        state_name: State name (e.g., "West Bengal", "Punjab", "Maharashtra")
        commodity_name: Commodity name (e.g., "Rice", "Wheat", "Onion")
        timeframe: Time period (e.g., "this month", "last month")
    
    Returns:
        State-wide supply analysis
    """
    try:
        result = f"📊 Getting {commodity_name} supply data across {state_name} ({timeframe})...\n\n"
        
        # Step 1: State Search
        logger.info(f"Searching for state: {state_name}")
        state_result = await search_states(state_name)
        
        if "❌" in state_result:
            result += f"❌ State Search Failed:\n{state_result}\n"
            return result
        
        # Extract state ID
        state_id = None
        try:
            lines = state_result.split('\n')
            for line in lines:
                if "ID:" in line and state_name.lower() in line.lower():
                    state_id = line.split("ID: ")[1].split(",")[0].strip()
                    break
        except:
            pass
            
        if not state_id:
            result += f"❌ Could not extract state ID\n"
            return result
            
        result += f"✅ State: Found {state_name} (ID: {state_id})\n"
        
        # Step 2: Commodity Search
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n"
        
        # Step 3: State-Level Supply Data
        logger.info(f"Getting state-level supply data for commodity {commodity_id} in state {state_id}")
        from_date, to_date = parse_date_range(timeframe)
        
        supply_result = await get_commodity_quantities_data(
            commodity_id=int(commodity_id),
            level="state",
            location_ids=state_id,
            from_date=from_date,
            to_date=to_date
        )
        
        if "❌" in supply_result:
            result += f"❌ Supply Data Failed:\n{supply_result}\n"
            return result
        
        result += f"✅ State-wide Supply Data Retrieved\n\n"
        result += supply_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_state_commodity_supply: {e}")
        return f"❌ Unexpected error: {str(e)}"


async def compare_commodity_prices_between_cities(city_names: str, commodity_name: str, timeframe: str = "today") -> str:
    """
    Compare commodity prices across multiple cities (max 3 cities to avoid rate limits).
    
    Workflow: find_location_for_city (×N) → search_commodities → get_commodity_prices_data (×N) → compare
    API Calls: ~(2N + 1) calls where N = number of cities (max 3)
    
    Args:
        city_names: Comma-separated city names (e.g., "Mumbai, Delhi, Kolkata")
        commodity_name: Commodity name (e.g., "Onion", "Rice", "Potato")
        timeframe: Time period (e.g., "today", "last week")
    
    Returns:
        Comparative price analysis across cities
    """
    try:
        cities = [city.strip() for city in city_names.split(",")]
        if len(cities) > 3:
            cities = cities[:3]  # Limit to 3 cities to avoid rate limits
            
        result = f"⚖️ Comparing {commodity_name} prices across {', '.join(cities)} ({timeframe})...\n\n"
        
        # Step 1: Commodity Search (once for all cities)
        logger.info(f"Searching for commodity: {commodity_name}")
        commodity_result = await search_commodities(commodity_name)
        
        if "❌" in commodity_result:
            result += f"❌ Commodity Search Failed:\n{commodity_result}\n"
            return result
        
        # Extract commodity ID
        commodity_id = None
        try:
            lines = commodity_result.split('\n')
            for line in lines:
                if "ID:" in line and commodity_name.lower() in line.lower():
                    commodity_id = line.split("ID: ")[1].split(")")[0].strip()
                    break
        except:
            pass
            
        if not commodity_id:
            result += f"❌ Could not extract commodity ID\n"
            return result
            
        result += f"✅ Commodity: Found {commodity_name} (ID: {commodity_id})\n\n"
        
        # Step 2: Get prices for each city
        city_prices = []
        from_date, to_date = parse_date_range(timeframe)
        
        for city in cities:
            try:
                logger.info(f"Processing city: {city}")
                result += f"🔍 Processing {city}...\n"
                
                # Location resolution
                location_result = await find_location_for_city(city)
                if "❌" in location_result:
                    result += f"   ❌ Could not resolve {city}\n"
                    continue
                
                # Extract district ID
                district_id = None
                try:
                    lines = location_result.split('\n')
                    for line in lines:
                        if "District:" in line and "ID:" in line:
                            district_id = line.split("ID: ")[1].split(")")[0].strip()
                            break
                except:
                    pass
                
                if not district_id:
                    result += f"   ❌ Could not extract district ID for {city}\n"
                    continue
                
                # Get price data
                price_result = await get_commodity_prices_data(
                    commodity_id=int(commodity_id),
                    level="district",
                    location_ids=district_id,
                    from_date=from_date,
                    to_date=to_date
                )
                
                if "❌" in price_result:
                    result += f"   ❌ No price data for {city}\n"
                    continue
                
                # Extract average price (simplified extraction)
                avg_price = None
                try:
                    lines = price_result.split('\n')
                    for line in lines:
                        if "Average Modal Price:" in line:
                            avg_price = float(line.split("₹")[1].split()[0])
                            break
                except:
                    pass
                
                if avg_price:
                    city_prices.append({
                        "city": city,
                        "price": avg_price,
                        "district_id": district_id
                    })
                    result += f"   ✅ {city}: ₹{avg_price:.0f}\n"
                else:
                    result += f"   ⚠️ {city}: Price data available but couldn't parse average\n"
                    
            except Exception as e:
                result += f"   ❌ Error processing {city}: {str(e)}\n"
                continue
        
        # Step 3: Comparison Analysis
        if len(city_prices) < 2:
            result += f"\n❌ Need at least 2 cities with valid price data for comparison\n"
            return result
        
        # Sort by price
        city_prices.sort(key=lambda x: x["price"])
        
        result += f"\n📊 Price Comparison Results:\n\n"
        
        # Show ranking
        for i, item in enumerate(city_prices, 1):
            if i == 1:
                result += f"🥇 {item['city']}: ₹{item['price']:.0f} (LOWEST)\n"
            elif i == len(city_prices):
                result += f"🥉 {item['city']}: ₹{item['price']:.0f} (HIGHEST)\n"
            else:
                result += f"🥈 {item['city']}: ₹{item['price']:.0f}\n"
        
        # Price analysis
        lowest = city_prices[0]
        highest = city_prices[-1]
        difference = highest["price"] - lowest["price"]
        percentage = (difference / lowest["price"]) * 100
        
        result += f"\n💡 Analysis:\n"
        result += f"• Price Range: ₹{difference:.0f} ({percentage:.1f}% variation)\n"
        result += f"• Best Market: {lowest['city']} (₹{lowest['price']:.0f})\n"
        result += f"• Costliest Market: {highest['city']} (₹{highest['price']:.0f})\n"
        
        if percentage > 20:
            result += f"• 🚨 Significant price difference! Consider {lowest['city']} for better rates\n"
        elif percentage > 10:
            result += f"• ⚠️ Moderate price variation across markets\n"
        else:
            result += f"• ✅ Fairly consistent pricing across markets\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in compare_commodity_prices_between_cities: {e}")
        return f"❌ Unexpected error: {str(e)}"


# ============================================================================
# LOCATION RESOLUTION TOOLS (Atomic Level)
# ============================================================================


async def search_states(query: str) -> str:
    """
    Search for Indian states that match the given query.
    
    Args:
        query: Natural language query for state (e.g., "west bengal", "maharashtra", "bengal", "bombay")
    
    Returns:
        List of matching states with their IDs and districts count
    """
    try:
        geographies = await ceda_client.get_geographies()
        
        query_clean = query.lower().strip()
        matching_states = []
        
        for geography in geographies:
            state_name_clean = geography.state_name.lower()
            
            # Check for various types of matches
            if (query_clean == state_name_clean or 
                query_clean in state_name_clean or 
                state_name_clean in query_clean or
                # Handle common variations
                (query_clean == "bengal" and "west bengal" in state_name_clean) or
                (query_clean == "bombay" and "maharashtra" in state_name_clean)):
                
                matching_states.append({
                    "state_id": geography.state_id,
                    "state_name": geography.state_name,
                    "districts_count": len(geography.districts)
                })
        
        if not matching_states:
            available_states = [g.state_name for g in geographies[:15]]
            return f"❌ No states found matching '{query}'. Available states include: {', '.join(available_states)}..."
        
        result = f"🗺️ States matching '{query}':\n\n"
        for state in matching_states:
            result += f"• {state['state_name']} (ID: {state['state_id']}, {state['districts_count']} districts)\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching states: {e}")
        return f"❌ Error searching states: {str(e)}"


async def search_districts(state_query: str, district_query: str = "") -> str:
    """
    Search for districts within a state that match the given queries.
    
    Args:
        state_query: Natural language query for state (e.g., "west bengal", "maharashtra")
        district_query: Natural language query for district (e.g., "asansol", "mumbai", "kolkata")
    
    Returns:
        List of matching districts within the state
    """
    try:
        geographies = await ceda_client.get_geographies()
        
        state_query_clean = state_query.lower().strip()
        district_query_clean = district_query.lower().strip() if district_query else ""
        
        # First find the matching state(s)
        matching_states = []
        for geography in geographies:
            state_name_clean = geography.state_name.lower()
            
            if (state_query_clean == state_name_clean or 
                state_query_clean in state_name_clean or 
                state_name_clean in state_query_clean or
                (state_query_clean == "bengal" and "west bengal" in state_name_clean) or
                (state_query_clean == "bombay" and "maharashtra" in state_name_clean)):
                matching_states.append(geography)
        
        if not matching_states:
            return f"❌ No states found matching '{state_query}'. Use search_states tool first to find the correct state."
        
        result = f"🏘️ Districts in {matching_states[0].state_name}"
        if district_query:
            result += f" matching '{district_query}'"
        result += ":\n\n"
        
        matching_districts = []
        for state in matching_states:
            for district in state.districts:
                district_name_clean = district.district_name.lower()
                
                # If no district query, return all districts
                if not district_query_clean:
                    matching_districts.append({
                        "state_name": state.state_name,
                        "district_id": district.district_id,
                        "district_name": district.district_name
                    })
                # Otherwise, filter by district query
                elif (district_query_clean == district_name_clean or
                      district_query_clean in district_name_clean or
                      district_name_clean in district_query_clean or
                      # Handle city-to-district mappings
                      (district_query_clean == "asansol" and "barddhaman" in district_name_clean) or
                      (district_query_clean == "durgapur" and "barddhaman" in district_name_clean) or
                      (district_query_clean == "siliguri" and "darjeeling" in district_name_clean) or
                      (district_query_clean == "kharagpur" and "paschim medinipur" in district_name_clean) or
                      (district_query_clean == "mumbai" and "mumbai" in district_name_clean) or
                      (district_query_clean == "pune" and "pune" in district_name_clean) or
                      (district_query_clean == "bangalore" and "bangalore" in district_name_clean) or
                      (district_query_clean == "hyderabad" and "hyderabad" in district_name_clean)):
                    
                    matching_districts.append({
                        "state_name": state.state_name,
                        "district_id": district.district_id,
                        "district_name": district.district_name
                    })
        
        if not matching_districts:
            if district_query:
                # Show available districts in the state
                all_districts = [d.district_name for d in matching_states[0].districts[:10]]
                return f"❌ No districts found matching '{district_query}' in {matching_states[0].state_name}. Available districts: {', '.join(all_districts)}..."
            else:
                return f"❌ No districts found in {matching_states[0].state_name}"
        
        # Limit output for readability
        for i, district in enumerate(matching_districts[:20]):
            result += f"• {district['district_name']} (ID: {district['district_id']})\n"
        
        if len(matching_districts) > 20:
            result += f"... and {len(matching_districts) - 20} more districts\n"
        
        result += f"\n💡 Total matching districts: {len(matching_districts)}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching districts: {e}")
        return f"❌ Error searching districts: {str(e)}"


async def find_location_for_city(city_name: str) -> str:
    """
    Find the state and district for a given city or location name.
    
    Args:
        city_name: Name of city, town, or location (e.g., "asansol", "mumbai", "siliguri")
    
    Returns:
        State and district information for the city
    """
    try:
        geographies = await ceda_client.get_geographies()
        city_clean = city_name.lower().strip()
        
        # Known city-to-district mappings for major Indian cities
        city_mappings = {
            # West Bengal cities
            "asansol": ("west bengal", "barddhaman"),
            "durgapur": ("west bengal", "barddhaman"),
            "siliguri": ("west bengal", "darjeeling"),
            "kharagpur": ("west bengal", "paschim medinipur"),
            "kolkata": ("west bengal", "kolkata"),
            "calcutta": ("west bengal", "kolkata"),
            "howrah": ("west bengal", "howrah"),
            
            # Maharashtra cities
            "mumbai": ("maharashtra", "mumbai"),
            "bombay": ("maharashtra", "mumbai"),
            "pune": ("maharashtra", "pune"),
            "nagpur": ("maharashtra", "nagpur"),
            "nashik": ("maharashtra", "nashik"),
            "aurangabad": ("maharashtra", "aurangabad"),
            
            # Karnataka cities
            "bangalore": ("karnataka", "bangalore"),
            "bengaluru": ("karnataka", "bangalore"),
            "mysore": ("karnataka", "mysore"),
            "hubli": ("karnataka", "dharwad"),
            
            # Tamil Nadu cities
            "chennai": ("tamil nadu", "chennai"),
            "madras": ("tamil nadu", "chennai"),
            "coimbatore": ("tamil nadu", "coimbatore"),
            "madurai": ("tamil nadu", "madurai"),
            
            # Other major cities
            "delhi": ("delhi", "delhi"),
            "hyderabad": ("telangana", "hyderabad"),
            "ahmedabad": ("gujarat", "ahmedabad"),
            "surat": ("gujarat", "surat"),
            "jaipur": ("rajasthan", "jaipur"),
            "lucknow": ("uttar pradesh", "lucknow"),
            "kanpur": ("uttar pradesh", "kanpur"),
            "patna": ("bihar", "patna"),
            "bhopal": ("madhya pradesh", "bhopal"),
            "chandigarh": ("chandigarh", "chandigarh"),
        }
        
        # Check if city is in our known mappings
        if city_clean in city_mappings:
            target_state, target_district = city_mappings[city_clean]
            
            # Find the actual geography data
            for geography in geographies:
                if target_state.lower() in geography.state_name.lower():
                    for district in geography.districts:
                        if target_district.lower() in district.district_name.lower():
                            return f"📍 Location found: {city_name.title()}\n\n• State: {geography.state_name} (ID: {geography.state_id})\n• District: {district.district_name} (ID: {district.district_id})\n\n✅ This location can be used for market queries."
        
        # If not in known mappings, try to find district with similar name
        possible_matches = []
        for geography in geographies:
            for district in geography.districts:
                district_name_clean = district.district_name.lower()
                
                if (city_clean in district_name_clean or 
                    district_name_clean in city_clean):
                    possible_matches.append({
                        "state_name": geography.state_name,
                        "state_id": geography.state_id,
                        "district_name": district.district_name,
                        "district_id": district.district_id
                    })
        
        if possible_matches:
            result = f"🔍 Possible locations for '{city_name}':\n\n"
            for match in possible_matches[:5]:
                result += f"• {match['district_name']}, {match['state_name']}\n"
            result += f"\n💡 If one of these matches your intended location, use that state and district for market queries."
            return result
        
        return f"❌ Could not find location for '{city_name}'. Try using search_states and search_districts tools to find the correct state and district names."
        
    except Exception as e:
        logger.error(f"Error finding location for city: {e}")
        return f"❌ Error finding location: {str(e)}"


async def resolve_location_from_query(location_query: str) -> Tuple[Optional[Geography], Optional[District]]:
    """
    Simple helper function to resolve location for internal use.
    This function is used by the commodity price tools when they need to resolve locations.
    The agent should primarily use the search_states, search_districts, and find_location_for_city tools.
    """
    try:
        geographies = await ceda_client.get_geographies()
        location_clean = location_query.lower().strip()
        
        # Try exact district match first (most specific)
        for geography in geographies:
            for district in geography.districts:
                if location_clean == district.district_name.lower():
                    return geography, district
        
        # Try exact state match
        for geography in geographies:
            if location_clean == geography.state_name.lower():
                return geography, None
        
        # Try partial matches for districts
        for geography in geographies:
            for district in geography.districts:
                if (location_clean in district.district_name.lower() or 
                    district.district_name.lower() in location_clean):
                    return geography, district
        
        # Try partial matches for states
        for geography in geographies:
            if (location_clean in geography.state_name.lower() or 
                geography.state_name.lower() in location_clean):
                return geography, None
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error resolving location: {e}")
        return None, None


def parse_date_range(user_timeframe: str) -> Tuple[str, str]:
    """Parse user timeframe to (from_date, to_date) tuple"""
    today = datetime.now()
    
    user_timeframe_lower = user_timeframe.lower().strip()
    
    if user_timeframe_lower in ["today", "now"]:
        date_str = today.strftime("%Y-%m-%d")
        return (date_str, date_str)
    elif user_timeframe_lower in ["yesterday"]:
        yesterday = today - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        return (date_str, date_str)
    elif user_timeframe_lower in ["last week", "past week"]:
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    elif user_timeframe_lower in ["last month", "past month"]:
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    elif user_timeframe_lower in ["last 3 months", "past 3 months"]:
        from_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    else:
        # Default to today
        date_str = today.strftime("%Y-%m-%d")
        return (date_str, date_str)
    """Parse user timeframe to (from_date, to_date) tuple"""
    today = datetime.now()
    
    user_timeframe_lower = user_timeframe.lower().strip()
    
    if user_timeframe_lower in ["today", "now"]:
        date_str = today.strftime("%Y-%m-%d")
        return (date_str, date_str)
    elif user_timeframe_lower in ["yesterday"]:
        yesterday = today - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        return (date_str, date_str)
    elif user_timeframe_lower in ["last week", "past week"]:
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    elif user_timeframe_lower in ["last month", "past month"]:
        from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    elif user_timeframe_lower in ["last 3 months", "past 3 months"]:
        from_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        return (from_date, to_date)
    else:
        # Default to today
        date_str = today.strftime("%Y-%m-%d")
        return (date_str, date_str)


def create_agent() -> LlmAgent:
    """Create the Market Intelligence Agent"""
    return LlmAgent(
        model="gemini-2.5-flash",
        name="Market_Intelligence_Agent",
        instruction="""
            **Role:** You are an Advanced Agricultural Market Intelligence Agent specialized in Indian commodity markets.
            You provide comprehensive market analysis using atomic API tools to compose complex workflows dynamically.

            **CORE PHILOSOPHY: ATOMIC TOOLS ORCHESTRATION**
            You have access to atomic tools that map 1:1 with the CEDA Agmarknet API. Your job is to intelligently orchestrate 
            these tools to fulfill complex user requests. Think of yourself as a conductor orchestrating an API symphony.

            **AVAILABLE ATOMIC TOOLS:**

            **🗺️ LOCATION RESOLUTION (ALWAYS USE FIRST):**
            - `search_states(query)` - Find states by name/partial name (e.g., "bengal" → "West Bengal")
            - `search_districts(state_id, query)` - Find districts within a state (e.g., find "asansol" in West Bengal)
            - `find_location_for_city(city_name)` - Resolve any city to state+district (e.g., "Mumbai" → Maharashtra+Mumbai)
            
            **🌾 COMMODITY DISCOVERY:**
            - `search_commodities(query)` - Search commodities by name (e.g., "onion", "pyaaz", "aloo")
            - `list_all_commodities()` - Get complete list of 453+ available commodities
            
            **🏪 MARKET DISCOVERY:**
            - `get_markets_for_commodity(commodity_id, state_id, district_id)` - Find all markets selling a commodity
            
            **💰 PRICE DATA (Multi-Level):**
            - `get_commodity_prices_data(commodity_id, level, location_ids, from_date, to_date)`
              • level: "national", "state", "district", "market"
              • location_ids: comma-separated IDs based on level
              • Returns: min_price, max_price, modal_price for each location
            
            **📦 QUANTITY DATA (Multi-Level):**
            - `get_commodity_quantities_data(commodity_id, level, location_ids, from_date, to_date)`
              • level: "national", "state", "district", "market"  
              • location_ids: comma-separated IDs based on level
              • Returns: arrival quantities for supply analysis

            **🎼 WORKFLOW ORCHESTRATION EXAMPLES:**

            **1. Simple Price Query: "Onion price in Mumbai today"**
            ```
            1. find_location_for_city("Mumbai") → get Maharashtra(27) + Mumbai(495) 
            2. search_commodities("onion") → get Onion commodity_id(5)
            3. get_commodity_prices_data(5, "district", "495", "2024-01-15", "2024-01-15")
            ```

            **2. Market Comparison: "Compare rice prices in Punjab vs Haryana"**
            ```
            1. search_states("Punjab") → Punjab(3)
            2. search_states("Haryana") → Haryana(6)  
            3. search_commodities("rice") → Rice(3)
            4. get_commodity_prices_data(3, "state", "3,6", "2024-01-15", "2024-01-15")
            ```

            **3. Supply Analysis: "Rice arrivals in all West Bengal districts"**
            ```
            1. search_states("West Bengal") → West Bengal(19)
            2. search_commodities("rice") → Rice(3)
            3. get_commodity_quantities_data(3, "state", "19", "2024-01-01", "2024-01-15")
            ```

            **4. Market Discovery: "Where is potato sold in Uttar Pradesh?"**
            ```
            1. search_states("Uttar Pradesh") → UP(9)
            2. search_commodities("potato") → Potato(8)  
            3. search_districts(9, "") → get all UP districts
            4. For each district: get_markets_for_commodity(8, 9, district_id)
            ```

            **🧠 INTELLIGENT ORCHESTRATION PRINCIPLES:**

            **Location Resolution (CRITICAL):**
            - ALWAYS resolve locations first before any price/quantity queries
            - For ambiguous locations, try find_location_for_city first
            - If city lookup fails, try search_states or search_districts
            - Guide users to correct location names if resolution fails

            **Multi-Level Analysis:**
            - National level: Use level="national", location_ids="" (empty)
            - State level: Use level="state", location_ids="state_id1,state_id2" 
            - District level: Use level="district", location_ids="district_id1,district_id2"
            - Market level: Use level="market", location_ids="market_id1,market_id2"

            **Date Handling:**
            - Parse natural language dates ("today", "last week", "last month")
            - Convert to YYYY-MM-DD format for API calls
            - Default to today's date for current prices

            **Commodity Resolution:**
            - Handle Indian language names (pyaaz→onion, aloo→potato, chawal→rice)
            - Use search_commodities for partial/fuzzy matching
            - Fall back to list_all_commodities if search fails

            **Complex Workflow Composition:**
            - Break down complex requests into atomic tool calls
            - Chain tools logically (location → commodity → markets → data)
            - Aggregate results from multiple atomic calls
            - Provide comprehensive analysis from combined data

            **📊 OUTPUT FORMATTING:**
            - Use clear, farmer-friendly language with emojis
            - Structure data in logical sections (prices, trends, insights)
            - Provide actionable market intelligence
            - Include data sources and timestamps
            - Handle errors gracefully with helpful suggestions

            **🔄 ERROR HANDLING & GUIDANCE:**
            - If location resolution fails, suggest using search tools
            - If no markets found, try broader geographical areas
            - If no data available, explain seasonal/regional factors
            - Always provide alternative approaches when primary path fails
            
            **⚡ RATE LIMITING PROTECTION:**
            - CEDA API has rate limits - avoid too many concurrent calls
            - For large queries (e.g., "all districts in a state"), use state-level queries first
            - If you get 429 errors, suggest simpler queries or retry later
            - Batch district queries intelligently - don't call all 19 West Bengal districts at once
            - Use state-level aggregation when possible instead of individual district calls

            **REMEMBER: You are an orchestrator, not a single-function tool. Use the atomic tools creatively to build 
            comprehensive market intelligence workflows that would be impossible with rigid, pre-built functions.**
        """,
        description="Agricultural Market Intelligence Agent providing real-time commodity prices, market trends, and supply analysis for Indian farmers and traders using official Agmarknet data.",
        tools=[
            # ===== TIER 1: COMPOSED WORKFLOW TOOLS (RECOMMENDED) =====
            # Price Analysis Workflows
            get_city_commodity_prices,
            get_state_commodity_prices,
            compare_commodity_prices_between_cities,
            
            # Market Discovery Workflows
            find_commodity_markets_in_city,
            find_commodity_markets_in_state,
            
            # Supply Analysis Workflows
            get_city_commodity_supply,
            get_state_commodity_supply,
            
            # ===== TIER 2: ATOMIC TOOLS (ADVANCED/FALLBACK) =====
            # Location Resolution Tools
            search_states,
            search_districts, 
            find_location_for_city,
            
            # Commodity Discovery Tools
            search_commodities,
            list_all_commodities,
            
            # Market Discovery Tools  
            get_markets_for_commodity,
            
            # Price Data Tools (All Levels)
            get_commodity_prices_data,
            
            # Quantity Data Tools (All Levels)
            get_commodity_quantities_data,
        ],
    )
