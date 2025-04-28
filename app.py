import select
import requests
import fnmatch
import socket
import glob
import json
import subprocess
import shelve
from flask import Flask, g, jsonify, request, send_file, make_response
from flask_restful import reqparse, abort, Api, Resource
import zipfile
from werkzeug.utils import secure_filename
import re
import ast
import logging
from collections import defaultdict
import binascii
import codecs
import cx_Oracle
import os
import pandas as pd
import numpy as np
import shutil
import time
from file_read_backwards import FileReadBackwards
from datetime import datetime, timezone
import configparser
from gunicorn import glogging
from flask_cors import CORS
import logging
import platform
import lzma
import hashlib
import psutil
import glob
import sqlite3
import threading
import multiprocessing as mp
import zmq
import base64
import grp
from Crypto.Cipher import AES
import boto3
import botocore
import smart_open
from io import BytesIO, TextIOWrapper
import gzip
import warnings
import sqlanydb
import openpyxl
from openpyxl import Workbook
import pyodbc

app = Flask(__name__, static_folder="./web", static_url_path="/")
CORS(app)
api = Api(app)

OSPlatBit = platform.processor()
OSPlat = platform.system()
sshTimeOut = 120

config = configparser.RawConfigParser()
config.read('config/oneplace.cfg')

oneplace_base = config.get('ONEPLACE_CONFIG', 'BASE_DIR')
oneplace_home = config.get('ONEPLACE_CONFIG', 'HOME_DIR')
gg_home = config.get('ONEPLACE_CONFIG', 'GG_HOME')
db_home = config.get('ONEPLACE_CONFIG', 'DB_HOME')
rac_check = config.get('ONEPLACE_CONFIG', 'RAC_CHECK')
oneplace_host = config.get('ONEPLACE_CONFIG', 'ONEPLACE_HOST')
oneplace_port = config.get('ONEPLACE_CONFIG', 'SERVER_PORT')
trailPath = config.get('ONEPLACE_CONFIG', 'GG_TRAIL')
OPlace_Debug = config.get('ONEPLACE_CONFIG', 'ONEPLACE_DEBUG')
image_uploads = os.path.join(oneplace_base, 'images')
processing_dir = os.path.join(oneplace_base, 'processing')
temp_dir = os.path.join(oneplace_base, 'tempdir')

if not os.path.exists(image_uploads): os.makedirs(image_uploads)
if not os.path.exists(processing_dir): os.makedirs(processing_dir)
if not os.path.exists(temp_dir): os.makedirs(temp_dir)

hName = socket.gethostname()
hName = hName.split('.')
hName = hName[0]

if os.path.exists(db_home):
    os.environ['LD_LIBRARY_PATH'] = os.path.join(db_home, 'lib64') + ':' + os.path.join(db_home, 'bin64', 'jre180', 'lib', 'amd64', 'client') + ':' + os.path.join( db_home, 'bin64', 'jre180', 'lib', 'amd64', 'server') + ':' + os.path.join(db_home, 'bin64', 'jre180', 'lib', 'amd64') + ':' + os.path.join( db_home, 'bin64', 'jre180', 'lib', 'amd64', 'native_threads')
    os.environ['SQLANY_API_DLL'] = os.path.join(db_home, 'bin64') + ':' + os.path.join(db_home, 'bin','sdk')

os.environ['ORACLE_HOME'] = db_home
logdump_bin = os.path.join(gg_home, 'logdump')
ggsci_bin = os.path.join(gg_home, 'ggsci')

LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
logging.basicConfig(filename=os.path.join(oneplace_home, 'oneperror.log'), level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()

warnings.simplefilter(action='ignore', category=UserWarning)


def processCheckAll():
    while True:
        time.sleep(300)
        processCheckDemand()


t = threading.Thread(target=processCheckAll)
t.start()


def transfer_dumpFile(src_dep_url, tgt_dep_url, srcdbName, jobName, srcDumpDir, fileName, cdbCheck, pdbName, tgtdbName,
                      tgtDumpDir):
    src_dep_url = src_dep_url + '/selectconn'
    payload = {"dbName": srcdbName}
    headers = {"Content-Type": "application/json"}
    r = requests.post(src_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
    user = r.json()[0]
    passwd = cipher.decrypt(r.json()[1])
    servicename = r.json()[2]
    conSrc = cx_Oracle.connect(user, passwd, servicename)
    tgt_dep_url = tgt_dep_url + '/selectconn'
    payload = {"dbName": tgtdbName}
    headers = {"Content-Type": "application/json"}
    r = requests.post(tgt_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
    user = r.json()[0]
    passwd = cipher.decrypt(r.json()[1])
    servicename = r.json()[2]
    conTgt = cx_Oracle.connect(user, passwd, servicename)
    cursorSrc = conSrc.cursor()
    cursorTgt = conTgt.cursor()
    if cdbCheck == 'YES' and len(pdbName) > 0:
        cursorSrc.execute('''alter session set container=''' + str(pdbName))
    src_bfile = cursorSrc.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (srcDumpDir, fileName));
    f_len = src_bfile.size()
    with open(os.path.join(oneplace_home, jobName, fileName + '_Size.log'), 'w') as infile:
        infile.write(str(f_len))
    f_buf = 1
    totalELA = 0
    xfrSpeed = 'UNKOWN'
    dumpDir = os.path.join(oneplace_home, jobName)
    dumpFile = os.path.join(oneplace_home, jobName, fileName)
    OTYPE = conTgt.gettype("SYS.UTL_FILE.FILE_TYPE")
    out_file = cursorTgt.callfunc("utl_file.fopen", OTYPE, (tgtDumpDir, fileName, 'ab', 32767));
    try:
        startTime = time.time()
        while f_buf <= f_len:
            f_buffer = src_bfile.read(f_buf, 32767)
            cursorTgt.callproc("utl_file.put_raw", [out_file, f_buffer, True]);
            f_buf = f_buf + len(f_buffer)
            endTime = time.time()
            elapTime = endTime - startTime
            tp = (f_buf / (1024 * 1024)) / elapTime
            eta = (f_len - f_buf) / (1024 * 1024) * tp
            if tp < 1:
                xfrSpeed = str(round(tp * 1024)) + ' KB/s'
            else:
                xfrSpeed = str(round(tp)) + ' MB/s'
            per = round(int(f_buf) / int(f_len) * 100, 2)
            with open(os.path.join(oneplace_home, jobName, fileName + '_speed'), 'w') as infile:
                infile.write(
                    str(per) + '$' + str(round(elapTime, 2)) + '$' + str(xfrSpeed) + '$' + str(f_len) + '$' + str(
                        f_buf - 1) + '$' + str(round(eta)))
        cursorTgt.callproc('UTL_FILE.FCLOSE', [out_file])
        tgt_bfile = cursorTgt.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (tgtDumpDir, fileName));
        if tgt_bfile.size() == f_len:
            per = 100
            with open(os.path.join(oneplace_home, jobName, fileName + '_speed'), 'w') as infile:
                infile.write(
                    str(per) + '$' + str(round(elapTime, 2)) + '$' + str(xfrSpeed) + '$' + str(f_len) + '$' + str(
                        f_buf - 1) + '$' + str(0))
    except cx_Oracle.DatabaseError as e:
        logger.info(str(e))
    except Exception as e:
        with open(os.path.join(oneplace_home, jobName, jobName + '_S3_Transfer.log'), 'w') as infile:
            infile.write(fileName + ' - ' + str(e))
        if os.path.exists(os.path.join(oneplace_home, jobName, fileName + '_Size.log')):
            os.remove(os.path.join(oneplace_home, jobName, fileName + '_Size.log'))
    finally:
        if conSrc:
            cursorSrc.close()
            conSrc.close()
        if conTgt:
            cursorTgt.close()
            conTgt.close()


def startExtract(jobName):
    try:
        print('Inside startEx')
        extract = os.path.join(oneplace_base, 'extract')
        ssh = subprocess.run([extract, jobName], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ILExtract, stderr = ssh.communicate(timeout=sshTimeOut)
    except Exception as e:
        logger.info('Extract Start Exception - ' + str(e))


def download_dumpFile(jobName, dbName, bucketName, dirName):
    con = selectConn(dbName)
    con = con[0]
    cursor = con.cursor()
    try:
        download_File = """SELECT rdsadmin.rdsadmin_s3_tasks.download_from_s3(
                                   p_bucket_name    =>  :bucketName, 
                                   p_directory_name =>  :dirName) 
                            AS TASK_ID FROM DUAL"""
        cursor.execute(download_File, bucketName=bucketName, dirName=dirName)
        db_row = cursor.fetchone()
        if db_row:
            taskID = db_row[0]
            with open(os.path.join(oneplace_home, jobName, jobName + '_Download'), 'w') as infile:
                infile.write(taskID)
    except cx_Oracle.DatabaseError as e:
        with open(os.path.join(oneplace_home, jobName, jobName + '_DownloadLog'), 'w') as infile:
            infile.write(str(e))
    finally:
        if con:
            cursor.close()
            con.close()


def ILGetStats(procName, jobName):
    while True:
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("stats " + procName + ' ,TOTAL,LATEST,REPORTRATE SEC \n')
        ILProcStatRate, stderr = ssh.communicate(timeout=sshTimeOut)
        if 'ERROR' in ILProcStatRate:
            pass
        else:
            with open(os.path.join(oneplace_home, jobName, procName + 'Rate.lst'), 'w') as infile:
                infile.write(ILProcStatRate)
        time.sleep(30)
        if not os.path.exists(os.path.join(oneplace_home, jobName, procName + 'running')):
            break


def processCheckDemand():
    if os.path.exists(ggsci_bin):
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write('info extract *' + '\n')
        ssh.stdin.write('info replicat *' + '\n')
        ssh.stdin.write('info mgr' + '\n')
        InfoAll, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'infoall'), mode='w') as outfile2:
            outfile2.write(InfoAll)


@app.route("/")
def index():
    return app.send_static_file("index.html")


def output_type_handler(cursor, name, defaultType, size, precision, scale):
    return cursor.var(cx_Oracle.STRING, 255, arraysize=cursor.arraysize)


def dataframe_difference(df1, df2, which=None):
    """Find rows which are different between two DataFrames."""
    comparison_df = df1.merge(df2,
                              indicator=True,
                              how='outer')
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]
    return diff_df


def chmod_dir(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o755)


def OPlaceDebug(filename):
    if OPlace_Debug == 'N':
        for name in filename:
            if os.path.exists(os.path.join(oneplace_home, name)):
                os.remove(os.path.join(oneplace_home, name))


BS = 32
pad = lambda s: bytes(s + (BS - len(s) % BS) * chr(BS - len(s) % BS), 'utf-8')
unpad = lambda s: s[0:-ord(s[-1:])]


class AESCipher:
    def __init__(self, key):
        self.key = bytes(key, 'utf-8')

    def encrypt(self, raw):
        raw = pad(raw)
        iv = 'OnePlaceMyPlaceV'.encode('utf-8')
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, enc):
        iv = 'OnePlaceMyPlaceV'.encode('utf-8')
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc)).decode('utf8')


cipher = AESCipher('OnePlaceMyPlaceJamboUrl111019808')


class ViewExtractLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        extractLog = []
        with open(os.path.join(oneplace_home, jobName, jobName + '_EXTRACT.log')) as infile:
            for line in infile:
                extractLog.append(line)
        return [extractLog]


class ViewReplicatLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        depName = data['depName']
        jobName = data['jobName']
        cursor.execute('select dep_url from onepconn where dep=:dep', {"dep": depName})
        row = cursor.fetchone()
        if row:
            tgt_dep_url = row[0]
            tgt_dep_url = tgt_dep_url + '/viewreplicatlog'
            headers = {"Content-Type": "application/json"}
            payload = {'jobName': jobName}
            r = requests.post(tgt_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            print(r.json()[0])
            replicatLog = r.json()[0]
        return [replicatLog]


class ggDepDet(Resource):
    def get(self):
        DBVersion = ''
        platform = ''
        try:
            val = selectConn(dbName)
            con = val[0]
            cursor = con.cursor()
            cursor.execute('''select version,platform from SYSHISTORY''')
            DBVer = cursor.fetchone()
            if DBVer:
                DBVersion = DBVer[0]
                platform = DBVer[1]
        except Exception as e:
            DBVer = 'Not Detected'
            platform = 'Not Detected'
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [DBVersion, platform]


class getTableName(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            tabDetails = {}
            schemaList = []
            cursor.execute("SELECT user_name(o.uid) AS owner, o.name AS tabname FROM sysobjects o WHERE o.type = 'U' AND o.name NOT LIKE 'sys%' UNION SELECT user_name(o.uid) AS owner, o.name AS tabname FROM sysobjects o WHERE o.type = 'U' AND o.name LIKE 'systemlink'")
            tabName = cursor.fetchall()
            for name in tabName:
                tabDetails[name[1]] = {"owner": name[0]}
                schemaList.append(name[0])    
            schemaList = list(set(schemaList))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tabDetails, schemaList]


class getViewName(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        try:
            val = selectConn(dbname)
            print(val)
            con = val[0]
            cursor = con.cursor()
            viewDetails = {}
            schemaList = []
            cursor.execute("SELECT user_name(uid) AS owner, name AS tabname FROM sysobjects WHERE type = 'V' AND name NOT LIKE 'sys%'")
            viewName = cursor.fetchall()
            #print(viewName)
            viewList = []
            for name in viewName:
                viewList.append({
                    'vcreator': name[0].strip(),
                    'viewtext': name[1].strip()  
                })
            for name in viewName:
                schemaList.append(name[0].strip())
            schemaList = list(set(schemaList))
        except Exception as e:
            logger.info(str(e))
            return jsonify({'error': str(e)})
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify({'views': viewList, 'schemas': schemaList})
        #return [viewName, schemaList]


class getProcName(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procDetails = {}
            schemaList = []
            cursor.execute("SELECT user_name(uid) AS owner, name AS procname from sysobjects where type='P'")
            procName = cursor.fetchall()
            for name in procName:
                schemaList.append(name[0].strip())
            schemaList = list(set(schemaList))
            procList = []
            for name in procName:
                procList.append({'owner':name[0].strip(), 'procName':name[1].strip()})
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify({'proc':procList, 'schemas':schemaList})
        #return [procName, schemaList]


class getTriggerName(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        trigName = []
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procDetails = {}
            schemaList = []
            cursor.execute("SELECT RTRIM(user_name(t.uid)) AS trigger_owner, t.name AS trigger_name, RTRIM(user_name(tbl.uid)) + '.' + tbl.name AS table_name FROM sysobjects t JOIN sysobjects tbl ON tbl.deltrig = t.id OR tbl.instrig = t.id OR tbl.updtrig = t.id WHERE t.type = 'TR'")
            table_fetch = cursor.fetchall()
            print(table_fetch)
            for name in table_fetch:
                trigName.append({'owner':name[0].strip(), 'trigName':name[1].strip(),'trigTable' : name[2].strip()})
            for name in table_fetch:
                print(name[0])
                schemaList.append(name[0])
            schemaList = list(set(schemaList))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [trigName, schemaList]


class getTrigNameFromSchema(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        print(schemaList)
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procNameList = []
            for schema in schemaList:
                cursor.execute("""
                                SELECT su.name + '.' + so.name AS full_trigger_name, so.name AS trigger_name, su.name AS owner, 
                                so.crdate AS created_date FROM sysobjects so JOIN sysusers su ON so.uid = su.uid 
                                WHERE so.type = 'TR' AND su.name = ? ORDER BY so.name
                                """, (schema,))
                table_fetch = cursor.fetchall()
                for name in table_fetch:
                    procNameList.append({'owner':name[0].strip()})
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [procNameList]


class getTrigText(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        procName = data['procName']
        print(procName)
        trigText=[]
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procName = procName.split('.')
            owner = procName[0]
            pname = procName[1]
            cursor.execute("SELECT c.text FROM sysobjects o JOIN syscomments c ON o.id = c.id WHERE o.type = 'TR' AND user_name(o.uid) = ? AND o.name = ? ", (owner, pname,))
            table_fetch = cursor.fetchall()
            for name in table_fetch: 
                trigText.append(name[0])
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [trigText]


class getProcNameFromSchema(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        count = 1
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procNameList = []
            for schema in schemaList:
                cursor.execute("SELECT RTRIM(user_name(uid)) + '.' + name AS proc_full_name  FROM sysobjects WHERE type = 'P' AND user_name(uid) = ? ", (schema,))
                table_fetch = cursor.fetchall()
                procNameList.extend([row[0] for row in table_fetch])
                print(procNameList)
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [procNameList]


class getProcText(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        procName = data['procName']
        procText=[]
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procName = procName.split('.')
            owner = procName[0]
            pname = procName[1]
            print(owner)
            print(pname)
            cursor.execute("SELECT sc.text AS procText FROM sysobjects so JOIN syscomments sc ON so.id = sc.id WHERE so.type = 'P' AND user_name(so.uid) = ? AND so.name = ?", (owner, pname,))
            table_fetch = cursor.fetchall()
            procText.extend([row[0] for row in table_fetch])
            print(procText)
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [procText]

class updateZoneDetails(Resource):
    def post(self):
        data = request.get_json(force=True)
        file_name = data['currentZone'] + ".txt"
        file_path = os.path.join("Zone", file_name)
        try:
            # if os.path.exists(file_path):
            #     with open(file_path, 'a') as file:
            #         existing_data = file.read().strip()
            #         input_elements = data['zoneFunctions'].split(',')
            #         for element in input_elements:
            #             if element.strip() not in existing_data:
            #                 with open(file_path, 'a') as file:
            #                     file.write(f"\n{element.strip()},")
            #                     print(f"Appended {element.strip()} to {file_name} in the {folder_name} folder.")
            #             else:
            #                 print(f"{element.strip()} already exists in {file_name} in the {folder_name} folder.")
            #         return "Apend"
            # else:
            #     with open(file_path, 'w') as file:
            #         input_elements = data['zoneFunctions'].split(',')
            #         for element in input_elements:
            #             file.write(f"{element.strip()},\n")
            #         return "Write"
            with open(file_path, 'w') as file:
                print(data['zoneFunctions'])
                file.write(data['zoneFunctions'])
                return "Success"
        except Exception as e:
            print(f"An error occurred: {e}")

class getZoneDetails(Resource):
    def post(self):
        data = request.get_json(force=True)
        file_name = data['currentZone'] + ".txt"
        directory_name = "Zone"
        file_path = os.path.join(directory_name, file_name)

        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
                return file_content
        except FileNotFoundError:
            return "No File"
        except Exception as e:
            return "Error"

class fetchAutomateExcel(Resource):
    def post(self):
        data = request.get_json(force=True)
        try:
            print("inside fetch excel")
            excel_file_path = data['sourceDbname'] + "_" + data['schemaName'] + '.xlsx'
            print(excel_file_path)
            df = pd.read_excel(excel_file_path)
            result_dict = df.to_dict(orient='records')
            response = jsonify(result_dict)
        except FileNotFoundError:
            response = jsonify({'error': 'File not found'})

        return response

class updateExcel(Resource):
    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + "_" + data['schemaName'] + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1

            # Add a new row with the determined "No," "Function," and "Output" values
            new_row = pd.DataFrame(
                {'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            # Save the updated DataFrame back to the Excel file
            df.to_excel(excel_file_path, index=False)
            return "Success"
        except Exception as e:
            return f"Error: {str(e)}"

class updateExcelView(Resource):
    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + "_view" + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1

            # Add a new row with the determined "No," "Function," and "Output" values
            new_row = pd.DataFrame(
                {'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            # Save the updated DataFrame back to the Excel file
            df.to_excel(excel_file_path, index=False)
            return "Success"
        except Exception as e:
            return f"Error: {str(e)}"

class updateExcelTrigger(Resource):
    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + "_" + data['schemaName'] + '_Trigger.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1

            # Add a new row with the determined "No," "Function," and "Output" values
            new_row = pd.DataFrame(
                {'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            # Save the updated DataFrame back to the Excel file
            df.to_excel(excel_file_path, index=False)
            return "Success"
        except Exception as e:
            return f"Error: {str(e)}"

class automateProcess(Resource):
    def post(self):
        data = request.get_json(force=True)
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        # print(procNameList)
        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            sshTimeOut = 600
            for process in procNameList:
                newProcName = process['vname']
                newProcName = newProcName.split('.')
                owner = newProcName[0]
                pname = newProcName[1]
                cursor.execute("select user_id from SYSUSER where user_name = ?", (owner,))
                userID = cursor.fetchall()[0][0]
                cursor.execute("select source from SYSPROCEDURE where creator = ? and proc_name = ?", (userID, pname,))
                procText = cursor.fetchall()
                if procText[0][0] != "None" or procText[0][0] != None:
                    dep_url = targetDep + "/updateAutomateProcess"
                    headers = {"Content-Type": "application/json"}
                    mgrPayload = {"dbName": targetDbname, "viewProc": procText, "processName":process['vname']}
                    resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=False, timeout=sshTimeOut)
                    print(str(resp.json()))
                    print("------------------------------------------------------")
                    if resp.json() == 'Created':
                        result = "Created"
                    elif "already exists" in resp.json():
                        result = "Already Exist"
                    elif "Not Loaded" in resp.json():
                        result = "Not Loaded"
                    else:
                        result = "Error"
                else:
                    result = "Error"

                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                # Write to Excel file
                excel_file = sourceDbname+ "_" + data['schemaName'] + '.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i +=1
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict


class fetchAutomateViewExcel(Resource):
    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_view.xlsx'
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class fetchAutomateTriggerExcel(Resource):
    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + "_" + data['schemaName'] + '_Trigger.xlsx'
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)


class automateView(Resource):
    def post(self):
        data = request.get_json(force=True)
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for process in procNameList:
                newProcName = process['vname']
                newProcName = newProcName.split('.')
                owner = newProcName[0]
                pname = newProcName[1]
                cursor.execute("select user_id from SYSUSER where user_name = ?", (owner,))
                userID = cursor.fetchall()[0][0]
                cursor.execute("select viewtext from SYSVIEWS where vcreator = ? and viewname= ?", (owner, pname,))
                procText = cursor.fetchall()
                dep_url = targetDep + "/updateAutomateView"
                headers = {"Content-Type": "application/json"}
                mgrPayload = {"dbName": targetDbname, "viewProc": procText}
                resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=False, timeout=sshTimeOut)
                print("=================================")
                print(resp.json())
                if resp.json() == 'Created':
                    result = "Created"
                elif "already exists" in resp.json():
                    result = "Already Exist"
                else:
                    result = "Error"

                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                # Write to Excel file
                excel_file = sourceDbname + '_view.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i +=1
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class automateTrigger(Resource):
    def post(self):
        data = request.get_json(force=True)
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        outputDict = []
        val = selectConn(sourceDbname)
        con = val[0]
        cursor = con.cursor()
        df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        try:
            i = 1
            for process in procNameList:
                newProcName = process['vname']
                newProcName = newProcName.split('.')
                owner = newProcName[0]
                pname = newProcName[1]
                cursor.execute("select trigdefn from SYSTRIGGERS where owner= ? and trigname = ?", (owner, pname,))
                procText = cursor.fetchall()
                dep_url = targetDep + "/updateAutomateTrigger"
                headers = {"Content-Type": "application/json"}
                mgrPayload = {"dbName": targetDbname, "viewProc": procText, "processName":process['vname']}
                resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=False, timeout=sshTimeOut)
                print("=================================")
                print(resp.json())
                if resp.json() == 'Created':
                    result = "Created"
                elif "already exists" in resp.json():
                    result = "Already Exist"
                else:
                    result = "Error"

                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                # Write to Excel file
                excel_file = sourceDbname+ "_" + data['schemaName'] + '_Trigger.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i +=1
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict


class getViewNameFromSchema(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            viewNameList = []
            for schema in schemaList:
                cursor.execute("SELECT rtrim(user_name(uid)) + '.' + name AS view_name  FROM sysobjects  WHERE type = 'V' AND user_name(uid) = ?", (schema,))
                table_fetch  = cursor.fetchall()
                viewNameList.extend([row[0] for row in table_fetch])
            print(f"View Names: {viewNameList}")
        except Exception as e:
            logger.info(str(e))
            print(str(e))
            return {"error": str(e)}
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify(viewNameList)


class getViewText(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        viewName = data['viewName']
        viewText = []
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            viewName = viewName.split('.')
            owner = viewName[0]
            vname = viewName[1]
            cursor.execute("SELECT sc.text AS viewtext FROM sysobjects so JOIN syscomments sc ON so.id = sc.id WHERE so.type = 'V' AND user_name(so.uid) = ? AND so.name = ?", (owner, vname,))
            table_fetch = cursor.fetchall()
            viewText.extend([row[0] for row in table_fetch])
            print(viewText)
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [viewText]


class getTableDetFromSchema(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            tableMetadataDict = []
            unSupportedTables = []
            for schema in schemaList:
                cursor.execute(
                    "SELECT user_name(uid) AS owner, name AS table_name FROM sysobjects WHERE type = 'U' AND user_name(uid) = ?", (schema,))
                table_fetch = cursor.fetchall()
                for row in table_fetch:
                    owner, table_name = row
                    unsupported = False
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {owner}.{table_name}")
                        row_count = cursor.fetchone()[0]
                    except Exception as e:
                        row_count = None
                        unsupported = True
                    cursor.execute(f"""
                                    SELECT '{table_name}' AS tname, c.name AS cname, t.name AS coltype, c.length AS width, c.prec AS syslength, 
                                    CASE WHEN c.status & 8 = 8 THEN 'NO' ELSE 'YES' END AS NN, 'UNKNOWN' AS in_primary_key, c.cdefault AS default_value, 
                                    '' AS remarks FROM syscolumns c JOIN systypes t ON c.usertype = t.usertype JOIN sysobjects o ON c.id = o.id 
                                    WHERE o.name = ? AND o.type = 'U' ORDER BY c.colid""", (table_name,))
                    tableMetadata_fetch = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]  # Get column names
                    table_data = [dict(zip(columns, row)) for row in tableMetadata_fetch]  # Zip column names with row values

                    if unsupported:
                        unSupportedTables.append(table_data)
                    else:
                        json_data = json.dumps(table_data)
                        tableMetadataDict.append(table_data)
            #print(tableMetadataDict)
        #           tableMetadata_fetch.to_csv(os.path.join(oneplace_home,'Table_Details.csv'),Index=False)
        except Exception as e:
            logger.info(str(e))
            print(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tableMetadataDict,unSupportedTables]


class getExtTrailName(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        Trail_Data = []
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write('info ' + extname + ' , showch' + '\n')
        infoExtTrail, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'infoextnametrail.out'), mode='w') as outfile:
            outfile.write(infoExtTrail)
        with  open(os.path.join(oneplace_home, 'infoextnametrail.out'), mode='r') as infile:
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                    Trail_Data.append(TrailName)
        OPlaceDebug(['infoextnametrail.out'])
        return [Trail_Data]


class addExtTrail(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        trailname = data['trailname']
        trailtype = data['trailtype']
        trailsize = data['trailsize']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write(
            'add ' + trailtype + ' ' + trailname + ', Extract ' + extname + ',megabytes ' + trailsize + '\n')
        delexttrail, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'addexttrail.out'), mode='w') as outfile:
            outfile.write(delexttrail)
        with  open(os.path.join(oneplace_home, 'addexttrail.out'), mode='r') as infile:
            AddExtErrPrint = []
            for line in infile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    AddExtErrPrint.append(line)
                elif 'file' in line:
                    line = line.split('>', 1)[-1]
                    AddExtErrPrint.append(line)
                elif 'Extract' in line:
                    line = line.split(':', 1)[-1].strip()
                    AddExtErrPrint.append(line)
        OPlaceDebug(['addexttrail.out'])
        return [AddExtErrPrint]


class ggGetAllTrails(Resource):
    def post(self):
        data = request.get_json(force=True)
        trailname = data['trailname']
        TrailName = []
        for name in trailname:
            if name.startswith('.') or name[0].isalnum():
                for name in glob.glob(os.path.join(gg_home, name + '*')):
                    size = os.stat(name).st_size
                    mtime = datetime.fromtimestamp(os.stat(name).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    TrailName.append({'file': name, 'size': size, 'mtime': mtime})
            else:
                for name in glob.glob(name + '*'):
                    size = os.stat(name).st_size
                    mtime = datetime.fromtimestamp(os.stat(name).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    TrailName.append({'file': name, 'size': size, 'mtime': mtime})

        return [TrailName]


class ggLogDumpCount(Resource):
    def post(self):
        data = request.get_json(force=True)
        trailfile = data['trailfile']
        Count_Detail_Ind = {}
        for trail in trailfile:
            ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write("count detail " + trail + "\n")
            TranNext, stderr = ssh.communicate(timeout=sshTimeOut)
            with  open(os.path.join(oneplace_home, 'Lodump_CountDetail.out'), mode='w') as outfile2:
                outfile2.write(TranNext)
            with  open(os.path.join(oneplace_home, 'Lodump_CountDetail.out'), mode='r') as infile:
                copy = False
                Count_Detail = []
                for line in infile:
                    line1 = line.split()
                    if len(line1) > 0:
                        if line1[0].startswith('Logdump'):
                            if line1[2].startswith('>'):
                                Count_Detail.append(line1[1])
            with  open(os.path.join(oneplace_home, 'Lodump_CountDetail.out'), mode='r') as infile, open(
                    os.path.join(oneplace_home, 'Lodump_CountDetail_Iter1.txt'), mode='w') as outfile:
                copy = False
                n = 0
                for line in infile:
                    if line.startswith('Logdump ' + str(Count_Detail[n])):
                        copy = True
                        continue
                        n = n + 1
                    elif line.startswith('Logdump ' + str(Count_Detail[n])):
                        copy = False
                        continue
                    elif copy:
                        outfile.write(line)

            with  open(os.path.join(oneplace_home, 'Lodump_CountDetail_Iter1.txt'), mode='r') as infile:
                copy = False
                for line in infile:
                    if 'Logdump' not in line:
                        if 'LogTrail' not in line:
                            if '*FileHeader*' not in line:
                                line1 = line.strip().split()
                                if len(line1) > 1:
                                    if line1[1] == 'Partition':
                                        tabname = line1[0]
                                        copy = True
                                        continue
                                    elif line1[1] == 'Partition':
                                        copy = False
                                        continue
                                    elif copy:
                                        if line1[0] == 'Before':
                                            pass
                                        elif line1[0] == 'RestartAbend':
                                            pass
                                        elif line1[0] == 'After':
                                            pass
                                        elif line1[0] == 'Metadata':
                                            pass
                                        elif line1[0] == 'Total':
                                            pass
                                        elif line1[0] == 'Avg':
                                            pass
                                        else:
                                            if tabname in Count_Detail_Ind.keys():
                                                Count_Detail_Ind[tabname] = int(Count_Detail_Ind[tabname]) + int(
                                                    line1[1])
                                            else:
                                                Count_Detail_Ind[tabname] = line1[1]
        OPlaceDebug(['Lodump_CountDetail.out', 'Lodump_CountDetail_Iter1.txt'])
        return [Count_Detail_Ind]


def hexConvert(filename):
    with open(os.path.join(oneplace_home, filename)) as infile:
        str = ''
        for line in infile:
            for word in line.split():
                str = str + word
    strAscii = binascii.unhexlify(str).decode('utf8')
    return strAscii


class ggLogDump(Resource):
    def post(self):
        data = request.get_json(force=True)
        trailfile = data['trailfile']
        trailfile = trailfile.lstrip('["').rstrip('"]')
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + "\n")
        ssh.stdin.write('fileheader detail' + "\n")
        ssh.stdin.write('n' + "\n")
        res, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'logdump.out'), mode='w') as outfile1:
            outfile1.write(res)
        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump2.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x30 '0' Sysname" in line:
                    copy = True
                    continue
                elif "TokenID x31 '1' Nodename" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)
        parse3 = hexConvert('ldump2.out')
        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump3.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x31 '1' Nodename" in line:
                    copy = True
                    continue
                elif "TokenID x32 '2' Release" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse4 = hexConvert('ldump3.out')
        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump4.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x32 '2' Release" in line:
                    copy = True
                    continue
                elif "TokenID x33 '3' Version" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse5 = hexConvert('ldump4.out')
        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump5.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x31 '1' Name" in line:
                    copy = True
                    continue
                elif "TokenID x32 '2' Instance" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)
        parse6 = hexConvert('ldump5.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump6.out'), mode='w', encoding='utf-8') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x36 '6' VerString" in line:
                    copy = True
                    continue
                elif "TokenID x37 '7' ClientCharset" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line.strip('00e5'))
        parse7 = hexConvert('ldump6.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump7.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x38 '8' ClientVerString" in line:
                    copy = True
                    continue
                elif "TokenID x39 '9' ClientNCharset" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse8 = hexConvert('ldump7.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump8.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x30 '0' Name" in line:
                    copy = True
                    continue
                elif "TokenID x31 '1' DataSource" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse9 = hexConvert('ldump8.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump9.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x37 '7' VerString" in line:
                    copy = True
                    continue
                elif "GroupID x34 '4' Continunity" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse10 = hexConvert('ldump9.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump10.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x3a ':' FirstCSN" in line:
                    copy = True
                    continue
                elif "TokenID x3b ';' LastCSN" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse11 = hexConvert('ldump10.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump11.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x3b ';' LastCSN" in line:
                    copy = True
                    continue
                elif "TokenID x3c '<' FirstIOTime" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse12 = hexConvert('ldump11.out')

        with  open(os.path.join(oneplace_home, 'logdump.out')) as infile, open(
                os.path.join(oneplace_home, 'ldump12.out'), mode='w') as outfile:
            copy = False
            for line in infile:
                line = line.split('|')[0]
                if "TokenID x3e '>' LOGBSN" in line:
                    copy = True
                    continue
                elif "TokenID x3f '?' BITFLAGS" in line:
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        parse13 = hexConvert('ldump12.out')

        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + "\n")
        ssh.stdin.write('count detail' + "\n")
        countRes, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'countdetail.out'), mode='w') as outfile2:
            outfile2.write(countRes)
        with  open(os.path.join(oneplace_home, 'countdetail.out')) as infile:
            copy = False
            Count_Detail = []
            for line in infile:
                line1 = line.split()
                if len(line1) > 0:
                    if line1[0].startswith('Logdump'):
                        if line1[2].startswith('>'):
                            Count_Detail.append(line1[1])

        with  open(os.path.join(oneplace_home, 'countdetail.out')) as infile, open(
                os.path.join(oneplace_home, 'countiter1.out'), mode='w') as outfile:
            copy = False
            n = 0
            for line in infile:
                if line.startswith('Logdump ' + str(Count_Detail[n])):
                    copy = True
                    continue
                    n = n + 1
                elif line.startswith('Logdump ' + str(Count_Detail[n])):
                    copy = False
                    continue
                elif copy:
                    outfile.write(line)

        with  open(os.path.join(oneplace_home, 'countiter1.out')) as infile:
            copy = False
            Count_Detail_Ind = []
            befImg = ''
            afterImg = ''
            graph = {}
            for line in infile:
                befImg = ''
                afterImg = ''
                if 'Logdump' not in line:
                    if '*FileHeader*' not in line:
                        line1 = line.strip().split()
                        if len(line1) > 1:
                            if line1[1] == 'Partition':
                                tabname = line1[0]
                                copy = True
                                continue
                            elif line1[1] == 'Partition':
                                copy = False
                                continue
                            elif copy:
                                if line1[0] == 'Before':
                                    befImg = line1[2]
                                elif line1[0] == 'After':
                                    afterImg = line1[2]
                                elif line1[0] == 'Metadata':
                                    metadata = line1[1]
                                elif line1[0] == 'Total':
                                    pass
                                elif line1[0] == 'Avg':
                                    pass
                                else:
                                    Count_Detail_Ind.append(
                                        {'tab_name': tabname, 'tran_type': line1[0], 'tran_det': line1[1]})
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=5)
        ssh.stdin.write('open ' + trailfile + "\n")
        ssh.stdin.write('n' + '\n')
        ssh.stdin.write('n' + '\n')
        trailData, stderr = ssh.communicate(timeout=sshTimeOut)
        with  open(os.path.join(oneplace_home, 'trandet.out'), mode='w') as outfile2:
            outfile2.write(trailData)
        with  open(os.path.join(oneplace_home, 'trandet.out')) as infile:
            copy = False
            parse16 = ''
            for line in infile:
                if 'RBA' in line:
                    parse16 = line.split()[6]
        OPlaceDebug(['ldump2.out', 'ldump3.out', 'ldump4.out', 'ldump5.out', 'ldump6.out', 'ldump7.out', 'ldump8.out',
                     'ldump9.out', 'ldump10.out', 'ldump11.out', 'ldump12.out', 'countdetail.out', 'countiter1.out',
                     'trandet.out'])
        return [parse3, parse4, parse5, parse6, parse7, parse8, parse9, parse10, parse11, parse12, parse13,
                Count_Detail_Ind, parse16]


class ggTranNext(Resource):
    def post(self):
        data = request.get_json(force=True)
        trailfile = data['trailfile']
        trailfile = trailfile.lstrip('["').rstrip('"]')
        rba = data['rba']
        filterlist = data['filterlist']
        filtmatch = data['filtmatch']
        TranNextRBA = ''
        FristTran = ''
        SecondTran = ''
        ssh = subprocess.Popen([logdump_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("open " + trailfile + '\n')
        ssh.stdin.write("ghdr on;detail data;usertoken detail;ggstoken detail;" + "\n")
        for filt in filterlist:
            ssh.stdin.write(filt + '\n')
        ssh.stdin.write(filtmatch + '\n')
        ssh.stdin.write("pos " + str(rba) + '\n')
        ssh.stdin.write('n' + '\n')
        ssh.stdin.write('n' + '\n')
        try:
            TranNext, stderr = ssh.communicate(timeout=sshTimeOut)
        except TimeoutExpired:
            ssh.kill()
        with  open(os.path.join(oneplace_home, 'trannext.out'), mode='w') as outfile:
            outfile.write(TranNext)
        with  open(os.path.join(oneplace_home, 'trannext.out')) as infile:
            copy = False
            i = 0
            FristTran = []
            SecondTran = []
            for line in infile:
                if '>______' in line:
                    i = i + 1
                    copy = True
                elif line.startswith('LogDump'):
                    copy = False
                    continue
                elif copy:
                    if 'Logdump' not in line and i == 1:
                        FristTran.append(line)
                    if 'Logdump' not in line and i == 2:
                        SecondTran.append(line)
                    if 'RBA' in line:
                        TranNextRBA = line.split()[-1]
        OPlaceDebug(['trannext.out'])
        return [TranNextRBA, FristTran, SecondTran]


class ggTranPrev(Resource):
    def post(self):
        data = request.get_json(force=True)
        trailfile = data['trailfile']
        trailfile = trailfile.lstrip('["').rstrip('"]')
        rba = data['rba']
        ssh = subprocess.Popen([logdump_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("open " + trailfile + '\n')
        ssh.stdin.write("ghdr on;detail data;usertoken detail;ggstoken detail;" + "\n")
        ssh.stdin.write("pos " + str(rba) + '\n')
        ssh.stdin.write("sfh prev" + '\n')
        ssh.stdin.write("sfh prev" + '\n')
        try:
            TranPrev, stderr = ssh.communicate(timeout=sshTimeOut)
        except TimeoutExpired:
            ssh.kill()
        with  open(os.path.join(oneplace_home, 'tranprev.out'), mode='w') as outfile:
            outfile.write(TranPrev)
        with  open(os.path.join(oneplace_home, 'tranprev.out')) as infile:
            copy = False
            i = 0
            FristTran = []
            SecondTran = []
            for line in infile:
                if '>______' in line:
                    i = i + 1
                    copy = True
                elif line.startswith('LogDump'):
                    copy = False
                    continue
                elif copy:
                    if 'Logdump' not in line and i == 1:
                        FristTran.append(line)
                    if 'Logdump' not in line and i == 2:
                        SecondTran.append(line)
                    if 'RBA' in line:
                        TranPrevRBA = line.split()[-1]
        OPlaceDebug(['tranprev.out'])
        return [TranPrevRBA, FristTran, SecondTran]


class rhpAddRep(Resource):
    def post(self):
        file = request.files['file']
        filename = secure_filename(file.filename)
        target = os.path.join(gg_home, 'dirprm', filename)
        if not os.path.exists(target):
            file.save(target)
            msg = 'Saved'
        else:
            msg = 'File Already Exists'
        return [msg]


class rhpWallet(Resource):
    def post(self):
        file = request.files['file']
        try:
            filename = secure_filename(file.filename)
            target = os.path.join(gg_home, 'dirwlt', filename)
            if not os.path.exists(target):
                file.save(target)
                msg = 'Wallet Saved'
            else:
                file.save(target)
                msg = 'Wallet Replaced'
        except OSError as e:
            msg = 'File not saved due to' + str(e)
        return [msg]


class downloadSoft(Resource):
    def post(self):
        data = request.get_json(force=True)
        softVer = data['softVer']
        dbVer = data['dbVer']
        BUCKET_NAME = 'ggsoft'
        if softVer.startswith('21'):
            KEY = softVer + '.zip'
        else:
            if dbVer.startswith('21'):
                KEY = softVer + '.zip'
            elif dbVer.startswith('19'):
                KEY = softVer + '_' + '19c.zip'
            elif dbVer.startswith('18'):
                KEY = softVer + '_' + '18c.zip'
            elif dbVer.startswith('12'):
                KEY = softVer + '_' + '12c.zip'
            elif dbVer.startswith('11'):
                KEY = softVer + '_' + '11g.zip'
        
        s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        RunIns = []
        path_to_zip_file = os.path.join(image_uploads, KEY)
        try:
            s3.Bucket(BUCKET_NAME).download_file(KEY, path_to_zip_file)
            with zipfile.ZipFile(path_to_zip_file, 'r') as zf:
                for info in zf.infolist():
                    extract_file(zf, info, gg_home)
                RunIns.append('Oracle Goldengate ' + KEY + ' Installed Successfully')
            if OSPlat == 'Linux' or OSPlat == 'AIX':
                if os.path.exists('/etc/oraInst.loc'):
                    with open('/etc/oraInst.loc', 'r') as infile:
                        for line in infile:
                            if line.startswith('inventory_loc='):
                                inv_loc = line.split('=', 1)[-1]
                            elif line.startswith('inst_group='):
                                inv_grp = line.split('=', 1)[-1]
                else:
                    with open(os.path.join(oneplace_base, 'oraInst.loc'), 'w') as outfile:
                        inv_loc = os.path.join(oneplace_base, 'oraInventory')
                        outfile.write('inventory_loc=' + inv_loc + '\n')
                        gid = os.getgid()
                        inv_grp = grp.getgrgid(gid).gr_name
                        outfile.write('inst_group=' + inv_grp)
            runInstaller = os.path.join(gg_home, 'oui', 'bin', 'runInstaller')
            softVer = softVer.split('.')
            softVerHome = softVer[0] + softVer[1] + softVer[2]
            if os.path.exists('/var/opt/oracle/oraInst.loc') or os.path.exists('/etc/oraInst.loc'):
                ssh = subprocess.Popen([runInstaller, '-silent', '-attachhome', 'ORACLE_HOME=' + gg_home,
                                        'ORACLE_HOME_NAME=' + 'GG' + softVerHome + 'Home1'], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                                       bufsize=0)
            else:
                ssh = subprocess.Popen([runInstaller, '-silent', '-attachHome', 'ORACLE_HOME=' + gg_home,
                                        'ORACLE_HOME_NAME=' + 'GG' + softVerHome + 'Home1', '-invPtrLoc',
                                        os.path.join(oneplace_base, 'oraInst.loc')], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                                       bufsize=0)
            InstallErr, stderr = ssh.communicate()
            RunIns.append(InstallErr)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                RunIns.append("The object does not exist.")
            else:
                RunIns.append(str(e))
        except OSError as e:
            RunIns.append(str(e))
        return [RunIns]


class rhpUploadImage(Resource):
    def post(self):
        file = request.files['file']
        filename = secure_filename(file.filename)
        path_to_zip_file = os.path.join(image_uploads, filename)
        SoftFile = []
        try:
            if filename.startswith('p'):
                patchFileSplit = filename.split('_')
                patchNumber = patchFileSplit[0].strip('p')
                patchVersion = patchFileSplit[1]
                patchPlatform = patchFileSplit[2].strip('.zip').split('-')
                patchPlatform = patchPlatform[0]
                if patchPlatform == OSPlat:
                    file.save(os.path.join(image_uploads, filename))
                    SoftFile.append(filename + ' Uploaded Sucessfully\n')
                else:
                    SoftFile.append('File uploaded is not suitable for this Operating System\n')
            elif 'fbo' in filename:
                ggFileSplit = filename.split('_')
                ggBaseVer = ggFileSplit[0]
                ggPlatform = ggFileSplit[3]
                ggBit = ggFileSplit[4]
                if ggPlatform == OSPlat:
                    file.save(os.path.join(image_uploads, filename))
                    SoftFile.append(filename + ' Uploaded Sucessfully\n')
                else:
                    SoftFile.append('File uploaded is not suitable for this Platform\n')
            elif filename.startswith('V'):
                file.save(os.path.join(image_uploads, filename))
                SoftFile.append(filename + ' Uploaded Sucessfully\n')
            with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                zip_ref.extractall(processing_dir)
            for fn in os.listdir(processing_dir):
                if 'fbo' in fn:
                    fbo_Dir = fn
            ggFileSplit = fbo_Dir.split('_')
            ggPlatform = ggFileSplit[2]
            ggBit = ggFileSplit[3]
            if ggPlatform != OSPlat:
                shutil.rmtree(processing_dir)
                SoftFile.append('File uploaded is not suitable for this Platform\n')
        except OSError as e:
            SoftFile.append(str(e))
        return [SoftFile]


class listSoftFiles(Resource):
    def get(self):
        softFiles = []
        for filename in os.listdir(image_uploads):
            if filename.startswith('p') and filename.endswith(".zip"):
                softFiles.append({'filename': filename, 'filetype': 'patch'})
            elif 'fbo' in filename and filename.endswith(".zip"):
                softFiles.append({'filename': filename, 'filetype': 'software'})
            elif filename.startswith('V') and filename.endswith(".zip"):
                softFiles.append({'filename': filename, 'filetype': 'software'})

        return [softFiles]


class ViewRunInsFile(Resource):
    def post(self):
        data = request.get_json(force=True)
        filename = data['filename']
        filename = filename.lstrip('"[').rstrip(']"')
        path_to_zip_file = os.path.join(image_uploads, filename)
        RunIns = []
        if not os.path.exists(gg_home): os.makedirs(gg_home)
        if 'fbo' in filename or filename.startswith('V'):
            if 'fbo' in filename:
                ggFileSplit = filename.split('_')
                ggBaseVer = ggFileSplit[0]
                ggPlatform = ggFileSplit[3]
                ggBit = ggFileSplit[4]
                ggVendor = ggFileSplit[5]
                shutil.rmtree(processing_dir)
                RunIns.append(filename + ' Processing ...')
                directory_to_extract_to = os.path.join(processing_dir, ggBaseVer, ggPlatform, ggBit)
                if not os.path.exists(directory_to_extract_to): os.makedirs(directory_to_extract_to)
                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    zip_ref.extractall(directory_to_extract_to)
                RunIns.append(filename + ' Processed Sucessfully')
                if ggVendor == 'Oracle':
                    fbo_Dir = 'fbo_ggs_' + ggPlatform + '_' + ggBit + '_Oracle_shiphome'
                else:
                    fbo_Dir = 'fbo_ggs_' + ggPlatform + '_' + ggBit + '_shiphome'
                runIns_Dir = os.path.join(directory_to_extract_to, fbo_Dir, 'Disk1')
                RunIns.append('Starting runInstaller on node ' + hName + ' to install Goldengate')
            elif filename.startswith('V'):
                shutil.rmtree(processing_dir)
                RunIns.append(filename + ' Processing ...')
                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    zip_ref.extractall(processing_dir)
                for filename in os.listdir(processing_dir):
                    if 'fbo' in filename:
                        fbo_Dir = filename
                    elif 'WinUnix' in filename and filename.endswith('.pdf'):
                        BaseVer = filename.split('_')
                        UpdBaseVer = BaseVer[4].strip('.pdf').replace('.', '')
                ggFileSplit = fbo_Dir.split('_')
                ggBaseVer = UpdBaseVer
                ggPlatform = ggFileSplit[2]
                ggBit = ggFileSplit[3]
                runIns_Dir = os.path.join(processing_dir, fbo_Dir, 'Disk1')
                RunIns.append('Starting runInstaller on node ' + hName + ' to install Goldengate')
            chmod_dir(runIns_Dir)
            ora_Options = []
            if ggPlatform == 'Linux' or ggPlatform == 'AIX':
                if os.path.exists('/etc/oraInst.loc'):
                    with open('/etc/oraInst.loc', 'r') as infile:
                        for line in infile:
                            if line.startswith('inventory_loc='):
                                inv_loc = line.split('=', 1)[-1]
                            elif line.startswith('inst_group='):
                                inv_grp = line.split('=', 1)[-1]
                else:
                    with open(os.path.join(oneplace_base, 'oraInst.loc'), 'w') as outfile:
                        inv_loc = os.path.join(oneplace_base, 'oraInventory')
                        if not os.path.exists(os.path.join(oneplace_base, 'oraInventory')): os.makedirs(
                            os.path.join(oneplace_base, 'oraInventory'))
                        outfile.write('inventory_loc=' + inv_loc + '\n')
                        gid = os.getgid()
                        inv_grp = grp.getgrgid(gid).gr_name
                        outfile.write('inst_group=' + inv_grp + '\n')
            elif ggPlatform == 'Solaris':
                if os.path.exists('/var/opt/oracle/oraInst.loc'):
                    with open('/var/opt/oracle/oraInst.loc') as infile:
                        for line in infile:
                            if line.startswith('inventory_loc='):
                                inv_loc = line.split('=', 1)[-1]
                            elif line.startswith('inst_group='):
                                inv_grp = line.split('=', 1)[-1]
                else:
                    with open(os.path.join(oneplace_base, 'oraInst.loc'), 'w') as infile:
                        inv_loc = os.path.join(oneplace_base, 'oraInventory')
                        outfile.write('inventory_loc=' + inv_loc + '\n')
                        gid = os.getgid()
                        inv_grp = grp.getgrgid(gid).gr_name
                        outfile.write('inst_group=' + inv_grp)
            if ggBaseVer.startswith('21'):
                ORA_Version = 'ora21c'
            else:
                db_clientVer = cx_Oracle.clientversion()
                main_ClientVer = db_clientVer[0]
                if main_ClientVer > 11:
                    ORA_Version = 'ORA' + str(main_ClientVer) + 'c'
                else:
                    ORA_Version = 'ORA' + str(main_ClientVer) + 'g'
            install_dir = os.path.join(runIns_Dir, 'install')
            oraparam_ini = os.path.join(install_dir, 'oraparam.ini')
            dest_file = 'oraparam.ini.orig'
            shutil.copy(oraparam_ini, dest_file)
            with open(dest_file, 'r') as infile:
                oraini_file = infile.read()
                oraini_file = oraini_file.replace('DEFAULT_HOME_NAME=OraHome',
                                                  'DEFAULT_HOME_NAME=' + 'OGG_' + ggBaseVer + '_' + ORA_Version + '_Home')
            RunIns.append('Goldengate Home is set to - OGG_' + ggBaseVer + '_' + ORA_Version + '_Home')
            with open(oraparam_ini, 'w') as infile:
                infile.write(oraini_file)
            response_File_Dir = os.path.join(runIns_Dir, 'response')
            response_File = os.path.join(response_File_Dir, 'oggcore.rsp')
            oneplace_RspFile = os.path.join(response_File_Dir, 'oggcore_oneplace.rsp')
            with open(response_File, 'r') as infile:
                readResponse = infile.readlines()
            with open(oneplace_RspFile, 'w') as infile:
                for line in readResponse:
                    if 'INSTALL_OPTION' in line:
                        infile.writelines('INSTALL_OPTION=' + ORA_Version)
                    elif line.startswith('SOFTWARE_LOCATION'):
                        infile.writelines('SOFTWARE_LOCATION=' + gg_home)
                    elif 'DATABASE_LOCATION' in line:
                        infile.writelines('DATABASE_LOCATION=' + db_home)
                    elif 'INVENTORY_LOCATION' in line:
                        infile.writelines('INVENTORY_LOCATION=' + inv_loc)
                    elif 'UNIX_GROUP_NAME' in line:
                        infile.writelines('UNIX_GROUP_NAME=' + inv_grp)
                    else:
                        infile.writelines(line)
            runInstaller = os.path.join(runIns_Dir, 'runInstaller')
            if os.path.exists('/var/opt/oracle/oraInst.loc') or os.path.exists('/etc/oraInst.loc'):
                ssh = subprocess.Popen([runInstaller, '-silent', '-showProgress', '-responseFile', oneplace_RspFile],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       universal_newlines=True, bufsize=0)
            else:
                ssh = subprocess.Popen(
                    [runInstaller, '-silent', '-showProgress', '-responseFile', oneplace_RspFile, '-invPtrLoc',
                     os.path.join(oneplace_base, 'oraInst.loc')], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            InstallErr, stderr = ssh.communicate()
            RunIns.append(InstallErr)
            shutil.copy(dest_file, oraparam_ini)
            if rac_check == 'Y':
                for name in copy_to_nodes:
                    RunIns.append('Connecting to ' + name + ' in order to setup software...')
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=name)
                    scp = SCPClient(ssh_client.get_transport())
                    rmdir_OH = 'rmdir ' + gg_home
                    stdin, stdout, stderr = ssh_client.exec_command(rmdir_OH)
                    RunIns.append('Copying files to remote node ' + name + ' ...')
                    scp.put(gg_home, recursive=True, remote_path=gg_home)
                    RunIns.append('Copy to remote node ' + name + ' completed ...')
                    runins_home = os.path.join(gg_home, 'oui', 'bin', 'runInstaller')
                    RunIns.append('Starting to attach Goldengate Home on  remote node ' + name + ' ...')
                    add_OH = runins_home + ' -silent -attachHome ORACLE_HOME=' + gg_home + ' ORACLE_HOME_NAME=' + 'OGG_' + ggBaseVer + '_' + ORA_Version + '_Home'
                    stdin, stdout, stderr = ssh_client.exec_command(add_OH)
                    RunIns.append(stdout.readlines())
                    RunIns.append('Setting up software on remote node ' + name + ' completed ...')
                    ssh_client.get_transport().close()
                    ssh_client.close()
                    RunIns.append('Software Setup is completed')
        elif filename.startswith('p'):
            patchFileSplit = filename.split('_')
            patchNumber = patchFileSplit[0].strip('p')
            patchVersion = patchFileSplit[1]
            patchPlatform = patchFileSplit[2].strip('.zip')
            path_to_zip_file = os.path.join(image_uploads, filename)
            opatch_dir = os.path.join(gg_home, 'OPatch', 'opatch')
            if patchNumber == '6880880':
                subprocess.run(["unzip", path_to_zip_file, "-d", gg_home])
                RunIns.append(filename + ' Processed Sucessfully\n\n')
                ssh = subprocess.Popen([opatch_dir, 'version'],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       universal_newlines=True, bufsize=0)

                opatchVersion, stderr = ssh.communicate()
                RunIns.append(opatchVersion)
                RunIns.append(stderr)
            else:

                directory_to_extract_to = os.path.join(processing_dir, patchNumber, patchVersion, patchPlatform)
                if not os.path.exists(directory_to_extract_to): os.makedirs(directory_to_extract_to)
                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    zip_ref.extractall(directory_to_extract_to)
                RunIns.append(filename + ' Processed Sucessfully')
                patch_directory = os.path.join(processing_dir, patchNumber, patchVersion, patchPlatform, patchNumber)
                chmod_dir(patch_directory)
                RunIns.append('Patching local node ' + hName)
                os.environ['ORACLE_HOME'] = gg_home
                if os.path.exists('/var/opt/oracle/oraInst.loc') or os.path.exists('/etc/oraInst.loc'):
                    ssh = subprocess.Popen([opatch_dir, 'apply', patch_directory, '-silent'],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           universal_newlines=True, bufsize=0)
                else:
                    ssh = subprocess.Popen([opatch_dir, 'apply', patch_directory, '-silent', '-invPtrLoc',
                                            os.path.join(oneplace_base, 'oraInst.loc')],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           universal_newlines=True, bufsize=0)
                InstallErr, stderr = ssh.communicate()
                RunIns.append(InstallErr)
                lsinv = subprocess.getoutput(opatch_dir + ' lsinventory -oh ' + gg_home + '\n')
                RunIns.append(lsinv)
                if rac_check == 'Y':
                    for name in copy_to_nodes:
                        RunIns.append('Connecting to ' + name + ' in order to patch Goldengate Home...')
                        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh_client.connect(hostname=name)
                        scp = SCPClient(ssh_client.get_transport())
                        RunIns.append('Patching remote node ' + name)
                        patch_directory = os.path.join(processing_dir, patchNumber, patchVersion, patchPlatform,
                                                       patchNumber)
                        opatch_dir = os.path.join(gg_home, 'OPatch', 'opatch')
                        if os.path.exists('/var/opt/oracle/oraInst.loc') or os.path.exists('/etc/oraInst.loc'):
                            patch_remote = 'export ORACLE_HOME=' + gg_home + '\n' + opatch_dir + ' apply ' + patch_directory + ' -silent' + '\n' + opatch_dir + ' lsinventory -oh ' + gg_home + '\n'
                        else:
                            patch_remote = 'export ORACLE_HOME=' + gg_home + '\n' + opatch_dir + ' apply ' + patch_directory + ' -silent -invPtrLoc ' + os.path.join(
                                oneplace_base, 'oraInst.loc') + '\n' + opatch_dir + ' lsinventory -oh ' + gg_home + '\n'
                        stdin, stdout, stderr = ssh_client.exec_command(patch_remote)
                        RunIns.append(stdout.readlines())
                        RunIns.append('Patching on remote node ' + name + ' completed ...')

        return [RunIns]


class ggCreateGoldImg(Resource):
    def get(self):
        abs_gghome = os.path.abspath(gg_home)
        LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
        logging.basicConfig(filename=oneplace_home + '/createGoldImg.log', level=logging.DEBUG, format=LOG_FORMAT)
        logger = logging.getLogger()
        logger.info('Creating  Gold Image from Goldengate Home - %s', gg_home)
        Gold_Img = os.path.join(processing_dir, 'GoldImage_' + hName + '.zip')
        abs_gghome = os.path.abspath(gg_home)
        with zipfile.ZipFile(Gold_Img, 'w', compression=zipfile.ZIP_LZMA) as zipf:
            for dirs, subdirs, files in os.walk(gg_home):
                subdirs[:] = [d for d in subdirs if 'dirdat' not in d if 'dirprm' not in d if 'dircrd' not in d if
                              'dirrpt' not in d if 'dirpcs' not in d if 'dirchk' not in d if 'dirdmp' not in d if
                              'dirtmp' not in d if 'BR' not in d]
                for file in files:
                    if 'gglog-' not in file and not file.endswith('.log'):
                        logger.info(file)
                        absname = os.path.abspath(os.path.join(dirs, file))
                        arcname = absname[len(abs_gghome) + 1:]
                        zipf.write(absname, arcname)
        logger.info('Gold Image from Goldengate Home - %s Completed', gg_home)
        logger.info('Validating Gold Image created from Goldengate Home - %s', gg_home)
        logger.info('Uploading Gold Image to central repository ')
        GGVer = subprocess.getoutput(ggsci_bin + ' -v')
        line = GGVer.splitlines()
        GGVer = line[2].split()[1]
        DBVer = line[3].split()
        GGDBVer = DBVer[DBVer.index('Oracle') + 1]
        GGDBVer = 'Oracle ' + GGDBVer
        response = make_response(send_file(Gold_Img, as_attachment=True))
        response.headers['GGVer'] = GGVer
        response.headers['GGDBVer'] = GGDBVer
        return response


class ggInfoDiagram(Resource):
    def get(self):
        ExtTrailSetTmp = {}
        ExtTrailSet = {}
        PmpTrailSet = {}
        PmpRmtTrailSet = {}
        RepTrailSet = {}
        InfoExt = subprocess.getoutput("echo -e 'info exttrail'|" + ggsci_bin)
        InfoPmp = subprocess.getoutput("echo -e 'info extract *'|" + ggsci_bin)
        with  open(os.path.join(oneplace_home, 'infoext.out'), mode='w') as outfile:
            outfile.write(InfoExt)
        with  open(os.path.join(oneplace_home, 'infopmp.out'), mode='w') as outfile:
            outfile.write(InfoPmp)
        with  open(os.path.join(oneplace_home, 'infopmp.out')) as infile:
            for line in infile:
                if 'EXTRACT' in line:
                    PmpName = line.split()[1]
                elif 'Redo' in line:
                    PmpName = ''
                elif 'File' in line:
                    TrailName = line.split('File', 1)[-1].strip()
                    TrailPath = TrailName.split('/')[:-1]
                    TrailName = TrailName.split('/')[-1]
                    TrailName = TrailName[:2]
                    Trail = ''
                    for name in TrailPath:
                        Trail += name + '/'
                    Trail = Trail + TrailName
                    PmpTrailSet[PmpName] = Trail
        with  open(os.path.join(oneplace_home, 'infoext.out')) as infile:
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip()
                    ExtTrailSetTmp[ExtName] = TrailName
        for key, value in ExtTrailSetTmp.items():
            if key not in PmpTrailSet:
                ExtTrailSet[key] = value
            else:
                PmpRmtTrailSet[key] = value
        RepTrail_Data = []
        InfoRep = subprocess.getoutput("echo -e 'info replicat * , showch'|" + ggsci_bin)
        with  open(os.path.join(oneplace_home, 'inforep.out'), mode='w') as outfile:
            outfile.write(InfoRep)
        with  open(os.path.join(oneplace_home, 'inforep.out')) as infile:
            for line in infile:
                if 'REPLICAT' in line:
                    RepName = line.split()[1]
                elif 'Extract Trail' in line:
                    RepTrailSet[RepName] = line.split(':', 1)[-1].strip()
        ExtProcessSet = {'uid': 'Extracts', 'nodeext': ExtTrailSet}
        PmpProcessSet = {'pid': 'Pump', 'nodepmp': PmpTrailSet}
        RepProcessSet = {'id': 'Replicats', 'noderep': RepTrailSet}
        ProcessSet1 = dict(ExtProcessSet, **PmpProcessSet)
        ProcessSet2 = dict(ProcessSet1, **RepProcessSet)
        Ext_df = pd.DataFrame(list(ExtTrailSet.items()), columns=['id', 'category'])
        Pmp_df = pd.DataFrame(list(PmpTrailSet.items()), columns=['id', 'category'])
        PmpRmt_df = pd.DataFrame(list(PmpRmtTrailSet.items()), columns=['id', 'category'])
        Rep_df = pd.DataFrame(list(RepTrailSet.items()), columns=['id', 'category'])
        TrailCommon1 = pd.merge(Ext_df, Pmp_df, on=['category'], how='inner')
        TrailCommon1['id'] = np.arange(TrailCommon1.shape[0])
        TrailCommon1.columns = ['start', 'category', 'end', 'id']
        TrailCommon2 = pd.merge(Ext_df, Rep_df, on=['category'], how='inner')
        TrailCommon2['id'] = np.arange(TrailCommon2.shape[0])
        TrailCommon3 = pd.merge(PmpRmt_df, Rep_df, on=['category'], how='inner')
        TrailCommon3['id'] = np.arange(TrailCommon3.shape[0])
        TrailCommon = np.concatenate((TrailCommon3, TrailCommon2, TrailCommon1), axis=0)
        column_names = ['start', 'category', 'end', 'id']
        df = pd.DataFrame(data=TrailCommon, columns=column_names)
        return [ProcessSet2, df.to_dict('records')]


class ggMonitorall(Resource):
    def get(self):
        val = infoall()
        return [val[0]]


class ggInfoall(Resource):
    def get(self):
        processCheckDemand()
        val = infoall()
        return [val[0], trailPath]


class ggInfoExt(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        InfoExt = subprocess.getoutput("echo -e 'info extract '" + extname + ",tasks|" + ggsci_bin)
        with  open(oneplace_home + "/infoext.out", mode='w') as outfile2:
            outfile2.write(InfoExt)
        with  open(oneplace_home + "/infoext.out", mode='r') as infile:
            Ext_Data = []
            for line in infile:
                if re.match("EXTRACT", line, re.IGNORECASE):
                    line = line.split()
                    Ext_Data.append({'extname': line[1], 'extstat': line[-1]})
        return [Ext_Data]


class ggInfoRep(Resource):
    def post(self):
        data = request.get_json(force=True)
        repname = data['repname']
        InfoRep = subprocess.getoutput("echo -e 'info replicat '" + repname + "|" + ggsci_bin)
        with  open(oneplace_home + "/inforep.out", mode='w') as outfile2:
            outfile2.write(InfoRep)
        with  open(oneplace_home + "/inforep.out", mode='r') as infile:
            Rep_Data = []
            for line in infile:
                if re.match("REPLICAT", line, re.IGNORECASE):
                    line = line.split()
                    Rep_Data.append({'repname': line[1], 'repstat': line[-1]})
        return [Rep_Data]


class ggAddCredStore(Resource):
    def get(self):
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("create subdirs" + "\n")
        ssh.stdin.write("add credentialstore" + "\n")
        CredStore_Out = []
        CredErr, stderr = ssh.communicate()
        CredStore_Out.append(CredErr)
        if os.path.exists('/home/oracle/1pmgr.prm'):
            shutil.copy('/home/oracle/1pmgr.prm', os.path.join(gg_home, 'dirprm', 'mgr.prm'))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            ssh.stdin.write("start mgr" + "\n")
            CredErr, stderr = ssh.communicate()
            CredStore_Out.append(CredErr)
        ssh.kill()
        ssh.stdin.close()
        with open(os.path.join(oneplace_home, 'CredStore_Out.lst'), 'w') as TestDBLoginFileIn:
            for listline in CredStore_Out:
                TestDBLoginFileIn.write(listline)
        with open(os.path.join(oneplace_home, 'CredStore_Out.lst'), 'r') as TestDBLoginFile:
            CredErrPrint = []
            for line in TestDBLoginFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
                elif 'Created' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
                elif 'Opened' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
                elif 'Credential' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
                elif 'subdirectories' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
                elif 'master' in line:
                    line = line.split('>', 1)[-1]
                    CredErrPrint.append(line)
        return [CredErrPrint]


class ggMasterKey(Resource):
    def get(self):
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("open wallet" + "\n")
        ssh.stdin.write("info masterkey" + "\n")
        Wallet_Out = []
        WalletErr, stderr = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with  open(os.path.join(oneplace_home, "infomasterkey.out"), mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with  open(os.path.join(oneplace_home, "infomasterkey.out")) as infile:
            MasterKey = {}
            for line in infile:
                if 'Name' in line or 'name' in line:
                    KeyName = line.split(':')[1].strip()
                elif re.match(r"^\d+.*$", line):
                    line1 = line.split()
                    MasterKey.setdefault(KeyName, []).append(
                        {'Version': line1[0], 'Created': line1[1], 'Status': line1[2]})
        return [MasterKey]

    def post(self):
        data = request.get_json(force=True)
        menuAction = data['menuAction']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        if os.path.exists(os.path.join(gg_home, 'dirwlt')):
            shutil.rmtree(os.path.join(gg_home, 'dirwlt'))
            os.makedirs(os.path.join(gg_home, 'dirwlt'))
        ssh.stdin.write("create wallet" + "\n")
        ssh.stdin.write("open wallet" + "\n")
        ssh.stdin.write("add masterkey" + "\n")
        Wallet_Out = []
        WalletErr, stderr = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with  open(oneplace_home + "/createmasterkey.out", mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with  open(oneplace_home + "/createmasterkey.out", mode='r') as infile:
            WalletErrPrint = []
            for line in infile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    WalletErrPrint.append(line)
                elif 'Created' in line:
                    line = line.split('>', 1)[-1]
                    WalletErrPrint.append(line)
                elif 'Opened' in line:
                    line = line.split('>', 1)[-1]
                    WalletErrPrint.append(line)
                elif 'master' in line:
                    line = line.split('>', 1)[-1]
                    WalletErrPrint.append(line)
                elif 'Wallet' in line:
                    line = line.split('>', 1)[-1]
                    WalletErrPrint.append(line)

        return [WalletErrPrint]


class ggMasterKeyAction(Resource):
    def post(self):
        data = request.get_json(force=True)
        menuAction = data['menuAction']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        Wallet_Out = []
        version = 0
        if menuAction == 'info':
            version = data['version']
            ssh.stdin.write("open wallet" + "\n")
            ssh.stdin.write("info masterkey version " + version + "\n")
        elif menuAction == 'renew':
            ssh.stdin.write("open wallet" + "\n")
            ssh.stdin.write("renew masterkey" + "\n")
        elif menuAction == 'delete':
            version = data['version']
            ssh.stdin.write("open wallet" + "\n")
            ssh.stdin.write("delete masterkey version " + version + "\n")
        elif menuAction == 'purge':
            ssh.stdin.write("purge wallet" + "\n")
        elif menuAction == 'deploy':
            dep_url = data['dep_url']
            dep_url = dep_url + '/rhpwallet'
            walletfile = os.path.join(gg_home, 'dirwlt', 'cwallet.sso')
            with open(walletfile, 'rb') as payload:
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                files = {'file': payload}
                r = requests.post(dep_url, files=files, verify=False)
                WalletErr = r.json()[0]
                Wallet_Out.append(WalletErr)
        WalletErr, stderr = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with  open(os.path.join(oneplace_home, "ActionMasterkey.out"), mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with  open(os.path.join(oneplace_home, "ActionMasterkey.out"), mode='r') as infile:
            MasterKey = []
            for line in infile:
                if 'Name' in line or 'name' in line:
                    KeyName = line.split(':')[1].strip()
                elif line.startswith(str(version)):
                    line1 = line.split()
                    MasterKey.append({'KeyName': KeyName, 'Version': line1[0], 'Created': line1[1], 'Status': line1[2]})
                elif 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    MasterKey.append(line)
                elif 'Wallet' in line:
                    line = line.split('>', 1)[-1]
                    MasterKey.append(line)
        return [MasterKey]


class ggCredStoreCheck(Resource):
    def get(self):
        if os.path.exists(ggsci_bin):
            InfoCred = subprocess.getoutput("echo -e 'info credentialstore'|" + ggsci_bin)
            with  open(oneplace_home + "/checkcreddom.out", mode='w') as outfile:
                outfile.write(InfoCred)
            with  open(oneplace_home + "/checkcreddom.out", mode='r') as infile:
                CredExists = ''
                for line in infile:
                    if 'Unable' in line:
                        CredExists = 'N'
                        break
                    else:
                        CredExists = 'Y'
            return [CredExists]


class ggCredStore(Resource):
    def get(self):
        if os.path.exists(ggsci_bin):
            InfoCred = subprocess.getoutput("echo -e 'info credentialstore'|" + ggsci_bin)
            with  open(oneplace_home + "/creddomains.out", mode='w') as outfile:
                outfile.write(InfoCred)
            with  open(oneplace_home + "/creddomains.out", mode='r') as infile, open(oneplace_home + "/othdom.out",
                                                                                     mode='w') as outfile:
                copy = False
                for line in infile:
                    if line.strip() == "Other domains:":
                        copy = True
                        continue
                    elif re.match("To", line.strip()):
                        copy = False
                        continue
                    elif copy:
                        outfile.write(line.strip().lstrip().rstrip())
                outfile.write(',OracleGoldenGate')

            if os.path.exists(oneplace_home + "/othdomdet.out"):
                os.remove(oneplace_home + "/othdomdet.out")
            else:
                logger.info("The file does not exist")
            with  open(oneplace_home + "/othdom.out", mode='r') as infile:
                Oth_Dom = []
                for line in infile:
                    Oth_Name = line.split(',')
                    for oth in Oth_Name:
                        if len(oth) > 0:
                            InfoOthDom = subprocess.getoutput(
                                "echo -e 'info credentialstore domain '" + oth + "|" + ggsci_bin)
                            with  open(oneplace_home + "/othdomdet.out", mode='a') as outfile:
                                outfile.write(InfoOthDom)
                            Oth_Set = {'value': oth, 'label': oth}
                            Oth_Dom.append(Oth_Set)
            with  open(oneplace_home + "/othdomdet.out", mode='r') as infile:
                Dom_Det = []
                Dom_Set = []
                Alias_Set = []
                for line in infile:
                    if re.match("Domain:", line.lstrip()):
                        Dom, DomName = line.split()
                        Dom_Set.append(DomName)
                    elif re.match("Alias", line.lstrip()):
                        Alias, Name = line.split()
                        Alias_Set.append({'dom': DomName, 'alias': Name})
                    elif re.match("Userid", line.lstrip()):
                        Userid, UserName = line.split()
                        Dom_Det.append({'alias': Name, 'uname': UserName})
            r = {}
            for set in Alias_Set:
                r.setdefault(set['dom'], []).append(set['alias'])
            Final_Alias = []
            for key, value in r.items():
                Final_Alias.append(
                    {'label': key, 'value': key, 'children': [{'label': val, 'value': val} for val in value]})

            return [Dom_Det, Oth_Dom, Dom_Set, Alias_Set, Final_Alias]


class ggTestDBLogin(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        TestDBLogin_Out = []
        LoginErr, stderr = ssh.communicate()
        TestDBLogin_Out.append(LoginErr)
        ssh.kill()
        ssh.stdin.close()
        with open(oneplace_home + '/TestDBLogin.lst', 'w') as TestDBLoginFileIn:
            for listline in TestDBLogin_Out:
                TestDBLoginFileIn.write(listline)
        with open(oneplace_home + '/TestDBLogin.lst', 'r') as TestDBLoginFile:
            LoginErrPrint = []
            for line in TestDBLoginFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    LoginErrPrint.append(line)
                elif 'database' in line:
                    line = line.split('>', 1)[-1]
                    line = line.split('.', 1)[0]
                    line = line.strip()
                    LoginErrPrint.append(line)
                elif '@' in line:
                    line = line.split('as', 1)[-1]
                    line = line.split(')', 1)[0]
                    line = line.split('@')
                    user = line[0].strip()
                    instance = line[1].strip()
                    LoginErrPrint.append(user)
                    LoginErrPrint.append(instance)

        return [LoginErrPrint]


class ggAddUserAlias(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        user = data['user']
        passwd = data['passwd']
        addUsr = subprocess.getoutput(
            "echo -e 'alter credentialstore add user '" + user + " password " + passwd + " alias " + alias + " domain " + domain + " |" + ggsci_bin + "|grep -i credential")
        if '@' in user:
            user = user.split('@')
            uname = user[0]
            servicename = user[1]
        else:
            uname = user
            servicename = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            passwd = cipher.encrypt(passwd).decode('utf-8')
            cursor.execute('''insert or replace into CONN values(:dbname,:user,:passwd,:servicename)''',
                           {"dbname": alias, "user": uname, "passwd": passwd, "servicename": servicename})
        except sqlite3.Error as e:
            clientType.append(e)
        finally:
            conn.commit()
            cursor.close()
            conn.close()

        return [addUsr]


class ggEditUserAlias(Resource):
    def post(self):
        data = request.get_json(force=True)
        alias = data['alias']
        user = data['user']
        passwd = data['passwd']
        domain = data['domain']
        editUsr = subprocess.getoutput(
            "echo -e 'alter credentialstore replace user '" + user + " password " + passwd + " alias " + alias + " domain " + domain + " |" + ggsci_bin + "|grep -i credential")
        if '@' in user:
            user = user.split('@')
            uname = user[0]
            servicename = user[1]
        else:
            uname = user
            servicename = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            passwd = cipher.encrypt(passwd).decode('utf-8')
            cursor.execute(
                '''INSERT OR REPLACE INTO CONN(dbname,user,passwd,servicename)  values(:dbname,:user,:passwd,:servicename)''',
                {"dbname": alias, "user": uname, "passwd": passwd, "servicename": servicename})
        except sqlite3.Error as e:
            editUsr = str(e)
        finally:
            conn.commit()
            cursor.close()
            conn.close()
        return [editUsr]


class ggDelUserAlias(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        user = data['user']
        delUsr = subprocess.getoutput(
            "echo -e 'alter credentialstore delete user '" + user + " alias " + alias + " domain " + domain + " |" + ggsci_bin + "|grep -i credential")
        if '@' in user:
            user = user.split('@')
            user = user[0]
            servicename = user[1]
        else:
            user = user
            servicename = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('''delete from CONN where dbname=:dbname''', {'dbname': alias})
        except sqlite3.Error as e:
            delUsr = str(e)
        finally:
            conn.commit()
            cursor.close()
            conn.close()
        return [delUsr]


class ggErrLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        lineNum = data['lineNum']
        chunkSize = int(lineNum) + 1024
        with  FileReadBackwards(gg_home + "/ggserr.log", encoding="utf-8") as infile:
            All_Data = []
            copy = False
            for _ in zip(range(lineNum), infile): pass
            for index, line in enumerate(infile, start=lineNum):
                if index == lineNum:
                    copy = True
                    continue
                elif index == chunkSize:
                    copy = False
                    continue
                elif copy:
                    AllVal = line.split(sep=None, maxsplit=3)
                    AllName_Set = {'AllVal': AllVal}
                    All_Data.append(AllName_Set)
                elif None:
                    lineNum = "No More Rows To Load"
            return [All_Data, chunkSize]


class writeTmpPrm(Resource):
    def post(self):
        data = request.get_json(force=True)
        currentExtParamList = data['currentExtParamList']
        with  open(oneplace_home + "/tmpPrm", 'w') as infile:
            infile.write(currentExtParamList)
        with  open(oneplace_home + "/tmpPrm", 'r') as outfile:
            prmFile = outfile.read()
        return [prmFile]


class writeMgrPrm(Resource):
    def post(self):
        data = request.get_json(force=True)
        Params = data['currentMgrParams']
        try:
            with  open(os.path.join(gg_home, 'dirprm', 'mgr.prm'), 'w') as infile:
                infile.write(Params)
                msg = 'Saved Manager Parameterfile'
        except OSError as e:
            msg = 'There is a problem in saving Parameterfile due to : ' + e
        return [msg]


class savePrm(Resource):
    def post(self):
        data = request.get_json(force=True)
        procName = data['procName']
        currentParams = data['currentParams']
        try:
            with  open(os.path.join(gg_home, 'dirprm', procName + '.prm'), 'w') as infile:
                infile.write(currentParams)
                msg = 'Saved ' + procName + ' Parameterfile'
        except OSError as e:
            msg = 'There is a problem in saving Parameterfile due to : ' + e
        return [msg]


class readMgrPrm(Resource):
    def get(self):
        try:
            with  open(os.path.join(gg_home, 'dirprm', 'mgr.prm'), 'r') as infile:
                mgrPrmFile = infile.read()
        except OSError as e:
            mgrPrmFile = 'Please setup the parameterfile here'

        return [mgrPrmFile]


class AddInitialLoadExt(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        extname = data['extname']
        currentExtParamList = data['currentExtParamList']
        startExtChk = data['startExtChk']
        ExtErrPrint = []
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("add extract " + extname + ',' + 'SOURCEISTABLE' + "\n")
        AddExt_Out = []
        extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
        if not os.path.exists(os.path.join(trailPath, jobName)): os.makedirs(os.path.join(trailPath, jobName))
        with open(extPrm, 'w') as extFile:
            extFile.write(currentExtParamList)
        if startExtChk is False:
            ssh.stdin.write("start extract " + extname + "\n")
        AddExtErr, stderr = ssh.communicate()
        AddExt_Out.append(AddExtErr)
        with open(oneplace_home + '/AddInitialExtErr.lst', 'w') as extErrFileIn:
            for listline in AddExt_Out:
                extErrFileIn.write(listline)
        with open(oneplace_home + '/AddInitialExtErr.lst', 'r') as extErrFile:
            ExtErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif 'added.' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)

        return [ExtErrPrint]


class insertSQLite3DB(Resource):
    def post(self):
        srcdep = data['srcdep']
        srcalias = data['srcalias']
        tgtdep = data['tgtdep']
        tgtalias = data['tgtalias']
        jobName = data['jobName']
        s3bucket = data['s3bucket']
        aws_access_key_id = data['aws_access_key_id']
        aws_secret_access_key = data['aws_secret_access_key']
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute(
                'insert into ILCSV values(:jobname,:srcalias,:srcdep,:tgtdep ,:tgtalias ,:s3bucket,:aws_access_key_id,:aws_secret_access_key)',
                {'jobname': jobName, 'srcdep': srcdep, 'srcalias': srcalias, "tgtdep": tgtdep, "tgtalias": tgtalias,
                 "s3bucket": s3bucket, "aws_access_key_id": aws_access_key_id,
                 "aws_secret_access_key": aws_secret_access_key})
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.info(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()


class AddCSVILProc(Resource):
    def post(self):
        data = request.get_json(force=True)
        srcdep = data['srcdep']
        srcalias = data['srcalias']
        tgtdep = data['tgtdep']
        tgtalias = data['tgtalias']
        jobName = data['jobName']
        s3bucket = data['s3bucket']
        aws_access_key_id = data['aws_access_key_id']
        aws_secret_access_key = data['aws_secret_access_key']
        ILProcStat = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute(
                'insert into ILCSV values(:jobname,:srcalias,:srcdep,:tgtdep ,:tgtalias ,:s3bucket,:aws_access_key_id,:aws_secret_access_key)',
                {'jobname': jobName, 'srcdep': srcdep, 'srcalias': srcalias, "tgtdep": tgtdep, "tgtalias": tgtalias,
                 "s3bucket": s3bucket, "aws_access_key_id": aws_access_key_id,
                 "aws_secret_access_key": aws_secret_access_key})
            conn.commit()
            with open(os.path.join(oneplace_home, jobName, jobName + '_EXTRACT.log'), 'w') as infile:
                pass
            cursor.execute('select dep_url from onepconn where dep=:dep', {"dep": tgtdep})
            row = cursor.fetchone()
            if row:
                tgt_dep_url = row[0]
                tgt_dep_url = tgt_dep_url + '/insertsqlite3db'
                headers = {"Content-Type": "application/json"}
                payload = {'jobName': jobName, 'srcdep': srcdep, 'srcalias': srcalias, "tgtdep": tgtdep,
                           "tgtalias": tgtalias, "s3bucket": s3bucket, "aws_access_key_id": aws_access_key_id,
                           "aws_secret_access_key": aws_secret_access_key}
                r = requests.post(tgt_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                print(r)
            ilp = threading.Thread(target=startExtract, args=(jobName,))
            ilp.start()
        except sqlite3.OperationalError as e:
            logger.info(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()


class CSVILProcMon(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        tabList = data['tabList']
        tgtdepurl = data['tgtdepurl']
        df = pd.read_csv(os.path.join(oneplace_home, jobName, jobName + '_Summary'))
        for name in glob.glob(os.path.join(oneplace_home, jobName, '*_stats')):
            with open(name) as infile:
                read_item = infile.read()
            os.remove(name)
            processed_rows, extElapsed = read_item.split('-')
            if not processed_rows:
                processed_rows = 0
            tempName = name.split('/')[-1]
            TabName = tempName.split('=+!')[0]
            df.loc[df['TabName'] == TabName, ['EXT_ROWS_PROCESSED']] = df.loc[df['TabName'] == TabName, [
                'EXT_ROWS_PROCESSED']] + int(processed_rows)
            df.loc[df['TabName'] == TabName, ['EXT_ELAPSED']] = extElapsed
        tgtdepurl = tgtdepurl + '/csvilprocmon'
        headers = {"Content-Type": "application/json"}
        payload = {"jobName": jobName, "tabList": tabList}
        r = requests.post(tgtdepurl, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        if (len(r.json()[0]) > 0):
            for key, value in r.json()[0].items():
                df.loc[df['TabName'] == key, ['REP_ROWS_PROCESSED']] = df.loc[df['TabName'] == key, [
                    'REP_ROWS_PROCESSED']] + int(value['REP_ROWS_PROCESSED'])
                df.loc[df['TabName'] == key, ['REP_ELAPSED']] = value['REP_ELAPSED']
        df.to_csv(os.path.join(oneplace_home, jobName, jobName + '_Summary'), index=False, header=True)
        ILExtProcStats = df.to_dict('records')
        return [ILExtProcStats]


class AddAutoILProc(Resource):
    def post(self):
        data = request.get_json(force=True)
        srcdep = data['srcdep']
        srcdomain = data['srcdomain']
        srcalias = data['srcalias']
        tgtdep = data['tgtdep']
        tgtdomain = data['tgtdomain']
        tgtalias = data['tgtalias']
        chktbl = data['chktbl']
        tabSplit = data['tabSplit']
        schemaList = data['schemaList']
        jobName = data['jobName']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        rmtHostName = data['rmtHostName']
        rmtMgrPort = data['rmtMgrPort']
        currentSCN = data['currentSCN']
        deferStart = data['deferStart']
        tgt_dep_type = 'oracle'
        AddAutoProcArray = []
        headers = {"Content-Type": "application/json"}
        TabExclude = ''
        status = ''
        df_iltables = {}
        if deferStart == False:
            status = 'RUNNING'
        elif deferStart == True:
            status = 'STOPPED'
        else:
            status = 'ABENDED'
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        try:
            ILEXT = '''select distinct b.dep_url url_src,b.dbtype db_type from onepconn b where b.dep=:srcdep'''
            param = {'srcdep': srcdep}
            ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param["srcdep"]])
            for ext in ILEXT_fetch.iterrows():
                src_api_url = ext[1]['url_src'] + '/addinitialloadext'
                src_dep_type = ext[1]['db_type']
            ILREP = '''select distinct b.dep_url url_tgt,b.dbtype db_type , user, passwd  from onepconn b where b.dep=:tgtdep'''
            param = {'tgtdep': tgtdep}
            ILREP_fetch = pd.read_sql_query(ILREP, conn, params=[param["tgtdep"]])
            for rep in ILREP_fetch.iterrows():
                url_tgt = rep[1]['url_tgt']
                tgt_dep_type = rep[1]['db_type']
                tgt_user = rep[1]['user']
                tgt_passwd = rep[1]['passwd']
            tgt_api_url = url_tgt + '/addinitialloadrep'
            trail_api_url = url_tgt + '/onepdepurl'
            tgt_mgr_upd = url_tgt + '/updatemgrfiles'
            rmtTrailPayload = {"dep": tgtdep}
            trail_req = requests.post(trail_api_url, json=rmtTrailPayload, headers=headers, verify=False,
                                      timeout=sshTimeOut)
            if len(trail_req.json()) > 0:
                rmtTrailPath = trail_req.json()[1]
            srcdblogin = 'useridalias ' + srcalias + ' domain ' + srcdomain
            tgtdblogin = 'useridalias ' + tgtalias + ' domain ' + tgtdomain
            reportRate = 'REPORTCOUNT EVERY 1 MINUTES,RATE'
            srcPDB = 'SOURCECATALOG ' + pdbName
            rmtDet = 'RMTHOST ' + rmtHostName + ',MGRPORT ' + rmtMgrPort + ', TCPBUFSIZE  4194304,ENCRYPT AES256 \n'
            batchSql = 'BATCHSQL BATCHESPERQUEUE 100, OPSPERBATCH 40000'
            sqlPred = ",SQLPREDICATE 'AS OF SCN " + str(currentSCN) + "';"
            for dfname in glob.glob(os.path.join(oneplace_home, jobName, '*tables')):
                df_iltables = pd.read_csv(dfname, index_col=False)
            for i, name in enumerate(tabSplit):
                name = name['TABLE_NAME']
                extName = 'E' + jobName + str(i)
                ExtParam = 'EXTRACT ' + extName + '\n' + srcdblogin + '\n'
                repName = 'R' + jobName + str(i)
                RepParam = 'REPLICAT ' + repName + '\n' + tgtdblogin + '\n'
                trailName = os.path.join(trailPath, jobName, 'Z' + str(i))
                rmtTrailName = os.path.join(rmtTrailPath, jobName, 'Z' + str(i))
                if srcdep == tgtdep:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + 'TABLE ' + name + sqlPred
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\nMAP ' + name + ',TARGET ' + name + ';'
                    else:
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + 'TABLE ' + name + sqlPred
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\nMAP ' + name + ',TARGET ' + name + ';'
                else:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + 'TABLE ' + name + sqlPred
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\nMAP ' + name + ',TARGET ' + name + ';'
                    else:
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\nTABLE ' + name + sqlPred
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\nMAP ' + name + ',TARGET ' + name + ';'
                srcpayload = {"jobName": jobName, "extname": extName, "currentExtParamList": extPrmContents,
                              "startExtChk": False}
                tgtpayload = {"jobName": jobName, "repname": repName, "tgtdomain": tgtdomain, "tgtalias": tgtalias,
                              "repmode": 'classic', "currentRepParamList": repPrmContents, "trail": rmtTrailName,
                              "chktbl": chktbl, "startRepChk": False}
                try:
                    src_req = requests.post(src_api_url, json=srcpayload, headers=headers, verify=False,
                                            timeout=sshTimeOut)
                    tgt_req = requests.post(tgt_api_url, json=tgtpayload, headers=headers, verify=False,
                                            timeout=sshTimeOut)
                    if len(src_req.json()[0]) > 0:
                        AddAutoProcArray.append(src_req.json()[0][0])
                        cursor.execute(
                            '''insert into ILEXT values(:jobname,:srcdep,:domain,:alias,:extname,:status, :srctrail)''',
                            {'jobname': jobName, 'srcdep': srcdep, 'domain': srcdomain, 'alias': srcalias,
                             'extname': extName, 'status': status, 'srctrail': rmtTrailName})
                        conn.commit()
                    if len(tgt_req.json()[0]) > 0:
                        AddAutoProcArray.append(tgt_req.json()[0][0])
                        cursor.execute('''insert into ILREP values(:jobname,:tgtdep,:domain,:alias,:repname,:status,
                                        :tgttrail)''',
                                       {'jobname': jobName, 'tgtdep': tgtdep, 'domain': tgtdomain, 'alias': tgtalias,
                                        'repname': repName, 'status': status, 'tgttrail': rmtTrailName})
                        conn.commit()
                except requests.exceptions.ConnectionError:
                    AddAutoProcArray.append('Remote Deployment Not reachable')
                TabExclude = TabExclude + 'TABLEEXCLUDE ' + name + '\n'
                df_iltables.loc[df_iltables.OWNER + '.' + df_iltables.TABLE_NAME == name, "PROC"] = extName
            extName = 'E' + jobName + 'AA'
            ExtParam = 'EXTRACT ' + extName + '\n' + srcdblogin + '\n'
            repName = 'R' + jobName + 'AA'
            RepParam = 'REPLICAT ' + repName + '\n' + tgtdblogin + '\n'
            trailName = os.path.join(trailPath, jobName, 'ZZ')
            rmtTrailName = os.path.join(rmtTrailPath, jobName, 'ZZ')
            extTableMaps = ''
            repTableMaps = ''
            for name in schemaList:
                extTableMaps = extTableMaps + 'TABLE ' + name + '.*' + sqlPred + '\n'
                repTableMaps = repTableMaps + 'MAP ' + name + '.*' + ',TARGET ' + name + '.*;' + '\n'
            if len(tabSplit) > 0:
                if srcdep == tgtdep:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                    else:
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
                else:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                    else:
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
            else:
                if srcdep == tgtdep:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                    else:
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
                else:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                    else:
                        extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
            mgrPrmload = {"prmFile": 'mgr.prm', "prmContent": '\nPURGEOLDEXTRACTS ' + os.path.join(rmtTrailPath,
                                                                                                   jobName) + '/*' + ',USECHECKPOINTS'}
            mgr_prm_upd = requests.post(tgt_mgr_upd, json=mgrPrmload, headers=headers, verify=False, timeout=sshTimeOut)
            mgrOps_url = url_tgt + '/ggmgrops'
            mgrRefreshPayload = {"mgrOps": 'mgrrefresh'}
            mgr_refresh = requests.post(mgrOps_url, json=mgrRefreshPayload, headers=headers, verify=False,
                                        timeout=sshTimeOut)
            df_iltables['PROC'].fillna(extName, inplace=True)
            df_iltables.to_csv(dfname)
            srcpayload = {"jobName": jobName, "extname": extName, "currentExtParamList": extPrmContents,
                          "startExtChk": False}
            if tgt_dep_type != 'bda':
                tgtpayload = {"jobName": jobName, "repname": repName, "tgtdomain": tgtdomain, "tgtalias": tgtalias,
                              "repmode": 'classic', "currentRepParamList": repPrmContents, "trail": rmtTrailName,
                              "chktbl": chktbl, "startRepChk": False}
            try:
                src_req = requests.post(src_api_url, json=srcpayload, headers=headers, verify=False, timeout=sshTimeOut)
                tgt_req = requests.post(tgt_api_url, json=tgtpayload, headers=headers, verify=False, timeout=sshTimeOut)
                if len(src_req.json()[0]) > 0:
                    AddAutoProcArray.append(src_req.json()[0][0])
                    cursor.execute('''insert into ILEXT values(:jobname,:srcdep,:domain,:alias,:extname,:status,
                                        :srctrail)''',
                                   {'jobname': jobName, 'srcdep': srcdep, 'domain': srcdomain, 'alias': srcalias,
                                    'extname': extName, 'status': status, 'srctrail': rmtTrailName})
                    conn.commit()
                if len(tgt_req.json()[0]) > 0:
                    AddAutoProcArray.append(tgt_req.json()[0][0])
                    cursor.execute('''insert into ILREP values(:jobname,:tgtdep,:domain,:alias,:repname,:status,
                                        :tgttrail)''',
                                   {'jobname': jobName, 'tgtdep': tgtdep, 'domain': tgtdomain, 'alias': tgtalias,
                                    'repname': repName, 'status': status, 'tgttrail': rmtTrailName})
                    conn.commit()
            except requests.exceptions.ConnectionError:
                AddAutoProcArray.append('Remote Deployment Not reachable')
            with open(os.path.join(oneplace_home, 'AddAutoProc.lst'), 'w') as extErrFileIn:
                for listline in AddAutoProcArray:
                    extErrFileIn.write(listline)
            with open(os.path.join(oneplace_home, 'AddAutoProc.lst'), 'r') as extErrFile:
                ExtErrPrint = []
                for line in extErrFile:
                    if 'ERROR' in line:
                        line = line.split('>', 1)[-1]
                        ExtErrPrint.append(line)
                    elif 'added.' in line:
                        line = line.split('>', 1)[-1]
                        ExtErrPrint.append(line)
        except sqlite3.DatabaseError as e:
            AddAutoProcArray.append(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()

        return [AddAutoProcArray]


class AddILEXT(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        srcdep = data['srcdep']
        extname = data['extname']
        trail = data['trail']
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('insert into ILEXT values(:jobname,:srcdep,:extname,:srctrail)',
                           {'jobname': jobName, 'srcdep': srcdep, 'extname': extname, 'srctrail': trail})
            conn.commit()
            conn.close()
            msg = 'Successfully Inserted'
        except sqlite3.DatabaseError as e:
            msg = str(e)
        return [msg]


class DelILEXT(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        srcdep = data['srcdep']
        extname = data['extname']
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('''delete from ILEXT where extname=:extname and srcdep=:srcdep and jobname=:jobname''',
                           {"srcdep": srcdep, "extname": extname, "jobname": jobName})
            conn.commit()
            conn.close()
            msg = 'Successfully Deleted'
        except sqlite3.DatabaseError as e:
            msg = str(e)
        return [msg]


class AddInitialLoadRep(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        repname = data['repname']
        tgtdomain = data['tgtdomain']
        tgtalias = data['tgtalias']
        repmode = data['repmode']
        currentRepParamList = data['currentRepParamList']
        startRepChk = data['startRepChk']
        repPrm = os.path.join(gg_home, 'dirprm', repname + '.prm')
        with open(repPrm, 'w') as repFile:
            repFile.write(currentRepParamList)
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        if repmode == 'parallel':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write(
                "add replicat " + repname + ',' + repmode + ',exttrail ' + trail + ',checkpointtable ' + chktbl + "\n")
        elif repmode == 'integrated':
            trail = data['trail']
            ssh.stdin.write("add replicat " + repname + ',' + repmode + ',exttrail ' + trail + "\n")
        elif repmode == '' or repmode == 'classic':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write("add replicat " + repname + ',exttrail ' + trail + ',checkpointtable ' + chktbl + "\n")
        elif repmode == 'coordinated':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write(
                "add replicat " + repname + ',' + repmode + ',exttrail ' + trail + ',checkpointtable ' + chktbl + "\n")
        elif repmode == 'SPECIALRUN':
            ssh.stdin.write("add replicat " + repname + ',' + repmode + "\n")
        if startRepChk is False:
            ssh.stdin.write("start replicat " + repname + "\n")
        AddRepErr, stderr = ssh.communicate()
        AddRep_Out = []
        AddRep_Out.append(AddRepErr)
        with open(oneplace_home + '/AddInitialRepErr.lst', 'w') as repErrFileIn:
            for listline in AddRep_Out:
                repErrFileIn.write(listline)
        with open(oneplace_home + '/AddInitialRepErr.lst', 'r') as repErrFile:
            RepErrPrint = []
            for line in repErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    RepErrPrint.append(line)
                elif 'added.' in line:
                    line = line.split('>', 1)[-1]
                    RepErrPrint.append(line)

        return [RepErrPrint]


class AddILREP(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        tgtdep = data['tgtdep']
        repname = data['repname']
        trail = data['trail']
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('''insert into ILREP values(:jobname,:tgtdep,:repname,:tgttrail)''',
                           {"jobname": jobName, "tgtdep": tgtdep, "repname": repname, "tgttrail": trail})
            conn.commit()
            conn.close()
            msg = 'Successfully Inserted'
        except sqlite3.DatabaseError as e:
            msg = str(e)
        return [msg]


class DelILREP(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        tgtdep = data['tgtdep']
        repname = data['repname']
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('''delete from ILREP where jobname=:jobname and repname=:repname and tgtdep=:tgtdep''',
                           {"jobname": jobName, "tgtdep": tgtdep, "repname": repname})
            conn.commit()
            conn.close()
            msg = 'Successfully Deleted'
        except sqlite3.DatabaseError as e:
            msg = str(e)
        return [msg]


class ggILDataSet(Resource):
    def get(self):
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            ILData = '''select jobname from ILCSV'''
            ILData_fetch = pd.read_sql_query(ILData, conn)
            ILData_fetch = ILData_fetch.to_dict('records')
        except sqlite3.Error as e:
            ILData_fetch = str(e)
        return [ILData_fetch]


class ggProcessAction(Resource):
    def post(self):
        data = request.get_json(force=True)
        processName = data['processName']
        ops = data['ops']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=100)
        if ops.startswith('stop'):
            for name in processName:
                for key, process in name.items():
                    if key == 'ExtName' or key == 'PmpName' or key == 'RepName':
                        ssh.stdin.write("stop " + process + '\n')
        elif ops.startswith('start'):
            for name in processName:
                for key, process in name.items():
                    if key == 'ExtName' or key == 'PmpName' or key == 'RepName':
                        ssh.stdin.write("start " + process + '\n')
        resProcess, stderr = ssh.communicate()
        ActionErrPrint = []
        with open(os.path.join(oneplace_home, 'ggProcessAction.trc'), 'w') as extChkFileIn:
            extChkFileIn.write(resProcess)
        with open(os.path.join(oneplace_home, 'ggProcessAction.trc')) as extErrFile:
            extErrFile = extErrFile.readlines()[8:]
            for line in extErrFile:
                if 'GGSCI' in line:
                    line = line.split('>', 1)[-1]
                    ActionErrPrint.append(line)
                else:
                    ActionErrPrint.append(line)

        return [ActionErrPrint]


class ggILTables(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['JobName']
        ILExtProcStats = {}
        tgtdeptype = ''
        tgtdepurl = ''
        try:
            metaDir = os.path.join(oneplace_home, jobName, jobName + '*.csv')
            for file in glob.glob(metaDir):
                df = pd.read_csv(file)
                for i, name in df.iterrows():
                    TabName = name['owner'] + '.' + name['table_name']
                    ILExtProcStats[TabName] = {'TargetRows': name['count'], 'Process': 'Extract',
                                               "EXT_ROWS_PROCESSED": 0, "EXT_ELAPSED": 0, "EXT_RATE": 0,
                                               "REP_ROWS_PROCESSED": 0, "REP_ELAPSED": 0, "REP_RATE": 0}
        except Exception as e:
            tgtdeptype = str(e)
        finally:
            df.index.name = 'TabName'
            if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Summary')):
                df.to_csv(os.path.join(oneplace_home, jobName, jobName + '_Summary'))
        return [ILExtProcStats, tgtdeptype, tgtdepurl]


class ggILJobAct(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        ilops = data['ilops']
        ILOpsErrPrint = []
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        if ilops.startswith('ext'):
            extname = data['extName']
            i = 1
            bindNames = ','.join(':%d' % i for i in range(len(extname)))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            if ilops == 'extstop':
                for name in extname:
                    ssh.stdin.write("kill " + name + '\n')
                ilExtKill, stderr = ssh.communicate()
                ILEXTUPD = '''update ILEXT set status='STOPPED' where extname in (%s)''' % bindNames
                cursor.execute(ILEXTUPD, extname)
                conn.commit()
                with open(os.path.join(oneplace_home, 'ILExtOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(ilExtKill)
            elif ilops == 'extstart':
                for name in extname:
                    ssh.stdin.write("start extract " + name + '\n')
                ilExtStart, stderr = ssh.communicate()
                ILEXTUPD = '''update ILEXT set status='RUNNING' where extname in (%s)''' % bindNames
                cursor.execute(ILEXTUPD, extname)
                conn.commit()
                with open(os.path.join(oneplace_home, 'ILExtOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(ilExtStart)
            elif ilops == 'extpurge':
                for name in extname:
                    ssh.stdin.write("delete " + name + '\n')
                ilExtDel, stderr = ssh.communicate()
                ILEXTDEL = '''delete from ILEXT where extname in (%s)''' % bindNames
                cursor.execute(ILEXTDEL, extname)
                conn.commit()
                with open(os.path.join(oneplace_home, 'ILExtOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(ilExtDel)
            with open(os.path.join(oneplace_home, 'ILExtOps.lst'), 'r') as ilExtOpsFile:
                ilExtOpsFile = ilExtOpsFile.readlines()[8:]
                for line in ilExtOpsFile:
                    if 'GGSCI' in line:
                        line = line.split('>', 1)[-1]
                        ILOpsErrPrint.append(line)
                    else:
                        ILOpsErrPrint.append(line)
        elif ilops.startswith('rep'):
            repDet = data['repDet']
            i = 1
            bindNames = ','.join(':%d' % i for i in range(len(repDet)))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            repName = []
            if ilops == 'repstop':
                for pattern in repDet:
                    ssh.stdin.write("kill " + pattern['repname'] + '\n')
                    ssh.stdin.write("alter replicat " + pattern['repname'] + ' , extseqno 0 , extrba 0  \n')
                    repName.append(pattern['repname'])
                    fileList = glob.glob(pattern['trail'] + '*', recursive=True)
                    for filename in fileList:
                        os.remove(filename)
                chkRep, stderr = ssh.communicate()
                ILREPUPD = '''update ILREP set status='STOPPED' where repname in (%s)''' % bindNames
                cursor.execute(ILREPUPD, repName)
                conn.commit()
                conn.close()
                with open(os.path.join(oneplace_home, 'ILRepOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(chkRep)
                for file in os.scandir(os.path.join(oneplace_home, jobName)):
                    if '_tables' not in file.name:
                        os.remove(file.path)
            elif ilops == 'repstart':
                for pattern in repDet:
                    ssh.stdin.write("start " + pattern['repname'] + ', NOFILTERDUPTRANSACTIONS \n')
                    repName.append(pattern['repname'])
                chkRep, stderr = ssh.communicate()
                ILREPUPD = '''update ILREP set status='RUNNING' where repname in (%s)''' % bindNames
                cursor.execute(ILREPUPD, repName)
                conn.commit()
                conn.close()
                with open(os.path.join(oneplace_home, 'ILRepOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(chkRep)
            elif ilops == 'reppurge':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                for pattern in repDet:
                    if pattern['status'] == 'STOPPED':
                        ssh.stdin.write('delete replicat ' + pattern['repname'] + '\n')
                        repName.append(pattern['repname'])
                    else:
                        chkRep = 'Replicat ' + pattern['repname'] + ' is still running'
                chkRep, stderr = ssh.communicate()
                ILREPDEL = '''delete from ILREP where repname in (%s)''' % bindNames
                cursor.execute(ILREPDEL, repName)
                conn.commit()
                conn.close()
                with open(os.path.join(oneplace_home, 'ILRepOps.lst'), 'w') as ilOpsFileIn:
                    ilOpsFileIn.write(chkRep)
            with open(os.path.join(oneplace_home, 'ILRepOps.lst'), 'r') as ilRepOpsFile:
                ilRepOpsFile = ilRepOpsFile.readlines()[8:]
                for line in ilRepOpsFile:
                    if 'GGSCI' in line:
                        line = line.split('>', 1)[-1]
                        ILOpsErrPrint.append(line)
                    else:
                        ILOpsErrPrint.append(line)
        return [ILOpsErrPrint]


class ggILAction(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        ilops = data['ilops']
        ilOpData = []
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        ILEXT = '''select distinct a.*,b.dep_url url_src from ILEXT a, onepconn b
                            where a.srcdep=b.dep and a.jobname=:jobName'''
        param = {'jobName': jobName}
        ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param["jobName"]])
        extName = []
        for ext in ILEXT_fetch.iterrows():
            dep_url = ext[1]['url_src']
            extName.append(ext[1]['extname'])
        api_url = dep_url + '/ggiljobact'
        payload = {"jobName": jobName, 'extName': extName, 'ilops': 'ext' + ilops}
        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(api_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            if len(r.json()[0]) > 0:
                ilOpData = r.json()[0]
        except requests.exceptions.ConnectionError:
            ILException = 'error'
        ILREP = '''select distinct a.*,b.dep_url url_tgt from ILREP a, onepconn b
                            where a.tgtdep=b.dep and jobname=:jobName'''
        param = {'jobName': jobName}
        ILREP_fetch = pd.read_sql_query(ILREP, conn, params=[param["jobName"]])
        repDet = []
        for rep in ILREP_fetch.iterrows():
            dep_url = rep[1]['url_tgt']
            repDet.append({'repname': rep[1]['repname'], 'status': rep[1]['status'], 'trail': rep[1]['trail']})
            tgtdomain = rep[1]['domain']
            tgtalias = rep[1]['alias']
        api_url = dep_url + '/ggiljobact'
        payload = {"jobName": jobName, 'repDet': repDet, 'ilops': 'rep' + ilops, 'domain': tgtdomain, 'alias': tgtalias}
        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(api_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            if len(r.json()[0]) > 0:
                ilOpData = r.json()[0]
        except requests.exceptions.ConnectionError:
            ILException = 'error'
        return [ilOpData]


class ggILProcesses(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['JobName']
        TrailCommon = ''
        ILException = ''
        ILExtData = []
        ILRepData = []
        ILExtProcStats = {}
        ILRepProcStats = {}
        ProcessNode = {}
        SrcLinkNode = []
        TgtLinkNode = []
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        ILEXT = '''select distinct a.*,b.dep_url url_src from ILCSV a, onepconn b
                            where a.srcdep=b.dep and a.jobname=:jobName'''
        param = {'jobName': jobName}
        ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param["jobName"]])
        for ext in ILEXT_fetch.iterrows():
            depName = ext[1]['srcdep']
            extname = 'Extract_' + jobName
            dep_url = ext[1]['url_src']
            trail = 'a'
            ProcessNode.setdefault(depName, []).append({'procname': extname, 'dep_url': dep_url, 'type': 'Ext'})
            SrcLinkNode.append({'extname': extname, 'trail': trail, 'dep_src': depName})
        metaDir = os.path.join(oneplace_home, jobName, jobName + '*.csv')
        for file in glob.glob(metaDir):
            df = pd.read_csv(file)
            for idx, row in df.iterrows():
                TabName = row['owner'] + '.' + row['table_name']
                ILExtProcStats[TabName] = {"TargetRows": row['count'], "TotalEXT": 0}
        tabNameList = []
        with open(os.path.join(oneplace_home, jobName, jobName + '_EXTRACT.log')) as infile:
            for line in infile:
                line = line.split()
                if line[-1] in ILExtProcStats.keys():
                    ILExtProcStats[line[-1]]["TotalEXT"] = line[5]
                    tabNameList.append(line[-1])
        ILREP = '''select distinct a.*,b.dep_url url_tgt from ILCSV a, onepconn b
                            where a.tgtdep=b.dep and a.jobname=:jobName'''
        param = {'jobName': jobName}
        ILREP_fetch = pd.read_sql_query(ILREP, conn, params=[param["jobName"]])
        for rep in ILREP_fetch.iterrows():
            depName = rep[1]['tgtdep']
            repname = 'REPLICAT_' + jobName
            tgt_dep_url = rep[1]['url_tgt']
            trail = 'a'
            ProcessNode.setdefault(depName, []).append({'procname': repname, 'dep_url': tgt_dep_url, 'type': 'Rep'})
            TgtLinkNode.append({'repname': repname, 'trail': trail, 'dep_tgt': depName})
        print(tgt_dep_url)
        tgt_dep_url = tgt_dep_url + '/replicatstats'
        payload = {"jobName": jobName, "tabNameList": tabNameList}
        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(tgt_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            print(r)
            if len(r.json()[0]) > 0:
                for key in r.json()[0]:
                    print(r.json()[0][key])
                    ILExtProcStats[key].update(r.json()[0][key])
                print(ILExtProcStats)
        except Exception as e:
            logger.info('Replicat Stats Collection Error ' + str(e))
        SrcLinkNode_fetch = pd.DataFrame(SrcLinkNode)
        TgtLinkNode_fetch = pd.DataFrame(TgtLinkNode)
        if SrcLinkNode_fetch.empty == False and TgtLinkNode_fetch.empty == False:
            TrailCommon = pd.merge(SrcLinkNode_fetch, TgtLinkNode_fetch, on=['trail'], how="inner")
            TrailCommon = TrailCommon.to_dict('records')
        return [TrailCommon, ILExtData, ILExtProcStats, ProcessNode, ILRepData, ILException]


class ggExtProcStats(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        procName = data['procName']
        procStats = data['procStats']
        ILExtProcStats = data['ILExtProcStats']
        if procStats == 'RUNNING':
            if not os.path.exists(os.path.join(oneplace_home, jobName)): os.makedirs(
                os.path.join(oneplace_home, jobName))
            if not os.path.exists(os.path.join(oneplace_home, jobName, procName + 'running')):
                with  open(os.path.join(oneplace_home, jobName, procName + 'running'), mode='w') as infile:
                    pass
                ilp = threading.Thread(target=ILGetStats, args=(procName, jobName))
                ilp.start()
            try:
                with  open(os.path.join(oneplace_home, jobName, procName + 'Rate.lst')) as infile:
                    copy = False
                    rateCopy = False
                    for line in infile:
                        if line.startswith('Extracting'):
                            TabName = line.split()[2]
                        elif 'Total statistics' in line:
                            rateCopy = True
                        elif 'updates/second' in line:
                            rateCopy = False
                        elif rateCopy:
                            if 'inserts/second' in line:
                                ExtRate = line.split()[2]
                        elif 'Latest statistics' in line:
                            line = line.split()
                            copy = True
                        elif 'End of statistics' in line:
                            copy = False
                        elif copy:
                            if 'Total inserts/second' in line:
                                TotalEXT = round(float(line.split()[2]))
                            elif 'Total discards/second' in line:
                                TotalEXTDSC = line.split()[2]
                                if TabName in ILExtProcStats.keys():
                                    ILExtProcStats[TabName].update(
                                        {'TotalEXT': TotalEXT, 'TotalEXTDSC': TotalEXTDSC, 'ExtRate': ExtRate})
            except FileNotFoundError:
                pass
        elif procStats == 'STOPPED' or 'ABENDED':
            stop_threads = True
            if os.path.exists(os.path.join(oneplace_home, jobName, procName + 'running')):
                os.remove(os.path.join(oneplace_home, jobName, procName + 'running'))
            if os.path.exists(os.path.join(oneplace_home, jobName, procName + 'Rate.lst')):
                os.remove(os.path.join(oneplace_home, jobName, procName + 'Rate.lst'))
            try:
                with open(os.path.join(gg_home, 'dirrpt', procName + '.rpt'), 'r') as infile:
                    for line in infile:
                        if 'Report at' in line:
                            line = line.split()
                            endTime = line[2] + ':' + line[3]
                            startTime = line[6] + ':' + line[7].rstrip(')')
                            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
                            elapTime = datetime.strptime(endTime, datetimeFormat) - datetime.strptime(startTime,
                                                                                                      datetimeFormat)
                            elapTime = str(elapTime.total_seconds())
                        elif line.startswith('From Table'):
                            TabName = line.split()[2].rstrip(':')
                        elif 'inserts' in line:
                            TotalEXT = line.split()[2]
                        elif 'discards' in line:
                            TotalEXTDSC = line.split()[2]
                            if TabName in ILExtProcStats.keys():
                                ILExtProcStats[TabName].update(
                                    {'TotalEXT': TotalEXT, 'TotalEXTDSC': TotalEXTDSC, 'ExtElapse': elapTime,
                                     'ExtRate': 'Completed'})
            except FileNotFoundError:
                pass
        return ILExtProcStats


class ggRepProcStats(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        viewList = []
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            for schema in schemaList:
                cursor.execute("""SELECT vcreator||'.'||viewname from SYSVIEWS where vcreator=?""", (schemaName,))
                viewName = cursor.fetchall()
                viewList.append(viewName)
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [viewList]


class ggAddIE(Resource):
    def post(self):
        data = request.get_json(force=True)
        regExtChk = data['regExtChk']
        regVal = data['regVal']
        lmDictSCN = data['lmDictSCN']
        currentShareOpt = data['currentShareOpt']
        CaptureName = data['CaptureName']
        extname = data['extname']
        domain = data['domain']
        alias = data['alias']
        mode = data['mode']
        beginmode = data['beginmode']
        trailtype = data['trailtype']
        trailsubdir = data['trailsubdir']
        trailsubdirslash = data['trailsubdirslash']
        trail = data['trail']
        trailsize = data['trailsize']
        currentExtParamList = data['currentExtParamList']
        startExtChk = data['startExtChk']
        CDBCheck = data['CDBCheck']
        PDBName = data['PDBName']
        pdbSelList = data['pdbSelList']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddExt_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddExt_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            AddExt_Out.append(LoginErr)
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            if str(regExtChk) == 'True':
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                if CDBCheck == 'YES':
                    PDBList = ""
                    for name in pdbSelList:
                        PDBList = PDBList + name + ','
                    PDBList = PDBList.rstrip(',')
                    AddExt_Out.append(PDBList)
                    if regVal == 'now':
                        ssh.stdin.write("register extract " + extname + " database CONTAINER(" + PDBList + ")" + "\n")
                    elif regVal == 'existscn':
                        ssh.stdin.write(
                            "register extract " + extname + " database CONTAINER(" + PDBList + ")" + " SCN " + str(
                                lmDictSCN) + "\n")
                else:
                    if regVal == 'now':
                        ssh.stdin.write("register extract " + extname + " database" + "\n")
                    elif regVal == 'existscn' and currentShareOpt == 'NONE':
                        ssh.stdin.write("register extract " + extname + " database SCN " + str(
                            lmDictSCN) + " SHARE " + currentShareOpt + "\n")
                    elif regVal == 'existscn' and currentShareOpt == 'AUTOMATIC':
                        ssh.stdin.write("register extract " + extname + " database SCN " + str(
                            lmDictSCN) + " SHARE " + currentShareOpt + "\n")
                    elif regVal == 'existscn' and currentShareOpt == 'EXTRACT':
                        ssh.stdin.write("register extract " + extname + " database SCN " + str(
                            lmDictSCN) + " SHARE " + CaptureName + "\n")
            RegErr, stderr = ssh.communicate()
            if "ERROR" in RegErr:
                AddExt_Out.append(RegErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                ssh = subprocess.Popen([ggsci_bin],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       universal_newlines=True,
                                       bufsize=0)
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("add extract " + extname + " integrated tranlog " + beginmode + "\n")
                ssh.stdin.write(
                    "add exttrail " + trailsubdir + trailsubdirslash + trail + " extract " + extname + " megabytes " + str(
                        trailsize) + "\n")
                AddExtErr, stderr = ssh.communicate()
                if 'ERROR' in AddExtErr:
                    AddExt_Out.append(AddExtErr)
                    ssh.kill()
                    ssh.stdin.close()
                else:
                    extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
                    with open(extPrm, 'w') as extFile:
                        extFile.write(currentExtParamList)
                        if startExtChk is False:
                            ssh = subprocess.Popen([ggsci_bin],
                                                   stdin=subprocess.PIPE,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT,
                                                   universal_newlines=True,
                                                   bufsize=0)
                            ssh.stdin.write("start extract " + extname)
                            StartExtErr, stderr = ssh.communicate()
                            AddExt_Out.append(AddExtErr)
                            AddExt_Out.append(StartExtErr)
                        else:
                            AddExt_Out.append(AddExtErr)
                            ssh.kill()
                            ssh.stdin.close()
        with open(oneplace_home + '/AddExtErr.lst', 'w') as extErrFileIn:
            for listline in AddExt_Out:
                extErrFileIn.write(listline)
        with open(oneplace_home + '/AddExtErr.lst', 'r') as extErrFile:
            ExtErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif 'added.' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)

        return [ExtErrPrint]


class ggInfoChkptTbl(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        InfoChkptErrPrint = []
        if os.path.exists(ggsci_bin):
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            InfoChkptTbl_Out = []
            LoginErr, stderr = ssh.communicate()
            if "ERROR" in LoginErr:
                InfoChkptTbl_Out.append(LoginErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                conn = sqlite3.connect('conn.db')
                cursor = conn.cursor()
                cursor.execute('SELECT tabname FROM CHKPT WHERE dbname=:dbname', {"dbname": alias})
                db_row = cursor.fetchone()
                if db_row:
                    tabname = db_row[0]
                    ssh = subprocess.Popen([ggsci_bin],
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True,
                                           bufsize=0)
                    ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                    ssh.stdin.write("info  checkpointtable " + tabname + "\n")
                    InfoChkptTblErr, stderr = ssh.communicate()
                    InfoChkptTbl_Out.append(InfoChkptTblErr)
                else:
                    InfoChkptTbl_Out.append('ERROR : No Checkpoint Table found')
            with open(os.path.join(oneplace_home, 'InfoChkptTbl.lst'), 'w') as InfoErrFileIn:
                for listline in InfoChkptTbl_Out:
                    InfoErrFileIn.write(listline)
            with open(os.path.join(oneplace_home, 'InfoChkptTbl.lst'), 'r') as InfoErrFile:
                for line in InfoErrFile:
                    if 'ERROR' in line:
                        line = line.split('>', 1)[-1]
                        InfoChkptErrPrint.append(line)
                    elif 'OCI' in line:
                        InfoChkptErrPrint.append(line)
                    elif 'created' in line:
                        line = line.split()
                        if 'created' in line[1:]:
                            InfoChkptErrPrint.append(line[line.index('table') + 1])

        return [InfoChkptErrPrint]


class ggAddChkptTbl(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        chkpttbl = data['chkpttbl']
        AddChkptErrPrint = ''
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddChkptTbl_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddChkptTbl_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            ssh.stdin.write("add checkpointtable  " + chkpttbl + "\n")
            AddChkptTblErr, stderr = ssh.communicate()
            AddChkptTbl_Out.append(AddChkptTblErr)
        with open(os.path.join(oneplace_home, 'AddChkptTbl.lst'), 'w') as extErrFileIn:
            for listline in AddChkptTbl_Out:
                extErrFileIn.write(listline)
        with open(os.path.join(oneplace_home, 'AddChkptTbl.lst'), 'r') as extErrFile:
            AddChkptErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    AddChkptErrPrint.append(line)
                    if 'already' in line:
                        conn = sqlite3.connect('conn.db')
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''insert into CHKPT values(:dbname,:tabname)''',
                                           {"dbname": alias, "tabname": chkpttbl})
                            conn.commit()
                        except sqlite3.DatabaseError as e:
                            pass
                        finally:
                            if conn:
                                cursor.close()
                                conn.close()
                elif 'OCI' in line:
                    AddChkptErrPrint.append(line)
                elif 'created' in line:
                    conn = sqlite3.connect('conn.db')
                    cursor = conn.cursor()
                    cursor.execute('''insert into CHKPT values(:dbname,:tabname)''',
                                   {"dbname": alias, "tabname": chkpttbl})
                    conn.commit()
                    conn.close()
                    line = line.split('>', 1)[-1]
                    AddChkptErrPrint.append(line)

        return [AddChkptErrPrint]


class ggAddCE(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        domain = data['domain']
        alias = data['alias']
        mode = data['mode']
        threads = data['threads']
        beginmode = data['beginmode']
        trailtype = data['trailtype']
        trailsubdir = data['trailsubdir']
        trailsubdirslash = data['trailsubdirslash']
        trail = data['trail']
        trailsize = data['trailsize']
        currentExtParamList = data['currentExtParamList']
        startExtChk = data['startExtChk']
        regExtChk = data['regExtChk']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddCE_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddCE_Out.append(LoginErr)
            ssh.kill()
        else:
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            ssh.stdin.write("add extract " + extname + " " + mode + " threads " + str(threads) + " " + beginmode + "\n")
            ssh.stdin.write(
                "add exttrail " + trailsubdir + trailsubdirslash + trail + " extract " + extname + " megabytes " + str(
                    trailsize) + "\n")
            if regExtChk is True:
                ssh.stdin.write("register extract " + extname + " LOGRETENTION \n")
            AddCEErr, stderr = ssh.communicate()
            AddCE_Out.append(AddCEErr)
            extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
            with open(extPrm, 'w') as extFile:
                extFile.write(currentExtParamList)
            if startExtChk is False:
                ssh = subprocess.Popen([ggsci_bin],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       universal_newlines=True,
                                       bufsize=0)
                ssh.stdin.write("start extract " + extname)
                StartCEErr, stderr = ssh.communicate()
                AddCE_Out.append(StartCEErr)
                ssh.kill()
                ssh.stdin.close()
        with open(os.path.join(oneplace_home, 'AddCEErr.lst'), 'w') as extErrFileIn:
            for listline in AddCE_Out:
                extErrFileIn.write(listline)
        with open(os.path.join(oneplace_home, 'AddCEErr.lst')) as extErrFile:
            ExtErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif 'added.' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
        return [ExtErrPrint]


class ggGetExtTrail(Resource):
    def get(self):
        ExtTrail_Data = []
        InfoExt = subprocess.getoutput("echo -e 'info exttrail'|" + ggsci_bin)
        with  open(oneplace_home + "/infoext.out", mode='w') as outfile2:
            outfile2.write(InfoExt)
        with  open(oneplace_home + "/infoext.out", mode='r') as infile:
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip()
                    ExtTrailSet = {'label': ExtName, 'value': TrailName}
                    ExtTrail_Data.append(ExtTrailSet)

        return [ExtTrail_Data]


class ggGetExtParam(Resource):
    def post(self):
        data = request.get_json(force=True)
        currentextname = data['currentextname']
        ExtPrm_Data = []
        exttrail = subprocess.getoutput(
            "echo -e 'info '" + currentextname + " , showch |" + ggsci_bin + "|grep -i 'Extract Trail:'")
        exttrail = exttrail.split(':')[1]
        copy = False
        for name in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
            name = name.split('/')[-1]
            if re.match(name, currentextname + '.prm', re.IGNORECASE):
                with  open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('sourcecatalog', line, re.IGNORECASE):
                            copy = True
                        if re.match('table', line, re.IGNORECASE):
                            copy = True
                        if copy:
                            ExtPrm_Data.append(line)

        return [ExtPrm_Data, exttrail]


class ggAddPumpPT(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        mode = data['mode']
        srcTrail = data['srcTrail']
        beginmode = data['beginmode']
        trail = data['trail']
        trailsize = data['trailsize']
        currentPmpParamList = data['currentPmpParamList']
        startPmpChk = data['startPmpChk']
        AddPmp_Out = []
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("add extract " + extname + " , " + mode + " " + srcTrail + " " + beginmode + "\n")
        ssh.stdin.write("add rmttrail " + trail + " extract " + extname + " megabytes " + str(trailsize) + "\n")
        AddPmpErr, stderr = ssh.communicate()
        with open(os.path.join(gg_home, 'dirprm', extname + '.prm'), 'w') as pmpFile:
            pmpFile.write(currentPmpParamList)
        if startPmpChk is False:
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            ssh.stdin.write("start extract " + extname + '\n')
            StartPmpErr, stderr = ssh.communicate()
            AddPmp_Out.append(AddPmpErr)
            AddPmp_Out.append(StartPmpErr)
        else:
            AddPmp_Out.append(AddPmpErr)
        with open(oneplace_home + '/AddPmpErr.lst', 'w') as pmpErrFileIn:
            for listline in AddPmp_Out:
                pmpErrFileIn.write(listline)
        with open(oneplace_home + '/AddPmpErr.lst', 'r') as pmpErrFile:
            PmpErrPrint = []
            for line in pmpErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    PmpErrPrint.append(line)
                elif 'EXTRACT' in line:
                    line = line.split('>', 1)[-1]
                    PmpErrPrint.append(line)
                elif 'added' in line:
                    line = line.split('>', 1)[-1]
                    PmpErrPrint.append(line)

        return [PmpErrPrint]


class ggDelExt(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        domain = data['domain']
        alias = data['alias']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        DelExt_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            DelExt_Out.append(LoginErr)
            ssh.kill()
        else:
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            ssh.stdin.write("delete " + extname + "\n")
            DelExtErr, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            DelExt_Out.append(DelExtErr)
        with open(oneplace_home + '/DelExtErr.lst', 'w') as extErrFileIn:
            for listline in DelExt_Out:
                extErrFileIn.write(listline)
        with open(oneplace_home + '/DelExtErr.lst', 'r') as extErrFile:
            ExtErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif 'EXTRACT' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif 'Deleted' in line:
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)

        return [ExtErrPrint]


class ggGetRMTTrail(Resource):
    def post(self):
        data = request.get_json(force=True)
        extName = data['extName']
        prm_dir = os.path.join(gg_home, 'dirprm')
        for name in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
            name = name.split('/')[-1]
            if re.match(name, extName + '.prm', re.IGNORECASE):
                with  open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('rmttrail', line, re.IGNORECASE):
                            rmtTrail = line.split()[1]
                        elif re.match('exttrail', line, re.IGNORECASE):
                            rmtTrail = line.split()[1]
        return [rmtTrail]


class ggDelRMT(Resource):
    def post(self):
        data = request.get_json(force=True)
        pmpName = data['pmpName']
        InfoRmt = subprocess.getoutput("echo -e 'info rmttrail'|" + ggsci_bin + "\n")
        DelRmt = ''
        with  open(oneplace_home + "/informt.out", mode='w') as outfile2:
            outfile2.write(InfoRmt)
        with  open(oneplace_home + "/informt.out", mode='r') as infile:
            RMT_Data = []
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip()
                    if ExtName.upper() == pmpName.upper():
                        DelRmt = subprocess.getoutput(
                            "echo -e 'delete rmttrail '" + TrailName + " , extract " + pmpName + "|" + ggsci_bin + "\n")
        if not DelRmt:
            DelRmt = 'No Remote trails attached to pump ' + pmpName
        with open(oneplace_home + '/DelRMTErr.lst', 'w') as delrmtErrFileIn:
            delrmtErrFileIn.write(DelRmt)
        with open(oneplace_home + '/DelRMTErr.lst', 'r') as delrmtErrFile:
            DelRMTErrPrint = []
            for line in delrmtErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    DelRMTErrPrint.append(line)
                elif 'match' in line:
                    line = line.split('>', 1)[-1]
                    DelRMTErrPrint.append(line)
                elif 'trail' in line:
                    line = line.split('>', 1)[-1]
                    DelRMTErrPrint.append(line)
                elif 'Deleted' in line:
                    line = line.split('>', 1)[-1]
                    DelRMTErrPrint.append(line)

        return [DelRMTErrPrint]


class ggViewMgrRpt(Resource):
    def get(self):
        mgrRpt = []
        PARAM_DIRECTORY = os.path.join(gg_home, "dirrpt")
        with open(os.path.join(gg_home, 'dirrpt', 'MGR.rpt')) as infile:
            for line in infile:
                mgrRpt.append(line)

        return [mgrRpt]


class ggExtOps(Resource):
    def post(self):
        data = request.get_json(force=True)
        extops = data['extops']
        extname = data['extname']
        prmfile = ''
        ExtErrPrint = []
        ExtProcStats = {}
        if extops == 'extrpt':
            for name in glob.glob(os.path.join(gg_home, 'dirrpt', '*.rpt')):
                name = name.split('/')[-1]
                if re.match(name, extname + '.rpt', re.IGNORECASE):
                    dest_file = os.path.join(gg_home, 'dirrpt', name)
                    with open(dest_file, 'r') as extErrFile:
                        for line in extErrFile:
                            ExtErrPrint.append(line)
        elif extops != 'extrpt':
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            if extops == 'extchk':
                ssh.stdin.write("info " + extname + " showch debug")
            elif extops == 'extstats':
                ssh.stdin.write("stats extract " + extname + '\n')
            elif extops == 'extstartdef':
                ssh.stdin.write("start extract " + extname + '\n')
            elif extops == 'extstartatcsn':
                extatcsn = data['extatcsn']
                ssh.stdin.write("start " + extname + " atcsn " + str(extatcsn))
            elif extops == 'extstartaftercsn':
                extaftercsn = data['extaftercsn']
                ssh.stdin.write("start " + extname + " aftercsn " + str(extaftercsn))
            elif extops == 'extstop':
                ssh.stdin.write("stop extract " + extname + '\n')
            elif extops == 'extforcestop':
                ssh.stdin.write("send extract " + extname + ' forcestop' + '\n')
            elif extops == 'extkill':
                ssh.stdin.write("kill extract " + extname + '\n')
            elif extops == 'extstatus':
                ssh.stdin.write("send extract " + extname + " status" + '\n')
            elif extops == 'extdel':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("delete extract " + extname + '\n')
            elif extops == 'pmpdel':
                ssh.stdin.write("delete extract " + extname + '\n')
            elif extops == 'upgie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("info " + extname)
                InfoExt, stderr = ssh.communicate()
                if 'Integrated' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Integrated Mode !! STOP !!')
                elif 'Oracle Redo Logs' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin],
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True,
                                           bufsize=1)
                    ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                    LoginErr, stderr = ssh.communicate()
                    if "ERROR" in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin],
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT,
                                               universal_newlines=True,
                                               bufsize=1)
                        ssh.stdin.write("send extract " + extname + " tranlogoptions PREPAREFORUPGRADETOIE" + "\n")
                        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                        ssh.stdin.write("stop extract " + extname + "\n")
                        time.sleep(60)
                        ssh.stdin.write("info extract " + extname + "\n")
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write("info extract " + extname + "\n")
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write("register extract " + extname + " database" + "\n")
                        RegErr = ssh.stdout.readline()
                        if "ERROR" in RegErr and "already registered" not in RegErr:
                            ExtErrPrint.append(RegErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(RegErr)
                            ssh.stdin.write("start extract " + extname + "\n")
                            time.sleep(60)
                            ssh.stdin.write("info extract " + extname + " upgrade" + "\n")
                            ssh.stdin.flush()
                        while True:
                            upg_Output = ssh.stdout.readline()
                            if 'ERROR' in upg_Output:
                                time.sleep(60)
                                ssh.stdin.write("info extract " + extname + " upgrade " + "\n")
                                ssh.stdout.flush()
                            elif 'capture.' in upg_Output:
                                break
                        ssh.stdin.write("start extract " + extname + "\n")
            elif extops == 'dwnie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("info " + extname)
                InfoExt, stderr = ssh.communicate()
                if 'Oracle Redo Logs' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Classic Mode !! STOP !!')
                elif 'Integrated' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin],
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True,
                                           bufsize=1)
                    ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                    LoginErr, stderr = ssh.communicate()
                    if "ERROR" in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin],
                                               stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT,
                                               universal_newlines=True,
                                               bufsize=1)
                        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                        ssh.stdin.write("stop extract " + extname + "\n")
                        time.sleep(60)
                        ssh.stdin.write("info extract " + extname + "\n")
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write("info extract " + extname + "\n")
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write("info " + extname + " downgrade" + "\n")
                        InfoIEErr = ssh.stdout.readline()
                        if "ready to be downgraded" not in InfoIEErr:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.stdin.write("alter extract " + extname + " downgrade integrated tranlog" + "\n")
                            ssh.stdin.write("info extract " + extname + "\n")
                            ssh.stdin.flush()
                        while True:
                            dwn_Output = ssh.stdout.readline()
                            if 'ERROR' in dwn_Output:
                                ssh.stdin.write("info extract " + extname + "\n")
                                ssh.stdout.flush()
                            elif 'Oracle Redo Logs' in dwn_Output:
                                break
                        ssh.stdin.write("unregister extract " + extname + " database" + "\n")
                        ssh.stdin.write("start extract " + extname + "\n")
            elif extops == 'extetroll':
                ssh.stdin.write("alter extract " + extname + " etrollover" + "\n")
            elif extops == 'extbegin':
                beginmode = data['beginmode']
                if beginmode == 'Now':
                    ssh.stdin.write("alter extract " + extname + ",begin now"  '\n')
                elif beginmode == 'Time':
                    domain = data['domain']
                    alias = data['alias']
                    ctvalue = data['ctvalue']
                    ctvalue = ctvalue.replace('T', ' ')
                    ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                    ssh.stdin.write("alter extract " + extname + ",begin " + ctvalue + '\n')
                elif beginmode == 'SCN':
                    domain = data['domain']
                    alias = data['alias']
                    scnvalue = data['scnvalue']
                    ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                    ssh.stdin.write("alter extract " + extname + ",scn " + str(scnvalue) + '\n')
                elif beginmode == 'pmpextseqno':
                    seqnovalue = data['seqnovalue']
                    rbavalue = data['rbavalue']
                    ssh.stdin.write(
                        "alter extract " + extname + ",extseqno " + str(seqnovalue) + ',extrba ' + str(rbavalue) + '\n')
            elif extops == 'exttraildel':
                trailname = data['trailname']
                for name in trailname:
                    ssh.stdin.write('delete exttrail ' + name + ', Extract ' + extname + '\n')
            elif extops == 'exttrailadd':
                trailname = data['trailname']
                trailtype = data['trailtype']
                trailsize = data['trailsize']
                ssh.stdin.write('add ' + trailtype + ' ' + trailname + ', Extract ' + extname + ',megabytes ' + str(
                    trailsize) + '\n')
            elif extops == 'cachemgr':
                ssh.stdin.write("send extract " + extname + " cachemgr cachestats" + "\n")
            elif extops == 'extunreg':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("unregister extract " + extname + " database" + "\n")
            elif extops == 'extedit':
                extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
                with open(extPrm, 'r') as extPrmFile:
                    prmfile = extPrmFile.read()
            chkExt, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            if extops == 'extstats':
                with open(os.path.join(oneplace_home, 'extStats'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(oneplace_home, 'extStats')) as extErrFile:
                    copy = False
                    rateCopy = False
                    for line in extErrFile:
                        if line.startswith('Extracting'):
                            TabName = line.split()[2]
                            ExtProcStats[TabName] = {}
                        elif '*** Latest' in line:
                            copy = True
                        elif line.startswith('End'):
                            copy = False
                        elif copy:
                            print(line)
                            if not line.strip().startswith('No'):
                                OpNameFinal = ''
                                OpName = line.strip().split()[0:-1]
                                if len(OpName) > 0:
                                    for Op in OpName:
                                        print(Op)
                                        OpNameFinal = OpNameFinal + Op
                                    OpNameFinal = OpNameFinal.lstrip()
                                    Oper = line.split()[-1]
                                    ExtProcStats[TabName].update({OpNameFinal: Oper})
                print(ExtProcStats)
            else:
                with open(os.path.join(oneplace_home, 'ChkExt.lst'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(oneplace_home, 'ChkExt.lst'), 'r') as extErrFile:
                    extErrFile = extErrFile.readlines()[8:]
                    for line in extErrFile:
                        if 'GGSCI' in line:
                            line = line.split('>', 1)[-1]
                            ExtErrPrint.append(line)
                        else:
                            ExtErrPrint.append(line)
        return [ExtErrPrint, prmfile, ExtProcStats]


class ggRepOps(Resource):
    def post(self):
        data = request.get_json(force=True)
        repops = data['repops']
        repname = data['repname']
        RepErrPrint = []
        prmFile = ''
        if repops == 'reprpt':
            for name in glob.glob(os.path.join(gg_home, 'dirrpt', '*.rpt')):
                name = name.split('/')[-1]
                if re.match(name, repname + '.rpt', re.IGNORECASE):
                    dest_file = os.path.join(gg_home, 'dirrpt', name)
                    with open(dest_file, 'r') as repErrFile:
                        for line in repErrFile:
                            RepErrPrint.append(line)
        elif repops != 'reprpt':
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            if repops == 'repchk':
                ssh.stdin.write("info " + repname + " showch debug")
            elif repops == 'repstats':
                ssh.stdin.write("stats replicat " + repname + '\n')
            elif repops == 'repstartdef':
                ssh.stdin.write("start replicat " + repname + '\n')
            elif repops == 'repskiptrans':
                ssh.stdin.write("start replicat " + repname + ' SKIPTRANSACTION' + '\n')
            elif repops == 'repnofilterdup':
                ssh.stdin.write("start replicat " + repname + ' NOFILTERDUPTRANSACTIONS' + '\n')
            elif repops == 'repatcsn':
                repatcsn = data['repatcsn']
                ssh.stdin.write("start replicat " + repname + ' ATCSN ' + str(repatcsn) + '\n')
            elif repops == 'repaftercsn':
                repaftercsn = data['repaftercsn']
                ssh.stdin.write("start replicat " + repname + ' AFTERCSN ' + str(repaftercsn) + '\n')
            elif repops == 'repstop':
                ssh.stdin.write("stop replicat " + repname + '\n')
            elif repops == 'repforcestop':
                ssh.stdin.write("send replicat " + repname + ' forcestop' + '\n')
            elif repops == 'repkill':
                ssh.stdin.write("kill replicat " + repname + '\n')
            elif repops == 'repdel':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("delete replicat " + repname + '\n')
            elif repops == 'upgir':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("alter replicat " + repname + ",integrated" + '\n')
            elif repops == 'dwnir':
                domain = data['domain']
                alias = data['alias']
                chktbl = data['chktbl']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                ssh.stdin.write("alter replicat " + repname + " nonintegrated ,CHECKPOINTTABLE " + chktbl + '\n')
            elif repops == 'repbegin':
                domain = data['domain']
                alias = data['alias']
                beginmode = data['beginmode']
                ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
                if beginmode == 'Now':
                    ssh.stdin.write("alter replicat " + repname + ",begin now"  '\n')
                elif beginmode == 'Time':
                    ctvalue = data['ctvalue']
                    ssh.stdin.write("alter replicat " + repname + ",begin " + ctvalue + '\n')
                elif beginmode == 'LOC':
                    seqnovalue = data['seqnovalue']
                    rbavalue = data['rbavalue']
                    ssh.stdin.write("alter replicat " + repname + ",extseqno " + str(seqnovalue) + ',extrba ' + str(
                        rbavalue) + '\n')
            elif repops == 'repedit':
                repPrm = os.path.join(gg_home, 'dirprm', repname + '.prm')
                with open(repPrm, 'r') as repPrmFile:
                    prmFile = repPrmFile.read()
            chkRep, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            with open(oneplace_home + '/ChkRep.lst', 'w') as repChkFileIn:
                repChkFileIn.write(chkRep)
            with open(oneplace_home + '/ChkRep.lst', 'r') as repErrFile:
                repErrFile = repErrFile.readlines()[8:]
                for line in repErrFile:
                    if 'GGSCI' in line:
                        line = line.split('>', 1)[-1]
                        RepErrPrint.append(line)
                    else:
                        RepErrPrint.append(line)

        return [RepErrPrint, prmFile]


class ggMgrOps(Resource):
    def post(self):
        data = request.get_json(force=True)
        mgrOps = data['mgrOps']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        if mgrOps == 'mgrstart':
            ssh.stdin.write("start manager")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrstop':
            ssh.stdin.write("stop manager!")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrrefresh':
            ssh.stdin.write("refresh manager")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrkill':
            ssh.stdin.write("kill manager")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrchildstatus':
            ssh.stdin.write("send manager childstatus debug")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrportinfo':
            ssh.stdin.write("send manager GETPORTINFO detail")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrpurgeold':
            ssh.stdin.write("send manager GETPURGEOLDEXTRACTS detail")
            mgrOps, stderr = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        with open(oneplace_home + '/MgrOps.lst', 'w') as mgrFileIn:
            mgrFileIn.write(mgrOps)
        with open(oneplace_home + '/MgrOps.lst', 'r') as mgrFileOut:
            MgrOpsPrint = []
            extErrFile = mgrFileOut.readlines()[8:]
            for line in extErrFile:
                if 'GGSCI' in line:
                    line = line.split('>', 1)[-1]
                    MgrOpsPrint.append(line)
                else:
                    MgrOpsPrint.append(line)

        return [MgrOpsPrint]


class ggExtShowTrans(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("SEND EXTRACT " + extname + " SHOWTRANS TABULAR " + "\n")
        extShowTrans, stderr = ssh.communicate()
        ssh.kill()
        ssh.stdin.close()
        with open(oneplace_home + '/ExtShowTrans.lst', 'w') as ExtShowTransFileIn:
            ExtShowTransFileIn.write(extShowTrans)
        with open(oneplace_home + '/ExtShowTrans.lst', 'r') as ExtShowTransFileOut:
            ExtShowTransPrint = []
            copy = False
            for line in ExtShowTransFileOut:
                line = line.strip()
                if len(line) > 0 and not line.startswith('-'):
                    if 'ERROR' in line:
                        line = line.split('>', 1)[-1]
                        ExtShowTransPrint.append(line)
                        ExtShowTransPrint_df = ExtShowTransPrint
                    else:
                        if line.startswith('XID'):
                            copy = True
                            continue
                        elif line.startswith('GGSCI'):
                            copy = False
                            continue
                        elif copy:
                            line = line.split()
                            ExtShowTransPrint.append(line)
                        ExtShowTransPrint_df = pd.DataFrame(ExtShowTransPrint,
                                                            columns=['XID', 'Items', 'Extract', 'Redo Thread',
                                                                     'Start Time', 'SCN', 'Redo Seq', 'Redo RBA',
                                                                     'Status'])
                        ExtShowTransPrint_df = ExtShowTransPrint_df.to_dict('records')

        return [ExtShowTransPrint_df]


class ggExtSkipTrans(Resource):
    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        xid = data['xid']
        xid = xid.lstrip('["').rstrip('"]')
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("SEND EXTRACT " + extname + " SKIPTRANS " + xid + " FORCE" + "\n")
        extSkipTrans, stderr = ssh.communicate()
        ssh.kill()
        ssh.stdin.close()
        with open(oneplace_home + '/ExtSkipTrans.lst', 'w') as ExtSkipTransFileIn:
            ExtSkipTransFileIn.write(extSkipTrans)
        with open(oneplace_home + '/ExtSkipTrans.lst', 'r') as ExtSkipTransFileOut:
            ExtSkipTransPrint = []
            for line in ExtSkipTransFileOut:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ExtSkipTransPrint.append(line)
                elif 'skipped' in line:
                    line = line.split('>', 1)[-1]
                    ExtSkipTransPrint.append(line)
                elif 'not found' in line:
                    line = line.split('>', 1)[-1]
                    ExtSkipTransPrint.append(line)

        return [ExtSkipTransPrint]


class ggAddReplicat(Resource):
    def post(self):
        data = request.get_json(force=True)
        repname = data['repname']
        domain = data['domain']
        alias = data['alias']
        repmode = data['repmode']
        beginmode = data['beginmode']
        trail = data['trail']
        chkpttbl = data['chkpttbl']
        currentParamList = data['currentParamList']
        startRepChk = data['startRepChk']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddRep_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddRep_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            ssh.stdin.write(
                "add replicat " + repname + " " + repmode + " exttrail " + trail + " , checkpointtable " + chkpttbl + "\n")
            AddRepErr, stderr = ssh.communicate()
            if "ERROR" in AddRepErr:
                AddRep_Out.append(AddRepErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                repPrm = os.path.join(gg_home, 'dirprm', repname + '.prm')
                with open(repPrm, 'w') as repFile:
                    repFile.write(currentParamList)
                AddRep_Out.append(AddRepErr)
                if startRepChk is False:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                    ssh.stdin.write("start replicat " + repname)
                    StartRepErr, stderr = ssh.communicate()
                    AddRep_Out.append(StartRepErr)
        with open(oneplace_home + '/AddRepErr.lst', 'w') as repErrFileIn:
            for listline in AddRep_Out:
                repErrFileIn.write(listline)
        with open(oneplace_home + '/AddRepErr.lst', 'r') as repErrFile:
            RepErrPrint = []
            for line in repErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    RepErrPrint.append(line)
                elif 'added.' in line:
                    line = line.split('>', 1)[-1]
                    RepErrPrint.append(line)
                elif 'starting' in line:
                    line = line.split('>', 1)[-1]
                    RepErrPrint.append(line)
        return [RepErrPrint]


class cdbCheck(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        msg = {}
        try:
            val = selectConn(dbname)
            con = val[0]
            schema_list = "select distinct trim(owner) username from  systables"
            schema_data_fetch = pd.read_sql_query(schema_list, con)
            schema_data_fetch = schema_data_fetch.to_dict('records')
            print(schema_data_fetch)
            cursor = con.cursor()
            cursor.execute('''select trim(dbinfo('dbname')),dbinfo('version','full') FROM systables WHERE tabid = 1''')
            dbName = cursor.fetchone()
            print(dbName)
            if dbName:
                msg['DBNAME'] = dbName[0]
                msg['ProductName'] = dbName[1]
            print(msg)
        except Exception as e:
            schema_data_fetch = str(e)
            print(str(e))
        finally:
            if con:
                con.close()
        return [schema_data_fetch, msg]


class lmDictDet(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        db_main_ver = val[1]
        cdb_check = 'NO'
        pdb_name_fetch = ''
        if int(db_main_ver) > 11:
            capture_name = """SELECT CLIENT_NAME FROM cdb_capture"""
            capture_name_fetch = pd.read_sql_query(capture_name, con)
        else:
            capture_name = """SELECT CLIENT_NAME FROM dba_capture"""
            capture_name_fetch = pd.read_sql_query(capture_name, con)
        dict_det = """SELECT first_change# FIRST_CHANGE,FIRST_TIME
                      FROM v$archived_log 
                      WHERE dictionary_begin = 'YES' AND 
                            standby_dest = 'NO' AND
                            name IS NOT NULL AND 
                            status = 'A'"""
        dict_det_fetch = pd.read_sql_query(dict_det, con)
        dict_det_fetch = dict_det_fetch.astype(str)

        return [capture_name_fetch.to_dict('records'), dict_det_fetch.to_dict('records')]


class tableList(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        gatherMeta = data['gatherMeta']
        tgt_dep_url = data['tgtDepURL']
        if gatherMeta == True:
            LoadName = data['LoadName']
        else:
            LoadName = ''
        val = selectConn(dbname)
        con = val[0]
        autoQualifySplit = []
        table_fetch = ''
        try:
            cursor = con.cursor()
            cursor.outputtypehandler = output_type_handler
            i = 1
            bindNames = ','.join(':%d' % i for i in range(len(schemaList)))
            schemas = []
            if LoadName:
                os.umask(0)
                if not os.path.exists(os.path.join(oneplace_home, LoadName)): os.makedirs(
                    os.path.join(oneplace_home, LoadName), mode=0o777)
            for schema in schemaList:
                schemas.append(schema)
                cursor.execute(
                    "select owner,tabname,nrows,nrows*rowsize tablesize,tabtype  from SYSTABLES where tabtype='T'  and owner = ?",
                    (schema,))
                table_fetch = cursor.fetchall()
                df = pd.DataFrame(table_fetch)
                df.to_csv(os.path.join(oneplace_home, LoadName, LoadName + '_' + schema + '.csv'),
                          header=['owner', 'table_name', 'count', 'tablesize', 'table_type_str'])
                counter = 0
                tot_tab_size = 0
                for row in table_fetch:
                    if gatherMeta is True:
                        tableMetadata = """SELECT a.cname,a.tname,a.coltype,a.length width,a.syslength,a.nulls NN,a.in_primary_key,a.default_value,a.column_kind,a.remarks FROM sys.syscolumns a where a.tname = :table_name """
                        param = {"table_name": str(row[1])}
                        tableMetadata_fetch = pd.read_sql_query(tableMetadata, con, params=[param["table_name"]])
                        tableMetadata_fetch['cname'] = tableMetadata_fetch['cname'].replace(['window','offset'],['window_name','offset_to'])
                        tableMetadata_fetch['coltype'] = tableMetadata_fetch['coltype'].replace(
                            ['integer', 'binary', 'binary varying', 'bit', 'datetime', 'datetimeoffset', 'float',
                             'image', 'long binary', 'long bit varying', 'long nvarchar', 'long varbit', 'long varchar',
                             'nchar', 'ntext', 'nvarchar', 'smalldatetime', 'smallmoney', 'uniqueidentifier',
                             'uniqueidentifierstr', 'unsigned bigint', 'unsigned int', 'unsigned smallint',
                             'unsigned tinyint', 'varbinary', 'tinyint','double'],
                            ['int', 'bytea', 'bytea', 'bit', 'timestamp', 'timestamp with time zone',
                             'double precision', 'bytea', 'bytea', 'bytea', 'text', 'bytea', 'text', 'char', 'text',
                             'varchar', 'timestamp', 'money', 'uuid', 'char(16)', 'numeric(20)', 'numeric(10)',
                             'numeric(5)', 'numeric(3)', 'bytea', 'smallint','double precision'])
                        tableMetadata_fetch['default_value'] = tableMetadata_fetch['default_value'].replace(
                            ['current timestamp', 'timestamp'], 'current_timestamp')
                        collist = ''
                        pkList = []
                        for idx, line in tableMetadata_fetch.iterrows():
                            if line['coltype'] == 'int' or line['coltype'] == 'smallint' or line[ 'coltype'] == 'bytea' or line[ 'coltype'] == 'date' or line['coltype'] == 'text' or line['coltype'] == 'boolean' or \
                                    line['coltype'] == 'bigint' or line['coltype'] == 'uuid' or line[
                                'coltype'] == 'timestamp' or line['coltype'] == 'money' or line[
                                'coltype'] == 'timestamp with time zone' or line['coltype'] == 'numeric(20)' or line[
                                'coltype'] == 'numeric(10)' or line['coltype'] == 'numeric(5)' or line[
                                'coltype'] == 'numeric(3)' or line['coltype'] == 'numeric' or line['coltype'] == 'bit' or line[ 'coltype'] == 'timestamp' or line['coltype'] == 'decimal' or line['coltype'] == 'double precision' or  line['coltype'] == 'xml' or line['coltype'] == 'varchar' or line['coltype'] == 'text' or line['coltype'] == 'uuid':
                                if line['default_value'] == 'autoincrement' and line['coltype'] == 'smallint' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + 'smallserial,'
                                elif line['coltype'] == 'smallint' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif line['coltype'] == 'smallint' and line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                                elif line['default_value'] == 'autoincrement' and line['coltype'] == 'bigint' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + 'bigserial,'
                                elif line['coltype'] == 'bigint' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif line['coltype'] == 'bigint' and line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                                elif line['default_value'] == 'autoincrement' and line['coltype'] == 'int' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + 'serial,'
                                elif line['coltype'] == 'int' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif line['coltype'] == 'int' and line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                                elif line['coltype'] == 'uuid' and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif line['coltype'] == 'uuid' and line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                                elif line['default_value'] == 'autoincrement' and line['coltype'] == 'numeric':
                                    collist = collist + line['cname'] + '  ' + 'serial,'
                                elif line['default_value'] == 'autoincrement' and line['coltype'] == 'decimal' :
                                     collist = collist + line['cname'] + '  ' + 'serial,'
                                elif line['coltype'] == 'double precision':
                                     collist = collist + line['cname'] + '  ' +  line['coltype'] + ','
                                elif line['coltype'] == 'xml':
                                     collist = collist + line['cname'] + '  ' +  line['coltype'] + ','
                                elif line['coltype'] == 'text':
                                     collist = collist + line['cname'] + '  ' +  line['coltype'] + ','
                                elif line['coltype'] == 'varchar' :
                                    if line['default_value'] == 'autoincrement':
                                       collist = collist + line['cname'] + '  ' + 'serial,'
                                    elif line['NN'] == 'N':
                                       collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ') NOT NULL ,'
                                    elif line['NN'] == 'Y':
                                       collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + '),'
                                elif line['coltype'] == 'bit':
                                    if line['NN'] == 'N' and line['default_value']:
                                        collist = collist + line['cname'] + ' ' + line['coltype'] + '  ' + ' default ' + line['default_value'] + "::bit" + ' not null' + ","
                                    elif line['NN'] == 'N':
                                       collist = collist + line['cname'] + ' ' + line['coltype'] + '  ' + 'not null' + ','
                                    elif line['NN'] == 'Y' and line['default_value']:
                                       collist = collist + line['cname'] + ' ' + line['coltype'] + ' default ' +  line['default_value'] + "::bit" + ","
                                    elif line['NN'] == 'Y' :
                                        collist = collist + line['cname'] + ' ' + line['coltype'] + ','
                                elif line['coltype'] == 'date' or line['coltype'] == 'timestamp':
                                    if line['default_value'] == 'current date':
                                        collist = collist + line['cname'] + ' ' + line['coltype'] + ' default ' + 'CURRENT_DATE,'
                                    else:
                                        collist = collist + line['cname'] + ' ' + line['coltype']  + ','
                                elif (line['coltype'] == 'numeric(10)' or line['coltype'] == 'numeric(20)' or line['coltype'] == 'numeric(5)' or line['coltype'] == 'numeric(3)')  and line['default_value'] == 'autoincrement':
                                    collist = collist + line['cname'] + '  ' + 'serial,'
                                elif (line['coltype'] == 'numeric(10)' or line['coltype'] == 'numeric(20)' or line['coltype'] == 'numeric(5)' or line['coltype'] == 'numeric(3)' or line['coltype'] == 'bytea' or  line['coltype'] == 'timestamp with time zone') and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif (line['coltype'] == 'numeric(10)' or line['coltype'] == 'numeric(20)' or line['coltype'] == 'numeric(5)' or line['coltype'] == 'numeric(3)' or line['coltype'] == 'bytea' or line['coltype'] == 'timestamp with time zone') and line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                                elif line['default_value'] and line['NN'] == 'N':
                                    collist = collist + line['cname'] + ' ' + line['coltype'] + ' NOT NULL default ' + line['default_value'] + ','
                                elif int(line['syslength']) == 0:
                                    print(line['tname'],line['cname'] , line['coltype'] , 'Inside syslength = 0' )
                                    if line['NN'] == 'N':
                                        collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ') NOT NULL,'
                                    else:
                                        collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + '),'
                                elif int(line['syslength']) != 0:
                                    print(line['tname'],line['cname'] , line['coltype'] , 'Inside syslength != 0 ')
                                    if line['NN'] == 'N':
                                        collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ',' + str(line['syslength']) + ') NOT NULL,'
                                    else:
                                        collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ',' + str(line['syslength']) + '),'
                                elif line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ' NOT NULL,'
                                elif line['NN'] == 'Y':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + ','
                            else:
                                if line['default_value'] and line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ') NOT NULL default ' + line['default_value'] + ','
                                elif line['NN'] == 'N':
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + ') NOT NULL ,'
                                else:
                                    collist = collist + line['cname'] + '  ' + line['coltype'] + '(' + str(line['width']) + '),'
                            if line['in_primary_key'] == 'Y':
                                pkList.append(line['cname'])
                            if re.match(r'^\d', line['tname']):
                               tabName = schema + '.' + '"' +  line['tname'] + '"'
                            else:
                               tabName = schema + '.' + line['tname']
                        pkStmt = ''
                        for name in pkList:
                            pkStmt = pkStmt + name + ','
                        pkStmt = pkStmt.rstrip(',')
                        collist = collist.rstrip(',')
                        if len(pkList) > 0:
                            createStmt = 'create table IF NOT EXISTS ' + tabName + '(' + collist + ',primary key(' + pkStmt + '))'
                        else:
                            createStmt = 'create table IF NOT EXISTS ' + tabName + '(' + collist + ')'
                        fileName = 'SQLAnyMetaData~' + str(row[0]) + '~' + str(row[1])
                        with open(os.path.join(oneplace_home, LoadName, fileName), 'w') as infile:
                            pass
                        dep_url = tgt_dep_url + '/writemetadatafile'
                        headers = {"Content-Type": "application/json"}
                        payload = {"jobName": LoadName, "fileName": fileName, "content": createStmt, "tabName": tabName}
                        r = requests.post(dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        except cx_Oracle.DatabaseError as e:
            logger.info(str(e))
            tableNameList.append(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [table_fetch, gg_home, autoQualifySplit]


class MetaDatafile(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        tabName = data['tabName']
        try:
            tabName = tabName.split('.')
            tabOwner = tabName[0]
            tableName = tabName[1]
            if os.path.exists(os.path.join(oneplace_home, jobName, 'SQLAnyMetaData~' + tabOwner + '~' + tableName)):
                response = make_response(
                    send_file(os.path.join(oneplace_home, jobName, 'SQLAnyMetaData~' + tabOwner + '~' + tableName),
                              as_attachment=True))
        except:
            pass
        return response


class writeMetaDataFile(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        fileName = data['fileName']
        content = data['content']
        if not os.path.exists(os.path.join(oneplace_home, jobName)): os.makedirs(os.path.join(oneplace_home, jobName))
        with open(os.path.join(oneplace_home, jobName, fileName), 'w') as infile:
            infile.write(content)


class ApplyMetadata(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        dep_url = data['dep_url']
        val = selectConn(dbname)
        con = val[0]
        cursor = con.cursor()
        TableCreate = []
        try:
            dep_url = dep_url + '/metadatafile'
            r = requests.get(dep_url)
            with open(os.path.join(oneplace_home, "metadata.sql"), 'wb') as metadata:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        metadata.write(chunk)
            with open(os.path.join(oneplace_home, "metadata.sql"), 'r') as infile:
                for line in infile:
                    try:
                        cursor.execute(line)
                        TableCreate.append({'TabName': line.split()[2], 'msg': 'Successfully Created'})
                    except cx_Oracle.DatabaseError as e:
                        TableCreate.append({'TabName': line.split()[2], 'msg': str(e)})
        except requests.exceptions.ConnectionError as e:
            TableCreate.append({'TabName': 'Source Dep not Reachable', 'msg': str(e)})
        finally:
            if con:
                cursor.close()
                con.close()
        return [TableCreate]


class suppLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        dbver = val[1]
        dbminver = val[2]
        cdb_check = 'NO'
        result = ''
        if 'ORA-' in dbver:
            result = dbver
        else:
            try:
                if int(dbver) == 11 and int(dbminver) == 4:
                    db_param = """select value from v$parameter where name='enable_goldengate_replication'"""
                    supp_log = '''select LOG_MODE,SUPPLEMENTAL_LOG_DATA_MIN,SUPPLEMENTAL_LOG_DATA_PK,SUPPLEMENTAL_LOG_DATA_UI,
                             SUPPLEMENTAL_LOG_DATA_FK,SUPPLEMENTAL_LOG_DATA_ALL,DB_UNIQUE_NAME,FORCE_LOGGING, from v$database'''
                elif int(dbver) > 11:
                    cdb_check = '''SELECT CDB from v$database'''
                    cdb_check_fetch = pd.read_sql_query(cdb_check, con)
                    cdb_check = cdb_check_fetch.to_dict('records')
                    cdb_check = cdb_check[0]['CDB']
                    db_param = """select value from v$parameter where name='enable_goldengate_replication'"""
                    supp_log = '''select LOG_MODE,SUPPLEMENTAL_LOG_DATA_MIN,SUPPLEMENTAL_LOG_DATA_PK,SUPPLEMENTAL_LOG_DATA_UI,
                             SUPPLEMENTAL_LOG_DATA_FK,SUPPLEMENTAL_LOG_DATA_ALL,DB_UNIQUE_NAME,FORCE_LOGGING from v$database'''
                else:
                    db_param = """select 'TRUE' value from dual"""
                    supp_log = '''select LOG_MODE,SUPPLEMENTAL_LOG_DATA_MIN,SUPPLEMENTAL_LOG_DATA_PK,SUPPLEMENTAL_LOG_DATA_UI,
                             SUPPLEMENTAL_LOG_DATA_FK,SUPPLEMENTAL_LOG_DATA_ALL,DB_UNIQUE_NAME,FORCE_LOGGING from v$database'''
                supp_data_fetch = pd.read_sql_query(supp_log, con)
                db_param_fetch = pd.read_sql_query(db_param, con)
                result = pd.concat([supp_data_fetch, db_param_fetch], axis=1)
                result = result.to_dict('records')
            except cx_Oracle.DatabaseError as e:
                result = str(e)
            finally:
                if con:
                    con.close()
        return [result, cdb_check]


class suppLogSchema(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        pdbName = data['pdbName']
        cdbCheck = data['cdbCheck']
        val = selectConn(dbname)
        con = val[0]
        dbver = val[1]
        dbminver = val[2]
        schema_data_fetch = ''
        if 'ORA-' in dbver:
            schema_data_fetch = dbver
        else:
            try:
                if cdbCheck == 'YES' and len(pdbName) > 0:
                    cursor = con.cursor()
                    cursor.execute('''alter session set container=''' + pdbName)
                    schema_list = """select username from  all_users
                            where username not in('SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS','ANONYMOUS','DBSFWUSER','SI_INFORMTN_SCHEMA',
                         'CTXSYS','AUDSYS','OJVMSYS','REMOTE_SCHEDULER_AGENT','GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS','LBACSYS','OUTLN','XDB',
                         'WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG','SYSRAC','SYSKM','SYSBACKUP','MDDATA','GGSYS' ,
                         'GSMCATUSER','XS$NULL','PDBADMIN','DIP','SYS$UMF')"""
                    schema_data_fetch = pd.read_sql_query(schema_list, con)
                    schema_data_fetch = schema_data_fetch.to_dict('records')
                else:
                    schema_list = """select username from  all_users
                            where username not in('SYS','SYSTEM','PUBLIC','ORACLE_OCM','DBSNMP','APPQOSSYS','ANONYMOUS','DBSFWUSER','SI_INFORMTN_SCHEMA',
                         'CTXSYS','AUDSYS','OJVMSYS','REMOTE_SCHEDULER_AGENT','GSMADMIN_INTERNAL','ORDPLUGINS','MDSYS','OLAPSYS','LBACSYS','OUTLN','XDB',
                         'WMSYS','DVF','ORDDATA','DVSYS','ORDSYS','SYSDG','SYSRAC','SYSKM','SYSBACKUP','MDDATA','GGSYS' ,
                         'GSMCATUSER','XS$NULL','PDBADMIN','DIP','SYS$UMF')"""
                    schema_data_fetch = pd.read_sql_query(schema_list, con)
                    schema_data_fetch = schema_data_fetch.to_dict('records')
            except cx_Oracle.DatabaseError as e:
                schema_data_fetch = str(e)
            finally:
                if con:
                    con.close()
        return [schema_data_fetch]


class xidDet(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        alias = data['alias']
        cdbCheck = data['cdbCheck']
        pdbList = data['pdbList']
        val = selectConn(alias)
        con = val[0]
        xid_det = []
        curr_time = ''
        first_scn_time = ''
        first_scn = ''
        xid_row = ''
        time_row = ''
        try:
            cursor = con.cursor()
            cursor.outputtypehandler = output_type_handler
            cursor.execute(
                """select to_char(scn_to_timestamp(first_scn),'mm/dd/yyyy hh24:mi:ss') from dba_capture where capture_name like '%%%s%%'""" % (
                    jobName))
            first_scn = cursor.fetchone()
            if cdbCheck == 'YES' and len(pdbList) > 0:
                cursor.execute('''alter session set container=''' + str(pdbList))
            cursor.execute(
                """select  INST_ID,XIDUSN,XIDSLOT,XIDSQN,min(START_TIME) start_time from gv$transaction group by INST_ID,XIDUSN,XIDSLOT,XIDSQN""")
            xid_row = cursor.fetchone()
            cursor.execute("""select to_char(systimestamp,'mm/dd/yyyy hh24:mi:ss') from dual""")
            time_row = cursor.fetchone()
            if first_scn:
                first_scn_time = first_scn[0]
            if xid_row:
                xid_det.append(
                    {'inst_id': xid_row[0], 'XIDUSN': xid_row[1], 'XIDSLOT': xid_row[2], 'XIDSQN': xid_row[3],
                     'start_time': xid_row[4]})
            if time_row:
                curr_time = time_row[0]
        except cx_Oracle.DatabaseError as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [xid_det, curr_time, first_scn_time]


class expDirs(Resource):
    def post(self):
        data = request.get_json(force=True)
        alias = data['alias']
        cdbCheck = data['cdbCheck']
        pdbList = data['pdbList']
        val = selectConn(alias)
        con = val[0]
        dir_name_fetch = []
        xid_det = []
        curr_time = ''
        try:
            cursor = con.cursor()
            cursor.outputtypehandler = output_type_handler
            if cdbCheck == 'YES' and len(pdbList) > 0:
                cursor.execute('''alter session set container=''' + str(pdbList))
                cursor.execute("""select directory_name from all_directories""")
                dir_row = cursor.fetchall()
            else:
                cursor.execute("""select directory_name from all_directories""")
                dir_row = cursor.fetchall()
            if dir_row:
                for name in dir_row:
                    dir_name_fetch.append(name[0])
        except cx_Oracle.DatabaseError as e:
            dir_name_fetch = str(e)
        finally:
            if con:
                cursor.close()
                con.close()
        return [dir_name_fetch]


class expDP(Resource):
    def post(self):
        data = request.get_json(force=True)
        srcDep = data['srcDep']
        tgtDep = data['tgtDep']
        srcdbName = data['srcdbName']
        exp_jobName = data['jobName']
        exp_logFile = exp_jobName + '_Export.log'
        schemas = data['schemas']
        exp_dirName = data['srcDirName']
        exp_dumpfile = exp_jobName + '%U.dmp'
        exp_parallel = data['expParallel']
        exp_contentOpt = data['contentOpt']
        exp_compOpt = data['compOpt']
        exp_compAlgo = data['compAlgo']
        tgtdbName = data['tgtdbName']
        imp_dirName = data['tgtDirName']
        imp_parallel = data['impParallel']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        tabExclude = data['tabExclude']
        remapSchema = data['remapSchema']
        reMapSchemaNameListDisp = data['reMapSchemaNameListDisp']
        remapTgtSchemaNames = data['remapTgtSchemaNames']
        remapTableSpaces = data['remapTableSpaces']
        reMapTablespaceListDisp = data['reMapTablespaceListDisp']
        remapTgtTableSpaceNames = data['remapTgtTableSpaceNames']
        exp_schema = ''
        expdpMon_fetch = []
        if not os.path.exists(os.path.join(oneplace_home, exp_jobName)): os.makedirs(
            os.path.join(oneplace_home, exp_jobName))
        for name in schemas:
            exp_schema = exp_schema + "''" + name + "'',"
        exp_schema = exp_schema.rstrip(',')
        with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_Schemas'), 'w') as infile:
            infile.write(exp_schema)
        with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_impParallel'), 'w') as infile:
            infile.write(imp_parallel)
        if remapSchema == 'yes':
            SRC_Remap_Schemas = ''
            for name in reMapSchemaNameListDisp:
                SRC_Remap_Schemas = SRC_Remap_Schemas + name + ','
            SRC_Remap_Schemas = SRC_Remap_Schemas.rstrip(',')
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_SRC_Remap_Schemas'), 'w') as infile:
                infile.write(SRC_Remap_Schemas)
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_TGT_Remap_Schemas'), 'w') as infile:
                infile.write(remapTgtSchemaNames)
        if remapTableSpaces == 'yes':
            SRC_Remap_Tablespaces = ''
            for name in reMapTablespaceListDisp:
                SRC_Remap_Tablespaces = SRC_Remap_Tablespaces + name + ','
            SRC_Remap_Tablespaces = SRC_Remap_Tablespaces.rstrip(',')
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_SRC_Remap_Tablespaces'), 'w') as infile:
                infile.write(SRC_Remap_Tablespaces)
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_TGT_Remap_Tablespaces'), 'w') as infile:
                infile.write(remapTgtTableSpaceNames)
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('select dep_url from ONEPCONN where dep=:dep', {"dep": srcDep})
            src_db_row = cursor.fetchone()
            if src_db_row:
                src_dep_url = src_db_row[0]
            cursor.execute('select dep_url from ONEPCONN where dep=:dep', {"dep": tgtDep})
            tgt_db_row = cursor.fetchone()
            if tgt_db_row:
                tgt_dep_url = tgt_db_row[0]
            cursor.close()
            conn.close()
            val = selectConn(srcdbName)
            DBconn = val[0]
            exp_jobOwner = val[3].upper()
            DBcursor = DBconn.cursor()
            if cdbCheck == 'YES' and len(pdbName) > 0:
                DBcursor.execute('''alter session set container=''' + str(pdbName))
            DBcursor.execute('''select dbms_flashback.get_system_change_number from dual''')
            db_row = DBcursor.fetchone()
            if db_row:
                flashback_scn = db_row[0]
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_flashbackscn'), 'w') as infile:
                infile.write(str(flashback_scn))
            expdpschema_cmd = """DECLARE
                       hdnl number; 
                       BEGIN 
                       hdnl := SYS.DBMS_DATAPUMP.OPEN('EXPORT','SCHEMA',NULL,:jobName);
                       SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :dumpfile, directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_dump_file,reusefile => 1); 
                       SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :logFile,directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_log_file);
                       SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'SCHEMA_EXPR','IN (""" + exp_schema + """)');
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'FLASHBACK_SCN',:flashback_scn);
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'INCLUDE_METADATA',:contentOpt);
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'COMPRESSION',:compOpt);
                       SYS.DBMS_DATAPUMP.SET_PARALLEL(hdnl,:parallel);
                       SYS.DBMS_DATAPUMP.START_JOB(hdnl);
                       END;"""
            expdptabexclude = """DECLARE
                       hdnl number; 
                       BEGIN 
                       hdnl := SYS.DBMS_DATAPUMP.OPEN('EXPORT','SCHEMA',NULL,:jobName);
                       SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :dumpfile, directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_dump_file,reusefile => 1); 
                       SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :logFile,directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_log_file);
                       SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'SCHEMA_EXPR','IN (""" + exp_schema + """)');
                       SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'NAME_EXPR','NOT IN(""" + tabExclude + """)', object_type => 'TABLE');
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'FLASHBACK_SCN',:flashback_scn);
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'INCLUDE_METADATA',:contentOpt);
                       SYS.DBMS_DATAPUMP.SET_PARAMETER(hdnl ,'COMPRESSION',:compOpt);
                       SYS.DBMS_DATAPUMP.SET_PARALLEL(hdnl,:parallel);
                       SYS.DBMS_DATAPUMP.START_JOB(hdnl);
                       END;"""
            if tabExclude:
                DBcursor.execute(expdptabexclude, jobName=exp_jobName, dirName=exp_dirName, dumpfile=exp_dumpfile,
                                 logFile=exp_logFile, flashback_scn=flashback_scn, contentOpt=exp_contentOpt,
                                 compOpt=exp_compOpt,
                                 parallel=exp_parallel)
            else:
                DBcursor.execute(expdpschema_cmd, jobName=exp_jobName, dirName=exp_dirName, dumpfile=exp_dumpfile,
                                 logFile=exp_logFile, flashback_scn=flashback_scn, contentOpt=exp_contentOpt,
                                 compOpt=exp_compOpt,
                                 parallel=exp_parallel)
            SRC_insert_expimp_url = src_dep_url + '/insertexpimp'
            TGT_insert_expimp_url = tgt_dep_url + '/insertexpimp'
            payload = {"srcDep": srcDep, "tgtDep": tgtDep, "srcdbName": srcdbName, "tgtdbName": tgtdbName,
                       "jobName": exp_jobName, "jobOwner": exp_jobOwner, "srcDumpDir": exp_dirName,
                       "tgtDumpDir": imp_dirName, "dumpFile": exp_dumpfile,
                       "cdbCheck": cdbCheck, "pdbName": pdbName, "reMapSchema": remapSchema,
                       "remapTablespace": remapTableSpaces}
            headers = {"Content-Type": "application/json"}
            r = requests.post(SRC_insert_expimp_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            r = requests.post(TGT_insert_expimp_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            startTime = datetime.now(timezone.utc)
            startTime = startTime.strftime('%Y-%m-%d:%H:%M:%S')
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_Stats'), 'w') as infile:
                infile.write(startTime)
            time.sleep(5)
        except cx_Oracle.DatabaseError as e:
            with open(os.path.join(oneplace_home, exp_jobName, exp_jobName + '_ExportOnDemand.log'), 'w') as infile:
                infile.write(str(e))
        finally:
            if DBconn:
                DBcursor.close()
                DBconn.close()


class insertExpImp(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobName = data['jobName']
        srcDep = data['srcDep']
        tgtDep = data['tgtDep']
        srcdbName = data['srcdbName']
        tgtdbName = data['tgtdbName']
        jobName = data['jobName']
        jobOwner = data['jobOwner']
        srcDumpDir = data['srcDumpDir']
        tgtDumpDir = data['tgtDumpDir']
        dumpFile = data['dumpFile']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        reMapSchema = data['reMapSchema']
        remapTablespace = data['remapTablespace']
        conn = sqlite3.connect('conn.db')
        sq_cursor = conn.cursor()
        sq_cursor.execute(
            '''insert into expimp(srcDep,tgtDep,srcdbName,tgtdbName,jobName,jobOwner,srcDumpDir,tgtDumpDir,dumpFile,cdbCheck,pdbName,reMapSchema,remapTablespace) values(:srcDep,:tgtDep,:srcdbName,:tgtdbName,:jobName,:jobOwner,:srcDumpDir,:tgtDumpDir,:dumpFile,:cdbCheck,:pdbName,:reMapSchema,:remapTablespace)''',
            {"srcDep": srcDep, "tgtDep": tgtDep, "srcdbName": srcdbName, "tgtdbName": tgtdbName, "jobName": jobName,
             "jobOwner": jobOwner, "srcDumpDir": srcDumpDir, "tgtDumpDir": tgtDumpDir, "dumpFile": dumpFile,
             "cdbCheck": cdbCheck, "pdbName": pdbName, "reMapSchema": reMapSchema,
             "remapTablespace": remapTablespace})
        conn.commit()
        sq_cursor.close()
        conn.close()


class updateExpImp(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobName = data['jobName']
        colName = data['colName']
        colValue = data['colValue']
        try:
            conn = sqlite3.connect('conn.db')
            sq_cursor = conn.cursor()
            upd_statement = '''update expimp set {0}=? where jobname=? and jobowner=?'''.format(colName)
            sq_cursor.execute(upd_statement, (colValue, jobName, jobOwner))
            conn.commit()
            sq_cursor.execute('''select * from expimp''')
        except Exception as e:
            logger.info(str(e))
        finally:
            if conn:
                sq_cursor.close()
                conn.close()


class impDP(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        src_dep_url = data['src_dep_url']
        tgtDep = data['tgtDep']
        tgtdbName = data['tgtdbName']
        tgtDirName = data['tgtDirName']
        dumpFile = data['dumpFile']
        reMapSchema = data['reMapSchema']
        remapTablespace = data['remapTablespace']
        imp_logFile = jobName + '_Import.log'
        remap_schema_clause = ''
        remap_tablespace_clause = ''
        readlog_dep_url = src_dep_url + '/readlog'
        payload = {"jobName": jobName, "log": '_Schemas'}
        headers = {"Content-Type": "application/json"}
        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        imp_schema = r.json()[0][0]
        readlog_dep_url = src_dep_url + '/readlog'
        payload = {"jobName": jobName, "log": '_impParallel'}
        headers = {"Content-Type": "application/json"}
        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        imp_parallel = r.json()[0][0]
        if reMapSchema == 'yes':
            readlog_dep_url = src_dep_url + '/readlog'
            payload = {"jobName": jobName, "log": '_SRC_Remap_Schemas'}
            headers = {"Content-Type": "application/json"}
            r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            SRC_Remap_Schemas = r.json()[0][0]
            SRC_Remap_Schemas = SRC_Remap_Schemas.split(',')
            readlog_dep_url = src_dep_url + '/readlog'
            payload = {"jobName": jobName, "log": '_TGT_Remap_Schemas'}
            headers = {"Content-Type": "application/json"}
            r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            TGT_Remap_Schemas = r.json()[0][0]
            TGT_Remap_Schemas = TGT_Remap_Schemas.split(',')
            for src in SRC_Remap_Schemas:
                for tgt in TGT_Remap_Schemas:
                    if SRC_Remap_Schemas.index(src) == TGT_Remap_Schemas.index(tgt):
                        remap_schema_clause = remap_schema_clause + """SYS.DBMS_DATAPUMP.METADATA_REMAP(hdnl,'REMAP_SCHEMA',""" + "'" + src + "'" + ',' + "'" + tgt + "');\n"
            remap_schema_clause = remap_schema_clause.rstrip('\n')
        if remapTablespace == 'yes':
            readlog_dep_url = src_dep_url + '/readlog'
            payload = {"jobName": jobName, "log": '_SRC_Remap_Tablespaces'}
            headers = {"Content-Type": "application/json"}
            r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            SRC_Remap_Tablespaces = r.json()[0][0]
            SRC_Remap_Tablespaces = SRC_Remap_Tablespaces.split(',')
            readlog_dep_url = src_dep_url + '/readlog'
            payload = {"jobName": jobName, "log": '_TGT_Remap_Tablespaces'}
            headers = {"Content-Type": "application/json"}
            r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            TGT_Remap_Tablespaces = r.json()[0][0]
            TGT_Remap_Tablespaces = TGT_Remap_Tablespaces.split(',')
            for src in SRC_Remap_Tablespaces:
                for tgt in TGT_Remap_Tablespaces:
                    if SRC_Remap_Tablespaces.index(src) == TGT_Remap_Tablespaces.index(tgt):
                        remap_tablespace_clause = remap_tablespace_clause + """SYS.DBMS_DATAPUMP.METADATA_REMAP(hdnl,'REMAP_TABLESPACE',""" + "'" + src + "'" + ',' + "'" + tgt + "');\n"
            remap_tablespace_clause = remap_tablespace_clause.rstrip('\n')
        if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Import')):
            try:
                val = selectConn(tgtdbName)
                DBconn = val[0]
                DBcursor = DBconn.cursor()
                impdp_cmd = """DECLARE
                                 hdnl number; 
                                 BEGIN 
                                 hdnl := SYS.DBMS_DATAPUMP.OPEN('IMPORT','SCHEMA',NULL,:jobName);
                                 SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :dumpfile, directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_dump_file,reusefile => 1); 
                                 SYS.DBMS_DATAPUMP.ADD_FILE(handle => hdnl, filename => :logFile,directory => :dirName,filetype => sys.dbms_datapump.ku$_file_type_log_file);
                                 SYS.DBMS_DATAPUMP.METADATA_FILTER(hdnl,'SCHEMA_EXPR','IN ("""'{0}'""")');
                                 """'{1}''{2}'"""
                                 SYS.DBMS_DATAPUMP.SET_PARALLEL(hdnl,:parallel);
                                 SYS.DBMS_DATAPUMP.START_JOB(hdnl);
                                 END;""".format(imp_schema, remap_schema_clause, remap_tablespace_clause)
                DBcursor.execute(impdp_cmd, jobName=jobName, dirName=tgtDirName, dumpfile=dumpFile, logFile=imp_logFile,
                                 parallel=imp_parallel)
                startTime = datetime.now(timezone.utc)
                startTime = startTime.strftime('%Y-%m-%d:%H:%M:%S')
                with open(os.path.join(oneplace_home, jobName, jobName + '_Import'), 'w') as infile:
                    infile.write(startTime)
            except cx_Oracle.DatabaseError as e:
                with open(os.path.join(oneplace_home, jobName, jobName + '_ImportOnDemand.log'), 'w') as infile:
                    infile.write(str(e))
            finally:
                if DBconn:
                    DBcursor.close()
                    DBconn.close()


class expimpJob(Resource):
    def get(self):
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT jobName FROM expimp')
        db_row = cursor.fetchall()
        cursor.close()
        conn.close()
        jobName = []
        if db_row:
            for name in db_row:
                jobName.append(name[0])
        return [jobName]


class readLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = []
        with open(os.path.join(oneplace_home, jobName, jobName + log)) as infile:
            for line in infile:
                retData.append(line)
        return [retData]


class writeLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = data['retData']
        with open(os.path.join(oneplace_home, jobName, jobName + log), 'w') as infile:
            for line in retData:
                infile.write(line)
        return ['Success']


class checkLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = ''
        if os.path.exists(os.path.join(oneplace_home, jobName, jobName + log)):
            retData = True
        else:
            retData = False
        return [retData]


class expMon(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobOwner = jobOwner.upper()
        jobName = data['jobName']
        src_dep_url = data['src_dep_url']
        tgt_dep_url = data['tgt_dep_url']
        srcdbName = data['srcdbName']
        srcDumpDir = data['srcDumpDir']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        expdpMon_fetch = {}
        flashbackSCN = ''
        exp_logFile = jobName + '_Export.log'
        try:
            val = selectConn(srcdbName)
            DBconn = val[0]
            DBcursor = DBconn.cursor()
            with open(os.path.join(oneplace_home, jobName, jobName + '_flashbackscn')) as infile:
                flashbackSCN = infile.read()
            if cdbCheck == 'YES' and len(pdbName) > 0:
                DBcursor.execute('''alter session set container=''' + str(pdbName))
            DBcursor.execute("""SELECT  round((sl.sofar/sl.totalwork)*100,2) DONE, dp.state STATE , dp.WORKERS DEGREE ,sl.time_remaining TIME_REMAINING
                                        FROM v$session_longops sl, v$datapump_job dp
                                        WHERE sl.opname = dp.job_name and sl.sofar != sl.totalwork and dp.job_name=:jobName""",
                             {"jobName": jobName})
            expdpMon = DBcursor.fetchall()
            if len(expdpMon) > 0:
                with open(os.path.join(oneplace_home, jobName, jobName + '_Stats')) as infile:
                    startTime = infile.read()
                endTime = datetime.now(timezone.utc)
                endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
                datetimeFormat = '%Y-%m-%d:%H:%M:%S'
                elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime,
                                                                                               datetimeFormat)
                elapTime = elapTime.total_seconds()
                expdpMon_fetch['STATE'] = expdpMon[0][1]
                expdpMon_fetch['DEGREE'] = expdpMon[0][2]
                expdpMon_fetch['DONE'] = expdpMon[0][0]
                expdpMon_fetch['TIME_REMAINING'] = expdpMon[0][3]
                expdpMon_fetch['ELA_TIME'] = elapTime
            if len(expdpMon) == 0:
                if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Export_EndTime.log')):
                    expdpMon_fetch['STATE'] = 'IN PROGRESS'
                    expdpMon_fetch['WORKERS'] = 5
                    expdpMon_fetch['DONE'] = -1
                    expdpMon_fetch['TIME_REMAINING'] = 0
                    expdpMon_fetch['Elapsed'] = 0
                    src_bfile = DBcursor.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (srcDumpDir, exp_logFile));
                    src_bfile_size = src_bfile.size()
                    f_buf = 1
                    dumpFile = []
                    with open(os.path.join(oneplace_home, jobName, jobName + '_Export.log'), 'w') as infile:
                        while f_buf <= src_bfile_size:
                            content = src_bfile.read(f_buf, 52428800)
                            f_buf = f_buf + 52428800
                            text = str(content).split('\\r\\n')
                            for line in text:
                                infile.write(line + '\n')
                                if '.dmp' in line or '.DMP' in line:
                                    line = line.split('\\')
                                    dumpFile.append(line[-1].strip())
                                elif line.startswith('Job'):
                                    line = line.split()
                                    expdpMon_fetch['STATE'] = 'COMPLETED'
                                    expdpMon_fetch['WORKERS'] = 5
                                    expdpMon_fetch['DONE'] = 100
                                    expdpMon_fetch['TIME_REMAINING'] = 0
                                    expdpMon_fetch['Elapsed'] = line[-1]
                                    for n in line:
                                        if n in 'at':
                                            expEndTime = line[line.index(n) + 1]
                                            if not os.path.exists(os.path.join(oneplace_home, jobName,
                                                                               jobName + '_Export_EndTime.log')):
                                                with open(os.path.join(oneplace_home, jobName,
                                                                       jobName + '_Export_EndTime.log'), 'w') as infile:
                                                    infile.write(expEndTime)
                                                update_dep_url = src_dep_url + '/updateexpimp'
                                                headers = {"Content-Type": "application/json"}
                                                payload = {"jobName": jobName, "jobOwner": jobOwner,
                                                           "colName": 'exp_stat', "colValue": 'COMPLETED'}
                                                r = requests.post(update_dep_url, json=payload, headers=headers,
                                                                  verify=False, timeout=sshTimeOut)
                                                update_dep_url = tgt_dep_url + '/updateexpimp'
                                                headers = {"Content-Type": "application/json"}
                                                payload = {"jobName": jobName, "jobOwner": jobOwner,
                                                           "colName": 'exp_stat', "colValue": 'COMPLETED'}
                                                r = requests.post(update_dep_url, json=payload, headers=headers,
                                                                  verify=False, timeout=sshTimeOut)
                                                with open(os.path.join(oneplace_home, jobName, jobName + '_dumpFiles'),
                                                          'w') as infile:
                                                    for name in dumpFile:
                                                        infile.write(name + '\n')
        except Exception as e:
            logger.info(str(e))
        finally:
            if DBconn:
                DBcursor.close()
                DBconn.close()
        return [expdpMon_fetch, flashbackSCN]


class xfrMon(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobOwner = jobOwner.upper()
        jobName = data['jobName']
        src_dep_url = data['src_dep_url']
        tgt_dep_url = data['tgt_dep_url']
        srcDep = data['srcDep']
        tgtDep = data['tgtDep']
        srcdbName = data['srcdbName']
        srcDumpDir = data['srcDumpDir']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        tgtdbName = data['tgtdbName']
        tgtDumpDir = data['tgtDumpDir']
        dumpFile = data['dumpFile']
        reMapSchema = data['reMapSchema']
        remapTablespace = data['remapTablespace']
        xfrPercent = []
        readytoImport = []
        readlog_dep_url = src_dep_url + '/readlog'
        payload = {"jobName": jobName, "log": '_dumpFiles'}
        headers = {"Content-Type": "application/json"}
        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        job_dir = os.path.join(oneplace_home, jobName)
        if not os.path.exists(job_dir): os.makedirs(job_dir)
        dumpFileList = r.json()[0]
        for fileName in dumpFileList:
            fileName = fileName.strip()
            if not os.path.exists(os.path.join(oneplace_home, jobName, fileName + '_Size.log')):
                readlog_dep_url = tgt_dep_url + '/xfrdumpfiles'
                payload = {"jobName": jobName, "jobOwner": jobOwner, "src_dep_url": src_dep_url,
                           "tgt_dep_url": tgt_dep_url, "srcdbName": srcdbName,
                           "srcDumpDir": srcDumpDir, "cdbCheck": cdbCheck, "pdbName": pdbName, "tgtdbName": tgtdbName,
                           "tgtDumpDir": tgtDumpDir, "fileName": fileName}
                headers = {"Content-Type": "application/json"}
                r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            if os.path.exists(os.path.join(oneplace_home, jobName, fileName + '_speed')):
                with open(os.path.join(oneplace_home, jobName, fileName + '_speed')) as infile:
                    xfrStats = infile.read()
                    xfrStats = xfrStats.split('$')
                    if len(xfrStats[0]) > 0:
                        xfrPercent.append({'fileName': fileName, 'Percent': xfrStats[0], 'elapTime': xfrStats[1],
                                           'XFRSpeed': xfrStats[2], 'TotalBytes': xfrStats[3], 'XFRBytes': xfrStats[4],
                                           'XFReta': xfrStats[5]})
            else:
                xfrPercent.append({'fileName': fileName, 'Percent': -1})
        for name in xfrPercent:
            if name['Percent'] == '100' or name['Percent'] == '100.0':
                readytoImport.append(name['fileName'])
        if len(readytoImport) == len(dumpFileList) and len(readytoImport) > 0:
            with open(os.path.join(oneplace_home, jobName, jobName + '_xfr_Stats'), 'w') as infile:
                for name in readytoImport:
                    infile.write(name + ',' + '100' + '\n')
            update_dep_url = src_dep_url + '/updateexpimp'
            headers = {"Content-Type": "application/json"}
            payload = {"jobName": jobName, "jobOwner": jobOwner, "colName": 'xfr_stat', "colValue": 'COMPLETED'}
            r = requests.post(update_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            update_dep_url = tgt_dep_url + '/updateexpimp'
            r = requests.post(update_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            imp_dep_url = tgt_dep_url + '/impdp'
            payload = {"jobName": jobName, "tgtDep": tgtDep, "tgtdbName": tgtdbName, "tgtDirName": tgtDumpDir,
                       "dumpFile": dumpFile, "src_dep_url": src_dep_url,
                       "reMapSchema": reMapSchema, "remapTablespace": remapTablespace}
            headers = {"Content-Type": "application/json"}
            r = requests.post(imp_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        return [xfrPercent]


class impMon(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobOwner = jobOwner.upper()
        jobName = data['jobName']
        tgtdbName = data['tgtdbName']
        tgtDumpDir = data['tgtDumpDir']
        src_dep_url = data['src_dep_url']
        tgt_dep_url = data['tgt_dep_url']
        imp_logFile = jobName + '_Import.log'
        impdpMon_fetch = {}
        try:
            tgtval = selectConn(tgtdbName)
            tgtcon = tgtval[0]
            tgtcursor = tgtcon.cursor()
            tgtcursor.execute(
                """select dp.state,dp.workers,-1 DONE,0 TIME_REMAINING  from gv$datapump_job dp where dp.job_name=:jobName""",
                {"jobName": jobName})
            impdpMon = tgtcursor.fetchall()
            if len(impdpMon) > 0:
                impdpMon_fetch['STATE'] = impdpMon[0][0]
                impdpMon_fetch['WORKERS'] = impdpMon[0][1]
                impdpMon_fetch['DONE'] = impdpMon[0][2]
                impdpMon_fetch['TIME_REMAINING'] = impdpMon[0][3]
            if len(impdpMon_fetch) == 0:
                impdpMon_fetch = {}
                if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Import_EndTime.log')):
                    impdpMon_fetch['STATE'] = 'IN PROGRESS'
                    impdpMon_fetch['WORKERS'] = 5
                    impdpMon_fetch['DONE'] = -1
                    impdpMon_fetch['TIME_REMAINING'] = 0
                    impdpMon_fetch['Elapsed'] = 0
                    src_bfile = tgtcursor.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (tgtDumpDir, imp_logFile));
                    src_bfile_size = src_bfile.size()
                    f_buf = 1
                    with open(os.path.join(oneplace_home, jobName, jobName + '_Import.log'), 'w') as infile:
                        while f_buf <= src_bfile_size:
                            content = src_bfile.read(f_buf, 5242880)
                            f_buf = f_buf + 5242880
                            text = str(content).split('\\r\\n')
                            for line in text:
                                infile.write(line + '\n')
                                if line.startswith('Job'):
                                    line = line.split()
                                    elaTime = line[-1]
                                    impdpMon_fetch['STATE'] = 'COMPLETED'
                                    impdpMon_fetch['WORKERS'] = 5
                                    impdpMon_fetch['DONE'] = 100
                                    impdpMon_fetch['TIME_REMAINING'] = 0
                                    impdpMon_fetch['Elapsed'] = elaTime
                                    for n in line:
                                        if n in 'at':
                                            if not os.path.exists(os.path.join(oneplace_home, jobName,
                                                                               jobName + '_Import_EndTime.log')):
                                                with open(os.path.join(oneplace_home, jobName,
                                                                       jobName + '_Import_EndTime.log'), 'w') as infile:
                                                    infile.write(elaTime)
                                    update_dep_url = src_dep_url + '/updateexpimp'
                                    headers = {"Content-Type": "application/json"}
                                    payload = {"jobName": jobName, "jobOwner": jobOwner, "colName": 'imp_stat',
                                               "colValue": 'COMPLETED'}
                                    r = requests.post(update_dep_url, json=payload, headers=headers, verify=False,
                                                      timeout=sshTimeOut)
                                    update_dep_url = tgt_dep_url + '/updateexpimp'
                                    r = requests.post(update_dep_url, json=payload, headers=headers, verify=False,
                                                      timeout=sshTimeOut)
                else:
                    impdpMon_fetch['STATE'] = 'COMPLETED'
                    impdpMon_fetch['WORKERS'] = 5
                    impdpMon_fetch['DONE'] = 100
                    impdpMon_fetch['TIME_REMAINING'] = 0
                    impdpMon_fetch['Elapsed'] = 0
        except Exception as e:
            logger.info(str(e))
        finally:
            if tgtcon:
                tgtcursor.close()
                tgtcon.close()
        return [impdpMon_fetch]


class exportCheckLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        tabStats = {}
        if os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Export.log')):
            with open(os.path.join(oneplace_home, jobName, jobName + '_Export.log')) as infile:
                for line in infile:
                    if line.startswith('.'):
                        line = line.split()
                        tabName = line[line.index('exported') + 1]
                        tabSize = line[line.index('exported') + 2]
                        tabRows = line[line.index('exported') + 4]
                        tabStats[tabName] = {'ExportRows': tabRows}
        return [tabStats]


class importCheckLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        reMapSchema = data['reMapSchema']
        src_dep_url = data['src_dep_url']
        if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Table_Stats.csv')):
            readlog_dep_url = src_dep_url + '/exportchecklog'
            payload = {"jobName": jobName}
            headers = {"Content-Type": "application/json"}
            r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
            tabStats = r.json()[0]
            if os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Import.log')):
                with open(os.path.join(oneplace_home, jobName, jobName + '_Import.log')) as infile:
                    for line in infile:
                        if line.startswith('.'):
                            line = line.split()
                            tabName = line[line.index('imported') + 1]
                            if reMapSchema == 'yes':
                                tabOwner = tabName.split('.')[0]
                                tabOwner = tabOwner.lstrip('"').rstrip('"')
                                tgtTabName = tabName.split('.')[1]
                                readlog_dep_url = src_dep_url + '/readlog'
                                payload = {"jobName": jobName, "log": '_SRC_Remap_Schemas'}
                                headers = {"Content-Type": "application/json"}
                                r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False,
                                                  timeout=sshTimeOut)
                                SRC_Remap_Schemas = r.json()[0][0]
                                SRC_Remap_Schemas = SRC_Remap_Schemas.split(',')
                                readlog_dep_url = src_dep_url + '/readlog'
                                payload = {"jobName": jobName, "log": '_TGT_Remap_Schemas'}
                                headers = {"Content-Type": "application/json"}
                                r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False,
                                                  timeout=sshTimeOut)
                                TGT_Remap_Schemas = r.json()[0][0]
                                TGT_Remap_Schemas = TGT_Remap_Schemas.split(',')
                                for src in SRC_Remap_Schemas:
                                    for tgt in TGT_Remap_Schemas:
                                        if tgt == tabOwner:
                                            if SRC_Remap_Schemas.index(src) == TGT_Remap_Schemas.index(tgt):
                                                tabName = '"' + src + '"' + '.' + tgtTabName
                            tabSize = line[line.index('imported') + 2]
                            tabRows = line[line.index('imported') + 4]
                            tabStats[tabName]['ImportRows'] = tabRows
                df = pd.DataFrame.from_dict(tabStats)
                df.to_csv(os.path.join(oneplace_home, jobName, jobName + '_Table_Stats.csv'))
        else:
            tabStats = pd.read_csv(os.path.join(oneplace_home, jobName, jobName + '_Table_Stats.csv'), index_col=0,
                                   keep_default_na=False)
            tabStats = tabStats.to_dict()
        return [tabStats]


class expdpMon(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        SQconn = sqlite3.connect('conn.db')
        SQcursor = SQconn.cursor()
        SQcursor.execute(
            'SELECT jobOwner,srcdbName,tgtdbName,srcDumpDir,tgtDumpDir,cdbCheck,pdbName,reMapSchema,srcDep,tgtDep,exp_stat,xfr_stat,imp_stat,dumpFile,remapTablespace FROM expimp  WHERE jobName=:jobName',
            {"jobName": jobName})
        db_row = SQcursor.fetchone()
        expdpMon_fetch = {}
        xfrPercent = []
        impdpMon_fetch = {}
        downloadPercent = ''
        readytoDownload = ''
        readytoImport = ''
        dumpFile = ''
        tabStats = {}
        currentSCN = ''
        flashbackSCN = ''
        xfrComplete = ''
        if db_row:
            jobOwner = db_row[0]
            jobOwner = jobOwner.upper()
            srcdbName = db_row[1]
            tgtdbName = db_row[2]
            srcDumpDir = db_row[3]
            tgtDumpDir = db_row[4]
            cdbCheck = db_row[5]
            pdbName = db_row[6]
            reMapSchema = db_row[7]
            srcDep = db_row[8]
            tgtDep = db_row[9]
            expStat = db_row[10]
            xfrStat = db_row[11]
            impStat = db_row[12]
            dumpFile = db_row[13]
            remapTablespace = db_row[14]
            SQcursor.execute('select dep_url from ONEPCONN where dep=:dep', {"dep": srcDep})
            src_db_row = SQcursor.fetchone()
            if src_db_row:
                src_dep_url = src_db_row[0]
            SQcursor.execute('select dep_url from ONEPCONN where dep=:dep', {"dep": tgtDep})
            tgt_db_row = SQcursor.fetchone()
            if tgt_db_row:
                tgt_dep_url = tgt_db_row[0]
            if expStat != 'COMPLETED':
                expmon_dep_url = src_dep_url + '/expmon'
                headers = {"Content-Type": "application/json"}
                payload = {"jobName": jobName, "jobOwner": jobOwner, "src_dep_url": src_dep_url,
                           "tgt_dep_url": tgt_dep_url, "srcdbName": srcdbName,
                           "srcDumpDir": srcDumpDir, "cdbCheck": cdbCheck, "pdbName": pdbName}
                r = requests.post(expmon_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                expdpMon_fetch = r.json()[0]
                flashbackSCN = r.json()[1]
            else:
                readlog_dep_url = src_dep_url + '/readlog'
                headers = {"Content-Type": "application/json"}
                payload = {"jobName": jobName, "log": '_Export_EndTime.log'}
                r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                elaTime = r.json()[0][0]
                readlog_dep_url = src_dep_url + '/readlog'
                headers = {"Content-Type": "application/json"}
                payload = {"jobName": jobName, "log": '_flashbackscn'}
                r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                flashbackSCN = r.json()[0]
                expdpMon_fetch['STATE'] = 'COMPLETED'
                expdpMon_fetch['WORKERS'] = 5
                expdpMon_fetch['DONE'] = 100
                expdpMon_fetch['TIME_REMAINING'] = 0
                expdpMon_fetch['Elapsed'] = elaTime
                if xfrStat != 'COMPLETED':
                    xfrlog_dep_url = tgt_dep_url + '/xfrmon'
                    headers = {"Content-Type": "application/json"}
                    payload = {"jobName": jobName, "jobOwner": jobOwner, "src_dep_url": src_dep_url,
                               "tgt_dep_url": tgt_dep_url, "srcdbName": srcdbName, "srcDep": srcDep, "tgtDep": tgtDep,
                               "srcDumpDir": srcDumpDir, "tgtDumpDir": tgtDumpDir, "cdbCheck": cdbCheck,
                               "pdbName": pdbName, "tgtdbName": tgtdbName, "dumpFile": dumpFile,
                               "reMapSchema": reMapSchema, "remapTablespace": remapTablespace}
                    r = requests.post(xfrlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                    xfrPercent = r.json()[0]
                    xfrComplete = 'NO'
                else:
                    xfrComplete = 'YES'
                    readlog_dep_url = tgt_dep_url + '/readlog'
                    headers = {"Content-Type": "application/json"}
                    payload = {"jobName": jobName, "log": '_xfr_Stats'}
                    r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                    for name in r.json()[0]:
                        name = name.split(',')
                        xfrPercent.append({'fileName': name[0], 'Percent': int(name[1].strip())})
                    if impStat != 'COMPLETED':
                        readlog_dep_url = tgt_dep_url + '/impmon'
                        payload = {"jobName": jobName, "jobOwner": jobOwner, "src_dep_url": src_dep_url,
                                   "tgt_dep_url": tgt_dep_url, "tgtdbName": tgtdbName, "tgtDumpDir": tgtDumpDir}
                        headers = {"Content-Type": "application/json"}
                        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False,
                                          timeout=sshTimeOut)
                        impdpMon_fetch = r.json()[0]
                    else:
                        readlog_dep_url = tgt_dep_url + '/readlog'
                        headers = {"Content-Type": "application/json"}
                        payload = {"jobName": jobName, "log": '_Import_EndTime.log'}
                        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False,
                                          timeout=sshTimeOut)
                        elaTime = r.json()[0][0]
                        impdpMon_fetch['STATE'] = 'COMPLETED'
                        impdpMon_fetch['WORKERS'] = 5
                        impdpMon_fetch['DONE'] = 100
                        impdpMon_fetch['TIME_REMAINING'] = 0
                        impdpMon_fetch['Elapsed'] = elaTime
                        implog_dep_url = tgt_dep_url + '/importchecklog'
                        headers = {"Content-Type": "application/json"}
                        payload = {"jobName": jobName, "reMapSchema": reMapSchema, "src_dep_url": src_dep_url}
                        r = requests.post(implog_dep_url, json=payload, headers=headers, verify=False,
                                          timeout=sshTimeOut)
                        tabStats = r.json()[0]
        return [expdpMon_fetch, xfrPercent, impdpMon_fetch, tabStats, flashbackSCN, src_dep_url, tgt_dep_url,
                xfrComplete]


class readExportLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        exp_logFile = jobName + '_Export.log'
        SQconn = sqlite3.connect('conn.db')
        SQcursor = SQconn.cursor()
        SQcursor.execute('SELECT jobOwner,srcdbName,srcdumpDir,srcDep FROM expimp  WHERE jobName=:jobName',
                         {"jobName": jobName})
        db_row = SQcursor.fetchone()
        ExportLog = []
        if db_row:
            srcdbName = db_row[1]
            srcDumpDir = db_row[2]
            try:
                val = selectConn(srcdbName)
                DBconn = val[0]
                DBcursor = DBconn.cursor()
                if cdbCheck == 'YES' and len(pdbName) > 0:
                    DBcursor.execute('''alter session set container=''' + str(pdbName))
                src_bfile = DBcursor.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (srcDumpDir, exp_logFile));
                src_bfile_size = src_bfile.size()
                f_buf = 1
                while f_buf <= src_bfile_size:
                    content = src_bfile.read(f_buf, 5242880)
                    f_buf = f_buf + 5242880
                    text = str(content).split('\\r\\n')
                    for line in text:
                        ExportLog.append(line.strip("b'") + '\n')
            except cx_Oracle.DatabaseError as e:
                ExportLog.append(str(e))
            except AttributeError as e:
                ExportLog.append(str(e))
            finally:
                if DBconn:
                    DBcursor.close()
                    DBconn.close()
        return [ExportLog]


class S3TransferLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        src_dep_url = data['src_dep_url']
        xfrPercent = []
        readlog_dep_url = src_dep_url + '/readlog'
        payload = {"jobName": jobName, "log": '_dumpFiles'}
        headers = {"Content-Type": "application/json"}
        r = requests.post(readlog_dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        dumpFileList = r.json()[0]
        for fileName in dumpFileList:
            fileName = fileName.strip()
            if os.path.exists(os.path.join(oneplace_home, jobName, fileName + '_speed')):
                with open(os.path.join(oneplace_home, jobName, fileName + '_speed')) as infile:
                    xfrStats = infile.read()
                    xfrStats = xfrStats.split('$')
                    if len(xfrStats[0]) > 0:
                        xfrPercent.append({'fileName': fileName, 'Percent': xfrStats[0], 'elapTime': xfrStats[1],
                                           'XFRSpeed': xfrStats[2], 'TotalBytes': xfrStats[3], 'XFRBytes': xfrStats[4],
                                           'XFReta': xfrStats[5]})
            else:
                xfrPercent.append(
                    {'fileName': fileName, 'Percent': 0, 'elapTime': 0, 'XFRSpeed': 0, 'TotalBytes': 0, 'XFRBytes': 0,
                     'XFReta': 0})
        return [xfrPercent]


class readImportLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        imp_logFile = jobName + '_Import.log'
        SQconn = sqlite3.connect('conn.db')
        SQcursor = SQconn.cursor()
        SQcursor.execute('SELECT tgtdbName,tgtDumpDir FROM expimp  WHERE jobName=:jobName', {"jobName": jobName})
        db_row = SQcursor.fetchone()
        ImportLog = []
        if db_row:
            tgtdbName = db_row[0]
            tgtDumpDir = db_row[1]
            try:
                val = selectConn(tgtdbName)
                DBconn = val[0]
                DBcursor = DBconn.cursor()
                src_bfile = DBcursor.callfunc("bfilename", cx_Oracle.DB_TYPE_BFILE, (tgtDumpDir, imp_logFile));
                src_bfile_size = src_bfile.size()
                f_buf = 1
                while f_buf <= src_bfile_size:
                    content = src_bfile.read(f_buf, 5242880)
                    f_buf = f_buf + 5242880
                    text = str(content).split('\\r\\n')
                    for line in text:
                        ImportLog.append(line.strip("b'") + '\n')
            except cx_Oracle.DatabaseError as e:
                ImportLog.append(str(e))
            finally:
                if DBconn:
                    DBcursor.close()
                    DBconn.close()
        return [ImportLog]


class downloadS3Log(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT jobOwner,tgtdbName,tgtDumpDir FROM expimp  WHERE jobName=:jobName', {"jobName": jobName})
        db_row = cursor.fetchone()
        cursor.close()
        conn.close()
        dbtask_fetch = []
        if db_row:
            jobOwner = db_row[0]
            jobOwner = jobOwner.upper()
            tgtdbName = db_row[1]
            tgtDirName = db_row[2]
            try:
                val = selectConn(tgtdbName)
                tgtcon = val[0]
                tgtcursor = tgtcon.cursor()
                with open(os.path.join(oneplace_home, jobName, jobName + '_Download')) as infile:
                    task_id = infile.read()
                if os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_DownloadLog')):
                    with open(os.path.join(oneplace_home, jobName, jobName + '_DownloadLog')) as infile:
                        log = infile.read()
                    dbtask_fetch.append({'TEXT': log})
                read_task = """SELECT text FROM table(rdsadmin.rds_file_util.read_text_file('BDUMP',:dbtask))"""
                dbtask_id_log = 'dbtask-' + task_id + '.log'
                param = {"dbtask": dbtask_id_log}
                dbtask_fetch = pd.read_sql_query(read_task, tgtcon, params=[param["dbtask"]])
                dbtask_fetch = dbtask_fetch.to_dict('records')
            except cx_Oracle.DatabaseError as e:
                dbtask_fetch.append(str(e))
            except pd.io.sql.DatabaseError as e:
                dbtask_fetch.append({'TEXT': str(e)})
            finally:
                if tgtcon:
                    tgtcursor.close()
                    tgtcon.close()
        return [dbtask_fetch]


class updateS3Config(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        bucketName = data['bucketName']
        aws_access_key_id = data['aws_access_key_id']
        aws_secret_access_key = data['aws_secret_access_key']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        msg = []
        try:
            cursor.execute(
                '''update expimp set bucketName=:bucketName,aws_access_key_id=:aws_access_key_id,aws_secret_access_key=:aws_secret_access_key WHERE jobName=:jobName''',
                {"bucketName": bucketName, "aws_access_key_id": aws_access_key_id,
                 "aws_secret_access_key": aws_secret_access_key, "jobName": jobName})
            conn.commit()
            msg.append('Updated Successfully')
        except sqlite3.DatabaseError as e:
            msg.append(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()
        return [msg]


class xfrDumpFiles(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobOwner = data['jobOwner']
        jobName = data['jobName']
        src_dep_url = data['src_dep_url']
        tgt_dep_url = data['tgt_dep_url']
        srcDumpDir = data['srcDumpDir']
        srcdbName = data['srcdbName']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        tgtdbName = data['tgtdbName']
        tgtDumpDir = data['tgtDumpDir']
        fileName = data['fileName']
        ilp = mp.Process(target=transfer_dumpFile, args=(
        src_dep_url, tgt_dep_url, srcdbName, jobName, srcDumpDir, fileName, cdbCheck, pdbName, tgtdbName, tgtDumpDir))
        ilp.start()
        time.sleep(1)


class downLoadfromS3(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT jobOwner,bucketName,tgtdbName,tgtDumpDir FROM expimp  WHERE jobName=:jobName',
                       {"jobName": jobName})
        db_row = cursor.fetchone()
        cursor.close()
        if db_row:
            jobOwner = db_row[0]
            jobOwner = jobOwner.upper()
            bucketName = db_row[1]
            tgtdbName = db_row[2]
            dirName = db_row[3]
            if not os.path.exists(os.path.join(oneplace_home, jobName, jobName + '_Download')):
                ilp = threading.Thread(target=download_dumpFile, args=(jobName, tgtdbName, bucketName, dirName))
                ilp.start()


class TshootImpDP(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tgtdbName FROM expimp  WHERE jobName=:jobName', {"jobName": jobName})
        db_row = cursor.fetchone()
        cursor.close()
        conn.close()
        impdp_longOps_fetch = ''
        resumable_job_fetch = ''
        session_waits_fetch = ''
        impdp_locks_fetch = ''
        if db_row:
            tgtdbName = db_row[0]
            try:
                val = selectConn(tgtdbName)
                tgtcon = val[0]
                resumable_job = """select session_id, status, start_time, suspend_time,resume_time,error_msg,SQL_TEXT from dba_resumable"""
                resumable_job_fetch = pd.read_sql_query(resumable_job, tgtcon)
                resumable_job_fetch = resumable_job_fetch.to_dict('records')
                impdp_longOps = """select dp.job_name,dp.state,dp.WORKERS,sl.OPNAME,sl.MESSAGE,ROUND(sl.SOFAR/sl.TOTALWORK*100,2) DONE,sl.TIME_REMAINING
                                      from gv$session_longops sl, gv$datapump_job dp
                                      where sl.opname = dp.job_name and sofar != totalwork and dp.job_name=:jobName"""
                param = {"jobName": jobName}
                impdp_longOps_fetch = pd.read_sql_query(impdp_longOps, tgtcon, params=[param["jobName"]])
                impdp_longOps_fetch = impdp_longOps_fetch.to_dict('records')
                impdp_locks = """select dw.waiting_session, dw.holding_session,b.serial# serial,w.event, w.program wprogram, b.program bprogram, 
                                w.module wmod,b.module bmod, LOCK_ID1
                                from sys.dba_waiters dw, gv$session w, gv$session b
                                where dw.waiting_session = w.sid
                                and dw.holding_session = b.sid
                                and (w.module like 'Data Pump%'
                                or w.program like '%EXPDP%'
                                or w.program like '%IMPDP%')
                                order by dw.holding_session"""
                impdp_locks_fetch = pd.read_sql_query(impdp_locks, tgtcon)
                impdp_locks_fetch = impdp_locks_fetch.to_dict('records')
                session_waits = """select sw.SID,s.program PROG,sw.SEQ# SEQ,sw.EVENT, sw.WAIT_TIME,sw.SECONDS_IN_WAIT,sw.STATE,sw.P1TEXT, sw.P1,sw.P2TEXT
                                 ,sw.P2,sw.P3TEXT,sw.P3 from GV$SESSION_WAIT sw, Gv$session s
                                 where sw.wait_class <> 'Idle'
                                 and sw.sid=s.sid
                                 and (s.module like 'Data Pump%'
                                 or s.program like '%EXPDP%'
                                 or s.program like '%IMPDP%')"""
                session_waits_fetch = pd.read_sql_query(session_waits, tgtcon)
                session_waits_fetch = session_waits_fetch.to_dict('records')
                dp_worker_sql = """select sysdate "date", s.program, s.sid,  s.status, s.username, d.job_name, p.spid, s.serial#, p.pid  
                                  from   gv$session s, gv$process p, dba_datapump_sessions d
                                  where  p.addr=s.paddr and s.saddr=d.saddr"""
                dp_worker_sql = pd.read_sql_query(dp_worker_sql, tgtcon)
                dp_worker_sql = dp_worker_sql.to_dict('records')

            except cx_Oracle.DatabaseError as e:
                logger.info(str(e))
        return [resumable_job_fetch, impdp_locks_fetch, session_waits_fetch, impdp_longOps_fetch]


class tableSpaceImpDP(Resource):
    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        schemas = data['schemas']
        srcdbName = data['srcdbName']
        tgtdbName = data['tgtdbName']
        cdbCheck = data['cdbCheck']
        pdbName = data['pdbName']
        tablespace_det_fetch = ''
        srcSchemaList = []
        try:
            val = selectConn(srcdbName)
            srccon = val[0]
            srccursor = srccon.cursor()
            if cdbCheck == 'YES' and len(pdbName) > 0:
                srccursor.execute('''alter session set container=''' + str(pdbName))
            bindNames = [":" + str(i + 1) for i in range(len(schemas))]
            tablespace_det = """select distinct tablespace_name from dba_segments where OWNER in (%s)""" % (
                ",".join(bindNames))
            tablespace_det_fetch = pd.read_sql_query(tablespace_det, srccon, params=[*schemas])
            tablespace_det_fetch = tablespace_det_fetch.to_dict('records')
        except cx_Oracle.DatabaseError as e:
            logger.info(str(e))
        finally:
            if srccon:
                srccon.close()
        return [tablespace_det_fetch]


class ggAddSupp(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        tranlevel = data['tranlevel']
        buttonValue = data['buttonValue']
        ssh = subprocess.Popen([ggsci_bin],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddSupp_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddSupp_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True,
                                   bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            if buttonValue == 'add':
                if tranlevel == 'schematrandata':
                    SchemaName = data['SchemaName']
                    opts = data['opts']
                    ssh.stdin.write("add " + tranlevel + " " + SchemaName + " " + opts + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)
                elif tranlevel == 'trandata':
                    tabNameList = data['tabNameList']
                    opts = data['opts']
                    with open(os.path.join(oneplace_home, 'addtrandata.oby'), 'w') as infile:
                        for tabname in tabNameList:
                            infile.write('add trandata ' + tabname + ' ' + opts)
                            infile.write("\n")
                    ssh.stdin.write("obey " + os.path.join(oneplace_home, 'addtrandata.oby') + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)
            elif buttonValue == 'info':
                if tranlevel == 'schematrandata':
                    SchemaName = data['SchemaName']
                    ssh.stdin.write("info " + tranlevel + " " + SchemaName + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)
                elif tranlevel == 'trandata':
                    tabNameList = data['tabNameList']
                    with open(os.path.join(oneplace_home, 'infotrandata.oby'), 'w') as infile:
                        for tabname in tabNameList:
                            infile.write('info trandata ' + tabname)
                            infile.write("\n")
                    ssh.stdin.write("obey " + os.path.join(oneplace_home, 'infotrandata.oby') + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)
            elif buttonValue == 'del':
                if tranlevel == 'schematrandata':
                    SchemaName = data['SchemaName']
                    opts = data['opts']
                    ssh.stdin.write("delete " + tranlevel + " " + SchemaName + " " + opts + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)
                elif tranlevel == 'trandata':
                    tabNameList = data['tabNameList']
                    opts = data['opts']
                    with open(os.path.join(oneplace_home, 'deltrandata.oby'), 'w') as infile:
                        for tabname in tabNameList:
                            infile.write('delete trandata ' + tabname + ' ' + opts)
                            infile.write("\n")
                    ssh.stdin.write("obey " + os.path.join(oneplace_home, 'deltrandata.oby') + "\n")
                    AddSuppErr, stderr = ssh.communicate()
                    AddSupp_Out.append(AddSuppErr)

        with open(oneplace_home + '/AddSuppErr.lst', 'w') as suppErrFileIn:
            for listline in AddSupp_Out:
                suppErrFileIn.write(listline)
        with open(oneplace_home + '/AddSuppErr.lst', 'r') as suppErrFile:
            ErrPrint = []
            for line in suppErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ErrPrint.append(line)
                if tranlevel == 'schematrandata':
                    if SchemaName in line:
                        line = line.split('INFO', 1)[-1]
                        ErrPrint.append(line)
                elif tranlevel == 'trandata':
                    if 'table' in line:
                        line = line.split('>', 1)[-1]
                        ErrPrint.append(line)
        return [ErrPrint]


class ggAddHeartBeat(Resource):
    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        hbTblOps = data['hbTblOps']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user FROM CONN WHERE dbname=:dbname', {"dbname": alias})
        db_row = cursor.fetchone()
        cursor.close()
        conn.close()
        if db_row:
            user = db_row[0]
        globalFile = []
        with open(os.path.join(gg_home, 'GLOBALS'), 'r') as infile:
            for line in infile:
                globalFile.append(line)
        with open(os.path.join(gg_home, 'GLOBALS'), 'w') as infile:
            for line in globalFile:
                if 'GGSCHEMA' in line:
                    new_line = line.replace(line, "GGSCHEMA " + user + "\n")
                    infile.write(new_line)
                else:
                    infile.write(line)
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, bufsize=0)
        ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
        AddHB_Out = []
        LoginErr, stderr = ssh.communicate()
        if "ERROR" in LoginErr:
            AddHB_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=0)
            ssh.stdin.write("dblogin useridalias " + alias + " domain " + domain + "\n")
            if hbTblOps == 'add':
                frequency = data['HBTblFrequency']
                retention_time = data['HBTblRetention']
                purge_frequency = data['HBTblPurgeFrequency']
                ssh.stdin.write("add heartbeattable frequency " + str(frequency) + " retention_time " + str(
                    retention_time) + " purge_frequency " + str(purge_frequency) + "\n")
            elif hbTblOps == 'edit':
                frequency = data['HBTblFrequency']
                retention_time = data['HBTblRetention']
                purge_frequency = data['HBTblPurgeFrequency']
                ssh.stdin.write("alter heartbeattable frequency " + str(frequency) + ", retention_time " + str(
                    retention_time) + ", purge_frequency " + str(purge_frequency) + "\n")
            elif hbTblOps == 'del':
                ssh.stdin.write("delete heartbeattable" + "\n")
            AddHBErr, stderr = ssh.communicate()
            if 'ERROR' in AddHBErr:
                AddHB_Out.append(AddHBErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                AddHB_Out.append(AddHBErr)
        with open(os.path.join(oneplace_home, 'AddHBErr.lst'), 'w') as HBErrFileIn:
            for listline in AddHB_Out:
                HBErrFileIn.write(listline)
        with open(os.path.join(oneplace_home, 'AddHBErr.lst'), 'r') as HBErrFile:
            ErrPrint = []
            for line in HBErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    ErrPrint.append(line)
                elif 'ORA-' in line:
                    line = line.split('>', 1)[-1]
                    line1 = 'Solution : Please grant create procedure and create view to Goldengate Admin user'
                    ErrPrint.append(line)
                    ErrPrint.append(line1)
                elif 'INFO' in line:
                    ErrPrint.append(line)
        return [ErrPrint]


class listPrm_files(Resource):
    def get(self):
        prmfiles = []
        globalsFile = 'GLOBALS'
        globalsPath = os.path.join(gg_home, globalsFile)
        PARAM_DIRECTORY = os.path.join(gg_home, 'dirprm')
        for filename in os.listdir(PARAM_DIRECTORY):
            if filename.endswith(".prm"):
                prmpath = os.path.join(gg_home, 'dirprm', filename)
                if os.path.isfile(prmpath):
                    prmfiles.append(filename)
        if not os.path.exists(globalsPath):
            with open(str(globalsPath), 'w') as globalsFile:
                wallet = 'GGSCHEMA TEST \nWALLETLOCATION ' + os.path.join(gg_home,
                                                                          'dirwlt') + '\n' + 'ALLOWOUTPUTDIR ' + trailPath
                globalsFile.write(wallet)
            prmfiles.append(globalsFile)
        else:
            prmfiles.append(globalsFile)

        return [prmfiles]


class listRptFiles(Resource):
    def get(self):
        rptfiles = []
        REPORT_DIRECTORY = os.path.join(gg_home, 'dirrpt')
        for filename in os.listdir(REPORT_DIRECTORY):
            if filename.endswith(".rpt"):
                rptpath = os.path.join(gg_home, 'dirrpt', filename)
                if os.path.isfile(rptpath):
                    rptfiles.append(filename)

        return [rptfiles]


class listDscFiles(Resource):
    def get(self):
        dscfiles = []
        REPORT_DIRECTORY = os.path.join(gg_home, 'dirrpt')
        PRM_DIRECTORY = os.path.join(gg_home, 'dirprm')
        for filename in os.listdir(REPORT_DIRECTORY):
            if filename.endswith(".dsc"):
                dscpath = os.path.join(gg_home, 'dirrpt', filename)
                if os.path.isfile(dscpath):
                    dscfiles.append(filename)
        dscnames = []
        for filename in os.listdir(PRM_DIRECTORY):
            if filename.endswith(".prm"):
                prmpath = os.path.join(gg_home, 'dirprm', filename)
                with open(prmpath) as infile:
                    for line in infile:
                        if 'DISCARDFILE' in line:
                            line = line.split()
                            line = line[1].rstrip(',')
                            dscnames.append(line)
        for name in dscnames:
            if name.startswith('.') or name[0].isalnum():
                dscfiles.append(os.path.join(gg_home, name))
            else:
                dscfiles.append(name)

        return [dscfiles]


class viewPrm_files(Resource):
    def post(self):
        data = request.get_json(force=True)
        prmFile = data['prmFile']
        globalsFile = 'GLOBALS'
        globalsPath = os.path.join(gg_home, globalsFile)
        prmFile = prmFile.lstrip('["').rstrip('"]')
        dest_file = os.path.join(gg_home, 'dirprm', prmFile)
        if prmFile == 'GLOBALS':
            with open(globalsPath, 'r') as prmFile:
                viewprmfile = prmFile.read()
        else:
            with open(dest_file, 'r') as prmFile:
                viewprmfile = prmFile.read()

        return [viewprmfile]


class viewRptFiles(Resource):
    def post(self):
        data = request.get_json(force=True)
        rptFile = data['rptFile']
        rptFile = rptFile.lstrip('["').rstrip('"]')
        dest_file = os.path.join(gg_home, 'dirrpt', rptFile)
        with open(dest_file, 'r') as rptFile:
            viewrptfile = rptFile.read()

        return [viewrptfile]


class viewDscFiles(Resource):
    def post(self):
        data = request.get_json(force=True)
        dscFile = data['dscFile']
        dscFile = dscFile.lstrip('["').rstrip('"]')
        dest_file = os.path.join(gg_home, 'dirrpt', dscFile)
        with open(dest_file, 'r') as dscFile:
            viewdscfile = dscFile.read()

        return [viewdscfile]


class savePrm_files(Resource):
    def post(self):
        data = request.get_json(force=True)
        prmFile = data['procName']
        prmContent = data['currentParams']
        prmFile = prmFile.lstrip('["').rstrip('"]')
        dest_file = os.path.join(gg_home, 'dirprm', prmFile + '.prm')
        globalsPath = os.path.join(gg_home, prmFile)
        if prmFile == 'GLOBALS':
            with open(globalsPath, 'w') as prmFile:
                viewprmfile = prmFile.write(prmContent)
        else:
            backupfile = dest_file + "." + datetime.now().strftime("%Y-%m-%d_%H%M%S")
            shutil.copy(dest_file, backupfile)
            with open(dest_file, 'w') as prmFile:
                viewprmfile = prmFile.write(prmContent)

        return ['Parameter File  Saved']


class savePrm_files_Temp(Resource):
    def post(self):
        data = request.get_json(force=True)
        prmFile = data['prmFile']
        prmContent = data['prmContent']
        prmFile = prmFile.lstrip('["').rstrip('"]')
        dest_file = os.path.join(gg_home, 'dirprm', prmFile)
        globalsPath = os.path.join(gg_home, prmFile)
        if prmFile == 'GLOBALS':
            with open(globalsPath, 'w') as prmFile:
                viewprmfile = prmFile.write(prmContent)
        else:
            backupfile = dest_file + "." + datetime.now().strftime("%Y-%m-%d_%H%M%S")
            shutil.copy(dest_file, backupfile)
            with open(dest_file, 'w') as prmFile:
                viewprmfile = prmFile.write(prmContent)

        return ['Parameter File  Saved']


class get_Version(Resource):
    def get(self):
        getVer = subprocess.getoutput(ggsci_bin + " -v")
        with open(os.path.join(oneplace_home, 'getVersion'), 'w') as verFileIn:
            getVerfile = verFileIn.write(getVer)
        with open(os.path.join(oneplace_home, 'getVersion')) as verFileOut:
            for i, line in enumerate(verFileOut):
                if 'Version' in line:
                    ggVer = line.split('Version', 1)[-1]
                    ggVer1 = ggVer.strip().split('.')
                    ggVersion = ggVer1[0] + ggVer1[1]
        return [ggVer, ggVersion]


class MemUsagebyProcess(Resource):
    def post(self):
        data = request.get_json(force=True)
        processName = data['processName']
        read_bytes = data['read_bytes']
        write_bytes = data['write_bytes']
        read_count = data['read_count']
        write_count = data['write_count']
        extpidfiles = []
        pidlist = []
        memProcessDet = {}
        cpuProcessDet = {}
        cpuThreadDet = []
        ioProcessDet = {}
        pid_dir = os.path.join(gg_home, 'dirpcs', processName)
        for file in glob.glob(pid_dir + '.pc*'):
            extpidfiles.append(file)
        i = 0
        total_process_mem = 0
        processTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for file in extpidfiles:
            process = file.split('/')
            process = process[-1].split('.')[0]
            with open(file) as infile:
                for line in infile:
                    line = line.strip()
                    if len(line) > 2:
                        line = line.split()
                        pid = line[line.index('PID') + 1]
                        try:
                            p = psutil.Process(int(pid))
                            memProcessDet['group'] = process
                            memProcessDet['rss'] = bytes2human(p.memory_full_info()[0])
                            memProcessDet['vms'] = bytes2human(p.memory_full_info()[1])
                            memProcessDet['swap'] = bytes2human(p.memory_full_info()[9])
                            memProcessDet['lib'] = bytes2human(p.memory_info()[5])
                            memProcessDet['uss'] = bytes2human(p.memory_full_info()[7])
                            memProcessDet['mem'] = round(p.memory_percent(), 2)
                            memProcessDet['rssper'] = p.memory_percent(memtype="rss")
                            memProcessDet['vmsper'] = p.memory_percent(memtype="vms")
                            memProcessDet['ussper'] = p.memory_percent(memtype="uss")
                            memProcessDet['inctime'] = processTime
                            cpu_percent = p.cpu_percent(interval=0.1)
                            cpuProcessDet['process'] = process
                            cpuProcessDet['pid'] = pid
                            cpuProcessDet['user'] = p.cpu_times()[0]
                            cpuProcessDet['kernel'] = p.cpu_times()[1]
                            cpuProcessDet['iowait'] = p.cpu_times()[4]
                            cpu_time = sum(p.cpu_times())
                            for t in p.threads():
                                cpu = round(cpu_percent * ((t.system_time + t.user_time) / cpu_time), 1)
                                cpuSys = round(cpu_percent * (round(t.system_time / cpu_time)))
                                cpuUser = round(cpu_percent * (round(t.user_time / cpu_time)))
                                cpuThreadDet.append({'group': process, 'pid': pid,
                                                     'thread': t[0], 'cpu': cpu, 'cpusys': cpuSys, 'cpuuser': cpuUser,
                                                     'inctime': processTime})
                            io_counters = p.io_counters()
                            if read_bytes > 0:
                                delta_read_bytes = (io_counters[2] - read_bytes)
                            else:
                                delta_read_bytes = 0
                            if write_bytes > 0:
                                delta_write_bytes = (io_counters[3] - write_bytes)
                            else:
                                delta_write_bytes = 0
                            if read_count > 0:
                                delta_read_count = (io_counters[0] - read_count)
                            else:
                                delta_read_count = 0
                            if write_count > 0:
                                delta_write_count = (io_counters[1] - write_count)
                            else:
                                delta_write_count = 0
                            disk_usage_process = io_counters[2] + io_counters[3]  # read_bytes + write_bytes
                            ioProcessDet['group'] = process
                            ioProcessDet['diskio'] = disk_usage_process
                            ioProcessDet['read_count'] = io_counters[0]
                            ioProcessDet['write_count'] = io_counters[1]
                            ioProcessDet['delta_read_count'] = delta_read_count
                            ioProcessDet['delta_write_count'] = delta_write_count
                            ioProcessDet['read_bytes'] = io_counters[2]
                            ioProcessDet['write_bytes'] = io_counters[3]
                            ioProcessDet['delta_read_bytes'] = delta_read_bytes
                            ioProcessDet['delta_write_bytes'] = delta_write_bytes
                            ioProcessDet['inctime'] = processTime
                        except psutil.NoSuchProcess:
                            pass
        return [memProcessDet, cpuProcessDet, cpuThreadDet, ioProcessDet]


class MemUsage(Resource):
    def get(self):
        extpidfiles = []
        pidlist = []
        memDet = []
        cpuDet = []
        ioDet = []
        pid_dir = os.path.join(gg_home, 'dirpcs')
        for file in glob.glob(pid_dir + '/*.pc*'):
            extpidfiles.append(file)
        i = 0
        total_process_mem = 0
        processTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for file in extpidfiles:
            process = file.split('/')
            process = process[-1].split('.')[0]
            with open(file) as infile:
                for line in infile:
                    line = line.strip()
                    if len(line) > 2:
                        line = line.split()
                        pid = line[line.index('PID') + 1]
                        #                 pid = line.split('PID',1)[-1].strip()
                        try:
                            p = psutil.Process(int(pid))
                            memDet.append(
                                {'id': i, 'group': process, 'rss': round(p.memory_full_info()[0] / (1024 * 1024)),
                                 'uss': round(p.memory_full_info()[7] / (1024 * 1024)),
                                 'mem': round(p.memory_percent(), 3), 'inctime': processTime})
                            total_process_mem = total_process_mem + p.memory_percent()
                            cpu_percent = p.cpu_percent(interval=.2)
                            cpuDet.append({'id': i, 'group': process, 'cpu': cpu_percent, 'inctime': processTime})
                            io_counters = p.io_counters()
                            disk_bytes_process = io_counters[2] + io_counters[3]  # read_bytes + write_bytes
                            disk_count_process = io_counters[0] + io_counters[1]  # read_count + write_count
                            ioDet.append({'id': i, 'group': process, 'diskbytes': disk_bytes_process,
                                          'diskcount': disk_count_process, 'inctime': processTime})
                            i = i + 1
                        except psutil.NoSuchProcess:
                            pass
        cpuUser = psutil.cpu_times_percent(interval=.2)[0]
        cpuSystem = psutil.cpu_times_percent(interval=.2)[2]
        loadavg = psutil.getloadavg()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        total = round(mem[0] / (1024 * 1024 * 1024))
        available = round(mem[1] / (1024 * 1024 * 1024))
        used = round(mem[3] / (1024 * 1024 * 1024))
        free = round(mem[4] / (1024 * 1024 * 1024))
        percent = mem[2]
        swap_tot = round(swap[0] / (1024 * 1024 * 1024))
        swap_used = round(swap[1] / (1024 * 1024 * 1024))
        swap_free = round(swap[2] / (1024 * 1024 * 1024))
        swap_percent = round(swap[3] / (1024 * 1024 * 1024))
        memutil = {}
        memutil = {'total': total, 'available': available, 'used': used, 'free': free, 'percent': percent,
                   'swap_tot': swap_tot, 'swap_used': swap_used, 'swap_free': swap_free, 'swap_percent': swap_percent,
                   'cpuUser': cpuUser, 'cpuSystem': cpuSystem, 'loadavg': loadavg}
        return [memDet, memutil, cpuDet, ioDet, round(total_process_mem, 1)]


class dbConn(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbButton = data['dbButton']
        msg = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            if dbButton == 'addDB':
                dbname = data['dbname']
                user = data['username']
                passwd = data['passwd']
                passwd = cipher.encrypt(passwd).decode('utf-8')
                servicename = data['servicename']
                cursor.execute('insert into CONN values(:dbname,:user,:passwd,:servicename)',
                               {"dbname": dbname, "user": user, "passwd": passwd, "servicename": servicename})
                msg = 'Database Details Added'
                conn.commit()
            elif dbButton == 'editDB':
                dbname = data['dbname']
                user = data['username']
                passwd = data['passwd']
                passwd = cipher.encrypt(passwd).decode('utf-8')
                servicename = data['servicename']
                cursor.execute('insert OR replace into CONN values(:dbname,:user,:passwd,:servicename)',
                               {"dbname": dbname, "user": user, "passwd": passwd, "servicename": servicename})
                msg = 'Database Details Updated'
                conn.commit()
            elif dbButton == 'delDB':
                dbname = data['dbname']
                cursor.execute('delete from CONN where dbname=:dbname', {"dbname": dbname})
                msg = 'Database Details Deleted'
                conn.commit()
            elif dbButton == 'viewDB':
                dbname = data['dbname']
                con = ''
                try:
                    val = selectConn(dbname)
                    con = val[0]
                    msg = {}
                    cursor = con.cursor()
                    cursor.execute('''select db_name() AS DatabaseName, @@servername AS ServerName, @@version AS VersionInfo''')
                    result = cursor.fetchone()
                    if result:
                        msg['DBNAME'] = result[0]
                        # msg['DBFile'] = dbName[1]
                        msg['ProductName'] = result[1]
                        msg['ProductVersion'] = result[2]
                        # msg['Platform'] = dbName[4]
                        # msg['PlatformVer'] = dbName[5]
                        # msg['ServerEdition'] = dbName[6]
                except Exception as e:
                    msg = str(e)
                    print(msg)
                finally:
                    if con:
                        cursor.close()
                        con.close()
        except sqlite3.DatabaseError as e:
            msg = str(e)
        finally:
            if conn:
                try:
                    cursor.close()
                except Exception as e:
                    print(f"Error closing cursor: {e}")
                finally:
                    conn.close()
        return [msg]


class selectDBDet(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        msg = []
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('select user,servicename from CONN where dbname=:dbname', {"dbname": dbname})
            db_row = cursor.fetchone()
            if db_row:
                msg.append({'user': db_row[0], 'servicename': db_row[1]})
        except sqlite3.DatabaseError as e:
            msg.append(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()
        return [msg]


class dbDet(Resource):
    def get(self):
        dbname = []
        conn = sqlite3.connect('conn.db')
        db_det = 'select dbname from CONN'
        db_det_fetch = pd.read_sql_query(db_det, conn)
        conn.close()
        return [db_det_fetch.to_dict('records')]


class RepType(Resource):
    def get(self):
        InfoRep = subprocess.getoutput("echo -e 'info replicat *'|" + ggsci_bin)
        with  open(oneplace_home + "/infopr.out", mode='w') as outfile2:
            outfile2.write(InfoRep)
        with  open(oneplace_home + "/infopr.out", mode='r') as infile:
            Rep_Data = []
            RepType = None
            for line in infile:
                if 'REPLICAT' in line:
                    RepName = line.split()[1]
                elif 'INTEGRATED' in line:
                    RepType = 'INTEGRATED'
                elif 'Parallel' in line:
                    RepType = 'PARALLEL'
                if 'Process' in line:
                    PID = line.split()[2]
                    if RepType == 'PARALLEL':
                        Rep_Data.append({'RepName': RepName, 'RepType': RepType, 'PID': PID})
                        RepType = None
                    elif RepType == None:
                        Rep_Data.append({'RepName': RepName, 'RepType': 'CLASSIC', 'PID': PID})
        return [Rep_Data]


class CRTshoot(Resource):
    def post(self):
        data = request.get_json(force=True)
        repName = data['repName']
        sql_det_fetch = ''
        ash_det_fetch = ''
        prm_dir = os.path.join(gg_home, 'dirprm')
        for name in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
            name = name.split('/')[-1]
            if re.match(name, repName + '.prm', re.IGNORECASE):
                with  open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('useridalias', line, re.IGNORECASE):
                            alias = line.split()[1]
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": alias})
        db_row = cursor.fetchone()
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            passwd = cipher.decrypt(passwd)
            servicename = db_row[2]
        con = cx_Oracle.connect(user, passwd, servicename)
        conn.close()
        db_det = '''SELECT db.DBid,db.name DBNAME, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,
                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  
                           i.instance_number instance,db.database_role,db.current_scn
                    from v$database db,v$instance i, v$version v
                    where banner like 'Oracle%' '''
        db_det_fetch = pd.read_sql_query(db_det, con)
        db_det_fetch = db_det_fetch.to_dict('records')
        PRpidfiles = []
        pid_dir = os.path.join(gg_home, 'dirpcs')
        for file in glob.glob(pid_dir + '/' + repName + '.pcr'):
            PRpidfiles.append(file)
        pidlist = []
        for file in PRpidfiles:
            process = file.split('/')
            process = process[-1].split('.')[0]
            with open(file) as infile:
                for line in infile:
                    line = line.strip()
                    if len(line) > 2:
                        pid = line.split('PID', 1)[-1].strip()
                        pidlist.append({'NAME': process, 'PROCESS': pid})
        df = pd.DataFrame(pidlist, columns=['NAME', 'PROCESS'])
        bindNames = [":" + str(i + 1) for i in range(len(pidlist))]
        pids = [pid['PROCESS'] for pid in pidlist]
        session_det = """SELECT s.sid sid,s.serial# serial,p.spid spid,s.sql_id sql_id ,
                                s.event event ,s.last_call_et call,s.process process 
                                from gv$session s , gv$process p  
                                where s.paddr = p.addr and s.process in (%s)""" % (",".join(bindNames))
        session_det_fetch = pd.read_sql_query(session_det, con, params=[*pids])
        session_det_fetch = pd.merge(session_det_fetch, df)
        session_det_fetch = session_det_fetch.to_dict('records')
        param = {'SESSION_ID': session_det_fetch[0]['SID'], 'SESSION_SERIAL': session_det_fetch[0]['SERIAL']}
        ash_det = """SELECT INST_ID,NVL(event,'ON CPU') event,COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60 and SESSION_ID = :SESSION_ID  and SESSION_SERIAL#= :SESSION_SERIAL
                             group by inst_id,event"""
        ash_det_fetch = pd.read_sql_query(ash_det, con, params=[param["SESSION_ID"], param["SESSION_SERIAL"]])
        ash_det_fetch = ash_det_fetch.astype(str)
        ash_det_fetch = ash_det_fetch.to_dict('records')
        sql_det = """select SQL_FULLTEXT from gv$sql where sql_id=:sqlid"""
        param = {'sqlid': session_det_fetch[0]['SQL_ID']}
        sql_det_fetch = pd.read_sql_query(sql_det, con, params=[param['sqlid']])
        sql_det_fetch = sql_det_fetch.astype(str)
        sql_det_fetch = sql_det_fetch.to_dict('records')
        InfoPstack = subprocess.getoutput("pstack " + min(pids))
        with  open(os.path.join(oneplace_home, "crpstack.out"), 'w') as outfile2:
            outfile2.write(InfoPstack)
        with  open(os.path.join(oneplace_home, "crpstack.out")) as infile:
            Pstack = {}
            for line in infile:
                if line.startswith('Thread '):
                    line1 = line.split()
                    copy = True
                    continue
                elif line.startswith('Thread '):
                    copy = False
                    continue
                elif copy:
                    Pstack.setdefault(line1[1], []).append(line)
        return [db_det_fetch, session_det_fetch, Pstack, ash_det_fetch, sql_det_fetch]


class PRTshoot(Resource):
    def post(self):
        data = request.get_json(force=True)
        repName = data['repName']
        prm_dir = os.path.join(gg_home, 'dirprm')
        for name in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
            name = name.split('/')[-1]
            if re.match(name, repName + '.prm', re.IGNORECASE):
                with  open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('useridalias', line, re.IGNORECASE):
                            alias = line.split()[1]
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": alias})
        db_row = cursor.fetchone()
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            servicename = db_row[2]
        con = cx_Oracle.connect(user, passwd, servicename)
        conn.close()
        db_det = '''SELECT db.DBid,db.name DBNAME, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,
                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  
                           i.instance_number instance,db.database_role,db.current_scn
                    from v$database db,v$instance i, v$version v
                    where banner like 'Oracle%' '''
        db_det_fetch = pd.read_sql_query(db_det, con)
        PRpidfiles = []
        pid_dir = os.path.join(gg_home, 'dirpcs')
        for file in glob.glob(pid_dir + '/' + repName + '*.pcr'):
            PRpidfiles.append(file)
        pidlist = []
        for file in PRpidfiles:
            process = file.split('/')
            process = process[-1].split('.')[0]
            with open(file) as infile:
                for line in infile:
                    line = line.strip()
                    if len(line) > 2:
                        pid = line.split('PID', 1)[-1].strip()
                        pidlist.append({'NAME': process, 'PROCESS': pid})
        df = pd.DataFrame(pidlist, columns=['NAME', 'PROCESS'])
        bindNames = [":" + str(i + 1) for i in range(len(pidlist))]
        pids = [pid['PROCESS'] for pid in pidlist]
        session_det = """SELECT s.sid sid,s.serial# serial,p.spid spid,s.sql_id sql_id ,s.event event ,s.last_call_et call,s.process process
                    from gv$session s , gv$process p  
                    where s.paddr = p.addr and 
                    s.process in (%s)""" % (",".join(bindNames))
        session_det_fetch = pd.read_sql_query(session_det, con, params=[*pids])
        session_det_fetch = pd.merge(session_det_fetch, df)
        InfoPRDepInfo = subprocess.getoutput("echo -e 'send '" + repName + ",depinfo |" + ggsci_bin)
        with  open(oneplace_home + "/prdepinfo.out", mode='w') as outfile:
            outfile.write(InfoPRDepInfo)
        with  open(oneplace_home + "/prdepinfo.out", mode='r') as infile:
            Scheduler_List = []
            RunningTxn_List = []
            WaitInfo = []
            copy = False
            for line in infile:
                if 'Scheduler' in line:
                    line = line.strip()
                    line = line.rstrip(':')
                    line = line.split()[1]
                    Scheduler_List.append(line)
                elif 'Group' in line:
                    line = line.strip()
                    line = line.split(':')
                    Txn = line[1].split(',')
                    RunningTxn_List.append({'Group': line[0], 'Txn': Txn})
                elif 'Waiting' in line:
                    copy = True
                elif copy:
                    WaitInfo.append(line.strip())
        Txn_List = []
        WaitTxn_List = []
        WaitGraph = []
        i = 0
        for name in WaitInfo:
            name = name.split()
            if len(name) > 1:
                Txn_List.append(name[3])
                WaitTxn_List.append(name[10])
                WaitGraph.append({'id': i, 'start': name[3], 'end': name[10], 'category': '0'})
                i = i + 1
        Txn_Data = []
        [Txn_Data.append(x) for x in Txn_List if x not in Txn_Data]
        WaitTxn_Data = []
        [WaitTxn_Data.append(x) for x in WaitTxn_List if x not in WaitTxn_Data]
        NodeData = []
        for name in Txn_Data:
            NodeData.append({'id': name, 'category': 'Txn'})
        for name in WaitTxn_Data:
            NodeData.append({'id': name, 'category': 'WaitTxn'})
        InfoPstack = subprocess.getoutput("pstack " + min(pids))
        with  open(oneplace_home + "/prpstack.out", mode='w') as outfile2:
            outfile2.write(InfoPstack)
        with  open(oneplace_home + "/prpstack.out", mode='r') as infile:
            Pstack = {}
            for line in infile:
                if line.startswith('Thread '):
                    line1 = line.split()
                    copy = True
                    continue
                elif line.startswith('Thread '):
                    copy = False
                    continue
                elif copy:
                    Pstack.setdefault(line1[1], []).append(line)
        return [db_det_fetch.to_dict('records'), session_det_fetch.to_dict('records'), Scheduler_List, RunningTxn_List,
                NodeData, WaitGraph, Pstack]


class ReqArchLog(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        req_scn = data['req_scn']
        val = selectConn(dbname)
        con = val[0]
        try:
            archive_log = '''select NAME,THREAD#,SEQUENCE# ,FIRST_TIME , NEXT_TIME,FIRST_CHANGE#, NEXT_CHANGE#,DELETED
                          from v$archived_log where :req_scn between FIRST_CHANGE# and NEXT_CHANGE#'''
            param = {"req_scn": req_scn}
            archive_log_fetch = pd.read_sql_query(archive_log, con, params=[param["req_scn"]])
            archive_log_fetch = archive_log_fetch.astype(str)
            archive_log_fetch = archive_log_fetch.to_dict('records')
        except cx_Oracle.DatabaseError as e:
            archive_log_fetch = str(e)
        finally:
            if con:
                con.close()
        return [archive_log_fetch]


class IETshoot(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        db_main_ver = val[1]
        db_minor_ver = val[2]
        if 'ORA-' in db_main_ver:
            ext_stat_fetch = db_main_ver
            ext_params_fetch = ''
            ext_mem_fetch = ''
            streams_pool_fetch = ''
            streams_pool_stats_fetch = ''
            logmnr_mem_fetch = ''
            long_running_fetch = ''
            reader_event_fetch = ''
            builder_event_fetch = ''
            preparer_event_fetch = ''
            db_main_ver = ''
            db_minor_ver = ''
            db_det = ''
            logmnr_stats_fetch = ''
            merger_event_fetch = ''
            reader_ash_fetch = ''
        else:
            try:
                db_det = '''SELECT db.DBid,db.name, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,
                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  
                           i.instance_number instance,db.database_role,db.current_scn, db.min_required_capture_change# min_required_capture_change
                    from v$database db,v$instance i, v$version v
                    where banner like 'Oracle%' '''
                db_det_fetch = pd.read_sql_query(db_det, con)
                db_det = db_det_fetch.to_dict('records')
                if int(db_main_ver) == 11:
                    ext_stat = '''select  SYSDATE Current_time,c.client_name extract_name,c.capture_name, 
                         c.capture_user,
                         c.capture_type, 
                         decode(cp.value,'N','NO', 'YES') Real_time_mine,
                         c.version,
                         c.required_checkpoint_scn,
                         (case 
                          when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                          else 'V1'
                          end) protocol,
                          c.logminer_id,
                          o.created registered,
                          o.last_ddl_time,
                          c.status,
                          g.STATE State,
                         (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                         g.bytes_of_redo_mined/1024/1024 mined_MB,
                         g.bytes_sent/1024/1024 sent_MB,
                         g.startup_time,
                         g.inst_id,
                         c.source_database
                         from dba_capture c, dba_objects o,
                              gv$goldengate_capture g,
                              dba_capture_parameters cp
                         where
                              c.capture_name=g.capture_name
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.status='ENABLED' and c.purpose='GoldenGate Capture'
                              and c.capture_name = o.object_name
                              and c.capture_name=g.capture_name
                         union all
                         select  SYSDATE Current_time,c.client_name extract_name,c.capture_name,
                         c.capture_user,  
                         c.capture_type, 
                         decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                         c.version,
                         c.required_checkpoint_scn,
                         'Unavailable',
                         c.logminer_id,
                         o.created registered,
                         o.last_ddl_time,
                         c.status,
                         'Unavailable',
                         NULL,
                         NULL,
                         NULL,
                         NULL,
                         NULL,
                         c.source_database
                         from dba_capture c, dba_objects o,
                              dba_capture_parameters cp
                         where
                         c.status in ('DISABLED','ABORTED') and c.purpose='GoldenGate Capture'
                         and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                         and c.capture_name = o.object_name
                         order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates 
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency                  
                            from dba_capture_parameters cp, dba_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                            group by cp.capture_name'''

                    ext_stat_fetch = pd.read_sql_query(ext_stat, con)
                    ext_stat_fetch = ext_stat_fetch.astype(str)
                    ext_params_fetch = pd.read_sql_query(ext_params, con)
                elif int(db_main_ver) == 12 and int(db_minor_ver) == 1:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name, 
                                 c.capture_user,
                                 c.capture_type, 
                                 decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                 c.version,
                                 c.required_checkpoint_scn,
                                 (case 
                                  when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                  else 'V1'
                                  end) protocol,
                                 c.logminer_id,
                                 o.created registered,
                                 o.last_ddl_time,
                                 c.status,
                                 g.STATE  State,
                                 (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                 g.bytes_of_redo_mined/1024/1024 mined_MB,
                                 g.bytes_sent/1024/1024 sent_MB,
                                 g.startup_time,
                                 g.con_id,
                                 g.inst_id,
                                 c.source_database
                         from cdb_capture c, cdb_objects o,
                              gv$goldengate_capture g,
                              cdb_capture_parameters cp
                         where
                              c.capture_name=g.capture_name
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                              and c.capture_name=o.object_name
                              and c.capture_name=g.capture_name
                         union all
                         select  SYSDATE Current_time, c.client_name extract_name,c.capture_name, 
                                 c.capture_user,
                                 c.capture_type, 
                                 decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                 c.version,
                                 c.required_checkpoint_scn,
                                 'Unavailable',
                                 c.logminer_id,
                                 o.created registered,
                                 o.last_ddl_time,
                                 c.status,
                                 'Unavailable',
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 NULL,
                                 c.source_database
                         from cdb_capture c, cdb_objects o,
                              cdb_capture_parameters cp
                         where
                              c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                              and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                              and c.capture_name=o.object_name
                              order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates 
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency                  
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                            group by cp.capture_name'''
                    ext_stat_fetch = pd.read_sql_query(ext_stat, con)
                    ext_stat_fetch = ext_stat_fetch.astype(str)
                    ext_params_fetch = pd.read_sql_query(ext_params, con)
                elif int(db_main_ver) == 12 and int(db_minor_ver) == 2:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name, 
                                  c.capture_user,
                                  c.capture_type, 
                                  decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  (case 
                                   when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                   else 'V1'
                                   end) protocol,
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  g.STATE State,
                                  (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                  g.bytes_of_redo_mined/1024/1024 mined_MB,
                                  g.bytes_sent/1024/1024 sent_MB,
                                  g.startup_time,
                                  g.con_id,
                                  g.inst_id,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               gv$goldengate_capture g,
                               cdb_capture_parameters cp
                          where
                               c.capture_name=g.capture_name
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                               and c.capture_name=o.object_name
                               and c.capture_name=g.capture_name
                          union all
                          select  SYSDATE Current_time, c.client_name extract_name,c.capture_name, 
                                  c.capture_user,
                                  c.capture_type, 
                                  decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  'Unavailable',
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  'Unavailable',
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               cdb_capture_parameters cp
                          where
                               c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.capture_name=o.object_name
                               order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates 
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency                  
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                           group by cp.capture_name'''
                elif int(db_main_ver) > 12:
                    ext_stat = '''select  SYSDATE Current_time,  c.client_name extract_name,c.capture_name, 
                                  c.capture_user,
                                  c.capture_type, 
                                  decode(cp.value,'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  (case 
                                   when g.sid=g.server_sid and g.serial#=g.server_serial# then 'V2'
                                   else 'V1'
                                   end) protocol,
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  g.STATE State,
                                  (SYSDATE- g.capture_message_create_time)*86400 capture_lag,
                                  g.bytes_of_redo_mined/1024/1024 mined_MB,
                                  g.bytes_sent/1024/1024 sent_MB,
                                  g.startup_time,
                                  g.con_id,
                                  g.inst_id,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               gv$goldengate_capture g,
                               cdb_capture_parameters cp
                          where
                               c.capture_name=g.capture_name
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.status='ENABLED'  and c.purpose='GoldenGate Capture'
                               and c.capture_name=o.object_name
                               and c.capture_name=g.capture_name
                          union all
                          select  SYSDATE Current_time, c.client_name extract_name,c.capture_name, 
                                  c.capture_user,
                                  c.capture_type, 
                                  decode(cp.value, 'N','NO', 'YES') Real_time_mine,
                                  c.version,
                                  c.required_checkpoint_scn,
                                  'Unavailable',
                                  c.logminer_id,
                                  o.created registered,
                                  o.last_ddl_time,
                                  c.status,
                                  'Unavailable',
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  NULL,
                                  c.source_database
                          from cdb_capture c, cdb_objects o,
                               cdb_capture_parameters cp
                          where
                               c.status in ('DISABLED', 'ABORTED') and c.purpose='GoldenGate Capture'
                               and c.capture_name=cp.capture_name and cp.parameter='DOWNSTREAM_REAL_TIME_MINE'
                               and c.capture_name=o.object_name
                               order by extract_name'''
                    ext_params = '''select cp.capture_name,substr(cp.capture_name,9,8)  extract_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size
                                  ,max(case when parameter='EXCLUDETAG' then value end) excludetag
                                  ,max(case when parameter='EXCLUDEUSER' then value end) excludeuser
                                  ,max(case when parameter='GETAPPLOPS' then value end) getapplops
                                  ,max(case when parameter='GETREPLICATES' then value end) getreplicates 
                                  ,max(case when parameter='_CHECKPOINT_FREQUENCY' then value end) checkpoint_frequency                  
                            from cdb_capture_parameters cp, cdb_capture c where c.capture_name=cp.capture_name
                                 and c.purpose='GoldenGate Capture'
                           group by cp.capture_name'''
                ext_mem = '''select session_name, available_txn, delivered_txn,
                             available_txn-delivered_txn as difference,
                             builder_work_size, prepared_work_size,
                             used_memory_size , max_memory_size,
                             (used_memory_size/max_memory_size)*100 as used_mem_pct
                             FROM gv$logmnr_session order by session_name'''
                streams_pool = '''select inst_id, TOTAL_MEMORY_ALLOCATED/(1024*1024) as used_MB,  CURRENT_SIZE/(1024*1024) as  max_MB,  
                          decode(current_size, 0,to_number(null),
                          (total_memory_allocated/current_size)*100) as pct_Streams_pool from gv$streams_pool_statistics'''
                streams_pool_stats = '''select capture_name,sga_used/(1024*1024) as used, sga_allocated/(1024*1024) as alloced
                                , (sga_used/sga_allocated)*100 as pct,total_messages_captured as msgs_captured, 
                                total_messages_enqueued as msgs_enqueued from gv$goldengate_capture order by capture_name'''
                logmnr_mem = '''select session_name, l.USED_MEMORY_SIZE/(1024*1024) as used_MB, l.MAX_MEMORY_SIZE/(1024*1024) as max_MB,  
                        (l.USED_MEMORY_SIZE/l.MAX_MEMORY_SIZE)*100 as pct_logminer_mem_used,s.current_size/(1024*1024) streams_size,decode(s.current_size, 0,
                        to_number(null),(l.used_memory_size/s.current_size)*100) pct_streams_pool 
                        from gv$logmnr_session l, gv$streams_pool_statistics s 
                        where l.inst_id=s.inst_id order by session_name'''

                long_running = '''select t.inst_id, sid||','||serial# sid,xidusn||'.'||xidslot||'.'||xidsqn xid, 
                          (sysdate -  start_date ) * 1440 runlength ,t.start_scn,terminal,
                          program from gv$transaction t, gv$session s 
                          where t.addr=s.taddr and (sysdate - start_date) * 1440 > 20 order by runlength desc'''
                reader_event = '''SELECT c.capture_name || ' - reader' as logminer_reader_name, 
                                 lp.sid,lp.SERIAL# SERIAL,lp.SPID,sess_capture.p2text,sess_capture.p2,sess_capture.p3text,sess_capture.p3,LATCHWAIT, LATCHSPIN,
                                 sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT,
                                p2,p2text,p3,p3text
                                FROM  gv$session
                                GROUP BY sid, serial#, event , p2,p2text,p3,p3text) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'reader' and lp.session_id = c.logminer_id
                          ORDER BY logminer_reader_name'''
                reader_ash = '''SELECT c.inst_id, c.capture_name || ' - reader' as logminer_reader_name
                              , ash_capture.event_count
                              , ash_total.total_count
                              , round(ash_capture.event_count*100/NULLIF(ash_total.total_count,0),2) as Percentage
                              , 'YES' busy
                              , nvl(ash_capture.event,'on CPU or wait on CPU') event
                        FROM (SELECT INST_ID, SESSION_ID, SESSION_SERIAL#, EVENT, COUNT(sample_time) AS EVENT_COUNT
                              FROM  gv$active_session_history
                              WHERE sample_time > sysdate - 30/24/60
                              GROUP BY inst_id, session_id, session_serial#, event) ash_capture
                          , (SELECT INST_ID, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                             FROM  gv$active_session_history
                             WHERE sample_time > sysdate - 30/24/60
                             group by inst_id) ash_total
                           , gv$logmnr_process lp
                           , gv$goldengate_capture c
                        WHERE lp.SID        = ash_capture.SESSION_ID
                        AND   lp.serial#    = ash_capture.SESSION_SERIAL#
                        AND   lp.role       = 'reader'
                        AND   lp.session_id = c.logminer_id
                        AND   c.inst_id = ash_capture.inst_id
                        AND   c.inst_id = ash_total.inst_id
                        AND   c.inst_id = lp.inst_id
                        ORDER BY c.inst_id, logminer_reader_name, Percentage'''
                builder_event = '''SELECT c.capture_name || ' - builder' as logminer_builder_name, 
                                  lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                  sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'builder' and lp.session_id = c.logminer_id
                          ORDER BY logminer_builder_name'''
                preparer_event = '''SELECT c.capture_name || ' - preparer' as logminer_preparer_name, 
                                 lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                 sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'preparer' and lp.session_id = c.logminer_id
                          ORDER BY logminer_preparer_name'''
                merger_event = '''SELECT c.capture_name || ' - merger' as logminer_merger_name,
                                  lp.sid,lp.SERIAL# SERIAL,lp.SPID , LATCHWAIT, LATCHSPIN,
                                  sess_capture.event EVENT
                          FROM (SELECT SID,
                                SERIAL#,
                                EVENT
                                FROM  gv$session
                                GROUP BY sid, serial#, event) sess_capture,
                          v$logmnr_process lp, v$goldengate_capture c
                          WHERE lp.SID = sess_capture.sid
                                AND lp.serial# = sess_capture.SERIAL#
                                AND lp.role = 'merger' and lp.session_id = c.logminer_id
                          ORDER BY logminer_merger_name'''

                logmnr_stats = '''select c.capture_name, name, value 
                          from gv$goldengate_capture c, gv$logmnr_stats l
                          where c.logminer_id = l.session_id 
                          order by capture_name,name'''

                ext_stat_fetch = pd.read_sql_query(ext_stat, con)
                ext_stat_fetch = ext_stat_fetch.astype(str)
                ext_stat_fetch = ext_stat_fetch.to_dict('records')
                ext_params_fetch = pd.read_sql_query(ext_params, con)
                ext_params_fetch = ext_params_fetch.to_dict('records')
                ext_mem_fetch = pd.read_sql_query(ext_mem, con)
                ext_mem_fetch = ext_mem_fetch.to_dict('records')
                streams_pool_fetch = pd.read_sql_query(streams_pool, con)
                streams_pool_fetch = streams_pool_fetch.to_dict('records')
                streams_pool_stats_fetch = pd.read_sql_query(streams_pool_stats, con)
                streams_pool_stats_fetch = streams_pool_stats_fetch.to_dict('records')
                logmnr_mem_fetch = pd.read_sql_query(logmnr_mem, con)
                logmnr_mem_fetch = logmnr_mem_fetch.to_dict('records')
                long_running_fetch = pd.read_sql_query(long_running, con)
                long_running_fetch = long_running_fetch.astype(str)
                long_running_fetch = long_running_fetch.to_dict('records')
                reader_event_fetch = pd.read_sql_query(reader_event, con)
                reader_event_fetch = reader_event_fetch.to_dict('records')
                builder_event_fetch = pd.read_sql_query(builder_event, con)
                builder_event_fetch = builder_event_fetch.to_dict('records')
                preparer_event_fetch = pd.read_sql_query(preparer_event, con)
                preparer_event_fetch = preparer_event_fetch.to_dict('records')
                logmnr_stats_fetch = pd.read_sql_query(logmnr_stats, con)
                logmnr_stats_fetch = logmnr_stats_fetch.to_dict('records')
                merger_event_fetch = pd.read_sql_query(merger_event, con)
                merger_event_fetch = merger_event_fetch.to_dict('records')
                reader_ash_fetch = pd.read_sql_query(reader_ash, con)
                reader_ash_fetch = reader_ash_fetch.to_dict('records')
            except cx_Oracle.DatabaseError as e:
                ext_stat_fetch = str(e)
            except cx_Oracle.OperationalError as e:
                ext_stat_fetch = str(e)
            finally:
                if con:
                    con.close()
        return [ext_stat_fetch, ext_params_fetch, ext_mem_fetch, streams_pool_fetch, streams_pool_stats_fetch,
                logmnr_mem_fetch, long_running_fetch, reader_event_fetch, builder_event_fetch, preparer_event_fetch,
                db_main_ver, db_minor_ver, db_det, logmnr_stats_fetch, merger_event_fetch, reader_ash_fetch]


class IRTshoot(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        db_main_ver = val[1]
        if 'ORA-' in db_main_ver:
            rep_summary_fetch = db_main_ver
            rep_params_fetch = ''
            rep_open_trans_fetch = ''
            rep_open_trans_10000_fetch = ''
            db_det = ''
            rep_inbound_fetch = ''
            apply_receiver_fetch = ''
            apply_receiver_ash_fetch = ''
            apply_reader_fetch = ''
            apply_reader_ash_fetch = ''
            apply_reader_info_fetch = ''
            apply_coordinator_info_fetch = ''
            apply_coordinator_fetch = ''
            apply_server_info_fetch = ''
            apply_server_txn_fetch = ''
            apply_fts_info_fetch = ''
            apply_server_ash_fetch = ''
            apply_flow_fetch = ''
            apply_server_agg_fetch = ''
            apply_server_waits_fetch = ''
            apply_reader_lcr_dep_fetch = ''
        else:
            try:
                db_det = '''SELECT db.DBid,db.name, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,
                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  
                           i.instance_number instance,db.database_role
                    from v$database db,v$instance i, v$version v
                    where banner like 'Oracle%' '''
                db_det_fetch = pd.read_sql_query(db_det, con)
                db_det = db_det_fetch.to_dict('records')
                if int(db_main_ver) == 11:
                    rep_params = '''select apply_name,substr(apply_name,5,8) replicat_name,
                                   max(case when parameter='PARALLELISM' then value end) parallelism
                                  ,max(case when parameter='MAX_PARALLELISM' then value end) max_parallelism
                                  ,max(case when parameter='COMMIT_SERIALIZATION' then value end) commit_serialization
                                  ,max(case when parameter='EAGER_SIZE' then value end) eager_size
                                  ,max(case when parameter='_DML_REORDER' then value end) batchsql 
                                  ,max(case when parameter='_BATCHTRANSOPS' then value end) batchtransops                           
                                  ,max(case when parameter='BATCHSQL_MODE' then value end) batchsql_mode 
                                  ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size  
                                  ,max(case when parameter='OPTIMIZE_PROGRESS_TABLE' then value end) optimize_progress_table
                            from dba_apply_parameters ap, dba_goldengate_inbound ib where ib.server_name=ap.apply_name
                            group by apply_name'''
                    rep_inbound = '''select server_name                               
                               , processed_low_position                           
                               , applied_low_position                              
                               , applied_high_position                            
                               , oldest_position                                 
                               , applied_low_scn                         
                               , applied_time                                   
                               , applied_message_create_time                                             
                               , logbsn 
                         from dba_gg_inbound_progress 
                         order by server_name'''
                    rep_summary = '''select sysdate Current_time
                                 , ib.replicat_name
                                 , ib.server_name
                                 , ib.apply_user
                                 , ib.status
                                 , o.created registered
                                 , o.last_ddl_time
                                 , a.apply_tag
                                 , r.state ReceiverState
                                 , g.state
                                 , g.active_server_count
                                 , g.unassigned_complete_txns
                                 , g.lwm_message_create_time lwm
                                 , NVL(Round((g.hwm_message_create_time-g.lwm_message_create_time)*24*3600,2),0) SourceTSrange
                                 , g.lwm_time apply_time
                                 , NVL(Round((g.hwm_time-g.lwm_time)*24*3600,2),0) ApplyTSrange
                                 , g.startup_time
                                 , g.inst_id
                           from dba_goldengate_inbound ib, dba_objects o, dba_apply a, gv$gg_apply_coordinator g, gv$gg_apply_receiver r
                           where ib.server_name = g.apply_name
                           and   ib.status      = 'ATTACHED'
                           and   ib.server_name = o.object_name
                           and   ib.server_name = g.apply_name
                           and   ib.server_name = r.apply_name
                           and   ib.server_name = a.apply_name
                           union all
                           select sysdate Current_time
                                  , ib.replicat_name
                                  , ib.server_name
                                  , ib.apply_user
                                  , ib.status
                                  , o.created registered
                                  , o.last_ddl_time
                                  , a.apply_tag
                                  , 'Unavailable'
                                  , null
                                  , null
                                  , null
                                  , pg.applied_message_create_time
                                  , null SourceTSrange
                                  , pg.applied_time
                                  , null ApplyTSrange
                                  , null
                                  , null
                          from dba_goldengate_inbound ib, dba_objects o, dba_gg_inbound_progress pg, dba_apply a
                          where ib.status     != 'ATTACHED' 
                          and   ib.server_name = o.object_name
                          and   ib.server_name = a.apply_name
                          and   ib.server_name = pg.server_name(+)
                          order by replicat_name'''
                    apply_reader = '''SELECT ap.APPLY_NAME
                                     , s.sid,s.serial# as serial
                                     , SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) as PROCESS_NAME
                                     , r.ELAPSED_DEQUEUE_TIME
                                     , r.ELAPSED_SCHEDULE_TIME
                                     , r.STATE
                                     , r.oldest_transaction_id
                              FROM gV$GG_APPLY_READER r, gV$SESSION s, DBA_APPLY ap
                              WHERE r.SID = s.SID AND
                              r.SERIAL# = s.SERIAL# AND
                              r.inst_id = s.inst_id AND
                              r.APPLY_NAME = ap.APPLY_NAME
                              order by ap.apply_name'''
                    apply_coordinator = '''SELECT ap.APPLY_NAME,s.sid,s.serial# as serial
                                        , SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS
                                        , c.STARTUP_TIME
                                        , c.ELAPSED_SCHEDULE_TIME
                                        , c.STATE
                                        , c.TOTAL_RECEIVED RECEIVED
                                        , c.TOTAL_ASSIGNED ASSIGNED
                                        , c.unassigned_complete_txns unassigned
                                        , c.TOTAL_APPLIED APPLIED
                                        , c.TOTAL_ERRORS ERRORS
                                        , c.total_ignored
                                        , c.total_rollbacks
                                  FROM gV$GG_APPLY_COORDINATOR  c, gV$SESSION s, dba_APPLY ap
                                  WHERE c.SID = s.SID
                                  AND   c.SERIAL# = s.SERIAL#
                                  AND   c.APPLY_NAME = ap.APPLY_NAME
                                  order by ap.apply_name'''
                elif int(db_main_ver) > 11:
                    rep_params = '''select apply_name,substr(apply_name,5,8) replicat_name,
                                  max(case when parameter='PARALLELISM' then value end) parallelism
                                 ,max(case when parameter='MAX_PARALLELISM' then value end) max_parallelism
                                 ,max(case when parameter='COMMIT_SERIALIZATION' then value end) commit_serialization
                                 ,max(case when parameter='EAGER_SIZE' then value end) eager_size
                                 ,max(case when parameter='_DML_REORDER' then value end) batchsql              
                                 ,max(case when parameter='_BATCHTRANSOPS' then value end) batchtransops              
                                 ,max(case when parameter='BATCHSQL_MODE' then value end) batchsql_mode  
                                 ,max(case when parameter='MAX_SGA_SIZE' then value end) max_sga_size   
                                 ,max(case when parameter='OPTIMIZE_PROGRESS_TABLE' then value end) optimize_progress_table             
                           from cdb_apply_parameters ap, cdb_goldengate_inbound ib where ib.server_name=ap.apply_name
                                 group by apply_name'''
                    rep_inbound = '''select con_id, server_name
                                   , processed_low_position
                                   , applied_low_position
                                   , applied_high_position
                                   , oldest_position
                                   , applied_low_scn
                                   , applied_time
                                   , applied_message_create_time
                                   , logbsn
                            from cdb_gg_inbound_progress
                            order by server_name'''
                    rep_summary = '''select sysdate Current_time
                                   , o.con_id
                                   , ib.replicat_name
                                   , ib.server_name
                                   , ib.apply_user
                                   , ib.status
                                   , o.created registered
                                   , o.last_ddl_time
                                   , a.apply_tag
                                   , r.state ReceiverState
                                   , g.state state
                                   , g.active_server_count
                                   , g.unassigned_complete_txns
                                   , g.lwm_message_create_time lwm
                                   , NVL(Round((g.hwm_message_create_time-g.lwm_message_create_time)*24*3600,2),0) SourceTSrange
                                   , g.lwm_time apply_time
                                   , NVL(Round((g.hwm_time-g.lwm_time)*24*3600,2),0) ApplyTSrange
                                   , g.startup_time
                                   , g.inst_id
                            from cdb_goldengate_inbound ib, cdb_objects o, cdb_apply a, gv$gg_apply_coordinator g, gv$gg_apply_receiver r
                            where ib.server_name=g.apply_name
                            and   ib.status='ATTACHED'
                            and   ib.server_name=o.object_name
                            and   ib.server_name = g.apply_name
                            and   ib.server_name = r.apply_name
                            and   ib.server_name = a.apply_name
                            union all
                            select sysdate Current_time , o.con_id
                                   , ib.replicat_name
                                   , ib.server_name
                                   , ib.apply_user
                                   , ib.status
                                   , o.created registered
                                   , o.last_ddl_time
                                   , a.apply_tag
                                   , 'Unavailable' ReceiverState
                                   , null State
                                   , null server_count
                                   , null unassigned_complete_txns
                                   , pg.applied_message_create_time
                                   , null SourceTSrange
                                   , pg.applied_time
                                   , null ApplyTSrange
                                   , null startup_time
                                   , null inst_id
                            from cdb_goldengate_inbound ib,cdb_objects o, cdb_apply a, cdb_gg_inbound_progress pg
                            where ib.status !='ATTACHED'
                            and   ib.server_name=a.apply_name
                            and   ib.server_name=o.object_name
                            and   ib.server_name=pg.server_name(+)
                            order by replicat_name'''
                    apply_reader = '''SELECT ap.APPLY_NAME
                                        , s.sid,s.serial# as serial
                                        , SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME
                                        , r.ELAPSED_DEQUEUE_TIME
                                        , r.ELAPSED_SCHEDULE_TIME
                                        , r.STATE
                                        , r.oldest_transaction_id
                                  FROM gV$GG_APPLY_READER r, gV$SESSION s, CDB_APPLY ap
                                  WHERE r.SID = s.SID AND
                                        r.SERIAL# = s.SERIAL# AND
                                        r.inst_id = s.inst_id AND
                                        r.APPLY_NAME = ap.APPLY_NAME
                                  order by ap.apply_name'''
                    apply_coordinator = '''SELECT ap.APPLY_NAME,s.sid,s.serial# as serial
                                        , SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS
                                        , c.STARTUP_TIME
                                        , c.ELAPSED_SCHEDULE_TIME
                                        , c.STATE
                                        , c.TOTAL_RECEIVED RECEIVED
                                        , c.TOTAL_ASSIGNED ASSIGNED
                                        , c.unassigned_complete_txns unassigned
                                        , c.TOTAL_APPLIED APPLIED
                                        , c.TOTAL_ERRORS ERRORS
                                        , c.total_ignored
                                        , c.total_rollbacks
                                  FROM gV$GG_APPLY_COORDINATOR  c, gV$SESSION s, cdb_APPLY ap
                                  WHERE c.SID = s.SID
                                  AND   c.SERIAL# = s.SERIAL#
                                  AND   c.APPLY_NAME = ap.APPLY_NAME
                                  order by ap.apply_name'''
                apply_server_ash = '''SELECT a.inst_id, a.apply_name|| ' - '  || a.server_id as apply_name
                                   , ash.event_count
                                   , ash_total.total_count
                                   , ash.event_count*100/NULLIF(ash_total.total_count,0) as Percentage 
                                   , 'YES' busy
                                   , NVL(ash.event,'on CPU or wait on CPU') event
                              FROM (SELECT inst_id
                                         , SESSION_ID
                                         , SESSION_SERIAL#
                                         , EVENT
                                         , COUNT(sample_time) AS EVENT_COUNT
                                    FROM  gv$active_session_history
                                    WHERE sample_time > sysdate - 30/24/60
                                    GROUP BY inst_id, session_id, session_serial#, event) ash
                                  , (SELECT inst_id, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                                     FROM  gv$active_session_history
                                     WHERE sample_time > sysdate - 30/24/60
                                     GROUP BY inst_id) ash_total
                                  , gv$gg_apply_server a
                              WHERE a.sid = ash.SESSION_ID
                              AND   a.serial# = ash.SESSION_SERIAL#
                              AND   a.inst_id = ash.inst_id
                              AND   a.inst_id = ash_total.inst_id
                              ORDER BY a.inst_id, apply_name, to_number(Percentage)'''

                apply_receiver = '''select inst_id,apply_name, sid, serial# as serial
                                    , startup_time
                                    , total_messages_received
                                    , total_available_messages
                                    , state
                                    , last_received_msg_position
                                    , acknowledgement_position
                             from gv$gg_apply_receiver
                             order by inst_id, apply_name'''
                apply_receiver_ash = '''SELECT a.inst_id, a.apply_name
                                      , ash.event_count
                                      , ash_total.total_count
                                      , ash.event_count*100/NULLIF(ash_total.total_count,0) as Percentage
                                      , DECODE(ash.event, 'Streams AQ: enqueue blocked on low memory', 'NO'
                                      , 'Streams AQ: enqueue blocked due to flow control', 'NO'
                                      , 'REPL Capture/Apply: flow control', 'NO'
                                      , 'REPL Capture/Apply: memory','NO'
                                      , 'YES') busy
                                      , nvl(ash.event,'on CPU or wait on CPU') event
                                FROM (SELECT inst_id, SESSION_ID
                                            , SESSION_SERIAL#
                                            , EVENT
                                            , COUNT(sample_time) AS EVENT_COUNT
                                      FROM  gv$active_session_history
                                      WHERE sample_time >  sysdate - 2
                                      GROUP BY inst_id, session_id, session_serial#, event
                                     ) ash
                                     , (SELECT inst_id, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                                        FROM   gv$active_session_history
                                        WHERE  sample_time > sysdate - 2
                                        group by inst_id
                                       ) ash_total
                                     , gv$gg_apply_receiver a
                                WHERE a.sid                  = ash.SESSION_ID
                                and   a.serial#              = ash.SESSION_SERIAL#
                                and   a.source_database_name = 'replicat'
                                and   a.inst_id = ash.inst_id
                                and   a.inst_id = ash_total.inst_id
                                order by a.inst_id, a.apply_name, to_number(Percentage) '''
                apply_reader_ash = '''SELECT a.inst_id, a.apply_name
                                    , ash.event_count
                                    , ash_total.total_count
                                    , ash.event_count*100/NULLIF(ash_total.total_count,0) as Percentage
                                    , DECODE(ash.event,'rdbms ipc message', 'NO', 'YES') busy
                                    , NVL(ash.event,'on CPU or wait on CPU') event
                              FROM (SELECT inst_id
                                          , SESSION_ID
                                          , SESSION_SERIAL#
                                          , EVENT
                                          , COUNT(sample_time) AS EVENT_COUNT
                                    FROM  gv$active_session_history
                                    WHERE sample_time > sysdate - 1
                                    GROUP BY inst_id, session_id, session_serial#, event
                                   ) ash
                                  , (SELECT inst_id, COUNT(DISTINCT sample_time) AS TOTAL_COUNT
                                     FROM  gv$active_session_history
                                     WHERE sample_time > sysdate - 1
                                     GROUP BY inst_id
                                    ) ash_total
                                  , gv$gg_apply_reader a
                              WHERE a.sid    = ash.SESSION_ID
                              AND  a.serial# = ash.SESSION_SERIAL#
                              AND  a.inst_id = ash.inst_id
                              AND  a.inst_id = ash_total.inst_id
                              ORDER BY a.inst_id, apply_name, to_number(Percentage) '''
                apply_reader_info = '''SELECT APPLY_NAME
                                     , ((DEQUEUE_TIME-DEQUEUED_MESSAGE_CREATE_TIME)*86400) "LATENCY"
                                     , TO_CHAR(DEQUEUED_MESSAGE_CREATE_TIME,'HH24:MI:SS MM/DD') DEQUEUED_MESSAGE_CREATE_TIME
                                     , TO_CHAR(DEQUEUE_TIME,'HH24:MI:SS MM/DD') LAST_DEQUEUE
                                     , DEQUEUED_POSITION
                               FROM gV$GG_APPLY_READER
                               order by apply_name'''
                apply_reader_lcr_dep = '''select r.apply_name
                                          , r.total_messages_dequeued
                                          , r.total_lcrs_with_dep
                                          , r.total_lcrs_with_WMdep
                                          , c.total_assigned
                                          , c.total_wait_deps
                                          , c.total_wait_commits
                                          , 100*(r.total_lcrs_with_dep)/nullif((r.total_messages_dequeued-c.total_assigned),0) "WaitDep_perc_msgs"
                                          , 100*(r.total_lcrs_with_WMdep)/nullif((c.total_received),0) "WM_WaitDep_perc_msgs"
                                     from gv$gg_apply_reader r , gv$gg_apply_coordinator c
                                     where r.apply_name = c.apply_name
                                     and r.inst_id = c.inst_id
                                     order by r.apply_name'''

                apply_coordinator_info = '''select apply_name
                                          , total_applied
                                          , total_wait_deps
                                          , total_wait_commits
                                          , (100*total_wait_deps/NULLIF(total_applied,0))    as "WAITDEP"
                                          , (100*total_wait_commits/NULLIF(total_applied,0)) as "COMMITDEP"
                                    from gv$gg_apply_coordinator
                                    order by apply_name'''
                apply_server_agg_stats = '''SELECT a.inst_id
                                         , a.apply_name
                                         , a.server_id
                                         , substr(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME
                                         , a.sid, a.serial# serial
                                         , a.STATE
                                         , a.xidusn||'.'||a.xidslt||'.'||a.xidsqn CURRENT_TXN
                                         , a.TOTAL_ASSIGNED ASSIGNED
                                         , a.TOTAL_MESSAGES_APPLIED msg_APPLIED
                                         , a.MESSAGE_SEQUENCE
                                         , a.lcr_retry_iteration
                                         , a.txn_retry_iteration
                                         , a.total_lcrs_retried
                                         , a.total_txns_retried
                                         , a.total_txns_recorded 
                                         , a.elapsed_apply_time, a.apply_time
                                         , s.logon_time
                                    FROM gV$GG_APPLY_SERVER a, gV$SESSION s
                                    WHERE a.SID = s.SID 
                                    AND   a.SERIAL# = s.SERIAL#
                                    AND   a.inst_id = s.inst_id 
                                    order by a.apply_name, a.server_id'''
                apply_server_info = '''select a.inst_id
                                     , a.apply_name
                                     , a.server_id
                                     , a.state
                                     , a.total_messages_applied
                                     , q.sql_id
                                     , q.sql_fulltext sqltext
                                     , q.executions
                                     , q.rows_processed
                                     , q.rows_processed/decode(q.executions,0,1,executions) rows_per_exec
                                     , q.optimizer_mode,optimizer_cost
                               from gv$GG_apply_server a, gv$sql q, gv$session s
                               where a.sid = s.sid and a.serial#=s.serial#
                               and   a.inst_id = s.inst_id
                               and   s.sql_hash_value = q.hash_value
                               and   s.sql_address = q.address
                               and   s.sql_id = q.sql_id
                               and   s.inst_id = q.inst_id
                               and   a.inst_id = q.inst_id
                               order by a.apply_name, a.server_id'''
                apply_server_txn = '''select a.inst_id
                                   , a.APPLY_NAME
                                   , SUBSTR(s.PROGRAM,INSTR(S.PROGRAM,'(')+1,4) PROCESS_NAME
                                   , server_id
                                   , a.state
                                   , a.sid, a.serial# serial
                                   , a.TOTAL_ASSIGNED ASSIGNED
                                   , a.TOTAL_MESSAGES_APPLIED msg_APPLIED
                                   , xidusn||'.'||xidslt||'.'||xidsqn CURRENT_TXN
                                   , commit_position
                                   , dep_xidusn||'.'||dep_xidslt||'.'||dep_xidsqn DEPENDENT_TXN
                                   , dep_commit_position
                                   , message_sequence
                                   , apply_time
                              FROM gV$GG_APPLY_SERVER a, gV$SESSION s
                              WHERE a.SID = s.SID
                              AND a.SERIAL# = s.SERIAL#
                              AND a.inst_id = s.inst_id
                              order by a.apply_name,a.state'''
                apply_fts_info = '''select distinct sp1.object_owner||'.'||sp1.object_name table_name
                                   from gv$sqlarea  sa, gv$sql_plan sp1
                                   where sa.sql_id = sp1.sql_id 
                                   and sa.inst_id = sp1.inst_id
                                   and sp1.depth < 2
                                   and (sp1.object_owner,sp1.object_name,sp1.inst_id) in 
                                   (select destination_table_owner,destination_table_name,inst_id from gv$goldengate_table_stats )
                                   and sa.parsing_schema_name in (select username from DBA_GOLDENGATE_PRIVILEGES)
                                   and (sa.action LIKE 'OGG%' or sa.module like 'OGG%' or sa.module like 'GoldenGate%')
                                   and sa.command_type in (3,6,7)
                                   and 0 = (select count(*) from gv$sql_plan sp2
                                   where sp2.object_owner in ('SYS','SYSTEM') and sp2.sql_id =sa.sql_id and sp2.inst_id = sa.inst_id)
                                   and 0 = (select count(*) from gv$sql_plan sp2
                                   where sp2.options in ('UNIQUE SCAN')       
                                   and sp2.sql_id =sa.sql_id and sp2.inst_id = sa.inst_id )'''
                apply_flow = '''SELECT TO_CHAR(sysdate,'YYYY-MM-DD HH24:MI:SS') mtime
                              , rcv.inst_id
                              , rcv.APPLY_NAME
                              , rcv.STATE receiver_state
                              , r.STATE reader_state
                              , ROUND(r.SGA_USED/1024/1024,2) SGA_USED
                              , ROUND(r.SGA_ALLOCATED/1024/1024,2) SGA_ALLOCATED
                              , rcv.TOTAL_available_messages
                              , rcv.TOTAL_MESSAGES_RECEIVED
                              , r.TOTAL_MESSAGES_DEQUEUED
                              , c.UNASSIGNED_COMPLETE_TXNS
                              , (select count(*)
                                 from gv$goldengate_transaction t
                                 where t.component_name = c.apply_name
                                 and t.inst_id = c.inst_id) open_txn
                                 , c.active_server_count
                                 , (select count(1) from gv$gg_apply_server s
                                    where s.state='EXECUTE TRANSACTION'
                                    and s.apply_name = c.apply_name
                                    and s.inst_id    = c.inst_id) active_executing_count
                              from gv$gg_apply_reader r,  gv$gg_apply_receiver rcv, gv$gg_apply_coordinator c
                              where c.apply_name=rcv.apply_name
                              and   c.apply_name=r.apply_name
                              and   c.inst_id=rcv.inst_id
                              and   c.inst_id=r.inst_id
                              order by r.SGA_USED desc'''
                apply_server_waits = '''select a.inst_id
                                     , a.apply_name
                                     , a.server_id
                                     , w.event
                                     , w.seconds_in_wait secs
                                from gv$GG_apply_server a, gv$session_wait w 
                                where a.sid = w.sid  
                                and a.inst_id = w.inst_id
                                order by a.apply_name, a.server_id'''

                rep_params_fetch = pd.read_sql_query(rep_params, con)
                rep_params_fetch = rep_params_fetch.to_dict('records')
                rep_inbound_fetch = pd.read_sql_query(rep_inbound, con)
                rep_inbound_fetch = rep_inbound_fetch.astype(str)
                rep_inbound_fetch = rep_inbound_fetch.to_dict('records')
                rep_summary_fetch = pd.read_sql_query(rep_summary, con)
                rep_summary_fetch = rep_summary_fetch.astype(str)
                rep_summary_fetch = rep_summary_fetch.to_dict('records')
                rep_open_trans = '''select component_name, count(*) "Open Transactions",sum(cumulative_message_count) "Total LCRs" 
                            from gv$Goldengate_transaction
                            where component_type='APPLY' group by component_name order by 3'''
                rep_open_trans_10000 = '''select component_name, count(*) "Open Transactions",sum(cumulative_message_count) "Total LCRs" 
                                  from gv$Goldengate_transaction 
                                  where component_type='APPLY'  and cumulative_message_count > 10000 group by component_name order by 1'''
                rep_open_trans_fetch = pd.read_sql_query(rep_open_trans, con)
                rep_open_trans_fetch = rep_open_trans_fetch.to_dict('records')
                rep_open_trans_10000_fetch = pd.read_sql_query(rep_open_trans_10000, con)
                rep_open_trans_10000_fetch = rep_open_trans_10000_fetch.to_dict('records')
                apply_receiver_fetch = pd.read_sql_query(apply_receiver, con)
                apply_receiver_fetch = apply_receiver_fetch.astype(str)
                apply_receiver_fetch = apply_receiver_fetch.to_dict('records')
                apply_receiver_ash_fetch = pd.read_sql_query(apply_receiver_ash, con)
                apply_receiver_ash_fetch = apply_receiver_ash_fetch.to_dict('records')
                apply_reader_fetch = pd.read_sql_query(apply_reader, con)
                apply_reader_fetch = apply_reader_fetch.astype(str)
                apply_reader_fetch = apply_reader_fetch.to_dict('records')
                apply_reader_info_fetch = pd.read_sql_query(apply_reader_info, con)
                apply_reader_info_fetch = apply_reader_info_fetch.to_dict('records')
                apply_reader_ash_fetch = pd.read_sql_query(apply_reader_ash, con)
                apply_reader_ash_fetch = apply_reader_ash_fetch.to_dict('records')
                apply_coordinator_info_fetch = pd.read_sql_query(apply_coordinator_info, con)
                apply_coordinator_info_fetch = apply_coordinator_info_fetch.to_dict('records')
                apply_coordinator_fetch = pd.read_sql_query(apply_coordinator, con)
                apply_coordinator_fetch = apply_coordinator_fetch.astype(str)
                apply_coordinator_fetch = apply_coordinator_fetch.to_dict('records')
                apply_server_info_fetch = pd.read_sql_query(apply_server_info, con)
                apply_server_info_fetch = apply_server_info_fetch.to_dict('records')
                apply_server_txn_fetch = pd.read_sql_query(apply_server_txn, con)
                apply_server_txn_fetch = apply_server_txn_fetch.to_dict('records')
                apply_server_ash_fetch = pd.read_sql_query(apply_server_ash, con)
                apply_server_ash_fetch = apply_server_ash_fetch.to_dict('records')
                apply_fts_info_fetch = pd.read_sql_query(apply_fts_info, con)
                apply_fts_info_fetch = apply_fts_info_fetch.to_dict('records')
                apply_flow_fetch = pd.read_sql_query(apply_flow, con)
                apply_flow_fetch = apply_flow_fetch.to_dict('records')
                apply_server_agg_fetch = pd.read_sql_query(apply_server_agg_stats, con)
                apply_server_agg_fetch = apply_server_agg_fetch.astype(str)
                apply_server_agg_fetch = apply_server_agg_fetch.to_dict('records')
                apply_server_waits_fetch = pd.read_sql_query(apply_server_waits, con)
                apply_server_waits_fetch = apply_server_waits_fetch.to_dict('records')
                apply_reader_lcr_dep_fetch = pd.read_sql_query(apply_reader_lcr_dep, con)
                apply_reader_lcr_dep_fetch = apply_reader_lcr_dep_fetch.to_dict('records')
            except cx_Oracle.DatabaseError as e:
                rep_summary_fetch = str(e)
            finally:
                if con:
                    con.close()
        return [rep_summary_fetch, rep_params_fetch, rep_open_trans_fetch, rep_open_trans_10000_fetch, db_det,
                rep_inbound_fetch, apply_receiver_fetch, apply_receiver_ash_fetch, apply_reader_fetch,
                apply_reader_ash_fetch, apply_reader_info_fetch, apply_coordinator_info_fetch, apply_coordinator_fetch,
                apply_server_info_fetch, apply_server_txn_fetch, apply_fts_info_fetch, apply_server_ash_fetch,
                apply_flow_fetch, apply_server_agg_fetch, apply_server_waits_fetch, apply_reader_lcr_dep_fetch]


class onepConn(Resource):
    def post(self):
        data = request.get_json(force=True)
        dep_type = data['dep_type']
        onepOps = data['onepOps']
        try:
            ErrPrint = []
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            oneplace_dep = config.get('ONEPLACE_CONFIG', 'ONEPLACE_DEPLOYMENT')
            if dep_type == 'ld':
                dep_url = 'http://' + oneplace_host + ':' + oneplace_port
                if onepOps == 'add':
                    user = data['user']
                    passwd = data['passwd']
                    passwd = cipher.encrypt(passwd).decode('utf-8')
                    role = data['role']
                    dep_url = data['dep_url']
                    cursor.execute('''insert into ONEPCONN values(:dep,:user,:passwd,:role,:dep_type,
                          :dep_url)''', {"dep": oneplace_dep, "user": user, "passwd": passwd, "role": role,
                                         "dep_type": dep_type, "dep_url": dep_url})
                elif onepOps == 'edit':
                    user = data['user']
                    passwd = data['passwd']
                    passwd = cipher.encrypt(passwd).decode('utf-8')
                    cursor.execute('''update ONEPCONN set passwd=:passwd where user=:user''',
                                   {"user": user, "passwd": passwd})
                elif onepOps == 'del':
                    user = data['user']
                    cursor.execute('''delete from  ONEPCONN  where user=:user''', {"user": user})
                conn.commit()
                ErrPrint.append('OneP User ' + user + ' Added')
            elif dep_type == 'rd':
                dep_url = data['dep_url']
                user = data['user']
                passwd = data['passwd']
                passwd = cipher.encrypt(passwd).decode('utf-8')
                dep_url = dep_url + '/oneplogin'
                payload = {"user": user, "passwd": passwd, "onepsuid": 'oneplaceusid1980'}
                headers = {"Content-Type": "application/json"}
                try:
                    r = requests.post(dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
                    SignIn = r.json()[1]
                    oneplace_role = r.json()[2]
                    oneplace_dep = r.json()[4]
                    dep_url = r.json()[3]
                    dbtype = r.json()[5]
                    if SignIn == 'Y' and oneplace_role == 'admin':
                        cursor.execute('''insert into ONEPCONN values(:dep,:user,:passwd,:role,:dep_type,
                                    :dep_url,:dbtype)''',
                                       {"dep": oneplace_dep, "user": user, "passwd": passwd, "role": oneplace_role,
                                        "dep_type": dep_type, "dep_url": dep_url, "dbtype": dbtype})
                        conn.commit()
                        ErrPrint.append('OneP User ' + user + ' Added')
                    else:
                        ErrPrint.append('Invalid Deployment Credentials')
                except requests.exceptions.ConnectionError:
                    ErrPrint.append('Invalid Deployment')
        except sqlite3.DatabaseError as e:
            ErrPrint.append("There is a problem with OneP Database " + str(e))
        finally:
            if conn:
                conn.close()
        return [ErrPrint]


class onepDep(Resource):
    def get(self):
        ErrPrint = []
        try:
            conn = sqlite3.connect('conn.db')
            dep_det = """SELECT distinct dep,dep_url FROM ONEPCONN where role='admin'"""
            dep_det_fetch = pd.read_sql_query(dep_det, conn)
        except sqlite3.DatabaseError as e:
            logger.info("There is a problem with Light Database " + str(e))
        finally:
            if conn:
                conn.close()
        return [dep_det_fetch.to_dict('records')]


class onepDepUrl(Resource):
    def post(self):
        data = request.get_json(force=True)
        dep = data['dep']
        ErrPrint = []
        DepUrl = ''
        DepType = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute("""SELECT distinct dep_url,dbtype FROM ONEPCONN WHERE dep=:dep""", {"dep": dep})
            user_row = cursor.fetchone()
            if user_row:
                DepUrl = user_row[0]
                DepType = user_row[1]
        except sqlite3.DatabaseError as e:
            logger.info(str(e))
        finally:
            if conn:
                conn.close()
        return [DepUrl, trailPath, DepType]


class ggRmtHostMgr(Resource):
    def get(self):
        data = request.get_json(force=True)
        user = data['user']
        passwd = data['passwd']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute("""SELECT user,passwd,role FROM ONEPCONN WHERE user=:user and passwd=:passwd
                               and role='admin' and dep_type='ld'""", {"user": user, "passwd": passwd})
        user_row = cursor.fetchone()
        if user_row:
            val = infoall()
            for i in val[0]:
                if 'mgrport' in i.keys():
                    rmtPort = i['mgrport']
        else:
            rmtPort = 'Invalid Credentials'
            rmtHost = 'Invalid Credentials'
        return [rmtPort, oneplace_host]


class onepLogin(Resource):
    def post(self):
        data = request.get_json(force=True)
        user = data['user']
        userpasswd = data['passwd']
        onepsuid = data["onepsuid"]
        ErrPrint = []
        SignIn = 'N'
        OnepDepName = ''
        OnepRole = ''
        OnepDepUrl = ''
        OnepType = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute(
                """SELECT dep,user,passwd,role,dep_url,dbtype FROM ONEPCONN WHERE user = :user and dep_type='ld'""",
                {"user": user})
            user_row = cursor.fetchone()
            if user_row:
                seluser = user_row[1]
                selpasswd = user_row[2]
                selpasswd = cipher.decrypt(selpasswd)
                if onepsuid == 'oneplaceusid1980':
                    userpasswd = cipher.decrypt(userpasswd)
                if seluser == user and selpasswd == userpasswd:
                    SignIn = 'Y'
                    OnepDepName = user_row[0]
                    OnepDepUrl = user_row[4]
                    OnepRole = user_row[3]
                    OnepType = user_row[5]
                else:
                    SignIn = 'N'
                    ErrPrint.append('Invalid Login Credentials')
            else:
                SignIn = 'N'
                ErrPrint.append('Invalid Login Credentials')
        except sqlite3.DatabaseError as e:
            SignIn = 'N'
            ErrPrint.append(str(e))
        finally:
            if conn:
                conn.close()

        return [ErrPrint, SignIn, OnepRole, OnepDepUrl, OnepDepName, OnepType]


class awsPricing(Resource):
    def post(self):
        data = request.get_json(force=True)
        region = data['region']
        os = data['os']
        sw = data['sw']
        region = region.split('$')
        resolved_region = region[1]
        region = region[0]
        req_memory = data['req_memory']
        req_vcpu = data['req_vcpu']
        pricing_auth = boto3.client('pricing', region_name='us-east-1')
        response = pricing_auth.get_products(ServiceCode='AmazonEC2', Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': resolved_region},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': sw},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os}])
        PriceListDict = {}
        PriceListMerge = {}
        for result in response['PriceList']:
            json_result = json.loads(result)
            for key, value in json_result.items():
                if key == 'product' and value['attributes']['memory'] != 'NA':
                    if int(value['attributes']['vcpu']) >= int(req_vcpu) and float(
                            value['attributes']['memory'].split()[0]) >= float(req_memory):
                        PriceListDict.setdefault(value['sku'], []).append(
                            {'InstanceType': value['attributes']['instanceType'],
                             'memory': value['attributes']['memory'], 'vcpu': value['attributes']['vcpu'],
                             'nwb': value['attributes']['networkPerformance'],
                             'os': value['attributes']['operatingSystem'], 'sw': value['attributes']['preInstalledSw'],
                             'arch': value['attributes']['processorArchitecture'],
                             'mo': value['attributes']['marketoption']})
                elif key == 'terms':
                    for key, value in value.items():
                        if key == 'OnDemand':
                            for res1 in value.values():
                                for res2 in res1['priceDimensions'].values():
                                    for key1, value1 in PriceListDict.items():
                                        if key1 == res1['sku']:
                                            PriceListMerge[value1[0]['InstanceType']] = {'memory': value1[0]['memory'],
                                                                                         'vcpu': value1[0]['vcpu'],
                                                                                         'nwb': value1[0]['nwb'],
                                                                                         'os': value1[0]['os'],
                                                                                         'sw': value1[0]['sw'],
                                                                                         'arch': value1[0]['arch'],
                                                                                         'OnDemandPrice': round(float(
                                                                                             res2['pricePerUnit'][
                                                                                                 'USD']), 4)}
                        else:
                            for res1 in value.values():
                                for res2 in res1['priceDimensions'].values():
                                    for key1, value1 in PriceListDict.items():
                                        if key1 == res1['sku']:
                                            PriceListMerge[value1[0]['InstanceType']].update({key +
                                                                                              res1['termAttributes'][
                                                                                                  'OfferingClass'] +
                                                                                              res1['termAttributes'][
                                                                                                  'PurchaseOption'].replace(
                                                                                                  " ", "") +
                                                                                              res1['termAttributes'][
                                                                                                  'LeaseContractLength'] +
                                                                                              res2['unit']: round(
                                                float(res2['pricePerUnit']['USD']), 4)})
        return [PriceListMerge]


class selectDBConn(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbName = data['dbName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": dbName})
        db_row = cursor.fetchone()
        cursor.close()
        conn.close()
        con = ''
        db_main_ver = ''
        db_minor_ver = ''
        user = ''
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            servicename = db_row[2]
        return [user, passwd, servicename]


def selectConn(dbname):
    conn = sqlite3.connect('conn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": dbname})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
    con = ''
    db_main_ver = ''
    db_minor_ver = ''
    user = ''
    if db_row:
        user = db_row[0]
        passwd = db_row[1]
        passwd = cipher.decrypt(passwd)
        servicename = db_row[2]
        # servicename = servicename.split('/')
        # hostname = servicename[0]
        # dbName = servicename[1]
        connection_string = (f'DSN={servicename};')
        try:
            con = pyodbc.connect(connection_string)
            db_det = '''SELECT @@version AS version'''
            db_det_fetch = pd.read_sql_query(db_det, con)
            db_det = db_det_fetch.to_dict('records')
            db_main_ver = db_det[0]['version']
        except cx_Oracle.DatabaseError as e:
            db_main_ver = str(e)
            logger.info(str(e))
    return [con, db_main_ver]


def selectConnPool(dbname, parallel):
    conn = sqlite3.connect('conn.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {"dbname": dbname})
    db_row = cursor.fetchone()
    cursor.close()
    conn.close()
    con = ''
    db_main_ver = ''
    db_minor_ver = ''
    user = ''
    if db_row:
        user = db_row[0]
        passwd = db_row[1]
        passwd = cipher.decrypt(passwd)
        servicename = db_row[2]
        try:
            pool = cx_Oracle.SessionPool(user, passwd, servicename, min=parallel, max=parallel, increment=0,
                                         threaded=True, getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT)
        except cx_Oracle.DatabaseError as e:
            logger.info(str(e))
    return [pool]


def large_csv_upload_to_s3(jobName, dbName, rsAlias, cdbCheck, pdbName, bucketName, chunk_id, aws_access_key_id,
                           aws_secret_access_key, table_owner, table_name, start_rowid, end_rowid, tgt_dep_url,
                           startTime, parallel):
    try:
        con = selectConn(dbName)[0]
        cursor = con.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursor.execute('''alter session set container=''' + pdbName)
            statFileName = os.path.join(oneplace_home, jobName,
                                        pdbName + '.' + table_owner + '.' + table_name + '=+!' + str(
                                            chunk_id) + '_stats')
        else:
            statFileName = os.path.join(oneplace_home, jobName,
                                        table_owner + '.' + table_name + '=+!' + str(chunk_id) + '_stats')
        chunk_proc = '''select * from ''' + table_owner + '.' + table_name + ''' where rowid between :start_rowid  and :end_rowid'''
        param = {"start_rowid": start_rowid, "end_rowid": end_rowid}
        df = pd.read_sql_query(chunk_proc, con, params=[param["start_rowid"], param["end_rowid"]])
        loadSize = str(len(df.index))
        if df.empty == False:
            csv_buffer = BytesIO()
            with gzip.GzipFile(mode='w', fileobj=csv_buffer) as zipped_file:
                df.to_csv(TextIOWrapper(zipped_file, 'utf8'), index=False, header=False)
            fileName = table_owner + '.' + table_name + str(chunk_id) + '.csv'
            s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            s3_object = s3.Object(bucketName, fileName).put(Body=csv_buffer.getvalue())
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
            dep_url = tgt_dep_url + '/addlargecsvilproc'
            payload = {"jobName": jobName, "cdbCheck": cdbCheck, "pdbName": pdbName, "chunk_id": chunk_id,
                       "table_owner": table_owner, "table_name": table_name, "rsAlias": rsAlias, "fileName": fileName,
                       "currentAWSBucket": bucketName, "aws_access_key_id": aws_access_key_id,
                       "aws_secret_access_key": aws_secret_access_key, "loadSize": loadSize, "startTime": startTime}
            headers = {"Content-Type": "application/json"}
            r = requests.post(dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        else:
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
    except Exception as e:
        pass
    finally:
        if con:
            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
            elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
            elapTime = elapTime.total_seconds()
            with open(statFileName, 'w') as infile:
                infile.write(loadSize + '-' + str(elapTime))
            cursor.callproc('DBMS_PARALLEL_EXECUTE.set_chunk_status', [jobName, chunk_id, 2]);
            cursor.close()
            con.close()


def small_csv_upload_to_s3(jobName, dbName, rsAlias, cdbCheck, pdbName, bucketName, aws_access_key_id,
                           aws_secret_access_key, table_name, tgt_dep_url):
    try:
        con = selectConn(dbName)[0]
        cursor = con.cursor()
        if cdbCheck == 'YES' and len(pdbName) > 0:
            cursor.execute('''alter session set container=''' + pdbName)
            statFileName = os.path.join(oneplace_home, jobName, pdbName + '.' + table_name + '=+!' + '_stats')
        else:
            statFileName = os.path.join(oneplace_home, jobName, table_name + '=+!' + '_stats')
        chunk_proc = '''select * from {}'''.format(table_name)
        startTime = datetime.now(timezone.utc)
        startTime = startTime.strftime('%Y-%m-%d:%H:%M:%S')
        df = pd.read_sql_query(chunk_proc, con)
        loadSize = str(len(df.index))
        if df.empty == False:
            csv_buffer = BytesIO()
            with gzip.GzipFile(mode='w', fileobj=csv_buffer) as zipped_file:
                df.to_csv(TextIOWrapper(zipped_file, 'utf8'), index=False, header=False)
            fileName = table_name + '.csv'
            s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            s3_object = s3.Object(bucketName, fileName).put(Body=csv_buffer.getvalue())
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
            dep_url = tgt_dep_url + '/addsmallcsvilproc'
            payload = {"jobName": jobName, "cdbCheck": cdbCheck, "pdbName": pdbName, "table_name": table_name,
                       "rsAlias": rsAlias, "fileName": fileName, "currentAWSBucket": bucketName,
                       "aws_access_key_id": aws_access_key_id, "aws_secret_access_key": aws_secret_access_key,
                       "loadSize": loadSize, "startTime": startTime}
            headers = {"Content-Type": "application/json"}
            r = requests.post(dep_url, json=payload, headers=headers, verify=False, timeout=sshTimeOut)
        else:
            endTime = datetime.now(timezone.utc)
            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
    except Exception as e:
        pass
    finally:
        if con:
            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
            elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
            elapTime = elapTime.total_seconds()
            with open(statFileName, 'w') as infile:
                infile.write(loadSize + '-' + str(elapTime))
            cursor.close()
            con.close()


def table_itter_rows(dbName, jobName):
    extract = os.path.join(oneplace_base, 'extract')
    print(extract)
    ssh = subprocess.Popen([extract, dbName, jobName], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
    ILProcStatRate, stderr = ssh.communicate(timeout=sshTimeOut)
    print(ILProcStatRate, stderr)


def infoall():
    processTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with  open(os.path.join(oneplace_home, 'infoall'), mode='r') as infile:
        GG_Data = []
        GG_Version = ''
        copy = False
        for line in infile:
            if 'Version' in line:
                ver = line.split()
                ggVer = ver[ver.index('Version') + 1]
                ggVer = ggVer.split('.')
                ggMainVer = ggVer[0]
            if re.match('EXTRACT', line, re.IGNORECASE):
                copy = True
            elif re.match('REPLICAT', line, re.IGNORECASE):
                copy = False
                break
            if copy:
                if re.match('EXTRACT', line, re.IGNORECASE):
                    line = line.split()
                    ExtName = line[1]
                    ExtStat = line[-1]
                elif 'Lag' in line:
                    line = line.split()
                    extlagH, extlagM, extlagS = line[2].split(':')
                    ExtLag = int(extlagH) * 3600 + int(extlagM) * 60 + int(extlagS)
                    extchkH, extchkM, extchkS = line[4].split(':')
                    ExtChkLag = int(extchkH) * 3600 + int(extchkM) * 60 + int(extchkS)
                elif 'Redo' in line:
                    GG_Data.append({'extname': ExtName, 'extstat': ExtStat, 'extlag': ExtLag, 'extchklag': ExtChkLag,
                                    'extIncTime': processTime})
                elif 'File' in line:
                    GG_Data.append({'pmpname': ExtName, 'pmpstat': ExtStat, 'pmplag': ExtLag, 'pmpchklag': ExtChkLag,
                                    'pmpIncTime': processTime})
    with  open(os.path.join(oneplace_home, 'infoall'), mode='r') as infile:
        copy = False
        for line in infile:
            if re.match('REPLICAT', line, re.IGNORECASE):
                copy = True
            elif 'Manager' in line:
                copy = False
                break
            if copy:
                if re.match('REPLICAT', line, re.IGNORECASE):
                    line = line.split()
                    RepName = line[1]
                    RepStat = line[-1]
                elif 'Lag' in line:
                    line = line.split()
                    replagH, replagM, replagS = line[2].split(':')
                    RepLag = int(replagH) * 3600 + int(replagM) * 60 + int(replagS)
                    repchkH, repchkM, repchkS = line[4].split(':')
                    RepChkLag = int(repchkH) * 3600 + int(replagM) * 60 + int(repchkS)
                elif 'File' in line:
                    GG_Data.append({'repname': RepName, 'repstat': RepStat, 'replag': RepLag, 'repchklag': RepChkLag,
                                    'repIncTime': processTime})
    with  open(os.path.join(oneplace_home, 'infoall'), mode='r') as infile:
        for line in infile:
            if 'Manager' in line:
                mgr = line.split()
                if not re.match('DOWN!', mgr[2], re.IGNORECASE):
                    tcpstr = mgr[mgr.index('port') + 1]
                    if ggMainVer == '12':
                        rmt = tcpstr.split('.')[1].rstrip(',')
                    else:
                        rmt = tcpstr.split(':')[1].rstrip(',')
                    rmtport = rmt.split('.')[-1]
                    rmthost = rmt.rstrip(rmtport + '.')
                else:
                    rmthost = socket.gethostname()
                    try:
                        with open(os.path.join(gg_home, 'dirprm', 'mgr.prm')) as infile:
                            for line in infile:
                                if 'port' in line or 'PORT' in line:
                                    rmtport = line.split()[1]
                    except FileNotFoundError as e:
                        rmtport = 'Not configured'
                GG_Data.append({'mgrstat': mgr[2], 'mgrhost': rmthost, 'mgrport': rmtport})
    return [GG_Data]


def extract_file(zf, info, extract_dir):
    zf.extract(info.filename, path=extract_dir)
    out_path = os.path.join(extract_dir, info.filename)
    perm = info.external_attr >> 16
    os.chmod(out_path, perm)


def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n


cipher = AESCipher('OnePlaceMyPlaceJamboUrl111019808')

api.add_resource(dbDet, '/dbdet')
api.add_resource(dbConn, '/dbconn')
api.add_resource(ggDepDet, '/depdet')
api.add_resource(MemUsage, '/memusage')
api.add_resource(ggTranNext, '/ggtrannext')
api.add_resource(ggTranPrev, '/ggtranprev')
api.add_resource(ggInfoall, '/gginfoall')
api.add_resource(ggMonitorall, '/ggmonitorall')
api.add_resource(ggInfoExt, '/gginfoext')
api.add_resource(ggInfoRep, '/gginforep')
api.add_resource(ggLogDump, '/gglogdump')
api.add_resource(ggCredStore, '/ggcredstore')
api.add_resource(ggAddCredStore, '/ggaddcredstore')
api.add_resource(ggAddUserAlias, '/ggaddusralias')
api.add_resource(ggEditUserAlias, '/ggeditusralias')
api.add_resource(ggDelUserAlias, '/ggdelusralias')
api.add_resource(ggTestDBLogin, '/testdblogin')
api.add_resource(ggErrLog, '/ggerrlog')
api.add_resource(ggAddIE, '/ggaddie')
api.add_resource(ggAddCE, '/ggaddce')
api.add_resource(ggDelExt, '/delext')
api.add_resource(suppLog, '/supplog')
api.add_resource(suppLogSchema, '/supplogschema')
api.add_resource(ggAddSupp, '/addsupplog')
api.add_resource(listPrm_files, '/listprm')
api.add_resource(listRptFiles, '/listrpt')
api.add_resource(listDscFiles, '/listdsc')
api.add_resource(viewPrm_files, '/viewprm')
api.add_resource(viewRptFiles, '/viewrpt')
api.add_resource(viewDscFiles, '/viewdsc')
api.add_resource(savePrm_files, '/saveprm')
api.add_resource(get_Version, '/ggversion')
api.add_resource(ggAddReplicat, '/ggaddreplicat')
api.add_resource(writeTmpPrm, '/writetmpprm')
api.add_resource(ggViewMgrRpt, '/viewmgrrpt')
api.add_resource(ggRepOps, '/ggrepops')
api.add_resource(ggExtOps, '/ggextops')
api.add_resource(ggMgrOps, '/ggmgrops')
api.add_resource(ggInfoDiagram, '/gginfodiag')
api.add_resource(ggAddChkptTbl, '/ggaddchkpttbl')
api.add_resource(rhpUploadImage, '/rhpuploadimg')
api.add_resource(listSoftFiles, '/listsoftfiles')
api.add_resource(ViewRunInsFile, '/viewrunins')
api.add_resource(ggCreateGoldImg, '/creategoldimg')
api.add_resource(ggGetAllTrails, '/gggettrails')
api.add_resource(getTableName, '/gettablename')
api.add_resource(getViewName, '/getviewname')
api.add_resource(getProcName, '/getprocname')
api.add_resource(IETshoot, '/ietshoot')
api.add_resource(IRTshoot, '/irtshoot')
api.add_resource(lmDictDet, '/lmdictdet')
api.add_resource(ggExtShowTrans, '/ggextshowtrans')
api.add_resource(ggExtSkipTrans, '/ggextskiptrans')
api.add_resource(onepConn, '/onepconn')
api.add_resource(onepLogin, '/oneplogin')
api.add_resource(ggInfoChkptTbl, '/infochkpttbl')
api.add_resource(ggGetExtTrail, '/gggetexttrail')
api.add_resource(ggGetExtParam, '/gggetextprm')
api.add_resource(ggAddPumpPT, '/ggaddpumppt')
api.add_resource(ggDelRMT, '/ggdelrmt')
api.add_resource(PRTshoot, '/prtshoot')
api.add_resource(CRTshoot, '/crtshoot')
api.add_resource(RepType, '/reptype')
api.add_resource(writeMgrPrm, '/writemgrprm')
api.add_resource(readMgrPrm, '/readmgrprm')
api.add_resource(ggAddHeartBeat, '/ggaddhbtbl')
api.add_resource(getExtTrailName, '/getexttrailname')
api.add_resource(addExtTrail, '/addexttrail')
api.add_resource(MemUsagebyProcess, '/memusagebyprocess')
api.add_resource(ggLogDumpCount, '/gglogdumpcount')
api.add_resource(tableList, '/tablelist')
api.add_resource(rhpAddRep, '/rhpaddrep')
api.add_resource(AddInitialLoadExt, '/addinitialloadext')
api.add_resource(AddInitialLoadRep, '/addinitialloadrep')
api.add_resource(onepDep, '/onepdep')
api.add_resource(ggCredStoreCheck, '/credstorecheck')
api.add_resource(ggRmtHostMgr, '/ggrmthostmgr')
api.add_resource(ggMasterKey, '/ggmasterkey')
api.add_resource(ggMasterKeyAction, '/ggmasterkeyaction')
api.add_resource(rhpWallet, '/rhpwallet')
api.add_resource(onepDepUrl, '/onepdepurl')
api.add_resource(AddILEXT, '/addilext')
api.add_resource(AddILREP, '/addilrep')
api.add_resource(ggILProcesses, '/ggilprocesses')
api.add_resource(cdbCheck, '/cdbcheck')
api.add_resource(DelILREP, '/delilrep')
api.add_resource(DelILEXT, '/delilext')
api.add_resource(ApplyMetadata, '/applymetadata')
api.add_resource(MetaDatafile, '/metadatafile')
api.add_resource(ReqArchLog, '/reqarchlog')
api.add_resource(ggILDataSet, '/ggildataset')
api.add_resource(AddAutoILProc, '/addautoilproc')
api.add_resource(ggExtProcStats, '/ggextprocstats')
api.add_resource(ggRepProcStats, '/ggrepprocstats')
api.add_resource(ggILTables, '/ggiltables')
api.add_resource(ggILAction, '/ggilaction')
api.add_resource(ggILJobAct, '/ggiljobact')
api.add_resource(downloadSoft, '/downloadsoft')
api.add_resource(expDirs, '/expdirs')
api.add_resource(expDP, '/expdp')
api.add_resource(expdpMon, '/expdpmon')
api.add_resource(expimpJob, '/expimpjob')
api.add_resource(xfrDumpFiles, '/xfrdumpfiles')
api.add_resource(downLoadfromS3, '/downloadfroms3')
api.add_resource(impDP, '/impdp')
api.add_resource(readExportLog, '/readexportlog')
api.add_resource(readImportLog, '/readimportlog')
api.add_resource(downloadS3Log, '/downloads3log')
api.add_resource(xidDet, '/xiddet')
api.add_resource(TshootImpDP, '/tshootimpdp')
api.add_resource(tableSpaceImpDP, '/tablespaceimpdp')
api.add_resource(S3TransferLog, '/s3transferlog')
api.add_resource(updateS3Config, '/updates3config')
api.add_resource(selectDBDet, '/selectdbdet')
api.add_resource(ggGetRMTTrail, '/gggetrmttrail')
api.add_resource(ggProcessAction, '/ggprocessaction')
api.add_resource(AddCSVILProc, '/addcsvilproc')
api.add_resource(CSVILProcMon, '/csvilprocmon')
api.add_resource(awsPricing, '/awspricing')
api.add_resource(selectDBConn, '/selectconn')
api.add_resource(insertExpImp, '/insertexpimp')
api.add_resource(readLog, '/readlog')
api.add_resource(writeLog, '/writelog')
api.add_resource(checkLog, '/checklog')
api.add_resource(updateExpImp, '/updateexpimp')
api.add_resource(expMon, '/expmon')
api.add_resource(xfrMon, '/xfrmon')
api.add_resource(impMon, '/impmon')
api.add_resource(exportCheckLog, '/exportchecklog')
api.add_resource(importCheckLog, '/importchecklog')
api.add_resource(savePrm_files_Temp, '/saveprmtmp')
api.add_resource(writeMetaDataFile, '/writemetadatafile')
api.add_resource(insertSQLite3DB, '/insertsqlite3db')
api.add_resource(getTableDetFromSchema, '/gettabledetfromschema')
api.add_resource(getViewNameFromSchema, '/getviewnamefromschema')
api.add_resource(getProcNameFromSchema, '/getprocnamefromschema')
api.add_resource(getViewText, '/getviewtext')
api.add_resource(getProcText, '/getproctext')
api.add_resource(getTriggerName, '/gettriggername')
api.add_resource(getTrigNameFromSchema, '/gettrignamefromschema')
api.add_resource(getTrigText, '/gettrigtext')
api.add_resource(ViewExtractLog, '/viewextractlog')
api.add_resource(automateProcess, '/automateProcess')
api.add_resource(fetchAutomateExcel, '/fetchAutomateExcel')
api.add_resource(fetchAutomateViewExcel, '/fetchAutomateViewExcel')
api.add_resource(fetchAutomateTriggerExcel, '/fetchAutomateTriggerExcel')
api.add_resource(automateView, '/automateView')
api.add_resource(updateExcel, '/updateExcel')
api.add_resource(updateExcelView, '/updateExcelView')
api.add_resource(updateExcelTrigger, '/updateExcelTrigger')
api.add_resource(getZoneDetails, '/getZoneDetails')
api.add_resource(updateZoneDetails, '/updateZoneDetails')
api.add_resource(automateTrigger, '/automateTrigger')
