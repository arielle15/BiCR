import urllib
import urllib.request
import urllib.error
import http.cookiejar
from bs4 import BeautifulSoup
import math
import time
from random import randint

#Run this script first to extract birth control user reviews and related information from drugs.com

#Set working directory
wd = ''

#drugInfo contains the drug name, chemical composition, and number of comments for each drug (>= 100 comments required)
drugInfo = open(wd + 'DrugCommentInfoUpdated.txt', 'r')

drugInfoList = []

for line in drugInfo:
    line = line.rstrip('\n')
    drugInfoList.append(line)

#Extract comments for each drug
for drug in drugInfoList:
    drugSplit = drug.split('\t')
    bc = drugSplit[0]
    bc_fullName = drugSplit[1]
    numComments = int(drugSplit[2])
    
    #Wait 6-11 seconds before extracting information from a new page
    TIME_BT_REQUESTS = randint(6,11)
    print(TIME_BT_REQUESTS)
    time.sleep(TIME_BT_REQUESTS)
    
    totalPages = math.ceil(numComments/25)

    num = 1

    output = open(wd + bc + '_' + bc_fullName + '_UserComments_ForContraception3.txt', 'w', encoding = "utf-8")

    if bc != '':
        bc = bc + '-'
        
    print(bc)    
    
    #Extract information from each page
    for page in range(1, totalPages + 1):
        url = ('http://www.drugs.com/comments/' + bc_fullName + '/' + bc + 'for-contraception.html?page=%s') % page

        class AppURLopener(urllib.request.FancyURLopener):
            version = "Mozilla/5.0"

        opener = AppURLopener()

        f = opener.open(url)

        soup = BeautifulSoup(f.read(), "html.parser")

        for post in soup.find_all('div', class_='user-comment'):
            #Find the text of the review
            comment = post.find('span')
            rating = post.find('div', class_='rating-score')
            timeTaken = post.find('span', class_='tiny light')
            otherDrugName =post.find('b')
            comment_stripped = comment.text.strip()
            comment_stripped_noQuote = comment_stripped[1:-1]
            #Determine rating of review
            if(rating):
                rating_stripped = rating.text.strip()
            else:
                rating_stripped = 'NoneRating'
            #Determine the amount of time that user has been taking the drug for (didn't end up using this information)
            if(timeTaken):
                timeTaken_stripped = timeTaken.text.strip()
                timeTaken_stripped_split = timeTaken_stripped.split('(taken for ')
                timeTaken_stripped_split2 = timeTaken_stripped_split[1].split(')')
                timeTaken_stripped = timeTaken_stripped_split2[0]
            else:
                timeTaken_stripped = 'NoneTimeTaken'
            #Determine if review is actually for another similar drug (usually this happens for generic drugs/brands names of those drugs)
            if(otherDrugName):
                otherDrugName_stripped = otherDrugName.text.strip()
                otherDrugName_stripped = otherDrugName_stripped[:-1]
            else:
                otherDrugName_stripped = 'NoneOtherDrugName'
            output.write('NewComment_' + str(num) + '\n' + comment_stripped_noQuote + '\n')
            output.write('NewRating_' + str(num) + '\n' + rating_stripped + '\n')
            output.write('NewTimeTaken_' + str(num) + '\n' + timeTaken_stripped + '\n')
            output.write('NewOtherDrugName_' + str(num) + '\n' + otherDrugName_stripped + '\n')
            num = num + 1      

        print(page)
        time.sleep(TIME_BT_REQUESTS)
        
    output.close()

print("All done")