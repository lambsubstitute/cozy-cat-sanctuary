import json,sys
for f in sys.argv[1:]:
    txt=open(f).read()
    for chunk in txt.split('=== ')[1:]:
        head, body = chunk.split('\n',1)
        j=json.loads(body[body.index('{'):body.rindex('}')+1])
        keys=['overlapFrames','worstInfo','illegal','teleports','noJumpChanges','badJumps','boxOverlap','boxInfo','boxes','knocks','birds','tunnelOverlap','tunnelInfo','tunnelTrips','tunnelStates','longestWait','errors','pageErrors']
        print(f, head.strip(), {k:j.get(k) for k in keys})
        hi = {k:v for k,v in j['visits'].items() if any(t in k for t in ['mantel','step','box','ask','mischief','tunnel'])}
        print('    new-spot arrivals:', hi, '| jumps:', {k:v for k,v in j['jumps'].items() if any(t in k for t in ['step','mantel','box','tunnel'])})
