#Revise ratings table so that ratings are integers

f = open('Ratings2.txt', 'r')

output = open('Ratings3.txt', 'w')

for line in f:
    line = line.rstrip('\n')
    cols = line.split('\t')
    rating = cols[2]
    if rating == 'NoneRating':
        rating = '0'
    elif rating != '10':
        rating = rating[0]
    output.write(cols[0] + '\t' + cols[1] + '\t' + rating + '\n')
    
output.close()