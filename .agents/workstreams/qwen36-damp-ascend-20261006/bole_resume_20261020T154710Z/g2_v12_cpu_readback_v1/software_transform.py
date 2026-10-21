def software_v12(old):
    def r(a,b,n=1):
        nonlocal old
        if old.count(a)!=n:raise ValueError('exact base-v2 software anchor '+repr(a))
        old=old.replace(a,b)
    r("bole.actual-G2-three-source-staged-software-gate/v11","bole.actual-G2-four-source-staged-software-gate/v12")
    r("root=CPU_OUT/'cpu-preflight/G2-V11-SOFTWARE'","root=CPU_OUT/'cpu-preflight/G2-V12-SOFTWARE'")
    r("value['tests']==322 and value['source8_fresh_cases']==279 and value['source10_fresh_cases']==25 and value['current11_fresh_cases']==18", "value['tests']==341 and value['source8_fresh_cases']==279 and value['source10_fresh_cases']==25 and value['source11_fresh_cases']==18 and value['current12_fresh_cases']==19")
    r('actual full three-source322 result; no cached PASS or source-context conflation','actual full four-source341 result; no cached PASS or source-context conflation')
    r('bole.actual-three-source-software-admission/v11','bole.actual-four-source-software-admission/v12')
    r("need(set(value['controls'])=={'source10','current11'},'both exact-source current control stages required')", "need(set(value['controls'])=={'source10','source11','current12'},'all three exact-source current control stages required')")
    r("for role,count,test_source,pattern in(('source10',25,V10_SOURCE,'test_g2_cold*.py'),('current11',18,sr,'test_g2_stage*.py')):", "for role,count,test_source,pattern in(('source10',25,V10_SOURCE,'test_g2_cold*.py'),('source11',18,V11_SOURCE,'test_g2_stage*.py'),('current12',19,sr,'test_g2_ack*.py')):")
    r('bole.actual-exact-source-only-unittest/v11','bole.actual-exact-source-only-unittest/v12',2)
    r('metadata runs after both complete fresh controls','metadata runs after all three complete fresh controls')
    r("current11_fresh18=control_rows['current11']", "source11_fresh18=control_rows['source11'],current12_fresh19=control_rows['current12']")
    r('tests=322,actual_original_3600_and_cleanup180_clock_preserved=True','tests=341,actual_original_3600_and_cleanup180_clock_preserved=True')
    return old
