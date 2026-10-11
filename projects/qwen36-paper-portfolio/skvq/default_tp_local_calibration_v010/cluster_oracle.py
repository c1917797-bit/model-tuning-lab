"""Independent stdlib cluster/permutation oracle; no Torch/producer/SKVQ imports."""
import math
def validate(features,row,ncluster):
    if len(features)!=256 or any(len(x)!=2 or not all(math.isfinite(a) for a in x) for x in features):
        raise ValueError("full finite256x2 minmax geometry")
    labels=row["labels"];centers=row["centers"]
    if (len(labels)!=256 or len(centers)!=ncluster or
        any(type(x) is not int or not 0<=x<ncluster for x in labels) or
        any(len(c)!=2 or not all(math.isfinite(x) for x in c) for c in centers)):
        raise ValueError("full actual sklearn labels/centers")
    permutation=row["permutation"];cuts=row["cluster_st_inds"]
    if (len(permutation)!=256 or any(type(x) is not int for x in permutation) or
        sorted(permutation)!=list(range(256)) or len(cuts)!=ncluster+1 or
        any(type(x) is not int for x in cuts) or cuts[0]!=0 or cuts[-1]!=256):
        raise ValueError("full unmodified author permutation/cuts")
    counts=[labels.count(c) for c in range(ncluster)]
    expected=[0]
    for count in counts:expected.append(expected[-1]+count)
    if cuts!=expected or any(a>=b for a,b in zip(cuts,cuts[1:])):
        raise ValueError("author cuts must match nonempty actual labels; never silently merge clusters")
    if any(labels[channel]!=cluster for cluster in range(ncluster)
           for channel in permutation[cuts[cluster]:cuts[cluster+1]]):
        raise ValueError("original labels.argsort cluster mapping")
    # FP64 diagnostic only. sklearn fitting uses original A16 expanded by sklearn;
    # exact non-tie disagreements are exposed, NOT approved/repaired by tolerance.
    wrong=[];ties=[]
    for i,(point,label) in enumerate(zip(features,labels)):
        distances=[math.fsum((x-y)**2 for x,y in zip(point,c)) for c in centers]
        best=min(distances);winners=[c for c,d in enumerate(distances) if d==best]
        if len(winners)>1:ties.append({"channel":i,"clusters":winners})
        if label not in winners:wrong.append({"channel":i,"label":label,"fp64_winners":winners,
                                              "assigned_distance":distances[label],"minimum_distance":best})
    return {"all_channel_mapping_checked":256,"counts":counts,
            "fp64_nearest_center_disagreements":wrong,"fp64_exact_ties":ties,
            "fp64_comparison_is_runtime_diagnostic_not_fitting_threshold":True}
