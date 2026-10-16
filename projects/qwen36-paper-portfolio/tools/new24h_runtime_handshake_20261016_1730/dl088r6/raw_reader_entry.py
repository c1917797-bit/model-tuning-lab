"""Transparent lossless raw hydration before original reviewed CPU consumers."""
import argparse,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 p=argparse.ArgumentParser(add_help=False,allow_abbrev=False);p.add_argument('--script',choices=('consume.py','domain_entry.py','run_consumer088.py'),required=True);a,left=p.parse_known_args()
 import torch,raw_codec
 raw_codec.install(torch);sys.argv=[str(P/a.script),*left];runpy.run_path(str(P/a.script),run_name='__main__')
if __name__=='__main__':main()
