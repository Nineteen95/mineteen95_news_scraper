import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel


def summarize_text(text):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print('CUDA доступна, используем устройство:', device)
    else:
        device = torch.device("cpu")
        print('CUDA недоступна, используем устройство:', device)

    # Загружаем модель
    model = GPT2LMHeadModel.from_pretrained('gpt2', output_hidden_states=True)
    model.to(device)

    input_ids = tokenizer.encode(text, return_tensors='pt')
    output = model.generate(input_ids, max_length=120, num_beams=5, no_repeat_ngram_size=2, early_stopping=True)

    summary = tokenizer.decode(output[0], skip_special_tokens=True)

    return summary
