# APIテストガイド

## 前提条件

- RunPod Serverless Endpointがデプロイ済みであること
- RunPod API Keyを取得済みであること
- `jq` がインストールされていること（`brew install jq`）

## セットアップ

### 1. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成します。

```bash
cp .env.example .env
```

`.env` を編集して実際の値を設定します。

```
RUNPOD_API_KEY=your-api-key
RUNPOD_ENDPOINT_ID=your-endpoint-id
```

### 2. 入力画像の配置

テスト用の画像を `test/input/` に配置します。

```
test/
├── input/          ← 入力画像を配置
│   └── sample.png
├── output/         ← 生成された動画が保存される
├── test_api.sh     ← テストスクリプト
└── .gitignore
```

## テストスクリプトの使い方

### 基本構文

```bash
./test/test_api.sh [画像パス] [プロンプト] [秒数]
```

| 引数 | デフォルト | 説明 |
|---|---|---|
| 画像パス | `example_image.png` | 入力画像のパス |
| プロンプト | 陶芸工房の女の子向けテスト用 | 動画の内容を記述するテキスト |
| 秒数 | `5` | 動画の長さ（秒）。フレーム数は `16 * 秒数 + 1` で自動計算 |

### 実行例

#### デフォルト（5秒動画）

```bash
./test/test_api.sh
```

#### 入力画像とプロンプトを指定

```bash
./test/test_api.sh test/input/sample.png "a person walking slowly"
```

#### 10秒の動画を生成

```bash
./test/test_api.sh test/input/sample.png "a person walking slowly" 10
```

### 秒数とフレーム数の対応

| 秒数 | フレーム数 | 備考 |
|---|---|---|
| 3 | 49 | 短い動画、高速テスト向き |
| 5 | 81 | デフォルト |
| 10 | 161 | VRAM消費増加 |
| 15 | 241 | 24GB GPUでは不安定な可能性あり |

## 出力

生成された動画は `test/output/output_video.mp4` に保存されます。

### ログ出力例

```
[08:15:30] === Wan2.2 APIテスト ===
[08:15:30] Endpoint: your-endpoint-id
[08:15:30] Image: test/input/sample.png
[08:15:30] Prompt: a person walking slowly
[08:15:30] Length: 5秒 (81フレーム)
[08:15:30] 画像をBase64エンコード中...
[08:15:31] ジョブを投入中...
[08:15:31] レスポンス: {"id":"xxx","status":"IN_QUEUE"}
[08:15:31] ジョブID: xxx
[08:15:31] 完了を待機中...
[08:15:31] ステータス: IN_QUEUE
[08:15:41] ステータス: IN_PROGRESS
[08:18:22] ジョブ完了!
[08:18:23] 動画を保存しました: test/output/output_video.mp4
[08:18:23] === テスト完了 ===
```

## トラブルシューティング

### ジョブIDを取得できない
- `.env` の `RUNPOD_API_KEY` と `RUNPOD_ENDPOINT_ID` が正しいか確認
- RunPodコンソールでEndpointがActiveか確認

### executionTimeout exceeded
- RunPodコンソールの Manage → Execution timeout を増やす（推奨: 1200秒以上）
- 秒数（フレーム数）を減らして再試行

### ステータスがFAILEDになる
- RunPodコンソールの Logs タブでエラー内容を確認
- GPU VRAMが不足している場合は解像度やフレーム数を下げる

### ワーカーがIdleにならない
- Max workers を `1` に設定（テスト中は1台で十分）
- Active workers が `0` になっているか確認
