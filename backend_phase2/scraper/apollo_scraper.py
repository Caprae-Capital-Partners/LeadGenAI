from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)  # Assuming you're using an LLM with an OpenAI-compatible API

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",  # Replace with actual base URL if different
)


def infer_business_type(description, industry=None):
    if not description or not description.strip():
        # Fallback 1: If no description but we have industry, try to infer from industry
        if industry and industry.strip():
            # Common B2B industries
            b2b_keywords = ["enterprise", "software", "saas", "manufacturing", "industrial", "consulting", "logistics", "wholesale", "b2b"]
            # Common B2C industries
            b2c_keywords = ["retail", "consumer", "ecommerce", "food", "restaurant", "hospitality", "travel", "b2c"]
            
            industry_lower = industry.lower()
            
            # Check for B2B indicators
            if any(keyword in industry_lower for keyword in b2b_keywords):
                return "B2B"
            # Check for B2C indicators
            elif any(keyword in industry_lower for keyword in b2c_keywords):
                return "B2C"
        
        return "N/A"

    prompt = (
        "You are a classifier. Based only on the description below, respond with one of the following labels: B2B, B2C, or B2B2C. "
        "Respond only with the label and nothing else.\n\n"
        f'Description:\n"{description}"\n\nBusiness Type:'
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # or the model you're using
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,  # Keep response short
            timeout=10,  # Add timeout to avoid hanging
        )
        label = response.choices[0].message.content.strip().upper()
        if label in ["B2B", "B2C", "B2B2C"]:
            return label
        else:
            # Fallback 2: If DeepSeek returns unexpected format, try keyword matching on description
            description_lower = description.lower()
            if "businesses" in description_lower or "enterprise" in description_lower or "companies" in description_lower:
                return "B2B"
            elif "consumers" in description_lower or "customers" in description_lower or "individuals" in description_lower:
                return "B2C"
            # Fallback 3: Try industry-based inference as a last resort
            elif industry and industry.strip():
                return infer_business_type("", industry)
            return "N/A"
    except Exception as e:
        print(f"[ERROR] Failed to classify business type: {e}")
        # Fallback 4: If DeepSeek API fails, try keyword matching
        try:
            description_lower = description.lower()
            if "businesses" in description_lower or "enterprise" in description_lower or "companies" in description_lower:
                return "B2B"
            elif "consumers" in description_lower or "customers" in description_lower or "individuals" in description_lower:
                return "B2C"
            # Fallback 5: Try industry-based inference as a last resort
            elif industry and industry.strip():
                return infer_business_type("", industry)
        except:
            pass
        return "N/A"


def enrich_single_company(domain):
    """Call Apollo API and extract founded_year, linkedin_url, keywords, annual_revenue_printed, website_url, employee_count."""
    url = "https://api.apollo.io/api/v1/organizations/enrich"
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY,
    }
    params = {"domain": domain}
    
    # Initialize default values
    result = {
        "founded_year": "",
        "linkedin_url": "",
        "keywords": "N/A",
        "annual_revenue_printed": "N/A",
        "website_url": domain if domain else "",
        "employee_count": "N/A",
        "industry": "N/A",
        "business_type": "N/A",
        "domain": domain,
    }

    try:
        # Set a timeout to avoid hanging requests
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            org = response.json().get("organization", {})
            
            # Extract basic information with fallbacks
            result["founded_year"] = org.get("founded_year", "")
            result["linkedin_url"] = org.get("linkedin_url", "")

            # Process industry with fallbacks
            industry = org.get("industry", "")
            industry_list = org.get("industries", [])
            
            # Prefer list if it exists and is non-empty
            if isinstance(industry_list, list) and industry_list:
                result["industry"] = ", ".join(industry_list[:5])  # limit to 5
            elif isinstance(industry, str) and industry.strip():
                result["industry"] = industry.strip()
            
            # Process keywords with fallbacks
            keywords_raw = org.get("keywords", [])
            if isinstance(keywords_raw, list) and keywords_raw:
                result["keywords"] = ", ".join(keywords_raw[:5])
                
            # Process revenue with multiple fallbacks
            annual_revenue_printed = org.get("annual_revenue_printed", "")
            annual_revenue = org.get("annual_revenue", "")
            estimated_annual_revenue = org.get("estimated_annual_revenue", "")
            
            # Try different revenue sources with fallbacks
            if annual_revenue_printed and annual_revenue_printed != "N/A":
                result["annual_revenue_printed"] = annual_revenue_printed
            elif annual_revenue and str(annual_revenue).isdigit():
                # Format numeric revenue as string with $ and appropriate suffix (M, B)
                revenue_num = int(annual_revenue)
                if revenue_num >= 1000000000:
                    result["annual_revenue_printed"] = f"${revenue_num/1000000000:.1f}B"
                elif revenue_num >= 1000000:
                    result["annual_revenue_printed"] = f"${revenue_num/1000000:.1f}M"
                else:
                    result["annual_revenue_printed"] = f"${revenue_num:,}"
            elif estimated_annual_revenue and str(estimated_annual_revenue).isdigit():
                # Format estimated revenue
                revenue_num = int(estimated_annual_revenue)
                if revenue_num >= 1000000000:
                    result["annual_revenue_printed"] = f"~${revenue_num/1000000000:.1f}B (est.)"
                elif revenue_num >= 1000000:
                    result["annual_revenue_printed"] = f"~${revenue_num/1000000:.1f}M (est.)"
                else:
                    result["annual_revenue_printed"] = f"~${revenue_num:,} (est.)"
            
            # Process website URL
            result["website_url"] = org.get("website_url", domain)
            
            # Process employee count with fallbacks
            employee_count = org.get("estimated_num_employees", "")
            employee_size_range = org.get("employee_size_range", "")
            
            if employee_count and str(employee_count).isdigit():
                result["employee_count"] = str(employee_count)
            elif employee_size_range:
                # Extract the average or middle value from range
                import re
                range_match = re.search(r'(\d+)-(\d+)', employee_size_range)
                if range_match:
                    min_emp = int(range_match.group(1))
                    max_emp = int(range_match.group(2))
                    result["employee_count"] = str(int((min_emp + max_emp) / 2))
            
            # Process company description and determine business type
            about = org.get("short_description", "")
            result["business_type"] = infer_business_type(about, result["industry"])
            
            return result
        else:
            print(f"[ERROR] Apollo API returned status {response.status_code} for domain {domain}")
            return result
    except requests.Timeout:
        print(f"[ERROR] Apollo API request timed out for domain {domain}")
        return result
    except Exception as e:
        print(f"[ERROR] Exception in Apollo API request for domain {domain}: {str(e)}")
        return result
