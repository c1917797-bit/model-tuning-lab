"""OpenAI completion SSE measurement; no inference or algorithm implementation."""
import json
import math

def measure_stream(lines,*,started,clock):
    first=None;usage=None;finish=None;text=[]
    done=False
    for raw in lines:
        if isinstance(raw,bytes):raw=raw.decode("utf-8")
        line=raw.strip()
        if not line or line.startswith(":"):continue
        if not line.startswith("data:"):raise ValueError("unexpected SSE field")
        data=line[5:].strip()
        if data=="[DONE]":
            done=True;break
        packet=json.loads(data)
        if packet.get("error"):raise ValueError("service stream error")
        for choice in packet.get("choices",[]):
            if choice.get("index",0)!=0:raise ValueError("single-choice protocol required")
            content=choice.get("text","")
            if not isinstance(content,str):raise ValueError("text completion required")
            if content:
                if first is None:first=clock()
                text.append(content)
            if choice.get("finish_reason") is not None:
                finish=choice["finish_reason"]
        if packet.get("usage") is not None:usage=packet["usage"]
    ended=clock()
    if not done or first is None or finish is None or usage is None:
        raise ValueError("incomplete stream/first-token/finish/usage evidence")
    count=usage.get("completion_tokens")
    if type(count) is not int or count<1:raise ValueError("invalid completion token count")
    if not all(math.isfinite(x) for x in (started,first,ended)) or not started<=first<=ended:
        raise ValueError("invalid monotonic timestamps")
    # Match the supplied successful-case ruler: divide by output_tokens.
    # Do not relabel this as the output_tokens-1 convention.
    return {"started":started,"first_content":first,"ended":ended,
            "ttft_ms":1000*(first-started),"duration_ms":1000*(ended-started),
            "tpot_ms":1000*(ended-first)/count,
            "tpot_denominator":"completion_tokens",
            "completion_tokens":count,"finish_reason":finish,"usage":usage,
            "text":"".join(text)}
