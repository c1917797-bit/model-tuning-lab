"""Actual051 dual Meta through the original CPU preflight stage."""
def run(torch,m,C):
 from meta051 import run as actual
 z=actual(torch,m['split_build_ref'],m['split_kernel_source_ref'])
 C.need(z['libraries']==[m['library_ref'],m['debug_library']],'actual051 exact two libraries')
 return dict(z,debug_library=m['debug_library'],debug_build=m['debug_build_ref'],registrations=z['rows'])
