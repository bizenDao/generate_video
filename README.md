# Wan2.2 動画生成 APIクライアント
[한국어 README 보기](README_kr.md) | [English README](README_org.md)

本プロジェクトは、**Wan2.2** モデルを使用し、RunPodのgenerate_videoエンドポイントを通じて画像から動画を生成するPythonクライアントを提供します。Base64エンコーディング、LoRA設定、バッチ処理に対応しています。

[![Runpod](https://api.runpod.io/badge/wlsdml1114/generate_video)](https://console.runpod.io/hub/wlsdml1114/generate_video)

**Wan2.2** は、静止画を自然な動きとリアルなアニメーションで動画に変換する先進的なAIモデルです。ComfyUIをベースに構築されており、高品質な動画生成機能を提供します。

## 🎨 Engui Studio 連携

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

このWan2.2クライアントは主に **Engui Studio**（包括的なAIモデル管理プラットフォーム）向けに設計されています。API経由でも使用可能ですが、Engui Studioではより充実した機能と幅広いモデルサポートを提供します。

## ✨ 主な機能

*   **Wan2.2モデル**: 高品質な動画生成のための先進的なWan2.2 AIモデルを搭載。
*   **画像から動画への変換**: 静止画を自然な動きのある動画に変換。
*   **Base64エンコーディング対応**: 画像のエンコード/デコードを自動処理。
*   **LoRA設定**: 動画生成を強化するために最大4つのLoRAペアをサポート。
*   **バッチ処理**: 複数の画像を一括で処理可能。
*   **エラーハンドリング**: 包括的なエラー処理とログ機能。
*   **非同期ジョブ管理**: 自動的なジョブ送信とステータス監視。
*   **ComfyUI連携**: 柔軟なワークフロー管理のためのComfyUI統合。

## 🚀 RunPod サーバーレステンプレート

このテンプレートには、**Wan2.2** をRunPod Serverless Workerとして実行するために必要なコンポーネントがすべて含まれています。

*   **Dockerfile**: Wan2.2モデル実行に必要な環境構築と依存関係のインストールを設定。
*   **handler.py**: RunPod Serverlessのリクエスト処理用ハンドラ関数を実装。
*   **entrypoint.sh**: ワーカー起動時の初期化タスクを実行。
*   **new_Wan22_api.json**: Wan2.2画像から動画への生成で最大4つのLoRAペアをサポートするワークフローファイル。

## 📖 Pythonクライアントの使い方

### 基本的な使い方

```python
from generate_video_client import GenerateVideoClient

# クライアントの初期化
client = GenerateVideoClient(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key"
)

# 画像から動画を生成
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

# 成功した場合、結果を保存
if result.get('status') == 'COMPLETED':
    client.save_video_result(result, "./output_video.mp4")
else:
    print(f"エラー: {result.get('error')}")
```

### LoRAの使用

```python
# LoRAペアの設定
lora_pairs = [
    {
        "high": "your_high_lora.safetensors",
        "low": "your_low_lora.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
    }
]

# LoRAを使用して動画を生成
result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0,
    lora_pairs=lora_pairs
)
```

### バッチ処理

```python
# 複数の画像を処理
batch_result = client.batch_process_images(
    image_folder_path="./input_images",
    output_folder_path="./output_videos",
    prompt="running man, grab the gun",
    negative_prompt="blurry, low quality, distorted",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)

print(f"バッチ処理完了: {batch_result['successful']}/{batch_result['total_files']} 件成功")
```

## 🔧 APIリファレンス

### 入力

`input` オブジェクトには以下のフィールドを含める必要があります。画像は**パス、URL、またはBase64**のいずれかの方法で入力できます。

#### 画像入力（いずれか1つを使用）
| パラメータ | 型 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | いいえ | - | 入力画像のローカルパス |
| `image_url` | `string` | いいえ | - | 入力画像のURL |
| `image_base64` | `string` | いいえ | - | 入力画像のBase64エンコード文字列 |

#### LoRA設定
| パラメータ | 型 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- | --- |
| `lora_pairs` | `array` | いいえ | `[]` | LoRAペアの配列。各ペアには `high`、`low`、`high_weight`、`low_weight` を含む |

**重要**: LoRAモデルを使用するには、RunPodのNetwork Volumeの `/loras/` フォルダにLoRAファイルをアップロードする必要があります。`lora_pairs` のLoRAモデル名は `/loras/` フォルダ内のファイル名と一致させてください。

#### LoRAペアの構造
| パラメータ | 型 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- | --- |
| `high` | `string` | はい | - | High LoRAモデル名 |
| `low` | `string` | はい | - | Low LoRAモデル名 |
| `high_weight` | `float` | いいえ | `1.0` | High LoRAの重み |
| `low_weight` | `float` | いいえ | `1.0` | Low LoRAの重み |

#### 動画生成パラメータ
| パラメータ | 型 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | はい | - | 生成する動画の説明テキスト |
| `negative_prompt` | `string` | いいえ | - | 動画から除外したい要素を指定するネガティブプロンプト |
| `seed` | `integer` | いいえ | `42` | 動画生成のランダムシード |
| `cfg` | `float` | いいえ | `2.0` | 生成時のCFGスケール |
| `width` | `integer` | いいえ | `480` | 出力動画の幅（ピクセル） |
| `height` | `integer` | いいえ | `832` | 出力動画の高さ（ピクセル） |
| `length` | `integer` | いいえ | `81` | 生成する動画の長さ |
| `steps` | `integer` | いいえ | `10` | デノイジングステップ数 |
| `context_overlap` | `integer` | いいえ | `48` | コンテキストオーバーラップ値 |

**リクエスト例:**

#### 1. 基本的な生成（LoRAなし）
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "length": 81,
    "steps": 10
  }
}
```

#### 2. LoRAペアを使用
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "lora_pairs": [
      {
        "high": "your_high_lora.safetensors",
        "low": "your_low_lora.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      }
    ]
  }
}
```

#### 3. 複数のLoRAペア（最大4つ）
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_path": "/my_volume/image.jpg",
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
      },
      {
        "high": "lora2_high.safetensors",
        "low": "lora2_low.safetensors",
        "high_weight": 1.0,
        "low_weight": 1.0
      }
    ]
  }
}
```

#### 4. URL画像入力
```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "negative_prompt": "blurry, low quality, distorted",
    "image_url": "https://example.com/image.jpg",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "context_overlap": 48
  }
}
```

### 出力

#### 成功時

ジョブが成功した場合、生成された動画がBase64エンコードされたJSONオブジェクトを返します。

| パラメータ | 型 | 説明 |
| --- | --- | --- |
| `video` | `string` | Base64エンコードされた動画ファイルデータ |

**成功レスポンス例:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### エラー時

ジョブが失敗した場合、エラーメッセージを含むJSONオブジェクトを返します。

| パラメータ | 型 | 説明 |
| --- | --- | --- |
| `error` | `string` | 発生したエラーの説明 |

**エラーレスポンス例:**

```json
{
  "error": "Video not found."
}
```

## 🛠️ API直接利用

1.  本リポジトリをベースにRunPodでServerless Endpointを作成します。
2.  ビルドが完了しエンドポイントが有効になったら、上記のAPIリファレンスに従ってHTTP POSTリクエストでジョブを送信します。

### 📁 Network Volumeの使用

Base64エンコードされたファイルを直接送信する代わりに、RunPodのNetwork Volumeを使用して大きなファイルを扱うことができます。大きな画像ファイルやLoRAモデルを扱う場合に特に便利です。

1.  **Network Volumeの作成と接続**: RunPodダッシュボードからNetwork Volume（例：S3ベースのボリューム）を作成し、Serverless Endpoint設定に接続します。
2.  **ファイルのアップロード**: 使用したい画像ファイルとLoRAモデルを作成したNetwork Volumeにアップロードします。
3.  **ファイルの配置**:
    - 入力画像はNetwork Volume内の任意の場所に配置
    - LoRAモデルファイルはNetwork Volume内の `/loras/` フォルダに配置
4.  **パスの指定**: APIリクエスト時にNetwork Volume内のファイルパスを指定します：
    - `image_path`: 画像ファイルのフルパス（例：`"/my_volume/images/portrait.jpg"`）
    - LoRAモデル: ファイル名のみ（例：`"my_lora_model.safetensors"`）- システムが自動的に `/loras/` フォルダを参照

## 🔧 クライアントメソッド

### GenerateVideoClient クラス

#### `__init__(runpod_endpoint_id, runpod_api_key)`
RunPodエンドポイントIDとAPIキーでクライアントを初期化します。

#### `create_video_from_image(image_path, prompt, width, height, length, steps, seed, cfg, context_overlap, lora_pairs, negative_prompt)`
単一の画像から動画を生成します。

**パラメータ:**
- `image_path` (str): 入力画像のパス
- `prompt` (str): 動画生成用のテキストプロンプト
- `negative_prompt` (str): 除外したい要素を指定するネガティブプロンプト（デフォルト: None）
- `width` (int): 出力動画の幅（デフォルト: 480）
- `height` (int): 出力動画の高さ（デフォルト: 832）
- `length` (int): フレーム数（デフォルト: 81）
- `steps` (int): デノイジングステップ数（デフォルト: 10）
- `seed` (int): ランダムシード（デフォルト: 42）
- `cfg` (float): CFGスケール（デフォルト: 2.0）
- `context_overlap` (int): コンテキストオーバーラップ（デフォルト: 48）
- `lora_pairs` (list): LoRA設定ペア（デフォルト: None）

#### `batch_process_images(image_folder_path, output_folder_path, valid_extensions, ...)`
フォルダ内の複数の画像を処理します。

**パラメータ:**
- `image_folder_path` (str): 画像を含むフォルダのパス
- `output_folder_path` (str): 出力動画の保存先パス
- `valid_extensions` (tuple): 有効な画像拡張子（デフォルト: ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')）
- その他のパラメータは `create_video_from_image` と同じ

#### `save_video_result(result, output_path)`
動画の結果をファイルに保存します。

**パラメータ:**
- `result` (dict): ジョブ結果の辞書
- `output_path` (str): 動画ファイルの保存先パス

## 🔧 Wan2.2 ワークフロー設定

このテンプレートでは、**Wan2.2** 用の単一ワークフロー設定を使用しています：

*   **new_Wan22_api.json**: Wan2.2 画像から動画への生成ワークフロー（最大4つのLoRAペアをサポート）

ワークフローはComfyUIをベースとしており、Wan2.2処理に必要なすべてのノードを含みます：
- プロンプト用CLIPテキストエンコーディング
- VAEのロードと処理
- 動画生成用WanImageToVideoノード
- LoRAのロードと適用ノード（WanVideoLoraSelectMulti）
- 画像結合・処理ノード

## 🙏 Wan2.2について

**Wan2.2** は、画像から動画への生成において最先端のAIモデルであり、自然な動きとリアルなアニメーションを持つ高品質な動画を生成します。本プロジェクトは、Wan2.2モデルの簡単なデプロイと利用のためのPythonクライアントとRunPodサーバーレステンプレートを提供します。

### Wan2.2の主な特徴:
- **高品質な出力**: 優れた画質とスムーズな動きの動画を生成
- **自然なアニメーション**: 静止画からリアルで自然な動きを創出
- **LoRAサポート**: ファインチューニングされた動画生成のためのLoRA（Low-Rank Adaptation）をサポート
- **ComfyUI連携**: 柔軟なワークフロー管理のためのComfyUI統合
- **カスタマイズ可能なパラメータ**: 動画生成パラメータを完全にコントロール

## 🙏 オリジナルプロジェクト

本プロジェクトは以下のオリジナルリポジトリをベースにしています。モデルとコアロジックに関するすべての権利はオリジナルの作者に帰属します。

*   **Wan2.2:** [https://github.com/Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **ComfyUI-WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 ライセンス

オリジナルのWan2.2プロジェクトはそれぞれのライセンスに従います。本テンプレートもそのライセンスに準拠します。
