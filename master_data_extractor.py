import os
import json
import zipfile
import pandas as pd
import glob

RESULTS_DIR = "freqtrade/user_data/backtest_results"
STRATEGY_NAME = "SentinelStrategy"
OUTPUT_DIR = "analysis_results"

def extract_all_data():
    summary_list = []
    pair_list = []
    exit_list = []
    tag_list = []
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    zip_files = glob.glob(os.path.join(RESULTS_DIR, "*.zip"))
    zip_files.sort() # 시간순 정렬 (파일명에 타임스탬프 있음)
    
    print(f"Found {len(zip_files)} result files. Starting precision extraction for {STRATEGY_NAME}...")

    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                json_files = [f for f in z.namelist() if f.endswith('.json') and 'config' not in f]
                if not json_files: continue
                
                with z.open(json_files[0]) as f:
                    data = json.load(f)
                    if STRATEGY_NAME not in data['strategy']: continue
                    
                    strat_data = data['strategy'][STRATEGY_NAME]
                    # 파일명에서 날짜 정보 추출 (디버깅용)
                    period_id = os.path.basename(zip_path).split('-')[-1].replace('.zip', '')
                    display_period = f"{strat_data.get('backtest_start', 'N/A')} to {strat_data.get('backtest_end', 'N/A')}"
                    
                    # 1. Summary (핵심 지표)
                    summary_list.append({
                        "period": display_period,
                        "trades": strat_data.get("total_trades"),
                        "win_rate": round(strat_data.get("winrate", 0) * 100, 2),
                        "profit_pct": round(strat_data.get("profit_total", 0) * 100, 2),
                        "profit_abs": round(strat_data.get("profit_total_abs", 0), 2),
                        "mdd_pct": round(strat_data.get("max_drawdown_account", 0) * 100, 2),
                        "sharpe": strat_data.get("sharpe"),
                        "profit_factor": strat_data.get("profit_factor"),
                        "cagr": strat_data.get("cagr")
                    })
                    
                    # 2. Results per Pair (페어별)
                    if "results_per_pair" in strat_data:
                        for entry in strat_data["results_per_pair"]:
                            row = entry.copy()
                            row["period"] = display_period
                            pair_list.append(row)
                            
                    # 3. Exit Reason Summary (청산 사유별)
                    if "exit_reason_summary" in strat_data:
                        for entry in strat_data["exit_reason_summary"]:
                            row = entry.copy()
                            row["period"] = display_period
                            exit_list.append(row)

                    # 4. Results per Enter Tag (진입 태그별: Long vs Short)
                    if "results_per_enter_tag" in strat_data:
                        for entry in strat_data["results_per_enter_tag"]:
                            row = entry.copy()
                            row["period"] = display_period
                            tag_list.append(row)
                            
        except Exception as e:
            print(f"Error processing {zip_path}: {e}")

    # 최종 CSV 저장 (중복 제거 포함)
    if summary_list:
        df_sum = pd.DataFrame(summary_list).drop_duplicates(subset=['period'])
        df_sum.to_csv(os.path.join(OUTPUT_DIR, "master_summary.csv"), index=False, encoding='utf-8-sig')
        
    if pair_list:
        df_pair = pd.DataFrame(pair_list)
        # 특정 페어의 'TOTAL' 행은 제외 (분석에 방해됨)
        df_pair = df_pair[df_pair['key'] != 'TOTAL']
        df_pair.to_csv(os.path.join(OUTPUT_DIR, "master_pair_performance.csv"), index=False, encoding='utf-8-sig')
        
    if exit_list:
        pd.DataFrame(exit_list).to_csv(os.path.join(OUTPUT_DIR, "master_exit_analysis.csv"), index=False, encoding='utf-8-sig')
        
    if tag_list:
        pd.DataFrame(tag_list).to_csv(os.path.join(OUTPUT_DIR, "master_tag_performance.csv"), index=False, encoding='utf-8-sig')
        
    print("\n✅ Ultimate Extraction Complete!")
    print(f"- Master Summary: {OUTPUT_DIR}/master_summary.csv")
    print(f"- Pair Performance: {OUTPUT_DIR}/master_pair_performance.csv")
    print(f"- Exit Analysis: {OUTPUT_DIR}/master_exit_analysis.csv")
    print(f"- Tag Performance: {OUTPUT_DIR}/master_tag_performance.csv")

if __name__ == "__main__":
    extract_all_data()