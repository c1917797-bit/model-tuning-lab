"""CPU-only format audit cases, including malformed historical messages."""
import runpy
from pathlib import Path

inspect = runpy.run_path(str(Path(__file__).with_name(
    "audit_sparse_prompt_format.py")), run_name="__mp_main__")["inspect_prompt"]
good = inspect("<|im_start|>user\nhello<|im_end|>\n<|im_start|>assistant\n")
assert good["messages"] == 1 and good["generation_stub"] == 1
assert good["missing_role_newline"] == good["unclosed_message"] == 0
bad = inspect("<|im_start|>systemrules<|im_end|><|im_start|>assistant"
              "<|im_end|><|im_start|>userhi<|im_end|><|im_start|>assistant")
assert bad["missing_role_newline"] == 3
assert bad["empty_closed_assistant"] == 1
assert bad["generation_stub_without_newline"] == 1
assert inspect("<|im_end|>")["orphan_end"] == 1
assert inspect("<|im_start|>user\nx<|im_start|>assistant")["unclosed_message"] == 1
assert inspect("<|im_start|>alien\nx<|im_end|>")["unknown_role"] == 1
assert inspect("<|im_start|>assistant\npartial")["unclosed_message"] == 1
try:
    inspect(None)
except ValueError:
    pass
else:
    raise AssertionError("non-string accepted")
print("PASS raw prompt format audit cases; no model or data import")
