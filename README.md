# 📝 Contact Form Widget

**1行のコードで埋め込み可能なお問い合わせフォームウィジェット**

零細中小企業向けに設計された、簡単導入・高機能なお問い合わせフォームサービスです。

## ✨ 特徴

- 🚀 **1行埋め込み**: `<script>`タグ1つで即座に導入完了
- 📱 **レスポンシブ対応**: モバイル・デスクトップ自動調整
- 🎨 **カスタマイズ可能**: テーマ・位置・文言を自由設定
- ✅ **リアルタイムバリデーション**: 入力エラーを即座に表示
- 📧 **自動通知**: Slack・メール・自動返信に対応
- 🛡️ **スタイル隔離**: Shadow DOMで既存サイトと干渉しない
- 💾 **データ保存**: Supabase連携で確実にデータを保管
- 📈 **GA4連携**: Google Analytics 4へのイベント送信（Measurement Protocol経由）に対応し、リード獲得状況や顧客エンゲージメントをトラッキング。
- ⚡ **高速表示**: 最適化されたバンドルサイズ

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

## 🎯 使用例

### WordPress
```php
// functions.phpに追加
function add_contact_form_widget() {
    echo '<script src="https://yourservice.com/contact-widget.js" data-form-id="wordpress-form"></script>';
}
add_action('wp_footer', 'add_contact_form_widget');
```

### Shopify
```html
<!-- theme.liquidに追加 -->
<script src="https://yourservice.com/contact-widget.js" 
        data-form-id="shopify-form"
        data-title="商品について"></script>
```

### 条件付き表示
```javascript
// 10秒後に自動表示
setTimeout(() => {
  window.ContactFormWidget.init({
    formId: 'auto-popup',
    title: 'まだお探しですか？'
  });
}, 10000);
```

## 🔧 開発環境セットアップ

### 前提条件

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 1. リポジトリをクローン

```bash
git clone https://github.com/yourcompany/contact-form-widget.git
cd contact-form-widget
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# .envファイルを編集してSupabaseの接続情報やその他のAPIキーを設定
# 例:
# SUPABASE_URL="YOUR_SUPABASE_URL"
# SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
# GEMINI_MODEL_NAME="gemini-1.5-flash-latest"
# # GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY" # (AI Agent用、ADCがなければ)
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

- **フロントエンド（管理画面）**: http://localhost:3000
- **ウィジェット開発サーバー**: http://localhost:5173
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs

## 🔗 APIエンドポイント概要

主要なAPIエンドポイントは以下の通りです。詳細は `/docs` (Swagger UI) を参照してください。

-   **`POST /submit`**:
    -   お問い合わせフォームからのデータを受け付け、データベースに保存します。
    -   保存成功後、GA4に `generate_lead` イベントを送信します（フォームにGA4設定がされている場合）。
-   **`POST /chat`**:
    -   AIチャットボットとの対話メッセージを処理します。
-   **`POST /api/v1/ga_configurations`**:
    -   新しいフォームに対するGA4設定（測定ID、APIシークレット等）を登録します。
-   **`GET /api/v1/ga_configurations`**:
    -   登録されている全てのフォームGA4設定をリストします。
-   **`GET /api/v1/ga_configurations/{form_id}`**:
    -   指定された `form_id` のGA4設定を取得します。
-   **`PUT /api/v1/ga_configurations/{form_id}`**:
    -   指定された `form_id` のGA4設定を更新します。
-   **`DELETE /api/v1/ga_configurations/{form_id}`**:
    -   指定された `form_id` のGA4設定を削除します。
-   **`PATCH /api/v1/submissions/{submission_id}/status`**:
    -   指定された問い合わせ (`submission_id`) のステータスを更新します。
    -   ステータス変更に応じて、適切なイベントをGA4に送信します（フォームにGA4設定がされている場合）。
-   **`GET /api/v1/users/me`**:
    -   **目的**: 認証済みユーザー自身のプロファイル情報（`id`, `email`, `app_role`, `tenant_id`, `full_name` など）を取得します。
    -   **認証**: 必要（Supabase JWTトークン）。
    -   **レスポンス**: ユーザープロファイル情報を含むJSONオブジェクト。

## 📁 プロジェクト構成

```
contact-form-widget/
├── frontend/                          # React フロントエンド
│   └── src/ # ... (詳細は省略)
├── backend/
│   ├── routers/
│   │   ├── form_ga_config_router.py   # GA4設定管理APIルーター
│   │   └── submission_router.py       # 問い合わせステータス管理APIルーター
│   ├── services/
│   │   ├── form_ga_config_service.py  # GA4設定管理サービス
│   │   ├── ga4_mp_service.py          # GA4 MPイベント送信サービス
│   │   └── submission_service.py      # 問い合わせステータス管理サービス
│   ├── models/
│   │   ├── ga4_config_models.py       # GA4設定API用Pydanticモデル
│   │   └── submission_models.py       # 問い合わせステータスAPI用Pydanticモデル
│   ├── contact_api.py                 # FastAPIメインアプリケーション
│   ├── ai_agent.py                    # AIチャットボットロジック
│   ├── config.py                      # 環境変数・設定管理
│   ├── db.py                          # Supabaseクライアント初期化
│   └── requirements.txt               # Python依存関係
├── database/
│   ├── contact_form_schema.sql        # 問い合わせデータテーブルスキーマ
│   └── form_ga_configurations_schema.sql # GA4設定テーブルスキーマ (Added)
├── examples/                          # 各プラットフォームでの使用例
│   ├── form_widget_loader.ts
│   └── usage_examples.html
├── docker-compose.yml                 # Docker Compose設定
├── Makefile                           # 開発用Makefile
└── README.md                          # 本ドキュメント
```

## テナント管理画面 (Frontend)

このプロジェクトには、テナント情報をブラウザ上で管理するためのフロントエンドアプリケーションが含まれています。

### 目的
テナントの参照、作成、更新、削除 (CRUD) 操作を行うためのWebインターフェースを提供します。

### 技術スタック
- React
- TypeScript
- Vite (ビルドツール・開発サーバー)
- axios (HTTPクライアント)
- react-router-dom (ルーティング)
- Supabase Client (`@supabase/supabase-js`)

### 主な機能
- テナントの一覧表示 (ページネーションは未実装)
- 新規テナントの作成フォーム
- 既存テナントの編集フォーム
- テナントの削除 (論理削除)
- ユーザー認証（ログイン・ログアウト）
- 認証済みユーザー（スーパーユーザーロール）のみアクセス可能な保護ルート
- RAG用ドキュメントファイルのアップロード機能 (テナントごと、拡張子バリデーション付き)

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
- `frontend/src/contexts/AuthContext.tsx`: グローバルな認証状態管理
- `frontend/src/api.ts`: バックエンドAPIと通信するための `axios` クライアントインスタンス
- `frontend/src/supabaseClient.ts`: Supabaseクライアントの初期化
- `frontend/src/App.tsx`: アプリケーション全体のルーティング設定

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
    -   アップロードされたファイルの情報（ファイル名、処理ID、バックエンドでの処理状況を確認するためのステータスURLなど）が画面に表示されます。
-   **ファイルバリデーション**:
    -   フロントエンドでファイル選択時に拡張子バリデーションが行われます。現在許可されている拡張子は、`.pdf`, `.txt`, `.md`, `.docx`, `.pptx`, `.xlsx` です。これ以外のファイルタイプはアップロードできません。
-   **利用API**:
    -   ファイルのアップロードには、バックエンドの `POST /api/v1/tenants/{tenant_id}/rag_files` エンドポイントが使用されます。
-   **注意点**:
    -   ファイルのアップロード後、バックエンドでは非同期処理（ファイルの解析、インデックス作成など）が実行される場合があります。実際のファイル処理状況は、アップロード結果に表示される「ステータスURL」から確認してください。
    -   この機能は認証が必要であり、操作を行うユーザーは対象テナントに所属しているか、スーパーユーザーである必要があります。

## 🛠️ 利用可能なコマンド

```bash
make dev          # 開発環境起動
make build        # 本番ビルド
make test         # テスト実行
make clean        # コンテナ削除
make logs         # ログ確認
make restart      # 再起動
```

## 🚀 デプロイ

### Vercel (フロントエンド)

```bash
cd frontend
vercel --prod
```

### Railway (バックエンド)

```bash
cd backend
railway deploy
```

### Supabase (データベース)

1. [Supabase](https://supabase.com)でプロジェクト作成
2. `database/contact_form_schema.sql`を実行
3. 環境変数にURL・KEYを設定

## 📊 機能一覧

### フォーム機能
- [x] 基本項目（名前・メール・会社・電話・メッセージ）
- [x] リアルタイムバリデーション
- [x] 送信中・完了状態の表示
- [x] レスポンシブデザイン

### 通知機能
- [ ] 管理者メール通知 (開発優先度 低)
- [ ] 顧客自動返信メール (開発優先度 低)
- [ ] Slack通知 (開発優先度 低)
- [ ] SMS通知 (開発優先度 低)
- [ ] Discord通知 (開発優先度 低)

### 管理機能
- [x] 送信データの保存
- [ ] データ分析 (GA4連携により高度な分析が可能)
- [x] 管理画面UI（開発中、テナント管理機能実装）
- [ ] 詳細分析 (GA4を活用)

### 📈 GA4連携機能
- [x] フォーム送信時に `generate_lead` イベントをGA4に送信 (Measurement Protocol経由)
- [x] 問い合わせステータス変更時に対応するGA4イベントを送信 (例: `working_lead`, `qualify_lead`, `close_convert_lead`)
- [x] フォームごとのGA4測定ID・APIシークレット設定機能 (専用API経由で管理)



---

**Made with ❤️ for small businesses**
