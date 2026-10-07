"""Independent scalar paper/GQA oracle, no candidate imports.
CPU used ONLY for finite software toy tests, never model/cache workload.
"""
import math
def softmax(xs):
    top=max(xs);e=[math.exp(x-top) for x in xs];den=sum(e);return [x/den for x in e]
def reference(query,keys,values,rank,budget,local=1,reallocation=False,variant="paper-gqa-probability"):
    h=len(query);d=len(query[0]);n=len(keys)
    if not(h and d and n and len(values)==n and 0<rank<=d and budget>=max(1,local)):
        raise ValueError("oracle shape/budget")
    importance=[sum(abs(q[j]) for q in query) for j in range(d)]
    channels=sorted(range(d),key=lambda j:(-importance[j],j))[:rank]
    logits=[];approx=[]
    for q in query:
        total=sum(abs(x) for x in q);coverage=sum(abs(q[j]) for j in channels)
        temperature=math.sqrt(d*coverage/total) if total else 1.
        score=[sum(q[j]*key[j] for j in channels)/temperature for key in keys]
        logits.append(score);approx.append(softmax(score))
    all_scores=approx if variant=="paper-gqa-probability" else logits
    combined=[sum(scores[i] for scores in all_scores) for i in range(n)]
    forced=min(local,n);k=min(n,budget)
    latest=list(range(n-forced,n)) if forced else []
    prior=sorted(range(n-forced),key=lambda i:(-combined[i],i))[:k-forced]
    selected=sorted(prior+latest);mean=[sum(v[j] for v in values)/n for j in range(d)]
    output=[];alphas=[]
    for q,a in zip(query,approx):
        w=softmax([sum(q[j]*keys[i][j] for j in range(d))/math.sqrt(d) for i in selected])
        y=[sum(weight*values[i][j] for weight,i in zip(w,selected)) for j in range(d)]
        alpha=sum(a[i] for i in selected);alphas.append(alpha)
        output.append([alpha*v+(1-alpha)*m for v,m in zip(y,mean)] if reallocation else y)
    return {"output":output,"channels":channels,"support":selected,"alpha":alphas,"mean":mean}
