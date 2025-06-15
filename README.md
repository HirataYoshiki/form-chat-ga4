# 📝 AI搭載型お問い合わせフォーム＆RAGシステム基盤

**1行のコードでWebサイトに埋め込み可能なお問い合わせフォームウィジェットと、テナントごとのRAG (Retrieval Augmented Generation) システムを組み合わせた顧客対応ソリューション**

本プロジェクトは、Webサイト訪問者からの問い合わせを効率的に処理し、AIによる自動応答やナレッジベース検索を通じて顧客満足度を向上させることを目的とした包括的なシステムです。お問い合わせフォーム、AIチャットボット、テナント管理、RAGドキュメント管理、GA4連携などの機能を提供します。

## ✨ 特徴

- 🚀 **簡単導入**: `<script>` タグ1つでお問い合わせフォームウィジェットをWebサイトに即座に導入可能。
- 🤖 **AIチャットボット**: Gemini API (または指定のLLM) を利用したAIチャットボットが一次対応。テナント固有の情報をRAGシステムから参照して回答精度を向上。
- 🧑‍💼 **テナント管理**: スーパーユーザーがテナント（顧客企業やサービス単位など）を管理可能。テナントごとにドメイン設定やRAG用ドキュメントを管理。
- 📄 **RAGシステム**: テナントごとに専用のナレッジベースを構築。アップロードされたドキュメント（PDF, TXT, Markdownなど）を基に、AIが関連情報を検索・参照して回答。
- 📱 **レスポンシブ対応**: お問い合わせフォームはモバイル・デスクトップに自動調整。
- 🎨 **カスタマイズ可能**: フォームウィジェットのテーマ、表示位置、文言などを設定可能。
- ✅ **リアルタイムバリデーション**: フォーム入力時のエラーを即座に表示。
- 🛡️ **スタイル隔離**: フォームウィジェットはShadow DOMで既存サイトのスタイルと干渉しない設計。
- 💾 **データ永続化**: Supabase (PostgreSQL) を利用して、問い合わせデータ、テナント情報、GA4設定、RAG関連ファイルメタデータを安全に保管。
- 📈 **高度なGA4連携**:
    - Measurement Protocol経由でGoogle Analytics 4へ各種イベント（リード獲得、ステータス変更など）をサーバーサイドから正確に送信。
    - フォームごと、テナントごとの詳細な効果測定や顧客行動分析が可能。
- 🔒 **認証と認可**:
    - テナント管理画面はSupabase Auth（メール・パスワード認証）を利用。
    - APIエンドポイントはJWTトークンで保護。
    - ロールベースアクセス制御（スーパーユーザー、テナントユーザーなど - 現在は主にスーパーユーザー向け機能）。
- ⚡ **開発・運用効率**:
    - Docker Composeによる容易な開発環境構築。
    - FastAPI (Python) による効率的なバックエンドAPI開発。
    - React (TypeScript, Vite) によるモダンなフロントエンド開発。
    - 詳細なAPIドキュメント (Swagger UI)。

## 🚀 クイックスタート

### 1. 基本的な埋め込み

お客様のサイトに以下の1行を追加するだけ：

```html
<script src="https://yourservice.com/contact-widget.js" data-form-id="default-form"></script>
```

### 2. カスタマイズした埋め込み

```html
<script src="https://yourservice.com/contact-widget.js" 
        data-form-id="product-inquiry"
        data-theme="dark"
        data-position="bottom-left"
        data-title="製品について"
        data-button-text="製品を問い合わせる"></script>
```

## 📋 設定オプション

| オプション | 説明 | デフォルト値 | 例 |
|-----------|------|-------------|-----|
| `data-form-id` | フォームID（必須） | - | `"default-form"` |
| `data-api-endpoint` | APIエンドポイント | 本番URL | `"https://api.example.com"` |
| `data-theme` | テーマ | `"light"` | `"light"` / `"dark"` |
| `data-position` | 表示位置 | `"bottom-right"` | `"bottom-right"` / `"bottom-left"` / `"center"` |
| `data-title` | フォームタイトル | `"お問い合わせ"` | `"製品について"` |
| `data-button-text` | ボタンテキスト | `"お問い合わせ"` | `"今すぐ相談"` |

## 💻 JavaScript API

プログラマティックな制御も可能：

```javascript
// フォームを表示
window.ContactFormWidget.init({
  formId: 'dynamic-form',
  theme: 'light',
  position: 'center',
  title: 'お問い合わせ',
  buttonText: 'お問い合わせする'
});

// フォームを非表示
window.ContactFormWidget.destroy();
```

## 🔧 開発環境セットアップ

### 前提条件

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourcompany/contact-form-widget.git # Replace with your repo URL
cd contact-form-widget
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# .envファイルを編集してSupabaseの接続情報やその他のAPIキーを設定
# 例:
# SUPABASE_URL="YOUR_SUPABASE_URL"
# SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
# OPENAI_API_KEY="YOUR_OPENAI_API_KEY" # (AI Agent用、またはGeminiの代わりに)
# GEMINI_MODEL_NAME="gemini-1.5-flash-latest"
# # GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY" # (Gemini API用、ADCがなければ)
# # GA4関連のAPIキーと測定IDは、API経由でフォームごとに設定します。
```

### 3. 開発環境を起動

```bash
# Docker Composeで起動
make dev

# または手動で起動
docker-compose up --build
```

### 4. アクセス確認

- **フロントエンド（管理画面）**: http://localhost:3000 (ログイン: `/login`, テナント管理: `/admin/tenants`)
- **ウィジェット開発サーバー**: http://localhost:5173 (サンプルページでウィジェット動作確認)
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント (Swagger UI)**: http://localhost:8000/docs

## 🔗 APIエンドポイント概要

主要なAPIエンドポイントは以下の通りです。詳細は `/docs` (Swagger UI) を参照してください。

### 一般向けAPI
-   **`POST /submit`**:
    -   **目的**: お問い合わせフォームからのデータを受け付け、データベースに保存します。
    -   **認証**: 不要（またはAPIキーベースの簡易認証を推奨）。
    -   **主要な処理**: データバリデーション、データベース保存、GA4への `generate_lead` イベント送信（フォームにGA4設定がされている場合）。
    -   **レスポンス**: 保存された問い合わせデータ。
-   **`POST /chat`**:
    -   **目的**: AIチャットボットとの対話メッセージを処理します。テナントIDに基づいてRAG検索を行い、関連情報をコンテキストに含めます。
    -   **認証**: 必要（Supabase JWTトークン、ユーザーがテナントに紐付いていること）。
    -   **レスポンス**: AIからの返信メッセージ、セッションID、追加アクション要求フラグ。

### 管理系API (要スーパーユーザー認証)
#### テナント管理 (Tenant Management)
-   **`POST /api/v1/tenants`**:
    -   **目的**: 新規テナントを作成します。
    -   **認証**: スーパーユーザー。
    -   **リクエストボディ**: 会社名、ドメインなど。
    -   **レスポンス**: 作成されたテナント情報。
-   **`GET /api/v1/tenants`**:
    -   **目的**: テナントのリストを取得します（ページネーション対応済み）。
    -   **認証**: スーパーユーザー。
    -   **レスポンス**: テナントのリストと総数。
-   **`GET /api/v1/tenants/{tenant_id}`**:
    -   **目的**: 指定されたテナントIDの詳細情報を取得します。
    -   **認証**: スーパーユーザー。
    -   **レスポンス**: テナント詳細情報。
-   **`PUT /api/v1/tenants/{tenant_id}`**:
    -   **目的**: 指定されたテナントIDの情報を更新します。
    -   **認証**: スーパーユーザー。
    -   **リクエストボディ**: 更新するテナント情報。
    -   **レスポンス**: 更新されたテナント情報。
-   **`DELETE /api/v1/tenants/{tenant_id}`**:
    -   **目的**: 指定されたテナントIDを論理削除または物理削除します（実装による）。
    -   **認証**: スーパーユーザー。
    -   **レスポンス**: 成功メッセージ。

#### RAGファイル管理 (RAG File Management) - テナントごと
-   **`POST /api/v1/tenants/{tenant_id}/rag_files`**:
    -   **目的**: 指定されたテナントのRAGシステム用ファイルをアップロードします。複数ファイル対応。
    -   **認証**: スーパーユーザー（またはテナント管理者）。
    -   **リクエストボディ**: `multipart/form-data` 形式のファイルリスト。
    -   **レスポンス**: アップロードされた各ファイルの処理ID、ファイル名、ステータス確認用URLなど。
-   **`GET /api/v1/tenants/{tenant_id}/rag_files`**:
    -   **目的**: 指定されたテナントにアップロード済みのRAGファイルリストを取得します。
    -   **認証**: スーパーユーザー（またはテナント管理者）。
    -   **レスポンス**: ファイルリスト（ファイル名、種類、サイズ、アップロード日時、処理ステータスなど）。
-   **`GET /api/v1/tenants/{tenant_id}/rag_files/{processing_id}`**:
    -   **目的**: 指定されたファイル（処理IDで指定）の詳細情報や処理ステータスを取得します。 (現状は`rag_processing_jobs`エンドポイントでステータス確認)
    -   **認証**: スーパーユーザー（またはテナント管理者）。
    -   **レスポンス**: ファイル詳細情報。
-   **`DELETE /api/v1/tenants/{tenant_id}/rag_files/{processing_id}`**:
    -   **目的**: 指定されたファイル（処理IDで指定）をRAGシステムから削除します（メタデータおよび関連インデックスの削除）。
    -   **認証**: スーパーユーザー（またはテナント管理者）。
    -   **レスポンス**: 成功メッセージ (HTTP 204 No Content)。
-   **`GET /api/v1/rag_processing_jobs/{processing_id}/status`**:
    -   **目的**: 指定された処理IDのファイル処理ジョブのステータス（例: Pending, Processing, Completed, Failed）を確認します。
    -   **認証**: スーパーユーザー（またはテナント管理者）。
    -   **レスポンス**: ジョブステータス、エラーメッセージ（あれば）。

#### GA4設定管理 (GA4 Configuration Management)
-   **`POST /api/v1/ga_configurations`**:
    -   **目的**: 新しいフォームに対するGA4設定（測定ID、APIシークレット等）を登録します。テナントIDとフォームIDに紐づきます。
    -   **認証**: スーパーユーザー。
    -   **レスポンス**: 登録されたGA4設定情報。
-   **`GET /api/v1/ga_configurations`**:
    -   **目的**: 登録されている全てのフォームGA4設定をリストします。
    -   **認証**: スーパーユーザー。
-   **`GET /api/v1/ga_configurations/{tenant_id}/{form_id}`**:
    -   **目的**: 指定されたテナントIDとフォームIDのGA4設定を取得します。
    -   **認証**: スーパーユーザー。
-   **`PUT /api/v1/ga_configurations/{tenant_id}/{form_id}`**:
    -   **目的**: 指定されたテナントIDとフォームIDのGA4設定を更新します。
    -   **認証**: スーパーユーザー。
-   **`DELETE /api/v1/ga_configurations/{tenant_id}/{form_id}`**:
    -   **目的**: 指定されたテナントIDとフォームIDのGA4設定を削除します。
    -   **認証**: スーパーユーザー。

#### 問い合わせ管理 (Submission Management)
-   **`PATCH /api/v1/submissions/{submission_id}/status`**:
    -   **目的**: 指定された問い合わせ (`submission_id`) のステータスを更新します（例: "新規", "対応中", "完了"）。
    -   **認証**: スーパーユーザー（または担当者）。
    -   **レスポンス**: 更新された問い合わせ情報。ステータス変更に応じてGA4イベントも送信。

#### ユーザー管理 (User Management)
-   **`GET /api/v1/users/me`**:
    -   **目的**: 認証済みユーザー自身のプロファイル情報（`id`, `email`, `app_role`, `tenant_id`, `full_name` など）を取得します。
    -   **認証**: 必要（Supabase JWTトークン）。
    -   **レスポンス**: ユーザープロファイル情報を含むJSONオブジェクト。

## 📁 プロジェクト構成

```
contact-form-widget/
├── frontend/                          # React フロントエンド (Vite, TypeScript)
│   ├── public/                        # 静的アセット
│   └── src/
│       ├── components/                # Reactコンポーネント (各ページ、UI部品)
│       ├── contexts/                  # Reactコンテキスト (例: AuthContext)
│       ├── services/                  # APIクライアントなど (api.ts, supabaseClient.ts)
│       ├── App.tsx                    # メインアプリケーションコンポーネント、ルーティング
│       └── main.tsx                   # エントリーポイント
├── backend/                           # FastAPI バックエンド (Python)
│   ├── routers/                       # APIルーター (各機能ごと)
│   │   ├── form_ga_config_router.py   # GA4設定管理APIルーター
│   │   ├── submission_router.py       # 問い合わせステータス管理APIルーター
│   │   ├── tenant_router.py           # テナント管理APIルーター
│   │   ├── rag_router.py              # RAGファイル管理APIルーター
│   │   └── user_router.py             # ユーザー情報APIルーター
│   ├── services/                      # ビジネスロジック (各機能ごと)
│   │   ├── form_ga_config_service.py
│   │   ├── ga4_mp_service.py          # GA4 Measurement Protocol イベント送信サービス
│   │   ├── submission_service.py
│   │   ├── tenant_service.py
│   │   └── rag_service.py             # RAGファイル処理、インデックス作成サービス
│   ├── models/                        # Pydanticモデル (APIリクエスト/レスポンス、DBモデル)
│   │   ├── ga4_config_models.py
│   │   ├── submission_models.py
│   │   ├── tenant_models.py
│   │   └── rag_models.py
│   ├── auth.py                        # 認証関連ロジック (JWT検証、ユーザー取得など)
│   ├── contact_api.py                 # FastAPIメインアプリケーション定義
│   ├── ai_agent.py                    # AIチャットボット、RAG検索ロジック (LLM連携)
│   ├── config.py                      # 環境変数・設定管理
│   ├── db.py                          # Supabaseクライアント初期化
│   └── requirements.txt               # Python依存関係
├── database/                          # Supabaseデータベーススキーマ
│   ├── contact_form_schema.sql        # 問い合わせデータテーブルスキーマ
│   └── form_ga_configurations_schema.sql # GA4設定テーブルスキーマ
│   └── tenants_schema.sql             # テナントテーブルスキーマ
│   └── rag_files_schema.sql           # RAGファイルメタデータテーブルスキーマ
├── examples/                          # 各プラットフォームでの使用例
│   ├── form_widget_loader.ts
│   └── usage_examples.html
├── docker-compose.yml                 # Docker Compose設定
├── Makefile                           # 開発用Makefile
└── README.md                          # 本ドキュメント
```

## 📈 GA4イベント連携と活用

本システムでは、Google Analytics 4 (GA4) との連携を重視し、顧客獲得からエンゲージメントまでの主要なタッチポイントでイベントを送信します。これにより、マーケティング効果の測定やユーザー行動の詳細な分析が可能になります。

### 送信される主なGA4イベント
-   **`generate_lead`**:
    -   **トリガー**: お問い合わせフォームが正常に送信された時。
    -   **目的**: 新規リード獲得のトラッキング。
    -   **主なパラメータ**: `form_id`, `tenant_id`, `event_category`, `event_label`。
-   **リードステータス変更イベント** (例):
    -   **`working_lead`**: 問い合わせ対応が開始された時（例: 管理画面でステータスを「対応中」に変更）。
    -   **`qualify_lead`**: リードが有望と判断された時。
    -   **`close_convert_lead`**: リードが成約に至った時。
    -   **`close_unconvert_lead`**: リードが失注した時。
    -   **トリガー**: 管理画面等で問い合わせのステータスが更新された時。
    -   **目的**: リードのファネル進捗状況をトラッキング。
    -   **主なパラメータ**: `submission_id`, `new_status`, `previous_status`, `tenant_id`。
-   **RAGシステム利用イベント** (検討中・将来的な拡張):
    -   `rag_query_success`: RAG検索が成功し、AIが情報を利用して回答した時。
    -   `rag_query_failed`: RAG検索が失敗した、または関連情報が見つからなかった時。
    -   `rag_document_view`: (もしプレビュー機能があれば) 管理者がRAGドキュメントを参照した時。

### 設定方法
-   GA4連携は、テナントごと・フォームごとに管理画面またはAPI経由で設定します。
-   必要な情報:
    -   GA4測定ID (Measurement ID, 例: `G-XXXXXXXXXX`)
    -   GA4 APIシークレット (Measurement Protocol API Secret)
-   これらの情報は、`ga_configurations` APIを通じて安全に保存・管理されます。

### 分析と活用
収集されたGA4イベントデータは、以下の分析や施策改善に活用できます。
-   **リード獲得チャネル分析**: どのフォームやキャンペーンが効果的にリードを獲得しているか。
-   **リード転換率分析**: 各ステータスへの移行率を分析し、ボトルネックを特定。
-   **顧客行動分析**: 問い合わせから成約までの平均所要時間、タッチポイントの分析。
-   **RAG効果測定**: (将来) RAGシステムがどの程度問い合わせ解決に貢献しているか。

## テナント管理画面 (Frontend)

このプロジェクトには、テナント情報をブラウザ上で管理するためのReactベースのフロントエンドアプリケーションが含まれています。

### 目的
スーパーユーザーがテナントの参照、作成、更新、削除 (CRUD) 操作、および各テナントに紐づくRAG用ドキュメントの管理を行うためのWebインターフェースを提供します。

### 技術スタック
- React (v18)
- TypeScript
- Vite (ビルドツール・開発サーバー)
- React Router (v6, ルーティング)
- Axios (HTTPクライアント)
- Supabase Client (`@supabase/supabase-js`) (認証、将来的にはデータアクセスも)

### 主な機能
- **テナント管理**:
    - テナントの一覧表示 (ページネーション対応)
    - 新規テナントの作成フォーム (会社名, ドメイン)
    - 既存テナントの編集フォーム
    - テナントの削除 (確認ダイアログ付き)
- **ユーザー認証**:
    - メールアドレスとパスワードによるログイン・ログアウト機能 (`/login`)。
    - 認証状態のグローバル管理 (`AuthContext.tsx`)。
- **アクセス制御**:
    - 管理機能へのアクセスは認証済みかつ「スーパーユーザー」ロールを持つユーザーに限定 (`ProtectedRoute.tsx`)。
    - 未認証ユーザーや権限のないユーザーはログインページやアクセス拒否画面にリダイレクト。
- **RAGファイル管理** (テナントごと):
    - 特定テナントのRAG用ドキュメントアップロードページ。
    - ファイル選択 (複数可、拡張子バリデーション: `.pdf`, `.txt`, `.md`, `.docx`, `.pptx`, `.xlsx`)。
    - アップロード実行と結果表示 (ファイル名、処理ID、ステータスURL)。
    - アップロード済みファイルの一覧表示 (ファイル名、種類、サイズ、アップロード日時、現在の処理ステータス)。
    - 一覧からのファイル削除機能 (確認ダイアログ付き)。
- **UI/UX**:
    - 各ページでのローディング・エラー表示。
    - 表形式データの表示、ホバーエフェクト。
    - フォーム入力時のバリデーション（一部）。

### 開発サーバーの起動方法
1.  `frontend` ディレクトリに移動します:
    ```bash
    cd frontend
    ```
2.  必要なパッケージをインストールします (初回のみ):
    ```bash
    npm install
    # または yarn install
    ```
3.  開発サーバーを起動します:
    ```bash
    npm run dev
    # または yarn dev
    ```
4.  ブラウザで `http://localhost:3000` (または `vite.config.ts` で設定したポート) を開きます。
    ログイン画面は `/login` で、テナント管理画面は `/admin/tenants` パスでアクセスできます。

開発サーバーは、バックエンドAPI (デフォルトで `http://localhost:8000` で実行されている想定) へのリクエストをプロキシするように設定されています (`vite.config.ts` を参照)。

### ディレクトリ構成のポイント
- `frontend/src/components/`: 主要なページコンポーネント (e.g., `TenantListPage.tsx`, `LoginPage.tsx`, `ProtectedRoute.tsx`, `RagFileManagementPage.tsx`)
- `frontend/src/contexts/AuthContext.tsx`: グローバルな認証状態管理 (Supabaseセッション、ユーザープロファイル、ロールなど)
- `frontend/src/api.ts`: バックエンドAPIと通信するための `axios` クライアントインスタンス (認証トークン自動付与)
- `frontend/src/supabaseClient.ts`: Supabaseクライアントの初期化
- `frontend/src/App.tsx`: アプリケーション全体のルーティング設定とプロバイダー設定

### 認証機能
テナント管理画面はSupabaseを利用したメールアドレスとパスワードによる認証機能を備えています。

-   **認証フロー**:
    1.  ユーザーは `/login` ページ (`LoginPage.tsx`) で認証情報を入力します。
    2.  `AuthContext.tsx` 内の `login` 関数がSupabaseの認証を実行します。
    3.  認証成功後、SupabaseからJWTトークンが発行され、セッション情報が確立されます。
    4.  `AuthContext.tsx` はセッション変更を検知し、バックエンドの `/api/v1/users/me` エンドポイントからユーザープロファイル（ロール情報を含む）を取得します。
    5.  取得したJWTトークンは、`api.ts` 内の `axios` インスタンス (`apiClient`) のリクエストインターセプターによって、以降のバックエンドAPIへのリクエストヘッダーに自動的に付与されます。
-   **状態管理 (`AuthContext.tsx`)**:
    -   グローバルな認証状態（Supabaseセッション、バックエンドから取得したユーザープロファイル `userProfile`、アプリケーションロール `appRole`、認証処理中のローディング状態 `authLoading`）を一元管理します。
    -   `login` および `logout` 関数を提供し、アプリケーション全体で利用可能にします。
-   **保護ルート (`ProtectedRoute.tsx`)**:
    -   `/admin/tenants` 以下のテナント管理関連のルートは `ProtectedRoute.tsx` によって保護されます。
    -   ユーザーが未認証の場合、または認証済みでも `appRole` が `'superuser'` でない場合は、それぞれログインページまたはアクセス拒否メッセージ（ホームページへのリンク付き）にリダイレクト/表示されます。
-   **Supabaseクライアント設定 (`supabaseClient.ts`)**:
    -   SupabaseのURLとanonキーは `frontend/src/supabaseClient.ts` ファイル内に直接記述されています。
    -   **注意**: **本番環境では、これらの値を環境変数（例: `.env` ファイル内の `VITE_SUPABASE_URL` および `VITE_SUPABASE_ANON_KEY`）として管理し、`import.meta.env.VITE_SUPABASE_URL` のようにアクセスすることを強く推奨します。** Viteプロジェクトでは、環境変数のプレフィックスに `VITE_` が必要です。
-   **APIクライアント (`api.ts`)**:
    -   `apiClient` (axiosインスタンス) はリクエストインターセプターを備えており、認証済みの場合は自動的にSupabaseから取得したJWTトークンを `Authorization: Bearer <token>` ヘッダーとして付加します。

#### RAGファイル管理

テナント管理画面には、特定のテナントに関連付けられたRAG (Retrieval Augmented Generation) システムで使用するドキュメントファイルをアップロード・管理する機能が含まれています。

-   **アクセス方法**:
    -   テナント一覧ページ (`/admin/tenants`) の各テナント行にある「RAG Files」ボタンから、該当テナントのRAGファイル管理ページ (`/admin/tenants/:tenantId/rag-files`) にアクセスできます。
-   **機能概要**:
    -   選択したテナントに対して、RAGシステムが参照するソースドキュメントをアップロードします。
    -   複数のファイルを一度に選択してアップロードすることが可能です。
    -   アップロードされたファイルの情報（ファイル名、処理ID、バックエンドでの処理状況を確認するためのステータスURLなど）がアップロード直後に表示されます。
    -   アップロード済みのファイル一覧がページに表示され、ファイル名、種類、サイズ、アップロード日時、現在の処理ステータス等を確認できます。
    -   一覧から不要なファイルを削除する機能があります（削除前に確認ダイアログが表示されます）。
-   **ファイルバリデーション**:
    -   フロントエンドでファイル選択時に拡張子バリデーションが行われます。現在許可されている拡張子は、`.pdf`, `.txt`, `.md`, `.docx`, `.pptx`, `.xlsx` です。これ以外のファイルタイプはアップロードできません。
-   **利用API**:
    -   ファイルのアップロードには、バックエンドの `POST /api/v1/tenants/{tenant_id}/rag_files` エンドポイントが使用されます。
-   **注意点**:
    -   ファイルのアップロード後、バックエンドでは非同期処理（ファイルの解析、インデックス作成など）が実行される場合があります。実際のファイル処理状況は、アップロード結果に表示される「ステータスURL」から確認してください。
    -   この機能は認証が必要であり、操作を行うユーザーは対象テナントに所属しているか、スーパーユーザーである必要があります。

## 🛠️ 利用可能なコマンド

```bash
make dev          # 開発環境起動 (Docker Compose)
make build        # 本番用ビルド (現状は主にフロントエンドのビルドを想定)
make test         # テスト実行 (未実装)
make clean        # Dockerコンテナ・ボリューム削除
make logs         # Dockerコンテナログ表示
make restart      # Dockerコンテナ再起動
```

## 🚀 デプロイ

デプロイ戦略はコンポーネントによって異なります。

### フロントエンド (テナント管理画面 - `frontend/`)
-   **Vercel**: 静的サイトとして簡単にデプロイ可能。
    ```bash
    cd frontend
    npm run build
    vercel --prod
    ```
-   **その他**: Netlify, AWS S3/CloudFront, GitHub Pagesなど。

### バックエンド (API - `backend/`)
-   **Railway**: Dockerfileベースでデプロイ可能。
    ```bash
    cd backend
    railway up # (railway CLI設定後)
    ```
-   **その他**: Google Cloud Run, AWS Fargate, Heroku (Dockerコンテナ対応)。

### データベース (Supabase)
-   Supabaseはクラウドサービスなので、[Supabase公式サイト](https://supabase.com)でプロジェクトを作成・設定します。
-   必要なテーブルスキーマは `database/` ディレクトリ内のSQLファイル (`contact_form_schema.sql`, `form_ga_configurations_schema.sql`, `tenants_schema.sql`, `rag_files_schema.sql` など) を参考に、SupabaseのSQLエディタで実行します。
-   取得したSupabase URLと各種キーをバックエンドおよびフロントエンドの環境変数に設定します。

## 📊 機能一覧

### コアウィジェット機能 (Contact Form Widget)
- [x] サイトへの1行埋め込み
- [x] 基本項目（名前・メール・会社・電話・メッセージ）
- [x] リアルタイムバリデーション
- [x] 送信中・完了状態の表示
- [x] レスポンシブデザイン
- [x] カスタマイズオプション (テーマ、位置、文言)
- [x] Shadow DOMによるスタイル隔離
- [ ] JavaScript APIによるプログラム制御 (一部実装、拡充予定)

### バックエンドAPI (`backend/`)
- [x] 問い合わせデータ受付・保存 (`/submit`)
- [x] AIチャットボット応答 (`/chat`, Gemini連携)
- **テナント管理API**:
    - [x] テナント作成 (`POST /api/v1/tenants`)
    - [x] テナント一覧取得 (`GET /api/v1/tenants`)
    - [x] テナント詳細取得 (`GET /api/v1/tenants/{tenant_id}`)
    - [x] テナント更新 (`PUT /api/v1/tenants/{tenant_id}`)
    - [x] テナント削除 (`DELETE /api/v1/tenants/{tenant_id}`)
- **RAGシステムAPI** (テナントごと):
    - [x] RAG用ファイルアップロード (`POST /api/v1/tenants/{tenant_id}/rag_files`)
    - [ ] アップロード済みファイル一覧表示 (`GET /api/v1/tenants/{tenant_id}/rag_files`) (API未実装)
    - [ ] ファイル処理ステータス確認 (`GET /api/v1/rag_processing_jobs/{processing_id}/status`) (API未実装)
    - [ ] RAG用ファイル削除 (`DELETE /api/v1/tenants/{tenant_id}/rag_files/{file_id}`) (API未実装)
    - [ ] RAGドキュメント検索 (AI Agent内で利用)
- **GA4設定管理API**:
    - [x] GA4設定登録・取得・更新・削除
- **問い合わせ管理API**:
    - [x] 問い合わせステータス更新 (`PATCH /api/v1/submissions/{submission_id}/status`)
- **ユーザー認証・プロファイルAPI**:
    - [x] ユーザープロファイル取得 (`GET /api/v1/users/me`)
    - [x] Supabase Auth連携によるJWT認証

### フロントエンド管理画面 (`frontend/`)
- **テナント管理**:
    - [x] テナント一覧表示・作成・編集・削除ページ
- **RAGファイル管理**:
    - [x] テナントごとのRAGファイルアップロードUI (拡張子バリデーション付き)
    - [ ] アップロード済みファイル一覧・ステータス表示 (UI未実装)
- **ユーザー認証**:
    - [x] ログインページ (`/login`)
    - [x] ログアウト機能
    - [x] 認証状態グローバル管理 (`AuthContext`)
- **アクセス制御**:
    - [x] スーパーユーザー専用ルート保護 (`ProtectedRoute`)
- [ ] GA4設定管理UI (未実装)
- [ ] 問い合わせ一覧・詳細表示・ステータス更新UI (未実装)
- [ ] ダッシュボード (未実装)

### GA4連携機能
- [x] フォーム送信時 `generate_lead` イベント送信
- [x] 問い合わせステータス変更時に関連イベント送信
- [x] サーバーサイド送信 (Measurement Protocol)
- [x] フォームごとのGA4設定管理 (APIレベル)

### RAGシステム (Retrieval Augmented Generation)
- [x] テナントごとのドキュメントベース (Supabase Vector/pgvector)
- [x] ドキュメントアップロードとチャンキング・インデックス作成 (基本的なファイルタイプ: PDF, TXT, MD)
- [x] AIチャット応答時のコンテキスト検索・注入
- [ ] 対応ファイルタイプの拡充 (.docx, .pptx, .xlsx など) - フロントエンドでは選択可能だがバックエンド処理は未実装
- [ ] インデックス管理・再構築機能 (API/UI)

### 通知機能 (将来的な拡張)
- [ ] 管理者メール通知
- [ ] 顧客自動返信メール
- [ ] Slack通知

---

**Made with ❤️ for small businesses and developers**
