import os
import subprocess
import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# -------------------------------------------------------------------------
# [설정 로드] 분석 환경 변수 설정
# -------------------------------------------------------------------------
STRATEGY = "SentinelStrategy"
CONFIG_PATH = "freqtrade/user_data/config.json"
RESULTS_DIR = "freqtrade/user_data/backtest_results"
SUMMARY_CSV = "sentinel_backtest_summary.csv"
# 실제 시작 데이터가 있는 시점으로 조정 가능 (예: 20220101)
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2025, 12, 27)
INTERVAL_MONTHS = 6

def generate_timeranges(start, end, interval):
    """지정된 간격으로 시작일-종료일 리스트를 생성합니다."""
    ranges = []
    current_start = start
    while current_start < end:
        current_end = current_start + relativedelta(months=interval) - timedelta(days=1)
        if current_end > end:
            current_end = end
        
        ranges.append({
            "start": current_start.strftime("%Y%m%d"),
            "end": current_end.strftime("%Y%m%d"),
            "display": f"{current_start.strftime('%Y%m%d')}_{current_end.strftime('%Y%m%d')}"
        })
        current_start += relativedelta(months=interval)
    return ranges

def run_backtest(timerange_str, display_name):
    """Docker Compose를 통해 백테스팅을 실행합니다."""
    export_filename = f"sentinel-backtest-{display_name}.json"
    
    # 컨테이너 내부 경로를 기준으로 절대 경로 설정
    cmd = [
        "docker", "compose", "run", "--rm", "sentinel-bot",
        "backtesting",
        "--strategy", STRATEGY,
        "--timerange", timerange_str,
        "--config", "user_data/config.json",
        "--export", "trades",
        "--export-filename", f"user_data/backtest_results/{export_filename}"
    ]
    
    print(f"\n[PROGRESS] Running Sentinel Backtest: {display_name} ({timerange_str})")
    # 로그를 실시간으로 확인하기 위해 capture_output을 제거하거나 직접 출력
    subprocess.run(cmd)    
    # 생성된 파일의 호스트 기준 경로
    return f"{RESULTS_DIR}/{export_filename}"

def parse_result(json_path, display_name):
    """JSON 결과 파일에서 핵심 지표를 추출합니다."""
    if not json_path or not os.path.exists(json_path):
        return None
        
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Freqtrade 결과 구조 파싱
        s_data = data['strategy'][STRATEGY]
        
        return {
            "Period": display_name,
            "Total Trades": s_data.get('total_trades', 0),
            "Win Rate %": round(s_data.get('win_rate', 0) * 100, 2),
            "Profit %": round(s_data.get('profit_total_pct', 0), 2),
            "Profit USDT": round(s_data.get('profit_total_abs', 0), 2),
            "Max Drawdown %": round(s_data.get('max_drawdown_account_pct', 0), 2),
            "Sharpe Ratio": s_data.get('sharpe_ratio', 0),
            "Profit Factor": s_data.get('profit_factor', 0),
            "Avg Duration": s_data.get('avg_duration', "N/A")
        }
    except Exception as e:
        print(f"[WARNING] Parsing error for {display_name}: {e}")
        return None

def main():
    print(f"=== Freqtrade Automation Pipeline Starting ===")
    
    # 1. 대상 기간 생성
    timeranges = generate_timeranges(START_DATE, END_DATE, INTERVAL_MONTHS)
    print(f"[INFO] Total periods to test: {len(timeranges)}")
    
    # 2. 데이터 다운로드 (사전 준비)
    print(f"[INFO] Pre-downloading data for the entire range...")
    full_timerange = f"{START_DATE.strftime('%Y%m%d')}-"
    download_cmd = [
        "docker", "compose", "run", "--rm", "sentinel-bot", "download-data",
        "--timerange", full_timerange, "--exchange", "binance", "--trading-mode", "futures", "-t", "1h 5m"
    ]
    subprocess.run(download_cmd, capture_output=True)

    # 3. 루프 실행 및 데이터 수집
    all_results = []
    for tr in timeranges:
        tr_str = f"{tr['start']}-{tr['end']}"
        json_file = run_backtest(tr_str, tr['display'])
        
        parsed = parse_result(json_file, tr['display'])
        if parsed:
            all_results.append(parsed)
            print(f"[SUCCESS] {tr['display']}: Profit {parsed['Profit %']}% | WinRate {parsed['Win Rate %']}")

    # 4. 결과 저장
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(SUMMARY_CSV, index=False, encoding='utf-8-sig')
        print(f"\n✅ All tasks completed. Summary saved to: {SUMMARY_CSV}")
        print(df.to_string(index=False)) # 터미널에도 요약 출력
    else:
        print("\n❌ No results collected.")

if __name__ == "__main__":
    main()
