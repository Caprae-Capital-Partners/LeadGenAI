# utils.py
import os
import json
import pandas as pd
from datetime import datetime

def save_validation_summary(df, output_file):
    """
    Generate and save a summary of validation results
    
    Args:
        df: DataFrame with validation results
        output_file: Path to save summary JSON
    """
    # Create summary object
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_records': len(df),
        'data_types': {}
    }
    
    # Process each data type
    for data_type in ['revenue', 'employee_count']:
        confidence_col = f'{data_type}_confidence'
        flags_col = f'{data_type}_flags'
        
        if confidence_col in df.columns:
            # Calculate confidence metrics
            confidence_values = df[confidence_col].dropna()
            
            data_type_summary = {
                'records_validated': len(confidence_values),
                'average_confidence': confidence_values.mean() if len(confidence_values) > 0 else 0,
                'high_confidence': sum(confidence_values >= 0.8),
                'medium_confidence': sum((confidence_values >= 0.6) & (confidence_values < 0.8)),
                'low_confidence': sum((confidence_values >= 0.3) & (confidence_values < 0.6)),
                'very_low_confidence': sum(confidence_values < 0.3),
                'common_flags': _get_common_flags(df, flags_col)
            }
            
            summary['data_types'][data_type] = data_type_summary
    
    # Add decision maker summaries
    decision_maker_counts = 0
    decision_maker_confidences = []
    
    for i in range(1, 4):
        dm_conf_col = f'decision_maker_{i}_confidence'
        if dm_conf_col in df.columns:
            confidence_values = df[dm_conf_col].dropna()
            decision_maker_counts += len(confidence_values)
            decision_maker_confidences.extend(confidence_values.tolist())
    
    if decision_maker_counts > 0:
        summary['data_types']['decision_makers'] = {
            'records_validated': decision_maker_counts,
            'average_confidence': sum(decision_maker_confidences) / len(decision_maker_confidences) if decision_maker_confidences else 0
        }
    
    # Calculate overall data quality
    confidence_columns = [col for col in df.columns if col.endswith('_confidence')]
    if confidence_columns:
        all_confidences = []
        for col in confidence_columns:
            all_confidences.extend(df[col].dropna().tolist())
        
        if all_confidences:
            summary['overall_quality'] = {
                'average_confidence': sum(all_confidences) / len(all_confidences),
                'high_quality_percentage': sum(c >= 0.8 for c in all_confidences) / len(all_confidences) * 100,
                'medium_quality_percentage': sum(0.6 <= c < 0.8 for c in all_confidences) / len(all_confidences) * 100,
                'low_quality_percentage': sum(c < 0.6 for c in all_confidences) / len(all_confidences) * 100
            }
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def _get_common_flags(df, flags_column):
    """Extract most common flags from JSON-encoded flags column"""
    if flags_column not in df.columns:
        return []
    
    all_flags = []
    
    for flags_json in df[flags_column].dropna():
        try:
            flags = json.loads(flags_json)
            all_flags.extend(flags)
        except:
            pass
    
    # Count occurrences of each flag
    flag_counts = {}
    for flag in all_flags:
        flag_counts[flag] = flag_counts.get(flag, 0) + 1
    
    # Sort by frequency
    sorted_flags = sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top 5 most common flags
    return [{"flag": flag, "count": count} for flag, count in sorted_flags[:5]]

def merge_validation_results(original_file, validation_file, output_file):
    """
    Merge original data with validation results
    
    Args:
        original_file: Original data CSV
        validation_file: Validation results CSV
        output_file: Output merged CSV
    """
    # Read files
    original_df = pd.read_csv(original_file)
    validation_df = pd.read_csv(validation_file)
    
    # Create company name mapping
    validation_company_col = 'Business Name' if 'Business Name' in validation_df.columns else 'Company'
    original_company_col = 'Business Name' if 'Business Name' in original_df.columns else 'Company'
    
    # Get validation columns (those ending with _confidence, _explanation, _flags)
    validation_cols = [col for col in validation_df.columns if 
                      col.endswith('_confidence') or 
                      col.endswith('_explanation') or 
                      col.endswith('_flags')]
    
    # Add validation info columns
    validation_cols.append('validation_error')
    
    # Create a subset DF with just the columns we need
    validation_subset = validation_df[[validation_company_col] + 
                                    [col for col in validation_cols if col in validation_df.columns]]
    
    # Merge datasets
    merged_df = pd.merge(
        original_df,
        validation_subset,
        left_on=original_company_col,
        right_on=validation_company_col,
        how='left'
    )
    
    # Save to file
    merged_df.to_csv(output_file, index=False)
    
    return merged_df