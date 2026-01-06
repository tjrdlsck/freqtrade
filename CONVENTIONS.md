# 📜 Project Sentinel Code Conventions

이 가이드는 구글 및 메타의 파이썬 스타일 가이드를 기반으로 하며, Freqtrade 전략 개발에 최적화되어 있습니다. 모든 팀원은 본 규칙을 준수하여 유지보수가 용이한 코드를 작성해야 합니다.

---

## 1. 파이썬 스타일 가이드 (Python Style)

### 1.1 명명 규칙 (Naming Conventions)
*   **Class:** `PascalCase` (예: `SentinelStrategy`)
*   **Functions/Variables:** `snake_case` (예: `calculate_indicators`, `entry_signal`)
*   **Constants:** `UPPER_SNAKE_CASE` (예: `MAX_ATR_MULTIPLIER`)
*   **Private Members:** 접두사 `_` 사용 (예: `_calculate_rsi`)

### 1.2 타입 힌팅 (Type Hinting)
모든 함수 선언에는 반드시 입력과 출력의 타입을 명시합니다.
```python
def get_entry_signal(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    ...
```

### 1.3 문서화 (Docstrings)
모든 클래스와 주요 함수에는 `Google Style` Docstring을 작성합니다.
```python
def calculate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    """전략에 필요한 기술적 지표를 계산합니다.

    Args:
        dataframe (DataFrame): 원본 시세 데이터.
        metadata (dict): 페어(pair) 정보를 포함한 메타데이터.

    Returns:
        DataFrame: 지표가 추가된 데이터프레임.
    """
```

---

## 2. 전략 개발 규칙 (Strategy Rules)

### 2.1 하이퍼옵트 파라미터 (Hyperopt Parameters)
*   모든 최적화 변수는 `IntParameter`, `DecimalParameter` 등을 사용하여 클래스 상단에 정의합니다.
*   매직 넘버(Magic Number)를 하드코딩하지 마십시오.

### 2.2 로직 분리
*   지표 계산(`populate_indicators`), 진입 로직(`populate_entry_trend`), 탈출 로직(`populate_exit_trend`)을 엄격히 분리합니다.
*   복잡한 수학적 필터는 별도의 Private 메서드로 추출합니다.

---

## 3. Git 커밋 메시지 (Conventional Commits)

메시지는 다음과 같은 형식을 따릅니다: `<type>(<scope>): <subject>`

*   **feat:** 새로운 기능/지표 추가
*   **fix:** 버그 수정 (예: 런타임 에러, 잘못된 지표 계산)
*   **refactor:** 성능 개선 및 코드 정리
*   **docs:** 문서 수정 (README, LOG 등)
*   **test:** 테스트 코드 추가 및 백테스트 스크립트 수정

---

## 4. 데이터 보안 (Security)

*   `config.json` 내의 API Key, Secret, Telegram Token은 절대 Git에 커밋하지 않습니다.
*   `.env` 파일이나 시스템 환경 변수를 활용하십시오.
*   현재 프로젝트의 `.gitignore`가 제대로 작동하는지 주기적으로 확인합니다.

---

## 5. 수학적 표현 (Mathematical Precision)
전략 내 수식 설명이 필요한 경우 LaTeX 형식을 사용합니다.
*   예: RSI 하단 돌파 필터 $RSI_{current} < RSI_{threshold}$
