import sys
import csv
import re
import os
import urllib2
import pandas as pd
from ssh import SSHConnection
from werkzeug.utils import secure_filename
from flask import render_template,Flask,request

import sys
reload(sys)
sys.setdefaultencoding('utf8')



app = Flask(__name__)




###**********  HOMEPAGE   *********###
@app.route('/')             # homepage
def homepage():
    return render_template('homepage.html')

@app.route('/Upload_esoi')
def Upload_esoi():
    return render_template('Upload_esoi.html')

@app.route('/Local_esoi')
def Local_esoi():
    return render_template('Local_esoi.html')


###*********   DEMO PART   **********###
@app.route('/Demo_YX')          #static web demo/YX's
def Demo_YX():
    return render_template('Demo_YX.html')

@app.route('/Demo_YD')       #static web demo/module/YD's
def Demo_YD():
    ## step 1. Read stock csv files(outputTest,outputTrain,outputTrainTest)
    outputTest = pd.read_csv('module/YD/outputTest.csv')
    outputTrain = pd.read_csv('module/YD/outputTrain.csv')
    outputTrainTest = pd.read_csv('module/YD/outputTrainTest.csv')
    Test_time = outputTest['Unnamed: 0']
    Test_origin = outputTest['origin']
    Test_predict = outputTest['predict']
    Train_time = outputTrain['Unnamed: 0']
    Train_origin = outputTrain['origin']
    Train_predict = outputTrain['predict']
    TrainTest_time = outputTrainTest['Unnamed: 0']
    TrainTest_origin = outputTrainTest['origin']
    TrainTest_predict = outputTrainTest['predict']

    ## step 2. creat stock_data dic  (stock_data is the data of the local file xxxx.csv in module/YD folder)
    stock_data={'Test_time':Test_time,'Test_origin':Test_origin,
    'Test_predict':Test_predict,'Train_time':Train_time,
    'Train_origin':Train_origin,'Train_predict':Train_predict,
    'TrainTest_time':TrainTest_time,'TrainTest_origin':TrainTest_origin,
    'TrainTest_predict':TrainTest_predict}

    ## step 3. upload stock_data to HTML part
    return render_template('Demo_YD.html',stock_data = stock_data)



###***************  ONLINE PART   *****************###

@app.route('/Local_Service')	  # Choose SERVICE or LOCAL
def Local_Service():
    return render_template('Local_Service.html')

@app.route('/Online_login',methods=['GET','POST'])    #log in service
def online():
    def get_s(name):  ##  get values from the HTML part ,'name' is the 'id' of HTML <input>
        return request.values.get(name)
    if request.method == 'POST':
        global dic_s                ## dic_s----------service data (host,port,username,password,remote work directory path)
        dic_s={}
        dic_s['host'] = str (get_s('host'))
        dic_s['port'] = int (get_s('port'))
        dic_s['username'] = str (get_s('username'))
        dic_s['password'] = str (get_s('password'))
        dic_s['remote work directory path'] = str (get_s('remote work directory path'))
        return render_template('Stock_House.html',dic_s=dic_s)
    else:
        return render_template('Login_account.html')


@app.route('/Upload_stock',methods=['GET','POST'])    #   upload stock files_SERVICE
def Upload_stock():
    if request.method == 'POST':
        ## step 1. load the file
        f = request.files['file']

        ## step 2. save the file
        f.save(secure_filename(f.filename))

        ## step 3. connect the service from ssh
            ### SSHConnection is the Class in ssh.py,its parameters contains(host=str, port=int, username=str,pwd=str)
        ssh_1=SSHConnection(dic_s['host'],dic_s['port'],dic_s['username'],dic_s['password'])
        ssh_1.connect()
        ssh_1.upload(str(os.getcwd()) + '/' + str(f.filename),dic_s['remote work directory path'] + '/FlaskIndexPrediction/data/data.csv')  # INPUT YOUR PATH
        ## ssh_1.upload(LOCAL FILE PATH,REMOTE PATH)
        return render_template('Choose_LSTM.html')

    else:
        return render_template('Upload_stock.html')

@app.route('/Upload_house',methods=['GET','POST'])			#upload housepriice files_SERVICE
def Upload_house():
    if request.method == 'POST':
        ## step 1. load the file
        f = request.files['file']

        ## step 2. save the file
        f.save(secure_filename(f.filename))

        ## step 3. connect the service from ssh
            ### SSHConnection is the Class in ssh.py,its parameters contains(host=str, port=int, username=str,pwd=str)
        ssh_2 = SSHConnection(dic_s['host'],dic_s['port'],dic_s['username'],dic_s['password'])
        ssh_2.connect()
        ssh_2.upload(str(os.getcwd()) + '/' + str(f.filename),dic_s['remote work directory path'] + '/lgbm/train1.csv')
        ## ssh_2.upload(LOCAL FILE PATH,REMOTE PATH)

        ##step 4. run data_v.py to get data of HousePrice
        global mydata  ## mydata is the visualization data of HousePrice data
        mydata = eval(ssh_2.cmd('cd lgbm;python data_v.py'))

        return render_template('Housedata_description.html',mydata=mydata)
    else:
        return render_template('Upload_house.html')

@app.route('/Housedata_parameter',methods=['GET','POST'])			#Upload Housedata_parameter
def Housedata_parameter():
    def get(name):      ##  get values from the HTML part ,'name' is the 'id' of HTML <input>
        return request.values.get(name)

    if request.method == 'POST':
        ##step 1. get housedata parameters from HTML
        LotArea = get("LotArea")
        Neighborhood = get("Neighborhood")
        YearBuilt = get("YearBuilt")
        GrLivArea = get("GrLivArea")
        Street = get("Street")
        Utilities = get("Utilities")
        LotConfig = get("LotConfig")
        HouseStyle = get("HouseStyle")
        RoofStyle = get("RoofStyle")
        SaleType = get('SaleType')
        SaleCondition = get('SaleCondition')
        lgbm_data=[LotArea,Street,Utilities,LotConfig,Neighborhood,
        HouseStyle,YearBuilt,RoofStyle,GrLivArea,SaleType,SaleCondition]
        lgbm_data_1=",".join(lgbm_data)

        ##step 2. Data Processing.
        def getSortedValues(row):       ## make data in a certain order('row' is the key for the data need to be sorted)
            sortedValues=[]
            keys=row.keys()
            keys.sort()
            for key in keys:
                sortedValues.append(row[key])
            return sortedValues

        rows = [{'Column1': 1, 'Column2': LotArea,'Column3': Street,'Column4':Utilities,'Column5':LotConfig,
                'Column6':Neighborhood,'Column7':HouseStyle,'Column8':YearBuilt,'Column9':RoofStyle,
                'Column10':GrLivArea,'Column11':SaleType,'Column12':SaleCondition},
                ]

        names={'Column1': 'Id', 'Column2': 'LotArea','Column3': 'Street','Column4':'Utilities','Column5':'LotConfig',
                'Column6':'Neighborhood','Column7':'HouseStyle','Column8':'YearBuilt','Column9':'RoofStyle',
                'Column10':'GrLivArea','Column11':'SaleType','Column12':'SaleCondition'}

        ## step 3. write the sorted data in a csv file('test.csv')
        fileobj=open("module/YX/test.csv",'wb')
        fileobj.write('\xEF\xBB\xBF')
        writer = csv.writer(fileobj)
        sortedValues = getSortedValues(names)
        writer.writerow(sortedValues)
        for row in rows:
            sortedValues = getSortedValues(row)
            print (sortedValues)
            writer.writerow(sortedValues)
        fileobj.close()

        ## step 4. upload test.csv
        ssh_3 = SSHConnection(dic_s['host'],dic_s['port'],dic_s['username'],dic_s['password'])
        ssh_3.connect()
        ssh_3.upload(str(os.getcwd())  + '/module/YX/' +  'test.csv','/root/lgbm/test.csv')

        ## step 5. running LGBM moudle to process the data
        show = ssh_3.cmd('cd lgbm;python lgbm.py')
        show_l = show.split('\n')                       ## the output of lgbm.py in terminal
        # print "showl_l"
        # print show_l

        pred_y = eval(show_l[-2])                       ##  the price output in list[]
        # print "pred_y"
        # print pred_y
        pred_y_show=pred_y[0]                           ##  the price output in float
        # print "pred_y_show"
        # print pred_y_show
        quantitative = re.findall("\d+",show_l[3])[0]    ## number of quantitative features
        qualitative = re.findall("\d+",show_l[3])[1]     ## number of qualitative features
        train_x1 = show_l[6]                            ## the shape of train_X(1018,11)
        # print "train_x1"
        # print  train_x1
        train_y1 = show_l[7]                            ## the shape of train_y(1018,)
        # print "train_y1"
        # print  train_y1
        test_x1 = show_l[8]                             ## the shape of test_x(1,11)
        # print "text_x1"
        # print  test_x1
        return render_template('House_final_output.html',pred_y=round(pred_y_show,2),train_x1=train_x1,train_y1=train_y1
            ,test_x1=test_x1,quantitative=quantitative,qualitative=qualitative)

    else:
        return render_template('Housedata_parameter.html',mydata=mydata)

@app.route('/Stockdata_parameter',methods=['GET','POST'])      #upload module/YD module parameter
def Stockdata_parameter():
    def get(name):                                      ##  get values from the HTML part ,'name' is the 'id' of HTML <input>
        return request.values.get(name)
    if request.method == 'POST':
        ## step 1. get the parameters of stock data from HTML
        stock_parameter={}                                          ##  stock_parameter is a dic to store teh parameters user input in HTML
        stock_parameter['e'] = int(get('e'))
        stock_parameter['lb'] = int (get('lb'))
        stock_parameter['lr'] = float (get('lr'))
        stock_parameter['tp'] = float (get('tp'))

        ## step 2. running the LSTM module in service
        ssh_s=SSHConnection(dic_s['host'],dic_s['port'],dic_s['username'],dic_s['password'])
        ssh_s.connect(  )
        s='cd FlaskIndexPrediction;python main.py -e {e} -lb {lb} -lr {lr} -tp{tp}'
        ssh_s.cmd(s.format(e=stock_parameter['e'],lb=stock_parameter['lb'],lr=stock_parameter['lr'],tp=stock_parameter['tp']))

        ## step 3.download the main.py output file to local
        ssh_s.download(dic_s['remote work directory path'] + '/FlaskIndexPrediction/output/outputTest.csv', str(os.getcwd())  + '/module/YD/' +  'outputTest.csv')
        ssh_s.download(dic_s['remote work directory path'] + '/FlaskIndexPrediction/output/outputTrain.csv',str(os.getcwd())  + '/module/YD/' +  'outputTrain.csv')
        ssh_s.download(dic_s['remote work directory path'] + '/FlaskIndexPrediction/output/outputTrainTest.csv',str(os.getcwd())  + '/module/YD/' +  'outputTrainTest.csv')

        ## step 4. read csv from local
        outputTest = pd.read_csv('module/YD/outputTest.csv')
        outputTrain = pd.read_csv('module/YD/outputTrain.csv')
        outputTrainTest = pd.read_csv('module/YD/outputTrainTest.csv')
        Test_time = outputTest['Unnamed: 0']
        Test_origin = outputTest['origin']
        Test_predict = outputTest['predict']
        Train_time = outputTrain['Unnamed: 0']
        Train_origin = outputTrain['origin']
        Train_predict = outputTrain['predict']
        TrainTest_time = outputTrainTest['Unnamed: 0']
        TrainTest_origin = outputTrainTest['origin']
        TrainTest_predict = outputTrainTest['predict']

        stock_data={'Test_time':Test_time,'Test_origin':Test_origin,
        'Test_predict':Test_predict,'Train_time':Train_time,
        'Train_origin':Train_origin,'Train_predict':Train_predict,
        'TrainTest_time':TrainTest_time,'TrainTest_origin':TrainTest_origin,
        'TrainTest_predict':TrainTest_predict}
        return render_template('Stock_final_output.html',stock_data = stock_data)
    else:
        return render_template('Stockdata_parameter.html')






###*******************    LOCAL PART    **************************###




@app.route('/Stock_House_local')		#   choose method(module/YD/YX)_LOCAL
def Stock_House_local():
    return render_template('Stock_House_local.html')

@app.route('/Upload_house_local',methods=['GET','POST'])   # upload houseprice files_LOCAL
def Upload_house_local():
    def getdata(df):                                    ## get the data in 'df' file  and return a dic with all data in
        id_num = []
        for each in df['Id']:
            id_num.append(str(each))
        LotArea = []
        for each in df['LotArea']:
            LotArea.append(str(each))
        Area_Price=[]
        for i in range(1,len(df)):
            Area_Price.append([df['Id'][i],df['SalePrice'][i]])
            Street = df['Street']
            Utilities = df['Utilities']
            LotConfig = df['LotConfig']
            Neighborhood=df['Neighborhood']
            YearBuilt = df['YearBuilt']
            RoofStyle = df['RoofStyle']
            GrLivArea = df['GrLivArea']
            SaleType = df['SaleType']
            SaleCondition = df['SaleCondition']
            SalePrice = []
        for each in df['SalePrice']:
            SalePrice.append(str(each))
        HouseStyle = df['HouseStyle']
        labels=sorted(df['Neighborhood'])

        counts = {}
        times=[]
        each_1=[]
        for x in labels:
            if x in counts:
                counts[x] += 1
            else:
                counts[x] = 1
        for each in counts:
            each_1.append(each)
            times.append(counts[each])
        Neighborhood_str = ",".join(Neighborhood)
        list_type = (list(df.head(0)))
        list_type_1=",".join(list_type)


        numeric_variables=[]
        categorical_variables=[]

        for each in list_type:
            if len(set(df[each])) < 26:

                categorical_variables.append(each)

            else:

                numeric_variables.append(each)
        categorical_variables_1=",".join(categorical_variables)
        numeric_variables_1= ",".join(numeric_variables)
        numeric_variables_lgbm=numeric_variables
        numeric_variables_lgbm.remove('Id')
        numeric_variables_lgbm.remove('SalePrice')


        mydata = {'numeric_variables_lgbm':numeric_variables_lgbm,'Street':list(set(Street)),'Utilities':list(set(Utilities)),'LotConfig':list(set(LotConfig)),
        'HouseStyle':list(set(HouseStyle)),'RoofStyle':list(set(RoofStyle)),'SaleType':list(set(SaleType)),
        'SaleCondition':list(set(SaleCondition)),'Neighborhood':list(set(Neighborhood)),
        'list_type':list_type_1,'list_type_1':list_type,'listnum':len(df),'Neighborhood_str':Neighborhood_str,
        'Area_Price':Area_Price,'Neighborhood_num_1':len(times),'Neighborhood_num':times,
        'Neighborhood_type':each_1,'id_num':map(int,id_num),'LotArea':map(int,LotArea),
        'SalePrice':map(int,SalePrice),'categorical_variables':categorical_variables_1,
        'numeric_variables':numeric_variables_1,'categorical_variables_1':categorical_variables,
        'numeric_variables_1':numeric_variables
        }
        return mydata
    if request.method == 'POST':
        ## step 1. get the file user choose and use def getdata to get the data needed.
        f = request.files['file']
        if 'file' not in request.files:
            log.error('[upload] Upload attempt with no file')
            return Response('No file uploaded', status=500)
        else:
            f.save(secure_filename(f.filename))
            df = pd.read_csv(f.filename)
        global mydata_l
        mydata_l = getdata(df)

        return render_template('Housedata_description_local.html',mydata=mydata_l)
    else:
        return render_template('Upload_house_local.html')





@app.route('/Upload_stock_local',methods=['GET','POST'])   # upload stock files_LOCAL
def Upload_stock_local():
    if request.method == 'POST':
        ## step 1. save the file user choose
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return render_template('Choose_LSTM_local.html')
    else:
        return render_template('Upload_stock_local.html')




@app.route('/Stockdata_parameter_local',methods=['GET','POST'])			# upload module/YD module parameter_local
def Stockdata_parameter_local():
    def get(name):                              ##  get values from the HTML part ,'name' is the 'id' of HTML <input>
        return request.values.get(name)
    if request.method == 'POST':
        ## step 1. get the stock data parameter from HTML
        stock_parameter={}
        stock_parameter['e'] = int(get('e'))
        stock_parameter['lb'] = int (get('lb'))
        stock_parameter['lr'] = float (get('lr'))
        stock_parameter['tp'] = float (get('tp'))

        ## step 2. run the LSTM module locally
        a = os.popen('python module/YD/main.py -e {e} -lb {lb} -lr {lr} -tp{tp}'.format(e=stock_parameter['e'],
        lb=stock_parameter['lb'],lr=stock_parameter['lr'],tp=stock_parameter['tp']))

        ## step 3. read main.py output csv files
        outputTest = pd.read_csv('module/YD/outputTest.csv')
        outputTrain = pd.read_csv('module/YD/outputTrain.csv')
        outputTrainTest = pd.read_csv('module/YD/outputTrainTest.csv')
        Test_time = outputTest['Unnamed: 0']
        Test_origin = outputTest['origin']
        Test_predict = outputTest['predict']
        Train_time = outputTrain['Unnamed: 0']
        Train_origin = outputTrain['origin']
        Train_predict = outputTrain['predict']
        TrainTest_time = outputTrainTest['Unnamed: 0']
        TrainTest_origin = outputTrainTest['origin']
        TrainTest_predict = outputTrainTest['predict']

        stock_data={'Test_time':Test_time,'Test_origin':Test_origin,
        'Test_predict':Test_predict,'Train_time':Train_time,
        'Train_origin':Train_origin,'Train_predict':Train_predict,
        'TrainTest_time':TrainTest_time,'TrainTest_origin':TrainTest_origin,
        'TrainTest_predict':TrainTest_predict}
        return render_template('Stock_final_output_local.html',stock_data = stock_data)
    else:
        return render_template('Stockdata_parameter_local.html')






@app.route('/Housedata_parameter_local',methods=['GET','POST'])		#YX modules brief_LOCAL
def Housedata_parameter_local   ():
    def get(name):                      ##  get values from the HTML part ,'name' is the 'id' of HTML <input>
        return request.values.get(name)

    if request.method == 'POST':
        ## step 1. get housedata parameters from HTML
        LotArea = get("LotArea")
        Neighborhood = get("Neighborhood")
        YearBuilt = get("YearBuilt")
        GrLivArea = get("GrLivArea")
        Street = get("Street")
        Utilities = get("Utilities")
        LotConfig = get("LotConfig")
        HouseStyle = get("HouseStyle")
        RoofStyle = get("RoofStyle")
        SaleType = get('SaleType')
        SaleCondition = get('SaleCondition')

        lgbm_data=[LotArea,Street,Utilities,LotConfig,Neighborhood,
        HouseStyle,YearBuilt,RoofStyle,GrLivArea,SaleType,SaleCondition]
        lgbm_data_1=",".join(lgbm_data)

         ##step 2. Data Processing.
        def getSortedValues(row):           ## make data in a certain order('row' is the key for the data need to be sorted)
            sortedValues=[]
            keys=row.keys()
            keys.sort()
            for key in keys:
                sortedValues.append(row[key])
            return sortedValues

        rows = [{'Column1': 1, 'Column2': LotArea,'Column3': Street,'Column4':Utilities,'Column5':LotConfig,
                'Column6':Neighborhood,'Column7':HouseStyle,'Column8':YearBuilt,'Column9':RoofStyle,
                'Column10':GrLivArea,'Column11':SaleType,'Column12':SaleCondition},
                ]

        names={'Column1': 'Id', 'Column2': 'LotArea','Column3': 'Street','Column4':'Utilities','Column5':'LotConfig',
                'Column6':'Neighborhood','Column7':'HouseStyle','Column8':'YearBuilt','Column9':'RoofStyle',
                'Column10':'GrLivArea','Column11':'SaleType','Column12':'SaleCondition'}

        ## step 3. write test.csv in order
        fileobj=open("module/YX/test.csv",'wb')
        fileobj.write('\xEF\xBB\xBF')
        writer = csv.writer(fileobj)
        sortedValues = getSortedValues(names)
        writer.writerow(sortedValues)
        for row in rows:
            sortedValues = getSortedValues(row)
            print (sortedValues)
            writer.writerow(sortedValues)
        fileobj.close()
        ## step 4. run LGBM module locally
        a = os.popen('python module/YX/lgbm.py')

        show = a.readlines()
        pred_y_show=eval((show[-1]))[0]
        quantitative = re.findall("\d+",show[3])[0]
        qualitative = re.findall("\d+",show[3])[1]
        train_x1 = show[6]
        train_y1 = show[7]
        test_x1 = show[8]
        return render_template('House_final_output_local.html',pred_y=round(pred_y_show,2),train_x1=train_x1,train_y1=train_y1
            ,test_x1=test_x1,quantitative=quantitative,qualitative=qualitative)

    else:
        return render_template('Housedata_parameter_local.html',mydata=mydata_l)



if __name__ == "__main__":
    app.run(port=5050,debug=True)
