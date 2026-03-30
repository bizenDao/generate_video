# Wan2.2 動画生成API 仕様書

## 1. システム概要

Wan2.2 AIモデルを使用し、静止画から動画を生成するRunPod Serverlessワーカー。ComfyUIをバックエンドとして動作し、REST API経由でジョブを受け付ける。

### アーキテクチャ

```
クライアント → RunPod API → Serverless Worker → ComfyUI → 動画出力
                                  (handler.py)     (WebSocket)
```

### 対応ワークフロー

| ワークフロー | ファイル | 用途 |
|---|---|---|
| I2V (Image to Video) | `new_Wan22_api.json` | 開始画像1枚から動画を生成 |
| FLF2V (First & Last Frame to Video) | `new_Wan22_flf2v_api.json` | 開始画像と終了画像の間を補間して動画を生成 |

ワークフローはリクエスト内容により自動選択される（`end_image_*` パラメータの有無で判定）。

## 2. 実行環境

### コンテナ構成

| 項目 | 値 |
|---|---|
| ベースイメージ | Dockerfileの `FROM` 行を参照 |
| バックエンド | ComfyUI（最新版を `git clone` でインストール） |
| ランタイム | Python + RunPod Serverless SDK |
| エントリポイント | `entrypoint.sh` → ComfyUI起動 → `handler.py` 起動 |

### GPU要件

| 項目 | 値 |
|---|---|
| GPU | ADA 24GB (RTX 4090等) / ADA 32GB PRO (A6000等) |
| CUDA | 12.8 |
| コンテナディスク | 180 GB |

### 使用モデル

| モデル | パス | サイズ |
|---|---|---|
| Wan2.2 I2V HIGH (fp8) | `/ComfyUI/models/diffusion_models/Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors` | 大 |
| Wan2.2 I2V LOW (fp8) | `/ComfyUI/models/diffusion_models/Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors` | 大 |
| Lightning LoRA (high) | `/ComfyUI/models/loras/high_noise_model.safetensors` | 小 |
| Lightning LoRA (low) | `/ComfyUI/models/loras/low_noise_model.safetensors` | 小 |
| CLIP Vision | `/ComfyUI/models/clip_vision/clip_vision_h.safetensors` | 中 |
| UMT5-XXL テキストエンコーダ | `/ComfyUI/models/text_encoders/umt5-xxl-enc-bf16.safetensors` | 大 |
| VAE | `/ComfyUI/models/vae/Wan2_1_VAE_bf16.safetensors` | 中 |

### ComfyUI カスタムノード

| ノード | リポジトリ |
|---|---|
| ComfyUI-Manager | comfyanonymous/ComfyUI-Manager |
| ComfyUI-GGUF | city96/ComfyUI-GGUF |
| ComfyUI-KJNodes | kijai/ComfyUI-KJNodes |
| ComfyUI-VideoHelperSuite | Kosinkadink/ComfyUI-VideoHelperSuite |
| ComfyUI-GGUF-FantasyTalking | kael558/ComfyUI-GGUF-FantasyTalking |
| ComfyUI-wanBlockswap | orssorbit/ComfyUI-wanBlockswap |
| ComfyUI-WanVideoWrapper | kijai/ComfyUI-WanVideoWrapper |
| IntelligentVRAMNode | eddyhhlure1Eddy/IntelligentVRAMNode |
| auto_wan2.2animate_freamtowindow_server | eddyhhlure1Eddy/auto_wan2.2animate_freamtowindow_server |
| ComfyUI-AdaptiveWindowSize | eddyhhlure1Eddy/ComfyUI-AdaptiveWindowSize |

## 3. API仕様

### エンドポイント

```
POST https://api.runpod.ai/v2/{endpoint_id}/run
```

ヘッダー:
```
Authorization: Bearer {runpod_api_key}
Content-Type: application/json
```

### 3.1 リクエスト

#### 画像入力（いずれか1つを指定）

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `image_path` | `string` | いいえ | Network Volume上の画像パス |
| `image_url` | `string` | いいえ | 画像のURL（wgetでダウンロード） |
| `image_base64` | `string` | いいえ | Base64エンコードされた画像データ |

いずれも未指定の場合、デフォルト画像 `/example_image.png` が使用される。

#### エンド画像入力（FLF2Vワークフロー用、オプション）

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `end_image_path` | `string` | いいえ | Network Volume上のエンド画像パス |
| `end_image_url` | `string` | いいえ | エンド画像のURL |
| `end_image_base64` | `string` | いいえ | Base64エンコードされたエンド画像データ |

`end_image_*` のいずれかが指定されると、FLF2Vワークフロー（`new_Wan22_flf2v_api.json`）が自動選択される。

#### 動画生成パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `prompt` | `string` | **はい** | - | 動画の内容を記述するテキスト |
| `negative_prompt` | `string` | いいえ | ※下記参照 | 除外要素を指定するネガティブプロンプト |
| `seed` | `integer` | **はい** | - | ランダムシード |
| `cfg` | `float` | **はい** | - | CFGスケール |
| `width` | `integer` | **はい** | - | 出力動画の幅（16の倍数に自動補正） |
| `height` | `integer` | **はい** | - | 出力動画の高さ（16の倍数に自動補正） |
| `length` | `integer` | いいえ | `81` | フレーム数 |
| `steps` | `integer` | いいえ | `10` | デノイジングステップ数 |
| `context_overlap` | `integer` | いいえ | `48` | コンテキストオーバーラップ値 |

**negative_promptのデフォルト値:**
```
bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards
```

**解像度の自動補正**: `width` と `height` は最も近い16の倍数に自動補正される（最小16）。

#### LoRA設定

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `lora_pairs` | `array` | いいえ | `[]` | LoRAペアの配列（最大4個） |

各LoRAペアの構造:

| フィールド | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `high` | `string` | はい | - | HIGH LoRAモデルのファイル名 |
| `low` | `string` | はい | - | LOW LoRAモデルのファイル名 |
| `high_weight` | `float` | いいえ | `1.0` | HIGH LoRAの重み |
| `low_weight` | `float` | いいえ | `1.0` | LOW LoRAの重み |

LoRAファイルはNetwork Volumeの `/loras/` フォルダに配置する必要がある（`extra_model_paths.yaml` で `/runpod-volume/loras/` がパスに含まれる）。

### 3.2 レスポンス

#### ジョブ投入時

```json
{
  "id": "job-id-string",
  "status": "IN_QUEUE"
}
```

#### ステータス確認

```
GET https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}
```

ステータス値: `IN_QUEUE` → `IN_PROGRESS` → `COMPLETED` / `FAILED`

#### 成功時

```json
{
  "status": "COMPLETED",
  "output": {
    "video": "Base64エンコードされた動画データ (MP4)"
  }
}
```

#### エラー時

```json
{
  "status": "FAILED",
  "output": {
    "error": "エラーメッセージ"
  }
}
```

### 3.3 リクエスト例

#### I2V: 基本的な動画生成

```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_base64": "Base64データ...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "length": 81,
    "steps": 10
  }
}
```

#### FLF2V: 開始・終了フレーム指定

```json
{
  "input": {
    "prompt": "walking forward",
    "image_base64": "開始画像のBase64データ...",
    "end_image_base64": "終了画像のBase64データ...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "length": 81,
    "steps": 10
  }
}
```

#### LoRA付き動画生成

```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "image_path": "/runpod-volume/images/portrait.jpg",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "lora_pairs": [
      {
        "high": "lora1_high.safetensors",
        "low": "lora1_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      }
    ]
  }
}
```

## 4. Pythonクライアント

### GenerateVideoClient クラス

`generate_video_client.py` に実装されたクライアントライブラリ。

#### コンストラクタ

```python
client = GenerateVideoClient(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key"
)
```

#### メソッド一覧

| メソッド | 説明 |
|---|---|
| `encode_file_to_base64(file_path)` | ファイルをBase64エンコード |
| `submit_job(input_data)` | RunPodにジョブを投入。Job IDを返す |
| `wait_for_completion(job_id, check_interval=10, max_wait_time=1800)` | ジョブ完了を待機（デフォルト最大30分） |
| `save_video_result(result, output_path)` | 結果の動画をファイルに保存 |
| `create_video_from_image(...)` | 画像から動画を生成（投入〜完了待機を一括実行） |
| `batch_process_images(...)` | フォルダ内の画像を一括処理 |

#### create_video_from_image パラメータ

| パラメータ | 型 | デフォルト |
|---|---|---|
| `image_path` | `str` | （必須） |
| `prompt` | `str` | `"running man, grab the gun"` |
| `negative_prompt` | `str` | `None` |
| `width` | `int` | `480` |
| `height` | `int` | `832` |
| `length` | `int` | `81` |
| `steps` | `int` | `10` |
| `seed` | `int` | `42` |
| `cfg` | `float` | `2.0` |
| `context_overlap` | `int` | `48` |
| `lora_pairs` | `list` | `None` |

#### batch_process_images 追加パラメータ

| パラメータ | 型 | デフォルト |
|---|---|---|
| `image_folder_path` | `str` | （必須） |
| `output_folder_path` | `str` | （必須） |
| `valid_extensions` | `tuple` | `('.jpg', '.jpeg', '.png', '.bmp', '.tiff')` |

## 5. 内部処理フロー

### 起動シーケンス（entrypoint.sh）

```
1. ComfyUIをバックグラウンドで起動
2. HTTP (127.0.0.1:8188) の応答を最大2分待機
3. handler.py を起動（RunPod Serverlessワーカー）
```

### リクエスト処理フロー（handler.py）

```
1. リクエスト受信
2. 画像入力処理
   - path: そのまま使用
   - url: wgetでダウンロード → 一時ファイル
   - base64: デコード → 一時ファイル
3. エンド画像の有無でワークフロー選択
   - なし: new_Wan22_api.json (I2V)
   - あり: new_Wan22_flf2v_api.json (FLF2V)
4. ワークフローにパラメータを注入
   - 画像パス（ノード244）
   - プロンプト（ノード135）
   - シード（ノード220, 540）
   - 解像度（ノード235, 236） ※16倍数に自動補正
   - LoRA設定（ノード279: HIGH, ノード553: LOW）
   - エンド画像（ノード617）※FLF2Vのみ
5. ComfyUIにHTTP接続確認（最大3分）
6. WebSocket接続（最大3分）
7. プロンプト送信 → 完了待機
8. 生成された動画をBase64エンコードして返却
```

### ComfyUI ワークフロー ノードマッピング

| ノードID | 役割 |
|---|---|
| 122 | WanVideoモデルローダー |
| 129 | VAEローダー |
| 130 | VAEタイリング設定 |
| 135 | プロンプト（positive/negative） |
| 220 | シード |
| 235 | 幅 |
| 236 | 高さ |
| 244 | 入力画像ロード |
| 279 | HIGH LoRAセレクター（lora_1〜lora_4） |
| 498 | コンテキスト設定（overlap, frames） |
| 540 | シード/CFG |
| 541 | フレーム数 |
| 553 | LOW LoRAセレクター（lora_1〜lora_4） |
| 617 | エンド画像ロード（FLF2Vのみ） |
| 829 | LowSteps（steps * 0.6） |
| 834 | Steps設定 |

## 6. Network Volume パス構成

`extra_model_paths.yaml` による追加パス設定:

```
/runpod-volume/
  models/         → diffusion_modelsの追加検索パス
  loras/          → LoRAの追加検索パス
```

## 7. 制約事項

- LoRAは最大4ペアまで（5個以上指定した場合、先頭4個のみ使用）
- 解像度は16の倍数に自動補正される（最小16px）
- ComfyUI起動に最大2分、接続確立に最大3分かかる場合がある
- 出力はBase64エンコードされたMP4（大容量になる可能性あり）
- ベースイメージは外部依存（Dockerfileの `FROM` 行を参照）

## 8. ファイル構成

```
generate_video/
├── .runpod/
│   └── hub.json                  # RunPod Hub テンプレート設定
├── docs/
│   ├── deploy.md                 # デプロイガイド
│   ├── specification.md          # 本仕様書
│   ├── README_en.md              # 英語README
│   └── README_kr.md              # 韓国語README
├── Dockerfile                    # コンテナビルド定義
├── entrypoint.sh                 # コンテナ起動スクリプト
├── handler.py                    # RunPod Serverlessハンドラ
├── generate_video_client.py      # Pythonクライアントライブラリ
├── new_Wan22_api.json            # I2Vワークフロー定義
├── new_Wan22_flf2v_api.json      # FLF2Vワークフロー定義
├── extra_model_paths.yaml        # ComfyUIモデルパス設定
├── example_image.png             # サンプル画像
└── README.md                     # 日本語README（メイン）
```
