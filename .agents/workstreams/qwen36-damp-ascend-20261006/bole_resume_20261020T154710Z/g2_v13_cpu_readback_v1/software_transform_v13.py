def software_v13(old):
    def r(a,b,n=1):
        nonlocal old
        if old.count(a)!=n:raise ValueError('exact actual source12 reader software anchor '+repr(a))
        old=old.replace(a,b)
    r("value['tests']==341","value['tests']==349")
    r("value['current12_fresh_cases']==19","value['current12_fresh_cases']==27")
    r('actual full four-source341 result; no cached PASS or source-context conflation','actual full four-source349 result; no cached PASS or source-context conflation')
    r("('current12',19,sr,'test_g2_ack*.py')","('current12',27,sr,'test_g2_ack*.py')")
    r("current12_fresh19=control_rows['current12']","current12_fresh27=control_rows['current12']")
    r('tests=341,actual_original_3600_and_cleanup180_clock_preserved=True','tests=349,actual_original_3600_and_cleanup180_clock_preserved=True')
    return old
