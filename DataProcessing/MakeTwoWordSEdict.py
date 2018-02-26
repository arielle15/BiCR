#Generate a dictionary, with keys representing two-word side effects as one single word (which were used in TF/cosine similarity model), and values representing those side effects as two words.

#Set working directory
wd = ''

import pickle

file = open(wd + 'TwoWordSEs.txt', 'r')

twoWordSEdict = {}

for line in file:
    line = line.rstrip('\n')
    cols = line.split('\t')
    twoWordSEdict[cols[0]] = cols[1]
    
with open(wd + 'twoWordSEdict.pkl', 'wb') as f:
    pickle.dump(twoWordSEdict, f)   