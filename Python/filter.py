import os
import json
import base64
import time
import subprocess

# ==========================================
# 1. AUTHENTICATION CHECK
# ==========================================
token = os.environ.get("KAGGLE_API_TOKEN")
if not token:
    print("❌ CRITICAL ERROR: KAGGLE_API_TOKEN secret nahi mila!")
    exit(1)

# Kaggle CLI ke liye token automatically configure karna
os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)
kaggle_config_path = os.path.expanduser("~/.kaggle/kaggle.json")

# Agar token directly diya gaya hai, toh temporary config file create kar lo
if not os.path.exists(kaggle_config_path):
    # Agar token 'KGAT_' se start ho raha hai, toh use bearer token format me likhte hain
    config_data = {"token": token}
    with open(kaggle_config_path, "w") as f:
        json.dump(config_data, f)
    os.chmod(kaggle_config_path, 0o600)

WORKSPACE_DIR = "Kaggle_Workspace"
FULL_KERNEL_ID = "tca-filter-engine-gpu"

# ==========================================
# 2. READ & ENCRYPT DATA
# ==========================================
if not os.path.exists("Data/1.json"):
    print("🤷‍♂️ Data/1.json not found. Exiting.")
    exit(0)

with open("Data/1.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

if not articles:
    print("🤷‍♂️ 1.json is empty. Exiting.")
    exit(0)

print(f"📦 Packing {len(articles)} articles for Kaggle GPU execution...")
b64_data = base64.b64encode(json.dumps(articles).encode('utf-8')).decode('utf-8')

# ==========================================
# 3. GENERATE KAGGLE SCRIPT
# ==========================================
os.makedirs(WORKSPACE_DIR, exist_ok=True)

KAGGLE_CODE = """
import os
import json
import base64
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("🚀 Extracting injected data...")
b64_data = "_INSERT_B64_HERE_"
articles = json.loads(base64.b64decode(b64_data).decode('utf-8'))
print(f"✅ Found {len(articles)} articles!")

print("🚀 Loading Qwen-2.5-7B from Persistent Cache...")
LOCAL_MODEL_PATH = "/kaggle/input/official-qwen-7b-instruct"
for item in os.listdir(LOCAL_MODEL_PATH):
    if os.path.isdir(os.path.join(LOCAL_MODEL_PATH, item)):
        LOCAL_MODEL_PATH = os.path.join(LOCAL_MODEL_PATH, item)
        break

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    LOCAL_MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto",
    local_files_only=True
)
print("✅ Model successfully loaded on GPU!")

SYSTEM_INSTRUCTION = '''You are an elite Current Affairs Evaluator & Content Strategist for Indian Competitive Exams (UPSC, SSC, Banking).
Your core job is to strictly filter out garbage news and rank only high-yield factual content.

### 1. RELEVANCE CHECK (relevant: 0 or 1)
- YES (1): Factual news about Economy (RBI, GDP, Taxation), Govt Schemes/Yojanas, Defense (ISRO, DRDO, Exercises), International Summits, Major Appointments, Indexes, Supreme Court verdicts, or Major Sports/Awards.
- NO (0): Political debates, election rallies, pure crime, entertainment/Bollywood, stock market daily fluctuations, opinions/editorials without new facts, or local municipal news.

### 2. RANKING RUBRIC (rank: 0 to 5) - Apply only if relevant=1
- 5: Major Policy changes, Union Budget, RBI Monetary Policy, Constitutional Amendments, Global Treaties, Nobel Prizes.
- 4: Defense deals, ISRO missions, Global Indexes, SC landmark judgments, Olympics/World Cup.
- 3: New State Govt schemes, Banking updates, bilateral MoUs, Important Days, National Awards.
- 2: Minor regional appointments, local state festivals, minor sports events.
- 1: Vague news with very slight exam potential.
- 0: If relevant=0.

### 3. STRICT OUTPUT RULES
- You MUST output ONLY a raw, valid JSON object starting strictly with { and ending with }.
- ABSOLUTELY NO MARKDOWN FORMATTING.
- No preamble, no explanations, no extra text whatsoever.
Example: {"relevant": 1, "rank": 5}'''

final_articles = []

for idx, article in enumerate(articles):
    title = article.get("title", "")
    content = article.get("content", "")
    if not title and not content: continue
    
    prompt = f"Analyze this news and return strictly a raw JSON object (WITHOUT any markdown backticks):\n\nTitle: {title}\nContent: {content}"
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": prompt}]
    
    input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([input_text], return_tensors="pt").to(model.device)
    
    try:
        outputs = model.generate(**inputs, max_new_tokens=256, do_sample=False)
        response = tokenizer.batch_decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)[0]
        
        if response.startswith("```json"): response = response[7:]
        if response.endswith("```"): response = response[:-3]
        
        result_data = json.loads(response.strip())
        if result_data.get("relevant", 0) == 1:
            article["rank"] = result_data.get("rank", 0)
            final_articles.append(article)
            print(f"✅ [{idx+1}/{len(articles)}] RELEVANT (Rank: {article['rank']}): {title[:40]}...")
        else:
            print(f"❌ [{idx+1}/{len(articles)}] REJECTED: {title[:40]}...")
            
    except Exception as e:
        print(f"⚠️ Error on {title[:20]}: {e}")

final_articles.sort(key=lambda x: x.get("rank", 0), reverse=True)
with open("2.json", "w", encoding="utf-8") as f:
    json.dump(final_articles, f, indent=4, ensure_ascii=False)

print(f"🎉 SUCCESS: Finished processing! {len(final_articles)} articles passed.")
"""

KAGGLE_CODE = KAGGLE_CODE.replace("_INSERT_B64_HERE_", b64_data)

with open(f"{WORKSPACE_DIR}/filter_engine.py", "w", encoding="utf-8") as f:
    f.write(KAGGLE_CODE)

# Kaggle metadata mein owner check karna zaroori hai
# Hum Kaggle CLI se username fetch kar lenge
def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8').strip()

print("🔍 Fetching Kaggle Username via CLI...")
whoami_out = run_cmd("kaggle kernels status me 2>&1 || true")
# Fallback mechanism agar username direct na mile
# Hum kaggle.json se read kar sakte hain ya environment se
kaggle_user = ""
try:
    with open(os.path.expanduser("~/.kaggle/kaggle.json"), "r") as cf:
        cdata = json.load(cf)
        # Token format check
        if "username" in cdata:
            kaggle_user = cdata["username"]
except Exception:
    pass

if not kaggle_user:
    # Agar token format me username nahi hai, toh kaggle config se nikalne ki koshish karo
    config_list = run_cmd("kaggle config view 2>&1 || true")
    for line in config_list.split('\n'):
        if "user" in line.lower():
            parts = line.split(':')
            if len(parts) > 1:
                kaggle_user = parts[1].strip()

# Agar phir bhi na mile toh user se bolenge ki env variable set karein, par hum yahan default set kar dete hain
full_kernel_id = f"tca_filter_gpu_job" 
# Better approach: kaggle api handles username if we just use a clean slug if configured correctly, 
# but let's write metadata properly.

metadata = {
  "id": f"tca_filter_engine_run",
  "title": "TCA Filter Engine",
  "code_file": "filter_engine.py",
  "language": "python",
  "kernel_type": "script",
  "is_private": True,
  "enable_gpu": True,
  "enable_internet": False, 
  "dataset_sources": [],
  "competition_sources": [],
  "kernel_sources": []
}

with open(f"{WORKSPACE_DIR}/kernel-metadata.json", "w") as f:
    json.dump(metadata, f, indent=4)

print("🚀 Pushing AI script to Kaggle GPU Server...")
push_res = run_cmd(f"kaggle kernels push -p {WORKSPACE_DIR}")
print(push_res)

print("⏳ Waiting for Kaggle GPU processing to finish...")
while True:
    time.sleep(30)
    status_out = run_cmd(f"kaggle kernels status {metadata['id']}")
    
    if '"complete"' in status_out or 'complete' in status_out.lower():
        print("\n✅ Kaggle GPU Processing Complete!")
        break
    elif '"error"' in status_out or '"cancel"' in status_out or 'error' in status_out.lower() or 'cancel' in status_out.lower():
        print(f"\n❌ Kaggle Kernel Failed!\nLogs: {status_out}")
        exit(1)
    else:
        print(".", end="", flush=True)

print("📥 Downloading 2.json from Kaggle...")
run_cmd(f"kaggle kernels output {metadata['id']} -p Data/")

print("🎉 Process Finished! Check Data/2.json.")
