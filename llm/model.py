from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class ChatLLM:
    def __init__(
        self,
        model_name: str = "yandex/YandexGPT-5-Lite-8B-instruct",
        device: str = "cuda",
        dtype: torch.dtype = torch.float16
    ):
        self.device = torch.device(
            device if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device,
            torch_dtype="auto"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Ты — полезный ассистент, который всегда даёт точные и информативные ответы.",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95
    ) -> str:
        # Формируем сообщения согласно документации
        messages = [{"role": "user", "content": prompt}]

        # Применяем чат-шаблон как в официальном примере
        input_ids = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            return_tensors="pt"
        ).to(self.device)

        # Генерация
        outputs = self.model.generate(
            input_ids,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )

        # Декодируем только новые токены как в документации
        response = self.tokenizer.decode(
            outputs[0][input_ids.size(1):],
            skip_special_tokens=True
        )

        return response.strip()
