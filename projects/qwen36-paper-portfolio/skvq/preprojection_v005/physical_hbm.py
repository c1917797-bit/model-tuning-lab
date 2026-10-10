"""Unchanged reviewed physical HBM predicate; no borrowed algorithm authority."""
import re
import current_contract as c
PHYSICAL=(4,5,6,7)
def actual_hbm(text,card):
 # npu-smi25.2 puts Memory and HBM in ONE third pipe segment.
 # Bind the exact header/order, then fullmatch both ratios; never search
 # the first ratio or guess a new pipe column from a different device format.
 c.require(type(card) is int and card in PHYSICAL,"actual owned physical4..7 only")
 lines=text.splitlines()
 headers=[l.split("|") for l in lines if re.match(r"\|\s*Chip\b",l)]
 c.require(len(headers)==1,"one actual Chip/Bus/AICore/Memory/HBM header")
 header=headers[0]
 c.require(len(header)==5 and not header[0].strip() and not header[4].strip() and
  header[1].strip()=="Chip" and header[2].strip()=="Bus-Id" and
  re.fullmatch(r"AICore\(%\)\s+Memory-Usage\(MB\)\s+HBM-Usage\(MB\)",header[3].strip()) is not None,
  "actual third-segment header AICore then Memory then HBM, units MB")
 indices=[i for i,l in enumerate(lines) if re.match(r"\|\s*"+str(card)+r"\s+910B4\s*\|",l)]
 c.require(len(indices)==1 and indices[0]+1<len(lines),"unique installed910B4 card and following chip row")
 health=lines[indices[0]].split("|")
 c.require(len(health)==5 and not health[0].strip() and not health[4].strip() and
  health[2].strip()=="OK","actual owned-card health OK")
 parts=lines[indices[0]+1].split("|")
 c.require(len(parts)==5 and not parts[0].strip() and not parts[4].strip() and parts[1].strip()=="0" and
  re.fullmatch(r"[0-9A-Fa-f]{4}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\.[0-7]",parts[2].strip()) is not None,
  "complete actual chip0 Bus-Id and one metrics segment")
 match=re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s+([0-9]+)\s*/\s*([0-9]+)\s+([0-9]+)\s*/\s*([0-9]+)\s*",parts[3])
 c.require(match is not None,"actual AICore plus exactly Memory and HBM ratios; unknown schema rejected")
 core,mem_used,mem_total,used,total=match.groups()
 c.require(0<=float(core)<=100 and 0<=int(mem_used)<=int(mem_total),"finite actual AICore and Memory range")
 used,total=int(used),int(total)
 c.require(total==32768 and 0<=used<=total-c.HBM_RESERVE_MIB,
  "actual physical HBM reserve3GiB percard; include full weights/native/GDN/allaux/driver, no allocator simulation")
 return dict(physical=card,used_mib=used,total_mib=total,reserve_mib=c.HBM_RESERVE_MIB,full_actual_physical_hbm=True)
