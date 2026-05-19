from rag.retriever import build_index, retrieve_topk, build_rag_prompt
idx = build_index('docs')
print('Indexed', len(idx), 'chunks')
q = 'How to deploy the API locally?'
res = retrieve_topk(idx, q, k=3)
for r, s in res:
    print('SCORE', s, 'DOC', r['doc'])
    print(r['text'][:200])
    print('---')
print('\nPrompt sample:\n')
if res:
    prompt = build_rag_prompt([r for r, s in res], q)
    print(prompt[:800])
