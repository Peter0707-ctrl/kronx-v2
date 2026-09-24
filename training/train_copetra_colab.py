"""
=============================================================================
Copetra AI - Google Colab Training Pipeline for Copetra-v1
Target Architecture: Qwen2.5-7B-Instruct / Llama-3.1-8B-Instruct via Unsloth & QLoRA
Execution Environment: Free Google Colab NVIDIA T4 GPU (or A100 / V100)
Outputs: copetra-v1-7b-q4_k_m.gguf (Ready for Ollama / vLLM / llama.cpp)
Zero emojis.
=============================================================================
"""

import os
import torch

def setup_environment():
    print("[1/5] Installing Unsloth and optimized dependencies...")
    os.system("pip install --no-deps \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"")
    os.system("pip install --no-deps trl peft accelerate bitsandbytes")
    os.system("pip install datasets sentencepiece protobuf")

def train_copetra(
    base_model_name: str = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
    dataset_file: str = "copetra_dataset_v1.jsonl",
    output_model_name: str = "copetra-v1-7b",
    max_seq_length: int = 2048,
    epochs: int = 3,
    learning_rate: float = 2e-4
):
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset

    print(f"[2/5] Loading base foundation weights: {base_model_name}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_name,
        max_seq_length=max_seq_length,
        dtype=None,  # Auto-detect FP16 or BF16
        load_in_4bit=True,
    )

    print("[3/5] Attaching LoRA adapters for Copetra custom fine-tuning...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    tokenizer = get_chat_template(
        tokenizer,
        chat_template="chatml",
        mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant", "system": "system"}
    )

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    print(f"[4/5] Loading and formatting dataset: {dataset_file}...")
    dataset = load_dataset("json", data_files=dataset_file, split="train")
    dataset = dataset.map(formatting_prompts_func, batched=True)

    print("[5/5] Launching GPU Training via SFTTrainer...")
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
            warmup_steps=5,
            max_steps=60,
            learning_rate=learning_rate,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="copetra_outputs",
        ),
    )

    trainer.train()

    print("[COMPLETED] Training finished successfully.")
    print("Exporting model to 4-bit GGUF format for Ollama / vLLM / llama.cpp...")
    model.save_pretrained_gguf(output_model_name, tokenizer, quantization_method="q4_k_m")
    print(f"SUCCESS: Exported GGUF model file: {output_model_name}-unsloth.Q4_K_M.gguf")

if __name__ == "__main__":
    setup_environment()
    train_copetra()
