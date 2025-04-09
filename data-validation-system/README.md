# Business Data Validation System

This system uses ChatGPT Plus to validate business lead data, including revenue figures, employee counts, and decision maker information. It provides confidence scores, explanatory reasoning, and flags potential issues with the data.

## Features

- Validates business data using ChatGPT's contextual understanding
- Works with a regular ChatGPT Plus subscription ($20/month) - no API needed
- Respects rate limits automatically
- Provides confidence scores for each data point
- Generates detailed explanations for validation decisions
- Flags potential issues or inconsistencies
- Processes data in batches and supports resuming interrupted validations
- Generates summary reports with validation statistics

## Setup

1. Install the required dependencies:

```bash
pip install -r config/requirements.txt
```

2. Set up Chrome/Chromium browser:
   - Make sure you have Chrome or Chromium installed on your system
   - Run the Chrome setup script to install the appropriate WebDriver:
   ```bash
   python chrome_setup.py
   ```

3. Create a `.env` file in the project root with your ChatGPT credentials:
   ```
   CHATGPT_EMAIL=your_email@example.com
   CHATGPT_PASSWORD=your_password
   BATCH_SIZE=5
   BATCH_MODE=single
   USE_HEADLESS=true
   ```

## Usage

### Running with the helper script

The easiest way to run the system is with the provided shell script:

```bash
# Basic usage with default parameters:
./run.sh

# With custom input/output files:
./run.sh data/input/sample_leads.csv data/output/validated_leads.csv
```

### Running directly with Python

```bash
python main.py --input data/input/sample_leads.csv \
               --output data/output/validated_leads.csv \
               --email your_email@example.com \
               --password your_password \
               --batch-size 5 \
               --summary data/output/validation_summary.json
```

### Input Format

The system expects a CSV file with business information. At minimum, it should include:
- Business Name or Company column
- Any additional data you want to validate (revenue, employee count, etc.)

Example input format:
```
Business Name,Company,Industry,Company Size,estimated_revenue,source
Acme Corp,,Technology,100-500 employees,$25M,crunchbase
,TechSolutions Inc,Software,51-200 employees,$8.5M,zoominfo
```

### Output & Reports

After processing, the system produces:
1. A validated CSV file with confidence scores and explanations
2. An optional JSON summary file with validation statistics
3. A log file with processing details
4. Visualization charts when using the report generator

To generate an HTML report from validation results:

```bash
python main.py --input data/input/sample_leads.csv --output data/output/validated_leads.csv --email vanessamae23@gmail.com --password your-password
```

## Additional Components

### Revenue Scraper

The system includes a simple web scraper to fetch company revenue data:

```python
from revenueScraper import get_company_revenue

result = get_company_revenue("Example Company")
print(result)
```

## Troubleshooting

- If you encounter login issues with ChatGPT, try running without headless mode by setting `USE_HEADLESS=false` in your `.env` file.
- For CSV parsing errors, check that your input file doesn't have extra commas or inconsistent quote characters.
- If rate limiting occurs, the system will automatically pause and resume - you can adjust the batch size for better control.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.