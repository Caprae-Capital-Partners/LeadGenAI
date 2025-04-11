import requests
import os
from dotenv import load_dotenv
import logging
import pandas as pd
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ApolloAPI:
    def __init__(self):
        self.api_key = os.getenv('APOLLO_API_KEY')
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in environment variables")
        
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Authorization": f"Bearer {self.api_key}"
        }

    def search_people(self, company_domain: str, titles: List[str] = None) -> List[Dict]:
        """
        Search for people at a company using Apollo API
        
        Args:
            company_domain: The company's domain (e.g., 'company.com')
            titles: List of job titles to search for (e.g., ['CEO', 'CTO', 'VP'])
            
        Returns:
            List of people matching the search criteria
        """
        try:
            # Build the search query
            query = {
                "q_organization_domains": company_domain,
                "page": 1,
                "per_page": 50
            }
            
            if titles:
                query["q_titles"] = titles
            
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                headers=self.headers,
                json=query
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('people', [])
            else:
                logging.error(f"Error searching people: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Exception while searching people: {str(e)}")
            return []

    def get_person_details(self, person_id: str) -> Optional[Dict]:
        """
        Get detailed information about a person including contact details
        
        Args:
            person_id: Apollo person ID
            
        Returns:
            Dictionary containing person's details or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/people/{person_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error getting person details: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Exception while getting person details: {str(e)}")
            return None

    def find_decision_makers(self, company_domain: str) -> pd.DataFrame:
        """
        Find decision-makers at a company and their contact details
        
        Args:
            company_domain: The company's domain
            
        Returns:
            DataFrame containing decision-makers and their contact details
        """
        # Define common decision-maker titles
        decision_maker_titles = [
            'CEO', 'CTO', 'CFO', 'COO', 'President',
            'Vice President', 'VP', 'Director', 'Head of',
            'Manager', 'Lead', 'Founder'
        ]
        
        # Search for people with these titles
        people = self.search_people(company_domain, decision_maker_titles)
        
        # Process results
        results = []
        for person in people:
            # Get detailed information
            details = self.get_person_details(person['id'])
            if details:
                result = {
                    'name': f"{person.get('first_name', '')} {person.get('last_name', '')}",
                    'title': person.get('title', ''),
                    'company': person.get('organization', {}).get('name', ''),
                    'linkedin_url': person.get('linkedin_url', ''),
                    'email': person.get('email', ''),
                    'phone': person.get('phone_numbers', [{}])[0].get('number', ''),
                    'location': person.get('location', '')
                }
                results.append(result)
        
        # Convert to DataFrame
        return pd.DataFrame(results)

    def enrich_company_data(self, company_domain: str) -> Dict:
        """
        Get additional company information from Apollo
        
        Args:
            company_domain: The company's domain
            
        Returns:
            Dictionary containing company details
        """
        try:
            response = requests.post(
                f"{self.base_url}/organizations/enrich",
                headers=self.headers,
                json={"domain": company_domain}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error enriching company data: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logging.error(f"Exception while enriching company data: {str(e)}")
            return {} 