"""Exact source-pinned single-user template realization, not content substring."""
import hashlib
TEMPLATE_SHA='e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259'
PREFIX='<|im_start|>user\n'
SUFFIX='<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
def validate(content,rendered,template):
 if type(template)is not str or len(template.encode())!=7764 or hashlib.sha256(template.encode()).hexdigest()!=TEMPLATE_SHA:raise ValueError('exact original checkpoint chat_template required')
 trimmed=content.strip()
 if not trimmed or rendered!=PREFIX+trimmed+SUFFIX:raise ValueError('official boundary trim only; exact original interior/code/five-shot content')
 return dict(contract='source-pinned-single-user-boundary-trim/v011',original_content_sha256=hashlib.sha256(content.encode()).hexdigest(),template_content_sha256=hashlib.sha256(trimmed.encode()).hexdigest(),leading_characters=len(content)-len(content.lstrip()),trailing_characters=len(content)-len(content.rstrip()),interior_exact=True)
