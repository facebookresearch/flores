import torch
import tqdm

xlmr = torch.hub.load('pytorch/fairseq', 'xlmr.large')
xlmr.eval()

lang_code = 'npi'
fname = "/checkpoint/oignat/backtranslation/data_books/books_10k/" + lang_code + "_mono.txt"

sents = []
with open(fname) as infile:
    for line in infile:
        sents.append(line.strip())

print(len(sents))

def force_decode(sentence):
    indices = xlmr.encode(sentence).view(1, -1)    # [B=1 x T]
    scores = xlmr.model(indices)[0]        # [B=1 x T x V]
    log_probs = torch.log_softmax(scores, dim=-1)  # [B=1 x T x V]
    lop_probs = log_probs.gather(dim=2, index=indices.unsqueeze(2)) # [B x T x 1]
    log_prob = lop_probs.squeeze(2).sum(dim=1)    # [B=1 x T] -> [B=1]
    return torch.exp(log_prob).item()

avg_perplexity = 0
for sent in tqdm.tqdm(sents):
    avg_perplexity += force_decode(sent)

avg_perplexity = avg_perplexity / len(sents)
print(avg_perplexity)