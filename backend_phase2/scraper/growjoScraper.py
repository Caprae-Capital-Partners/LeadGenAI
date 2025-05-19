import os
import time
import difflib
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from openai import OpenAI

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
    )
GROWJO_LOGIN_URL = "https://growjo.com/login"
GROWJO_SEARCH_URL = "https://growjo.com/"
LOGIN_EMAIL = os.getenv("GROWJO_EMAIL")
LOGIN_PASSWORD = os.getenv("GROWJO_PASSWORD")


class GrowjoScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver_public = None  # Public browser (no login)
        self.driver_logged_in = None  # Private browser (with login)
        self.wait1 = None
        self.wait2 = None
        self.logged_in = False

        self._setup_browsers()

    def _setup_browsers(self):
        """Initialize two Edge browser instances faster."""
        options = EdgeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # 🚀 Install only once
        driver_path = EdgeChromiumDriverManager().install()
        service = EdgeService(driver_path)

        # 🚀 Launch browsers
        self.driver_public = webdriver.Edge(service=service, options=options)
        self.driver_public.maximize_window()

        self.driver_logged_in = webdriver.Edge(service=service, options=options)
        self.driver_logged_in.maximize_window()

        self.wait_public = WebDriverWait(self.driver_public, 10)
        self.wait_logged_in = WebDriverWait(self.driver_logged_in, 10)

    def login_logged_in_browser(self):
        """Login into Growjo on the logged-in driver, with retry if initial attempt fails."""
        print("[DEBUG] Logging into Growjo (logged-in driver)...")

        max_retries = 3
        retry_delay = 3  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                print(f"[DEBUG] Login attempt {attempt}/{max_retries}")
                self.driver_logged_in.get(GROWJO_LOGIN_URL)
                time.sleep(1.5)

                email_field = self.driver_logged_in.find_element(By.ID, "email")
                password_field = self.driver_logged_in.find_element(By.ID, "password")
                email_field.clear()
                email_field.send_keys(LOGIN_EMAIL)
                password_field.clear()
                password_field.send_keys(LOGIN_PASSWORD)

                form = self.driver_logged_in.find_element(By.TAG_NAME, "form")
                form.submit()

                time.sleep(2)  # Give some time for redirect

                if "/login" not in self.driver_logged_in.current_url:
                    print("[DEBUG] Login successful.")
                    self.logged_in = True
                    return  # Exit on success

                else:
                    print("[WARN] Still on login page. Possibly failed credentials or slow load.")

            except Exception as e:
                print(f"[ERROR] Login attempt {attempt} failed: {e}")

            if attempt < max_retries:
                print(f"[DEBUG] Retrying login after {retry_delay}s...")
                time.sleep(retry_delay)

        print("[ERROR] All login attempts failed.")
        raise Exception("Login failed after multiple attempts.")




    def deepseek_guess_website(self, company_name, street=None, city=None, state=None):
        import re
        import json

        # Build location string from available inputs
        location_parts = [part for part in [street, city, state] if part]
        location_context = ", ".join(location_parts)

        # Create prompt with conditional location info
        prompt = (
            f"You are an AI assistant. Given a company name, guess the most likely website domain (e.g., example.com). "
            f"Only respond with this JSON format:\n"
            f'{{"domain": "..."}}\n\n'
            f"Company name: {company_name}"
        )

        if location_context:
            prompt += f"\nLocation context: {location_context}"

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            text = response.choices[0].message.content.strip()

            # Try parsing JSON
            try:
                parsed = json.loads(text)
                raw_domain = parsed.get("domain", "not found")
            except json.JSONDecodeError:
                print(f"[WARN] DeepSeek returned invalid JSON: {text}. Attempting regex fallback...")
                match = re.search(r'([\w\.-]+\.[a-z]{2,})', text, re.IGNORECASE)
                raw_domain = match.group(1) if match else "not found"

            # Normalize domain (strip protocol and trailing slash)
            website = re.sub(r"^https?://", "", raw_domain).rstrip("/")
            return {"website": website}

        except Exception as e:
            print(f"[ERROR] DeepSeek fallback failed: {e}")
            return {"website": "not found"}


        
    def search_company(self, driver, wait, company_name):
        """
        Search for a company on Growjo and click its link if matched.
        Use similarity score between intended and found company name.
        Retries up to 3x per query variant before trimming.
        """
        try:
            print(f"\n[DEBUG] Searching for company: '{company_name}'")

            intended = company_name.strip().lower()
            words = intended.split()

            while words:
                query = " ".join(words)
                print(f"[DEBUG] Trying search with query: '{query}'")

                search_url = f"https://growjo.com/?query={'%20'.join(query.split())}"
                driver.get(search_url)
                time.sleep(1)

                try:
                    print("[DEBUG] Waiting for at least one company row to load...")
                    wait.until(EC.presence_of_element_located((By.XPATH, "//table//tbody//tr")))
                    print("[DEBUG] Company table and rows loaded ✅")
                except TimeoutException:
                    print(f"[DEBUG] Company table not loaded for '{query}'.")
                    if len(words) <= 1:
                        print(f"[ERROR] Search failed even for single word '{query}'. Stopping.")
                        return False
                    words.pop()
                    continue

                max_retries = 3
                retry_delay = 3  # seconds
                attempt = 0
                similarity = 0.0
                link = None

                while attempt < max_retries:
                    try:
                        company_links = driver.find_elements(
                            By.XPATH, "//table//tbody//a[starts-with(@href, '/company/')]"
                        )
                        if not company_links:
                            print(f"[DEBUG] Attempt {attempt + 1}: No company links found.")
                            break

                        link = company_links[0]
                        href = link.get_attribute("href")
                        if href and "/company/" in href:
                            href_company_part = href.split("/company/")[1]
                            link_full_text = href_company_part.replace("_", " ").lower()
                        else:
                            link_full_text = link.text.strip().lower()

                        similarity = self._calculate_similarity(intended, link_full_text)
                        print(f"[DEBUG] Attempt {attempt + 1}: Result='{link_full_text}' | Similarity={similarity:.2f}")

                        if similarity >= 0.7:
                            print(f"[DEBUG] Accepting result '{link_full_text}' with score {similarity:.2f}")
                            driver.execute_script("arguments[0].click();", link)
                            time.sleep(1)
                            return "/company/" in driver.current_url

                    except Exception as e:
                        print(f"[ERROR] Attempt {attempt + 1} failed: {str(e)}")

                    attempt += 1
                    if attempt < max_retries:
                        time.sleep(retry_delay)

                # After retries exhausted
                print(f"[WARN] All {max_retries} retries failed for query: '{query}'")

                if len(words) <= 1:
                    print(f"[ERROR] No good match after all trims for '{company_name}'.")
                    return False

                print(f"[DEBUG] Trimming query and retrying with fewer words...")
                words.pop()

            print(f"[ERROR] Company '{company_name}' not found after all attempts.")
            return False

        except Exception as e:
            print(f"[ERROR] Unexpected error in search_company: {str(e)}")
            return False

    def _calculate_similarity(self, a: str, b: str) -> float:
        """
        Helper to calculate similarity between two strings using difflib.
        Returns a float between 0 and 1.
        """
        a_clean = a.replace(",", "").replace(".", "").lower()
        b_clean = b.replace(",", "").replace(".", "").lower()
        return difflib.SequenceMatcher(None, a_clean, b_clean).ratio()

    def extract_company_details(self, driver, company_name):
        details = {
            "company": company_name,
            "city": "",
            "state": "",
            "industry": "",
            "website": "",
            "employees": "",
            "revenue": "",
            "specialties": "",
        }
        try:
            # City
            try:
                city_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/city/')]")
                details["city"] = city_elem.text.strip()
            except:
                pass

            # State
            try:
                state_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/state/')]")
                details["state"] = state_elem.text.strip()
            except:
                pass

            # Industry
            try:
                industry_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/industry/')]")
                details["industry"] = industry_elem.text.strip()
            except:
                pass

            # Website
            try:
                website_elem = driver.find_element(
                    By.XPATH, "//a[contains(@target, '_blank') and contains(@href, '//') and img]"
                )
                href = website_elem.get_attribute("href")
                if href:
                    details["website"] = (
                        href.replace("//", "https://") if href.startswith("//") else href
                    )
            except:
                pass

            # Revenue
            try:
                revenue_section = driver.find_element(
                    By.XPATH,
                    "//h2[contains(text(), 'Estimated Revenue & Valuation')]/following-sibling::ul[1]/li",
                )
                if revenue_section:
                    revenue_text = revenue_section.text.strip()
                    print(f"[DEBUG] Raw revenue section text: {revenue_text}")

                    import re

                    match = re.search(r"\$[0-9\.]+[BMK]?", revenue_text)
                    if match:
                        details["revenue"] = match.group(0)
            except:
                pass

            # Employees
            try:
                employee_section = driver.find_element(
                    By.XPATH, "//h2[contains(., 'Employee Data')]/following-sibling::ul[1]/li"
                )
                if employee_section:
                    employee_text = employee_section.text.strip()
                    print(f"[DEBUG] Raw employee section text: {employee_text}")

                    import re

                    match = re.search(r"\b\d+\b", employee_text)
                    if match:
                        details["employees"] = match.group(0)
            except:
                pass

            # Keywords (Specialties)
            try:
                keywords_elem = driver.find_element(
                    By.XPATH, "//strong[contains(text(), 'keywords:')]"
                )
                parent = keywords_elem.find_element(By.XPATH, "..")
                parent_text = parent.text
                if "keywords:" in parent_text:
                    details["specialties"] = parent_text.split("keywords:", 1)[1].strip()
                else:
                    details["specialties"] = ""
            except:
                details["specialties"] = ""

        except Exception as e:
            print(f"[ERROR] Error extracting company details for {company_name}: {str(e)}")

        return details

    def find_decision_maker(self, driver, wait, company_name):
        try:
            print(f"[DEBUG] Looking for decision makers in '{company_name}'...")

            # Step 1: Scroll to bottom to trigger lazy loading
            print("[DEBUG] Scrolling to trigger lazy loading of employees...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Step 2: Wait until at least 5 rows are present
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//h2[contains(., 'People')]/following::table//tbody/tr[5]")
                    )
                )
                print("[DEBUG] People table and at least 5 rows loaded ✅")
            except TimeoutException:
                print(
                    f"[ERROR] People table or enough rows not loaded after scrolling for {company_name}."
                )
                return None

            # Step 3: Locate and parse people
            people_table = driver.find_element(
                By.XPATH, "//h2[contains(., 'People')]/following::table[1]"
            )
            rows = people_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            print(f"[DEBUG] Found {len(rows)} people listed.")

            candidates = []

            def assign_priority(title):
                """Assign decision maker priority based on strict title rules."""
                title = title.lower().replace("&", "and").replace("/", " ")
                words = title.split()
                if not words:
                    return 999
                first_word = words[0]
                if first_word in ["owner", "founder", "president", "director", "founding"]:
                    return 1
                elif first_word in ["co-founder", "cofounder"]:
                    return 2
                elif first_word == "ceo":
                    return 3
                elif first_word == "chief" and len(words) > 1:
                    second_word = words[1]
                    if second_word in [
                        "executive",
                        "product",
                        "marketing",
                        "financial",
                        "sales",
                        "growth",
                        "operating",
                        "audit",
                        "compliance",
                        "information",
                    ]:
                        return 3
                return 999

            for idx, row in enumerate(rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 2:
                    continue

                name_col = cols[0]
                title_col = cols[1]

                try:
                    profile_link_elem = name_col.find_element(
                        By.XPATH, ".//a[contains(@href, '/employee/')]"
                    )
                    href = profile_link_elem.get_attribute("href")
                    name = profile_link_elem.text.strip()
                    raw_title = title_col.text.strip()

                    if not href or not name:
                        continue

                    profile_url = (
                        "https://growjo.com" + href if href.startswith("/employee/") else href
                    )
                    priority = assign_priority(raw_title)

                    candidates.append(
                        {
                            "name": name,
                            "title": raw_title,
                            "profile_url": profile_url,
                            "priority": priority,
                        }
                    )

                    print(f"[DEBUG] Candidate: {name} - {raw_title} (Priority: {priority})")

                except Exception as e:
                    print(f"[ERROR] Could not extract person info: {str(e)}")
                    continue

            # Step 4: Pick best candidate
            if candidates:
                candidates.sort(key=lambda x: x["priority"])
                best_candidate = candidates[0]

                print(
                    f"[DEBUG] Best candidate selected: {best_candidate['name']} - {best_candidate['title']} (Priority: {best_candidate['priority']})"
                )

                return {
                    "name": best_candidate["name"],
                    "title": best_candidate["title"],
                    "profile_url": best_candidate["profile_url"],
                }

            print("[DEBUG] No decision makers found.")
            return None

        except Exception as e:
            print(f"[ERROR] Error finding decision maker: {str(e)}")
            return None

    def scrape_decision_maker_details(self, profile_url, driver):
        try:
            print(f"[DEBUG] Navigating to decision maker profile: {profile_url}")
            driver.get(profile_url)
            time.sleep(2)

            # Click reveal buttons
            reveal_buttons = driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Reveal')] | //a[contains(text(), 'Reveal')]"
            )
            for btn in reveal_buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"[DEBUG] Clicked a reveal button.")
                    time.sleep(3)
                except Exception as e:
                    print(f"[ERROR] Error clicking reveal button: {str(e)}")

            # Now start scraping Email and Phone
            email = None
            phone = None

            try:
                # Find all <a href="/join"> elements after reveal
                join_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/join')]")
                print(f"[DEBUG] Found {len(join_links)} elements with href='/join'")

                for elem in join_links:
                    text = elem.text.strip()
                    print(f"[DEBUG] join_link text: '{text}'")

                    if "@" in text and "." in text and not email:
                        email = text
                    elif text.isdigit() and len(text) >= 8 and not phone:
                        phone = text

                if not email:
                    print("[DEBUG] Email not found after reveal.")
                if not phone:
                    print("[DEBUG] Phone number not found after reveal.")

            except Exception as e:
                print(f"[ERROR] Error extracting email/phone: {str(e)}")

            # Scrape LinkedIn link separately
            linkedin_url = None
            try:
                linkedin_links = driver.find_elements(
                    By.XPATH, "//a[contains(@href, 'linkedin.com')]"
                )
                if linkedin_links:
                    linkedin_url = linkedin_links[0].get_attribute("href")
            except Exception as e:
                print(f"[ERROR] Error extracting LinkedIn URL: {str(e)}")

            return {
                "email": email or "not found",
                "phone": phone or "not found",
                "linkedin": linkedin_url or "not found",
            }

        except Exception as e:
            print(f"[ERROR] Error scraping decision maker details: {str(e)}")
            return {
                "email": "not found",
                "phone": "not found",
                "linkedin": "not found",
            }

    def scrape_full_pipeline(self, company_name):
        """Master method to run full Growjo scraping pipeline, with DeepSeek fallback if company not found."""
        try:
            # Step 1: Try Growjo
            found = self.search_company(self.driver_public, self.wait_public, company_name)
            if not found:
                print("[DEBUG] Growjo failed to find company — falling back to DeepSeek...")
                inferred = self.deepseek_guess_website(company_name)
                return {
                    "company_name": company_name,
                    "company_website": inferred.get("website", "not found"),
                    "revenue": "not found",
                    "location": "not found",
                    "industry": "not found",
                    "interests": "not found",
                    "employee_count": "not found",
                    "decider_name": "not found",
                    "decider_title": "not found",
                    "decider_email": "not found",
                    "decider_phone": "not found",
                    "decider_linkedin": "not found"
                }

            # Step 2: Scrape company details
            company_info = self.extract_company_details(self.driver_public, company_name)
            decision_maker = self.find_decision_maker(self.driver_public, self.wait_public, company_name)

            # Step 3: If decider found, get sensitive info
            sensitive_info = {
                "email": "not found",
                "phone": "not found",
                "linkedin": "not found"
            }
            if decision_maker:
                profile_url = decision_maker["profile_url"]
                if not self.logged_in:
                    self.login_logged_in_browser()
                sensitive_info = self.scrape_decision_maker_details(profile_url, self.driver_logged_in)

            # Step 4: Return final combined result
            return {
                "company_name": company_info.get("company", company_name),
                "company_website": company_info.get("website", "not found"),
                "revenue": company_info.get("revenue", "not found"),
                "location": ", ".join(filter(None, [company_info.get("city", ""), company_info.get("state", "")])) or "not found",
                "industry": company_info.get("industry", "not found"),
                "interests": company_info.get("specialties", "not found"),
                "employee_count": company_info.get("employees", "not found"),
                "decider_name": decision_maker.get("name", "not found") if decision_maker else "not found",
                "decider_title": decision_maker.get("title", "not found") if decision_maker else "not found",
                "decider_email": sensitive_info.get("email", "not found"),
                "decider_phone": sensitive_info.get("phone", "not found"),
                "decider_linkedin": sensitive_info.get("linkedin", "not found")
            }

        except Exception as e:
            print(f"[ERROR] Full pipeline error: {str(e)}")
            return {"error": str(e)}


    
    def close(self):
        """Close both browser instances."""
        try:
            self.driver_public.quit()
            self.driver_logged_in.quit()
        except Exception as e:
            print(f"[ERROR] Closing drivers error: {str(e)}")
