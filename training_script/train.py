"""
RunPod Fine-tuning Script with Unsloth (Faster & Memory Efficient)
Base Model: Llama-3-8B-Instruct (Korean Optimized)
"""

import os
import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import pandas as pd

# 1. Configuration
MAX_SEQ_LENGTH = 2048  # Supports up to 8192 for Llama-3
DTYPE = None  # None = Float16 for Tesla T4, Bfloat16 for Ampere+
LOAD_IN_4BIT = True  # Quanitzation for memory efficiency

# Base Model (You can change this to 'meta-llama/Meta-Llama-3-8B-Instruct')
# Using a Korean-finetuned base can yield better results
MODEL_ID = "unsloth/llama-3-8b-Instruct-bnb-4bit" 
NEW_MODEL_NAME = "haruON-llama3-v1"
HF_USERNAME = "slyeee"  # Change this to your HF username
HF_TOKEN = os.getenv("HF_TOKEN") # Load from environment variable

def format_conversation(row):
    """
    Convert ChatML JSONL format to Llama-3 Prompt Format
    Input: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    messages = row['messages']
    
    # Extract content by role (Safe Robust Way)
    system_text = next((m['content'] for m in messages if m['role'] == 'system'), 
                       "당신은 깊은 공감 능력과 전문성을 갖춘 심리 상담 AI '마음이'입니다.")
    user_text = next((m['content'] for m in messages if m['role'] == 'user'), "")
    ai_text = next((m['content'] for m in messages if m['role'] == 'assistant'), "")
    
    # Llama-3 Chat Template logic remains the same
    text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_text}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{ai_text}<|eot_id|>"
    return {"text": text}

def train():
    print("🚀 [Training] Initializing Unsloth Model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_ID,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=DTYPE,
        load_in_4bit=LOAD_IN_4BIT,
    )

    # Add LoRA Adapters (Efficient Fine-tuning)
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

    print("📂 [Data] Loading Datasets...")
    # Load JSONL files
    dataset_train = load_dataset('json', data_files='data/final_train.jsonl', split='train')
    dataset_valid = load_dataset('json', data_files='data/final_valid.jsonl', split='train')

    # Format Data
    dataset_train = dataset_train.map(format_conversation)
    dataset_valid = dataset_valid.map(format_conversation)

    print(f"✅ Loaded {len(dataset_train)} train samples and {len(dataset_valid)} validation samples.")

    # Training Arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60, # Adjust based on data size (e.g., 1 epoch)
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset_train,
        eval_dataset=dataset_valid,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    print("🔥 [Training] Start Fine-tuning...")
    trainer.train()

    print("💾 [Save] Saving Model...")
    model.save_pretrained(NEW_MODEL_NAME)
    tokenizer.save_pretrained(NEW_MODEL_NAME)
    
    # 4. Push to Hugging Face (Optional)
    if HF_TOKEN:
        print(f"☁️ [Upload] Pushing to Hugging Face: {HF_USERNAME}/{NEW_MODEL_NAME}")
        model.push_to_hub(f"{HF_USERNAME}/{NEW_MODEL_NAME}", token=HF_TOKEN)
        tokenizer.push_to_hub(f"{HF_USERNAME}/{NEW_MODEL_NAME}", token=HF_TOKEN)
        print("✅ [Success] Model Uploaded!")
    else:
        print("⚠️ [Skip] No HF_TOKEN found. Model saved locally.")

if __name__ == "__main__":
    train()
