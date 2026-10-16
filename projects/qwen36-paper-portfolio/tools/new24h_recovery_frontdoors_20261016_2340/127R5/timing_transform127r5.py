"""Only the original elapsed-time predicate changes after exact R4 inverse."""
from audit_transform127r4 import transform as prior,inverse as prior_inverse
OLD="time.monotonic()-start<600,'CPU600s'"
NEW="time.monotonic()-start<2700,'CPU2700s new independent R5 registration'"
def transform(raw):
 text=prior(raw)
 if text.count(OLD)!=1:raise ValueError('one exact original CPU600 timing predicate')
 text=text.replace(OLD,NEW)
 if inverse(text)!=raw:raise ValueError('whole original mathematical body inverse')
 return text
def inverse(text):
 if text.count(NEW)!=1:raise ValueError('one new CPU2700 timing predicate')
 return prior_inverse(text.replace(NEW,OLD))
