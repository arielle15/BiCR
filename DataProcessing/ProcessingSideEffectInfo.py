import sklearn
import numpy as np
import pickle
import pandas as pd

#Use this script after running NegEx on phrases from review comments.

#Set working directory
wd = ''

sideEffectFile = pd.read_csv(wd + 'SideEffectListTotal.txt', header = None)

sideEffectList = sideEffectFile[0].tolist()

numDrugs = 49

#For each drug, a string containing side effects that were mentioned for that drug
reducedCommentList = ['']*numDrugs

synonymsFile = open(wd + 'SideEffectSynonyms.txt', 'r')

#Store synonyms for each side effect - key represents synonym and value represents main side effect it's referring to.
seToSynonyms = {}

for line in synonymsFile:
    line = line.rstrip('\n')
    cols = line.split('\t')
    mainSE = cols[0]
    for se in cols:
        seToSynonyms[se] = mainSE
        
for se in seToSynonyms:
    print(se + '\t' + seToSynonyms[se])

#Mentions of 'sex drive' or 'libido' need to be treated differently, as *no/low* sex drive or *no/low* libido counts as an affirmed side effect.   
sexDriveSE = []
sexDriveSE.append('sexdrive')
sexDriveSE.append('libido')

seTableList = []

#Reduce comments for each drug down to just the side effects that are mentioned (affirmed or negated mentions of side effects)
for se in sideEffectList:
    f = open(wd + 'negex_output_' + se + '_updated_ratings_table2.txt', 'r', encoding = 'utf-8')
    print(se)
    for line in f:
        line = line.rstrip('\n')
        cols = line.split('\t')
        first = cols[0]
        if first[0] != 'P':
            firstSplit = first.split('_')
            drugNum = int(firstSplit[0])
            sentNum = firstSplit[1]
            if len(cols) < 7:
                print(line)
            status = cols[6]
            seSyn = seToSynonyms[se]
            seSplit = seSyn.split(' ')
            if len(seSplit) >= 2:
                seNew = seSplit[0] + seSplit[1]
            else:
                seNew = seSyn
            seEntry = ''    
            if seNew not in sexDriveSE:
                if status == 'affirmed':
                    seNew2 = seNew
                else:
                    seNew2 = 'no' + seNew
                seEntry = str(drugNum) + '\t' + str(sentNum) + '\t' + seNew2 + '\t' + status
            else:
                if status == 'affirmed':
                    seNew2 = 'no' + seNew
                    seEntry = str(drugNum) + '\t' + str(sentNum) + '\t' + seNew2 + '\tnegated'
                else:
                    seNew2 = seNew
                    seEntry = str(drugNum) + '\t' + str(sentNum) + '\t' + seNew2 + '\taffirmed'
            current = reducedCommentList[drugNum - 1]
            if current == '':
                reducedCommentList[drugNum - 1] = seNew2
            else:
                reducedCommentList[drugNum - 1] = current + ' ' + seNew2
            seTableList.append(seEntry)

#Put side effects into table (to be used for retrieving comments relevant to the user's side effect inputs)
seTable = open(wd + 'sideEffectsTable.txt', 'w')			
			
for se in seTableList:
    seTable.write(se + '\n')
    
seTable.close()



#Determine fractions of side effect mentions for each drug and for all drugs
counts = CountVectorizer()
countsText = counts.fit_transform(reducedCommentList)

countsText_a = countsText.todense()

rowSums = countsText_a.sum(axis = 1)

colSums = countsText_a.sum(axis = 0)

#Fraction of each side effect for each drug
perDrugSEfreq = countsText_a/(countsText_a.sum(axis=1))

#Fraction of each side effect for *all* drugs
totalSEfreq = colSums/(colSums.sum(axis=1))

#Percent change in side effect for each drug, compared to all drugs
percentChangeSE = (1 - (perDrugSEfreq/totalSEfreq))*100

#Percent change in side effect for all drugs, compared to each drug
with np.errstate(divide='ignore'):
    percentChangeSEreverse = (1 - (totalSEfreq/perDrugSEfreq))*100


with open(wd + 'reducedCommentList.pkl', 'wb') as f:
    pickle.dump(reducedCommentList, f)  
    
with open(wd + 'sePercentChange.pkl', 'wb') as f:
    pickle.dump(percentChangeSE, f)
    
with open(wd + 'sePercentChangeReverse.pkl', 'wb') as f:
    pickle.dump(percentChangeSEreverse, f)    

with open(wd + 'bcNameList.pkl', 'rb') as f:
    bcNameList = pickle.load(f)


