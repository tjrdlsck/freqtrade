import pandas as pd
import os
import glob

def generate_report():
    print("📊 Loading analysis data...")
    
    # Define file paths
    base_dir = 'analysis_results'
    files = {
        'summary': os.path.join(base_dir, 'master_summary.csv'),
        'pairs': os.path.join(base_dir, 'master_pair_performance.csv'),
        'tags': os.path.join(base_dir, 'master_tag_performance.csv'),
        'exit': os.path.join(base_dir, 'master_exit_analysis.csv')
    }
    
    # Load Dataframes
    dfs = {}
    for key, path in files.items():
        if os.path.exists(path):
            try:
                dfs[key] = pd.read_csv(path)
                # Standardize period column type if needed, but string is fine for grouping
            except Exception as e:
                print(f"⚠️ Error loading {path}: {e}")
                return
        else:
            print(f"⚠️ File not found: {path}")
            return

    # Sort Summary by Period (Simple string sort usually works for YYYY-MM-DD, 
    # but let's try to extract start date for proper sorting)
    try:
        dfs['summary']['start_date'] = dfs['summary']['period'].apply(lambda x: x.split(' to ')[0])
        dfs['summary']['start_date'] = pd.to_datetime(dfs['summary']['start_date'])
        dfs['summary'] = dfs['summary'].sort_values('start_date')
    except Exception as e:
        print(f"⚠️ Warning: Could not sort by date ({e}). Using default order.")

    # Initialize Markdown
    md = "# 🛡️ SentinelStrategy Official Performance Report\n\n"
    md += f"**Generated Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md += "> 본 보고서는 Sentinel 시스템의 과거 성과를 분석한 공식 리포트입니다.\n\n"
    md += "---\n\n"

    # ---------------------------------------------------------
    # 1. Executive Summary (Table of all periods)
    # ---------------------------------------------------------
    md += "## 1. 🗓️ Executive Summary\n\n"
    md += "| Period | Net Profit ($) | Profit (%) | Win Rate | Max Drawdown | Sharpe |\n"
    md += "| :--- | ---: | ---: | ---: | ---: | ---: |\n"
    
    for _, row in dfs['summary'].iterrows():
        period_short = row['period'].split(' to ')[0] # Just show start date or simplify
        profit_emoji = "✅" if row['profit_abs'] > 0 else "Lr"
        
        md += f"| {row['period']} | {profit_emoji} {row['profit_abs']:.2f} | {row['profit_pct']:.2f}% | {row['win_rate']:.2f}% | {row['mdd_pct']:.2f}% | {row['sharpe']:.2f} |\n"
    
    md += "\n---\n\n"

    # ---------------------------------------------------------
    # 2. Detailed Period Analysis
    # ---------------------------------------------------------
    md += "## 2. 🔍 Detailed Period Analysis\n\n"

    # Loop through each period in summary
    for _, row in dfs['summary'].iterrows():
        period = row['period']
        md += f"### 📅 Period: {period}\n\n"
        
        # A. Key Metrics
        md += "**Key Metrics:**\n"
        md += f"- **Total Profit:** `{row['profit_abs']:.2f} USD` ({row['profit_pct']:.2f}%)\n"
        md += f"- **Total Trades:** `{row['trades']}`\n"
        md += f"- **Win Rate:** `{row['win_rate']:.2f}%`\n"
        md += f"- **Max Drawdown:** `{row['mdd_pct']:.2f}%`\n"
        md += f"- **Sharpe Ratio:** `{row['sharpe']:.2f}`\n\n"

        # B. Best & Worst Pairs (Filter pairs df by period)
        if 'pairs' in dfs:
            period_pairs = dfs['pairs'][dfs['pairs']['period'] == period].copy()
            if not period_pairs.empty:
                # Sort by profit_total_abs
                period_pairs = period_pairs.sort_values('profit_total_abs', ascending=False)
                best_pair = period_pairs.iloc[0]
                worst_pair = period_pairs.iloc[-1]

                md += "**🏆 Best Pair:**\n"
                md += f"> **{best_pair['key']}**: +{best_pair['profit_total_abs']:.2f} USD ({best_pair['winrate']*100:.1f}% Win)\n\n"
                
                md += "**💀 Worst Pair:**\n"
                md += f"> **{worst_pair['key']}**: {worst_pair['profit_total_abs']:.2f} USD ({worst_pair['winrate']*100:.1f}% Win)\n\n"
        
        # C. Long vs Short Analysis (Tag Analysis)
        if 'tags' in dfs:
            period_tags = dfs['tags'][dfs['tags']['period'] == period].copy()
            if not period_tags.empty:
                md += "**🏷️ Strategy Logic Analysis (Long vs Short):**\n"
                md += "| Tag | Trades | Profit ($) | Win Rate |\n"
                md += "| :--- | ---: | ---: | ---: |\n"
                for _, tag_row in period_tags.iterrows():
                    md += f"| `{tag_row['key']}` | {tag_row['trades']} | {tag_row['profit_total_abs']:.2f} | {tag_row['winrate']*100:.1f}% |\n"
                md += "\n"

        # D. Exit Reason Analysis
        if 'exit' in dfs:
            period_exits = dfs['exit'][dfs['exit']['period'] == period].copy()
            if not period_exits.empty:
                md += "**🚪 Exit Reasons:**\n"
                md += "| Exit Type | Count | Profit ($) |\n"
                md += "| :--- | ---: | ---: |\n"
                for _, exit_row in period_exits.iterrows():
                    md += f"| {exit_row['key']} | {exit_row['trades']} | {exit_row['profit_total_abs']:.2f} |\n"
                md += "\n"
        
        md += "---\n\n"

    # Save File
    output_file = "STRATEGY_PERFORMANCE_REPORT.md"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(md)
    
    print(f"✅ Report successfully generated: {output_file}")

if __name__ == "__main__":
    generate_report()
