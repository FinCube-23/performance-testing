#!/usr/bin/env python3
"""
Onchain Sync Success Rate Analysis
===================================
This script analyzes the success rates of onchain synchronization for an audit trail service
by comparing confirmation_source and transaction_confirmation_trace metrics.

Success Criteria:
- confirmation_source: Success if NOT 'pending_source'
- transaction_confirmation_trace: Success if NOT null

Author: Performance Testing Team
Date: October 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set style for professional research-quality plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16


class OnchainSyncAnalyzer:
    """Analyzer for onchain synchronization performance metrics."""
    
    def __init__(self, data_path: str):
        """Initialize the analyzer with transaction data."""
        self.data_path = Path(data_path)
        self.df = None
        self.results = {}
    
    @staticmethod
    def format_source_label(source: str) -> str:
        """Format confirmation source labels for display in visualizations."""
        label_map = {
            'graph': 'Successful',
            'pending_source': 'Pending'
        }
        return label_map.get(source, source)
        
    def load_data(self) -> pd.DataFrame:
        """Load and preprocess the transaction data."""
        print(f"Loading data from {self.data_path}...")
        self.df = pd.read_csv(self.data_path)
        
        # Convert timestamps
        self.df['created_at'] = pd.to_datetime(self.df['created_at'])
        self.df['updated_at'] = pd.to_datetime(self.df['updated_at'])
        
        # Calculate sync duration
        self.df['sync_duration_seconds'] = (
            self.df['updated_at'] - self.df['created_at']
        ).dt.total_seconds()
        
        print(f"Loaded {len(self.df)} transactions")
        print(f"Date range: {self.df['created_at'].min()} to {self.df['updated_at'].max()}")
        
        return self.df
    
    def calculate_success_metrics(self) -> Dict:
        """Calculate success metrics for both confirmation methods."""
        # Confirmation Source Success
        self.df['source_success'] = self.df['confirmation_source'] != 'pending_source'
        
        # Transaction Trace Success
        self.df['trace_success'] = self.df['transaction_confirmation_trace'].notna()
        
        # Overall Success (both metrics successful)
        self.df['both_success'] = self.df['source_success'] & self.df['trace_success']
        
        # Calculate metrics
        total = len(self.df)
        source_success_count = self.df['source_success'].sum()
        trace_success_count = self.df['trace_success'].sum()
        both_success_count = self.df['both_success'].sum()
        
        self.results = {
            'total_transactions': total,
            'confirmation_source': {
                'successful': int(source_success_count),
                'failed': int(total - source_success_count),
                'success_rate': float(source_success_count / total * 100)
            },
            'transaction_confirmation_trace': {
                'successful': int(trace_success_count),
                'failed': int(total - trace_success_count),
                'success_rate': float(trace_success_count / total * 100)
            },
            'both_metrics': {
                'successful': int(both_success_count),
                'failed': int(total - both_success_count),
                'success_rate': float(both_success_count / total * 100)
            }
        }
        
        # Source distribution
        source_dist = self.df['confirmation_source'].value_counts()
        self.results['source_distribution'] = source_dist.to_dict()
        
        # Status distribution
        status_dist = self.df['trx_status'].value_counts()
        self.results['status_distribution'] = status_dist.to_dict()
        
        return self.results
    
    def print_summary(self):
        """Print a detailed summary of the analysis."""
        print("\n" + "="*80)
        print("ONCHAIN SYNC SUCCESS RATE ANALYSIS")
        print("="*80)
        
        print(f"\nTotal Transactions Analyzed: {self.results['total_transactions']}")
        
        print("\n📊 CONFIRMATION SOURCE SUCCESS")
        print("-" * 40)
        cs = self.results['confirmation_source']
        print(f"  ✓ Successful: {cs['successful']} ({cs['success_rate']:.2f}%)")
        print(f"  ✗ Failed:     {cs['failed']} ({100-cs['success_rate']:.2f}%)")
        
        print("\n📊 TRANSACTION CONFIRMATION TRACE SUCCESS")
        print("-" * 40)
        tc = self.results['transaction_confirmation_trace']
        print(f"  ✓ Successful: {tc['successful']} ({tc['success_rate']:.2f}%)")
        print(f"  ✗ Failed:     {tc['failed']} ({100-tc['success_rate']:.2f}%)")
        
        print("\n📊 COMBINED SUCCESS (Both Metrics)")
        print("-" * 40)
        both = self.results['both_metrics']
        print(f"  ✓ Successful: {both['successful']} ({both['success_rate']:.2f}%)")
        print(f"  ✗ Failed:     {both['failed']} ({100-both['success_rate']:.2f}%)")
        
        print("\n📋 SOURCE DISTRIBUTION")
        print("-" * 40)
        for source, count in self.results['source_distribution'].items():
            print(f"  {source}: {count}")
        
        print("\n⏱️  SYNC DURATION STATISTICS")
        print("-" * 40)
        successful_syncs = self.df[self.df['both_success']]
        if len(successful_syncs) > 0:
            print(f"  Mean:   {successful_syncs['sync_duration_seconds'].mean():.2f} seconds")
            print(f"  Median: {successful_syncs['sync_duration_seconds'].median():.2f} seconds")
            print(f"  Min:    {successful_syncs['sync_duration_seconds'].min():.2f} seconds")
            print(f"  Max:    {successful_syncs['sync_duration_seconds'].max():.2f} seconds")
            print(f"  Std:    {successful_syncs['sync_duration_seconds'].std():.2f} seconds")
        
        print("\n" + "="*80)
    
    def plot_success_comparison(self, output_dir: Path):
        """Create comprehensive success rate comparison visualizations."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Onchain Sync Success Rate Analysis', fontsize=18, fontweight='bold', y=0.995)
        
        # 1. Bar Chart: Success Rate Comparison
        ax1 = axes[0, 0]
        metrics = ['Confirmation\nSource', 'Transaction\nConfirmation Trace', 'Both\nMetrics']
        success_rates = [
            self.results['confirmation_source']['success_rate'],
            self.results['transaction_confirmation_trace']['success_rate'],
            self.results['both_metrics']['success_rate']
        ]
        colors = ['#2ecc71', '#3498db', '#9b59b6']
        
        bars = ax1.bar(metrics, success_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Success Rate (%)', fontweight='bold')
        ax1.set_title('Success Rate Comparison', fontweight='bold', pad=15)
        ax1.set_ylim(0, 105)
        ax1.axhline(y=100, color='red', linestyle='--', alpha=0.3, label='100% Target')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        ax1.legend()
        
        # 2. Pie Chart: Confirmation Source Distribution
        ax2 = axes[0, 1]
        source_labels = list(self.results['source_distribution'].keys())
        source_values = list(self.results['source_distribution'].values())
        # Format labels for display
        display_labels = [self.format_source_label(label) for label in source_labels]
        colors_pie = sns.color_palette('Set2', len(source_labels))
        
        wedges, texts, autotexts = ax2.pie(source_values, labels=display_labels, autopct='%1.1f%%',
                                            colors=colors_pie, startangle=90,
                                            explode=[0.05 if label == 'pending_source' else 0 for label in source_labels])
        ax2.set_title('Confirmation Source Distribution', fontweight='bold', pad=15)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # 3. Stacked Bar: Success vs Failure Breakdown
        ax3 = axes[1, 0]
        categories = ['Confirmation\nSource', 'Transaction\nConfirmation Trace', 'Both\nMetrics']
        successful = [
            self.results['confirmation_source']['successful'],
            self.results['transaction_confirmation_trace']['successful'],
            self.results['both_metrics']['successful']
        ]
        failed = [
            self.results['confirmation_source']['failed'],
            self.results['transaction_confirmation_trace']['failed'],
            self.results['both_metrics']['failed']
        ]
        
        x = np.arange(len(categories))
        width = 0.6
        
        p1 = ax3.bar(x, successful, width, label='Successful', color='#2ecc71', alpha=0.8, edgecolor='black')
        p2 = ax3.bar(x, failed, width, bottom=successful, label='Failed', color='#e74c3c', alpha=0.8, edgecolor='black')
        
        ax3.set_ylabel('Number of Transactions', fontweight='bold')
        ax3.set_title('Success vs Failure Breakdown', fontweight='bold', pad=15)
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.legend(loc='upper right')
        ax3.grid(axis='y', alpha=0.3)
        
        # Add count labels
        for i, (succ, fail) in enumerate(zip(successful, failed)):
            ax3.text(i, succ/2, str(succ), ha='center', va='center', fontweight='bold', color='white')
            ax3.text(i, succ + fail/2, str(fail), ha='center', va='center', fontweight='bold', color='white')
        
        # 4. Horizontal Bar: Side-by-Side Comparison
        ax4 = axes[1, 1]
        metrics_detailed = [
            'Confirmation Source\n(Successful)',
            'Transaction Trace\n(Not null)',
            'Combined\n(Both successful)'
        ]
        
        y_pos = np.arange(len(metrics_detailed))
        success_counts = [
            self.results['confirmation_source']['successful'],
            self.results['transaction_confirmation_trace']['successful'],
            self.results['both_metrics']['successful']
        ]
        
        bars = ax4.barh(y_pos, success_counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(metrics_detailed)
        ax4.set_xlabel('Number of Successful Transactions', fontweight='bold')
        ax4.set_title('Successful Transactions by Metric', fontweight='bold', pad=15)
        ax4.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, success_counts)):
            width = bar.get_width()
            ax4.text(width + 1, bar.get_y() + bar.get_height()/2.,
                    f'{count}\n({count/self.results["total_transactions"]*100:.1f}%)',
                    ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        output_path = output_dir / 'success_rate_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_sync_duration_analysis(self, output_dir: Path):
        """Analyze and visualize sync duration patterns."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Sync Duration Performance Analysis', fontsize=18, fontweight='bold', y=0.995)
        
        successful_syncs = self.df[self.df['both_success']]
        failed_syncs = self.df[~self.df['both_success']]
        
        # 1. Distribution of Sync Duration (Successful)
        ax1 = axes[0, 0]
        if len(successful_syncs) > 0:
            ax1.hist(successful_syncs['sync_duration_seconds'], bins=30, color='#2ecc71', 
                    alpha=0.7, edgecolor='black')
            ax1.axvline(successful_syncs['sync_duration_seconds'].mean(), color='red', 
                       linestyle='--', linewidth=2, label=f'Mean: {successful_syncs["sync_duration_seconds"].mean():.2f}s')
            ax1.axvline(successful_syncs['sync_duration_seconds'].median(), color='blue', 
                       linestyle='--', linewidth=2, label=f'Median: {successful_syncs["sync_duration_seconds"].median():.2f}s')
        ax1.set_xlabel('Sync Duration (seconds)', fontweight='bold')
        ax1.set_ylabel('Frequency', fontweight='bold')
        ax1.set_title('Distribution of Sync Duration (Successful Syncs)', fontweight='bold', pad=15)
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # 2. Box Plot: Success vs Failure
        ax2 = axes[0, 1]
        data_to_plot = []
        labels = []
        if len(successful_syncs) > 0:
            data_to_plot.append(successful_syncs['sync_duration_seconds'])
            labels.append('Successful')
        if len(failed_syncs) > 0:
            data_to_plot.append(failed_syncs['sync_duration_seconds'])
            labels.append('Failed')
        
        if data_to_plot:
            bp = ax2.boxplot(data_to_plot, labels=labels, patch_artist=True,
                            boxprops=dict(facecolor='#3498db', alpha=0.7),
                            medianprops=dict(color='red', linewidth=2))
            ax2.set_ylabel('Sync Duration (seconds)', fontweight='bold')
            ax2.set_title('Sync Duration: Successful vs Failed', fontweight='bold', pad=15)
            ax2.grid(axis='y', alpha=0.3)
        
        # 3. Timeline: Sync Duration Over Time
        ax3 = axes[1, 0]
        if len(successful_syncs) > 0:
            ax3.scatter(successful_syncs['created_at'], successful_syncs['sync_duration_seconds'],
                       alpha=0.6, color='#2ecc71', label='Successful', s=50)
        if len(failed_syncs) > 0:
            ax3.scatter(failed_syncs['created_at'], failed_syncs['sync_duration_seconds'],
                       alpha=0.6, color='#e74c3c', label='Failed', s=50, marker='x')
        ax3.set_xlabel('Transaction Created At', fontweight='bold')
        ax3.set_ylabel('Sync Duration (seconds)', fontweight='bold')
        ax3.set_title('Sync Duration Timeline', fontweight='bold', pad=15)
        ax3.legend()
        ax3.grid(alpha=0.3)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 4. Cumulative Distribution
        ax4 = axes[1, 1]
        if len(successful_syncs) > 0:
            sorted_durations = np.sort(successful_syncs['sync_duration_seconds'])
            cumulative = np.arange(1, len(sorted_durations) + 1) / len(sorted_durations) * 100
            ax4.plot(sorted_durations, cumulative, color='#2ecc71', linewidth=2)
            ax4.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50th Percentile')
            ax4.axhline(y=95, color='orange', linestyle='--', alpha=0.5, label='95th Percentile')
            ax4.axhline(y=99, color='purple', linestyle='--', alpha=0.5, label='99th Percentile')
        ax4.set_xlabel('Sync Duration (seconds)', fontweight='bold')
        ax4.set_ylabel('Cumulative Percentage (%)', fontweight='bold')
        ax4.set_title('Cumulative Distribution of Sync Duration', fontweight='bold', pad=15)
        ax4.legend()
        ax4.grid(alpha=0.3)
        
        plt.tight_layout()
        output_path = output_dir / 'sync_duration_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_trace_analysis(self, output_dir: Path):
        """Analyze transaction confirmation trace patterns."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Transaction Confirmation Trace Analysis', fontsize=18, fontweight='bold', y=0.995)
        
        # Parse trace data
        trace_services = []
        trace_counts = {}
        
        for idx, row in self.df.iterrows():
            if pd.notna(row['transaction_confirmation_trace']):
                try:
                    trace_data = json.loads(row['transaction_confirmation_trace'])
                    for service_entry in trace_data:
                        service_name = service_entry.get('service', 'unknown')
                        trace_services.append(service_name)
                        trace_counts[service_name] = trace_counts.get(service_name, 0) + 1
                except:
                    pass
        
        # 1. Service Distribution
        ax1 = axes[0, 0]
        if trace_counts:
            services = list(trace_counts.keys())
            counts = list(trace_counts.values())
            bars = ax1.bar(services, counts, color=sns.color_palette('Set2', len(services)), 
                          alpha=0.8, edgecolor='black', linewidth=1.5)
            ax1.set_ylabel('Occurrences', fontweight='bold')
            ax1.set_title('Services in Transaction Confirmation Trace', fontweight='bold', pad=15)
            ax1.grid(axis='y', alpha=0.3)
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add value labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        str(count), ha='center', va='bottom', fontweight='bold')
        
        # 2. Trace Completeness
        ax2 = axes[0, 1]
        trace_lengths = []
        for idx, row in self.df.iterrows():
            if pd.notna(row['transaction_confirmation_trace']):
                try:
                    trace_data = json.loads(row['transaction_confirmation_trace'])
                    trace_lengths.append(len(trace_data))
                except:
                    trace_lengths.append(0)
            else:
                trace_lengths.append(0)
        
        if trace_lengths:
            length_counts = pd.Series(trace_lengths).value_counts().sort_index()
            ax2.bar(length_counts.index, length_counts.values, color='#3498db', 
                   alpha=0.8, edgecolor='black', linewidth=1.5)
            ax2.set_xlabel('Number of Services in Trace', fontweight='bold')
            ax2.set_ylabel('Number of Transactions', fontweight='bold')
            ax2.set_title('Trace Completeness Distribution', fontweight='bold', pad=15)
            ax2.grid(axis='y', alpha=0.3)
        
        # 3. Success by Trace ID
        ax3 = axes[1, 0]
        trace_id_success = self.df.groupby('trace_id')['both_success'].agg(['sum', 'count'])
        trace_id_success = trace_id_success[trace_id_success['count'] > 0].sort_values('sum', ascending=False).head(10)
        
        if len(trace_id_success) > 0:
            bars = ax3.barh(range(len(trace_id_success)), trace_id_success['sum'], 
                           color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
            ax3.set_yticks(range(len(trace_id_success)))
            ax3.set_yticklabels([f"{tid[:8]}..." if pd.notna(tid) else "None" 
                                 for tid in trace_id_success.index])
            ax3.set_xlabel('Successful Syncs', fontweight='bold')
            ax3.set_title('Top 10 Trace IDs by Success Count', fontweight='bold', pad=15)
            ax3.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for i, (bar, val) in enumerate(zip(bars, trace_id_success['sum'])):
                width = bar.get_width()
                ax3.text(width + 0.3, bar.get_y() + bar.get_height()/2.,
                        f'{int(val)}', ha='left', va='center', fontweight='bold')
        
        # 4. Status Distribution
        ax4 = axes[1, 1]
        status_success = self.df.groupby('trx_status')['both_success'].agg(['sum', 'count'])
        
        x = np.arange(len(status_success))
        width = 0.35
        
        p1 = ax4.bar(x - width/2, status_success['sum'], width, label='Successful', 
                    color='#2ecc71', alpha=0.8, edgecolor='black')
        p2 = ax4.bar(x + width/2, status_success['count'] - status_success['sum'], 
                    width, label='Failed', color='#e74c3c', alpha=0.8, edgecolor='black')
        
        ax4.set_ylabel('Number of Transactions', fontweight='bold')
        ax4.set_xlabel('Transaction Status', fontweight='bold')
        ax4.set_title('Success by Transaction Status', fontweight='bold', pad=15)
        ax4.set_xticks(x)
        ax4.set_xticklabels(status_success.index)
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_path = output_dir / 'trace_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def plot_advanced_metrics(self, output_dir: Path):
        """Create advanced analytical visualizations."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Advanced Performance Metrics', fontsize=18, fontweight='bold', y=0.995)
        
        # 1. Success Rate by Source Type
        ax1 = axes[0, 0]
        source_success = self.df.groupby('confirmation_source')['both_success'].agg(['sum', 'count'])
        source_success['rate'] = source_success['sum'] / source_success['count'] * 100
        
        # Format source labels for display
        display_labels = [self.format_source_label(src) for src in source_success.index]
        
        colors_map = {'graph': '#2ecc71', 'pending_source': '#e74c3c'}
        colors = [colors_map.get(src, '#95a5a6') for src in source_success.index]
        
        bars = ax1.bar(display_labels, source_success['rate'], color=colors, 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Success Rate (%)', fontweight='bold')
        ax1.set_title('Success Rate by Confirmation Source', fontweight='bold', pad=15)
        ax1.set_ylim(0, 105)
        ax1.grid(axis='y', alpha=0.3)
        
        for i, (bar, rate, count) in enumerate(zip(bars, source_success['rate'], source_success['count'])):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%\n(n={count})',
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Sync Duration by Source
        ax2 = axes[0, 1]
        sources = self.df['confirmation_source'].unique()
        # Format labels for display
        display_source_labels = [self.format_source_label(src) for src in sources]
        data_by_source = [self.df[self.df['confirmation_source'] == src]['sync_duration_seconds'].dropna() 
                         for src in sources]
        
        bp = ax2.boxplot(data_by_source, labels=display_source_labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax2.set_ylabel('Sync Duration (seconds)', fontweight='bold')
        ax2.set_title('Sync Duration by Confirmation Source', fontweight='bold', pad=15)
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. Hourly Success Pattern
        ax3 = axes[1, 0]
        self.df['hour'] = self.df['created_at'].dt.hour
        hourly_success = self.df.groupby('hour')['both_success'].agg(['sum', 'count'])
        hourly_success['rate'] = hourly_success['sum'] / hourly_success['count'] * 100
        
        ax3.plot(hourly_success.index, hourly_success['rate'], marker='o', linewidth=2, 
                markersize=8, color='#3498db')
        ax3.fill_between(hourly_success.index, hourly_success['rate'], alpha=0.3, color='#3498db')
        ax3.set_xlabel('Hour of Day', fontweight='bold')
        ax3.set_ylabel('Success Rate (%)', fontweight='bold')
        ax3.set_title('Success Rate by Hour of Day', fontweight='bold', pad=15)
        ax3.set_xticks(hourly_success.index)
        ax3.grid(alpha=0.3)
        ax3.set_ylim(0, 105)
        
        # 4. Performance Heatmap
        ax4 = axes[1, 1]
        
        # Create bins for sync duration
        self.df['duration_bin'] = pd.cut(self.df['sync_duration_seconds'], 
                                         bins=[0, 5, 10, 30, 60, 300, float('inf')],
                                         labels=['0-5s', '5-10s', '10-30s', '30-60s', '60-300s', '300s+'])
        
        # Cross-tabulation
        heatmap_data = pd.crosstab(self.df['confirmation_source'], 
                                   self.df['duration_bin'])
        
        if not heatmap_data.empty:
            # Rename index labels for display
            heatmap_data.index = [self.format_source_label(idx) for idx in heatmap_data.index]
            
            sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', 
                       cbar_kws={'label': 'Transaction Count'}, ax=ax4)
            ax4.set_title('Transaction Distribution: Source vs Duration', 
                         fontweight='bold', pad=15)
            ax4.set_xlabel('Sync Duration Range', fontweight='bold')
            ax4.set_ylabel('Confirmation Source', fontweight='bold')
        
        plt.tight_layout()
        output_path = output_dir / 'advanced_metrics.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_path}")
        plt.close()
    
    def export_results(self, output_dir: Path):
        """Export detailed results to CSV and JSON."""
        # Summary CSV
        summary_df = pd.DataFrame([
            {
                'Metric': 'Confirmation Source',
                'Successful': self.results['confirmation_source']['successful'],
                'Failed': self.results['confirmation_source']['failed'],
                'Success Rate (%)': self.results['confirmation_source']['success_rate']
            },
            {
                'Metric': 'Transaction Confirmation Trace',
                'Successful': self.results['transaction_confirmation_trace']['successful'],
                'Failed': self.results['transaction_confirmation_trace']['failed'],
                'Success Rate (%)': self.results['transaction_confirmation_trace']['success_rate']
            },
            {
                'Metric': 'Both Metrics Combined',
                'Successful': self.results['both_metrics']['successful'],
                'Failed': self.results['both_metrics']['failed'],
                'Success Rate (%)': self.results['both_metrics']['success_rate']
            }
        ])
        
        summary_path = output_dir / 'success_summary.csv'
        summary_df.to_csv(summary_path, index=False)
        print(f"✓ Saved: {summary_path}")
        
        # Detailed results JSON
        json_path = output_dir / 'detailed_results.json'
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"✓ Saved: {json_path}")
        
        # Source breakdown CSV
        source_breakdown = self.df.groupby('confirmation_source').agg({
            'source_success': ['sum', 'count'],
            'trace_success': ['sum', 'count'],
            'both_success': ['sum', 'count'],
            'sync_duration_seconds': ['mean', 'median', 'std']
        }).round(2)
        
        source_path = output_dir / 'success_by_source_trace.csv'
        source_breakdown.to_csv(source_path)
        print(f"✓ Saved: {source_path}")
        
        # Top slowest transactions
        slowest = self.df.nlargest(20, 'sync_duration_seconds')[
            ['id', 'trx_hash', 'confirmation_source', 'trx_status', 
             'sync_duration_seconds', 'source_success', 'trace_success']
        ]
        slowest_path = output_dir / 'top_slowest_transactions.csv'
        slowest.to_csv(slowest_path, index=False)
        print(f"✓ Saved: {slowest_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze onchain sync success rates from k6 performance test data'
    )
    parser.add_argument('--input', '-i', default='transactions.csv',
                       help='Path to the input CSV file')
    parser.add_argument('--outdir', '-o', default='reports',
                       help='Output directory for reports and visualizations')
    
    args = parser.parse_args()
    
    # Setup output directory
    output_dir = Path(args.outdir)
    figures_dir = output_dir / 'figures'
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("ONCHAIN SYNC PERFORMANCE ANALYSIS")
    print("="*80)
    print(f"Input file: {args.input}")
    print(f"Output directory: {output_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Initialize analyzer
    analyzer = OnchainSyncAnalyzer(args.input)
    
    # Load and analyze data
    analyzer.load_data()
    analyzer.calculate_success_metrics()
    analyzer.print_summary()
    
    # Generate visualizations
    print("\n📊 Generating visualizations...")
    analyzer.plot_success_comparison(figures_dir)
    analyzer.plot_sync_duration_analysis(figures_dir)
    analyzer.plot_trace_analysis(figures_dir)
    analyzer.plot_advanced_metrics(figures_dir)
    
    # Export results
    print("\n📁 Exporting results...")
    analyzer.export_results(output_dir)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"All reports saved to: {output_dir.absolute()}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
