#!/usr/bin/env python
# coding: utf-8

# ## Data Wrangling (Python3)
# ### Manipulate Remote Engine Local Talend Log Files 
# ### Author: matheuspavanetti@gmail.com
# ### Release: 0.1.0 | Last Update Date: 7/28/2021

# In[1]:


# Ideas and notes for future releases
# Implement logging


# In[65]:


# Importing Libraries
from pandas import DataFrame,read_csv,to_datetime,merge
from datetime import datetime
from os import path,remove
from glob import glob
from shutil import rmtree
from time import sleep
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from configparser import ConfigParser
import pytz
#from logging import info,debug,error,fatal

# Modules to install on virtual environment
#pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org elasticsearch
#pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pandas


# In[66]:

# configparser initialization
config = ConfigParser()
config.read(path.dirname(__file__)+"\..\config.ini")
#config.sections()

def boolean(x):
    if(x == 'True' or x == 'true'):
        return True
    else:
        return False


# In[67]:


# Starting an Elasticsearch client instance
es = Elasticsearch(
    [config['Elasticsearch']['host']],
    http_auth=(config['Elasticsearch']['login'], config['Elasticsearch']['password']),
    scheme=config['Elasticsearch']['scheme'],
    port=int(config['Elasticsearch']['port']),
    http_compress=boolean(config['Elasticsearch']['http_compress'])
)


# In[68]:


# Talend Remote Engine Job Log Files Folder and filemasks.
   
# Point this variable to the Remote Engine Installetion Folder 
config_files_path = config['TalendLogFiles']['path']

# Do not change the files pattern
resuming_files = config['TalendLogFiles']['resuming_mask']
stdOutErr_Files = config['TalendLogFiles']['stdoutErr_mask']
task_files = config['TalendLogFiles']['task_mask']

# Start (True/False) variable
start = boolean(config['Application']['start'])

# Interval Seconds
seconds = int(config['Application']['seconds'])


# In[69]:


# function to check if files exist on source dir.
def check_files():
    resuming = [path.abspath(x) for x in glob(config_files_path + resuming_files)]
    stdOutErr = [path.abspath(x) for x in glob(config_files_path + stdOutErr_Files)]
    task = [path.abspath(x) for x  in glob(config_files_path + task_files)]

    if not resuming and not task and not stdOutErr:
        #print("Resuming, task and stdOutErr files were not found in source dir, Aborting operation...")
        return False
    else:    
        print("Files found, starting processing...")
        return True


# In[314]:


# Function Parse Talend Logs

def parseLogs():
    
    try:
        # Listing Files to process and storing on variables.
        resuming = [path.abspath(x) for x in glob(config_files_path + resuming_files)]
        stdOutErr = [path.abspath(x) for x in glob(config_files_path + stdOutErr_Files)]
        task = [path.abspath(x) for x  in glob(config_files_path + task_files)]
         
        # Declaring Timezone
        timezone = pytz.timezone("UTC")

        # Looping over resuming, stdOutErr and task (sequentially).
        for i in resuming:
            resumingPid = i.split('\\')[-1].replace(".log","").replace("resuming_","")
            resumingDate = datetime.strptime(resumingPid.split('_')[0], '%Y%m%d%H%M%S')
            resumingDateWith_timezone = timezone.localize(resumingDate)
            resumingYear = str(resumingDateWith_timezone.year)
            resumingMonth = str(resumingDateWith_timezone.month)
            
            # Looping over stdOutErr
            for j in stdOutErr:
                stdOutErrPid = j.split('\\')[-1].replace(".log","").replace("stdOutErr_","")
                stdOutErrDate = datetime.strptime(stdOutErrPid.split('_')[0], '%Y%m%d%H%M%S')
                stdOutErrWith_timezone = timezone.localize(stdOutErrDate)
                stdOutErrYear = str(stdOutErrWith_timezone.year)
                stdOutErrMonth = str(stdOutErrWith_timezone.month)

                # Checking if the resuming pid is the same as stdOutErr
                if(resumingPid == stdOutErrPid):

                    # Creating a dataframe for resuming files.
                    resuming_df = read_csv(i,sep = ',', engine = 'python')
                    
                    # remove extra strings from column JobContext
                    resuming_df['context'] = resuming_df['jobContext'].str.split('_').str[0]
                    
                    # parse datetime to elasticsearch date format
                    resuming_df['eventDate'] = to_datetime(resuming_df['eventDate'])
                    resuming_df["datetime"] = resuming_df['eventDate'].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
                    
                    # check flag
                    def checkFlag(row):
                        if row['type'] == "JOB_ENDED":
                            return 1
                        else:
                            return 0
                    
                    # Assign flag column    
                    resuming_df['flag'] = resuming_df.apply (lambda row: checkFlag(row), axis=1)
                    
                    # Canculating flag result
                    flagResult = resuming_df['flag'].sum()

                    # Calculating column result
                    def checkResult(row):
                        if row['logPriority'] == "FATAL":
                            return 1
                        if row['logPriority'] == "ERROR":
                            return 1
                        if row['logPriority'] == "ERRO":
                            return 1
                        return 0
                        
                    # Applying calculated function result to result column
                    resuming_df['tempresult'] = resuming_df.apply (lambda row: checkResult(row), axis=1)
                    
                    # Sum of errors
                    status = resuming_df['tempresult'].sum()
                    
                    # Check Status funcion
                    def checkStatus(row):
                        if row['type'] == "JOB_ENDED":
                            if status > 0:
                                return "FAILED"
                            else:
                                return "SUCCESS"
                        elif (row['type'] == "JOB_STARTED" and flagResult == 0):
                            return "RUNNING"
                        else:
                            return ""
                    
                    # Assign result    
                    resuming_df['result'] = resuming_df.apply (lambda row: checkStatus(row), axis=1)

                    # Calculating column duration
                    def checkDuration(row):
                        if row['type'] == "JOB_STARTED":
                            return row['datetime']
                        else:
                            return None
                        
                   # Applyting date dif     
                    resuming_df['tempDuration'] = resuming_df.apply (lambda row: checkDuration(row), axis=1)
                    
                    # Storing Start Datetime
                    startDate = resuming_df['tempDuration'][0]
                    
                    # Calculating duration time
                    def duration(row):
                        if row['type'] == "JOB_ENDED":
                            startTime = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%S.%f')
                            endTime = datetime.strptime(row['datetime'], '%Y-%m-%dT%H:%M:%S.%f')
                            if endTime >= startTime:
                                elapsed = endTime - startTime
                            else:
                                return ""
                            return str(elapsed)
                        else:
                            return ""
                        
                    # Updating column duration
                    resuming_df['duration'] = resuming_df.apply (lambda row: duration(row), axis=1)
                    
                    # Eliminating non useful columns from the resuming_df by filtering columns.
                    new_resuming_df = resuming_df[['datetime','pid','type','partName','project','jobName','context','jobVersion','logPriority','errorCode','message','result','duration']].fillna("")

                    # Opening stdOutErr Files and splitting strings.
                    with open(j,'r') as file:
                        filePath = j
                        filename = filePath.split("\\")[-1]
                        pid = filename.replace("stdOutErr_","").replace(".log","")
                        readFile = file.read()
                        datetimeStr = datetime.strptime(pid.split("_")[0], '%Y%m%d%H%M%S')

                    # Creating a data dictionary with the new strings.   
                    stdOutErrDict = {
                        "datetime2": datetimeStr,
                        "pid": pid,
                        "fileName": filename,
                        "studioLogs": readFile
                    }
                    
                    # Checking if the stdOutErr file has the job ended by user string
                    if("ENDED BY USER" in readFile):
                        jobAborted = True
                    else:
                        jobAborted = False

                    # Creating a pd dataframe from the dictionary with a single index.
                    stdOutErrDf = DataFrame(stdOutErrDict, index=[0])
                    
                    # Looking up resuming with stdOutErr, filtering
                    resumingXstdOutErrDf = merge(left=new_resuming_df,right=stdOutErrDf, left_on='pid',right_on='pid')
                    resumingXstdOutErrDfFiltered = resumingXstdOutErrDf[['pid','datetime2','jobName','fileName','studioLogs']].drop_duplicates()
                    
                    # Deleting resuming and stdoutrr files
                    if(flagResult > 0):
                        remove(j)
                        stdOutErr.remove(j)
                        remove(i)
                        resuming.remove(i)
                        
                    # Looping over task log files
                    for k in task:

                        # Creating a dataframe for task files.
                        task_df = read_csv(k,sep = '|', engine = 'python', index_col=False, 
                                         names=['datetime', 'loglevel', 'thread', 'action','location','message']).iloc[ 0:20 , : ]

                        # Getting Artifact Name
                        if(task_df[task_df.columns[0]].count() >= 11):
                            taskArtifactName = task_df['datetime'][11].replace(",","").strip().split(':')[1].strip().replace("\"","")
                        else:
                            continue

                        # Getting task datetime
                        taskDateTime = datetime.strptime(task_df['datetime'][0].replace(",",".").strip(), '%Y-%m-%dT%H:%M:%S.%f')
                        taskDateTimeWith_timezone = timezone.localize(taskDateTime)
                        difference = (resumingDateWith_timezone - taskDateTimeWith_timezone).total_seconds()

                        # Getting resuming Artifact Name
                        resumingArtifactName = new_resuming_df['jobName'].drop_duplicates()[0]

                        # Checking if the pid is correct matching resuming job name with artifact name plus time seconds difference must be between zero and five
                        if(taskArtifactName == resumingArtifactName):
                            if(difference >= -1 and difference <=10):

                                # Opening stdOutErr Files and splitting strings.
                                with open(k,'r') as file:
                                    readTaskFile = file.read()
                                    datetimeTask = datetime.strptime(new_resuming_df['pid'].drop_duplicates()[0].split("_")[0], '%Y%m%d%H%M%S')
                                    datetimeTaskYear = str(datetimeTask.year)
                                    datetimeTaskMonth = str(datetimeTask.month)

                                # Creating Result Task Dict    
                                result_taskDict = {
                                    "pid": new_resuming_df['pid'].drop_duplicates()[0],
                                    "datetime": task_df['datetime'][10].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "jobName": new_resuming_df['jobName'].drop_duplicates()[0],
                                    "task_id": task_df['datetime'][13].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "task_execution_id": task_df['datetime'][4].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "remote_engine_id": task_df['datetime'][2].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "remote_engine_name": task_df['datetime'][3].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "task_execution_id": task_df['datetime'][4].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "workspace_name": task_df['datetime'][5].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "workspace_id": task_df['datetime'][6].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "environment_name": task_df['datetime'][7].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "environment_id": task_df['datetime'][8].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "environment_version": task_df['datetime'][9].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "trigger_timestamp": task_df['datetime'][10].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "artifact_name": task_df['datetime'][11].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "artifact_version": task_df['datetime'][12].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "task_name": task_df['datetime'][14].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "task_version": task_df['datetime'][15].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "run_type": task_df['datetime'][16].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "compatibility_version": task_df['datetime'][17].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "count_of_attempts": task_df['datetime'][18].replace(",","").strip().split(':')[1].strip().replace("\"",""),
                                    "taskLog": readTaskFile
                                }
                                result_taskDF = DataFrame(result_taskDict, index=[0]) # Assigning a DataFrame

                                # Inserting task documents to elasticsearch index
                                taskIndex = 'talendlog-task-'+datetimeTaskYear+'-'+datetimeTaskMonth+'-000001'
                                taskIndexDict = result_taskDF.to_dict(orient="records")
                                bulk(es,taskIndexDict,index=taskIndex,request_timeout=200) # Elasticsearch bulk insert
                                
                                # Deleting task files
                                if(flagResult > 0):
                                    remove(k)
                                    task.remove(k)
                                
                                # Checking if the task has the execution terminated info
                                if("EXECUTION_TERMINATED" in readTaskFile):
                                    taskAborted = True
                                else:
                                    taskAborted = False

                                # Removing jobs running from the list array
                                #if(flagResult == 0 and taskAborted == False):
                                if(flagResult == 0):
                                    task.remove(k)
                    
                    
                    # Elasticsearch running query body
                    runningBody = {
                          "query": {
                            "bool": {
                              "filter": [
                                {
                                  "term": {
                                    "pid": {
                                      "value": resumingPid
                                    }
                                  }
                                },
                                {
                                  "term": {
                                    "type": {
                                      "value": "JOB_STARTED"
                                    }
                                  }
                                },
                                {
                                  "term": {
                                    "result": {
                                      "value": "RUNNING"
                                    }
                                  }
                                }
                              ], 
                              "must": [
                                {
                                  "match_all": {}
                                }
                              ]
                            }
                          }
                        }
                    
                    # Elasticsearch delete by query body
                    deleteRunningbody = {
                              "query":{
                               "term": {
                                    "pid": {
                                    "value": resumingPid
                                  }
                                } 
                              }
                            }
                    
                    
                    # Update by query , aborted
                    updateAbortedBody = {
                         "script": {
                            "inline": "ctx._source.result='ABORTED'",
                            "lang": "painless"
                         },
                         "query": {
                            "bool": {
                              "filter": [
                                {
                                  "term": {
                                    "pid": {
                                      "value": resumingPid
                                    }
                                  }
                                },
                                {
                                  "term": {
                                    "type": {
                                      "value": "JOB_STARTED"
                                    }
                                  }
                                },
                                {
                                  "term": {
                                    "result": {
                                      "value": "RUNNING"
                                    }
                                  }
                                }
                              ], 
                              "must": [
                                {
                                  "match_all": {}
                                }
                              ]
                            }
                          }
                       } 
                    
                    updateRunning = {
                      "doc": {
                        "result": "ABORTED"
                      }
                    }
                    
                    # resuming documents to elasticsearch index 
                    resumingIndex = 'talendlog-resuming-'+resumingYear+'-'+resumingMonth+'-000001'
                    resumingElasticDict = new_resuming_df.to_dict(orient="records")
                    
                    # stdOutErr documents to elasticsearch index
                    stdOutErrIndex = 'talendlog-stdouterr-'+stdOutErrYear+'-'+stdOutErrMonth+'-000001'
                    stdOutErrDict = resumingXstdOutErrDfFiltered.to_dict(orient="records")
                    
                    # Checking if the index exist if not, create the index and bulk insert the document
                    if (es.indices.exists(index=resumingIndex) and es.indices.exists(index=stdOutErrIndex) and es.indices.exists(index=taskIndex)):
                        
                        # Searching for the match document
                        jobRunning = es.search(index=resumingIndex, body=runningBody)
                        jobRunningResult = int(jobRunning['hits']['total']['value'])
                    
                        # querying for jobs that has the running status in elasticsearch index
                        if(flagResult == 0):
                            # Check if the job running already exist in elasticsearch, if so, delete it
                            if ((not taskAborted or not jobAborted) and jobRunningResult > 0):

                                # Elasticsearch Bulk delete by query
                                es.delete_by_query(index=resumingIndex, body=deleteRunningbody)
                                es.delete_by_query(index=stdOutErrIndex, body=deleteRunningbody)
                                es.delete_by_query(index=taskIndex, body=deleteRunningbody)

                                # Elasticsearch Insert Documents
                                bulk(es, resumingElasticDict, index=resumingIndex, request_timeout=200) #Elasticsearch bulk insert
                                bulk(es,stdOutErrDict,index=stdOutErrIndex,request_timeout=200) #Elasticsearch bulk insert


                            # Check if the job was aborted and status is running still
                            elif ((taskAborted or jobAborted) and jobRunningResult > 0):

                                # Elasticsearch Update (Alternative)
                                #jobRunningId = jobRunning['hits']['hits'][0]['_id']
                                #es.update(index=resumingIndex,id=jobRunningId,body=updateRunning)

                                # Elasticsearch update by query
                                es.update_by_query(index=resumingIndex, body=updateAbortedBody)

                                # Delete log files from jobs wich were aborted
                                remove(i)
                                remove(j)
                                remove(k)

                            else:  
                                # Elasticsearch Insert Documents
                                bulk(es, resumingElasticDict, index=resumingIndex, request_timeout=200) #Elasticsearch bulk insert
                                bulk(es,stdOutErrDict,index=stdOutErrIndex,request_timeout=200) #Elasticsearch bulk insert

                        elif(flagResult > 0 and jobRunningResult > 0):
                            # Elasticsearch Bulk delete by query
                            es.delete_by_query(index=resumingIndex, body=deleteRunningbody)
                            es.delete_by_query(index=stdOutErrIndex, body=deleteRunningbody)
                            es.delete_by_query(index=taskIndex, body=deleteRunningbody)

                            # Elasticsearch Bulk insert documents
                            bulk(es, resumingElasticDict, index=resumingIndex, request_timeout=200) #Elasticsearch bulk insert
                            bulk(es,stdOutErrDict,index=stdOutErrIndex,request_timeout=200) #Elasticsearch bulk insert
                            
                        else:
                            # Elasticsearch Bulk insert documents
                            bulk(es, resumingElasticDict, index=resumingIndex, request_timeout=200) #Elasticsearch bulk insert
                            bulk(es,stdOutErrDict,index=stdOutErrIndex,request_timeout=200) #Elasticsearch bulk insert
                                        
                    else:
                        # Elasticsearch Bulk insert documents
                        bulk(es, resumingElasticDict, index=resumingIndex, request_timeout=200) #Elasticsearch bulk insert
                        bulk(es,stdOutErrDict,index=stdOutErrIndex,request_timeout=200) #Elasticsearch bulk insert
                        

        print("Talend Logs files has been successfully sent to Elasticsearch.")
        return True
    
    except Exception as e:
        print("Some error has occured during the parseLogs function:")
        print(e)
        return False            


# In[281]:


# Starting point to run parseLogs function if files are available.

# Inifinite Loop Function
if start:
    while True:
        sleep(seconds)
        if check_files():
            parseLogs()
