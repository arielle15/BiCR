from flask import render_template
from flaskexample import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
from flask import request
import pickle
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

#Set working directory (contains 'BCapp_Themed' folder)
wd = ''

username = 'postgres'    
password = '' #Removed password
host = 'localhost'
port     = '5432'
dbname = 'bicr_db'

engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, dbname) )


#Code for creating database (only need for first time running code)
#create_database(engine.url)


#Read in data with comment sentences, ratings, and side effect information for PostgreSQL table (only need for first time running code)
#sentence_data = pd.read_csv(wd + 'BCapp_Themed/flaskexample/Sentences2.txt', delimiter = '\t', names = ["drug_id", "sentence_id", "sentence"])
#ratings_data = pd.read_csv(wd + 'BCapp_Themed/flaskexample/Ratings3.txt', delimiter = '\t', names = ["drug_id", "sentence_id", "rating"])
#se_data = pd.read_csv(wd + 'BCapp_Themed/flaskexample/sideEffectsTable2.txt', delimiter = '\t', names = ["drug_id", "sentence_id", "side_effect", "status"])

#sentence_data.to_sql('sentence_data_table', engine, if_exists='replace')
#ratings_data.to_sql('ratings_data_table', engine, if_exists='replace')
#se_data.to_sql('se_data_table', engine, if_exists='replace')



con = psycopg2.connect(database = dbname, user = username, host=host, password=password)




@app.route('/')
@app.route('/index')
def index():
	return render_template("input.html")
	
@app.route('/input')
def bc_input():
    return render_template("input.html")
	
@app.route('/about')
def about():
    return render_template("about.html")	

@app.route('/output')
def bc_output():
	#Get input from user
	side_effect_input = request.args.getlist('side_effect')
	if len(side_effect_input) == 0:
		return render_template("input_select_se.html")	
	bc_type_input = request.args.get('bc_type')
	conditions_input = request.args.getlist('condition')
	
	#Import various lists/dictionaries/files that contain drug, comment, and side effect information
	with open(wd + 'BCapp_Themed/flaskexample/reducedCommentList.pkl', 'rb') as f:
		reducedCommentList = pickle.load(f)
	with open(wd + 'BCapp_Themed/flaskexample/bcNameList.pkl', 'rb') as f:
		bcNameList = pickle.load(f)
	with open(wd + 'BCapp_Themed/flaskexample/sePercentChange.pkl', 'rb') as f:
		sePercentChange = pickle.load(f)
	with open(wd + 'BCapp_Themed/flaskexample/sePercentChangeReverse.pkl', 'rb') as f:
		sePercentChangeReverse = pickle.load(f)
	with open(wd + 'BCapp_Themed/flaskexample/twoWordSEdict.pkl', 'rb') as f:
		twoWordSEdict = pickle.load(f)		
	inputPrefInfo = pd.read_csv('/home/ubuntu/BCapp_Themed/flaskexample/BiCR_InputConditions3.txt', delimiter = '\t')
	
	#Function needed to get percentage change in side effect for a particular drug, compared to all drugs
	def GetPercentages(side_effect, idx):
		seIndex = words.index(side_effect)
		firstPercent = int(sePercentChange[bc_index_rankedList[idx], seIndex])
		modifier = 'fewer'
		allPercent = 100
		drugPercent = 100 - firstPercent
		if firstPercent < 0: #this means there are *more* occurences of side effect in this drug compared to all drugs
			firstPercent = int(sePercentChangeReverse[bc_index_rankedList[idx], seIndex])
			modifier = 'more'
			allPercent = round(100/((firstPercent/100) + 1))
			drugPercent = 100
		return [str(firstPercent), modifier, str(allPercent), str(drugPercent)]
	
	#Generate TF matrix
	tf = TfidfVectorizer(use_idf = False)
	normText = tf.fit_transform(reducedCommentList)
	words = tf.get_feature_names()
	response = tf.transform(side_effect_input)
	
	#Perform cosine similarity for affirmed and negated side effects
	cosim_test = cosine_similarity(response, normText)
	cosim_test_sum = [sum(x) for x in zip(*cosim_test)]
	side_effect_input_n = ['no' + se for se in side_effect_input]
	response_n = tf.transform(side_effect_input_n)	
	cosim_test_n = cosine_similarity(response_n, normText)
	cosim_test_sum_n = [sum(x) for x in zip(*cosim_test_n)]
	
	#Subtract cosine similarities
	cosim_test_diff = [x1 - x2 for (x1, x2) in zip(cosim_test_sum, cosim_test_sum_n)]
	bc_index_ranked = np.argsort(cosim_test_diff)
	drug_output = [bcNameList[i] for i in bc_index_ranked[:]]
	min_score = min(cosim_test_diff)
	max_score = max(cosim_test_diff)
	cosim_test_range = max_score - min_score
	cosim_test_sorted = sorted(cosim_test_diff)
	
	#Determine relative score
	score_list = []
	for i in range(0, len(bcNameList)):
		relativeScore = (cosim_test_sorted[i] - min_score)/(cosim_test_range)
		score_list.append(int(round((1 - relativeScore)*100)))
	
	#Remove certain drugs based on user's personal preferences and medical history
	removeDrugTypes = np.asarray([100])
	removeDrugTypesNoIUD = np.asarray([100])
	removeDrugTypesNoCHC = np.asarray([100])
	removeDrugTypesCuIDonly = np.asarray([100])
	conditionsNoIUD = ['pelvic', 'cervicalcancer', 'endometrialcancer', 'postpartum', 'tb', 'bleeding']
	conditionsNoCHC = ['dvt', 'aura', 'bloodpressure', 'smoker', 'heart', 'livertumors', 'peripartum', 'stroke']
	if  bc_type_input == 'pill':
		removeDrugTypes = np.asarray(inputPrefInfo.index[inputPrefInfo.PreferPill == 1])
	elif bc_type_input == 'other_type':
		removeDrugTypes = np.asarray(inputPrefInfo.index[inputPrefInfo.PreferOther == 1])
	for c in conditionsNoIUD:
		if c in conditions_input:
			removeDrugTypesNoIUD = np.asarray(inputPrefInfo.index[inputPrefInfo.NoIUD == 1])
			break
	for c in conditionsNoCHC:
		if c in conditions_input:
			removeDrugTypesNoCHC = np.asarray(inputPrefInfo.index[inputPrefInfo.NoCHC == 1])
			#ts = 'hey!'
	if 'breastcancer' in conditions_input:
		removeDrugTypesCuIDonly = np.asarray(inputPrefInfo.index[inputPrefInfo.CuIUDonly == 1])			
	#Which indices belong to the drugs we should remove?	
	indicesRemoveU1 = np.union1d(removeDrugTypes, removeDrugTypesNoIUD)
	indicesRemoveU2 = np.union1d(removeDrugTypesNoCHC, removeDrugTypesCuIDonly)
	indicesRemoveU = np.union1d(indicesRemoveU1, indicesRemoveU2)
	indicesRemoveU.sort()
	indicesRemoveU = indicesRemoveU[::-1]
	firstEl = indicesRemoveU[0]
	if firstEl == 100:
		indicesRemoveU = np.delete(indicesRemoveU, 0)
	query_results = indicesRemoveU
	indicesRemoveU = indicesRemoveU.tolist()
	indicesRemove = np.where(np.in1d(bc_index_ranked, indicesRemoveU))[0]
	indicesRemove.sort()
	indicesRemove = indicesRemove[::-1]
	bc_index_rankedList = bc_index_ranked.tolist()
	#Remove these drugs
	for index in indicesRemove:
		del drug_output[index]
		del score_list[index]
	query_results = indicesRemove
	troubleshoot = indicesRemoveU
	for i in indicesRemoveU:
		bc_index_rankedList.remove(i)

	#Find percentage increases/decreases for both affirmed and negated side effects
	sePercentInfoAll = []
	no_sePercentInfoAll = []
	for i in range(0, 3):
		if i + 1 > len(drug_output):
			break
		else:
			percentInfo = []
			percentInfo_no_se = []
			for i_se, se in enumerate(side_effect_input):
				percentageSE = GetPercentages(se, i)
				percentageNoSE = GetPercentages('no' + se, i)
				percentInfo.append(percentageSE)
				percentInfo_no_se.append(percentageNoSE)
			sePercentInfoAll.append(percentInfo)
			no_sePercentInfoAll.append(percentInfo_no_se)
	test = bc_index_ranked
	best_bc = drug_output[:3]
	worst_bc = drug_output[-3:]
	
	#Find relevant comments
	drugSEcomments = []
	for i in range(0, 3):
		if i + 1 > len(drug_output):
			break
		else:	
			commentList = []
			for se in side_effect_input:
				drugID = str(bc_index_rankedList[i] + 1)
				query = "SELECT sentence FROM sentence_data_table JOIN ratings_data_table ON (ratings_data_table.sentence_id = sentence_data_table.sentence_id) WHERE sentence_data_table.sentence_id IN (SELECT sentence_id FROM se_data_table WHERE drug_id = " + drugID + " AND side_effect = '" + se + "' and status = 0 ORDER BY random()) AND sentence_data_table.drug_id = " + drugID + "AND ratings_data_table.drug_id = " + drugID + " ORDER BY ratings_data_table.rating DESC, random() LIMIT 1"
				query_results = pd.read_sql_query(query,con)
				if query_results.empty:
					query = "SELECT sentence FROM sentence_data_table JOIN ratings_data_table ON (ratings_data_table.sentence_id = sentence_data_table.sentence_id) WHERE sentence_data_table.sentence_id IN (SELECT sentence_id FROM se_data_table WHERE drug_id = " + drugID + " AND side_effect = '" + se + "' and status = 1 ORDER BY random()) AND sentence_data_table.drug_id = " + drugID + "AND ratings_data_table.drug_id = " + drugID + " ORDER BY ratings_data_table.rating DESC, random() LIMIT 1"
					query_results = pd.read_sql_query(query,con)
					if query_results.empty:
						query_results = 'There were no comments mentioning ' + se + '.'
					else:
						query_results = '"' + query_results.iloc[0]['sentence'] + '"'
				else:
					query_results = '"' + query_results.iloc[0]['sentence'] + '"'
				commentList.append(query_results)
			drugSEcomments.append(commentList)
			
	#Find birth control type info
	bcTypeList = []
	for i in range(0, 3):
		if i + 1 > len(drug_output):
			break
		else:	
			drugNum = bc_index_rankedList[i]
			article = inputPrefInfo.iloc[drugNum]['Article']
			type = inputPrefInfo.iloc[drugNum]['Type']
			hormones = inputPrefInfo.iloc[drugNum]['Hormones']
			bcTypeList.append([article, type, hormones])
	
	#Get proper names for side effects with two or more words
	for i, se in enumerate(side_effect_input):
		if se in twoWordSEdict:
			newSE = twoWordSEdict[se]
			side_effect_input[i] = newSE
	
	#Determine which output page to show (depends on number of birth control drugs we are outputting)
	if len(drug_output) >= 3:
		return render_template("output.html", best_bc = best_bc, worst_bc = worst_bc, drug_output = drug_output, query_results = query_results, score_list = score_list, sePercentInfoAll = sePercentInfoAll, no_sePercentInfoAll = no_sePercentInfoAll, side_effect_input = side_effect_input, drugSEcomments = drugSEcomments, bcTypeList = bcTypeList)
	elif len(drug_output) == 2:
		return render_template("output_2drugs.html", best_bc = best_bc, worst_bc = worst_bc, drug_output = drug_output, query_results = query_results, score_list = score_list, sePercentInfoAll = sePercentInfoAll, no_sePercentInfoAll = no_sePercentInfoAll, side_effect_input = side_effect_input, drugSEcomments = drugSEcomments, bcTypeList = bcTypeList)
	elif len(drug_output) == 1:
		return render_template("output_1drug.html", best_bc = best_bc, worst_bc = worst_bc, drug_output = drug_output, query_results = query_results, score_list = score_list, sePercentInfoAll = sePercentInfoAll, no_sePercentInfoAll = no_sePercentInfoAll, side_effect_input = side_effect_input, drugSEcomments = drugSEcomments, bcTypeList = bcTypeList)		
	else:
		return render_template("output_nodrugs.html")
	
