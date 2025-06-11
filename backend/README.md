# Contact Form Widget - Backend

このドキュメントは、Contact Form Widgetプロジェクトのバックエンドアプリケーションに関する技術的な詳細、セットアップ手順、API仕様について説明します。

## 1. 概要 (Overview)

バックエンドアプリケーションは、Contact Form Widgetから送信されるお問い合わせデータの受付、保存、および管理機能を提供します。また、AIチャットボット機能、Google Analytics 4 (GA4) へのイベント送信機能も担います。

主な機能は以下の通りです。

-   **フォームデータ処理**: フロントエンドウィジェットからの問い合わせデータ（名前、メールアドレス、メッセージ等）を受信し、データベースに保存します。
-   **AIチャットボット連携**: ユーザーからの質問に対してAI（Geminiモデルを利用）が応答するチャット機能を提供します。
-   **GA4 Measurement Protocol連携**: フォーム送信時や問い合わせステータス変更時に、リードジェネレーション関連のイベントをGA4に送信します。
-   **GA4設定管理**: フォームごとにGA4の測定IDとAPIシークレットを設定・管理するためのAPIを提供します。
-   **問い合わせステータス管理**: 問い合わせの進捗ステータス（新規、連絡済み、成約など）を管理し、ステータス変更を行うためのAPIを提供します。

このバックエンドは、フロントエンドの埋め込みウィジェットと連携して動作するように設計されています。

## 2. 技術スタック (Tech Stack)

バックエンドシステムは以下の主要な技術で構成されています。

-   **プログラミング言語**: Python 3.11+
-   **フレームワーク**: FastAPI - 高パフォーマンスな非同期Webフレームワーク。
-   **データベース**: Supabase (PostgreSQL) - `supabase-py` クライアントライブラリを通じて連携。
-   **データバリデーション**: Pydantic V2 - APIリクエスト/レスポンスの型定義とバリデーション。
-   **HTTPクライアント**: `httpx` - GA4 Measurement Protocol APIなど、外部APIとの非同期通信に使用。
-   **AI連携**: Google Agent Development Kit (ADK) - Geminiモデルを利用したAIエージェント機能。
-   **リトライ処理**: tenacity - AI Agentなどの外部API呼び出しにおけるリトライ処理に使用。
-   **ASGIサーバー**: Uvicorn - FastAPIアプリケーションの実行。
-   **依存関係管理**: `pip` と `requirements.txt`。

## 3. プロジェクト構造 (Project Structure)

`backend/` ディレクトリ内の主要なサブディレクトリとファイルの役割は以下の通りです。

```
backend/
├── .gitkeep                     # 空ディレクトリをGit管理するためのプレースホルダ (あれば)
├── ai_agent.py                  # AIチャットボットのロジック（ADK、Gemini連携）
├── config.py                    # 環境変数管理（Pydantic Settingsによる設定読み込み）
├── contact_api.py               # メインFastAPIアプリケーション定義、主要エンドポイント（/submit, /chat）、ルーター登録
├── db.py                        # Supabaseクライアントの初期化とFastAPI依存性注入の提供
├── models/                      # Pydanticモデル定義用ディレクトリ
│   ├── ga4_config_models.py     # GA4設定管理API用のリクエスト/レスポンスモデル
│   └── submission_models.py     # 問い合わせステータス更新API用のリクエストモデル
├── requirements.txt             # Pythonの依存パッケージリスト
├── routers/                     # APIルーターモジュール用ディレクトリ
│   ├── form_ga_config_router.py # GA4設定管理APIのエンドポイント定義
│   └── submission_router.py     # 問い合わせステータス更新APIのエンドポイント定義
├── services/                    # ビジネスロジック層用ディレクトリ
│   ├── form_ga_config_service.py# GA4設定のCRUD処理ロジック
│   ├── ga4_mp_service.py        # GA4 Measurement Protocol APIへのイベント送信ロジック
│   └── submission_service.py    # 問い合わせステータス更新処理ロジック
└── tests/                       # 自動テスト用ディレクトリ
    ├── test_contact_api.py      # /submit API (/chat APIは未実装) のテスト
    ├── test_form_ga_config_api.py # GA4設定管理APIのテスト
    ├── test_submission_api.py   # ステータス更新APIのテスト
    └── test_ai_agent.py         # AI Agent関連ロジックのテスト (追加)
```

-   **`contact_api.py`**: FastAPIアプリケーションのインスタンス (`app`) を生成し、ミドルウェアの設定、主要なエンドポイント（`/submit`, `/chat`）、および各機能ルーターの登録を行います。
-   **`config.py`**: `.env` ファイルから環境変数を読み込み、アプリケーション全体で利用可能な設定オブジェクトを提供します。
-   **`db.py`**: Supabaseクライアントを初期化し、APIエンドポイントでデータベース接続を利用するためのFastAPI依存性注入関数 (`get_supabase_client`) を提供します。
-   **`ai_agent.py`**: Google ADKを利用したAIチャットボットの応答生成ロジックを実装しています。
-   **`routers/`**: 各機能グループに対応するAPIエンドポイント（パスオペレーション）を定義した `APIRouter` モジュールを格納します。
-   **`services/`**: APIエンドポイントから呼び出されるビジネスロジックやデータベース操作をカプセル化した関数/クラスを格納します。
-   **`models/`**: APIのリクエストボディやレスポンスボディの構造を定義するPydanticモデルを格納します。
-   **`tests/`**: `pytest` を利用した自動テストコードを格納します。各APIルーターや主要なサービスに対応するテストファイルが含まれます。

## 4. ローカル開発環境セットアップ (Local Development Setup)

バックエンドアプリケーションをローカル環境でセットアップし、実行するための手順です。

### 前提条件
-   Python 3.11 以降
-   `pip` (Python パッケージインストーラ)
-   Supabaseプロジェクト（詳細はプロジェクトルートのREADME.mdを参照し、セットアップ済みであること）
-   (推奨) Python仮想環境 (`venv`, `conda` など)

### セットアップ手順
1.  **リポジトリのクローン** (まだの場合):
    ```bash
    # git clone <repository_url>
    # cd <repository_name>/backend
    # (リポジトリをクローン後、backendディレクトリに移動している想定で以降を記述)
    ```

2.  **(推奨) Python仮想環境の作成と有効化** (例: `backend` ディレクトリ内で):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows (バックスラッシュをエスケープ)
    ```

3.  **依存関係のインストール**:
    `backend` ディレクトリ直下で以下を実行します。
    ```bash
    pip install -r requirements.txt
    ```

4.  **`.env` ファイルの作成と設定**:
    *   プロジェクトのルートディレクトリにある `.env.example` をコピーし、同じくプロジェクトルートに `.env` ファイルとして作成します。
    *   `.env` ファイルを編集し、以下の必須環境変数を設定してください。
        ```dotenv
        SUPABASE_URL="YOUR_SUPABASE_PROJECT_URL"
        SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"

        # AI Agent用 (オプション)
        # GEMINI_MODEL_NAME="gemini-1.5-flash-latest" # config.pyにデフォルト値あり
        # GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_IF_ADC_IS_NOT_SETUP"

        # --- AI Agent Retry Settings (オプション、config.pyにデフォルト値あり) ---
        # AI AgentのAPI呼び出しリトライ回数の最大値
        # AI_AGENT_RETRY_ATTEMPTS=3
        # リトライ時の初回待機秒数
        # AI_AGENT_RETRY_WAIT_INITIAL_SECONDS=1
        # リトライ時の最大待機秒数（指数バックオフ利用時）
        # AI_AGENT_RETRY_WAIT_MAX_SECONDS=10
        # 指数バックオフの乗数 (例: 1秒後, 2秒後, 4秒後...)
        # AI_AGENT_RETRY_WAIT_MULTIPLIER=2
        ```
        `GEMINI_MODEL_NAME` およびAI Agentリトライ関連の設定は `config.py` でデフォルト値が設定されています。環境変数で上書き可能です。`GOOGLE_API_KEY` はApplication Default Credentials (ADC) が設定されていれば不要な場合があります。GA4関連のAPIキーと測定IDは、API経由でフォームごとにデータベースに設定します。

5.  **データベーススキーマの適用**:
    SupabaseプロジェクトのSQL Editorを使用して、以下のスキーマファイルを順番に実行し、必要なテーブルとカラムを作成します。
    1.  `database/contact_form_schema.sql` (問い合わせ保存用テーブル `contact_submissions` 作成)
    2.  `database/form_ga_configurations_schema.sql` (フォームごとのGA4設定用テーブル `form_ga_configurations` 作成)
    3.  以下のSQLを実行して `contact_submissions` テーブルに `updated_at` カラムと自動更新トリガーを追加 (以前の指示で実行済み):
        ```sql
        -- Add updated_at column and auto-update trigger to contact_submissions table
        ALTER TABLE contact_submissions
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

        COMMENT ON COLUMN contact_submissions.updated_at IS 'Timestamp of when this submission record was last updated.';

        CREATE OR REPLACE FUNCTION update_contact_submissions_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER trigger_update_contact_submissions_updated_at
        BEFORE UPDATE ON contact_submissions
        FOR EACH ROW
        EXECUTE FUNCTION update_contact_submissions_updated_at_column();
        ```

6.  **開発サーバーの起動**:
    プロジェクトのルートディレクトリから（または `PYTHONPATH` が適切に設定されていれば `backend` ディレクトリから）以下のコマンドを実行します。
    ```bash
    uvicorn backend.contact_api:app --reload --port 8000
    ```
    `--reload` オプションにより、コード変更時にサーバーが自動的に再起動します。

7.  **APIドキュメントへのアクセス**:
    サーバー起動後、ブラウザで http://localhost:8000/docs にアクセスすると、Swagger UIによるAPIドキュメントが表示され、各エンドポイントを試すことができます。 http://localhost:8000/redoc でもRedoc形式のドキュメントが確認できます。

## 5. APIエンドポイント詳細 (API Endpoints)

バックエンドアプリケーションは以下の主要なAPIエンドポイントを提供します。
詳細なリクエスト/レスポンスのスキーマやパラメータについては、サーバー起動後に `/docs` (Swagger UI) または `/redoc` (Redoc) でご確認ください。

### 5.1. フォーム送信 (Form Submission)

-   **`POST /submit`**
    -   **説明**: フロントエンドウィジェットからのお問い合わせデータを受け付け、データベースに保存します。保存成功後、GA4が設定されていれば `generate_lead` イベントを送信します。
    -   **認証**: 不要 (通常、公開エンドポイント)
    -   **リクエストボディ例**:
        ```json
        {
          "name": "山田 太郎",
          "email": "yamada.taro@example.com",
          "message": "製品Aについて詳しく知りたいです。",
          "ga_client_id": "GA1.2.123456789.1678901234",
          "ga_session_id": "1678901234",
          "form_id": "product_inquiry_form"
        }
        ```
    -   **成功レスポンス例 (200 OK)**:
        ```json
        {
          "id": 123,
          "created_at": "2024-03-15T10:30:00Z",
          "name": "山田 太郎",
          "email": "yamada.taro@example.com",
          "message": "製品Aについて詳しく知りたいです。",
          "ga_client_id": "GA1.2.123456789.1678901234",
          "ga_session_id": "1678901234",
          "form_id": "product_inquiry_form",
          "submission_status": "new",
          "status_change_reason": null,
          "updated_at": "2024-03-15T10:30:00Z"
        }
        ```
    -   **主なエラーステータス**:
        -   `422 Unprocessable Entity`: リクエストボディのバリデーションエラー。
        -   `503 Service Unavailable`: データベースクライアント未初期化など。
        -   `500 Internal Server Error`: その他のサーバー内部エラー。

### 5.2. AIチャット (AI Chat)

-   **`POST /chat`**
    -   **説明**: AIチャットボット（Geminiモデル）との対話メッセージを処理し、AIからの応答を返します。
    -   **認証**: 不要 (通常、公開エンドポイント)
    -   **リクエストボディ例**:
        ```json
        {
          "message": "このウィジェットの価格は？",
          "session_id": "chat-session-789"
        }
        ```
    -   **成功レスポンス例 (200 OK)**:
        ```json
        {
          "reply": "価格については、料金ページをご覧ください...",
          "session_id": "chat-session-789",
          "require_form_after_message": false
        }
        ```
    -   **主なエラーステータス**:
        -   `422 Unprocessable Entity`: リクエストボディのバリデーションエラー。
        -   `500 Internal Server Error`: AIエージェント処理中のエラーなど。

### 5.3. 問い合わせデータ一覧取得 (List Submissions)

-   **`GET /api/v1/submissions`**
    -   **説明**: 問い合わせデータの一覧を、指定されたフィルター条件、ページネーション、ソート順に基づいて取得します。
    -   **認証**: 必要。
    -   **クエリパラメータ**:
        -   `form_id: Optional[str]` (フォームID)
        -   `submission_status: Optional[str]` (ステータス)
        -   `email: Optional[str]` (メールアドレス、部分一致)
        -   `name: Optional[str]` (名前、部分一致)
        -   `start_date: Optional[date]` (作成日範囲始点 YYYY-MM-DD)
        -   `end_date: Optional[date]` (作成日範囲終点 YYYY-MM-DD)
        -   `skip: int` (デフォルト `0`, 0以上)
        -   `limit: int` (デフォルト `20`, 1以上100以下)
        -   `sort_by: Optional[str]` (デフォルト `created_at`, Enum: `created_at`, `updated_at`, `name`, `submission_status`, `id`, `email`, `form_id`)
        -   `sort_order: Optional[str]` (デフォルト `desc`, Enum: `asc`, `desc`)
    -   **成功レスポンス例 (200 OK)**:
        ```json
        {
          "submissions": [
            {
              "id": 123,
              "created_at": "2024-03-15T10:30:00Z",
              "name": "山田 太郎",
              "email": "yamada.taro@example.com",
              "message": "製品Aについて詳しく知りたいです。",
              "ga_client_id": "GA1.2.123456789.1678901234",
              "ga_session_id": "1678901234",
              "form_id": "product_inquiry_form",
              "submission_status": "new",
              "status_change_reason": null,
              "updated_at": "2024-03-15T10:30:00Z"
            }
          ],
          "total_count": 1,
          "skip": 0,
          "limit": 20
        }
        ```
    -   **主なエラーステータス**:
        -   `422 Unprocessable Entity`: クエリパラメータのバリデーションエラー。
        -   `503 Service Unavailable`: データベースクライアント未初期化など。
        -   `500 Internal Server Error`: その他のサーバー内部エラー。

### 5.4. GA4設定管理 (GA4 Form Configurations)

これらのエンドポイントは、フォームごとのGA4測定IDとAPIシークレットを管理します。
**認証**: 必要 (全てのGA4設定管理エンドポイント)

-   **`POST /api/v1/ga_configurations`**
    -   **説明**: 新しいフォームに対するGA4設定を登録します。`form_id` はリクエストボディに含めます。
    -   **成功レスポンス (201 Created)**: 作成されたGA4設定情報。
    -   **主なエラーステータス**: `409 Conflict` (指定`form_id`が既に存在する場合), `422`, `500`, `503`。

-   **`GET /api/v1/ga_configurations`**
    -   **説明**: 登録されている全てのフォームGA4設定をリストします（ページネーション対応: `skip`, `limit` クエリパラメータ）。
    -   **成功レスポンス (200 OK)**: GA4設定のリスト。

-   **`GET /api/v1/ga_configurations/{form_id}`**
    -   **説明**: 指定された `form_id` のGA4設定を取得します。
    -   **成功レスポンス (200 OK)**:該当するGA4設定情報。
    -   **主なエラーステータス**: `404 Not Found`。

-   **`PUT /api/v1/ga_configurations/{form_id}`**
    -   **説明**: 指定された `form_id` のGA4設定を更新します。
    -   **成功レスポンス (200 OK)**: 更新されたGA4設定情報。
    -   **主なエラーステータス**: `404 Not Found`, `422`, `500`, `503`。

-   **`DELETE /api/v1/ga_configurations/{form_id}`**
    -   **説明**: 指定された `form_id` のGA4設定を削除します。
    -   **成功レスポンス (204 No Content)**。
    -   **主なエラーステータス**: `404 Not Found`。

### 5.5. 問い合わせステータス更新 (Submission Status Update)

-   **`PATCH /api/v1/submissions/{submission_id}/status`**
    -   **説明**: 指定された問い合わせ (`submission_id`) のステータス (`submission_status`と任意で`status_change_reason`) を更新します。ステータス変更に応じて、GA4イベントが送信されます。
    -   **認証**: 必要。
    -   **リクエストボディ例**:
        ```json
        {
          "new_status": "converted",
          "reason": "Lead successfully closed."
        }
        ```
    -   **成功レスポンス例 (200 OK)**: 更新された問い合わせレコード全体。
    -   **主なエラーステータス**: `404 Not Found` (submission_idが見つからない場合), `422`, `500`, `503`。

## 6. データベーススキーマ概要 (Database Schema Overview)

バックエンドはSupabase (PostgreSQL) データベースを使用します。主要なテーブルは以下の通りです。
詳細なスキーマ定義はプロジェクトルートの `database/` ディレクトリ内の各SQLファイルを参照してください。

-   **`contact_submissions`**:
    -   **説明**: お問い合わせフォームから送信されたデータを保存します。
    -   **スキーマファイル**: `database/contact_form_schema.sql` (および `updated_at` 追加・トリガー設定SQL)
    -   **主要カラム**:
        -   `id` (BIGSERIAL, PK): 一意なID。
        -   `created_at` (TIMESTAMPTZ): 作成日時。
        -   `updated_at` (TIMESTAMPTZ): 最終更新日時 (トリガーで自動更新)。
        -   `name` (TEXT): 送信者名。
        -   `email` (TEXT): 送信者メールアドレス。
        -   `message` (TEXT): 問い合わせ内容。
        -   `ga_client_id` (TEXT, Optional): GA4クライアントID。
        -   `ga_session_id` (TEXT, Optional): GA4セッションID。
        -   `form_id` (TEXT, Optional): フォーム識別ID。
        -   `submission_status` (TEXT, NOT NULL, DEFAULT 'new'): 問い合わせステータス。
        -   `status_change_reason` (TEXT, Optional): ステータス変更理由。

-   **`form_ga_configurations`**:
    -   **説明**: フォームごとのGoogle Analytics 4 Measurement Protocol設定（測定ID、APIシークレット）を保存します。
    -   **スキーマファイル**: `database/form_ga_configurations_schema.sql`
    -   **主要カラム**:
        -   `form_id` (TEXT, PK): フォーム識別ID。
        -   `ga4_measurement_id` (TEXT NOT NULL): GA4測定ID。
        -   `ga4_api_secret` (TEXT NOT NULL): GA4 APIシークレット (DB内では暗号化推奨)。
        -   `description` (TEXT, Optional): 設定の説明。
        -   `created_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()): 作成日時。
        -   `updated_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()): 最終更新日時 (トリガーで自動更新)。

## 7. Google Analytics 4 (GA4) 連携 (GA4 Integration)

このバックエンドは、GA4のMeasurement Protocol (v2) を使用して、リードジェネレーションに関連するイベントをGoogle Analyticsに送信します。

### 設定方法
1.  **GA4プロパティでの準備**: GA4プロパティで「測定ID」と「APIシークレット」を取得します。
2.  **バックエンドへの設定登録**: `/api/v1/ga_configurations` エンドポイント（「5.4. GA4設定管理」参照）を使用して、フォームごと (`form_id` 単位) に取得した測定IDとAPIシークレットを登録します。

### 送信される主要イベント
-   **`generate_lead`**:
    -   **トリガー**: `/submit` エンドポイントでフォーム送信が正常に処理された際。
    -   **主なパラメータ**: `client_id`, `session_id` (フォームから提供された場合), `form_id` (カスタムパラメータ `event_label` として), `event_category: "contact_form"`。
-   **ステータス変更連動イベント**: `/api/v1/submissions/{submission_id}/status` エンドポイントで問い合わせステータスが変更された際。
    -   `contacted` 時: `working_lead` (パラメータ `lead_status: "contacted"`)
    -   `qualified` 時: `qualify_lead`
    -   `converted` 時: `close_convert_lead` (パラメータ `transaction_id` に `submission_id` を使用)
    -   `unconverted` 時: `lead_unconverted` (カスタムイベント)
    -   `disqualified` 時: `lead_disqualified` (カスタムイベント)
    -   これらのイベントにも `client_id`, `session_id`, `form_id` などの関連情報が付与されます。

全てのイベントには、固定値として `value: 0`, `currency: "JPY"` が設定されます。
イベント送信処理は `backend/services/ga4_mp_service.py` の `send_ga4_event` 関数が担当します。

## 8. テスト (Testing)

バックエンドのユニットテストおよび結合テストは `pytest` を使用して実行します。

### テストの実行
1.  上記「ローカル開発環境セットアップ」が完了していることを確認してください。
2.  `pytest` が `requirements.txt` に含まれており、インストールされていることを確認してください。
3.  プロジェクトのルートディレクトリで以下のコマンドを実行します。
    ```bash
    pytest backend/tests/
    ```
    または、特定のテストファイルのみを実行する場合:
    ```bash
    pytest backend/tests/test_contact_api.py
    pytest backend/tests/test_form_ga_config_api.py
    pytest backend/tests/test_submission_api.py
    ```

### テストファイルの場所
テストコードは `backend/tests/` ディレクトリに配置されています。

-   `test_contact_api.py`: `/submit`, `/chat` エンドポイントおよび関連機能のテスト。
-   `test_form_ga_config_api.py`: GA4設定管理API (`/api/v1/ga_configurations/...`) のテスト。
-   `test_submission_api.py`: 問い合わせステータス更新API (`/api/v1/submissions/.../status`) および一覧取得APIのテスト。
-   `test_ai_agent.py`: AI Agentの応答生成ロジック（リトライ処理含む）のテスト。

テストは、サービス層のロジックや外部依存（Supabaseクライアントなど）をモックして、各コンポーネントの動作を独立して検証することに主眼を置いています。

## 9. その他 (Miscellaneous)

-   (現時点では特記事項なし)

```
