#Revise side effects table so that affirmed side effects are represented by a 1 and negated side effects are represented by a 0.

#Set working directory
wd = ''

f = open(wd + 'sideEffectsTable.txt', 'r')
output = open(wd + 'sideEffectsTable2.txt', 'w')

for line in f:
    line = line.rstrip('\n')
    cols = line.split('\t')
    se = cols[2]
    status = cols[3]
    seFirst2 = se[:2]
    if seFirst2 == 'no':
        se = se[2:]
    if status == 'affirmed':
        status = 1
    if status == 'negated':
        status = 0
    output.write(cols[0] + '\t' + cols[1] + '\t' + se + '\t' + str(status) + '\n')
    
output.close()