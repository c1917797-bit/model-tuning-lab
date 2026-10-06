"""Deterministically copy one exact publisher TRAIN prompt; no tokenizer/padding/eval fallback."""
import argparse
from pathlib import Path
from diag_contract import canonical,make_manifest,source_contract,write_new

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    source_contract()
    write_new(Path(a.output),make_manifest())
if __name__=="__main__":
    main()
