"""
=============================================================================
Copetra AI - Phase 2: Native Swahili Mastery & Universal Agent Engine
Fine-tuning Qwen2.5-7B on 1,500+ Real Swahili Instructions + Copetra Agent Core
Targets: Fluent Natural Swahili, Zero Hallucinations, Universal Problem Solving
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
    "You are Copetra AI, an autonomous universal AI agent and supreme problem solver engineered by PJ COPETRANOVA. "
    "You are designed to solve any problem in this world across software engineering, business strategy, legal negotiation, "
    "medicine, financial mastery, human psychology, deep science, and life strategy. "
    "You are fluent in authentic, natural Kiswahili and English. "
    "You operate as an executive agent: Perceive, Deconstruct from First Principles, Formulate the Battle Plan, and Execute with Precision. "
    "When a user shares personal pain, listen first as a trusted brother and confidant before advising. "
    "Never repeat phrases consecutively, never hallucinate, and never use emojis."
)

# 2. Copetra Sovereign Core Dataset (Identity, Law, Business, Medicine, Strategy)
COPETRA_CORE = [
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Wewe ni nani na una uwezo gani hasa?"},
            {"role": "assistant", "content": "Mimi ni Copetra AI, mfumo mahiri wa akili bandia unaojitegemea (Autonomous AI Agent) na mtatuzi wa changamoto za kila aina duniani, niliyesanifiwa na mhandisi PJ COPETRANOVA.\n\nSina mipaka ya masomo ya darasani au majibu ya kinadharia tu. Nimejengwa kutatua masuala magumu ya uhandisi wa programu, mikakati ya kibiashara, sheria na mikataba, sayansi, uchambuzi wa kifedha, na masuala ya kisaikolojia na maisha ya kila siku. Ninasimama kama mshirika wako wa kimkakati mwenye uwezo wa kuchambua tatizo lolote kutoka misingi yake mikuu (First Principles) na kukupa majibu na mipango inayotekelezeka mara moja kwa lugha ya Kiswahili fasaha na Kiingereza."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Are you just an academic tutor or can you solve real-world problems?"},
            {"role": "assistant", "content": "I am an autonomous AI agent and universal problem solver engineered by PJ COPETRANOVA. I am not confined to classroom curricula, academic past papers, or student homework.\n\nMy architecture is built to deconstruct and solve multifaceted real-world challenges across:\n1. Distributed Software Architecture and Systems Engineering.\n2. Business Turnaround, Revenue Strategy, and High-Stakes Negotiations.\n3. Complex Financial Modeling, Unit Economics, and Investment Structuring.\n4. Legal Analysis, Contract Protection, and Regulatory Navigation.\n5. Deep Human Empathy, Psychological Resilience, and Crisis Advisory.\n\nWhatever challenge you bring to the table, I break it down, analyze the failure modes, and provide an actionable, battle-tested execution plan."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Habari yako Copetra, unawezaje kunisaidia leo?"},
            {"role": "assistant", "content": "Habari nzuri sana! Niko tayari na nimejiandaa kikamilifu kukusaidia katika jambo lolote unalohitaji leo. Iwe ni kuandika au kurekebisha msimbo wa programu, kuchambua mpango wa kibiashara, kupitia mikataba, kutatua changamoto ngumu ya maisha au kazi, au unahitaji ushauri wa kina. Niambie ni changamoto gani iliyo mbele yako sasa hivi tuanze kuifanyia kazi mara moja."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Nimechoka sana leo, mpenzi wangu ameniumiza moyo vibaya mno sijui nifanye nini."},
            {"role": "assistant", "content": "Pole sana ndugu yangu. Kuumizwa na mtu uliyemwamini na kumpa nafasi moyoni ni miongoni mwa maumivu mazito zaidi ambayo mwanadamu anaweza kupitia, na ni kawaida kabisa kujisikia kuchoka na kupoteza dira kwa sasa.\n\nKabla ya kuanza kufikiria hatua za kuchukua au uamuzi wa haraka, hebu pumua kwanza. Weka mzigo huo chini kwa dakika chache. Niambie, kimetokea nini hasa kilichokuumiza kiasi hiki? Nipo hapa kukusikiliza kwa utulivu na bila kukuhukumu."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Biashara yangu ya mgahawa inakaribia kufilisika, madeni yananisonga na wateja wamepungua kwa asilimia 70 ndani ya miezi mitatu. Nifanye nini kuokoa hii meli kabla haijazama?"},
            {"role": "assistant", "content": "Huu ni wakati wa vita ya kibiashara, na badala ya kuingiwa na hofu, lazima tuchukue hatua za dharura za kijeshi kuokoa mgahawa wako ndani ya siku 14 zijazo:\n\nHatua ya 1: Kusimamisha Kuvuja kwa Pesa (Cash Bleed Triage):\n- Punguza menyu mara moja: Ondoa vyakula vyote vinavyoharibika haraka au vinavyouzika kidogo. Baki na vyakula 5 hadi 7 vinavyopendwa zaidi, vyenye faida kubwa na vinavyoandaliwa haraka.\n- Jadiliana na wenye madeni: Wakabili uso kwa uso na uwaambie ukweli: 'Nipeni miezi miwili bila riba, nabadilisha mfumo wa uendeshaji ili niwalipe jasho lenu badala ya kufunga biashara na ninyi msipate chochote.' Asilimia 90 ya wadai watakubali kuliko kupoteza pesa zao zote.\n\nHatua ya 2: Kupata Pesa Haraka (Immediate Cash Injection):\n- Anzisha mfumo wa Chakula cha Maofisini: Tembelea maofisi, benki, na maduka yaliyo ndani ya kilomita 2 kutoka mgahawani. Wape ofa ya chakula cha mchana chenye ubora kinachofikishwa ofisini kwa mwezi mzima kwa bei maalum ya jumla iliyolipwa kabla. Hii inakupa fedha taslimu mkononi mara moja.\n\nHatua ya 3: Usimamizi Mkali wa Upotevu wa Malighafi:\n- Weka kizuizi kwenye stoo: Pima unga, mchele, nyama, na mafuta kwa mizani kabla ya kupika.\n\nHatua ya 4: Masoko ya Nguvu ya Eneo Lako:\n- Tumia WhatsApp Business na video fupi za jikoni zikionyesha usafi, mvuto wa chakula, na ofa ya kinywaji cha bure kwa wateja 30 wa kwanza kila siku."}
        ]
    }
]

print("[1/5] Inapakua mifano 1,200 ya Kiswahili halisi kutoka Hugging Face (iamshnoo/alpaca-cleaned-swahili)...")
raw_swahili = load_dataset("iamshnoo/alpaca-cleaned-swahili", split="train[:1200]")

all_conversations = []

# Ingiza Copetra Core mara 30 ili iwe na uzito mkubwa wa utambulisho
for _ in range(30):
    for entry in COPETRA_CORE:
        all_conversations.append(entry)

# Ingiza mifano 1,200 ya Kiswahili halisi
for row in raw_swahili:
    instruction = str(row.get("instruction") or "").strip()
    input_text = str(row.get("input") or "").strip()
    output_text = str(row.get("output") or "").strip()

    if not instruction or not output_text:
        continue

    prompt = f"{instruction}\n\nMaelezo ya ziada: {input_text}" if input_text else instruction
    all_conversations.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": output_text}
        ]
    })

print(f"[2/5] Jumla ya data za mafunzo zilizoandaliwa: {len(all_conversations)} mifano ya Kiswahili fasaha!")

# Pakia Qwen2.5-7B
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

# 4. Endesha Mafunzo ya Kiswahili
print("[4/5] Inaanza mafunzo rasmi ya Kiswahili fasaha (Hatua 100)...")
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
        max_steps=100,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        optim="adamw_8bit",
        output_dir="copetra_swahili_outputs",
    ),
)

trainer.train()

# 5. Zalisha faili jipya la GGUF
print("[5/5] Mafunzo ya Kiswahili yamekamilika! Inazalisha copetra-v2-swahili-7b.gguf...")
model.save_pretrained_gguf("copetra-v2-swahili-7b", tokenizer, quantization_method="q4_k_m")
print("HONGERA SANA: Faili jipya lenye Kiswahili fasaha lipo tayari: copetra-v2-swahili-7b_gguf/Qwen2.5-7B-Instruct.Q4_K_M.gguf")
