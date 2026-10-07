"""Current MA070e release only. Running/failed numeric results never become PASS."""
from __future__ import annotations
import json
from pathlib import Path
from v2_contract import file_sha, require, v1

OP="exec-000000000000070e"
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
ROOT=Path("/cache/cch/qwen36-damp-20261006/allT-dispatch-selected_row_bal_v1")
ADMISSION_SHA="5733e97b13d9def37625d5b7dffbb624e9cc4e92245ced626ad67b06813f1ab0"
PLAN_SHA="26bf109d7f6b680b7111c1c02fbe130c91a25d240d799a48a9a712c407067838"
PACKET_SHA="61cec4646d5721c7c793aa85e842c507edc34c0d8566abc72bf5f789c476844d"
OWNER="damp-allT-dispatch-v1"
RUN_LABEL="selected_row_bal_v1"
IDS={
4:"63f9a6cea8729f5b943c0bfbe4745188d5f09935a48706ca2f0cff2adae62ec8",
5:"4a66d94b3642effc5e4dcf490648d87756c420f2c8a64281ae5d8b1e31e26381",
6:"53f9efa3e4982492ac9b206d1ee5e2c4d79698db7b96940a9a23c771d4523658",
7:"a5bc47197540c0fd97cf1f3adbfcf9e80548af3d2f0bc6dca37684b24ec121ad"}
SHAS={
4:"3b08af992b969e4b56c7e087457ee9e2082e40556074fb95d660583b019b9ff7",
5:"bba9dbd852f6965d086ed0dca27002fb541a94fe5d1e213d00980de3577f6f2f",
6:"72f3942a934d0cd03659f4752d5a76a278c8e4d44dbf326998ae23e44772335e",
7:"b99bcca4fa807122aedc8724b795e6dee44efacf5956f2147bd63c0583676122"}

def identity(value,card):
    old=v1(); h=value["HostConfig"];labels=value["Config"].get("Labels") or {}
    expected={"/dev/davinci"+str(card):"/dev/davinci0",
              "/dev/davinci_manager":"/dev/davinci_manager",
              "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
    devices=h.get("Devices") or []
    require(value["Id"]==IDS[card] and
            value["Name"]=="/qwen36_damp_allt_npu"+str(card)+"_20261006_selected_row_bal_v1" and
            value["Image"]==old.IMAGE and labels.get("model-tuning-lab.owner")==OWNER and
            labels.get("model-tuning-lab.run")==RUN_LABEL and h["Privileged"] is False and
            not h.get("DeviceRequests") and len(devices)==4 and
            {x["PathOnHost"]:x["PathInContainer"] for x in devices}==expected and
            all(x["CgroupPermissions"]=="rwm" for x in devices),
            "current070e immutable identity/device scope drift")
    return {"id":value["Id"],"name":value["Name"],"image":value["Image"],
            "owner":OWNER,"run":RUN_LABEL,"physical":card,
            "state":value["State"],"devices":devices}

def current_allT(value):
    if value["Id"] not in IDS.values(): return False
    card=next(c for c,i in IDS.items() if value["Id"]==i)
    identity(value,card)
    return True

def references(paths,shas):
    require(len(paths)==len(shas)==4,"four actual current070e proofs required")
    require(file_sha(ROOT/"admission.json")==ADMISSION_SHA and
            file_sha(ROOT/"launch/EXECUTION_PLAN.json")==PLAN_SHA,"current launch provenance drift")
    old=v1()
    require(file_sha(old.ROOT/"projects/damp-ascend/tools/selected_row_dispatch_v1/PACKET.json")==PACKET_SHA,
            "current070e packet drift")
    admission=json.loads((ROOT/"admission.json").read_text())
    refs=[];proofs=[]
    for card,path,sha in zip((4,5,6,7),paths,shas):
        row=admission["cards"][str(card)]
        expected=Path(row["device_proof"])
        require(Path(path).resolve()==expected and sha==row["device_proof_sha256"]==SHAS[card] and
                file_sha(path)==sha and row["container_id"]==IDS[card],
                "actual current070e producer Ref drift")
        proof=json.loads(Path(path).read_text())
        require(proof["container_id"]==IDS[card] and proof["logical_to_physical"]=={"0":card} and
                proof["physical_npu_ids"]==[card] and proof["privileged"] is False,
                "actual current070e proof fields differ")
        identity(proof["container_inspect"],card)
        refs.append({"path":str(expected),"sha256":sha});proofs.append(proof)
    return refs,proofs

def stopped(proofs,read_inspect):
    require(len(proofs)==4,"four current070e identities required")
    actual=[]
    for card,proof in zip((4,5,6,7),proofs):
        identity(proof["container_inspect"],card)
        value=read_inspect(IDS[card])
        require(value is not None,"current070e retained container missing")
        row=identity(value,card)
        require(value["State"]["Running"] is False and value["State"]["Pid"]==0,
                "current070e not actually stopped/PID0")
        actual.append(row)
    return actual

def terminal(payload):
    old=v1()
    root=payload.get("structuredContent",payload);op=root["operation"];r=op["result"]["record"]
    require(root["schema"]=="agentweb.operation/v1" and root["operationId"]==OP and
            root["terminal"] is True and root["phase"]==root["status"]=="completed" and
            op["routeDecision"]=="peer_direct" and op["targetPeerId"]==PEER and
            op["fallbackUsed"] is False and r["id"]==OP and r["state"]=="completed" and
            r["cancelled"] is False and r["timedOut"] is False and type(r["exitCode"]) is int and
            r["cwd"]==str(old.ROOT),"current actual MAIN070e terminal/route required")
    return {"operation_id":OP,"peer":PEER,"exit_code":r["exitCode"],
            "scheduling_terminal_only":True,"numerical_pass_claimed":False}

HOST_REFS={
"FAILURE.json":"c30bef4436562085165fd273f21c22eeb163eafa843a7574c24c29dcb8c2d567",
"STOP_RETAIN.json":"4259d591b59c82cda036304c7da4b2484c84d3e141e7c39376d5cf8825f8a67b",
"POST_RELEASE.json":"6bd2b348f54c6bfb77e50f72583bc500138d6f8f9ef25ee8af41600008e3d752",
"parallel-docker_gate_exec_argv-physical4.receipt.json":"166a5874ac9aa5168adbcd006d346f33baf46d0bf88d14357c32426d1543d6e7",
"parallel-docker_gate_exec_argv-physical5.receipt.json":"3cda0e635e1c093672acbcd7f49c3882f8dbd548fdc22e3eaa0c776268cb0493",
"parallel-docker_gate_exec_argv-physical6.receipt.json":"40018f313339139df9987e46fd0dbd6b107c0317ce6d501aac1e948e253cab2b",
"parallel-docker_gate_exec_argv-physical7.receipt.json":"3fad1f7548c922b92a8bbcdc7c1495a05e0a17b1eae46f67a8c9c1f5805ecf49",
"10310-owned-stop.receipt.json":"95da9f6e854e41be43b0cbfd8087e7f30206ef1018a54ee9538c7e359fb2894c",
"10311-stop-afterinspect.receipt.json":"7609f420438b3dbfa2ff41a448bab0a5472adb28a1a12e1fa3545ff55e9791e5",
"10313-owned-stop.receipt.json":"936389a7d0841770e2484db0a5eacc3672d07f07b990f8ae5746db3b9f8f7a06",
"10314-stop-afterinspect.receipt.json":"3cb01c63868632086c6e3bbb3e7c7c4674d0364248892515ad8970767b4d0c33",
"10316-owned-stop.receipt.json":"efb631079d6ed2c270c5d82429ad6e093df2f124f0ced229817ae56af99654eb",
"10317-stop-afterinspect.receipt.json":"4671dd7366625dc8aa7d68106003deebeb13a2323c9ceb1d40a6c3fd81a1f002",
"10319-owned-stop.receipt.json":"80b15ac5c79c9b8553334733fe7f48de8acdbbc13421fa29ed5b71e3c3a48090",
"10320-stop-afterinspect.receipt.json":"87bb0174bd814fd2550805ff1437121fcb7c7e471e895164ebdf7b193e3b3ae3"}
STOP_NAMES={4:("10310-owned-stop.receipt.json","10311-stop-afterinspect.receipt.json"),
5:("10313-owned-stop.receipt.json","10314-stop-afterinspect.receipt.json"),
6:("10316-owned-stop.receipt.json","10317-stop-afterinspect.receipt.json"),
7:("10319-owned-stop.receipt.json","10320-stop-afterinspect.receipt.json")}

def no_exec_clients(proc=Path("/proc")):
    observed=[]
    for item in proc.iterdir():
        if not item.name.isdigit(): continue
        try: argv=(item/"cmdline").read_bytes().split(b"\0")
        except (FileNotFoundError,ProcessLookupError): continue
        if len(argv)>=3 and Path(argv[0].decode(errors="strict")).name=="docker" and argv[1]==b"exec":
            targets=set(x.decode(errors="strict") for x in argv[2:] if x).intersection(IDS.values())
            for ident in targets:
                observed.append({"pid":int(item.name),"container_id":ident})
    require(not observed,"current070e host docker exec client still present")
    return {"scope":"fresh /proc exact docker exec immutableCID scan",
            "active_clients":observed,"historical_host_child_pid_claimed":False}

def host_job():
    """Independent cleanup admission, NOT a reconstructed AWMCP operation terminal."""
    old=v1();launch=ROOT/"launch";data={};refs=[]
    for name,digest in HOST_REFS.items():
        p=launch/name
        require(file_sha(p)==digest,"actual host-job original bytes drift: "+name)
        data[name]=json.loads(p.read_text());refs.append({"path":str(p),"sha256":digest})
    packet_path=old.ROOT/"projects/damp-ascend/tools/selected_row_dispatch_v1/PACKET.json"
    require(file_sha(packet_path)==PACKET_SHA,"current producer packet drift")
    packet=json.loads(packet_path.read_text())
    for name,digest in packet["sources"].items():
        require(file_sha(packet_path.parent/name)==digest,"current producer source drift")
    for name,digest in packet["dependencies"].items():
        require(file_sha(old.ROOT/name)==digest,"current producer dependency drift")
    require(file_sha(ROOT/"launch/EXECUTION_PLAN.json")==PLAN_SHA,"actual original argv plan drift")
    plan=json.loads((ROOT/"launch/EXECUTION_PLAN.json").read_text())
    shards={x["physical_card"]:x for x in plan["shards"]}
    require(set(shards)==set(IDS),"actual host-job shards differ")
    failure=data["FAILURE.json"]
    require(failure["automatic_retry"] is False and
            failure["original_error"]=="ValueError('single bounded phase timeout; no automatic retry')",
            "unexpected host-job finalization")
    stop=data["STOP_RETAIN.json"]
    require(len(stop)==4 and {x["id"] for x in stop}==set(IDS.values()) and
            all(x["status"]=="exited" and x["deleted"] is False for x in stop),
            "host-job cleanup not complete/retained")
    results=[]
    for card,ident in IDS.items():
        row=data["parallel-docker_gate_exec_argv-physical"+str(card)+".receipt.json"]
        expected=list(shards[card]["docker_gate_exec_argv"]);expected[2]=ident
        require(row["argv"]==expected and row["container_id"]==ident and
                row["automatic_retry"] is False and type(row["exit_code"]) is int,
                "actual host child command/exit identity differs")
        for prefix in ("stdout","stderr"):
            p=Path(row[prefix])
            require(p.parent==launch and file_sha(p)==row[prefix+"_sha256"],
                    "host child original output Ref drift")
        stop_name,inspect_name=STOP_NAMES[card]
        stopped_row=data[stop_name];ins=data[inspect_name]
        require(stopped_row["argv"]==["docker","stop","--time","30",ident] and
                stopped_row["exit_code"]==0 and stopped_row["error"] is None and
                ins["argv"]==["docker","inspect",ident] and ins["exit_code"]==0,
                "exact cleanup command failed")
        for receipt in (stopped_row,ins):
            for prefix in ("stdout","stderr"):
                p=Path(receipt[prefix])
                require(p.parent==launch and file_sha(p)==receipt[prefix+"_sha256"],
                        "cleanup output Ref drift")
        historical=json.loads(Path(ins["stdout"]).read_text())
        require(len(historical)==1,"ambiguous cleanup inspect")
        identity(historical[0],card)
        require(historical[0]["State"]["Running"] is False and historical[0]["State"]["Pid"]==0,
                "historical actual container PID not zero")
        results.append({"physical":card,"container_id":ident,
                        "host_client_exit_code":row["exit_code"],"cleanup_pid":0})
    return {"authority_kind":"host_job_cleanup_observed","operation_id_context_only":OP,
            "awmcp_terminal_reconstructed":False,"scheduling_terminal_only":True,
            "numerical_pass_claimed":False,"original_failure_retained":True,
            "references":refs,"child_commands_and_cleanup":results}
