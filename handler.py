import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64エラー処理用にimport
import subprocess
import time
# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())
def to_nearest_multiple_of_16(value):
    """指定値を最も近い16の倍数に補正、最小16を保証"""
    try:
        numeric_value = float(value)
    except Exception:
        raise Exception(f"width/heightの値が数値ではありません: {value}")
    adjusted = int(round(numeric_value / 16.0) * 16)
    if adjusted < 16:
        adjusted = 16
    return adjusted
def process_input(input_data, temp_dir, output_filename, input_type):
    """入力データを処理してファイルパスを返す関数"""
    if input_type == "path":
        # パスの場合はそのまま返す
        logger.info(f"📁 パス入力処理: {input_data}")
        return input_data
    elif input_type == "url":
        # URLの場合はダウンロード
        logger.info(f"🌐 URL入力処理: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        # Base64の場合はデコードして保存
        logger.info(f"🔢 Base64入力処理")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"サポートされていない入力タイプ: {input_type}")

        
def download_file_from_url(url, output_path):
    """URLからファイルをダウンロードする関数"""
    try:
        # wgetを使用してファイルダウンロード
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ URLからファイルを正常にダウンロードしました: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wgetダウンロード失敗: {result.stderr}")
            raise Exception(f"URLダウンロード失敗: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ ダウンロードタイムアウト")
        raise Exception("ダウンロードタイムアウト")
    except Exception as e:
        logger.error(f"❌ ダウンロード中にエラー発生: {e}")
        raise Exception(f"ダウンロード中にエラー発生: {e}")


def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64データをファイルに保存する関数"""
    try:
        # Base64文字列デコード
        decoded_data = base64.b64decode(base64_data)

        # ディレクトリが存在しなければ作成
        os.makedirs(temp_dir, exist_ok=True)

        # ファイルに保存
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)

        logger.info(f"✅ Base64入力を'{file_path}'ファイルに保存しました。")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64デコード失敗: {e}")
        raise Exception(f"Base64デコード失敗: {e}")
    
def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # fullpathを利用して直接ファイルを読み込みbase64でエンコード
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # 画像入力処理 (image_path, image_url, image_base64のいずれか1つを使用)
    image_path = None
    if "image_path" in job_input:
        image_path = process_input(job_input["image_path"], task_id, "input_image.jpg", "path")
    elif "image_url" in job_input:
        image_path = process_input(job_input["image_url"], task_id, "input_image.jpg", "url")
    elif "image_base64" in job_input:
        image_path = process_input(job_input["image_base64"], task_id, "input_image.jpg", "base64")
    else:
        # デフォルト値を使用
        image_path = "/example_image.png"
        logger.info("デフォルト画像ファイルを使用します: /example_image.png")

    # エンド画像入力処理 (end_image_path, end_image_url, end_image_base64のいずれか1つを使用)
    end_image_path_local = None
    if "end_image_path" in job_input:
        end_image_path_local = process_input(job_input["end_image_path"], task_id, "end_image.jpg", "path")
    elif "end_image_url" in job_input:
        end_image_path_local = process_input(job_input["end_image_url"], task_id, "end_image.jpg", "url")
    elif "end_image_base64" in job_input:
        end_image_path_local = process_input(job_input["end_image_base64"], task_id, "end_image.jpg", "base64")
    
    # LoRA設定確認 - 配列で受け取って処理
    lora_pairs = job_input.get("lora_pairs", [])

    # 最大4個のLoRAまでサポート
    lora_count = min(len(lora_pairs), 4)
    if lora_count > len(lora_pairs):
        logger.warning(f"LoRA数が{len(lora_pairs)}個です。最大4個までサポートされます。最初の4個のみ使用します。")
        lora_pairs = lora_pairs[:4]

    # ワークフローファイル選択 (end_image_*がある場合はFLF2Vワークフローを使用)
    workflow_file = "/new_Wan22_flf2v_api.json" if end_image_path_local else "/new_Wan22_api.json"
    logger.info(f"Using {'FLF2V' if end_image_path_local else 'single'} workflow with {lora_count} LoRA pairs")
    
    prompt = load_workflow(workflow_file)
    
    length = job_input.get("length", 81)
    steps = job_input.get("steps", 10)

    prompt["244"]["inputs"]["image"] = image_path
    prompt["541"]["inputs"]["num_frames"] = length
    prompt["135"]["inputs"]["positive_prompt"] = job_input["prompt"]
    prompt["135"]["inputs"]["negative_prompt"] = job_input.get("negative_prompt", "bright tones, overexposed, static, blurred details, subtitles, style, works, paintings, images, static, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, still picture, messy background, three legs, many people in the background, walking backwards")
    prompt["220"]["inputs"]["seed"] = job_input["seed"]
    prompt["540"]["inputs"]["seed"] = job_input["seed"]
    prompt["540"]["inputs"]["cfg"] = job_input["cfg"]
    # 解像度(幅/高さ) 16倍数補正
    original_width = job_input["width"]
    original_height = job_input["height"]
    adjusted_width = to_nearest_multiple_of_16(original_width)
    adjusted_height = to_nearest_multiple_of_16(original_height)
    if adjusted_width != original_width:
        logger.info(f"Width adjusted to nearest multiple of 16: {original_width} -> {adjusted_width}")
    if adjusted_height != original_height:
        logger.info(f"Height adjusted to nearest multiple of 16: {original_height} -> {adjusted_height}")
    prompt["235"]["inputs"]["value"] = adjusted_width
    prompt["236"]["inputs"]["value"] = adjusted_height
    prompt["498"]["inputs"]["context_overlap"] = job_input.get("context_overlap", 48)
    prompt["498"]["inputs"]["context_frames"] = length

    # step設定適用
    if "834" in prompt:
        prompt["834"]["inputs"]["steps"] = steps
        logger.info(f"Steps set to: {steps}")
        lowsteps = int(steps*0.6)
        prompt["829"]["inputs"]["step"] = lowsteps
        logger.info(f"LowSteps set to: {lowsteps}")

    # エンド画像がある場合、617番ノードにパス適用 (FLF2V専用)
    if end_image_path_local:
        prompt["617"]["inputs"]["image"] = end_image_path_local
    
    # LoRA設定適用 - HIGH LoRAはノード279、LOW LoRAはノード553
    if lora_count > 0:
        # HIGH LoRAノード (279番)
        high_lora_node_id = "279"

        # LOW LoRAノード (553番)
        low_lora_node_id = "553"

        # 入力されたLoRA pairsを適用 (lora_1から開始)
        for i, lora_pair in enumerate(lora_pairs):
            if i < 4:  # 最大4個まで
                lora_high = lora_pair.get("high")
                lora_low = lora_pair.get("low")
                lora_high_weight = lora_pair.get("high_weight", 1.0)
                lora_low_weight = lora_pair.get("low_weight", 1.0)
                
                # HIGH LoRA設定 (ノード279番、lora_1から開始)
                if lora_high:
                    prompt[high_lora_node_id]["inputs"][f"lora_{i+1}"] = lora_high
                    prompt[high_lora_node_id]["inputs"][f"strength_{i+1}"] = lora_high_weight
                    logger.info(f"LoRA {i+1} HIGH applied to node 279: {lora_high} with weight {lora_high_weight}")
                
                # LOW LoRA設定 (ノード553番、lora_1から開始)
                if lora_low:
                    prompt[low_lora_node_id]["inputs"][f"lora_{i+1}"] = lora_low
                    prompt[low_lora_node_id]["inputs"][f"strength_{i+1}"] = lora_low_weight
                    logger.info(f"LoRA {i+1} LOW applied to node 553: {lora_low} with weight {lora_low_weight}")

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # まずHTTP接続が可能か確認
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP接続確認 (最大1分)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP接続成功 (試行 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP接続失敗 (試行 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUIサーバーに接続できません。サーバーが実行中か確認してください。")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # WebSocket接続試行 (最大3分)
    max_attempts = int(180/5)  # 3分 (5秒ごとに試行)
    for attempt in range(max_attempts):
        import time
        try:
            ws.connect(ws_url)
            logger.info(f"WebSocket接続成功 (試行 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"WebSocket接続失敗 (試行 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("WebSocket接続タイムアウト (3分)")
            time.sleep(5)
    videos = get_videos(ws, prompt)
    ws.close()

    # 動画が見つからない場合の処理
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}
    
    return {"error": "動画が見つかりません。"}

runpod.serverless.start({"handler": handler})