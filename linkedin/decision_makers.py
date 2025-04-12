import requests
import logging
from typing import Dict
from apollo_api import ApolloAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_business_info(domain: str, deepseek_api_key: str, apollo_api_key: str) -> Dict:
    """
    Scrape and enrich business information based on a given website domain,
    using DeepSeek and Apollo APIs for enhanced data extraction.

    Args:
        domain (str): The domain of the business website (e.g., "example.com").
        deepseek_api_key (str): API key for DeepSeek, used for company enrichment or web understanding.
        apollo_api_key (str): API key for Apollo.io, used to find decision makers and estimate revenue.

    Returns:
        dict: A JSON-serializable dictionary containing:
            - domain (str): The input domain.
            - business_type (str): Type of business (e.g., "B2B", "B2C").
            - revenue (str): revenue from apollo (e.g., "$10M").
            - decision_maker_title (str): Title of a key decision maker (e.g., "CEO").
            - decision_maker_name (str): Full name of the decision maker.

    Raises:
        ValueError: If the input domain or API keys are invalid or not provided.
        Exception: For unexpected failures during API calls or data enrichment.
    """
    if not domain or not deepseek_api_key or not apollo_api_key:
        raise ValueError("Domain and API keys are required")

    try:
        # Initialize Apollo API with the provided key
        apollo = ApolloAPI()
        apollo.api_key = apollo_api_key  # Override the environment variable with provided key
        apollo.headers["Authorization"] = f"Bearer {apollo_api_key}"

        # Get company enrichment data from Apollo
        company_data = apollo.enrich_company_data(domain)
        if not company_data:
            raise Exception("Failed to get company data from Apollo")

        # Get decision makers from Apollo
        decision_makers_df = apollo.find_decision_makers(domain)
        if decision_makers_df.empty:
            raise Exception("No decision makers found")

        # Get the first decision maker (usually highest ranking)
        decision_maker = decision_makers_df.iloc[0]

        # Use DeepSeek API to analyze business type
        deepseek_url = "https://api.deepseek.ai/v1/chat/completions"
        deepseek_headers = {
            "Authorization": f"Bearer {deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        # Create a prompt to analyze the business type
        deepseek_prompt = f"""
        Analyze the following company domain and determine if it's primarily a B2B or B2C business.
        Consider the company's products/services, target audience, and business model.
        
        Domain: {domain}
        
        Return only one of these options:
        - B2B
        - B2C
        - Hybrid
        
        Provide a brief explanation for your choice.
        """
        
        deepseek_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a business analyst specializing in determining business models."},
                {"role": "user", "content": deepseek_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 150
        }
        
        deepseek_response = requests.post(
            deepseek_url,
            headers=deepseek_headers,
            json=deepseek_payload
        )
        
        if deepseek_response.status_code != 200:
            logging.warning("Failed to get business type from DeepSeek, using default")
            business_type = "B2B"  # Default to B2B if analysis fails
        else:
            response_data = deepseek_response.json()
            business_type = response_data.get("choices", [{}])[0].get("message", {}).get("content", "B2B")
            # Extract just the business type (B2B, B2C, or Hybrid)
            business_type = business_type.split("\n")[0].strip()

        # Prepare the result
        result = {
            "domain": domain,
            "business_type": business_type,
            "revenue": company_data.get("estimated_revenue", "Unknown"),
            "decision_maker_title": decision_maker.get("title", ""),
            "decision_maker_name": decision_maker.get("name", "")
        }

        return result

    except Exception as e:
        logging.error(f"Error getting business info: {str(e)}")
        raise 