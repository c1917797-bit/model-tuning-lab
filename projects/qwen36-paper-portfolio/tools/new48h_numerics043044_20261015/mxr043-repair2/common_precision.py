"""ONE shared entry for candidate and any future native control, outside timing.

043 has a candidate-only diagnostic owner, not an executed paired dense arm.
Future pair must invoke this same source for BOTH arms and retain both receipts.
"""
def apply(torch,refiner):
 value=refiner.precision_policy(torch)
 if value['allow_hf32']is not False:raise ValueError('shared HF32-off readback')
 return dict(value,scope='whole diagnostic worker before warmup, including unchanged native fullGDN operators',paired_dense_arm_executed=False)
