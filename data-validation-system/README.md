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