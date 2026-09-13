"""Use the actual local tokenizers without issuing any inference requests."""
import argparse
import hashlib
from no_thinking_api import NoThinkingCompletions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tokenizers", nargs="+")
    args = parser.parse_args()
    for path in args.tokenizers:
        lm = NoThinkingCompletions(
            model="offline-fixture", tokenizer=path,
            tokenizer_backend="huggingface", tokenized_requests=True,
            base_url="http://127.0.0.1:1/v1/completions",
            max_length=40960, trust_remote_code=False,
        )
        messages = [{"role": "user", "content": "What is 2 plus 2?"}]
        actual = lm.apply_chat_template(messages)
        expected = lm.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            continue_final_message=False, enable_thinking=False)
        enabled = lm.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            continue_final_message=False, enable_thinking=True)
        assert actual == expected and actual != enabled
        tokens = lm.tokenizer.encode(actual, add_special_tokens=False)
        payload = lm._create_payload([tokens], generate=False)
        assert payload["prompt"] == [tokens] and payload["echo"] is True
        assert payload["logprobs"] == 1
        continuation = messages + [{"role": "assistant", "content": "Answer:"}]
        assert lm.apply_chat_template(continuation, False) == lm.tokenizer.apply_chat_template(
            continuation, tokenize=False, add_generation_prompt=False,
            continue_final_message=True, enable_thinking=False)
        lm.tokenized_requests = False
        try:
            lm.apply_chat_template(messages)
        except ValueError:
            pass
        else:
            raise AssertionError("uncontrolled template backend was accepted")
        print("PASS", path, "render_sha256", hashlib.sha256(actual.encode()).hexdigest())
    print("No network or model inference performed; API scoring still needs live canary")


if __name__ == "__main__":
    main()
