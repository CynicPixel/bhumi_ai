# Market Intelligence Agent (ADK)

A sophisticated Agricultural Market Intelligence Agent built using Google ADK framework for the DemeterA2A agricultural intelligence ecosystem. This agent provides real-time commodity prices, market analysis, and supply data for Indian agricultural markets using the official CEDA Agmarknet API.

## Features

### 🌾 Core Capabilities
- **Real-time Commodity Prices**: Get current prices for agricultural commodities across Indian markets
- **Market Comparison**: Compare prices across multiple markets to identify best opportunities
- **Price Trend Analysis**: Analyze historical price trends for informed decision making
- **Supply Monitoring**: Track commodity arrival quantities and market supply conditions

### 🗣️ Multi-language Support
- **English**: Standard commodity names (Onion, Potato, Rice, Wheat, etc.)
- **Hindi**: Local names (pyaaz, aloo, chawal, gehun, etc.)
- **Bengali**: Regional names (peyaj, alu, chal, gom, etc.)
- **Tamil**: Regional names (vengayam, urulaikizhangu, arisi, etc.)

### 🏛️ Official Data Source
- **CEDA Agmarknet API**: Official Indian government agricultural market data
- **Comprehensive Coverage**: Major agricultural markets across India
- **Reliable Data**: Government-verified commodity prices and supply information

## Installation

### Prerequisites
- Python 3.10 or higher
- CEDA API key (obtain from [api.ceda.ashoka.edu.in](https://api.ceda.ashoka.edu.in))

### Setup
1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Set up environment variables**:
   Create a `.env` file with your CEDA API key:
   ```env
   CEDA_API_KEY=your_ceda_api_key_here
   ```

## Usage

### Command Line Interface

#### Run Demonstration
```bash
python -m market_agent_adk demo
```

#### Interactive Mode
```bash
python -m market_agent_adk interactive
```

#### Quick Test
```bash
python -m market_agent_adk test
```

### Example Queries

- "Get onion prices in Mumbai today"
- "Compare potato prices in Delhi and Kolkata"
- "What are current pyaaz prices in Kharagpur?" (Hindi)
- "Show rice price trends in Punjab last month"

### Programmatic Usage

```python
from market_agent_adk.agent_executor import executor

# Get commodity prices
response = await executor.execute("Get onion prices in Mumbai today")

# Compare markets
comparison = await executor.compare_markets("Potato", ["Delhi", "Mumbai"], "today")
```

## Agent Skills & Capabilities

### 🎯 **7 Comprehensive Market Intelligence Skills**

1. **Commodity Price Intelligence**: Advanced price analysis across 453+ commodities with city, state, and market-level data using CEDA Agmarknet API
2. **Market Discovery Intelligence**: Intelligent market location resolution and geographic intelligence across Indian agricultural markets  
3. **Supply Chain Analysis**: Comprehensive arrival quantities, supply conditions, and market flow analysis
4. **Comparative Market Analysis**: Multi-level comparative analysis across cities, states, markets, and time periods
5. **Intelligent Commodity Resolution**: Multilingual commodity search with fuzzy matching (Hindi, Bengali, Tamil support)
6. **Contextual Market Intelligence**: Context-aware analysis with conversation memory and personalized insights
7. **Atomic API Orchestration**: Dynamic orchestration of atomic CEDA API tools for custom market intelligence workflows

### 🛠️ **26+ Technical Tools Available**
- **Tier 1 Workflows**: `get_city_commodity_prices`, `get_state_commodity_prices`, `compare_commodity_prices_between_cities`
- **Market Discovery**: `find_commodity_markets_in_city`, `find_commodity_markets_in_state`
- **Supply Analysis**: `get_city_commodity_supply`, `get_state_commodity_supply`
- **Atomic Tools**: Location resolution, commodity search, market discovery, price/quantity data tools
- **Context Tools**: `get_conversation_context`, `get_last_conversation`

## Chain of Thought Resolution

The agent follows a 5-step resolution process:
1. Resolve commodity names (e.g., "pyaaz" → "Onion")
2. Resolve geography (e.g., "Kharagpur" → West Bengal, Paschim Medinipur)
3. Find specific markets
4. Execute precise API calls
5. Synthesize natural language responses

## Supported Data

### Commodities
Vegetables, Grains, Cash Crops, Fruits with multi-language support

### Locations
40+ supported locations across India including major cities and agricultural centers

### Time Periods
Current data (today) and historical data (last week, month, 3 months)

## Integration

Compatible with DemeterA2A framework and other agricultural agents using A2A protocol.

---

🌾 **Market Intelligence Agent | DemeterA2A Agricultural Intelligence Framework**
