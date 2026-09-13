"""External lm-eval backend: native templates with explicit thinking disabled.

No installed harness/framework files are changed. For standard MMLU/GSM8K use
this LM object with simple_evaluate(apply_chat_template=True). Tokenized requests
preserve the locally rendered native template when calling /v1/completions.
HumanEval generated-code execution remains a separate CPU-sandbox stage.
"""
from lm_eval.models.openai_completions import LocalCompletionsAPI


class NoThinkingCompletions(LocalCompletionsAPI):
    def apply_chat_template(self, chat_history, add_generation_prompt=True):
        if self.tokenizer_backend != "huggingface" or not self.tokenized_requests:
            raise ValueError("No-thinking quality protocol requires local HF tokenized requests")
        return self.tokenizer.apply_chat_template(
            chat_history,
            tokenize=False,
            add_generation_prompt=add_generation_prompt,
            continue_final_message=not add_generation_prompt,
            enable_thinking=False,
        )

    @property
    def tokenizer_name(self):
        return str(self.tokenizer.name_or_path) + ":thinking-disabled"
