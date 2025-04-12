from linkedin.decision_makers import get_business_info
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

apollo_api_key = os.getenv('APOLLO_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')  

# Test domain
test_domain = "microsoft.com"  # Using Microsoft as a test case

try:
    print(f"Testing with domain: {test_domain}")
    print(f"Using Apollo API key: {apollo_api_key[:5]}...")  # Show first 5 chars of API key
    
    result = get_business_info(
        domain=test_domain,
        deepseek_api_key=deepseek_api_key,
        apollo_api_key=apollo_api_key
    )
    
    print("\nBusiness Information Results:")
    print("----------------------------")
    for key, value in result.items():
        print(f"{key}: {value}")
except Exception as e:
    print(f"Error occurred: {str(e)}") 