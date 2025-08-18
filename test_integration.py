#!/usr/bin/env python3
"""
Quick integration test for Bhumi AI system
Tests frontend, orchestrator, and backend agent connectivity
"""

import requests
import json
import time

def test_service_health(service_name, url):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name}: Healthy")
            return True
        else:
            print(f"❌ {service_name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name}: {str(e)}")
        return False

def test_orchestrator_api():
    """Test orchestrator API with a sample query"""
    url = "http://localhost:10007/"
    
    payload = {
        "jsonrpc": "2.0",
        "id": "test_001",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "user_id: test_farmer\n\nWhat are onion prices in Mumbai?"
                    }
                ],
                "messageId": "test_msg_001"
            }
        }
    }
    
    try:
        print("🧪 Testing orchestrator API...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "status" in data["result"]:
                print("✅ Orchestrator API: Working")
                print(f"📝 Response preview: {data['result']['status']['message']['parts'][0]['text'][:100]}...")
                return True
            else:
                print(f"❌ Orchestrator API: Invalid response format")
                return False
        else:
            print(f"❌ Orchestrator API: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator API: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("🌾 Bhumi AI Integration Test")
    print("=" * 50)
    
    # Test all service health endpoints
    services = [
        ("Frontend", "http://localhost:3000"),
        ("Orchestrator", "http://localhost:10007/.well-known/agent.json"),
        ("Market Agent", "http://localhost:10006/.well-known/agent.json"),
        ("Weather Agent", "http://localhost:10005/.well-known/agent.json"),
        ("Schemes Agent", "http://localhost:10004/.well-known/agent.json"),
    ]
    
    print("\n🔍 Health Check Results:")
    print("-" * 30)
    
    healthy_services = 0
    for service_name, url in services:
        if test_service_health(service_name, url):
            healthy_services += 1
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n📊 Health Summary: {healthy_services}/{len(services)} services healthy")
    
    # Test orchestrator API if it's healthy
    if healthy_services >= 4:  # At least orchestrator + 3 agents
        print("\n🚀 API Integration Test:")
        print("-" * 30)
        test_orchestrator_api()
    else:
        print("\n⚠️  Skipping API test - not enough services healthy")
    
    print("\n" + "=" * 50)
    if healthy_services == len(services):
        print("🎉 All systems operational! Frontend ready at http://localhost:3000")
    else:
        print("⚠️  Some services may need attention. Check the logs above.")
    
    print("\n💡 Next steps:")
    print("   1. Open http://localhost:3000 in your browser")
    print("   2. Try asking: 'What are onion prices in Mumbai?'")
    print("   3. Test voice recording and image upload features")
    print("   4. Use quick action buttons for common queries")

if __name__ == "__main__":
    main()
