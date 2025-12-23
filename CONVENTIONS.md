**Project Sentinel** 개발을 위한 코드 컨벤션 가이드라인입니다.

이 프로젝트는 **금융 자산**을 다루는 시스템이므로, 일반적인 웹 서비스보다 **더 엄격한 타입 체크(Type Safety), 에러 처리, 그리고 가독성**이 요구됩니다. 개발팀(또는 미래의 본인)은 아래 규칙을 준수하여 시스템의 안정성(Stability)을 확보해야 합니다.

---

# Project Sentinel 코드 컨벤션 (Code Convention Rules)

## 0. 기본 원칙 (General Principles)
1.  **Safety First:** 코드가 예쁘게 보이는 것보다, **에러가 나지 않는 것**이 최우선입니다.
2.  **Explicit is better than Implicit:** 암묵적인 동작보다는 명시적인 코드 작성을 지향합니다. (Zen of Python)
3.  **English Code, Korean Doc:** 변수명, 주석, 커밋 메시지는 **영어**를 사용하고, 복잡한 비즈니스 로직에 대한 설명이나 PR 문서 등은 **한국어**로 작성합니다.

---

## 1. Backend (Python: Freqtrade Strategy & FastAPI)

### 1.1 스타일 가이드 및 포맷팅
*   **Formatter:** `Black`을 사용합니다. (Line Length: 100자 권장)
*   **Linter:** `Ruff` 또는 `Flake8`을 사용하여 미사용 임포트 등을 정리합니다.
*   **Import 순서:** 표준 라이브러리 -> 서드파티(FastAPI, Pandas 등) -> 로컬 모듈 순서로 정렬합니다 (`isort` 사용 권장).

### 1.2 네이밍 규칙 (Naming Convention)
*   **변수/함수:** `snake_case` (예: `calculate_rsi`, `current_price`)
*   **클래스:** `PascalCase` (예: `FuturesStrategyV1`, `TradeService`)
*   **상수:** `UPPER_SNAKE_CASE` (예: `MAX_LEVERAGE = 3`)
*   **프라이빗 변수:** 언더스코어 접두사 `_variable` 사용.

### 1.3 타입 힌트 (Type Hinting) - **필수(Critical)**
금융 계산 오류 방지를 위해 모든 함수 인자와 반환값에 타입을 명시합니다.
```python
# Bad
def calculate_profit(entry, current):
    return (current - entry) / entry

# Good
from decimal import Decimal

def calculate_profit(entry_price: float, current_price: float) -> float:
    if entry_price == 0:
        return 0.0
    return (current_price - entry_price) / entry_price
```

### 1.4 Freqtrade 전략 파일 규칙
*   **벡터화 연산:** `for` 문을 사용하여 데이터프레임을 순회하지 않습니다. 반드시 Pandas/NumPy의 벡터 연산을 사용합니다. (속도 이슈 방지)
*   **지표 계산:** `populate_indicators` 메서드 내에서만 지표를 추가합니다.
*   **안전 장치:** 전략 클래스 최상단에 `stoploss`, `timeframe`을 명시적으로 선언합니다.

### 1.5 FastAPI 규칙
*   **Pydantic 모델 사용:** API 입출력 데이터 검증을 위해 반드시 Pydantic 모델(`BaseModel`)을 정의합니다. `dict`를 직접 리턴하지 않습니다.
*   **Async/Await:** I/O 작업(DB 조회, 외부 API 호출)이 있는 핸들러는 반드시 `async def`로 정의합니다.
*   **에러 핸들링:** `try-except` 블록에서 `pass`를 절대 사용하지 않습니다. 로그를 남기거나 적절한 HTTP Exception을 발생시킵니다.

---

## 2. Frontend (React + TypeScript)

### 2.1 기술 스택 및 스타일
*   **언어:** **TypeScript** (JavaScript 금지). `.tsx`, `.ts` 확장자만 사용합니다.
*   **스타일:** `Tailwind CSS`를 사용하며, 클래스 순서는 논리적 그룹핑을 따릅니다 (Layout -> Box Model -> Typography -> Visual).
*   **Linter:** `ESLint` + `Prettier` 설정 필수.

### 2.2 네이밍 규칙
*   **컴포넌트:** `PascalCase` (예: `DashboardCard.tsx`)
*   **함수/변수:** `camelCase` (예: `fetchUserBalance`)
*   **인터페이스/타입:** `IPrefix`를 사용하지 않고 명확한 이름을 짓습니다 (예: `IUser` (X) -> `User` or `UserProps` (O)).

### 2.3 컴포넌트 구조
UI 로직과 비즈니스 로직(데이터 페칭 등)을 분리합니다.
*   **Container/View:** 페이지 구조 및 데이터 호출 담당.
*   **Component:** 순수 UI 렌더링 담당.
*   **Hooks:** 복잡한 로직은 커스텀 훅(`useTokenPrice` 등)으로 분리.

### 2.4 모바일/데스크탑 분리 전략
*   반응형이 가능하더라도, UX가 완전히 다른 경우 컴포넌트를 분리합니다.
*   디렉토리 구조 예시:
    ```text
    src/
      components/
        mobile/    # 모바일 전용 (큰 버튼, 심플한 카드)
          PanicButton.tsx
        desktop/   # 데스크탑 전용 (차트, 상세 테이블)
          TradingViewChart.tsx
        shared/    # 공통 컴포넌트
          StatusBadge.tsx
    ```

### 2.5 상태 관리 (State Management)
*   **Server State:** API 데이터는 `TanStack Query (React Query)`를 사용합니다.
*   **Client State:** 전역 UI 상태(테마, 사이드바 토글 등)는 `Zustand`를 사용합니다. `Redux`는 지양합니다.

---

## 3. 예외 처리 및 로깅 (Critical for Trading)

### 3.1 로깅 규칙 (Logging)
*   단순 `print()` 사용 금지. Python `logging` 모듈을 사용합니다.
*   로그 레벨 정책:
    *   `DEBUG`: 지표 계산 값, API 호출 파라미터.
    *   `INFO`: 매수/매도 주문 실행, 봇 상태 변경.
    *   `WARNING`: API 지연, 비정상적인 데이터 수신.
    *   `ERROR`: 주문 실패, 연결 끊김, 예외 발생. **(텔레그램 알림 연동 필수)**

### 3.2 부동소수점 처리 (Floating Point)
*   돈과 관련된 계산(특히 수량, 가격)은 Python의 `float` 오차를 인지하고, 필요 시 `Decimal`을 사용하거나, 거래소 API가 요구하는 자리수(`precision`)로 `round()` 처리 후 전송합니다.

---

## 4. 버전 관리 및 커밋 (Git Convention)

### 4.1 커밋 메시지 (Conventional Commits)
형식: `type(scope): subject`
*   `feat`: 새로운 기능 (예: `feat(strategy): add macd cross logic`)
*   `fix`: 버그 수정 (예: `fix(api): handle timeout error`)
*   `docs`: 문서 수정
*   `style`: 포맷팅 수정 (코드 변경 없음)
*   `refactor`: 리팩토링 (기능 변경 없음)
*   `chore`: 빌드 설정, 패키지 매니저 설정 등

### 4.2 브랜치 전략
*   `main`: 배포 가능한 안정 버전.
*   `dev`: 개발 중인 버전.
*   `feature/기능명`: 개별 기능 개발 브랜치.

---

## 5. 보안 (Security)

### 5.1 API Key 관리
*   API Key와 Secret Key는 **절대** 코드 내에 하드코딩하지 않습니다.
*   반드시 `.env` 파일을 통해 로드하며, `.gitignore`에 `.env`를 포함시킵니다.

### 5.2 Panic Button (긴급 정지) 로직 안전 장치
*   프론트엔드에서 '긴급 정지' 버튼 클릭 시, 실수 방지를 위해 **"Double Confirmation (2차 확인 모달)"** 또는 **"Long Press (길게 누르기)"** UX를 적용해야 합니다.
*   백엔드에서는 해당 요청이 인증된 사용자(Admin)에게서 왔는지 재검증해야 합니다.

---

### 개발자를 위한 한마디
> "이 코드는 내 돈을 다룹니다. **'이 정도면 되겠지'**라는 생각으로 커밋하지 마십시오. 백테스팅과 로그가 증명하지 않은 코드는 신뢰하지 마십시오."