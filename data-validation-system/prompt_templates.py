# prompt_templates.py

class PromptTemplates:
    """
    Templates for different validation prompts
    """
    
    @staticmethod
    def revenue_validation_prompt(company_info, revenue_data):
        """Template for validating revenue"""
        company_name = company_info.get('name', company_info.get('Business Name', 'Unknown Company'))
        
        # Format company context
        context_parts = []
        fields = {
            'Industry': company_info.get('Industry', 'Not specified'),
            'Company Size': company_info.get('Company Size', 'Not specified'),
            'Founded': company_info.get('Founded', 'Not specified'),
            'Headquarters': company_info.get('Headquarters', 'Not specified')
        }
        
        for field, value in fields.items():
            if value and value != 'Not specified' and value != 'Not found':
                context_parts.append(f"{field}: {value}")
        
        context = "\n".join(context_parts)
        
        # Get revenue value and source
        revenue_value = revenue_data.get('estimated_revenue', 'Not available')
        revenue_source = revenue_data.get('source', 'Unknown source')
        
        prompt = f"""Please validate the following company revenue data:

Company: {company_name}
{context}

Revenue: {revenue_value}
Source: {revenue_source}

Based on your knowledge of businesses and industry patterns, please:
1. Provide a confidence score from 0.0 to 1.0 (where 1.0 is highly confident in the data's accuracy)
2. Briefly explain your reasoning
3. Identify any potential issues or flags with this revenue figure

Return your assessment in this JSON format:
{{
  "confidence": 0.0,
  "explanation": "Your explanation here",
  "flags": ["Flag 1", "Flag 2"]
}}
"""
        return prompt
    
    @staticmethod
    def employee_count_validation_prompt(company_info):
        """Template for validating employee count"""
        company_name = company_info.get('name', company_info.get('Business Name', 'Unknown Company'))
        
        # Format company context
        context_parts = []
        fields = {
            'Industry': company_info.get('Industry', 'Not specified'),
            'Founded': company_info.get('Founded', 'Not specified'),
            'Headquarters': company_info.get('Headquarters', 'Not specified'),
            'Revenue': company_info.get('estimated_revenue', 'Not specified')
        }
        
        for field, value in fields.items():
            if value and value != 'Not specified' and value != 'Not found':
                context_parts.append(f"{field}: {value}")
        
        context = "\n".join(context_parts)
        
        # Get employee count value
        employee_count = company_info.get('Company Size', 'Not available')
        
        prompt = f"""Please validate the following company employee count data:

Company: {company_name}
{context}

Employee Count: {employee_count}
Source: LinkedIn

Based on your knowledge of businesses and industry patterns, please:
1. Provide a confidence score from 0.0 to 1.0 (where 1.0 is highly confident in the data's accuracy)
2. Briefly explain your reasoning
3. Identify any potential issues or flags with this employee count

Return your assessment in this JSON format:
{{
  "confidence": 0.0,
  "explanation": "Your explanation here",
  "flags": ["Flag 1", "Flag 2"]
}}
"""
        return prompt
    
    @staticmethod
    def decision_maker_validation_prompt(company_info, decision_maker):
        """Template for validating decision maker information"""
        company_name = company_info.get('name', company_info.get('Business Name', 'Unknown Company'))
        
        # Format company context
        context_parts = []
        fields = {
            'Industry': company_info.get('Industry', 'Not specified'),
            'Company Size': company_info.get('Company Size', 'Not specified'),
            'Founded': company_info.get('Founded', 'Not specified'),
            'Headquarters': company_info.get('Headquarters', 'Not specified')
        }
        
        for field, value in fields.items():
            if value and value != 'Not specified' and value != 'Not found':
                context_parts.append(f"{field}: {value}")
        
        context = "\n".join(context_parts)
        
        # Format decision maker data
        name = decision_maker.get('name', decision_maker.get('Name', 'Not available'))
        title = decision_maker.get('title', decision_maker.get('Title', 'Not available'))
        source = decision_maker.get('source', decision_maker.get('Source', 'Unknown source'))
        
        prompt = f"""Please validate the following company decision maker data:

Company: {company_name}
{context}

Decision Maker:
- Name: {name}
- Title: {title}
Source: {source}

Based on your knowledge of businesses and industry patterns, please:
1. Provide a confidence score from 0.0 to 1.0 (where 1.0 is highly confident in the data's accuracy)
2. Briefly explain your reasoning
3. Identify any potential issues or flags with this decision maker information

Return your assessment in this JSON format:
{{
  "confidence": 0.0,
  "explanation": "Your explanation here",
  "flags": ["Flag 1", "Flag 2"]
}}
"""
        return prompt
    
    @staticmethod
    def batch_validation_prompt(company_info, data_points):
        """Template for validating multiple data points at once"""
        company_name = company_info.get('name', company_info.get('Business Name', 'Unknown Company'))
        
        # Format company context
        context_parts = []
        fields = {
            'Industry': company_info.get('Industry', 'Not specified'),
            'Company Size': company_info.get('Company Size', 'Not specified'),
            'Founded': company_info.get('Founded', 'Not specified'),
            'Headquarters': company_info.get('Headquarters', 'Not specified')
        }
        
        for field, value in fields.items():
            if value and value != 'Not specified' and value != 'Not found':
                context_parts.append(f"{field}: {value}")
        
        context = "\n".join(context_parts)
        
        # Format data points
        data_points_text = ""
        for point_name, point_data in data_points.items():
            data_points_text += f"\n{point_name}: {point_data.get('value', 'Not available')}"
            if 'source' in point_data:
                data_points_text += f" (Source: {point_data['source']})"
        
        prompt = f"""Please validate the following business data points for a company:

Company: {company_name}
{context}

Data points to validate:{data_points_text}

Based on your knowledge of businesses and industry patterns, please validate each data point separately.
For each data point:
1. Provide a confidence score from 0.0 to 1.0 (where 1.0 is highly confident in the data's accuracy)
2. Briefly explain your reasoning
3. Identify any potential issues or flags

Return your assessment in this JSON format:
{{
  "data_points": {{
    "data_point_1_name": {{
      "confidence": 0.0,
      "explanation": "Your explanation here",
      "flags": ["Flag 1", "Flag 2"]
    }},
    "data_point_2_name": {{
      "confidence": 0.0,
      "explanation": "Your explanation here",
      "flags": ["Flag 1", "Flag 2"]
    }}
  }}
}}

Replace 'data_point_1_name', etc. with the actual data point names.
"""
        return prompt