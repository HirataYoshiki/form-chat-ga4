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
# .envファイルを編集してAPI キーを設定
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

## 📁 プロジェクト構成

```
contact-form-widget/
├── frontend/                          # React フロントエンド
│   └── src/
│       └── components/
│           └── ContactFormWidget.tsx  # メインウィジェット
├── backend/
│   └── contact_api.py                 # FastAPI バックエンド
├── database/
│   └── contact_form_schema.sql        # Supabaseスキーマ
├── examples/
│   ├── form_widget_loader.ts          # 埋め込みローダー
│   └── usage_examples.html            # 使用例
├── docker-compose.yml
├── Makefile
└── README.md
```

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
- [x] 基本的な分析
- [ ] 管理画面UI（開発中）
- [ ] 詳細分析ダッシュボード（予定）



---

**Made with ❤️ for small businesses**
