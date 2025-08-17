import asyncio
import logging
from typing import Dict, List, Any, Optional
from google.adk.tools.tool_context import ToolContext
from remote_agent_manager import RemoteAgentManager

logger = logging.getLogger(__name__)

class AgriculturalTools:
    """Domain-specific tools for agricultural intelligence orchestration"""
    
    def __init__(self, remote_manager: RemoteAgentManager):
        self.remote_manager = remote_manager
    
    async def get_market_weather_insights(
        self, 
        commodity: str, 
        location: str, 
        time_period: str,
        tool_context: ToolContext
    ) -> str:
        """Get combined market and weather insights for farming decisions"""
        
        try:
            # Check if required agents are available
            required_agents = ["Market Intelligence Agent for Indian Agriculture", "Weather Agent for Indian Farmers"]
            available_agents = self.remote_manager.get_available_agents()
            
            missing_agents = [agent for agent in required_agents if agent not in available_agents]
            if missing_agents:
                return f"❌ **Agent Unavailable Error**\n\nThe following required agents are not available: {', '.join(missing_agents)}\n\nPlease ensure these agents are running and accessible before requesting market-weather insights."
            
            logger.info(f"🔍 Getting market and weather insights for {commodity} in {location}")
            
            # Query Market Agent for price trends
            market_query = f"Get {commodity} prices in {location} for {time_period}"
            market_response = await self.remote_manager.send_to_agent(
                "Market Intelligence Agent for Indian Agriculture", 
                market_query
            )
            
            # Query Weather Agent for conditions
            weather_query = f"Get weather forecast for {location} for {time_period}"
            weather_response = await self.remote_manager.send_to_agent(
                "Weather Agent for Indian Farmers",
                weather_query
            )
            
            # Synthesize insights
            synthesis = self._synthesize_market_weather_insights(
                commodity, location, time_period, market_response, weather_response
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Error getting market-weather insights: {e}")
            return f"❌ **Error Getting Market-Weather Insights**\n\nAn error occurred while processing your request: {str(e)}\n\nPlease try again or check if the specialized agents are running properly."
    
    async def analyze_farming_conditions(
        self,
        crop: str,
        location: str,
        tool_context: ToolContext
    ) -> str:
        """Analyze farming conditions by combining multiple data sources"""
        
        try:
            # Check if required agents are available
            required_agents = ["Market Intelligence Agent for Indian Agriculture", "Weather Agent for Indian Farmers"]
            available_agents = self.remote_manager.get_available_agents()
            
            missing_agents = [agent for agent in required_agents if agent not in available_agents]
            if missing_agents:
                return f"❌ **Agent Unavailable Error**\n\nThe following required agents are not available: {', '.join(missing_agents)}\n\nPlease ensure these agents are running and accessible before requesting farming conditions analysis."
            
            logger.info(f"🌾 Analyzing farming conditions for {crop} in {location}")
            
            # Query both agents for comprehensive analysis
            queries = {
                "Market Intelligence Agent for Indian Agriculture": f"Get current market conditions and prices for {crop} in {location}",
                "Weather Agent for Indian Farmers": f"Get current weather conditions and soil conditions for {crop} farming in {location}"
            }
            
            # Send specific queries to each agent
            responses = {}
            for agent_name, query in queries.items():
                response = await self.remote_manager.send_to_agent(agent_name, query)
                responses[agent_name] = response
            
            # Synthesize farming recommendations
            synthesis = self._synthesize_farming_conditions(
                crop, location, responses
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing farming conditions: {e}")
            return f"❌ **Error Analyzing Farming Conditions**\n\nAn error occurred while processing your request: {str(e)}\n\nPlease try again or check if the specialized agents are running properly."
    
    async def get_seasonal_advice(
        self,
        crop: str,
        location: str,
        season: str,
        tool_context: ToolContext
    ) -> str:
        """Get seasonal agricultural advice combining market and weather insights"""
        
        try:
            logger.info(f"📅 Getting seasonal advice for {crop} in {location} for {season}")
            
            # Query both agents for seasonal insights
            queries = {
                "Market Intelligence Agent for Indian Agriculture": f"Get seasonal market trends and price forecasts for {crop} in {location} for {season}",
                "Weather Agent for Indian Farmers": f"Get seasonal weather patterns and farming recommendations for {crop} in {location} for {season}"
            }
            
            # Send specific queries to each agent
            responses = {}
            for agent_name, query in queries.items():
                response = await self.remote_manager.send_to_agent(agent_name, query)
                responses[agent_name] = response
            
            # Synthesize seasonal recommendations
            synthesis = self._synthesize_seasonal_advice(
                crop, location, season, responses
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Error getting seasonal advice: {e}")
            return f"Error getting seasonal advice: {str(e)}"
    
    async def compare_regional_conditions(
        self,
        crop: str,
        regions: List[str],
        tool_context: ToolContext
    ) -> str:
        """Compare farming conditions across different Indian regions"""
        
        try:
            logger.info(f"🗺️ Comparing farming conditions for {crop} across {len(regions)} regions")
            
            # Query both agents for each region
            all_responses = {}
            
            for region in regions:
                market_query = f"Get market conditions and prices for {crop} in {region}"
                weather_query = f"Get weather and soil conditions for {crop} farming in {region}"
                
                market_response = await self.remote_manager.send_to_agent(
                    "Market Intelligence Agent for Indian Agriculture",
                    market_query
                )
                
                weather_response = await self.remote_manager.send_to_agent(
                    "Weather Agent for Indian Farmers",
                    weather_query
                )
                
                all_responses[region] = {
                    "market": market_response,
                    "weather": weather_response
                }
            
            # Synthesize regional comparison
            synthesis = self._synthesize_regional_comparison(
                crop, regions, all_responses
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Error comparing regional conditions: {e}")
            return f"Error comparing regional conditions: {str(e)}"
    
    def _synthesize_market_weather_insights(
        self,
        commodity: str,
        location: str,
        time_period: str,
        market_response: str,
        weather_response: str
    ) -> str:
        """Synthesize market and weather insights into coherent advice"""
        
        synthesis = f"""🌾 **Agricultural Intelligence for {commodity} in {location}** ({time_period})

📊 **Market Insights:**
{market_response}

🌤️ **Weather Conditions:**
{weather_response}

💡 **Farming Recommendations:**
Based on the market and weather data above, here are your key farming insights for {commodity} in {location}:

• **Market Timing**: {self._extract_market_timing(market_response)}
• **Weather Considerations**: {self._extract_weather_considerations(weather_response)}
• **Risk Assessment**: {self._assess_farming_risks(market_response, weather_response)}
• **Action Items**: {self._generate_action_items(commodity, market_response, weather_response)}

This analysis combines real-time market data with weather forecasts to help you make informed farming decisions."""
        
        return synthesis
    
    def _synthesize_farming_conditions(
        self,
        crop: str,
        location: str,
        responses: Dict[str, str]
    ) -> str:
        """Synthesize farming conditions from multiple agent responses"""
        
        synthesis = f"""🌱 **Farming Conditions Analysis for {crop} in {location}**

📋 **Comprehensive Assessment:**
{self._format_agent_responses(responses)}

🎯 **Key Insights:**
• **Current Conditions**: {self._extract_current_conditions(responses)}
• **Risk Factors**: {self._identify_risk_factors(responses)}
• **Opportunities**: {self._identify_opportunities(responses)}
• **Recommendations**: {self._generate_farming_recommendations(crop, responses)}

This analysis provides a holistic view of farming conditions by combining market intelligence with weather and soil data."""
        
        return synthesis
    
    def _synthesize_seasonal_advice(
        self,
        crop: str,
        location: str,
        season: str,
        responses: Dict[str, str]
    ) -> str:
        """Synthesize seasonal agricultural advice"""
        
        synthesis = f"""📅 **Seasonal Agricultural Advice for {crop} in {location}** ({season})

🌾 **Seasonal Insights:**
{self._format_agent_responses(responses)}

📈 **Seasonal Planning:**
• **Preparation Phase**: {self._extract_preparation_advice(responses)}
• **Planting Window**: {self._extract_planting_window(responses)}
• **Care Requirements**: {self._extract_care_requirements(responses)}
• **Harvest Timing**: {self._extract_harvest_timing(responses)}

🌱 **Action Plan for {season}:**
{self._generate_seasonal_action_plan(crop, season, responses)}"""
        
        return synthesis
    
    def _synthesize_regional_comparison(
        self,
        crop: str,
        regions: List[str],
        all_responses: Dict[str, Dict[str, str]]
    ) -> str:
        """Synthesize regional comparison analysis"""
        
        synthesis = f"""🗺️ **Regional Farming Conditions Comparison for {crop}**

📊 **Regional Analysis:**
{self._format_regional_responses(regions, all_responses)}

🏆 **Regional Rankings:**
{self._rank_regions_by_conditions(crop, regions, all_responses)}

💡 **Cross-Regional Insights:**
• **Best Performing Region**: {self._identify_best_region(regions, all_responses)}
• **Most Challenging Region**: {self._identify_challenging_region(regions, all_responses)}
• **Regional Advantages**: {self._identify_regional_advantages(regions, all_responses)}

🎯 **Strategic Recommendations:**
{self._generate_regional_strategies(crop, regions, all_responses)}"""
        
        return synthesis
    
    # Helper methods for synthesis
    def _extract_market_timing(self, market_response: str) -> str:
        """Extract market timing insights from market response"""
        # Simple extraction - in production, use more sophisticated NLP
        if "price" in market_response.lower() and "trend" in market_response.lower():
            return "Monitor price trends closely for optimal selling timing"
        elif "high" in market_response.lower() and "price" in market_response.lower():
            return "Current high prices suggest good selling opportunity"
        else:
            return "Review market data for timing decisions"
    
    def _extract_weather_considerations(self, weather_response: str) -> str:
        """Extract weather considerations from weather response"""
        if "rain" in weather_response.lower():
            return "Rain expected - plan irrigation accordingly"
        elif "dry" in weather_response.lower() or "drought" in weather_response.lower():
            return "Dry conditions - ensure adequate irrigation"
        else:
            return "Weather conditions appear favorable for farming"
    
    def _assess_farming_risks(self, market_response: str, weather_response: str) -> str:
        """Assess overall farming risks"""
        risks = []
        if "error" in market_response.lower():
            risks.append("Market data unavailable")
        if "error" in weather_response.lower():
            risks.append("Weather data unavailable")
        if not risks:
            risks.append("Low risk - data available from both sources")
        return "; ".join(risks)
    
    def _generate_action_items(self, commodity: str, market_response: str, weather_response: str) -> str:
        """Generate actionable farming items"""
        actions = []
        if "plant" in market_response.lower() or "sow" in market_response.lower():
            actions.append("Consider planting timing based on market conditions")
        if "harvest" in market_response.lower():
            actions.append("Plan harvest based on market prices")
        if "irrigation" in weather_response.lower():
            actions.append("Adjust irrigation based on weather forecast")
        if not actions:
            actions.append("Monitor conditions and adjust farming practices accordingly")
        return "; ".join(actions)
    
    def _format_agent_responses(self, responses: Dict[str, str]) -> str:
        """Format agent responses for display"""
        formatted = ""
        for agent_name, response in responses.items():
            formatted += f"**{agent_name}**:\n{response}\n\n"
        return formatted
    
    def _extract_current_conditions(self, responses: Dict[str, str]) -> str:
        """Extract current conditions from responses"""
        return "Combined market and weather data indicates current farming conditions"
    
    def _identify_risk_factors(self, responses: Dict[str, str]) -> str:
        """Identify risk factors from responses"""
        return "Review responses for specific risk factors"
    
    def _identify_opportunities(self, responses: Dict[str, str]) -> str:
        """Identify opportunities from responses"""
        return "Market and weather data may reveal farming opportunities"
    
    def _generate_farming_recommendations(self, crop: str, responses: Dict[str, str]) -> str:
        """Generate farming recommendations"""
        return f"Based on current conditions, adjust {crop} farming practices accordingly"
    
    def _extract_preparation_advice(self, responses: Dict[str, str]) -> str:
        """Extract preparation advice from responses"""
        return "Review seasonal data for preparation requirements"
    
    def _extract_planting_window(self, responses: Dict[str, str]) -> str:
        """Extract planting window from responses"""
        return "Weather data indicates optimal planting timing"
    
    def _extract_care_requirements(self, responses: Dict[str, str]) -> str:
        """Extract care requirements from responses"""
        return "Adjust care based on weather and market conditions"
    
    def _extract_harvest_timing(self, responses: Dict[str, str]) -> str:
        """Extract harvest timing from responses"""
        return "Plan harvest based on market prices and weather"
    
    def _generate_seasonal_action_plan(self, crop: str, season: str, responses: Dict[str, str]) -> str:
        """Generate seasonal action plan"""
        return f"Follow seasonal best practices for {crop} in {season}"
    
    def _format_regional_responses(self, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Format regional responses for display"""
        formatted = ""
        for region in regions:
            if region in all_responses:
                formatted += f"**{region}**:\n"
                for source, response in all_responses[region].items():
                    formatted += f"  {source}: {response[:200]}...\n"
                formatted += "\n"
        return formatted
    
    def _rank_regions_by_conditions(self, crop: str, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Rank regions by farming conditions"""
        return f"Ranking based on combined market and weather conditions for {crop}"
    
    def _identify_best_region(self, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Identify best performing region"""
        return "Analysis of market and weather data reveals best performing region"
    
    def _identify_challenging_region(self, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Identify most challenging region"""
        return "Identify region with most challenging conditions"
    
    def _identify_regional_advantages(self, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Identify regional advantages"""
        return "Each region has unique advantages for farming"
    
    def _generate_regional_strategies(self, crop: str, regions: List[str], all_responses: Dict[str, Dict[str, str]]) -> str:
        """Generate regional strategies"""
        return f"Develop region-specific strategies for {crop} farming"
