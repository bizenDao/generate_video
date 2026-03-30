# RunPod デプロイガイド

本プロジェクトをRunPod Serverless Endpointとしてデプロイする手順を説明します。

## 前提条件

- [RunPod](https://www.runpod.io/) のアカウント
- GitHubリポジトリが公開（public）であること

## デプロイ手順

### 1. Serverless Endpointの作成

1. [RunPod Serverlessコンソール](https://www.runpod.io/console/serverless) にログイン
2. **New Endpoint** をクリック

### 2. エンドポイント設定

| 項目 | 設定値 |
|---|---|
| Source | GitHub → `https://github.com/bizenDao/generate_video` |
| GPU Type | `ADA 24GB` または `ADA 32GB PRO` |
| Container Disk | `180 GB` |
| Min Workers | `0`（コスト節約）または `1`（常時起動） |
| Max Workers | 用途に応じて設定 |

### 3. Network Volume（オプション）

LoRAモデルを使用する場合は、Network Volumeの設定が必要です。

1. RunPodダッシュボードから **Network Volume** を作成
2. 作成したVolumeをEndpointにアタッチ
3. Volume内の `/loras/` フォルダにLoRAファイルをアップロード

### 4. デプロイ

**Deploy** をクリックするとビルドが開始されます。

- ビルド時間: 30分〜1時間程度（モデルダウンロードを含む）
- ステータスが **Active** になればデプロイ完了

## 動作確認

デプロイ完了後、以下のようなリクエストでテストできます。

```python
from generate_video_client import GenerateVideoClient

client = GenerateVideoClient(
    runpod_endpoint_id="your-endpoint-id",
    runpod_api_key="your-runpod-api-key"
)

result = client.create_video_from_image(
    image_path="./example_image.png",
    prompt="running man, grab the gun",
    width=480,
    height=832,
    length=81,
    steps=10,
    seed=42,
    cfg=2.0
)
```

または、RunPodコンソールの **Requests** タブから直接JSONを送信してテストできます。

```json
{
  "input": {
    "prompt": "running man, grab the gun",
    "image_base64": "data:image/jpeg;base64,...",
    "seed": 42,
    "cfg": 2.0,
    "width": 480,
    "height": 832,
    "length": 81,
    "steps": 10
  }
}
```

## トラブルシューティング

### ビルドが失敗する場合
- RunPodのビルドログを確認してください
- Dockerfileで指定されているベースイメージが利用可能か確認してください

### Endpointがタイムアウトする場合
- ComfyUIの起動に最大2分かかります（entrypoint.shで待機処理あり）
- GPUのVRAMが不足している場合、より大きなGPUを選択してください

### LoRAが適用されない場合
- Network Volumeがアタッチされているか確認
- LoRAファイルが `/loras/` フォルダに配置されているか確認
- `lora_pairs` のファイル名がVolume内のファイル名と一致しているか確認
