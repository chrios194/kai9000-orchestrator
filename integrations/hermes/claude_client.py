"""
Claude API Client — Foundation v1.0
Универсальный клиент с кэшированием, историей сообщений и memory state.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic


# --- Конфигурация ---

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MEMORY_FILE = Path(__file__).parent / "memory_state.yaml"


# --- Клиент ---

client = anthropic.Anthropic()  # берёт ключ из ANTHROPIC_API_KEY env var


# --- System Prompt ---
# Загружается из файла — удобнее редактировать отдельно

SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt_fundament.md"


def load_system_prompt() -> str:
    """Загрузить system prompt из файла."""
    if SYSTEM_PROMPT_FILE.exists():
        return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(
        f"System prompt не найден: {SYSTEM_PROMPT_FILE}\n"
        "Создайте файл system_prompt.md рядом с этим скриптом."
    )


def load_memory() -> str:
    """Загрузить memory state из YAML файла."""
    if MEMORY_FILE.exists():
        return MEMORY_FILE.read_text(encoding="utf-8").strip()
    return ""


def save_memory(yaml_text: str) -> None:
    """Сохранить обновлённый memory state."""
    MEMORY_FILE.write_text(yaml_text, encoding="utf-8")


# --- Сессия с историей сообщений ---

class Session:
    """
    Сессия разговора с полной историей.
    Каждое сообщение сохраняется — модель помнит весь контекст.
    """

    def __init__(self):
        self.messages: list[dict] = []
        self.created_at = datetime.now(timezone.utc)

    def ask(self, user_message: str) -> str:
        """Отправить сообщение и получить ответ с полным контекстом."""

        system_prompt = load_system_prompt()
        memory = load_memory()

        # System: статичный промпт (кэшируется) + динамический memory (не кэшируется)
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if memory:
            system_blocks.append({
                "type": "text",
                "text": f"[MEMORY STATE]\n{memory}",
            })

        # Добавляем сообщение пользователя в историю
        self.messages.append({"role": "user", "content": user_message})

        # Вызов API с retry
        response = self._call_with_retry(system_blocks)

        # Извлекаем текст ответа
        reply = self._extract_text(response)

        # Добавляем ответ в историю
        self.messages.append({"role": "assistant", "content": reply})

        # Проверяем наличие [MEMORY UPDATE] в ответе
        self._check_memory_update(reply)

        return reply

    def _call_with_retry(self, system_blocks: list, max_retries: int = 3) -> object:
        """Вызов API с обработкой rate limit и сетевых ошибок."""
        for attempt in range(max_retries):
            try:
                return client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=system_blocks,
                    messages=self.messages,
                )
            except anthropic.RateLimitError:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                print(f"[rate limit] ждём {wait}s...")
                time.sleep(wait)
            except anthropic.APIConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"[connection error] попытка {attempt + 1}/{max_retries}: {e}")
                time.sleep(2)
            except anthropic.APIStatusError as e:
                # 4xx кроме 429 — не ретраить
                if e.status_code < 500 and e.status_code != 429:
                    raise
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt * 3)

        raise RuntimeError("Все попытки исчерпаны")

    @staticmethod
    def _extract_text(response) -> str:
        """Безопасное извлечение текста из ответа."""
        if not response.content:
            return "[пустой ответ от модели]"
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return "[ответ без текстового блока]"

    @staticmethod
    def _check_memory_update(reply: str) -> None:
        """Если модель выдала [MEMORY UPDATE] — сохраняем."""
        marker = "[MEMORY UPDATE]"
        if marker in reply:
            idx = reply.index(marker) + len(marker)
            yaml_block = reply[idx:].strip()
            # Ищем YAML-блок (до конца или до следующей секции)
            if yaml_block.startswith("```"):
                # Убираем markdown code fence
                lines = yaml_block.split("\n")
                yaml_lines = []
                inside = False
                for line in lines:
                    if line.strip().startswith("```") and not inside:
                        inside = True
                        continue
                    if line.strip() == "```" and inside:
                        break
                    if inside:
                        yaml_lines.append(line)
                yaml_block = "\n".join(yaml_lines)

            if yaml_block:
                save_memory(yaml_block)
                print("[memory updated]")

    def reset(self) -> None:
        """Сбросить историю (новая сессия)."""
        self.messages.clear()
        self.created_at = datetime.now(timezone.utc)

    @property
    def message_count(self) -> int:
        return len(self.messages) // 2  # пары user/assistant


# --- CLI интерфейс ---

def main():
    """Простой REPL для работы из терминала."""
    print("Claude Foundation Client v1.0")
    print("Команды: /new (новая сессия), /mem (показать memory), /quit (выход)")
    print("-" * 40)

    session = Session()

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[выход]")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/new":
            session.reset()
            print("[новая сессия]")
            continue
        if user_input == "/mem":
            mem = load_memory()
            print(mem if mem else "[memory пуст]")
            continue

        try:
            reply = session.ask(user_input)
            print(f"\n{reply}")
        except Exception as e:
            print(f"\n[ошибка] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
