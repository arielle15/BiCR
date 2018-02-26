import glob
import nltk
from nltk import word_tokenize
from nltk.tokenize import sent_tokenize
import sklearn
import pickle
import pandas as pd

#Run this script after extracting birth control information from online user reviews (GetInfo_AllBC.py)
#After running this script, run NegEx on files ending in '_PhrasesRatingsTableUpdate.txt' to determine whether side effects are affirmed or negated

#Set working directory
wd = ''

#Dictionary with comments as keys, and their associated ratings as values.
commentToRating = {}

#This function returns a dictionary of comments from a file (generated from GetInfo_AllBC.py), with the comments as keys (no values).
#It also keeps track of the rating associated with each comment (commentToRating dictionary.)
def getCommentDict(f):
    commentDict = {}
    file = open(f, 'r',  encoding='utf-8')
    tracker2 = 0
    for line in file:
        line = line.rstrip('\n')
        if len(line) >= 10:
            if line[:10] == 'NewComment':
                tracker = 1
                continue
        if tracker == 1:
            commentDict[line] = 'NA'
            reviewComment = line
            tracker = 0
        if len(line) >= 9:
            if line[:9] == 'NewRating':
                tracker2 = 1
                continue
        if tracker2 == 1:
            commentToRating[reviewComment] = line
            tracker2 = 0
    return commentDict
            
            
#List of dictionaries of comments for each drug (Index to dictionary of comments for that drug)
commentList = [] 

#Keeping track of birth control drugs with the same comments (for troubleshooting purposes)
pairedBC = {}

#Dictionary, with numerical index as key and file as value
indexToFile = {}

ind = 0

#Go through the comment file of each drug, extract comments, and remove comments that are duplicates
for file in glob.glob(wd + '*_UserComments_ForContraception3.txt'):
    print(file)
    indexToFile[ind] = file
    ind = ind + 1
	#Get a dictionary of comments for this drug
    commentDict = getCommentDict(file)
    for i in range(0,len(commentList)):
        currentDict = commentList[i]
        for c in currentDict:
            if c in commentDict: #both drugs have the same review c
                commentDict.pop(c) #remove the review from the newest dictionary
                pairedBC[str(i) + '_' + str(len(commentList))] = 'NA'
    commentList.append(commentDict) 
    
#for i in pairedBC:
#    print(i)

minComments = 100

#List of comments for each drug, for drugs that have more than minComments
commentListNew = [] 

#List of birth control drugs that have more than minComments
bcNameList = []

#List of files with scraped comments, for drugs that have more than minComments
newFileOrder = []

#Index to dictionary of comments for that drug, removing the ones that don't have enough comments anymore
commentListUpdated = []

#Filling commentListNew, newFileOrder, commentListUpdated
for i in range(0,len(commentList)):
    file = indexToFile[i]
    print(file)
    commentDict = commentList[i]
    numComments = len(commentDict)
    if numComments >= minComments:
        print(file + '\t' + str(numComments))
        commentString = ''
        for c in commentDict:
            commentString = commentString + ' ' + c.lower()
        commentListNew.append(commentString)
        newFileOrder.append(file)
        commentListUpdated.append(commentDict)

#Function that replaces hyphens with spaces in birth control names		
def new_bcName(name):
    bcNameSplit = name.split('-')
    if len(bcNameSplit) > 1:
        bcName = ' '.join(i for i in bcNameSplit)
    else:
        bcName = name
    return bcName
    
#Filling bcNameList	        
for file in newFileOrder:
    fileSplit = file.split('\\')
    fileSplit2 = fileSplit[1].split('_')
    bcName = fileSplit2[0]
    if bcName == '':
        bcName = fileSplit2[1]
        bcName = new_bcName(bcName)
    else:
        bcName = new_bcName(bcName)
    bcName = "%s%s" % (bcName[0].upper(), bcName[1:])    
    print(bcName)        
    bcNameList.append(bcName)    

with open(wd + 'bcNameList.pkl', 'wb') as f:
    pickle.dump(bcNameList, f)
    
    
#for i in commentListNew:
#    print(len(i))
    
#numDocs = len(commentListNew)

#print('Numdocs: ' + str(numDocs))



######New stuff##########
#Find phrases that contain mentions of specific side effects. Phrases are elements between sentences separated by commas. If there are no commas, it is the whole sentence.
#We will also keep track of sentences mentioning these side effects.

#File with side effects
sideEffectFile = pd.read_csv(wd + 'SideEffectListTotal.txt', header = None)

sideEffectList = sideEffectFile[0].tolist()

#Drug number to sentence number
drugNumToSentenceNum = {}

#Need to keep track of sentences so we don't repeat them (dictionaries), as well as ratings
drugToIDtoSentence = {}
drugToIDtoRating = {}

counter = 0

for i in range(1, len(commentListUpdated) + 1):
    drugNumToSentenceNum[i] = 0
    drugToIDtoSentence[i] = {}
    drugToIDtoRating[i] = {}
 
#This function returns a sentence number/ID, rating associated with that sentence, and a counter that represents the comment # for a particular side effect.
#It also keeps tracks of sentences/ratings, to be put into a table so that we can retrieve and show them in the web app.
def RecordSentenceRating(count, rate, sentence):
    prevSentNum = drugNumToSentenceNum[count]
    IDtoSentence = drugToIDtoSentence[count]
    sentenceTaken = 0
    sentenceTakenID = 0
    for ID in IDtoSentence:
        sent = IDtoSentence[ID]
        if sent == sentence: #Then this sentence has already been used for this drug
            sentenceTaken = 1
            sentenceTakenID = ID #Record ID for this sentence so we can return it
    if sentenceTaken == 0:#Then this is a new sentence
        sentNum = prevSentNum + 1
        IDtoSentence[sentNum] = sentence
        IDtoRating = drugToIDtoRating[count]
        IDtoRating[sentNum] = rate
        drugToIDtoSentence[count] = IDtoSentence
        drugToIDtoRating[count] = IDtoRating
        drugNumToSentenceNum[count] = sentNum
    else:
        sentNum = sentenceTakenID
    return str(count) + '\t' + rate + '\t' + str(sentNum)
    
    
 
#For each side effect
for se in sideEffectList:
    print(se)
    counter = 0
    phraseToDrugScore = []
	#For each drug
    for i in range(0,len(commentListUpdated)):
        counter = counter + 1
        print(str(counter))
        commentDict = commentListUpdated[i]
		#For each comment
        for c in commentDict:
            rating = commentToRating[c]
            sentList = sent_tokenize(c)
			#For each sentence
            for sent in sentList:
                sentCommaSep = sent.split(',')
				#For each phrase
                for p in sentCommaSep:
                    pDict = {}
					#For each word
                    for w in word_tokenize(p):
						#If word is a side effect, then store this phrase and its associated rating and number/ID for the sentence it's in (and a counter representing comment # for this side effect)
                        if w == se:
                            pDict[p] = RecordSentenceRating(counter, rating, sent)
                    wordList = word_tokenize(p)
					#Check if two adjacent words (bigram) represent a side effect
                    for x, y in zip(wordList, wordList[1:]):
                        bigram = x + ' ' + y
                        if bigram.lower() == se:
                            pDict[p] = RecordSentenceRating(counter, rating, sent)
                    phraseToDrugScore.append(pDict)
                        
    savePhrasesFile = open(wd + 'save_' + se + '_PhrasesRatingsTableUpdate.txt', 'w', encoding = 'utf-8')
    
	#Write out phrases, ratings, and associated side effect (to be used as input for NegEx)
    for pd in phraseToDrugScore:
        for p in pd:
            drugRating = pd[p]
            drugRatingSplit = drugRating.split('\t')
            drug = drugRatingSplit[0]
            rating = drugRatingSplit[1]
            sentNum = drugRatingSplit[2]
            savePhrasesFile.write(drug + '_' + sentNum + '_' + rating + '\t' + se + '\t' + p + '\tAffirmed\t\n')
    savePhrasesFile.close()
        

#Make tables with sentences and review ratings (to be used for retrieving sentences from review comments that are relevant to the user's input side effects)
sentence_file = open(wd + 'Sentences2.txt', 'w', encoding = 'utf-8')
rating_file = open(wd + 'Ratings2.txt', 'w', encoding = 'utf-8')

for i in drugToIDtoSentence:
    IDtoSentence = drugToIDtoSentence[i]
    IDtoRating = drugToIDtoRating[i]
    for ID in IDtoSentence:
        sentence = IDtoSentence[ID]
        rating = IDtoRating[ID]
        sentence_file.write(str(i) + '\t' + str(ID) + '\t' + sentence + '\n')
        rating_file.write(str(i) + '\t' + str(ID) + '\t' + rating + '\n')
    
sentence_file.close()
rating_file.close()
        
print('The end')   