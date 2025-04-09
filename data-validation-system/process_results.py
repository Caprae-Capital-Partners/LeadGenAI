# process_results.py
"""
Utility script to analyze validation results and generate reports
"""
import os
import sys
import json
import pandas as pd
import argparse
import matplotlib.pyplot as plt
from datetime import datetime

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Process validation results')
    parser.add_argument('--input', required=True, help='Path to validated CSV file')
    parser.add_argument('--summary', required=False, help='Path to validation summary JSON')
    parser.add_argument('--report', required=False, help='Path to output HTML report')
    parser.add_argument('--charts', required=False, help='Directory to save charts')
    return parser.parse_args()

def generate_confidence_chart(df, output_dir):
    """Generate confidence distribution chart"""
    plt.figure(figsize=(10, 6))
    
    # Find confidence columns
    confidence_cols = [col for col in df.columns if col.endswith('_confidence')]
    
    # Create data for chart
    data = {}
    for col in confidence_cols:
        data_type = col.replace('_confidence', '')
        values = df[col].dropna()
        if len(values) > 0:
            data[data_type] = {
                'high': sum(values >= 0.8) / len(values) * 100,
                'medium': sum((values >= 0.6) & (values < 0.8)) / len(values) * 100,
                'low': sum((values >= 0.3) & (values < 0.6)) / len(values) * 100,
                'very_low': sum(values < 0.3) / len(values) * 100
            }
    
    # Create grouped bar chart
    data_types = list(data.keys())
    x = range(len(data_types))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot bars for each confidence level
    rects1 = ax.bar([i - width*1.5 for i in x], [data[dt]['high'] for dt in data_types], width, label='High (≥0.8)')
    rects2 = ax.bar([i - width*0.5 for i in x], [data[dt]['medium'] for dt in data_types], width, label='Medium (0.6-0.8)')
    rects3 = ax.bar([i + width*0.5 for i in x], [data[dt]['low'] for dt in data_types], width, label='Low (0.3-0.6)')
    rects4 = ax.bar([i + width*1.5 for i in x], [data[dt]['very_low'] for dt in data_types], width, label='Very Low (<0.3)')
    
    # Add labels and title
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Confidence Score Distribution by Data Type')
    ax.set_xticks(x)
    ax.set_xticklabels([dt.replace('_', ' ').title() for dt in data_types])
    ax.legend()
    
    # Add percentage labels on bars
    def add_labels(rects):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
    
    add_labels(rects1)
    add_labels(rects2)
    add_labels(rects3)
    add_labels(rects4)
    
    plt.tight_layout()
    
    # Save chart
    chart_path = os.path.join(output_dir, 'confidence_distribution.png')
    plt.savefig(chart_path)
    
    return chart_path

def generate_html_report(df, summary_path, charts_dir):
    """Generate HTML report from validation results"""
    # Create report directory if needed
    os.makedirs(charts_dir, exist_ok=True)
    
    # Generate charts
    confidence_chart = generate_confidence_chart(df, charts_dir)
    
    # Load summary if available
    summary = None
    if summary_path and os.path.exists(summary_path):
        with open(summary_path, 'r') as f:
            summary = json.load(f)
    
    # Prepare HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Validation Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; padding: 20px; }}
            .chart-container {{ text-align: center; margin: 20px 0; }}
            .chart {{ max-width: 100%; height: auto; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ display: flex; flex-wrap: wrap; gap: 20px; }}
            .summary-card {{ flex: 1; min-width: 250px; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
            .confidence-high {{ color: green; }}
            .confidence-medium {{ color: orange; }}
            .confidence-low {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Data Validation Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="card">
                <h2>Overview</h2>
                <div class="summary">
                    <div class="summary-card">
                        <h3>Records</h3>
                        <p><strong>Total records:</strong> {len(df)}</p>
    """
    
    if summary:
        # Add summary statistics
        html += f"""
                    </div>
                    <div class="summary-card">
                        <h3>Overall Quality</h3>
        """
        
        if 'overall_quality' in summary:
            avg_conf = summary['overall_quality'].get('average_confidence', 0)
            conf_class = 'confidence-high' if avg_conf >= 0.8 else 'confidence-medium' if avg_conf >= 0.6 else 'confidence-low'
            
            html += f"""
                        <p><strong>Average confidence:</strong> <span class="{conf_class}">{avg_conf:.2f}</span></p>
                        <p><strong>High quality data:</strong> {summary['overall_quality'].get('high_quality_percentage', 0):.1f}%</p>
                        <p><strong>Medium quality data:</strong> {summary['overall_quality'].get('medium_quality_percentage', 0):.1f}%</p>
                        <p><strong>Low quality data:</strong> {summary['overall_quality'].get('low_quality_percentage', 0):.1f}%</p>
            """
    
    html += """
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Confidence Distribution</h2>
                <div class="chart-container">
                    <img src="confidence_distribution.png" alt="Confidence Distribution Chart" class="chart">
                </div>
            </div>
    """
    
    # Add data type specific sections
    if summary and 'data_types' in summary:
        for data_type, data in summary['data_types'].items():
            html += f"""
            <div class="card">
                <h2>{data_type.replace('_', ' ').title()} Validation</h2>
                <p><strong>Records validated:</strong> {data.get('records_validated', 0)}</p>
                <p><strong>Average confidence:</strong> {data.get('average_confidence', 0):.2f}</p>
                
                <h3>Common Flags</h3>
                <ul>
            """
            
            if 'common_flags' in data:
                for flag_info in data['common_flags']:
                    html += f"""
                    <li>{flag_info['flag']} ({flag_info['count']} occurrences)</li>
                    """
            
            html += """
                </ul>
            </div>
            """
    
    # Add sample data section
    html += """
            <div class="card">
                <h2>Sample Data</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
    """
    
    # Sample columns to show (original and validation columns)
    display_columns = ['Business Name', 'Company']
    validation_columns = [col for col in df.columns if col.endswith('_confidence') or col.endswith('_flags')]
    display_columns.extend(validation_columns[:6])  # Limit to 6 validation columns
    
    # Add headers
    for col in display_columns:
        if col in df.columns:
            html += f"<th>{col}</th>"
    
    html += """
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Add sample data rows (limit to 10)
    for _, row in df.head(10).iterrows():
        html += "<tr>"
        for col in display_columns:
            if col in df.columns:
                value = row.get(col, '')
                if col.endswith('_confidence'):
                    conf_class = 'confidence-high' if value >= 0.8 else 'confidence-medium' if value >= 0.6 else 'confidence-low'
                    html += f'<td><span class="{conf_class}">{value:.2f}</span></td>'
                else:
                    html += f"<td>{value}</td>"
        html += "</tr>"
    
    html += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card">
                <h2>Recommendations</h2>
                <ul>
    """
    
    # Add recommendations based on results
    low_confidence_cols = []
    for col in df.columns:
        if col.endswith('_confidence'):
            values = df[col].dropna()
            if len(values) > 0 and values.mean() < 0.6:
                low_confidence_cols.append(col.replace('_confidence', ''))
    
    if low_confidence_cols:
        html += f"""
                    <li><strong>Verify low confidence data:</strong> The following data types have low average confidence and should be manually verified: {', '.join(low_confidence_cols)}</li>
        """
    
    html += """
                    <li><strong>Address common flags:</strong> Review and address the most common flags identified in the validation process.</li>
                    <li><strong>Enhance data collection:</strong> Consider improving data collection methods for types with consistently low confidence scores.</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def main():
    """Main function to process validation results"""
    args = parse_args()
    
    try:
        # Read validation results
        df = pd.read_csv(args.input)
        print(f"Loaded validation results from {args.input} ({len(df)} records)")
        
        # Create charts directory if needed
        charts_dir = args.charts or 'charts'
        os.makedirs(charts_dir, exist_ok=True)
        
        # Generate HTML report
        html_report = generate_html_report(df, args.summary, charts_dir)
        
        # Save HTML report
        report_path = args.report or 'validation_report.html'
        with open(report_path, 'w') as f:
            f.write(html_report)
        
        print(f"Generated HTML report at {report_path}")
        print(f"Generated charts in {charts_dir}")
        
    except Exception as e:
        print(f"Error processing results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()