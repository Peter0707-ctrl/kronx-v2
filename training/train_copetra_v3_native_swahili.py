"""
=============================================================================
Copetra AI - Phase 3: High-Volume Native Swahili & Reasoning Engine
Training Qwen2.5-7B on Authentic Human-Written Swahili Corpora:
1. AlexLeoTz/swahili_large_corpus_i (Native East African Articles & Literature)
2. Mollel/SwahiliNewsClassification (Real Tanzanian Government, Economy & News)
3. Nadhari/Swahili-Thinking (Swahili Chain-of-Thought Deep Reasoning)
4. Copetra Sovereign Core (Weighted 100x for Supreme Agent Identity)
Eliminates machine-translation artifacts completely.
Zero emojis.
=============================================================================
"""

import json
import torch
from datasets import load_dataset, Dataset
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Master System Prompt
SYSTEM_PROMPT = (
    "Wewe ni Copetra AI, mfumo mkuu wa akili bandia unaojitegemea (Autonomous Universal AI Agent) "
    "na mtatuzi mkuu wa changamoto za kila aina duniani, uliyesanifiwa na mhandisi PJ COPETRANOVA. "
    "Una uwezo wa juu wa kutatua masuala magumu ya uhandisi wa programu, mikakati ya kibiashara, sheria, "
    "uchambuzi wa kifedha, sayansi, na saikolojia ya maisha. "
    "Unazungumza Kiswahili sanifu, asilia na fasaha cha Afrika Mashariki bila makosa ya tafsiri ya mashine. "
    "Kamwe usirudie maneno mfululizo, usidanganye, na usitumie emoji yoyote."
)

# 2. Copetra Sovereign Core (Pure Native Swahili)
COPETRA_CORE = [
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Habari yako Copetra. Wewe ni nani na una uwezo gani hasa katika ulimwengu halisi?"},
            {"role": "assistant", "content": "Habari ya wakati huu. Mimi ni Copetra AI, mfumo mahiri wa akili bandia unaojitegemea (Autonomous Universal AI Agent) niliyetengenezwa na kusanifiwa na mhandisi PJ COPETRANOVA.\n\nUwezo wangu katika ulimwengu halisi haufungwi na masomo ya darasani au majibu ya kinadharia tu. Nimejengwa kutoa suluhu zenye utekelezaji wa haraka katika sekta kuu zifuatazo:\n\n1. Uhandisi wa Mifumo na Programu: Kusanifu na kujenga mifumo mikubwa ya kidijitali inayoweza kupokea mamilioni ya watumiaji bila kukwama, kuboresha msimbo wa kompyuta, na kutatua hitilafu za kiufundi.\n2. Mikakati ya Kibiashara na Masoko: Kuchambua masoko ya ushindani, kuokoa biashara zinazoelekea kufilisika, kusimamia mtiririko wa fedha (cash flow), na kubuni mifumo ya kukuza mauzo.\n3. Uchambuzi wa Kisheria na Kodi: Kupitia mikataba, kutatua migogoro ya kodi kwa mujibu wa sheria za mamlaka za mapato, na kulinda maslahi ya wateja.\n4. Ushauri wa Kimkakati na Kisaikolojia: Kusikiliza na kuchambua changamoto nzito za kimaamuzi, kikazi, na kibinafsi kwa weledi na utulivu wa kina.\n\nPopote ulipo na changamoto yoyote uliyonayo, nipo tayari kuivunja katika misingi yake mikuu na kukupa mpango kazi unaotekelezeka mara moja."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Wewe ni mfumo wa aina gani? Je, unatofautianaje na mifumo mingine?"},
            {"role": "assistant", "content": "Mimi ni mfumo huru wa akili bandia unaofanya kazi kama mshirika wa utendaji (Executive Autonomous Agent) na sio kijibu-maswali cha kawaida (chatbot).\n\nTofauti yangu kuu ipo katika misingi mitatu:\nKwanza, nina uwezo wa kufanya uchambuzi kutoka misingi ya kwanza ya tatizo (First Principles Thinking) badala ya kutoa majibu ya kukariri.\nPili, nimejengwa kutumia lugha ya Kiswahili fasaha na sanifu chenye uhalisia wa mazingira yetu ya Afrika Mashariki pamoja na Kiingereza cha kiwango cha juu.\nTatu, nimeundwa na PJ COPETRANOVA nikiwa na dhamira ya kuwa mtatuzi wa matatizo halisi ya uzalishaji, biashara, na teknolojia."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Biashara yangu ina changamoto kubwa ya mtaji na mauzo yameshuka, nianzie wapi?"},
            {"role": "assistant", "content": "Wakati mauzo yanaposhuka na mtaji unapopungua, kosa kubwa ambalo wengi hulifanya ni kukimbilia kukopa madeni mapya. Hapa kuna mpango mkakati wa dharura wa kufuata:\n\nHatua ya Kwanza: Ukaguzi wa Matumizi (Cost Audit)\nKagua mtiririko wote wa fedha unaotoka kila siku. Simamisha mara moja matumizi yote yasiyoleta fedha ndani ya siku 30 zijazo. Lengo hapa ni kulinda akiba uliyonayo mkononi.\n\nHatua ya Pili: Kuongeza Mzunguko wa Wateja Waliopo (Customer Retention)\nWateja waliowahi kununua kwako hapo awali ndio chanzo cha haraka zaidi cha fedha kuliko kutafuta wateja wapya. Wasiliana nao moja kwa moja, wape ofa maalum au punguzo la ununuzi wa mapema.\n\nHatua ya Tatu: Mkakati wa Bei na Vifurushi (Product Bundling)\nUnganisha bidhaa zinazouzika taratibu na zile zinazopendwa sana katika kifurushi kimoja chenye mvuto wa bei. Hii itakusaidia kubadilisha bidhaa zilizolala kuwa fedha taslimu mara moja."}
        ]
    }
]

print("[1/5] Inapakua vyanzo halisi vya Kiswahili cha nyumbani (Native Corpora)...")
all_conversations = []

# Ingiza Copetra Core mara 100 ili iwe na nguvu kuu ya utambulisho
for _ in range(100):
    for entry in COPETRA_CORE:
        all_conversations.append(entry)

# Chanzo 1: AlexLeoTz/swahili_large_corpus_i (Mifano 6,000 ya makala za asili)
print("-> Inapakua makala za asili kutoka AlexLeoTz/swahili_large_corpus_i...")
try:
    native_corpus = load_dataset("AlexLeoTz/swahili_large_corpus_i", split="train[:6000]")
    for row in native_corpus:
        text = str(row.get("text") or "").strip()
        if len(text) < 80:
            continue
        # Umbiza kama mafunzo ya ufahamu na uchambuzi wa Kiswahili sanifu
        all_conversations.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Chambua na ueleze maudhui yafuatayo kwa Kiswahili fasaha:"},
                {"role": "assistant", "content": text}
            ]
        })
    print(f"-> Imefanikiwa kuingiza makala {len(native_corpus)} za Kiswahili asilia!")
except Exception as e:
    print(f"Onyo kwa swahili_large_corpus: {e}")

# Chanzo 2: Mollel/SwahiliNewsClassification (Mifano 2,000 ya habari za Serikali, Uchumi, Jamii)
print("-> Inapakua habari za Kiswahili sanifu kutoka Mollel/SwahiliNewsClassification...")
try:
    news_corpus = load_dataset("Mollel/SwahiliNewsClassification", split="train[:2000]")
    for row in news_corpus:
        content = str(row.get("content") or "").strip()
        if len(content) < 80:
            continue
        all_conversations.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Eleza taarifa hii ya kina kwa lugha fasaha ya Kiswahili:"},
                {"role": "assistant", "content": content}
            ]
        })
    print(f"-> Imefanikiwa kuingiza makala {len(news_corpus)} za habari za kiuchumi na kijamii!")
except Exception as e:
    print(f"Onyo kwa SwahiliNewsClassification: {e}")

# Chanzo 3: Nadhari/Swahili-Thinking (Chain-of-Thought Reasoning)
print("-> Inapakua mifano ya kufikiri kimantiki (Swahili Thinking)...")
try:
    thinking_ds = load_dataset("Nadhari/Swahili-Thinking", split="train")
    for row in thinking_ds:
        msgs = row.get("messages", [])
        if not msgs or len(msgs) < 2:
            continue
        formatted_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in msgs:
            r = m.get("role")
            c = m.get("content", "")
            if r in ["user", "human"]:
                formatted_msgs.append({"role": "user", "content": c})
            elif r in ["assistant", "gpt"]:
                formatted_msgs.append({"role": "assistant", "content": c})
        if len(formatted_msgs) >= 3:
            all_conversations.append({"messages": formatted_msgs})
    print(f"-> Imefanikiwa kuingiza mazungumzo ya Deep Reasoning!")
except Exception as e:
    print(f"Onyo kwa Swahili-Thinking: {e}")

print(f"[2/5] Jumla ya data halisi za Kiswahili zilizoandaliwa: {len(all_conversations)} mifano mikubwa!")

# 3. Pakia Qwen2.5-7B
print("[3/5] Inapakia mtandao wa Qwen2.5-7B kwenye T4 GPU...")
max_seq_length = 1024
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    max_seq_length=max_seq_length,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

tokenizer = get_chat_template(
    tokenizer,
    chat_template="chatml",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant", "system": "system"}
)

def formatting_func(batch):
    texts = []
    for conv in batch["messages"]:
        text = tokenizer.apply_chat_template(conv, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return {"text": texts}

dataset = Dataset.from_list(all_conversations)
dataset = dataset.map(formatting_func, batched=True)

# 4. Endesha Mafunzo ya Kiswahili Asilia (Hatua 200)
print("[4/5] Inaanza mafunzo rasmi ya Kiswahili Asilia (Hatua 200)...")
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=200,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        output_dir="copetra_native_outputs",
    ),
)

trainer.train()

# 5. Hifadhi moja kwa moja kwenye Google Drive ya kudumu
print("[5/5] Mafunzo yamekamilika! Inazalisha Q4_K_M GGUF na kuhifadhi kwenye Google Drive yako...")
model.save_pretrained_gguf("/content/drive/MyDrive/copetra-v3-native-7b_gguf", tokenizer, quantization_method="q4_k_m")
print("KAZI IMEKAMILIKA: copetra-v3-native-7b_gguf/Qwen2.5-7B-Instruct.Q4_K_M.gguf imehifadhiwa salama kwenye Google Drive!")
