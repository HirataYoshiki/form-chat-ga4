# Contact Form Widget - Backend

このドキュメントは、Contact Form Widgetプロジェクトのバックエンドアプリケーションに関する技術的な詳細、セットアップ手順、API仕様について説明します。

## 1. 概要 (Overview)

バックエンドアプリケーションは、Contact Form Widgetから送信されるお問い合わせデータの受付、保存、および管理機能を提供します。マルチテナントアーキテクチャを採用しており、クライアント企業（テナント）ごとにデータを分離・管理できます。また、AIチャットボット機能、Google Analytics 4 (GA4) へのイベント送信機能も担います。

主な機能は以下の通りです。

-   **マルチテナント対応**: 各テナントは自身のフォーム、問い合わせデータ、GA4設定を独立して管理できます。
-   **フォームデータ処理**: フロントエンドウィジェットからの問い合わせデータ（名前、メールアドレス、メッセージ等）を受信し、テナントごとにデータベースに保存します。
-   **AIチャットボット連携**: ユーザーからの質問に対してAI（Geminiモデルを利用）が応答するチャット機能を提供します。AIとの通信時には、設定に基づいたリトライ処理が実行され、一時的な通信エラーに対する堅牢性を高めています。
-   **GA4 Measurement Protocol連携**: フォーム送信時や問い合わせステータス変更時に、リードジェネレーション関連のイベントをGA4に送信します。この機能もテナントごとに設定可能です。
-   **GA4設定管理**: テナント内のフォームごとにGA4の測定IDとAPIシークレットを設定・管理するためのAPIを提供します。
-   **問い合わせステータス管理**: 問い合わせの進捗ステータス（新規、連絡済み、成約など）を管理し、ステータス変更を行うためのAPIをテナントごとに提供します。
-   **テナント管理 (スーパーユーザー限定)**: スーパーユーザー向けに、テナント（クライアント企業アカウント）の作成、一覧表示、更新、削除を行うAPIを提供します。

このバックエンドは、フロントエンドの埋め込みウィジェットと連携して動作するように設計されています。認証はSupabase Authを利用したJWTベースで行われ、ユーザーロール（`user`, `superuser`）に応じたアクセス制御が適用されます。

## 2. 技術スタック (Tech Stack)

バックエンドシステムは以下の主要な技術で構成されています。

-   **プログラミング言語**: Python 3.11+
-   **フレームワーク**: FastAPI - 高パフォーマンスな非同期Webフレームワーク。
-   **データベース**: Supabase (PostgreSQL) - `supabase-py` クライアントライブラリを通じて連携。
-   **データバリデーション**: Pydantic V2 - APIリクエスト/レスポンスの型定義とバリデーション。
-   **HTTPクライアント**: `httpx` - GA4 Measurement Protocol APIなど、外部APIとの非同期通信に使用。
-   **AI連携**: Google Agent Development Kit (ADK) - Geminiモデルを利用したAIエージェント機能。
-   **認証**: Supabase Auth (JWTベースの認証)
-   **JWT処理**: python-jose[cryptography] (JWTのデコードと検証)
-   **リトライ処理**: tenacity - AI Agentなどの外部API呼び出しにおけるリトライ処理に使用。
-   **ASGIサーバー**: Uvicorn - FastAPIアプリケーションの実行。
-   **依存関係管理**: `pip` と `requirements.txt`。

## 3. プロジェクト構造 (Project Structure)

`backend/` ディレクトリ内の主要なサブディレクトリとファイルの役割は以下の通りです。

```
backend/
├── .gitkeep                     # 空ディレクトリをGit管理するためのプレースホルダ (あれば)
├── ai_agent.py                  # AIチャットボットのロジック（ADK、Gemini連携）
├── auth.py                      # JWT認証・認可ロジック
├── config.py                    # 環境変数管理（Pydantic Settingsによる設定読み込み）
├── contact_api.py               # メインFastAPIアプリケーション定義、主要エンドポイント（/submit, /chat）、ルーター登録
├── db.py                        # Supabaseクライアントの初期化とFastAPI依存性注入の提供
├── models/                      # Pydanticモデル定義用ディレクトリ
│   ├── ga4_config_models.py     # GA4設定管理API用のリクエスト/レスポンスモデル
│   ├── submission_models.py     # 問い合わせステータス更新API用のリクエストモデル
│   └── tenant_models.py         # テナント管理API用のリクエスト/レスポンスモデル
├── requirements.txt             # Pythonの依存パッケージリスト
├── routers/                     # APIルーターモジュール用ディレクトリ
│   ├── form_ga_config_router.py # GA4設定管理APIのエンドポイント定義
│   ├── submission_router.py     # 問い合わせステータス更新APIのエンドポイント定義
│   └── tenant_router.py         # テナント管理APIのエンドポイント定義
├── services/                    # ビジネスロジック層用ディレクトリ
│   ├── form_ga_config_service.py# GA4設定のCRUD処理ロジック
│   ├── ga4_mp_service.py        # GA4 Measurement Protocol APIへのイベント送信ロジック
│   ├── submission_service.py    # 問い合わせステータス更新処理ロジック
│   └── tenant_service.py        # テナント管理のCRUD処理ロジック
└── tests/                       # 自動テスト用ディレクトリ
    ├── test_contact_api.py      # /submit API (/chat APIは未実装) のテスト
    ├── test_form_ga_config_api.py # GA4設定管理APIのテスト
    ├── test_submission_api.py   # ステータス更新・一覧取得APIのテスト
    ├── test_ai_agent.py         # AI Agent関連ロジックのテスト
    └── test_tenant_api.py       # テナント管理APIのテスト
```

-   **`contact_api.py`**: FastAPIアプリケーションのインスタンス (`app`) を生成し、ミドルウェアの設定、主要なエンドポイント（`/submit`, `/chat`）、および各機能ルーターの登録を行います。認証機能 (`get_current_active_user`) は `auth.py` からインポートして利用します。
-   **`config.py`**: `.env` ファイルから環境変数を読み込み、アプリケーション全体で利用可能な設定オブジェクトを提供します。
-   **`db.py`**: Supabaseクライアントを初期化し、APIエンドポイントでデータベース接続を利用するためのFastAPI依存性注入関数 (`get_supabase_client`) を提供します。
-   **`auth.py`**: JWTベースの認証・認可処理を実装します。Supabaseから発行されたJWTの検証、ユーザー情報の取得（`public.users` テーブル経由）、ロールベースアクセス制御（RBAC）のための依存性注入関数 (`get_current_active_user`, `require_superuser_role` など) を提供します。
-   **`ai_agent.py`**: Google ADKを利用したAIチャットボットの応答生成ロジックを実装しています。
-   **`models/`**: APIのリクエストボディやレスポンスボディの構造を定義するPydanticモデルを格納します。`tenant_models.py` が追加されました。
-   **`routers/`**: 各機能グループに対応するAPIエンドポイント（パスオペレーション）を定義した `APIRouter` モジュールを格納します。`tenant_router.py` が追加されました。
-   **`services/`**: APIエンドポイントから呼び出されるビジネスロジックやデータベース操作をカプセル化した関数/クラスを格納します。`tenant_service.py` が追加されました。
-   **`tests/`**: `pytest` を利用した自動テストコードを格納します。各APIルーターや主要なサービスに対応するテストファイルが含まれます。`test_tenant_api.py` が追加されました。

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

        # --- Supabase Auth Settings (JWT検証に必須) ---
        # SupabaseプロジェクトのJWKS URI (例: https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json)
        SUPABASE_JWKS_URI="YOUR_SUPABASE_JWKS_URI"
        # Supabase JWTの期待されるAudience (通常 'authenticated')
        SUPABASE_JWT_AUDIENCE="authenticated"
        # オプション: JWTのIssuerを明示的に設定する場合 (通常 SUPABASE_URL + "/auth/v1" から導出可能)
        # SUPABASE_JWT_ISSUER="YOUR_SUPABASE_ISSUER_URL"

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
    (注意: 実際のファイル名はプロジェクトに合わせて確認してください。ファイル名に含まれる番号はマイグレーションの推奨適用順序を示します。)
    1.  `database/0001_tenants_schema.sql` (テナント管理用テーブル `tenants` 作成)
    2.  `database/0002_user_profiles_schema.sql` (`public.users` プロファイルテーブル作成、`auth.users` と連携、`tenants` とのFK設定)
    3.  `database/0003_contact_form_submissions_schema.sql` (旧 `contact_form_schema.sql` - 問い合わせ保存用テーブル `contact_submissions` 作成、`tenant_id` カラム追加とFK設定含む)
    4.  `database/0004_form_ga_configurations_schema.sql` (旧 `form_ga_configurations_schema.sql` - フォームごとのGA4設定用テーブル `form_ga_configurations` 作成、`tenant_id` カラム追加とFK設定含む)
    5.  以下のSQL (または各テーブル作成スキーマに統合されていることを確認) を実行して `contact_submissions` およびその他の関連テーブルに `updated_at` カラムと自動更新トリガーを追加:
        ```sql
        -- Add updated_at column and auto-update trigger to contact_submissions table (example)
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
        (同様のトリガーを `tenants`, `users`, `form_ga_configurations` にも設定することを推奨します。)

6.  **開発サーバーの起動**:
    プロジェクトのルートディレクトリから（または `PYTHONPATH` が適切に設定されていれば `backend` ディレクトリから）以下のコマンドを実行します。
    ```bash
    uvicorn backend.contact_api:app --reload --port 8000
    ```
    `--reload` オプションにより、コード変更時にサーバーが自動的に再起動します。

7.  **APIドキュメントへのアクセス**:
    サーバー起動後、ブラウザで http://localhost:8000/docs にアクセスすると、Swagger UIによるAPIドキュメントが表示され、各エンドポイントを試すことができます。 http://localhost:8000/redoc でもRedoc形式のドキュメントが確認できます。

## 5. 認証・認可 (Authentication & Authorization)

バックエンドAPIの保護されたエンドポイントへのアクセスには、JWT (JSON Web Token) を使用した認証が必要です。

### 認証フロー
1.  **ユーザー認証**: フロントエンドアプリケーションまたはクライアントは、Supabase Auth (例: `supabase-js`ライブラリ) を使用してユーザーのログイン処理を行います。
2.  **JWT取得**: 認証成功後、Supabase AuthからJWT（アクセストークン）が発行されます。
3.  **APIリクエスト**: 保護されたAPIエンドポイントへのリクエスト時、このJWTを `Authorization` HTTPヘッダーに `Bearer <token>` の形式で含めて送信します。

### JWT検証 (バックエンド)
-   バックエンド (`auth.py` モジュールの `get_current_active_user` 依存性注入関数内) は、受け取ったJWTを検証します。
-   検証には、SupabaseプロジェクトのJWKS (JSON Web Key Set) URI (`SUPABASE_JWKS_URI` 環境変数で設定) から取得した公開鍵セットを使用します。
-   JWTの署名、有効期限、発行者 (issuer - `SUPABASE_URL` から派生)、対象者 (audience - `SUPABASE_JWT_AUDIENCE` 環境変数で設定) が検証されます。
-   検証成功後、トークン内のユーザーID (`sub` クレーム) を使用して、`public.users` テーブルからユーザープロファイル情報（`app_role`, `tenant_id` など）を取得します。
-   これらの情報を含む `AuthenticatedUser` オブジェクトが、保護されたエンドポイント関数に注入されます。

### ロールベースアクセス制御 (RBAC)
-   **`app_role`**: ユーザープロファイルに格納されるロール（例: `user`, `admin`, `superuser`）。
-   **`user` ロール**: 通常のテナントユーザー。自身のテナントに関連するデータ（フォーム設定、問い合わせデータなど）へのアクセスが許可されます。
-   **`superuser` ロール**: システム管理者。テナント作成・管理など、システム全体に関わる操作が許可されます。
-   各APIルーターまたは個別のエンドポイントで、必要なロールを持つユーザーのみがアクセスできるように制御されます（例: `tenant_router.py` の `require_superuser_role` 依存性）。

## 6. APIエンドポイント詳細 (API Endpoints)

バックエンドアプリケーションは以下の主要なAPIエンドポイントを提供します。
詳細なリクエスト/レスポンスのスキーマやパラメータについては、サーバー起動後に `/docs` (Swagger UI) または `/redoc` (Redoc) でご確認ください。

### 6.1. フォーム送信 (Form Submission)

-   **`POST /submit`**
    -   **説明**: フロントエンドウィジェットからのお問い合わせデータを受け付け、データベースに保存します。保存成功後、GA4が設定されていれば `generate_lead` イベントを送信します。
    -   **認証**: 不要 (通常、公開エンドポイント)
    -   **リクエストボディ例**:
        ```json
        {
          "name": "山田 太郎",
          "email": "yamada.taro@example.com",
          "message": "製品Aについて詳しく知りたいです。",
          "tenant_id": "your-tenant-uuid-here",
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
          "tenant_id": "your-tenant-uuid-here",
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

### 6.2. AIチャット (AI Chat)

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

### 6.3. 問い合わせデータ一覧取得 (List Submissions)

-   **`GET /api/v1/submissions`**
    -   **説明**: 問い合わせデータの一覧を、指定されたフィルター条件、ページネーション、ソート順に基づいて取得します。
    -   **認証**: 必要 (テナントユーザーは自身のテナントのデータのみアクセス可能)。
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
              "tenant_id": "your-tenant-uuid-here",
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
        -   `403 Forbidden`: ユーザーがテナントに紐付いていない場合。
        -   `422 Unprocessable Entity`: クエリパラメータのバリデーションエラー。
        -   `503 Service Unavailable`: データベースクライアント未初期化など。
        -   `500 Internal Server Error`: その他のサーバー内部エラー。

### 6.4. GA4設定管理 (GA4 Form Configurations)

これらのエンドポイントは、テナント内のフォームごとのGA4測定IDとAPIシークレットを管理します。
**認証**: 必要 (テナントユーザーは自身のテナントの設定のみ管理可能)。

-   **`POST /api/v1/ga_configurations/{form_id}`**:
    -   **説明**: 指定された `form_id` に対して新しいGA4設定を登録します。
    -   **成功レスポンス (201 Created)**: 作成されたGA4設定情報。
    -   **主なエラーステータス**: `409 Conflict` (指定`form_id`が既に存在する場合), `403`, `422`, `500`, `503`。

-   **`GET /api/v1/ga_configurations`**:
    -   **説明**: 認証ユーザーのテナントに登録されている全てのフォームGA4設定をリストします（ページネーション対応: `skip`, `limit` クエリパラメータ）。
    -   **成功レスポンス (200 OK)**: GA4設定のリスト。

-   **`GET /api/v1/ga_configurations/{form_id}`**:
    -   **説明**: 指定された `form_id` のGA4設定を取得します。
    -   **成功レスポンス (200 OK)**:該当するGA4設定情報。
    -   **主なエラーステータス**: `404 Not Found`。

-   **`PUT /api/v1/ga_configurations/{form_id}`**:
    -   **説明**: 指定された `form_id` のGA4設定を更新します。
    -   **成功レスポンス (200 OK)**: 更新されたGA4設定情報。
    -   **主なエラーステータス**: `404 Not Found`, `422`, `500`, `503`。

-   **`DELETE /api/v1/ga_configurations/{form_id}`**:
    -   **説明**: 指定された `form_id` のGA4設定を削除します。
    -   **成功レスポンス (204 No Content)**。
    -   **主なエラーステータス**: `404 Not Found`。

### 6.5. 問い合わせステータス更新 (Submission Status Update)

-   **`PATCH /api/v1/submissions/{submission_id}/status`**
    -   **説明**: 指定された問い合わせ (`submission_id`) のステータス (`submission_status`と任意で`status_change_reason`) を更新します。ステータス変更に応じて、GA4イベントが送信されます。
    -   **認証**: 必要 (ユーザーは自身のテナント内の問い合わせのみ更新可能)。
    -   **リクエストボディ例**:
        ```json
        {
          "new_status": "converted",
          "reason": "Lead successfully closed."
        }
        ```
    -   **成功レスポンス例 (200 OK)**: 更新された問い合わせレコード全体。
    -   **主なエラーステータス**: `404 Not Found` (submission_idが見つからない、または他テナントのデータ), `403`, `422`, `500`, `503`。

### 6.6. テナント管理 (Tenant Management - Superuser Only)
-   **`POST /api/v1/tenants`**: 新規テナント作成。
-   **`GET /api/v1/tenants`**: テナント一覧取得。
-   **`GET /api/v1/tenants/{tenant_id}`**: 特定テナント情報取得。
-   **`PUT /api/v1/tenants/{tenant_id}`**: テナント情報更新。
-   **`DELETE /api/v1/tenants/{tenant_id}`**: テナント削除（論理/物理）。
    -   **認証**: スーパーユーザーのみ（`require_superuser_role` 依存性により実施）。

## 7. データベーススキーマ概要 (Database Schema Overview)

バックエンドはSupabase (PostgreSQL) データベースを使用します。主要なテーブルは以下の通りです。
詳細なスキーマ定義はプロジェクトルートの `database/` ディレクトリ内の各SQLファイルを参照してください（ファイル名に注意し、マイグレーション順序に従ってください）。

-   **`tenants`**:
    -   **説明**: 各テナント（クライアント企業）の情報を格納します。`tenant_id` (UUID) が主キーです。
    -   **スキーマファイル**: `database/0001_tenants_schema.sql` (または同等の内容を含むファイル)
    -   **主要カラム**: `tenant_id`, `company_name`, `domain`, `is_deleted`, `created_at`, `updated_at`。

-   **`users` (in `public` schema, linked to `auth.users`)**:
    -   **説明**: アプリケーションユーザーのプロファイル情報。Supabaseの `auth.users` テーブルのレコードと `id` (UUID) で1対1に対応します。ユーザーは特定のテナントに所属し、アプリケーション固有のロール（`app_role`）を持ちます。
    -   **スキーマファイル**: `database/0002_user_profiles_schema.sql` (または同等の内容を含むファイル)
    -   **主要カラム**: `id` (FK to `auth.users.id`), `app_role` (`user`, `superuser`など), `tenant_id` (FK to `public.tenants.tenant_id`), `full_name`, `created_at`, `updated_at`。

-   **`contact_submissions`**:
    -   **説明**: お問い合わせフォームから送信されたデータをテナントごとに保存します。`tenant_id` カラムでテナントに紐付けられます。
    -   **スキーマファイル**: `database/0003_contact_form_submissions_schema.sql` (または同等の内容を含むファイル、`tenant_id` 追加済みであること)
    -   **主要カラム**: `id`, `created_at`, `updated_at`, `name`, `email`, `message`, `ga_client_id`, `ga_session_id`, `form_id`, `submission_status`, `status_change_reason`, `tenant_id`。

-   **`form_ga_configurations`**:
    -   **説明**: テナント内のフォームごとのGoogle Analytics 4 Measurement Protocol設定を保存します。`tenant_id` と `form_id` の複合主キーで管理されます。
    -   **スキーマファイル**: `database/0004_form_ga_configurations_schema.sql` (または同等の内容を含むファイル、`tenant_id` 追加済みであること)
    -   **主要カラム**: `tenant_id`, `form_id`, `ga4_measurement_id`, `ga4_api_secret`, `description`, `created_at`, `updated_at`。

## 8. Google Analytics 4 (GA4) 連携 (GA4 Integration)

このバックエンドは、GA4のMeasurement Protocol (v2) を使用して、リードジェネレーションに関連するイベントをGoogle Analyticsに送信します。各テナントは自身のGA4プロパティと連携できます。

### 設定方法
1.  **GA4プロパティでの準備**: GA4プロパティで「測定ID」と「APIシークレット」を取得します。
2.  **バックエンドへの設定登録**: `/api/v1/ga_configurations` エンドポイント（「6.4. GA4設定管理」参照）を使用して、テナント内のフォームごと (`form_id` 単位) に取得した測定IDとAPIシークレットを登録します。

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

## 9. テスト (Testing)

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
    pytest backend/tests/test_ai_agent.py
    pytest backend/tests/test_tenant_api.py
    ```

### テストファイルの場所
テストコードは `backend/tests/` ディレクトリに配置されています。

-   `test_contact_api.py`: `/submit`, `/chat` エンドポイントおよび関連機能のテスト。
-   `test_form_ga_config_api.py`: GA4設定管理API (`/api/v1/ga_configurations/...`) のテスト。
-   `test_submission_api.py`: 問い合わせステータス更新API (`/api/v1/submissions/.../status`) および一覧取得APIのテスト。
-   `test_ai_agent.py`: AI Agentの応答生成ロジック（リトライ処理含む）のテスト。
-   `test_tenant_api.py`: テナント管理API (`/api/v1/tenants/...`) のテスト。

テストは、サービス層のロジックや外部依存（Supabaseクライアントなど）をモックして、各コンポーネントの動作を独立して検証することに主眼を置いています。

## 10. その他 (Miscellaneous)

-   (現時点では特記事項なし)

```
