import sys
import time
import random
import pandas as pd
import os
import asyncio
import re
# import yfinance as yf
import platform
import subprocess
import matplotlib.pyplot as plt
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import ollama
from backend.config.browser_config import PlaywrightManager
from datetime import datetime
import google_maps_scraper as gms
import httpx
from gradio_client import Client
from huggingface_hub import login
from openai import OpenAI

class AsyncCompanyScraper:
    def __init__(self):
        self.df = pd.DataFrame(columns=[
            'Overview', 'Product Services', 'Revenue'
        ])
        # self.sources = ["Name", "Overview", "Products & Services", "Revenue Zoominfo", "Revenue RocketReach", "General Revenue", "Employee", "Year Founded", "Business Type"]
        self.sources = ["Name", "Overview", "Products & Services"]
        self.google_search = "https://www.bing.com/search?q="
        self.manager = PlaywrightManager(headless=True)
        # self.client = Client("Fatmagician/caprae_scraper")
        # self.client = Client.duplicate("Fatmagician/caprae_scraper", hf_token='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')
        self.client = OpenAI(api_key="sk-b37194c5c44e4653ac21eee3c20f2ee1", base_url="https://api.deepseek.com")
        
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async def fetch_page_text(self, page, url, tags_to_find):
        try:
            await page.goto(url)
            await page.wait_for_load_state("domcontentloaded")
            
            await page.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                all.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none') el.style.display = 'block';
                    if (style.visibility === 'hidden') el.style.visibility = 'visible';
                    if (style.opacity === '0') el.style.opacity = '1';
                });
            }
            """)

            texts = []
            for tag in tags_to_find:
                elements = await page.query_selector_all(tag)
                texts.extend([await element.inner_text() for element in elements])
                
            return "\n".join(texts)
        except Exception as e:
            return f"Error loading page: {e}"

    async def process_company(self, company_name):
        current_year = datetime.now().year
        urls = [
            f'https://www.bing.com/search?q={company_name}+LinkedIn',
            f'https://www.bing.com/search?q={company_name}+Products+Services',
            # f'https://www.bing.com/search?q={company_name}+Revenue+Zoominfo',
            # f'https://www.bing.com/search?q={company_name}+Revenue+RocketReach',
            # f'https://www.bing.com/search?q={company_name}+Revenue+"{current_year}"',
            # f'https://www.bing.com/search?q={company_name}+Founder',
            # f'https://www.bing.com/search?q=How+much+employee+works+in+{company_name}',
            # f'https://www.bing.com/search?q=When+is+{company_name}+Founded',
        ]
        
        def extract_revenue(text):
            pattern = re.compile(
                r'(?P<sign><|>)?\s*(?P<symbol>\$)?\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>million|billion|m|b|M|B)?',
                re.IGNORECASE
            )

            match = pattern.search(text)
            if match:
                sign = match.group('sign') or ''
                symbol = match.group('symbol') or '$'
                amount = float(match.group('amount'))
                unit = (match.group('unit') or '').lower()

                if unit in ['m', 'million']:
                    return f"{sign}{symbol}{round(amount, 2)}M"
                elif unit in ['b', 'billion']:
                    return f"{sign}{symbol}{round(amount, 2)}B"
                else:
                    return f"{sign}{symbol}{round(amount, 2)}"

            return None

        async with async_playwright() as p:
            await self.manager.start_browser(stealth_on = False)  # start once
            context = await self.manager.browser.new_context()
            
            #Get real URLS for Overview
            # new_urls = []
            # for i in range(len(urls)):
            #     # query = f"{google_search}{company_name} {sources[i]}"
            #     # page.goto(query)
            #     page = await context.new_page()
                
            #     await page.goto(urls[i])
            #     await page.wait_for_load_state("domcontentloaded")
                
            #     links = await page.query_selector_all("a")

            #     found_url = None
            #     for link in links:
            #         href = await link.get_attribute('href')
            #         if not href:
            #             continue

            #         if i == 0 and 'linkedin.com/company/' in href:
            #             found_url = href
            #             break
            #         elif i == 1 and 'finance.yahoo.com/quote/' in href:
            #             found_url = href
            #             break
            #         elif i == 2 and 'bing.com' not in href and href.startswith('http'):
            #             found_url = href
            #             break

            #     new_urls.append(found_url if found_url else 'Not Found')
                
            # print(new_urls[0])
            # urls[0] = new_urls[0]
            
            tasks = []
            for url in urls:
                page = await context.new_page()
                tasks.append(self.fetch_page_text(page, url, ['p', 'h1', 'h2', 'h3']))

            texts = await asyncio.gather(*tasks)
            await self.manager.stop_browser()

            print(f"Total texts extracted: {len(texts)}")

            # Menghindari IndexError
            overview_text = texts[0] if len(texts) > 0 else "No overview data"
            services_text = texts[1] if len(texts) > 1 else "No services data"
            # zoominfo_text = texts[2] if len(texts) > 2 else "No services data"
            # rocket_text = texts[3] if len(texts) > 3 else "No services data"
            # revenue_text = texts[4] if len(texts) > 4 else "No services data"
            # founder_text = texts[5] if len(texts) > 5 else "No services data"
            # employee_text = texts[6] if len(texts) > 6 else "No services data"
            # year_text = texts[7] if len(texts) > 7 else "No services data"
            
            prompts = [
                f"Explain in brief about {company_name} using the info provided: {overview_text}. Explain in about 50 words. Only answer by using the given information.",
                f"Explain what {company_name} offers in terms of its products or the services they provide using this info: {services_text}. Provide a overview of around 100 words. Only answer by using the given information.",
                # f"Please tell me the provided revenue of {company_name} based on this info: {zoominfo_text}. Just return give a number & the unit to represent the revenue based on provided information. Only answer by a number with its unit. (Shortest answer as possible). If not sure then answer with Not Found",
                # f"Please tell me the provided revenue of {company_name} based on this info: {rocket_text}. Just return give a number & the unit to represent the revenue based on provided information. Only answer by a number with its unit. (Shortest answer as possible). If not sure then answer with Not Found",
                # f"Please tell me the provided revenue of {company_name} based on this info: {revenue_text}. Just return give a number & the unit to represent the revenue based on provided information in {current_year} (if possible). Only answer by a number with its unit. (Shortest answer as possible). if not sure then answer with Not Found",
                # f"Please tell me the full name of founder or owner of {company_name} company based on this info: {founder_text}. Only return the name of the individual. (Shortest answer as possible)",
                # f"Based on using this information: {employee_text}. How much employee works in {company_name}? Only return with a number, if not sure then answer with Not Found",
                # f"Based on using this information: {year_text}. What year/when is {company_name} founded? Just return with the most possible year number. (Shortest answer as possible)",
                # f"Based on using this information: {overview_text + services_text}. What type of business is {company_name}? Is it Business to Customers (B2C) or Business to Businesses (B2B)? Only return with either B2B or B2C or B2B, B2C (if both) (Shortest answer as possible)"
            ]
            
            answers = []
            with open('base_knowledge.txt', 'r', encoding='utf-8') as f:
                base_knowledge = f.read()
            for prompt in prompts:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are an intelligent extraction agent. Your job is to analyze raw text (scraped from search engines) and extract accurate company information, **based only on what's actually in the text**. If the required info is missing or uncertain, return: Not Found."},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False
                )
                
                # print(response.choices[0].message.content)
                answers.append(response.choices[0].message.content)

            await self.manager.stop_browser()
            
            # answers[2] = extract_revenue(answers[2])
            # answers[3] = extract_revenue(answers[3])
            # answers[4] = extract_revenue(answers[4])

        return {
            "Name": company_name,
            "Overview": answers[0] if len(answers) > 0 else "Not Found",
            "Products & Services": answers[1] if len(answers) > 1 else "Not Found",
            # "Zoominfo Revenue": answers[2] if len(answers) > 2 else "Not Found",
            # "RocketReach Revenue": answers[3] if len(answers) > 3 else "Not Found",
            # "General Revenue": answers[4] if len(answers) > 4 else "Not Found",
            # "Founder/CEO": answers[5] if len(answers) > 5 else "Not Found",
            # "Employee": answers[6] if len(answers) > 6 else "Not Found",
            # "Year Founded": answers[7] if len(answers) > 7 else "Not Found",
            # "Business Type": answers[8] if len(answers) > 8 else "Not Found",
        }

    async def save(self, df, folder='../data'):
        os.makedirs(folder, exist_ok=True)
        df = pd.DataFrame([df])
        # df.to_csv(os.path.join(folder, 'overview & products/services.csv'), index=False)
        # df.to_excel(os.path.join(folder, 'overview & products/services.xlsx'), index=False)
        
        # # Make sure the folder exists
        # os.makedirs(folder, exist_ok=True)
    
        # Set file paths
        csv_path = os.path.join(folder, 'overview_and_products_services.csv')
        excel_path = os.path.join(folder, 'overview_and_products_services.xlsx')
    
        if os.path.exists(csv_path):
            data = pd.read_csv(csv_path)
            data = pd.concat([data, df], axis=0).reset_index(drop=True)
            data.to_csv(csv_path, index=False)
            data.to_excel(excel_path, index=False)
        else:
            df.to_csv(csv_path, index=False)
            df.to_excel(excel_path, index=False)
            
    async def combine_leads(self, df, leads, folder='../data'):
        os.makedirs(folder, exist_ok=True)
        df = pd.read_csv(folder + '/' + df)
        leads = pd.read_csv(folder + '/' + leads)
        
        # df = pd.DataFrame(gms.scrape_lead_by_industry("New York", "Contractors"))
        # leads = pd.DataFrame()
        # for i in list(df['Names']):
        #     df.insert(self.process_company(i).keys)
        
        combined_leads = pd.merge(leads, df, on='Name', how='left')
    
        # Set file paths
        csv_path = os.path.join(folder, 'new_leads.csv')
        excel_path = os.path.join(folder, 'new_leads.xlsx')
        
        combined_leads.to_csv(csv_path, index=False)
        combined_leads.to_excel(excel_path, index=False)
    
        # if os.path.exists(csv_path):
        #     data = pd.read_csv(csv_path)
        #     data = pd.concat([data, df], axis=0).reset_index(drop=True)
        #     data.to_csv(csv_path, index=False)
        #     data.to_excel(excel_path, index=False)
        # else:
        #     df.to_csv(csv_path, index=False)
        #     df.to_excel(excel_path, index=False)
        
if __name__ == "__main__":
    scraper = AsyncCompanyScraper()
    result = asyncio.run(scraper.process_company("Veritas Capital Fund Management LLC"))
    # result = asyncio.get_event_loop().run_until_complete(scraper.process_company("Born Again Construction LLC"))
    asyncio.run(scraper.save(result))
    asyncio.run(scraper.combine_leads('overview_and_products_services.csv', 'leads_private equity firms_New York.csv'))
    print(result)