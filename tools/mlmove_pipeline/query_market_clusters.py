import json

data = json.load(open(r'c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_5\mirage_spot_clusters.json', encoding='utf-8'))
for c in data['clusters']:
    pl = c['valve_place']
    x, y, z = c['medoid']
    if -2300 <= x <= -1600 and -650 <= y <= 300:
        print(f"id={c['cluster_id']:3d} | pl={pl:15s} | pos=[{x:7.1f}, {y:7.1f}, {z:6.1f}] | demos={c['unique_demos']:3d} | ct={c['ct_ratio']:.2f}")
