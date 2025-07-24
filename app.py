import requests
import socket
import json
import subprocess
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import zipfile
import tarfile
from werkzeug.utils import secure_filename
import re
import logging
import binascii
import os
import pandas as pd
import numpy as np
import shutil
import time
import random
from file_read_backwards import FileReadBackwards
from datetime import datetime
import configparser
from flask_cors import CORS
import logging
import platform
import hashlib
import psutil
import glob
import sqlite3
import threading
import base64
import sys
import grp
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import botocore
import warnings
import pyodbc
import torch
import torch.nn.functional as F
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_aws import ChatBedrock
from langchain_core.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from transformers import AutoTokenizer, AutoModel
from langchain_huggingface import HuggingFaceEmbeddings
from RAG import saveClaudeFromat
from RAG.queryFetch import run_sybase_to_oracle_conversion
from RAG.s3_list import getS3BucketList, upload_file_to_s3
import cx_Oracle

app = Flask(__name__, static_folder='./web', static_url_path='/')
CORS(app)
api = Api(app)
OSPlatBit = platform.processor()
OSPlat = platform.system()
sshTimeOut = 120
config = configparser.RawConfigParser()
config.read('config/skyliftai.cfg')
agent_base = config.get('AGENT_CONFIG', 'BASE_DIR')
agent_home = config.get('AGENT_CONFIG', 'HOME_DIR')
gg_home = config.get('AGENT_CONFIG', 'GG_HOME')
agent_host = config.get('AGENT_CONFIG', 'AGENT_HOST')
web_port = config.get('AGENT_CONFIG', 'SERVER_PORT')
trailPath = config.get('AGENT_CONFIG', 'GG_TRAIL')
agent_debug = config.get('AGENT_CONFIG', 'AGENT_DEBUG')
table_split_chunk_size = config.get('AGENT_CONFIG', 'TABLE_SPLIT_CHUNK_SIZE')
ssl_verify = config.get('AGENT_CONFIG', 'SSL_VERIFY')
image_uploads = os.path.join(agent_base, 'images')
processing_dir = os.path.join(agent_base, 'processing')
temp_dir = os.path.join(agent_base, 'tempdir')
agent_dep = config.get('AGENT_CONFIG', 'AGENT_DEPLOYMENT')
db_home = config.get('AGENT_CONFIG', 'SYBASE_HOME')
ase_home = config.get('AGENT_CONFIG', 'ASE_HOME')
ocs_home = config.get('AGENT_CONFIG', 'OCS_HOME')
sap_jre8_home = config.get('AGENT_CONFIG', 'SAP_JRE8_HOME')
llm_model_id = config.get('AGENT_CONFIG', 'LLM_MODEL_ID')
llm_model_provider = config.get('AGENT_CONFIG', 'LLM_MODEL_PROVIDER')
llm_model_kwargs = config.get('AGENT_CONFIG', 'LLM_MODEL_KWARGS')
embedding_model = config.get('AGENT_CONFIG', 'EMBEDDING_MODEL')
db_search_args = config.get('AGENT_CONFIG', 'DB_SEARCH_ARGS')
aws_region = config.get('AGENT_CONFIG', 'AWS_REGION')
if not os.path.exists(image_uploads):
    os.makedirs(image_uploads)
if not os.path.exists(processing_dir):
    os.makedirs(processing_dir)
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
hName = socket.gethostname()
hName = hName.split('.')
hName = hName[0]
if os.path.exists(db_home):
    os.environ['LD_LIBRARY_PATH'] = os.path.join(ase_home, 'lib') + ':' + os.path.join(ocs_home, 'lib3p64') + ':' + os.path.join(ocs_home, 'lib')
    os.environ['SYBROOT'] = db_home
    os.environ['SYBASE'] = db_home
    os.environ['SAP_JRE8'] = sap_jre8_home
os.environ['USER_AGENT'] = 'sybase-to-oracle-rag/1.0'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
embedding_fn = HuggingFaceEmbeddings(model_name=embedding_model, encode_kwargs={'normalize_embeddings': True})
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
reranker_model = AutoModel.from_pretrained(embedding_model).to(device)
tokenizer = AutoTokenizer.from_pretrained(embedding_model)
vector_db_path = os.path.join(agent_base, 'RAG')
if not os.path.exists(vector_db_path):
    os.makedirs(vector_db_path)
db = Chroma(persist_directory='./RAG/chroma_claude_db', embedding_function=embedding_fn)
retriever = db.as_retriever(search_kwargs={'k': db_search_args})
llm_model_kwargs = json.loads(llm_model_kwargs)
llm = ChatBedrock(model_id=llm_model_id, provider=llm_model_provider, region_name=aws_region, model_kwargs=llm_model_kwargs)
logdump_bin = os.path.join(gg_home, 'logdump')
ggsci_bin = os.path.join(gg_home, 'ggsci')
LOG_FORMAT = '[%(asctime)s] %(levelname)s - %(message)s'
logging.basicConfig(filename=os.path.join(agent_home, 'agent_error.log'), level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
warnings.simplefilter(action='ignore', category=UserWarning)

def processCheckAll():
    while True:
        time.sleep(300)
        processCheckDemand()
t = threading.Thread(target=processCheckAll)
t.start()

def ILGetStats(procName, jobName):
    while True:
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('stats ' + procName + ' ,TOTAL,LATEST,REPORTRATE SEC \n')
        (ILProcStatRate, stderr) = ssh.communicate(timeout=sshTimeOut)
        if 'ERROR' in ILProcStatRate:
            pass
        else:
            with open(os.path.join(agent_home, jobName, procName + 'Rate.lst'), 'w') as infile:
                infile.write(ILProcStatRate)
        time.sleep(30)
        if not os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
            break

def processCheckDemand():
    if os.path.exists(ggsci_bin):
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('info extract *' + '\n')
        ssh.stdin.write('info replicat *' + '\n')
        ssh.stdin.write('info mgr' + '\n')
        (InfoAll, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'infoall'), mode='w') as outfile2:
            outfile2.write(InfoAll)

@app.route('/')
def index():
    return app.send_static_file('index.html')

def chmod_dir(path):
    for (root, dirs, files) in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 493)
        for f in files:
            os.chmod(os.path.join(root, f), 493)

def OPlaceDebug(filename):
    if agent_debug == 'N':
        for name in filename:
            if os.path.exists(os.path.join(agent_home, name)):
                os.remove(os.path.join(agent_home, name))

class AESCipher:

    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()[:16]
        self.iv = b'OnePlaceMyPlaceV'

    def encrypt(self, raw):
        raw_bytes = raw.encode('utf-8')
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(raw_bytes) + padder.finalize()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(ct).decode('utf-8')

    def decrypt(self, enc):
        ct = base64.b64decode(enc)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plain = decryptor.update(ct) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_plain) + unpadder.finalize()
        return data.decode('utf-8')
cipher = AESCipher('SkyliftMyPlaceJamboUrl111019808')

class ViewExtractLog(Resource):

    def post(self):
        data = request.get_json(force=True)
        extops = data['extops']
        extname = data['extname']
        prmfile = ''
        ExtErrPrint = []
        ExtProcStats = {}
        if extops == 'rpt':
            for name in glob.glob(os.path.join(gg_home, 'dirrpt', '*.rpt')):
                name = name.split('/')[-1]
                if re.match(name, extname + '.rpt', re.IGNORECASE):
                    dest_file = os.path.join(gg_home, 'dirrpt', name)
                    with open(dest_file, 'r') as extErrFile:
                        for line in extErrFile:
                            ExtErrPrint.append(line)
        elif extops != 'rpt':
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            if extops == 'chk':
                ssh.stdin.write('info ' + extname + ' showch debug')
            elif extops == 'stats':
                ssh.stdin.write('stats extract ' + extname + '\n')
            elif extops == 'startdef':
                ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'startatcsn':
                extatcsn = data['extatcsn']
                ssh.stdin.write('start ' + extname + ' atcsn ' + str(extatcsn))
            elif extops == 'startaftercsn':
                extaftercsn = data['extaftercsn']
                ssh.stdin.write('start ' + extname + ' aftercsn ' + str(extaftercsn))
            elif extops == 'stop':
                ssh.stdin.write('stop extract ' + extname + '\n')
            elif extops == 'forcestop':
                ssh.stdin.write('send extract ' + extname + ' forcestop' + '\n')
            elif extops == 'kill':
                ssh.stdin.write('kill extract ' + extname + '\n')
            elif extops == 'extstatus':
                ssh.stdin.write('send extract ' + extname + ' status' + '\n')
            elif extops == 'del':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('sourcedb ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
                ssh.stdin.write('delete extract ' + extname + '\n')
            elif extops == 'pmpdel':
                ssh.stdin.write('delete extract ' + extname + '\n')
            elif extops == 'upgie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('info ' + extname)
                (InfoExt, stderr) = ssh.communicate()
                if 'Integrated' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Integrated Mode !! STOP !!')
                elif 'Oracle Redo Logs' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    (LoginErr, stderr) = ssh.communicate()
                    if 'ERROR' in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                        ssh.stdin.write('send extract ' + extname + ' tranlogoptions PREPAREFORUPGRADETOIE' + '\n')
                        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                        ssh.stdin.write('stop extract ' + extname + '\n')
                        time.sleep(60)
                        ssh.stdin.write('info extract ' + extname + '\n')
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write('register extract ' + extname + ' database' + '\n')
                        RegErr = ssh.stdout.readline()
                        if 'ERROR' in RegErr and 'already registered' not in RegErr:
                            ExtErrPrint.append(RegErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(RegErr)
                            ssh.stdin.write('start extract ' + extname + '\n')
                            time.sleep(60)
                            ssh.stdin.write('info extract ' + extname + ' upgrade' + '\n')
                            ssh.stdin.flush()
                        while True:
                            upg_Output = ssh.stdout.readline()
                            if 'ERROR' in upg_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + ' upgrade ' + '\n')
                                ssh.stdout.flush()
                            elif 'capture.' in upg_Output:
                                break
                        ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'dwnie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('info ' + extname)
                (InfoExt, stderr) = ssh.communicate()
                if 'Oracle Redo Logs' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Classic Mode !! STOP !!')
                elif 'Integrated' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    (LoginErr, stderr) = ssh.communicate()
                    if 'ERROR' in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                        ssh.stdin.write('stop extract ' + extname + '\n')
                        time.sleep(60)
                        ssh.stdin.write('info extract ' + extname + '\n')
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write('info ' + extname + ' downgrade' + '\n')
                        InfoIEErr = ssh.stdout.readline()
                        if 'ready to be downgraded' not in InfoIEErr:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.stdin.write('alter extract ' + extname + ' downgrade integrated tranlog' + '\n')
                            ssh.stdin.write('info extract ' + extname + '\n')
                            ssh.stdin.flush()
                        while True:
                            dwn_Output = ssh.stdout.readline()
                            if 'ERROR' in dwn_Output:
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'Oracle Redo Logs' in dwn_Output:
                                break
                        ssh.stdin.write('unregister extract ' + extname + ' database' + '\n')
                        ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'extetroll':
                ssh.stdin.write('alter extract ' + extname + ' etrollover' + '\n')
            elif extops == 'extbegin':
                beginmode = data['beginmode']
                if beginmode == 'Now':
                    ssh.stdin.write('alter extract ' + extname + ',begin now\n')
                elif beginmode == 'Time':
                    domain = data['domain']
                    alias = data['alias']
                    ctvalue = data['ctvalue']
                    ctvalue = ctvalue.replace('T', ' ')
                    ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' domain ' + domain + '\n')
                    ssh.stdin.write('alter extract ' + extname + ',begin ' + ctvalue + '\n')
                elif beginmode == 'SCN':
                    domain = data['domain']
                    alias = data['alias']
                    scnvalue = data['scnvalue']
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    ssh.stdin.write('alter extract ' + extname + ',scn ' + str(scnvalue) + '\n')
                elif beginmode == 'pmpextseqno':
                    seqnovalue = data['seqnovalue']
                    rbavalue = data['rbavalue']
                    ssh.stdin.write('alter extract ' + extname + ',extseqno ' + str(seqnovalue) + ',extrba ' + str(rbavalue) + '\n')
            elif extops == 'exttraildel':
                trailname = data['trailname']
                for name in trailname:
                    ssh.stdin.write('delete exttrail ' + name + ', Extract ' + extname + '\n')
            elif extops == 'exttrailadd':
                trailname = data['trailname']
                trailtype = data['trailtype']
                trailsize = data['trailsize']
                ssh.stdin.write('add ' + trailtype + ' ' + trailname + ', Extract ' + extname + ',megabytes ' + str(trailsize) + '\n')
            elif extops == 'cachemgr':
                ssh.stdin.write('send extract ' + extname + ' cachemgr cachestats' + '\n')
            elif extops == 'extunreg':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                ssh.stdin.write('unregister extract ' + extname + ' database' + '\n')
            elif extops == 'edit':
                extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
                with open(extPrm, 'r') as extPrmFile:
                    prmfile = extPrmFile.read()
            (chkExt, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            if extops == 'stats':
                with open(os.path.join(agent_home, 'extStats'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(agent_home, 'extStats')) as extErrFile:
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
                            if not line.strip().startswith('No'):
                                OpNameFinal = ''
                                OpName = line.strip().split()[0:-1]
                                if len(OpName) > 0:
                                    for Op in OpName:
                                        OpNameFinal = OpNameFinal + Op
                                    OpNameFinal = OpNameFinal.lstrip()
                                    Oper = line.split()[-1]
                                    ExtProcStats[TabName].update({OpNameFinal: Oper})
            else:
                with open(os.path.join(agent_home, 'ChkExt.lst'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(agent_home, 'ChkExt.lst'), 'r') as extErrFile:
                    extErrFile = extErrFile.readlines()[8:]
                    for line in extErrFile:
                        if 'GGSCI' in line:
                            line = line.split('>', 1)[-1]
                            ExtErrPrint.append(line)
                        else:
                            ExtErrPrint.append(line)
        return [ExtErrPrint, prmfile, ExtProcStats]

class ggDepDet(Resource):

    def get(self):
        Client_Ver = ''
        try:
            GGVer = subprocess.check_output([ggsci_bin, '-v'], stderr=subprocess.STDOUT, universal_newlines=True)
            line = GGVer.splitlines()
            GGVer = line[2].split()[1]
            GGDBVer = line[3].split()[4]
        except Exception as e:
            GGVer = 'Not Installed'
            GGDBVer = 'Not Installed'
            logger.info(str(e))
        try:
            SoftList = []
            Client_Ver = pyodbc.version
            if Client_Ver[0] == 21:
                SoftList.append({'label': 'Oracle GoldenGate 21.3.0.0.0', 'value': '21.3.0.0.0'})
            elif Client_Ver[0] == 19:
                SoftList.append({'label': 'Oracle GoldenGate 21.3.0.0.0', 'value': '21.3.0.0.0'})
                SoftList.append({'label': 'Oracle GoldenGate 19.1.0.0.210720 - July 2021', 'value': '19.1.0.0.210720'})
        except cx_Oracle.DatabaseError as e:
            Client_Ver = 'Client Binary not Dectected'
            logger.info(str(e))
        return [hName, OSPlat, OSPlatBit, Client_Ver, GGVer, GGDBVer, gg_home, db_home, SoftList]

class getSchemaName(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
      
        try:
            val = selectConn(dbname)
            con = val[0]
            
            cursor = con.cursor()
            schemaList = []
            cursor.execute("SELECT DISTINCT user_name(uid) AS schema_name FROM sysobjects WHERE type = 'U' ORDER BY schema_name")
            schemaName = cursor.fetchall()
            for name in schemaName:
                schemaList.append(name[0])
            schemaList = list(set(schemaList))
            
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [schemaList]

class getTypeName(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            typeList = []
            cursor.execute('SELECT name from systypes where usertype>100')
            typeName = cursor.fetchall()
            for name in typeName:
                typeList.append(name[0])
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [typeList]

class getTypeDetails(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        typeName = data['typeName']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            cursor.execute(f"exec sp_help '{typeName}'")
            typeDet = cursor.fetchall()
            typeDDL = ''
            for name in typeDet:
                if name[5].strip() == '0':
                    nullvalue = 'not null'
                else:
                    nullvalue = 'null'
                if name[1] == int:
                    typeDDL = ('sp_addtype ' + name[0] + ',' + name[1], ',' + nullvalue)
                elif name[1] == 'decimal':
                    typeDDL = 'sp_addtype ' + name[0] + ',' + name[1] + '(' + name[3].strip() + ',' + name[4].strip() + '),' + nullvalue
                else:
                    typeDDL = 'sp_addtype ' + name[0] + ',' + name[1] + '(' + name[2].strip() + '),' + nullvalue
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [typeDDL]

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
                tabDetails[name[1]] = {'owner': name[0]}
                schemaList.append(name[0])
            schemaList = list(set(schemaList))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tabDetails, schemaList]

class getKeyConstrants(Resource):

    def get(self):
        file_names = []
        try:
            directory = 'Foreign_key_constraints'
            file_names = [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f)) and (os.path.getsize(os.path.join(directory, f)) > 0)]
        except Exception as e:
            logger.error(str(e))
        return file_names

class getKeyConstraintsLines(Resource):

    def post(self):
        data = request.get_json(force=True)
        tableName = data['tableName']
        file_path = f'Foreign_key_constraints/{tableName}.txt'
        lines = ''
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            return ''
        return jsonify({'constraintText': lines})

class constraintDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        constraintDDL = data['constraintDDL']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        constraintName = data['constraintName']       
        
        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)        

        converted_queries = []
        for query in constraintDDL:
            if query.strip():
               oracle_converted_sql = convertCodeGenAi(query)
               converted_queries.append(oracle_converted_sql)
               time.sleep(random.randint(5, 10))

        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'constraints')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{constraintName}.txt"
            file_path = os.path.join(folder_path, file_name)

            alter_statements = [line for line in converted_queries if line.strip().upper().startswith('ALTER TABLE')]
            joined_alter_statements = ',\n'.join(alter_statements)
            with open(file_path, "w") as file:
                file.write(joined_alter_statements)
            s3_key = f'Converted/constraints/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()

        return jsonify({'converted_lines': converted_queries})

class getGrantKeyConstraints(Resource):

    def get(self):
        file_names = []
        try:
            directory = 'Grant_constraints'
            file_names = [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f)) and (os.path.getsize(os.path.join(directory, f)) > 0)]
        except Exception as e:
            logger.error(str(e))
        return file_names

class getGrantKeyConstraintsLines(Resource):

    def post(self):
        data = request.get_json(force=True)
        tableName = data['tableName']
        file_path = f'Grant_constraints/{tableName}.txt'
        lines = ''
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            return ''
        return jsonify({'constraintText': lines})

class grantKeyDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        constraintDDL = data['constraintDDL']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        grantName = data['grantName']
        converted_queries = []

        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)
 
        for query in constraintDDL:
            oracle_converted_sql = convertCodeGenAi(query)
            converted_queries.append(oracle_converted_sql)
            time.sleep(random.randint(5, 10))
        
        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'grants')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{grantName}.txt"
            file_path = os.path.join(folder_path, file_name)
            clean_lines = [line.strip() for line in converted_queries if line.strip()]
            formatted = '\n'.join(line + ',' if idx < len(clean_lines) - 1 else line
                         for idx, line in enumerate(clean_lines))
            with open(file_path, "w") as file:
                file.write(formatted)
            s3_key = f'Converted/grants/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()

        return jsonify({'converted_lines': converted_queries})

class getIndexConstraints(Resource):

    def get(self):
        file_names = []
        try:
            directory = 'indexes'
            file_names = [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f)) and (os.path.getsize(os.path.join(directory, f)) > 0)]
        except Exception as e:
            logger.error(str(e))
        return file_names

class getIndexConstraintsLines(Resource):

    def post(self):
        data = request.get_json(force=True)
        tableName = data['tableName']
        file_path = f'indexes/{tableName}.txt'
        lines = ''
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            return ''
        return jsonify({'constraintText': lines})

class indexDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
       
        constraintDDL = data.get('constraintDDL', [])
        indexName = data['indexName']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        sourceDep = data['sourceDep']

        converted_queries = []

        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)

        for query in constraintDDL:
            oracle_converted_sql = convertCodeGenAi(query)
            converted_queries.append(oracle_converted_sql)
            time.sleep(random.randint(5, 10))

        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'indexes')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{indexName}.txt"
            file_path = os.path.join(folder_path, file_name)
            cleaned_list = [re.sub(r',\s*$', '', item.strip()) for item in converted_queries]
            cleaned_string = "\n".join(cleaned_list)
            with open(file_path, "w") as file:
                file.write(cleaned_string)
            s3_key = f'Converted/indexes/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()         

        return jsonify({'converted_lines': converted_queries})

def extract_view_mappings(sql: str):
    mappings = {'view_name': '', 'table_aliases': {}, 'column_mapping': {}, 'reverse_column_mapping': {}}
    col_counter = 1
    view_match = re.search('CREATE\\s+VIEW\\s+(\\w+)', sql, re.IGNORECASE)
    if not view_match:
        raise ValueError('No view name found.')
    view_name = view_match.group(1)
    mappings['view_name'] = view_name
    table_matches = re.findall('(FROM|JOIN)\\s+(\\w+)(?:\\s+(\\w+))?', sql, re.IGNORECASE)
    for (i, (_, table_name, alias)) in enumerate(table_matches, 1):
        actual_alias = alias if alias else table_name
        mappings['table_aliases'][actual_alias] = table_name
    alias_mapping = mappings['table_aliases']
    all_cols = re.findall('\\b(\\w+)\\.((?:\\[[^\\]]+\\])|(?:\\w+))', sql)
    for (alias, col) in all_cols:
        clean_col = col.strip('[]')
        if clean_col not in mappings['column_mapping']:
            dummy_col = f'col_{col_counter}'
            mappings['column_mapping'][clean_col] = dummy_col
            mappings['reverse_column_mapping'][dummy_col] = clean_col
            col_counter += 1
    select_match = re.search('SELECT\\s+(.*?)\\s+FROM', sql, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_cols = select_match.group(1)
        cols = [c.strip() for c in re.split(',(?![^\\(]*\\))', select_cols)]
        for c in cols:
            c = re.sub('\\s+AS\\s+\\w+', '', c, flags=re.IGNORECASE)
            tokens = re.findall('(\\[[^\\]]+\\]|\\w+)', c)
            for token in tokens:
                clean_token = token[1:-1] if token.startswith('[') and token.endswith(']') else token
                if clean_token.upper() in ('AS', 'COUNT', 'SUM', 'MAX', 'MIN', 'AVG', 'NULL') or clean_token in alias_mapping or clean_token in mappings['column_mapping']:
                    continue
                dummy_col = f'col_{col_counter}'
                mappings['column_mapping'][clean_token] = dummy_col
                mappings['reverse_column_mapping'][dummy_col] = clean_token
                col_counter += 1
    return mappings

def apply_anonymization_view(sql: str, mappings: dict):
    sql = re.sub(f"\\b{re.escape(mappings['view_name'])}\\b", 'view_1', sql)
    for (i, (alias, table_name)) in enumerate(mappings['table_aliases'].items(), 1):
        dummy_table = f'dummy_table_{i}'
        if alias != table_name:
            sql = re.sub(f'\\b{re.escape(table_name)}\\b\\s+{re.escape(alias)}\\b', f'{dummy_table} {alias}', sql)
        sql = re.sub(f'\\b{re.escape(table_name)}\\b', dummy_table, sql)
    for (orig, dummy) in mappings['column_mapping'].items():
        sql = re.sub(f'\\[{re.escape(orig)}\\]', f'[{dummy}]', sql)
        sql = re.sub(f'\\b{re.escape(orig)}\\b', dummy, sql)
    return sql

def deanonymize_view_sql(anonymized_sql: str, mappings: dict):
    sql = anonymized_sql
    for (dummy_col, orig_col) in sorted(mappings['reverse_column_mapping'].items(), key=lambda x: -len(x[0])):
        sql = re.sub(f'\\b{dummy_col.upper()}\\b', orig_col, sql)
        sql = re.sub(f'\\[\\b{dummy_col.upper()}\\b\\]', f'[{orig_col}]', sql)
    for (i, (alias, table_name)) in enumerate(mappings['table_aliases'].items(), 1):
        dummy_table = f'dummy_table_{i}'
        if alias != table_name:
            sql = re.sub(f'\\b{dummy_table.upper()}\\s+{alias}\\b', f'{table_name} {alias}', sql)
        else:
            sql = re.sub(f'\\b{dummy_table.upper()}\\b', table_name, sql)
    sql = re.sub(f'\\bVIEW_1\\b', mappings['view_name'], sql, count=1)
    return sql

def convertCodeGenAi(sql_query):
    system_prompt_text = load_prompt_template('./RAG/code_prompt')
    strict_prompt_template = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(system_prompt_text), HumanMessagePromptTemplate.from_template('{input}')])
    context = extract_types_and_query_context(sql_query=sql_query, db=db, top_k_per_type=db_search_args, use_reranker=True, rerank_fn=rerank_results)
    translate = get_sql_rag_chain(llm, retriever, strict_prompt_template, context)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            oracle_ddl = translate(sql_query)
            return oracle_ddl
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait_time = 2 ** attempt
                logger.info(f'[Retry {attempt + 1}/{max_retries}] Throttled. Waiting {wait_time} seconds...')
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            logger.error(f'Unexpected error on attempt {attempt + 1}: {e}')
            time.sleep(2 ** attempt)
    raise Exception('Max retries exceeded while translating SQL.')

def convertProcedureGenAi(sql_query):
    system_prompt_text = load_prompt_template('./RAG/procedure_prompt')
    strict_prompt_template = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(system_prompt_text), HumanMessagePromptTemplate.from_template('{input}')])
    context = extract_types_and_query_context(sql_query=sql_query, db=db, top_k_per_type=db_search_args, use_reranker=True, rerank_fn=rerank_results)
    translate = get_sql_rag_chain(llm, retriever, strict_prompt_template, context)
    oracle_ddl = translate(sql_query)
    return oracle_ddl

def convertTableGenAi(sql_query):
    system_prompt_text = load_prompt_template('./RAG/table_ddl_prompt')
    strict_prompt_template = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(system_prompt_text), HumanMessagePromptTemplate.from_template('{input}')])
    context = extract_types_and_query_context(sql_query=sql_query, db=db, top_k_per_type=db_search_args, use_reranker=True, rerank_fn=rerank_results)
    translate = get_sql_rag_chain(llm, retriever, strict_prompt_template, context)
    oracle_ddl = translate(sql_query)
    return oracle_ddl

class viewDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        viewDDL = data['viewProc']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        viewName = data['viewName']

        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)

        map_data = extract_view_mappings(viewDDL)
        anon_sql = apply_anonymization_view(viewDDL, map_data)
        oracle_converted_sql = convertCodeGenAi(anon_sql)
        viewDDLStmt = deanonymize_view_sql(oracle_converted_sql, map_data)
        
        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'views')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{viewName}.txt"
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as file:
                file.write(viewDDLStmt)
            s3_key = f'Converted/views/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()

        return jsonify({'converted_lines': viewDDLStmt})

def extract_proc_details(sql: str):
    result = {'procedure_name': None, 'parameters': [], 'local_variables': [], 'columns': [], 'tables': []}
    proc_match = re.search('CREATE\\s+PROCEDURE\\s+(\\w+)', sql, re.IGNORECASE)
    if proc_match:
        result['procedure_name'] = proc_match.group(1)
    param_match = re.search('CREATE\\s+PROCEDURE\\s+\\w+\\s*(\\(?.*?\\)?)\\s+AS', sql, re.IGNORECASE | re.DOTALL)
    if param_match:
        params_str = param_match.group(1).strip(' ()\n\t')
        params = re.split(',(?![^(]*\\))', params_str)
        result['parameters'] = [p.strip() for p in params if p.strip()]
    declare_blocks = re.findall('\\bDECLARE\\b\\s+(.*?)(?=\\b(?:SELECT|BEGIN|IF|EXEC|RETURN|END)\\b|\\n\\s*\\n)', sql, re.IGNORECASE | re.DOTALL)
    local_vars = []
    for block in declare_blocks:
        vars_found = re.findall('@[\\w]+', block)
        local_vars.extend(vars_found)
    result['local_variables'] = sorted(set(local_vars))
    select_clauses = re.findall('\\bSELECT\\b\\s+(.*?)\\bFROM\\b', sql, re.IGNORECASE | re.DOTALL)
    columns_set = set()
    for clause in select_clauses:
        cols = re.split(',(?![^\\(\\[]*[\\)\\]])', clause)
        for col in cols:
            col = col.strip()
            col = re.sub('\\s+AS\\s+\\[?\\w+\\]?$', '', col, flags=re.IGNORECASE).strip()
            col = re.sub('\\s+AS\\s+\\w+$', '', col, flags=re.IGNORECASE).strip()
            col_refs = re.findall('\\b\\w+\\.(\\[[^\\]]+\\]|\\w+)', col)
            if col_refs:
                for c in col_refs:
                    columns_set.add(c.strip('[]'))
            elif re.match('^[\\w\\[\\]]+$', col):
                columns_set.add(col.strip('[]'))
    insert_columns = re.findall('INSERT\\s+INTO\\s+\\w+\\s*\\((.*?)\\)', sql, re.IGNORECASE | re.DOTALL)
    for col_block in insert_columns:
        cols = re.split(',(?![^\\(\\[]*[\\)\\]])', col_block)
        for col in cols:
            col = col.strip(' []')
            if col:
                columns_set.add(col)
    extra_cols = re.findall('\\b\\w+\\.(\\[[^\\]]+\\]|\\w+)', sql)
    for c in extra_cols:
        columns_set.add(c.strip('[]'))
    result['columns'] = sorted(columns_set)
    table_matches = re.findall('\\b(?:FROM|JOIN|INTO|UPDATE|DELETE\\s+FROM)\\s+(\\w+)', sql, re.IGNORECASE)
    seen = set()
    tables = []
    for t in table_matches:
        if t not in seen:
            seen.add(t)
            tables.append(t)
    result['tables'] = tables
    return result

def replace_proc_with_dummies(sql: str, details: dict):
    mappings = {'procedure': {details['procedure_name']: 'proc_name'} if details['procedure_name'] else {}, 'parameters': {}, 'local_variables': {}, 'columns': {}, 'tables': {}}
    if details['procedure_name']:
        sql = re.sub(f"(?i)(CREATE\\s+PROCEDURE\\s+){re.escape(details['procedure_name'])}", f'\\1proc_name', sql)
    for (idx, param) in enumerate(details['parameters'], 1):
        name_match = re.match('@?(\\w+)', param)
        if name_match:
            param_name = name_match.group(1)
            dummy_param = f'@param_{idx}'
            mappings['parameters'][f'@{param_name}'] = dummy_param
            pattern = re.compile(f'(?<!\\w)@{param_name}(?!\\w)', re.IGNORECASE)

            def safe_replace(line):
                masked = line.replace('@@', '__ATAT__')
                replaced = pattern.sub(dummy_param, masked)
                return replaced.replace('__ATAT__', '@@')
            sql = '\n'.join((safe_replace(line) for line in sql.splitlines()))
    for (idx, var) in enumerate(details.get('local_variables', []), 1):
        var_name = var.lstrip('@')
        dummy_var = f'@var_{idx}'
        mappings['local_variables'][f'@{var_name}'] = dummy_var
        sql = '\n'.join((line if '@@' in line else re.sub(f'(?<!\\w)@{var_name}(?!\\w)', dummy_var, line) for line in sql.splitlines()))
    for (idx, table) in enumerate(details['tables'], 1):
        dummy_table = f'dummy_table{idx}'
        mappings['tables'][table] = dummy_table
        sql = re.sub(f'(?<!\\w){re.escape(table)}(?!\\w)', dummy_table, sql)
    for (idx, col) in enumerate(sorted(details['columns'], key=len, reverse=True), 1):
        dummy_col = f'col_{idx}'
        mappings['columns'][col] = dummy_col
        match = re.match('(?i)(\\w+)\\.(\\[?)(\\w+)(\\]?)', col)
        if match:
            (alias, left_bracket, col_name, right_bracket) = match.groups()
            has_brackets = left_bracket == '[' and right_bracket == ']'
            pattern = re.compile(f'(?<!\\w){alias}\\.{re.escape(left_bracket)}{re.escape(col_name)}{re.escape(right_bracket)}(?!\\w)', re.IGNORECASE)
            replacement = f'{alias}.[{dummy_col}]' if has_brackets else f'{alias}.{dummy_col}'
            sql = pattern.sub(replacement, sql)
        col_escaped = re.escape(col.split('.')[-1])
        pattern = re.compile(f'(?<!\\w)(\\w+\\.)?{col_escaped}(?!\\w)')

        def replacer(match):
            alias = match.group(1) or ''
            return alias + dummy_col
        sql = pattern.sub(replacer, sql)
    return (sql, mappings)

def deanonymize_proc(sql: str, mappings: dict) -> str:
    inv_locals = {v.lstrip('@'): k.lstrip('@') for (k, v) in mappings.get('local_variables', {}).items()}
    for (dummy_var, real_var) in sorted(inv_locals.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(f'(?<!\\w){re.escape(dummy_var)}(?!\\w)', re.IGNORECASE)
        sql = pattern.sub(real_var, sql)
    inv_params = {v.lstrip('@'): k.lstrip('@') for (k, v) in mappings.get('parameters', {}).items()}
    for (dummy_param, real_param) in sorted(inv_params.items(), key=lambda x: -len(x[0])):
        v_pattern = re.compile(f'(?<!\\w)v_{re.escape(dummy_param)}(?!\\w)', re.IGNORECASE)
        sql = v_pattern.sub(f'v_{real_param}', sql)
        pattern = re.compile(f'(?<!\\w){re.escape(dummy_param)}(?!\\w)', re.IGNORECASE)
        sql = pattern.sub(real_param, sql)
    inv_columns = {}
    for (real_col, dummy_col) in mappings.get('columns', {}).items():
        match = re.match('(?i)(\\w+)\\.(\\[?\\w+\\]?)', real_col)
        if match:
            (alias, real_field) = match.groups()
            dummy_field = dummy_col.strip('[]')
            real_field = real_field.strip('[]')
            inv_columns[f'{alias}.{dummy_field}'] = f'{alias}.{real_field}'
            inv_columns[f'{alias}.[{dummy_field}]'] = f'{alias}.{real_field}'
        else:
            dummy_field = dummy_col.strip('[]')
            real_field = real_col.strip('[]')
            inv_columns[dummy_field] = real_field
            inv_columns[f'[{dummy_field}]'] = real_field
    for (full_dummy_col, full_real_col) in sorted(inv_columns.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(f'(?<!\\w){re.escape(full_dummy_col)}(?!\\w)', re.IGNORECASE)
        sql = pattern.sub(full_real_col, sql)
    inv_tables = {v: k for (k, v) in mappings.get('tables', {}).items()}
    for (dummy_table, real_table) in sorted(inv_tables.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(f'(?<!\\w){re.escape(dummy_table)}(?!\\w)', re.IGNORECASE)
        sql = pattern.sub(real_table, sql)
    inv_proc = {v: k for (k, v) in mappings.get('procedure', {}).items()}
    for (dummy_proc, real_proc) in sorted(inv_proc.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(f'(?<!\\w){re.escape(dummy_proc)}(?!\\w)', re.IGNORECASE)
        sql = pattern.sub(real_proc, sql)
    return sql

def split_sql(sql: str, min_lines: int=100):
    sql = sql.strip()
    if sql.count('\n') + 1 < min_lines or (sql.upper().count('BEGIN') <= 1 and sql.upper().count('END') <= 1):
        return [sql]
    sql = re.sub('\\r\\n|\\r', '\n', sql)
    chunks = []
    lines = sql.split('\n')
    current_chunk = []
    block_stack = []
    capture_proc_head = False
    declared = False
    found_begin_transaction = False
    in_if_block = False
    if_block_indent = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        upper = stripped.upper()
        if re.match('^CREATE\\s+PROCEDURE\\b', upper):
            capture_proc_head = True
        if capture_proc_head and (not found_begin_transaction):
            if 'BEGIN TRANSACTION' in upper:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = [line]
                capture_proc_head = False
                found_begin_transaction = True
                i += 1
                continue
            else:
                current_chunk.append(line)
                i += 1
                continue
        if re.match('^\\s*IF\\b', upper):
            in_if_block = True
            if_block_indent = 0
            while i < len(lines):
                block_line = lines[i]
                block_stripped = block_line.strip()
                block_upper = block_stripped.upper()
                current_chunk.append(block_line)
                if re.match('^\\s*BEGIN\\b', block_upper):
                    block_stack.append('BEGIN')
                    if_block_indent += 1
                elif re.match('^\\s*END\\b', block_upper):
                    if block_stack:
                        block_stack.pop()
                        if_block_indent -= 1
                        if if_block_indent <= 0:
                            chunks.append('\n'.join(current_chunk).strip())
                            current_chunk = []
                            in_if_block = False
                            i += 1
                            break
                i += 1
            continue
        if re.match('^\\s*INSERT\\b', upper):
            insert_chunk = [line]
            i += 1
            while i < len(lines):
                select_line = lines[i]
                if re.search(';\\s*$', select_line) or re.match('^\\s*(SELECT|WHERE|FROM|VALUES|JOIN)', select_line, re.IGNORECASE):
                    pass
                if not select_line.strip().endswith(',') and (re.search('\\bFROM\\b', select_line, re.IGNORECASE) or re.search('\\bWHERE\\b', select_line, re.IGNORECASE) or re.match('^\\s*SELECT\\b', select_line, re.IGNORECASE)):
                    next_line = lines[i + 1] if i + 1 < len(lines) else ''
                if next_line.strip().upper().startswith(('INSERT', 'IF', 'SELECT', 'EXEC', 'RETURN')):
                    break
                insert_chunk.append(select_line)
                i += 1
            chunks.append('\n'.join(insert_chunk).strip())
            continue
        if re.match('^\\s*BEGIN\\b', upper):
            if current_chunk:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
            block_stack.append('BEGIN')
        current_chunk.append(line)
        if re.match('^\\s*END\\b', upper):
            if block_stack:
                block_stack.pop()
                if not block_stack:
                    chunks.append('\n'.join(current_chunk).strip())
                    current_chunk = []
            i += 1
            continue
        if not block_stack and (not in_if_block) and re.match('^(IF|SELECT|INSERT|UPDATE|DELETE|EXEC|RETURN|ROLLBACK|COMMIT)\\b', upper):
            if len(current_chunk) > 1:
                chunks.append('\n'.join(current_chunk[:-1]).strip())
                current_chunk = [current_chunk[-1]]
        i += 1
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
    return chunks

def is_chunk_boundary(chunk):
    chunk = chunk.strip().lower()
    return chunk.endswith('end') or chunk.startswith('commit') or 'rollback' in chunk or ('return' in chunk)

def smart_merge_chunks(chunks):
    merged_blocks = []
    buffer = ''
    for chunk in chunks:
        buffer += '\n' + chunk
        if is_chunk_boundary(chunk):
            merged_blocks.append(buffer.strip())
            buffer = ''
    if buffer.strip():
        merged_blocks.append(buffer.strip())
    return merged_blocks

def split_sql_begintransaction(sql: str, min_lines: int=100):
    sql = sql.strip()
    if sql.count('\n') + 1 < min_lines:
        return [sql]
    sql = re.sub('\\r\\n|\\r', '\n', sql)
    lines = sql.split('\n')
    pre_transaction = []
    transaction_block = []
    found_begin_transaction = False
    for line in lines:
        upper = line.strip().upper()
        if not found_begin_transaction:
            if 'BEGIN TRANSACTION' in upper:
                found_begin_transaction = True
                transaction_block.append(line)
            else:
                pre_transaction.append(line)
        else:
            transaction_block.append(line)
    chunks = []
    if pre_transaction:
        chunks.append('\n'.join(pre_transaction).strip())
    if transaction_block:
        chunks.append('\n'.join(transaction_block).strip())
    return chunks

class readConvertFile(Resource):

    def get(self):
        file_path = os.path.join(agent_home,'convert_output.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return '⚠️ File not found.'
        except Exception as e:
            return f'⚠️ Error reading file: {str(e)}'

def add_metadata_headers(chunks, procedure_name):
    total = len(chunks)
    return [f'-- This is part of procedure {procedure_name}, chunk {i + 1} of {total}\n' + chunk for (i, chunk) in enumerate(chunks)]

def correctingProcQuery(query):
    lines = query.splitlines()
    output_lines = []
    declare_block = []
    begin_block = []
    begin_statements = []
    remove_exception = False
    inside_exception = False
    inside_declare = False
    inside_begin_block = False
    chunk_seen = False
    exception_count = 0
    for line in lines:
        stripped = line.strip()
        if re.match('^EXCEPTION\\b', stripped, re.IGNORECASE):
            exception_count += 1
    for line in lines:
        stripped = line.strip()
        chunk_match = re.search('CHUNK\\s+(\\d+)\\s+OF\\s+(\\d+)', stripped, re.IGNORECASE)
        if chunk_match:
            chunk_seen = True
            current_chunk = int(chunk_match.group(1))
            total_chunks = int(chunk_match.group(2))
            remove_exception = current_chunk != total_chunks
        if (remove_exception or not chunk_seen) and exception_count > 1 and re.match('^EXCEPTION\\b', stripped, re.IGNORECASE):
            inside_exception = True
            continue
        if inside_exception:
            if re.match('^END\\b', stripped, re.IGNORECASE):
                inside_exception = False
            continue
        if re.match('^(AS|DECLARE)\\b', stripped, re.IGNORECASE):
            inside_declare = True
            if re.match('^DECLARE\\b', stripped, re.IGNORECASE):
                continue
            output_lines.append(line)
            continue
        if inside_declare:
            if re.match('^BEGIN\\b', stripped, re.IGNORECASE):
                inside_declare = False
                inside_begin_block = True
                continue
            declare_block.append(line)
            continue
        if inside_begin_block:
            begin_block.append(line)
            if stripped.endswith(';'):
                inside_begin_block = False
            continue
        output_lines.append(line)
    current_stmt = ''
    for line in begin_block:
        normalized = ' '.join(line.strip().split())
        current_stmt += normalized + ' '
        if normalized.endswith(';'):
            begin_statements.append(current_stmt)
            current_stmt = ''
    if current_stmt.strip():
        begin_statements.append(current_stmt.strip())
    final_result = []
    inserted = False
    for line in output_lines:
        if re.search('\\bRETURN\\s+\\S+\\s*;', line, flags=re.IGNORECASE):
            line = re.sub('\\bRETURN\\s+\\S+\\s*;', 'RETURN;', line, flags=re.IGNORECASE)
        final_result.append(line)
        if not inserted and re.match('^AS\\b', line.strip(), re.IGNORECASE):
            final_result.extend(declare_block)
            inserted = True
            final_result.append('BEGIN')
            final_result.extend(begin_statements)
    return '\n'.join(final_result)

class procDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        procDDL = data['viewProc']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        procName = data['procName']        
        
        log_file = os.path.join(agent_home,'convert_output.txt')    
        if os.path.exists(log_file):
            os.remove(log_file)

        details = extract_proc_details(procDDL)
        (replaced_sql, mappings) = replace_proc_with_dummies(procDDL, details)
        chunks = split_sql(replaced_sql)
        merged_chunks = smart_merge_chunks(chunks)
        match = re.search('CREATE\\s+PROCEDURE\\s+(\\w+)', replaced_sql, re.IGNORECASE)
        proc_name = match.group(1) if match else 'UnknownProcedure'
        chunks_with_headers = add_metadata_headers(merged_chunks, proc_name)
        original_converted_sql = ''
        for chunk in chunks_with_headers:
            oracle_converted_sql = convertProcedureGenAi(chunk)
            original_converted_sql += f'\n{oracle_converted_sql}\n'
            time.sleep(random.randint(5, 10))
        original_sql = deanonymize_proc(original_converted_sql.strip(), mappings)
        original_sql = correctingProcQuery(original_sql.strip())
        
        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'procedure')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{procName}.txt"
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as file:
                file.write(original_sql)
            s3_key = f'Converted/procedure/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()
        
        return jsonify({'converted_lines': original_sql.strip()})

def anonymize_trigger_sql(sql: str):
    SQL_KEYWORDS = {'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'DELETE', 'JOIN', 'ON', 'AS', 'BEGIN', 'END', 'IF', 'EXISTS', 'PRINT', 'ROLLBACK', 'FOR', 'INSERTED', 'DELETED', 'GETDATE', 'AND', 'OR', 'NOT', 'NULL', 'LIKE', 'CREATE', 'TRIGGER', 'TABLE', 'FOR', 'ROW', 'AFTER', 'BEFORE'}
    table_counter = 1
    column_counter = 1
    trigger_counter = 1
    table_map = {}
    column_map = {}
    trigger_map = {}
    string_literals = re.findall("'[^']*'", sql)
    placeholders = [f'__STR_{i}__' for i in range(len(string_literals))]
    for (lit, ph) in zip(string_literals, placeholders):
        sql = sql.replace(lit, ph)
    trigger_match = re.search('CREATE\\s+TRIGGER\\s+(\\w+)', sql, re.IGNORECASE)
    if trigger_match:
        real_trigger = trigger_match.group(1)
        dummy_trigger = f'TRG_{trigger_counter}'
        trigger_map[real_trigger] = dummy_trigger
        sql = re.sub(f'\\b{real_trigger}\\b', dummy_trigger, sql, flags=re.IGNORECASE)
    table_names = set()
    for keyword in ['ON', 'INTO', 'INSERT INTO', 'UPDATE']:
        pattern = f'{keyword}\\s+(\\w+)'
        found = re.findall(pattern, sql, flags=re.IGNORECASE)
        for tbl in found:
            if tbl.lower() in ('inserted', 'deleted'):
                continue
            table_names.add(tbl)
    for tbl in sorted(table_names, key=lambda x: -len(x)):
        if tbl not in table_map:
            table_map[tbl] = f'T{table_counter}'
            table_counter += 1
        sql = re.sub(f'\\b{tbl}\\b', table_map[tbl], sql, flags=re.IGNORECASE)
    col_lists = re.findall('INSERT\\s+INTO\\s+\\w+\\s*\\(([^)]+)\\)', sql, flags=re.IGNORECASE)
    for col_list in col_lists:
        cols = [c.strip() for c in col_list.split(',')]
        for col in cols:
            if not col or col.upper() in SQL_KEYWORDS:
                continue
            if col not in column_map:
                column_map[col] = f'col_{column_counter}'
                column_counter += 1
    tokens = re.findall('\\b\\w+\\b', sql)
    for token in tokens:
        upper_token = token.upper()
        if upper_token in SQL_KEYWORDS:
            continue
        if token.isdigit():
            continue
        if token in ('inserted', 'deleted'):
            continue
        if re.match('T\\d+', token):
            continue
        if token in trigger_map.values():
            continue
        if token in table_map.values():
            continue
        if token not in column_map:
            column_map[token] = f'col_{column_counter}'
            column_counter += 1
    parts = re.split('(__STR_\\d+__)', sql)
    for i in range(len(parts)):
        if not parts[i].startswith('__STR_'):
            for (col_name, dummy_col) in column_map.items():
                parts[i] = re.sub(f'\\b{col_name}\\b', dummy_col, parts[i])
    sql = ''.join(parts)
    for (ph, lit) in zip(placeholders, string_literals):
        sql = sql.replace(ph, lit)
    return (sql, {'tables': table_map, 'columns': column_map, 'trigger': trigger_map})

def deanonymize_trigger_sql(anonymized_sql: str, mappings: dict):
    inv_table_map = {v: k for (k, v) in mappings.get('tables', {}).items()}
    inv_column_map = {v: k for (k, v) in mappings.get('columns', {}).items()}
    inv_trigger_map = {v: k for (k, v) in mappings.get('trigger', {}).items()}

    def replace_all(text, replacements):
        for dummy_name in sorted(replacements.keys(), key=len, reverse=True):
            original_name = replacements[dummy_name]
            pattern = re.compile(f'\\b{re.escape(dummy_name)}\\b', re.IGNORECASE)
            text = pattern.sub(original_name, text)
        return text
    sql = replace_all(anonymized_sql, inv_column_map)
    sql = replace_all(sql, inv_table_map)
    sql = replace_all(sql, inv_trigger_map)
    return sql

class trigDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        trigDDL = data['viewProc']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        trigName = data['trigName']

        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)

        (anonymized_sql, mappings) = anonymize_trigger_sql(trigDDL)
        oracle_converted_sql = convertCodeGenAi(anonymized_sql)
        original_sql = deanonymize_trigger_sql(oracle_converted_sql, mappings)

        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'trigger')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{trigName}.txt"
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as file:
                file.write(original_sql)
            s3_key = f'Converted/trigger/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()

        return jsonify({'converted_lines': original_sql.strip()})

class getViewName(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            viewDetails = {}
            schemaList = []
            cursor.execute("SELECT user_name(uid) AS owner, name AS tabname FROM sysobjects WHERE type = 'V' AND name NOT LIKE 'sys%'")
            viewName = cursor.fetchall()
            viewList = []
            for name in viewName:
                viewList.append({'vcreator': name[0].strip(), 'viewtext': name[1].strip()})
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
                procList.append({'owner': name[0].strip(), 'procName': name[1].strip()})
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify({'proc': procList, 'schemas': schemaList})

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
            for name in table_fetch:
                trigName.append({'owner': name[0].strip(), 'trigName': name[1].strip(), 'trigTable': name[2].strip()})
            for name in table_fetch:
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
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procNameList = []
            for schema in schemaList:
                cursor.execute("\n                                SELECT su.name + '.' + so.name AS full_trigger_name, so.name AS trigger_name, su.name AS owner, \n                                so.crdate AS created_date FROM sysobjects so JOIN sysusers su ON so.uid = su.uid \n                                WHERE so.type = 'TR' AND su.name = ? ORDER BY so.name\n                                ", (schema,))
                table_fetch = cursor.fetchall()
                for name in table_fetch:
                    procNameList.append({'owner': name[0].strip()})
        except Exception as e:
            logger.info(str(e))
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
        trigText = []
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            procName = procName.split('.')
            owner = procName[0]
            pname = procName[1]
            cursor.execute("SELECT c.text FROM sysobjects o JOIN syscomments c ON o.id = c.id WHERE o.type = 'TR' AND user_name(o.uid) = ? AND o.name = ? ", (owner, pname))
            table_fetch = cursor.fetchall()
            for name in table_fetch:
                trigText.append(name[0])
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify({'trigText': trigText})

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
        except Exception as e:
            logger.info(str(e))
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
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('select user,passwd from CONN where dbname=:dbname', {'dbname': dbname})
            db_row = cursor.fetchone()
            sql_lines = ''
            if db_row:
                user = db_row[0]
                passwd = db_row[1]
                passwd = cipher.decrypt(passwd)
                dbname = dbname.split('@')
                db = dbname[0]
                server = dbname[1]
                ddlgen = os.path.join(ase_home, 'bin', 'ddlgen')
                result = subprocess.run([ddlgen, '-U', user, '-P', passwd, '-S', server, '-D', db, '-T', 'P', '-N', procName], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                stdout_text = result.stdout
                copy = False
                create_lines = []
                for line in result.stdout.splitlines():
                    if re.match('(?i)^create procedure', line.strip()):
                        copy = True
                    elif line.startswith('go'):
                        copy = False
                    if copy:
                        create_lines.append(line.strip())
                        sql_lines = '\n'.join(create_lines) + '\n'
        except Exception as e:
            logger.info(str(e))
        return jsonify({'procText': sql_lines})

class updateZoneDetails(Resource):

    def post(self):
        data = request.get_json(force=True)
        file_name = data['currentZone'] + '.txt'
        file_path = os.path.join('Zone', file_name)
        try:
            with open(file_path, 'w') as file:
                file.write(data['zoneFunctions'])
                return 'Success'
        except Exception as e:
            return str(e)    

class getZoneDetails(Resource):

    def post(self):
        data = request.get_json(force=True)
        file_name = data['currentZone'] + '.txt'
        directory_name = 'Zone'
        file_path = os.path.join(directory_name, file_name)
        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
                return file_content
        except FileNotFoundError:
            return 'No File'
        except Exception as e:
            return 'Error'

class fetchAutomateExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        try:
            excel_file_path = data['sourceDbname'] + '_' + data['schemaName'] + '.xlsx'
            if not os.path.exists(excel_file_path):
                empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
                empty_df.to_excel(excel_file_path, index=False)
            df = pd.read_excel(excel_file_path)
            result_dict = df.to_dict(orient='records')
            response = jsonify(result_dict)
        except FileNotFoundError:
            response = jsonify({'error': 'File not found'})
        return response

class fetchAutomateProcExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        try:
            excel_file_path = data['sourceDbname'] + '_proc.xlsx'
            if not os.path.exists(excel_file_path):
                empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
                empty_df.to_excel(excel_file_path, index=False)
            df = pd.read_excel(excel_file_path)
            result_dict = df.to_dict(orient='records')
            response = jsonify(result_dict)
        except FileNotFoundError:
            response = jsonify({'error': 'File not found'})
        return response

class updateExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_proc.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelTable(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_table' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelRole(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_role' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelConstraints(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_constraint' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelGrantConstraints(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_grant_constraint' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelIndexes(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_index' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelView(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_view' + '.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class updateExcelTrigger(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_' + data['schemaName'] + '_Trigger.xlsx'
        try:
            df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
        function_name_to_update = data['functionName']
        if function_name_to_update in df['Function'].values:
            df.loc[df['Function'] == function_name_to_update, 'Output'] = data['output']
        else:
            new_no_value = df['No'].max() + 1 if not df.empty else 1
            new_row = pd.DataFrame({'No': [new_no_value], 'Function': [function_name_to_update], 'Output': [data['output']]})
            df = pd.concat([df, new_row], ignore_index=True)
        try:
            df.to_excel(excel_file_path, index=False)
            return 'Success'
        except Exception as e:
            return f'Error: {str(e)}'

class automateProcess(Resource):

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
            sshTimeOut = 600
            for process in procNameList:
                newProcName = process['vname']
                newProcName = newProcName.split('.')
                owner = newProcName[0]
                pname = newProcName[1]
                cursor.execute("SELECT RTRIM(user_name(uid)) + '.' + name AS proc_full_name  FROM sysobjects WHERE type = 'P' AND user_name(uid) = ? ", (owner,))
                userID = cursor.fetchall()[0][0]
                cursor.execute("SELECT sc.text AS procText FROM sysobjects so JOIN syscomments sc ON so.id = sc.id WHERE so.type = 'P' AND user_name(so.uid) = ? AND so.name = ?", (owner, pname))
                procTextRow = cursor.fetchone()
                if procTextRow:
                    procText = procTextRow[0]
                else:
                    procText = ''
                dep_url = targetDep + '/updateAutomateProcess'
                headers = {'Content-Type': 'application/json'}
                mgrPayload = {'dbName': targetDbname, 'viewProc': procText, 'processName': process['vname']}
                resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                response_data = resp.json()
                if response_data.get('message') == 'Created':
                    result = 'Created'
                elif response_data.get('message') == 'Already Exist':
                    result = 'Already Exist'
                else:
                    result = 'Error'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                excel_file = sourceDbname + '_' + data['schemaName'] + '.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i += 1
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class fetchAutomateRoleExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        try:
            excel_file_path = data['sourceDbname'] + '_role.xlsx'
            if not os.path.exists(excel_file_path):
                empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
                empty_df.to_excel(excel_file_path, index=False)
            df = pd.read_excel(excel_file_path)
            result_dict = df.to_dict(orient='records')
            response = jsonify(result_dict)
        except FileNotFoundError:
            response = jsonify({'error': 'File not found'})
        return response

class fetchAutomateTableExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_table.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class fetchAutomateConstraintsExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_constraint.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class fetchAutomateGrantConstraintsExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_grant_constraint.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class fetchAutomateIndexesExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_index.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)


class fetchAutomateViewExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_view.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class fetchAutomateTriggerExcel(Resource):

    def post(self):
        data = request.get_json(force=True)
        excel_file_path = data['sourceDbname'] + '_' + data['schemaName'] + '_Trigger.xlsx'
        if not os.path.exists(excel_file_path):
            empty_df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            empty_df.to_excel(excel_file_path, index=False)
        df = pd.read_excel(excel_file_path)
        result_dict = df.to_dict(orient='records')
        return jsonify(result_dict)

class automateOracleView(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for process in procNameList:
                viewName = process['vname']
                src_url = sourceDep + '/getviewtext'
                headers = {'Content-Type': 'application/json'}
                payload = {'dbname': sourceDbname, 'viewName': viewName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('viewText', '')
                ddl_text = '\n'.join(ddlLines)
                convert_url = sourceDep + '/viewDDLGenAi'
                convertPayload = {'viewProc': ddl_text, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'viewName': viewName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                targ_url = targetDep + '/pgCreateView'
                savePayload = {'dbName': targetDbname, 'viewText': convertedLines}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_view.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [viewName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': viewName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

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
                cursor.execute("SELECT rtrim(user_name(uid)) + '.' + name AS view_name  FROM sysobjects  WHERE type = 'V' AND user_name(uid) = ? AND name NOT LIKE 'sys%'", (owner,))
                userID = cursor.fetchall()[0][0]
                cursor.execute("SELECT sc.text AS viewtext FROM sysobjects so JOIN syscomments sc ON so.id = sc.id WHERE so.type = 'V' AND user_name(so.uid) = ? AND so.name = ?", (owner, pname))
                procTextRow = cursor.fetchone()
                if procTextRow:
                    procText = procTextRow[0]
                else:
                    procText = ''
                dep_url = targetDep + '/updateAutomateView'
                headers = {'Content-Type': 'application/json'}
                mgrPayload = {'dbName': targetDbname, 'viewProc': procText}
                resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                response_data = resp.json()
                if response_data.get('message') == 'Created':
                    result = 'Created'
                elif response_data.get('message') == 'Already Exist':
                    result = 'Already Exist'
                else:
                    result = 'Error'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                excel_file = sourceDbname + '_view.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i += 1
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class automateOracleProc(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for process in procNameList:
                procName = process['vname']
                src_url = sourceDep + '/getproctext'
                headers = {'Content-Type': 'application/json'}
                payload = {'dbname': sourceDbname, 'procName': procName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('procText', '')
                ddl_text = '\n'.join(ddlLines)
                convert_url = sourceDep + '/procDDLGenAi'
                convertPayload = {'viewProc': ddl_text, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket':s3Bucket, 'procName': procName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify, timeout=None)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                targ_url = targetDep + '/pgCreateProcedure'
                savePayload = {'dbName': targetDbname, 'procText': convertedLines}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_proc.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [procName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': procName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class automateOracleTrig(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        procNameList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for process in procNameList:
                procName = process['vname']
                src_url = sourceDep + '/gettrigtext'
                headers = {'Content-Type': 'application/json'}
                payload = {'dbname': sourceDbname, 'procName': procName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('trigText', '')
                ddl_text = '\n'.join(ddlLines)
                convert_url = sourceDep + '/trigDDLGenAi'
                convertPayload = {'viewProc': ddl_text, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'trigName': procName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify, timeout=None)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                targ_url = targetDep + '/pgCreateTrigger'
                savePayload = {'dbName': targetDbname, 'procText': convertedLines}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_Trigger.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [procName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': procName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
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
                cursor.execute("SELECT c.text FROM sysobjects o JOIN syscomments c ON o.id = c.id WHERE o.type = 'TR' AND user_name(o.uid) = ? AND o.name = ? ", (owner, pname))
                procTextRow = cursor.fetchone()
                if procTextRow:
                    procText = procTextRow[0]
                else:
                    procText = ''
                dep_url = targetDep + '/updateAutomateTrigger'
                headers = {'Content-Type': 'application/json'}
                mgrPayload = {'dbName': targetDbname, 'viewProc': procText, 'processName': process['vname']}
                resp = requests.post(dep_url, json=mgrPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                response_data = resp.json()
                if response_data.get('message') == 'Created':
                    result = 'Created'
                elif response_data.get('message') == 'Already Exist':
                    result = 'Already Exist'
                else:
                    result = 'Error'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [process['vname']], 'Output': [result]})], ignore_index=True)
                excel_file = sourceDbname + '_' + data['schemaName'] + '_Trigger.xlsx'
                df.to_excel(excel_file, index=False)
                outputDict.append({'process': process['vname'], 'result': result})
                i += 1
        except Exception as e:
            logger.info(str(e))
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
                cursor.execute("SELECT rtrim(user_name(uid)) + '.' + name AS view_name  FROM sysobjects  WHERE type = 'V' AND user_name(uid) = ? AND name NOT LIKE 'sys%'", (schema,))
                table_fetch = cursor.fetchall()
                for name in table_fetch:
                    viewNameList.append({'owner': name[0].strip()})
        except Exception as e:
            logger.info(str(e))
            return {'error': str(e)}
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
            cursor.execute("SELECT sc.text AS viewtext FROM sysobjects so JOIN syscomments sc ON so.id = sc.id WHERE so.type = 'V' AND user_name(so.uid) = ? AND so.name = ?", (owner, vname))
            table_fetch = cursor.fetchall()
            viewText.extend([row[0] for row in table_fetch])
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return jsonify({'viewText': viewText})

class getUsersAndRolesFromDB(Resource):
    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']        

        try:
            val = selectConn(dbname)
            conn = val[0]
            cursor = conn.cursor()
            output_list = []
            #cursor.execute("SELECT name FROM sysusers WHERE uid > 0 AND suid IS NOT NULL AND name NOT IN ('dbo', 'guest', 'public')")
            #users_fetch = cursor.fetchall()                  
            #for row in users_fetch:
                #output_list.append({"name": row[0], "type": "user"}) 
            
            #existing_names = {entry["name"] for entry in output_list}
            cursor.execute("USE master")
            cursor.execute("SELECT name FROM syssrvroles where status=0")
            roles_fetch = cursor.fetchall()
            for row in roles_fetch:
                output_list.append({"name": row[0], "type": "role"}) 
         
        except Exception as e:
            output_list.append(str(e))
        finally:
            if conn:
               cursor.close()
               conn.close()

        return jsonify({'user_role_list': output_list})

def getIndexes(sql):
    pattern = re.compile("-- DDL for Index '.*?'\\s*.*?(create\\s+(unique\\s+)?(clustered|nonclustered)?\\s*index\\s+\\w+.*?on\\s+[\\w\\.]+\\([^)]+\\)\\s*\\n.*?with\\s+.*?)(?:\\s*go)", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(sql)
    return [match[0].strip() for match in matches]

class getDDLFromTable(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        tableName = data['tableName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('select user,passwd from CONN where dbname=:dbname', {'dbname': dbname})
        db_row = cursor.fetchone()
        sql_lines = ''
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            passwd = cipher.decrypt(passwd)
            dbname = dbname.split('@')
            db = dbname[0]
            server = dbname[1]
            ddlgen = os.path.join(ase_home, 'bin', 'ddlgen')
            try:
                result = subprocess.run([ddlgen, '-U', user, '-P', passwd, '-S', server, '-D', db, '-T', 'U', '-N', tableName], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                stdout_text = result.stdout
                index_ddl_blocks = getIndexes(stdout_text)
                if index_ddl_blocks:
                    os.makedirs('indexes', exist_ok=True)
                    file_path = os.path.join('indexes', f'{tableName}_index.txt')
                    with open(file_path, 'w') as file:
                        for ddl in index_ddl_blocks:
                            file.write(ddl + '\n\n')
                grant_lines = []
                for line in stdout_text.splitlines():
                    if line.strip().lower().startswith('grant'):
                        grant_lines.append(line.strip())
                if grant_lines:
                    folder_path = 'Grant_constraints'
                    os.makedirs(folder_path, exist_ok=True)
                    file_path = os.path.join(folder_path, f'{tableName}.txt')
                    with open(file_path, 'w') as file:
                        for block in grant_lines:
                            cleaned_string = block.replace('\n', ' ').strip()
                            file.write(cleaned_string + '\n\n')
                ddl_blocks = re.findall('(alter\\s+table.*?)(?=^\\s*go\\b)', stdout_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
                if ddl_blocks:
                    folder_path = 'Foreign_key_constraints'
                    os.makedirs(folder_path, exist_ok=True)
                    file_path = os.path.join(folder_path, f'{tableName}.txt')
                    with open(file_path, 'w') as file:
                        for block in ddl_blocks:
                            cleaned_string = block.replace('\n', ' ').strip()
                            file.write(cleaned_string + '\n\n')
                copy = False
                create_lines = []
                for line in result.stdout.splitlines():
                    if line.startswith('create table'):
                        copy = True
                    elif line.startswith('go'):
                        copy = False
                    if copy:
                        create_lines.append(line.strip())
                        sql_lines = '\n'.join(create_lines) + '\n'
            except Exception as e:
                sql_lines = str(e)
            finally:
                if conn:
                    cursor.close()
                    conn.close()
        return jsonify({'ddl': sql_lines})

class tableDDLGenAi(Resource):

    def post(self):
        data = request.get_json(force=True)
        tableDDL = data['tableDDL']
        sourceDep = data['sourceDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")
        tableName = data['tableName']

        log_file = os.path.join(agent_home,'convert_output.txt')
        if os.path.exists(log_file):
            os.remove(log_file)


        (anon_sql, map_data) = anonymize_sql(tableDDL)
        oracle_converted_sql = convertTableGenAi(anon_sql)
        createDDLStmt = deanonymize_sql(oracle_converted_sql, map_data)

        if s3BucketChecked:   
            folder_path = os.path.join(agent_home, 'Converted', 'table')
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{tableName}.txt"
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as file:
                file.write(createDDLStmt)
            s3_key = f'Converted/table/{file_name}'
            src_url = sourceDep + '/uploadS3Bucket'
            headers = {'Content-Type': 'application/json'}
            payload = {'bucket_name': s3Bucket, 'file_name': file_path, 's3_key': s3_key}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()
            
        return jsonify({'converted_lines': createDDLStmt})

class automateTable(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        tableNameList = data['procNameList']
        targetDep = data['targetDep']     
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for tableName in tableNameList:
                tableName = tableName['tabname']
                src_url = sourceDep + '/getddlfromtable'
                headers = {'Content-Type': 'application/json'}
                payload = {'dbname': sourceDbname, 'tableName': tableName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('ddl', '')
                convert_url = sourceDep + '/tableDDLGenAi'
                convertPayload = {'tableDDL': ddlLines, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'tableName': tableName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                targ_url = targetDep + '/saveddl'
                savePayload = {'dbname': targetDbname, 'tableDDLConvertedText': convertedLines}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Table Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg

                excel_file = sourceDbname + '_table.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [tableName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'tableName': tableName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class automateRole(Resource):
    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        targetDep = data['targetDep']

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            roleNameList = []
            src_url = sourceDep + '/getUsersAndRolesFromDB'
            headers = {'Content-Type': 'application/json'}
            payload = {'dbname': sourceDbname}
            resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            result = resp.json()
            roleNameList = result.get('user_role_list', '')
            
            for roleName in roleNameList:
                roleName = roleName['name']                
                targ_url = targetDep + '/createRole'
                savePayload = {'dbName': targetDbname, 'roleName': roleName}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'conflicts with another user or role' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                
                excel_file = sourceDbname + '_role.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [roleName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'roles': roleName, 'result': save_result})
                i += 1
                
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict



class automateConstraints(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        constraintsList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")         

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for constraint in constraintsList:
                constraintName = constraint['tabname']
                src_url = sourceDep + '/getKeyConstraintsLines'
                headers = {'Content-Type': 'application/json'}
                payload = {'tableName': constraintName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('constraintText', '')
                convert_url = sourceDep + '/constraintDDLGenAi'
                
                convertPayload = {'constraintDDL': ddlLines, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'constraintName': constraintName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                alter_statements = [line for line in convertedLines if line.strip().upper().startswith('ALTER TABLE')]
                joined_alter_statements = ',\n'.join(alter_statements)
                targ_url = targetDep + '/saveConstraints'
                savePayload = {'dbname': targetDbname, 'constraintDDLConvertedText': joined_alter_statements}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already exists in the table' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_constraint.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [constraintName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'constraintName': constraintName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

class automateGrantConstraints(Resource):

    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        constraintsList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for constraint in constraintsList:
                constraintName = constraint['tabname']
                src_url = sourceDep + '/getGrantKeyConstraintsLines'
                headers = {'Content-Type': 'application/json'}
                payload = {'tableName': constraintName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('constraintText', '')
                ddlLines = [line.strip() for line in ddlLines if line.strip() != '']
                convert_url = sourceDep + '/grantKeyDDLGenAi'
                convertPayload = {'constraintDDL': ddlLines, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'grantName': constraintName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                targ_url = targetDep + '/saveGrants'
                savePayload = {'dbname': targetDbname, 'constraintDDLConvertedText': convertedLines}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_grant_constraint.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [constraintName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'constraintName': constraintName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict

def split_index_blocks(lines):
    index_blocks = []
    buffer = []

    for line in lines:
        if re.match(r'^create\s+unique\s+(clustered|nonclustered)?\s*index', line.strip(), re.IGNORECASE):
            if buffer:
                index_blocks.append(''.join(buffer).strip())
                buffer = []
        buffer.append(line)

    if buffer:
        index_blocks.append(''.join(buffer).strip())

    return index_blocks

class automateIndexes(Resource):
    def post(self):
        data = request.get_json(force=True)
        sourceDep = data['sourceDep']
        sourceDbname = data['sourceDbname']
        targetDbname = data['targetDbname']
        constraintsList = data['procNameList']
        targetDep = data['targetDep']
        s3BucketChecked = data.get('s3BucketChecked', False)
        s3Bucket = data.get('s3Bucket', "")

        outputDict = []
        try:
            val = selectConn(sourceDbname)
            con = val[0]
            cursor = con.cursor()
            df = pd.DataFrame(columns=['No', 'Function', 'Output'])
            i = 1
            for constraint in constraintsList:
                constraintName = constraint['tabname']
                src_url = sourceDep + '/getIndexConstraintsLines'
                headers = {'Content-Type': 'application/json'}
                payload = {'tableName': constraintName}
                resp = requests.post(src_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                result = resp.json()
                ddlLines = result.get('constraintText', '')
                ddlLines = [line.strip() for line in ddlLines if line.strip() != '']
                ddlLines = split_index_blocks(ddlLines)                                                
                convert_url = sourceDep + '/indexDDLGenAi'
                convertPayload = {'constraintDDL': ddlLines, 'sourceDep': sourceDep, 's3BucketChecked': s3BucketChecked, 's3Bucket': s3Bucket, 'indexName': constraintName}
                cpnvertResp = requests.post(convert_url, json=convertPayload, headers=headers, verify=ssl_verify)
                convertResult = cpnvertResp.json()
                convertedLines = convertResult.get('converted_lines', '')
                cleaned_list = [re.sub(r',\s*$', '', item.strip()) for item in convertedLines]            
                targ_url = targetDep + '/saveIndexes'
                savePayload = {'dbname': targetDbname, 'constraintDDLConvertedText': cleaned_list}
                saveResp = requests.post(targ_url, json=savePayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                resultData = saveResp.json()
                resultMsg = resultData.get('msg', '')
                if 'Created' in resultMsg:
                    save_result = 'Created'
                elif 'already used by an existing' in resultMsg:
                    save_result = 'Already Exist'
                elif 'Network connection problem' in resultMsg:
                    save_result = 'Connection problem'
                else:
                    save_result = resultMsg
                excel_file = sourceDbname + '_index.xlsx'
                df = pd.concat([df, pd.DataFrame({'No': [i], 'Function': [constraintName], 'Output': [save_result]})], ignore_index=True)
                df.to_excel(excel_file, index=False)
                outputDict.append({'constraintName': constraintName, 'result': save_result})
                i += 1
                time.sleep(random.randint(5, 10))
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return outputDict


class getTableDetFromSchema(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        tableMetadataDict = []
        unSupportedTables = []
        try:
            val = selectConn(dbname)
            con = val[0]
            cursor = con.cursor()
            for schema in schemaList:
                cursor.execute("SELECT user_name(uid) AS owner, name AS table_name FROM sysobjects WHERE type = 'U' AND user_name(uid) = ?", (schema,))
                table_fetch = cursor.fetchall()
                for row in table_fetch:
                    (owner, table_name) = row
                    unsupported = False
                    query_columns = f"\n                                    SELECT '{table_name}' AS tname, c.name AS cname, t.name AS coltype, c.length AS width, c.prec AS syslength, \n                                    CASE WHEN c.status & 8 = 8 THEN 'NO' ELSE 'YES' END AS NN,c.cdefault AS default_value, \n                                    '' AS remarks FROM syscolumns c JOIN systypes t ON c.usertype = t.usertype JOIN sysobjects o ON c.id = o.id \n                                    WHERE o.name = ? AND o.type = 'U' ORDER BY c.colid"
                    cursor.execute(query_columns, (table_name,))
                    columns_data = cursor.fetchall()
                    columns_names = [col[0] for col in cursor.description]
                    columns_list = [dict(zip(columns_names, row)) for row in columns_data]
                    cursor.execute(f"sp_columns '{table_name}'")
                    columns_list_null = cursor.fetchall()
                    nullable_map = {}
                    scale_map = {}
                    remarks_map = {}
                    for row in columns_list_null:
                        col_name = row[3]
                        scale = row[7]
                        nullable_flag = row[10]
                        remarks = row[11]
                        scale_map[col_name] = scale
                        nullable_map[col_name] = 'YES' if nullable_flag == 1 else 'NO'
                    pk_columns = set()
                    try:
                        cursor.execute(f"sp_helpconstraint '{table_name}', 'detail'")
                        pk_info_rows = cursor.fetchall()
                        for pk_row in pk_info_rows:
                            if 'PRIMARY KEY INDEX' in pk_row[2].upper():
                                match = re.search('\\((.*?)\\)', pk_row[2])
                                if match:
                                    keys_str = match.group(1)
                                    pk_columns.update([k.strip() for k in keys_str.split(',')])
                    except Exception as e:
                        logger.warning(f'Could not fetch primary key info for {table_name}: {str(e)}')
                    for col in columns_list:
                        cname = col['cname']
                        col['NN'] = nullable_map.get(cname, 'YES')
                        col['scale'] = scale_map.get(cname)
                        col['remarks'] = remarks_map.get(cname, 'None')
                        if cname in pk_columns:
                            col['in_primary_key'] = 'YES'
                        else:
                            col['in_primary_key'] = 'NO'
                    if unsupported:
                        unSupportedTables.append(columns_list)
                    else:
                        json_data = json.dumps(columns_list)
                        tableMetadataDict.append(columns_list)
        except Exception as e:
            logger.info(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tableMetadataDict, unSupportedTables]

class getExtTrailName(Resource):

    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        Trail_Data = []
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('info ' + extname + ' , showch' + '\n')
        (infoExtTrail, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'infoextnametrail.out'), mode='w') as outfile:
            outfile.write(infoExtTrail)
        with open(os.path.join(agent_home, 'infoextnametrail.out'), mode='r') as infile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('add ' + trailtype + ' ' + trailname + ', Extract ' + extname + ',megabytes ' + trailsize + '\n')
        (delexttrail, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'addexttrail.out'), mode='w') as outfile:
            outfile.write(delexttrail)
        with open(os.path.join(agent_home, 'addexttrail.out'), mode='r') as infile:
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
            ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('count detail ' + trail + '\n')
            (TranNext, stderr) = ssh.communicate(timeout=sshTimeOut)
            with open(os.path.join(agent_home, 'Lodump_CountDetail.out'), mode='w') as outfile2:
                outfile2.write(TranNext)
            with open(os.path.join(agent_home, 'Lodump_CountDetail.out'), mode='r') as infile:
                copy = False
                Count_Detail = []
                for line in infile:
                    line1 = line.split()
                    if len(line1) > 0:
                        if line1[0].startswith('Logdump'):
                            if line1[2].startswith('>'):
                                Count_Detail.append(line1[1])
            with open(os.path.join(agent_home, 'Lodump_CountDetail.out'), mode='r') as infile, open(os.path.join(agent_home, 'Lodump_CountDetail_Iter1.txt'), mode='w') as outfile:
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
            with open(os.path.join(agent_home, 'Lodump_CountDetail_Iter1.txt'), mode='r') as infile:
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
                                        elif tabname in Count_Detail_Ind.keys():
                                            Count_Detail_Ind[tabname] = int(Count_Detail_Ind[tabname]) + int(line1[1])
                                        else:
                                            Count_Detail_Ind[tabname] = line1[1]
        OPlaceDebug(['Lodump_CountDetail.out', 'Lodump_CountDetail_Iter1.txt'])
        return [Count_Detail_Ind]

def hexConvert(filename):
    with open(os.path.join(agent_home, filename)) as infile:
        str = ''
        for line in infile:
            for word in line.split():
                str = str + word
    strAscii = binascii.unhexlify(str).decode('utf8', errors='ignore')
    return strAscii

class ggLogDump(Resource):

    def post(self):
        data = request.get_json(force=True)
        trailfile = data['trailfile']
        trailfile = trailfile.lstrip('["').rstrip('"]')
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + '\n')
        ssh.stdin.write('fileheader detail' + '\n')
        ssh.stdin.write('n' + '\n')
        (res, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'logdump.out'), mode='w') as outfile1:
            outfile1.write(res)
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump2.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump3.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump4.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump5.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump6.out'), mode='w', encoding='utf-8') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump7.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump8.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump9.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump10.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump11.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'logdump.out')) as infile, open(os.path.join(agent_home, 'ldump12.out'), mode='w') as outfile:
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
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + '\n')
        ssh.stdin.write('count detail' + '\n')
        (countRes, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'countdetail.out'), mode='w') as outfile2:
            outfile2.write(countRes)
        with open(os.path.join(agent_home, 'countdetail.out')) as infile:
            copy = False
            Count_Detail = []
            for line in infile:
                line1 = line.split()
                if len(line1) > 0:
                    if line1[0].startswith('Logdump'):
                        if line1[2].startswith('>'):
                            Count_Detail.append(line1[1])
        with open(os.path.join(agent_home, 'countdetail.out')) as infile, open(os.path.join(agent_home, 'countiter1.out'), mode='w') as outfile:
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
        with open(os.path.join(agent_home, 'countiter1.out')) as infile:
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
                                    Count_Detail_Ind.append({'tab_name': tabname, 'tran_type': line1[0], 'tran_det': line1[1]})
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=5)
        ssh.stdin.write('open ' + trailfile + '\n')
        ssh.stdin.write('n' + '\n')
        ssh.stdin.write('n' + '\n')
        (trailData, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'trandet.out'), mode='w') as outfile2:
            outfile2.write(trailData)
        with open(os.path.join(agent_home, 'trandet.out')) as infile:
            copy = False
            parse16 = ''
            for line in infile:
                if 'RBA' in line:
                    parse16 = line.split()[6]
        OPlaceDebug(['ldump2.out', 'ldump3.out', 'ldump4.out', 'ldump5.out', 'ldump6.out', 'ldump7.out', 'ldump8.out', 'ldump9.out', 'ldump10.out', 'ldump11.out', 'ldump12.out', 'countdetail.out', 'countiter1.out', 'trandet.out'])
        return [parse3, parse4, parse5, parse6, parse7, parse8, parse9, parse10, parse11, parse12, parse13, Count_Detail_Ind, parse16]

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
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + '\n')
        ssh.stdin.write('ghdr on;detail data;usertoken detail;ggstoken detail;' + '\n')
        for filt in filterlist:
            ssh.stdin.write(filt + '\n')
        ssh.stdin.write(filtmatch + '\n')
        ssh.stdin.write('pos ' + str(rba) + '\n')
        ssh.stdin.write('n' + '\n')
        ssh.stdin.write('n' + '\n')
        try:
            (TranNext, stderr) = ssh.communicate(timeout=sshTimeOut)
        except TimeoutExpired:
            ssh.kill()
        with open(os.path.join(agent_home, 'trannext.out'), mode='w') as outfile:
            outfile.write(TranNext)
        with open(os.path.join(agent_home, 'trannext.out')) as infile:
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
        ssh = subprocess.Popen([logdump_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('open ' + trailfile + '\n')
        ssh.stdin.write('ghdr on;detail data;usertoken detail;ggstoken detail;' + '\n')
        ssh.stdin.write('pos ' + str(rba) + '\n')
        ssh.stdin.write('sfh prev' + '\n')
        ssh.stdin.write('sfh prev' + '\n')
        try:
            (TranPrev, stderr) = ssh.communicate(timeout=sshTimeOut)
        except TimeoutExpired:
            ssh.kill()
        with open(os.path.join(agent_home, 'tranprev.out'), mode='w') as outfile:
            outfile.write(TranPrev)
        with open(os.path.join(agent_home, 'tranprev.out')) as infile:
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
            if filename.startswith('p') and filename.endswith('.zip'):
                softFiles.append({'filename': filename, 'filetype': 'patch'})
            elif 'fbo' in filename and filename.endswith('.zip'):
                softFiles.append({'filename': filename, 'filetype': 'software'})
            elif filename.startswith('V') and filename.endswith('.zip'):
                softFiles.append({'filename': filename, 'filetype': 'software'})
        return [softFiles]

class ViewRunInsFile(Resource):

    def post(self):
        data = request.get_json(force=True)
        filename = data['filename']
        filename = filename.lstrip('"[').rstrip(']"')
        path_to_zip_file = os.path.join(image_uploads, filename)
        RunIns = []
        if not os.path.exists(gg_home):
            os.makedirs(gg_home)
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
                if not os.path.exists(directory_to_extract_to):
                    os.makedirs(directory_to_extract_to)
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
                    with open(os.path.join(agent_base, 'oraInst.loc'), 'w') as outfile:
                        inv_loc = os.path.join(agent_base, 'oraInventory')
                        if not os.path.exists(os.path.join(agent_base, 'oraInventory')):
                            os.makedirs(os.path.join(agent_base, 'oraInventory'))
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
                    with open(os.path.join(agent_base, 'oraInst.loc'), 'w') as infile:
                        inv_loc = os.path.join(agent_base, 'oraInventory')
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
                oraini_file = oraini_file.replace('DEFAULT_HOME_NAME=OraHome', 'DEFAULT_HOME_NAME=' + 'OGG_' + ggBaseVer + '_' + ORA_Version + '_Home')
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
                ssh = subprocess.Popen([runInstaller, '-silent', '-showProgress', '-responseFile', oneplace_RspFile], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            else:
                ssh = subprocess.Popen([runInstaller, '-silent', '-showProgress', '-responseFile', oneplace_RspFile, '-invPtrLoc', os.path.join(agent_base, 'oraInst.loc')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            (InstallErr, stderr) = ssh.communicate()
            RunIns.append(InstallErr)
            shutil.copy(dest_file, oraparam_ini)
            if rac_check == 'Y':
                for name in copy_to_nodes:
                    RunIns.append('Connecting to ' + name + ' in order to setup software...')
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(hostname=name)
                    scp = SCPClient(ssh_client.get_transport())
                    rmdir_OH = 'rmdir ' + gg_home
                    (stdin, stdout, stderr) = ssh_client.exec_command(rmdir_OH)
                    RunIns.append('Copying files to remote node ' + name + ' ...')
                    scp.put(gg_home, recursive=True, remote_path=gg_home)
                    RunIns.append('Copy to remote node ' + name + ' completed ...')
                    runins_home = os.path.join(gg_home, 'oui', 'bin', 'runInstaller')
                    RunIns.append('Starting to attach Goldengate Home on  remote node ' + name + ' ...')
                    add_OH = runins_home + ' -silent -attachHome ORACLE_HOME=' + gg_home + ' ORACLE_HOME_NAME=' + 'OGG_' + ggBaseVer + '_' + ORA_Version + '_Home'
                    (stdin, stdout, stderr) = ssh_client.exec_command(add_OH)
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
                subprocess.run(['unzip', path_to_zip_file, '-d', gg_home])
                RunIns.append(filename + ' Processed Sucessfully\n\n')
                ssh = subprocess.Popen([opatch_dir, 'version'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                (opatchVersion, stderr) = ssh.communicate()
                RunIns.append(opatchVersion)
                RunIns.append(stderr)
            else:
                extracted_files = []
                path_to_zip_file = os.path.join(image_uploads, filename)
                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    tar_name = None
                    for name in zip_ref.namelist():
                        if name.endswith('.tar'):
                            tar_name = name
                            break
                        if tar_name is None:
                            raise FileNotFoundError('No .tar file found inside the zip archive.')
                    temp_tar_path = os.path.join(gg_home, os.path.basename(tar_name))
                    with open(temp_tar_path, 'wb') as f:
                        f.write(zip_ref.read(tar_name))
                with tarfile.open(temp_tar_path, 'r') as tar_ref:
                    members = tar_ref.getmembers()
                    tar_ref.extractall(path=gg_home)
                    extracted_files = [member.name for member in members]
                RunIns.append(f'Extracted {len(extracted_files)} items from {tar_name} to {gg_home}')
                for f in extracted_files:
                    RunIns.append(f' - {f}')
        return [RunIns]

class ggTgtDiag(Resource):

    def get(self):
        RepTrailSet = {}
        proc = subprocess.run([ggsci_bin], input='info replicat * , showch\n', text=True, capture_output=True)
        InfoRep = proc.stdout
        with open(os.path.join(agent_home, 'inforep.out'), mode='w') as outfile:
            outfile.write(InfoRep)
        with open(os.path.join(agent_home, 'inforep.out')) as infile:
            for line in infile:
                if re.search('REPLICAT', line, re.IGNORECASE):
                    RepName = line.split()[1] + ' ' + agent_dep
                elif 'Extract Trail' in line:
                    RepTrailSet[RepName] = line.split(':', 1)[-1].strip()
        return [RepTrailSet]

class ggInfoDiagram(Resource):

    def get(self):
        ExtTrailSetTmp = {}
        ExtTrailSet = {}
        PmpTrailSet = {}
        PmpRmtTrailSet = {}
        RepTrailSet = {}
        InfoExt = subprocess.getoutput("echo -e 'info exttrail'|" + ggsci_bin)
        InfoPmp = subprocess.getoutput("echo -e 'info extract *'|" + ggsci_bin)
        with open(os.path.join(agent_home, 'infoext.out'), mode='w') as outfile:
            outfile.write(InfoExt)
        with open(os.path.join(agent_home, 'infopmp.out'), mode='w') as outfile:
            outfile.write(InfoPmp)
        with open(os.path.join(agent_home, 'infopmp.out')) as infile:
            for line in infile:
                if re.search('EXTRACT', line, re.IGNORECASE):
                    PmpName = line.split()[1] + ' ' + agent_dep
                elif 'VAM' in line:
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
        with open(os.path.join(agent_home, 'infoext.out')) as infile:
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip() + ' ' + agent_dep
                    ExtTrailSetTmp[ExtName] = TrailName
        for (key, value) in ExtTrailSetTmp.items():
            if key not in PmpTrailSet:
                ExtTrailSet[key] = value
            else:
                PmpRmtTrailSet[key] = value
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        try:
            DEP = "select distinct dep_url from onepconn where dep='ORACLE'"
            DEP_fetch = pd.read_sql_query(DEP, conn)
            for ext in DEP_fetch.iterrows():
                tgt_api_url = ext[1]['dep_url']
            tgtDiag = tgt_api_url + '/ggtgtdiag'
            tgtDiag_req = requests.get(tgtDiag)
            if len(tgtDiag_req.json()) > 0:
                RepTrailSet = tgtDiag_req.json()[0]
        except Exception as e:
            logger.error(str(e))
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
        return [ProcessSet2, df.to_dict('records'), Ext_df.to_dict('records'), Pmp_df.to_dict('records'), PmpRmt_df.to_dict('records'), Rep_df.to_dict('records')]

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
        ggsci_input = f'info extract {extname},tasks\n'
        proc = subprocess.run([ggsci_bin], input=ggsci_input, text=True, capture_output=True)
        InfoExt = proc.stdout
        output_path = os.path.join(agent_home, 'infoext.out')
        with open(output_path, mode='w') as outfile2:
            outfile2.write(InfoExt)
        with open(output_path, mode='r') as infile:
            Ext_Data = []
            for line in infile:
                if re.match('EXTRACT', line, re.IGNORECASE):
                    line = line.split()
                    Ext_Data.append({'extname': line[1], 'extstat': line[-1]})
        return [Ext_Data]

class ggInfoRep(Resource):

    def post(self):
        data = request.get_json(force=True)
        repname = data['repname']
        proc = subprocess.run([ggsci_bin], input=f'info replicat {repname}\n', text=True, capture_output=True)
        InfoRep = proc.stdout
        info_path = os.path.join(agent_home, 'inforep.out')
        with open(info_path, mode='w') as outfile2:
            outfile2.write(InfoRep)
        with open(info_path, mode='r') as infile:
            Rep_Data = []
            for line in infile:
                if re.match('REPLICAT', line, re.IGNORECASE):
                    line = line.split()
                    Rep_Data.append({'repname': line[1], 'repstat': line[-1]})
        return [Rep_Data]

class ggAddCredStore(Resource):

    def get(self):
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('create subdirs' + '\n')
        ssh.stdin.write('add credentialstore' + '\n')
        CredStore_Out = []
        (CredErr, stderr) = ssh.communicate()
        CredStore_Out.append(CredErr)
        if os.path.exists('/home/oracle/1pmgr.prm'):
            shutil.copy('/home/oracle/1pmgr.prm', os.path.join(gg_home, 'dirprm', 'mgr.prm'))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('start mgr' + '\n')
            (CredErr, stderr) = ssh.communicate()
            CredStore_Out.append(CredErr)
        ssh.kill()
        ssh.stdin.close()
        with open(os.path.join(agent_home, 'CredStore_Out.lst'), 'w') as TestDBLoginFileIn:
            for listline in CredStore_Out:
                TestDBLoginFileIn.write(listline)
        with open(os.path.join(agent_home, 'CredStore_Out.lst'), 'r') as TestDBLoginFile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('open wallet' + '\n')
        ssh.stdin.write('info masterkey' + '\n')
        Wallet_Out = []
        (WalletErr, stderr) = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with open(os.path.join(agent_home, 'infomasterkey.out'), mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with open(os.path.join(agent_home, 'infomasterkey.out')) as infile:
            MasterKey = {}
            for line in infile:
                if 'Name' in line or 'name' in line:
                    KeyName = line.split(':')[1].strip()
                elif re.match('^\\d+.*$', line):
                    line1 = line.split()
                    MasterKey.setdefault(KeyName, []).append({'Version': line1[0], 'Created': line1[1], 'Status': line1[2]})
        return [MasterKey]

    def post(self):
        data = request.get_json(force=True)
        menuAction = data['menuAction']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        if os.path.exists(os.path.join(gg_home, 'dirwlt')):
            shutil.rmtree(os.path.join(gg_home, 'dirwlt'))
            os.makedirs(os.path.join(gg_home, 'dirwlt'))
        ssh.stdin.write('create wallet' + '\n')
        ssh.stdin.write('open wallet' + '\n')
        ssh.stdin.write('add masterkey' + '\n')
        Wallet_Out = []
        (WalletErr, stderr) = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with open(agent_home + '/createmasterkey.out', mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with open(agent_home + '/createmasterkey.out', mode='r') as infile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        Wallet_Out = []
        version = 0
        if menuAction == 'info':
            version = data['version']
            ssh.stdin.write('open wallet' + '\n')
            ssh.stdin.write('info masterkey version ' + version + '\n')
        elif menuAction == 'renew':
            ssh.stdin.write('open wallet' + '\n')
            ssh.stdin.write('renew masterkey' + '\n')
        elif menuAction == 'delete':
            version = data['version']
            ssh.stdin.write('open wallet' + '\n')
            ssh.stdin.write('delete masterkey version ' + version + '\n')
        elif menuAction == 'purge':
            ssh.stdin.write('purge wallet' + '\n')
        elif menuAction == 'deploy':
            dep_url = data['dep_url']
            dep_url = dep_url + '/rhpwallet'
            walletfile = os.path.join(gg_home, 'dirwlt', 'cwallet.sso')
            with open(walletfile, 'rb') as payload:
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                files = {'file': payload}
                r = requests.post(dep_url, files=files, verify=ssl_verify)
                WalletErr = r.json()[0]
                Wallet_Out.append(WalletErr)
        (WalletErr, stderr) = ssh.communicate()
        Wallet_Out.append(WalletErr)
        ssh.kill()
        ssh.stdin.close()
        with open(os.path.join(agent_home, 'ActionMasterkey.out'), mode='w') as outfile:
            for listline in Wallet_Out:
                outfile.write(listline)
        with open(os.path.join(agent_home, 'ActionMasterkey.out'), mode='r') as infile:
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
            proc = subprocess.run([ggsci_bin], input='info credentialstore\n', text=True, capture_output=True)
            InfoCred = proc.stdout
            output_path = os.path.join(agent_home, 'checkcreddom.out')
            with open(output_path, mode='w') as outfile:
                outfile.write(InfoCred)
            with open(output_path, mode='r') as infile:
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
        if not os.path.exists(ggsci_bin):
            return ({'error': 'ggsci binary not found'}, 404)
        proc = subprocess.run([ggsci_bin], input='info credentialstore\n', text=True, capture_output=True)
        InfoCred = proc.stdout
        with open(os.path.join(agent_home, 'creddomains.out'), 'w') as outfile:
            outfile.write(InfoCred)
        othdom_path = os.path.join(agent_home, 'othdom.out')
        with open(os.path.join(agent_home, 'creddomains.out'), 'r') as infile, open(othdom_path, 'w') as outfile:
            copy = False
            for line in infile:
                if line.strip() == 'Other domains:':
                    copy = True
                    continue
                elif re.match('^To', line.strip()):
                    copy = False
                    continue
                elif copy:
                    outfile.write(line.strip() + '\n')
            outfile.write('OracleGoldenGate\n')
        othdomdet_path = os.path.join(agent_home, 'othdomdet.out')
        if os.path.exists(othdomdet_path):
            os.remove(othdomdet_path)
        Oth_Dom = []
        with open(othdom_path, 'r') as infile:
            for line in infile:
                for oth in line.strip().split(','):
                    oth = oth.strip()
                    if oth:
                        proc = subprocess.run([ggsci_bin], input=f'info credentialstore domain {oth}\n', text=True, capture_output=True)
                        with open(othdomdet_path, 'a') as outfile:
                            outfile.write(proc.stdout)
                        Oth_Dom.append({'value': oth, 'label': oth})
        Dom_Det = []
        Dom_Set = []
        Alias_Set = []
        with open(othdomdet_path, 'r') as infile:
            DomName = None
            Name = None
            for line in infile:
                line = line.strip()
                if re.match('^Domain:', line):
                    (_, DomName) = line.split(':', 1)
                    Dom_Set.append(DomName.strip())
                elif re.match('^Alias', line):
                    (_, Name) = line.split(':', 1)
                    Alias_Set.append({'dom': DomName.strip(), 'alias': Name.strip()})
                elif re.match('^Userid', line):
                    (_, UserName) = line.split(':', 1)
                    Dom_Det.append({'alias': Name.strip(), 'uname': UserName.strip()})
        r = {}
        for entry in Alias_Set:
            r.setdefault(entry['dom'], []).append(entry['alias'])
        Final_Alias = [{'label': dom, 'value': dom, 'children': [{'label': alias, 'value': alias} for alias in aliases]} for (dom, aliases) in r.items()]
        return [Dom_Det, Oth_Dom, Dom_Set, Alias_Set, Final_Alias]

class ggTestDBLogin(Resource):

    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('select user,passwd from CONN where dbname=:dbname', {'dbname': alias})
        db_row = cursor.fetchone()
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            passwd = cipher.decrypt(passwd)
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin SOURCEDB ' + alias + ',userid ' + user + ' , password ' + passwd + '\n')
        TestDBLogin_Out = []
        (LoginErr, stderr) = ssh.communicate()
        TestDBLogin_Out.append(LoginErr)
        ssh.kill()
        ssh.stdin.close()
        with open(agent_home + '/TestDBLogin.lst', 'w') as TestDBLoginFileIn:
            for listline in TestDBLogin_Out:
                TestDBLoginFileIn.write(listline)
        with open(agent_home + '/TestDBLogin.lst', 'r') as TestDBLoginFile:
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
        input_command = f'alter credentialstore add user {user} password {passwd} alias {alias} domain {domain}\n'
        proc = subprocess.run([ggsci_bin], input=input_command, text=True, capture_output=True)
        for line in proc.stdout.splitlines():
            if 'credential' in line.lower():
                addUsr = line
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            passwd = cipher.encrypt(passwd)
            cursor.execute('insert or replace into CONN values(:dbname,:user,:passwd,:servicename)', {'dbname': alias, 'user': user, 'passwd': passwd, 'servicename': alias})
            addUsr = 'Successfully Added'
        except sqlite3.Error as e:
            clientType.append(e)
            addUsr = str(e)
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
        command_input = f'alter credentialstore replace user {user} password {passwd} alias {alias} domain {domain}\n'
        proc = subprocess.run([ggsci_bin], input=command_input, text=True, capture_output=True)
        for line in proc.stdout.splitlines():
            if 'credential' in line.lower():
                editUsr = line
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            passwd = cipher.encrypt(passwd)
            cursor.execute('INSERT OR REPLACE INTO CONN(dbname,user,passwd,servicename)  values(:dbname,:user,:passwd,:servicename)', {'dbname': alias, 'user': user, 'passwd': passwd, 'servicename': alias})
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
        command_input = f'alter credentialstore delete user {user} alias {alias} domain {domain}\n'
        proc = subprocess.run([ggsci_bin], input=command_input, text=True, capture_output=True)
        for line in proc.stdout.splitlines():
            if 'credential' in line.lower():
                delUsr = line
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('delete from CONN where dbname=:dbname', {'dbname': alias})
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
        with FileReadBackwards(gg_home + '/ggserr.log', encoding='utf-8') as infile:
            All_Data = []
            copy = False
            for _ in zip(range(lineNum), infile):
                pass
            for (index, line) in enumerate(infile, start=lineNum):
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
                    lineNum = 'No More Rows To Load'
            return [All_Data, chunkSize]

class writeTmpPrm(Resource):

    def post(self):
        data = request.get_json(force=True)
        currentExtParamList = data['currentExtParamList']
        with open(agent_home + '/tmpPrm', 'w') as infile:
            infile.write(currentExtParamList)
        with open(agent_home + '/tmpPrm', 'r') as outfile:
            prmFile = outfile.read()
        return [prmFile]

class writeMgrPrm(Resource):

    def post(self):
        data = request.get_json(force=True)
        Params = data['currentMgrParams']
        try:
            with open(os.path.join(gg_home, 'dirprm', 'mgr.prm'), 'w') as infile:
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
            with open(os.path.join(gg_home, 'dirprm', procName + '.prm'), 'w') as infile:
                infile.write(currentParams)
                msg = 'Saved ' + procName + ' Parameterfile'
        except OSError as e:
            msg = 'There is a problem in saving Parameterfile due to : ' + e
        return [msg]

class readMgrPrm(Resource):

    def get(self):
        try:
            with open(os.path.join(gg_home, 'dirprm', 'mgr.prm'), 'r') as infile:
                mgrPrmFile = infile.read()
        except OSError as e:
            mgrPrmFile = 'Please setup the parameterfile here'
        return [mgrPrmFile]

class AddInitialLoadExt(Resource):

    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        srcdep = data['srcdep']
        srcdomain = data['srcdomain']
        srcalias = data['srcalias']
        extname = data['extname']
        srctrail = data['srctrail']
        currentExtParamList = data['currentExtParamList']
        startExtChk = data['startExtChk']
        ExtErrPrint = []
        try:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write(f'add extract  {extname},SOURCEISTABLE\n')
            AddExt_Out = []
            extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
            if not os.path.exists(os.path.join(trailPath, jobName)):
                os.makedirs(os.path.join(trailPath, jobName))
            with open(extPrm, 'w') as extFile:
                extFile.write(currentExtParamList)
            status = 'STOPPED'
            if startExtChk is False:
                ssh.stdin.write(f'start extract {extname}\n')
                status = 'RUNNING'
            (AddExtErr, stderr) = ssh.communicate()
            AddExt_Out.append(AddExtErr)
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute('insert into ILEXT values(:jobname,:srcdep,:domain,:alias,:extname,:status,:trail)', {'jobname': jobName, 'srcdep': srcdep, 'domain': srcdomain, 'alias': srcalias, 'extname': extname, 'status': status, 'trail': srctrail})
            conn.commit()
        except Exception as e:
            AddExt_Out.append(str(e))
        finally:
            if conn:
                cursor.close()
                conn.close()
        with open(os.path.join(agent_home, 'AddInitialExtErr.lst'), 'w') as extErrFileIn:
            for listline in AddExt_Out:
                extErrFileIn.write(listline)
        with open(os.path.join(agent_home, 'AddInitialExtErr.lst')) as extErrFile:
            ExtErrPrint = []
            for line in extErrFile:
                if re.search('error', line, re.IGNORECASE):
                    line = line.split('>', 1)[-1]
                    ExtErrPrint.append(line)
                elif re.search('added.', line, re.IGNORECASE):
                    line = line.split('>', 1)[-1]
        return [ExtErrPrint]

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
        deferStart = data['deferStart']
        tgt_dep_type = 'oracle'
        AddAutoProcArray = []
        headers = {'Content-Type': 'application/json'}
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
            ILEXT = 'select distinct b.dep_url url_src,b.dbtype db_type from onepconn b where b.dep=:srcdep'
            param = {'srcdep': srcdep}
            ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param['srcdep']])
            for ext in ILEXT_fetch.iterrows():
                src_api_url = ext[1]['url_src'] + '/addinitialloadext'
                src_dep_type = ext[1]['db_type']
            ILREP = 'select distinct b.dep_url url_tgt,b.dbtype db_type , user, passwd  from onepconn b where b.dep=:tgtdep'
            param = {'tgtdep': tgtdep}
            ILREP_fetch = pd.read_sql_query(ILREP, conn, params=[param['tgtdep']])
            for rep in ILREP_fetch.iterrows():
                url_tgt = rep[1]['url_tgt']
                tgt_dep_type = rep[1]['db_type']
                tgt_user = rep[1]['user']
                tgt_passwd = rep[1]['passwd']
            tgt_api_url = url_tgt + '/addinitialloadrep'
            trail_api_url = url_tgt + '/onepdepurl'
            tgt_mgr_upd = url_tgt + '/updatemgrfiles'
            rmtTrailPayload = {'dep': tgtdep}
            trail_req = requests.post(trail_api_url, json=rmtTrailPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            if len(trail_req.json()) > 0:
                rmtTrailPath = trail_req.json()[1]
            srcdblogin = 'SOURCEDB ' + srcalias + ' , useridalias ' + srcalias + ' , domain ' + srcdomain
            tgtdblogin = 'useridalias ' + tgtalias + ' , domain ' + tgtdomain
            reportRate = 'REPORTCOUNT EVERY 1 MINUTES,RATE'
            srcPDB = 'SOURCECATALOG ' + pdbName
            rmtDet = 'RMTHOST ' + rmtHostName + ',MGRPORT ' + rmtMgrPort + ', TCPBUFSIZE  4194304,ENCRYPT AES256 \n'
            batchSql = 'BATCHSQL BATCHESPERQUEUE 100, OPSPERBATCH 40000'
            for dfname in glob.glob(os.path.join(agent_home, jobName, '*.csv')):
                df_iltables = pd.read_csv(dfname, index_col=False)
            df_iltables['PROC'] = np.nan
            df_iltables['PROC'] = df_iltables['PROC'].astype(object)
            for (i, name) in enumerate(tabSplit):
                name = name['TABLE_NAME']
                extName = 'E' + jobName + str(i)
                ExtParam = 'EXTRACT ' + extName + '\n' + srcdblogin + '\n'
                repName = 'R' + jobName + str(i)
                RepParam = 'REPLICAT ' + repName + '\n' + tgtdblogin + '\n'
                trailName = os.path.join(trailPath, jobName, 'Z' + str(i))
                rmtTrailName = os.path.join(rmtTrailPath, jobName, 'Z' + str(i))
                if srcdep == tgtdep:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + 'TABLE ' + name + ';'
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\nMAP ' + name + ',TARGET ' + name + ';'
                    else:
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + 'TABLE ' + name + ';'
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\nMAP ' + name + ',TARGET ' + name + ';'
                elif cdbCheck == 'YES':
                    extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + 'TABLE ' + name + ';'
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\nMAP ' + name + ',TARGET ' + name + ';'
                else:
                    extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\nTABLE ' + name + ';'
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\nMAP ' + name + ',TARGET ' + name + ';'
                srcpayload = {'jobName': jobName, 'srcdep': srcdep, 'srcdomain': srcdomain, 'srcalias': srcalias, 'extname': extName, 'srctrail': rmtTrailName, 'currentExtParamList': extPrmContents, 'startExtChk': False}
                tgtpayload = {'jobName': jobName, 'tgtdep': tgtdep, 'repname': repName, 'tgtdomain': tgtdomain, 'tgtalias': tgtalias, 'repmode': 'classic', 'currentRepParamList': repPrmContents, 'trail': rmtTrailName, 'chktbl': chktbl, 'startRepChk': False}
                try:
                    src_req = requests.post(src_api_url, json=srcpayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                    tgt_req = requests.post(tgt_api_url, json=tgtpayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                    if len(src_req.json()[0]) > 0:
                        AddAutoProcArray.append(src_req.json()[0][0])
                    if len(tgt_req.json()[0]) > 0:
                        AddAutoProcArray.append(tgt_req.json()[0][0])
                except requests.exceptions.ConnectionError:
                    AddAutoProcArray.append('Remote Deployment Not reachable')
                TabExclude = TabExclude + 'TABLEEXCLUDE ' + name + '\n'
                df_iltables.loc[df_iltables.table_name == name, 'PROC'] = extName
            extName = 'E' + jobName + 'AA'
            ExtParam = 'EXTRACT ' + extName + '\n' + srcdblogin + '\n'
            repName = 'R' + jobName + 'AA'
            RepParam = 'REPLICAT ' + repName + '\n' + tgtdblogin + '\n'
            trailName = os.path.join(trailPath, jobName, 'ZZ')
            rmtTrailName = os.path.join(rmtTrailPath, jobName, 'ZZ')
            extTableMaps = ''
            repTableMaps = ''
            for name in schemaList:
                extTableMaps = extTableMaps + 'TABLE ' + name + '.*;' + '\n'
                repTableMaps = repTableMaps + 'MAP ' + name + '.*' + ',TARGET ' + name + '.*;' + '\n'
            if len(tabSplit) > 0:
                if srcdep == tgtdep:
                    if cdbCheck == 'YES':
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                    else:
                        extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + TabExclude + '\n' + extTableMaps
                        repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
                elif cdbCheck == 'YES':
                    extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + TabExclude + '\n' + extTableMaps
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                else:
                    extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + TabExclude + '\n' + extTableMaps
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
            elif srcdep == tgtdep:
                if cdbCheck == 'YES':
                    extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + srcPDB + '\n' + extTableMaps
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
                else:
                    extPrmContents = ExtParam + 'extfile ' + trailName + '\n' + reportRate + '\n' + extTableMaps
                    repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
            elif cdbCheck == 'YES':
                extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + srcPDB + '\n' + extTableMaps
                repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + srcPDB + '\n' + repTableMaps
            else:
                extPrmContents = ExtParam + rmtDet + 'rmtfile ' + rmtTrailName + '\n' + reportRate + '\n' + extTableMaps
                repPrmContents = RepParam + reportRate + '\n' + batchSql + '\n' + repTableMaps
            mgrPrmload = {'prmFile': 'mgr.prm', 'prmContent': '\nPURGEOLDEXTRACTS ' + os.path.join(rmtTrailPath, jobName) + '/*' + ',USECHECKPOINTS'}
            mgr_prm_upd = requests.post(tgt_mgr_upd, json=mgrPrmload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            mgrOps_url = url_tgt + '/ggmgrops'
            mgrRefreshPayload = {'mgrOps': 'mgrrefresh'}
            mgr_refresh = requests.post(mgrOps_url, json=mgrRefreshPayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
            df_iltables.fillna({'PROC': extName}, inplace=True)
            df_iltables.to_csv(dfname)
            srcpayload = {'jobName': jobName, 'srcdep': srcdep, 'extname': extName, 'srcdomain': srcdomain, 'srcalias': srcalias, 'srctrail': rmtTrailName, 'currentExtParamList': extPrmContents, 'startExtChk': False}
            tgtpayload = {'jobName': jobName, 'tgtdep': tgtdep, 'repname': repName, 'tgtdomain': tgtdomain, 'tgtalias': tgtalias, 'repmode': 'classic', 'currentRepParamList': repPrmContents, 'trail': rmtTrailName, 'chktbl': chktbl, 'startRepChk': False}
            try:
                src_req = requests.post(src_api_url, json=srcpayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                tgt_req = requests.post(tgt_api_url, json=tgtpayload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(src_req.json()[0]) > 0:
                    AddAutoProcArray.append(src_req.json()[0][0])
                if len(tgt_req.json()[0]) > 0:
                    AddAutoProcArray.append(tgt_req.json()[0][0])
            except requests.exceptions.ConnectionError:
                AddAutoProcArray.append('Remote Deployment Not reachable')
            with open(os.path.join(agent_home, 'AddAutoProc.lst'), 'w') as extErrFileIn:
                for listline in AddAutoProcArray:
                    extErrFileIn.write(listline)
            with open(os.path.join(agent_home, 'AddAutoProc.lst'), 'r') as extErrFile:
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
            cursor.execute('insert into ILEXT values(:jobname,:srcdep,:extname,:srctrail)', {'jobname': jobName, 'srcdep': srcdep, 'extname': extname, 'srctrail': trail})
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
            cursor.execute('delete from ILEXT where extname=:extname and srcdep=:srcdep and jobname=:jobname', {'srcdep': srcdep, 'extname': extname, 'jobname': jobName})
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        if repmode == 'parallel':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write('add replicat ' + repname + ',' + repmode + ',exttrail ' + trail + ',checkpointtable ' + chktbl + '\n')
        elif repmode == 'integrated':
            trail = data['trail']
            ssh.stdin.write('add replicat ' + repname + ',' + repmode + ',exttrail ' + trail + '\n')
        elif repmode == '' or repmode == 'classic':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write('add replicat ' + repname + ',exttrail ' + trail + ',checkpointtable ' + chktbl + '\n')
        elif repmode == 'coordinated':
            trail = data['trail']
            chktbl = data['chktbl']
            ssh.stdin.write('add replicat ' + repname + ',' + repmode + ',exttrail ' + trail + ',checkpointtable ' + chktbl + '\n')
        elif repmode == 'SPECIALRUN':
            ssh.stdin.write('add replicat ' + repname + ',' + repmode + '\n')
        if startRepChk is False:
            ssh.stdin.write('start replicat ' + repname + '\n')
        (AddRepErr, stderr) = ssh.communicate()
        AddRep_Out = []
        AddRep_Out.append(AddRepErr)
        with open(agent_home + '/AddInitialRepErr.lst', 'w') as repErrFileIn:
            for listline in AddRep_Out:
                repErrFileIn.write(listline)
        with open(agent_home + '/AddInitialRepErr.lst', 'r') as repErrFile:
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
            cursor.execute('insert into ILREP values(:jobname,:tgtdep,:repname,:tgttrail)', {'jobname': jobName, 'tgtdep': tgtdep, 'repname': repname, 'tgttrail': trail})
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
            cursor.execute('delete from ILREP where jobname=:jobname and repname=:repname and tgtdep=:tgtdep', {'jobname': jobName, 'tgtdep': tgtdep, 'repname': repname})
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
            ILData = 'select jobname from ILEXT'
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=100)
        if ops.startswith('stop'):
            for name in processName:
                for (key, process) in name.items():
                    if key == 'ExtName' or key == 'PmpName' or key == 'RepName':
                        ssh.stdin.write('stop ' + process + '\n')
        elif ops.startswith('start'):
            for name in processName:
                for (key, process) in name.items():
                    if key == 'ExtName' or key == 'PmpName' or key == 'RepName':
                        ssh.stdin.write('start ' + process + '\n')
        (resProcess, stderr) = ssh.communicate()
        ActionErrPrint = []
        with open(os.path.join(agent_home, 'ggProcessAction.trc'), 'w') as extChkFileIn:
            extChkFileIn.write(resProcess)
        with open(os.path.join(agent_home, 'ggProcessAction.trc')) as extErrFile:
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
            metaDir = os.path.join(agent_home, jobName, jobName + '*.csv')
            for file in glob.glob(metaDir):
                df = pd.read_csv(file)
                for (i, name) in df.iterrows():
                    TabName = name['owner'] + '.' + name['table_name']
                    ILExtProcStats[TabName] = {'TargetRows': name['count'], 'Process': 'Extract', 'EXT_ROWS_PROCESSED': 0, 'EXT_ELAPSED': 0, 'EXT_RATE': 0, 'REP_ROWS_PROCESSED': 0, 'REP_ELAPSED': 0, 'REP_RATE': 0}
        except Exception as e:
            tgtdeptype = str(e)
        finally:
            df.index.name = 'TabName'
            if not os.path.exists(os.path.join(agent_home, jobName, jobName + '_Summary')):
                df.to_csv(os.path.join(agent_home, jobName, jobName + '_Summary'))
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
            placeholders = ','.join(['?'] * len(repDet))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            if ilops == 'extstop':
                for name in extname:
                    ssh.stdin.write('kill ' + name + '\n')
                (ilExtKill, stderr) = ssh.communicate()
                ILEXTUPD = f"update ILEXT set status='STOPPED' where extname in ({placeholders})"
                cursor.execute(ILEXTUPD, extname)
                conn.commit()
            elif ilops == 'extstart':
                for name in extname:
                    ssh.stdin.write(f'start extract {name}\n')
                (ilExtStart, stderr) = ssh.communicate()
                ILEXTUPD = f"update ILEXT set status='RUNNING' where extname in ({placeholders})"
                cursor.execute(ILEXTUPD, extname)
                conn.commit()
            elif ilops == 'extpurge':
                for name in extname:
                    ssh.stdin.write(f'delete {name}\n')
                (ilExtDel, stderr) = ssh.communicate()
                ILEXTDEL = f'delete from ILEXT where extname in ({placeholders})'
                cursor.execute(ILEXTDEL, extname)
                conn.commit()
            with open(os.path.join(agent_home, 'ILExtOps.lst'), 'w') as ilOpsFileIn:
                ilOpsFileIn.write(ilExtDel)
            with open(os.path.join(agent_home, 'ILExtOps.lst'), 'r') as ilExtOpsFile:
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
            placeholders = ','.join(['?'] * len(repDet))
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            repName = []
            if ilops == 'repstop':
                for pattern in repDet:
                    ssh.stdin.write(f"kill {pattern['repname']} \n")
                    ssh.stdin.write(f"alter replicat {pattern['repname']}, extseqno 0 , extrba 0 \n")
                    repName.append(pattern['repname'])
                    fileList = glob.glob(pattern['trail'] + '*', recursive=True)
                    for filename in fileList:
                        os.remove(filename)
                (chkRep, stderr) = ssh.communicate()
                ILREPUPD = f"update ILREP set status='STOPPED' where repname in ({placeholders})"
                cursor.execute(ILREPUPD, repName)
                conn.commit()
                conn.close()
                for file in os.scandir(os.path.join(agent_home, jobName)):
                    if '_tables' not in file.name:
                        os.remove(file.path)
            elif ilops == 'repstart':
                for pattern in repDet:
                    ssh.stdin.write(f"start {pattern['repname']} , NOFILTERDUPTRANSACTIONS \n")
                    repName.append(pattern['repname'])
                (chkRep, stderr) = ssh.communicate()
                ILREPUPD = f"update ILREP set status='RUNNING' where repname in ({placeholders})"
                cursor.execute(ILREPUPD, repName)
                conn.commit()
                conn.close()
            elif ilops == 'reppurge':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write(f'dblogin sourcedb  {alias} , useridalias {alias} , domain {domain}\n')
                for pattern in repDet:
                    if pattern['status'] == 'STOPPED':
                        ssh.stdin.write(f"delete replicat {pattern['repname']}\n")
                        repName.append(pattern['repname'])
                    else:
                        chkRep = f"Replicat {pattern['repname']} is still running"
                (chkRep, stderr) = ssh.communicate()
                ILREPDEL = f'delete from ILREP where repname in ({placeholders})'
                cursor.execute(ILREPDEL, repName)
                conn.commit()
                conn.close()
            with open(os.path.join(agent_home, 'ILRepOps.lst'), 'w') as ilOpsFileIn:
                ilOpsFileIn.write(chkRep)
            with open(os.path.join(agent_home, 'ILRepOps.lst'), 'r') as ilRepOpsFile:
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
        try:
            ILEXT = 'select distinct a.*,b.dep_url url_src from ILEXT a, onepconn b\n                            where a.srcdep=b.dep and a.jobname=:jobName'
            param = {'jobName': jobName}
            ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param['jobName']])
            extName = []
            for ext in ILEXT_fetch.iterrows():
                dep_url = ext[1]['url_src']
                extName.append(ext[1]['extname'])
            api_url = dep_url + '/ggiljobact'
            payload = {'jobName': jobName, 'extName': extName, 'ilops': 'ext' + ilops}
            headers = {'Content-Type': 'application/json'}
            try:
                r = requests.post(api_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(r.json()[0]) > 0:
                    ilOpData = r.json()[0]
            except requests.exceptions.ConnectionError:
                ILException = 'error'
        except Exception as e:
            pass
        try:
            ILREP = 'select distinct a.*,b.dep_url url_tgt from ILREP a, onepconn b\n                            where a.tgtdep=b.dep and jobname=:jobName'
            param = {'jobName': jobName}
            ILREP_fetch = pd.read_sql_query(ILREP, conn, params=[param['jobName']])
            repDet = []
            for rep in ILREP_fetch.iterrows():
                dep_url = rep[1]['url_tgt']
                repDet.append({'repname': rep[1]['repname'], 'status': rep[1]['status'], 'trail': rep[1]['trail']})
                tgtdomain = rep[1]['domain']
                tgtalias = rep[1]['alias']
            api_url = dep_url + '/ggiljobact'
            payload = {'jobName': jobName, 'repDet': repDet, 'ilops': 'rep' + ilops, 'domain': tgtdomain, 'alias': tgtalias}
            headers = {'Content-Type': 'application/json'}
            try:
                r = requests.post(api_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(r.json()[0]) > 0:
                    ilOpData = r.json()[0]
            except requests.exceptions.ConnectionError:
                ILException = 'error'
        except Exception as e:
            ilOpData = str(e)
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
        ILEXT = 'select distinct a.*,b.dep_url url_src from ILEXT a, onepconn b\n                            where a.srcdep=b.dep and a.jobname=:jobName'
        param = {'jobName': jobName}
        ILEXT_fetch = pd.read_sql_query(ILEXT, conn, params=[param['jobName']])
        for dfname in glob.glob(os.path.join(agent_home, jobName, '*.csv')):
            tabList = pd.read_csv(dfname, index_col=False)
            tabList = tabList.to_dict(orient='records')
        for ext in ILEXT_fetch.iterrows():
            depName = ext[1]['srcdep']
            extname = ext[1]['extname']
            dep_url = ext[1]['url_src']
            trail = ext[1]['trail']
            ProcessNode.setdefault(depName, []).append({'procname': extname, 'dep_url': dep_url, 'type': 'Ext'})
            SrcLinkNode.append({'extname': extname, 'trail': trail, 'dep_src': depName})
        if dep_url:
            api_url = dep_url + '/gginfoext'
            extname = 'E' + jobName + '*'
            payload = {'extname': extname}
            headers = {'Content-Type': 'application/json'}
            for name in tabList:
                ILExtProcStats[name['table_name']] = {'TargetRows': name['count'], 'Process': name['PROC'], 'TotalEXT': 0}
            try:
                r = requests.post(api_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(r.json()[0]) > 0:
                    ILExtData = r.json()[0]
                    stat_url = dep_url + '/ggextprocstats'
                    for name in r.json()[0]:
                        payload = {'procName': name['extname'], 'procStats': name['extstat'], 'jobName': jobName, 'ILExtProcStats': ILExtProcStats}
                        try:
                            r = requests.post(stat_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                            if r.json() != None:
                                if len(r.json()) > 0:
                                    ILExtProcStats.update(r.json())
                        except requests.exceptions.ConnectionError:
                            ILException = 'error'
            except requests.exceptions.ConnectionError:
                ILException = 'error'
        ILRMT = "select distinct dep_url url_tgt from onepconn where dep_type='rd'"
        ILRMT_fetch = pd.read_sql_query(ILRMT, conn)
        for rep in ILRMT_fetch.iterrows():
            tgt_url = rep[1]['url_tgt']
        if tgt_url:
            api_url = tgt_url + '/ggilrep'
            payload = {'jobName': jobName}
            headers = {'Content-Type': 'application/json'}
            try:
                r = requests.post(api_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(r.json()[0]) > 0:
                    for name in r.json()[0]:
                        depName = name['depName']
                        repname = name['repname']
                        dep_url = name['dep_url']
                        trail = name['trail']
                        ProcessNode.setdefault(depName, []).append({'procname': repname, 'dep_url': dep_url, 'type': 'Rep'})
                        TgtLinkNode.append({'repname': repname, 'trail': trail, 'dep_tgt': depName})
            except requests.exceptions.ConnectionError:
                depName = 'error'
            api_url = tgt_url + '/gginforep'
            repname = 'R' + jobName + '*'
            payload = {'repname': repname}
            headers = {'Content-Type': 'application/json'}
            try:
                r = requests.post(api_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                if len(r.json()[0]) > 0:
                    ILRepData = r.json()[0]
                    stat_url = tgt_url + '/ggrepprocstats'
                    for name in r.json()[0]:
                        payload = {'procName': name['repname'], 'jobName': jobName, 'procStats': name['repstat'], 'ILExtProcStats': ILExtProcStats}
                        try:
                            r = requests.post(stat_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                            if r.json() != None:
                                if len(r.json()) > 0:
                                    ILExtProcStats.update(r.json())
                        except requests.exceptions.ConnectionError:
                            ILException = 'error'
            except requests.exceptions.ConnectionError as e:
                ILException = 'error'
        SrcLinkNode_fetch = pd.DataFrame(SrcLinkNode)
        TgtLinkNode_fetch = pd.DataFrame(TgtLinkNode)
        if SrcLinkNode_fetch.empty == False and TgtLinkNode_fetch.empty == False:
            TrailCommon = pd.merge(SrcLinkNode_fetch, TgtLinkNode_fetch, on=['trail'], how='inner')
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
            if not os.path.exists(os.path.join(agent_home, jobName)):
                os.makedirs(os.path.join(agent_home, jobName))
            if not os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
                with open(os.path.join(agent_home, jobName, procName + 'running'), mode='w') as infile:
                    pass
                ilp = threading.Thread(target=ILGetStats, args=(procName, jobName))
                ilp.start()
            try:
                with open(os.path.join(agent_home, jobName, procName + 'Rate.lst')) as infile:
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
                                    ILExtProcStats[TabName].update({'TotalEXT': TotalEXT, 'TotalEXTDSC': TotalEXTDSC, 'ExtRate': ExtRate})
            except FileNotFoundError:
                pass
        elif procStats == 'STOPPED' or 'ABENDED':
            stop_threads = True
            if os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
                os.remove(os.path.join(agent_home, jobName, procName + 'running'))
            if os.path.exists(os.path.join(agent_home, jobName, procName + 'Rate.lst')):
                os.remove(os.path.join(agent_home, jobName, procName + 'Rate.lst'))
            try:
                with open(os.path.join(gg_home, 'dirrpt', procName + '.rpt'), 'r') as infile:
                    for line in infile:
                        if 'Report at' in line:
                            line = line.split()
                            endTime = line[2] + ':' + line[3]
                            startTime = line[6] + ':' + line[7].rstrip(')')
                            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
                            elapTime = datetime.strptime(endTime, datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
                            elapTime = str(elapTime.total_seconds())
                        elif line.startswith('From Table'):
                            TabName = line.split()[2].rstrip(':')
                        elif 'inserts' in line:
                            TotalEXT = line.split()[2]
                        elif 'discards' in line:
                            TotalEXTDSC = line.split()[2]
                            if TabName in ILExtProcStats.keys():
                                ILExtProcStats[TabName].update({'TotalEXT': TotalEXT, 'TotalEXTDSC': TotalEXTDSC, 'ExtElapse': elapTime, 'ExtRate': 'Completed'})
            except FileNotFoundError:
                pass
        return ILExtProcStats

class ggRepProcStats(Resource):

    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        procName = data['procName']
        procStats = data['procStats']
        ILExtProcStats = data['ILExtProcStats']
        elapTime = ''
        if procStats == 'RUNNING':
            if not os.path.exists(os.path.join(agent_home, jobName)):
                os.makedirs(os.path.join(agent_home, jobName))
            if not os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
                with open(os.path.join(agent_home, jobName, procName + 'running'), mode='w') as infile:
                    pass
                ilp = threading.Thread(target=ILGetStats, args=(procName, jobName))
                ilp.start()
            try:
                with open(os.path.join(agent_home, jobName, procName + 'Rate.lst')) as infile:
                    copy = False
                    rateCopy = False
                    for line in infile:
                        if line.startswith('Replicating'):
                            TabName = line.split()[2]
                        elif 'Total statistics' in line:
                            rateCopy = True
                            continue
                        elif 'Total operations/second' in line:
                            rateCopy = False
                            continue
                        elif rateCopy:
                            if 'inserts/second' in line:
                                RepRate = line.split()[2]
                        elif 'Latest statistics' in line:
                            line = line.split()
                            startTime = line[4] + ':' + line[5].rstrip(')')
                            datetimeFormat = '%Y-%m-%d:%H:%M:%S'
                            copy = True
                            continue
                        elif 'End of statistics' in line:
                            copy = False
                            continue
                        elif copy:
                            if 'Total inserts/second' in line:
                                TotalREP = round(float(line.split()[2]))
                            elif 'Total discards/second' in line:
                                TotalREPDSC = line.split()[2]
                                Status = ''
                                RepETA = 0
                                for (key, value) in ILExtProcStats.items():
                                    if key == TabName:
                                        if int(value['TotalEXT']) == int(TotalREP) and value['ExtRate'] == 'Completed':
                                            if not os.path.exists(os.path.join(agent_home, jobName, TabName + 'endtime')):
                                                with open(os.path.join(agent_home, jobName, TabName + 'endtime'), mode='w') as infile:
                                                    endTime = datetime.now()
                                                    endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
                                                    infile.write(str(endTime) + ' ' + startTime + ' ' + str(TotalREP) + ' ' + str(TotalREPDSC))
                                                    elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
                                                    elapTime = elapTime.total_seconds()
                                                    Status = 'Completed'
                                            else:
                                                with open(os.path.join(agent_home, jobName, TabName + 'endtime')) as infile:
                                                    endTime = infile.read()
                                                    endTime = endTime.split()[0]
                                                    elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
                                                    elapTime = elapTime.total_seconds()
                                                    Status = 'Completed'
                                        else:
                                            endTime = datetime.now()
                                            endTime = endTime.strftime('%Y-%m-%d:%H:%M:%S')
                                            elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
                                            elapTime = elapTime.total_seconds()
                                            Status = 'InProgress'
                                            RepETA = (int(value['TargetRows']) - int(TotalREP)) / float(RepRate)
                                if TabName in ILExtProcStats.keys():
                                    ILExtProcStats[TabName].update({'TotalREP': TotalREP, 'TotalREPDSC': TotalREPDSC, 'RepRate': RepRate, 'RepElapse': elapTime, 'RepETA': round(RepETA), 'Status': Status})
            except FileNotFoundError:
                pass
        elif procStats == 'STOPPED' or 'ABENDED':
            if os.path.exists(os.path.join(agent_home, jobName, procName + 'running')):
                os.remove(os.path.join(agent_home, jobName, procName + 'running'))
            if os.path.exists(os.path.join(agent_home, jobName, procName + 'Rate.lst')):
                os.remove(os.path.join(agent_home, jobName, procName + 'Rate.lst'))
            try:
                datetimeFormat = '%Y-%m-%d:%H:%M:%S'
                for name in glob.glob(os.path.join(agent_home, jobName, '*endtime')):
                    with open(name) as infile:
                        procTime = infile.read()
                        procTime = procTime.split()
                        endTime = procTime[0]
                        startTime = procTime[1]
                        TotalREP = procTime[2]
                        TotalREPDSC = procTime[3]
                        elapTime = datetime.strptime(str(endTime), datetimeFormat) - datetime.strptime(startTime, datetimeFormat)
                        elapTime = elapTime.total_seconds()
                        TabName = name.split('/')[-1].strip('endtime')
                        if procStats == 'STOPPED':
                            Status = 'Completed'
                        elif procStats == 'ABENDED':
                            Status = 'Abended'
                        if TabName in ILExtProcStats.keys():
                            ILExtProcStats[TabName].update({'TotalREP': TotalREP, 'TotalREPDSC': TotalREPDSC, 'RepElapse': elapTime, 'Status': Status})
            except FileNotFoundError:
                pass
        return ILExtProcStats

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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
        AddExt_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            AddExt_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            AddExt_Out.append(LoginErr)
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            if str(regExtChk) == 'True':
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                if CDBCheck == 'YES':
                    PDBList = ''
                    for name in pdbSelList:
                        PDBList = PDBList + name + ','
                    PDBList = PDBList.rstrip(',')
                    AddExt_Out.append(PDBList)
                    if regVal == 'now':
                        ssh.stdin.write('register extract ' + extname + ' database CONTAINER(' + PDBList + ')' + '\n')
                    elif regVal == 'existscn':
                        ssh.stdin.write('register extract ' + extname + ' database CONTAINER(' + PDBList + ')' + ' SCN ' + str(lmDictSCN) + '\n')
                elif regVal == 'now':
                    ssh.stdin.write('register extract ' + extname + ' database' + '\n')
                elif regVal == 'existscn' and currentShareOpt == 'NONE':
                    ssh.stdin.write('register extract ' + extname + ' database SCN ' + str(lmDictSCN) + ' SHARE ' + currentShareOpt + '\n')
                elif regVal == 'existscn' and currentShareOpt == 'AUTOMATIC':
                    ssh.stdin.write('register extract ' + extname + ' database SCN ' + str(lmDictSCN) + ' SHARE ' + currentShareOpt + '\n')
                elif regVal == 'existscn' and currentShareOpt == 'EXTRACT':
                    ssh.stdin.write('register extract ' + extname + ' database SCN ' + str(lmDictSCN) + ' SHARE ' + CaptureName + '\n')
            (RegErr, stderr) = ssh.communicate()
            if 'ERROR' in RegErr:
                AddExt_Out.append(RegErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                ssh.stdin.write('add extract ' + extname + ' integrated tranlog ' + beginmode + '\n')
                ssh.stdin.write('add exttrail ' + trailsubdir + trailsubdirslash + trail + ' extract ' + extname + ' megabytes ' + str(trailsize) + '\n')
                (AddExtErr, stderr) = ssh.communicate()
                if 'ERROR' in AddExtErr:
                    AddExt_Out.append(AddExtErr)
                    ssh.kill()
                    ssh.stdin.close()
                else:
                    extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
                    with open(extPrm, 'w') as extFile:
                        extFile.write(currentExtParamList)
                        if startExtChk is False:
                            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                            ssh.stdin.write('start extract ' + extname)
                            (StartExtErr, stderr) = ssh.communicate()
                            AddExt_Out.append(AddExtErr)
                            AddExt_Out.append(StartExtErr)
                        else:
                            AddExt_Out.append(AddExtErr)
                            ssh.kill()
                            ssh.stdin.close()
        with open(agent_home + '/AddExtErr.lst', 'w') as extErrFileIn:
            for listline in AddExt_Out:
                extErrFileIn.write(listline)
        with open(agent_home + '/AddExtErr.lst', 'r') as extErrFile:
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
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin SOURCEDB ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
            InfoChkptTbl_Out = []
            (LoginErr, stderr) = ssh.communicate()
            if 'ERROR' in LoginErr:
                InfoChkptTbl_Out.append(LoginErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                conn = sqlite3.connect('conn.db')
                cursor = conn.cursor()
                cursor.execute('SELECT tabname FROM CHKPT WHERE dbname=:dbname', {'dbname': alias})
                db_row = cursor.fetchone()
                if db_row:
                    tabname = db_row[0]
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                    ssh.stdin.write('dblogin SOURCEDB ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
                    ssh.stdin.write('info  checkpointtable ' + tabname + '\n')
                    (InfoChkptTblErr, stderr) = ssh.communicate()
                    InfoChkptTbl_Out.append(InfoChkptTblErr)
                    InfoChkptErrPrint.append(db_row)
                else:
                    InfoChkptTbl_Out.append('ERROR : No Checkpoint Table found')
            with open(os.path.join(agent_home, 'InfoChkptTbl.lst'), 'w') as InfoErrFileIn:
                for listline in InfoChkptTbl_Out:
                    InfoErrFileIn.write(listline)
            with open(os.path.join(agent_home, 'InfoChkptTbl.lst'), 'r') as InfoErrFile:
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
        return [InfoChkptTbl_Out, InfoChkptErrPrint]

class ggAddChkptTbl(Resource):

    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        chkpttbl = data['chkpttbl']
        AddChkptErrPrint = ''
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin SOURCEDB ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
        AddChkptTbl_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            AddChkptTbl_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin SOURCEDB ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
            ssh.stdin.write('add checkpointtable  ' + chkpttbl + '\n')
            (AddChkptTblErr, stderr) = ssh.communicate()
            AddChkptTbl_Out.append(AddChkptTblErr)
        with open(os.path.join(agent_home, 'AddChkptTbl.lst'), 'w') as extErrFileIn:
            for listline in AddChkptTbl_Out:
                extErrFileIn.write(listline)
        with open(os.path.join(agent_home, 'AddChkptTbl.lst'), 'r') as extErrFile:
            AddChkptErrPrint = []
            for line in extErrFile:
                if 'ERROR' in line:
                    line = line.split('>', 1)[-1]
                    AddChkptErrPrint.append(line)
                    if 'already' in line:
                        conn = sqlite3.connect('conn.db')
                        cursor = conn.cursor()
                        try:
                            cursor.execute('insert into CHKPT values(:dbname,:tabname)', {'dbname': alias, 'tabname': chkpttbl})
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
                    cursor.execute('insert into CHKPT values(:dbname,:tabname)', {'dbname': alias, 'tabname': chkpttbl})
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
        beginmode = data['beginmode']
        trailtype = data['trailtype']
        trailsubdir = data['trailsubdir']
        trailsubdirslash = data['trailsubdirslash']
        trail = data['trail']
        trailsize = data['trailsize']
        currentExtParamList = data['currentExtParamList']
        if trailtype == 'rmttrail':
            rmttrailSubDir = data['rmttrailSubDir']
            rmtTrailName = data['rmtTrailName']
        startExtChk = data['startExtChk']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' domain ' + domain + '\n')
        AddCE_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            AddCE_Out.append(LoginErr)
            ssh.kill()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' domain ' + domain + '\n')
            ssh.stdin.write('add extract ' + extname + ' , ' + mode + ' , ' + beginmode + '\n')
            if trailtype == 'rmttrail':
                ssh.stdin.write('add rmttrail ' + rmttrailSubDir + trailsubdirslash + rmtTrailName + ' extract ' + extname + ' megabytes ' + str(trailsize) + '\n')
            else:
                ssh.stdin.write('add exttrail ' + trailsubdir + trailsubdirslash + trail + ' extract ' + extname + ' megabytes ' + str(trailsize) + '\n')
            (AddCEErr, stderr) = ssh.communicate()
            AddCE_Out.append(AddCEErr)
            extPrm = os.path.join(gg_home, 'dirprm', extname + '.prm')
            with open(extPrm, 'w') as extFile:
                extFile.write(currentExtParamList)
            if startExtChk is False:
                ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                ssh.stdin.write('start extract ' + extname)
                (StartCEErr, stderr) = ssh.communicate()
                AddCE_Out.append(StartCEErr)
                ssh.kill()
                ssh.stdin.close()
        with open(os.path.join(agent_home, 'AddCEErr.lst'), 'w') as extErrFileIn:
            for listline in AddCE_Out:
                extErrFileIn.write(listline)
        with open(os.path.join(agent_home, 'AddCEErr.lst')) as extErrFile:
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
        proc = subprocess.run([ggsci_bin], input='info exttrail\n', text=True, capture_output=True)
        InfoExt = proc.stdout
        with open(os.path.join(agent_home, 'infoext.out'), mode='w') as outfile2:
            outfile2.write(InfoExt)
        with open(os.path.join(agent_home, 'infoext.out'), mode='r') as infile:
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
        ggsci_proc = subprocess.run([ggsci_bin], input=f'info {currentextname} , showch\n', text=True, capture_output=True)
        for line in ggsci_proc.stdout.splitlines():
            if 'Extract Trail:' in line:
                exttrail = line.split(':')[1]
        copy = False
        for name in glob.glob(os.path.join(gg_home, 'dirprm', '*.prm')):
            name = name.split('/')[-1]
            if re.match(name, currentextname + '.prm', re.IGNORECASE):
                with open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('add extract ' + extname + ' , ' + mode + ' ' + srcTrail + ' ' + beginmode + '\n')
        ssh.stdin.write('add rmttrail ' + trail + ' extract ' + extname + ' megabytes ' + str(trailsize) + '\n')
        (AddPmpErr, stderr) = ssh.communicate()
        with open(os.path.join(gg_home, 'dirprm', extname + '.prm'), 'w') as pmpFile:
            pmpFile.write(currentPmpParamList)
        if startPmpChk is False:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('start extract ' + extname + '\n')
            (StartPmpErr, stderr) = ssh.communicate()
            AddPmp_Out.append(AddPmpErr)
            AddPmp_Out.append(StartPmpErr)
        else:
            AddPmp_Out.append(AddPmpErr)
        with open(agent_home + '/AddPmpErr.lst', 'w') as pmpErrFileIn:
            for listline in AddPmp_Out:
                pmpErrFileIn.write(listline)
        with open(agent_home + '/AddPmpErr.lst', 'r') as pmpErrFile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
        DelExt_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            DelExt_Out.append(LoginErr)
            ssh.kill()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
            ssh.stdin.write('delete ' + extname + '\n')
            (DelExtErr, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            DelExt_Out.append(DelExtErr)
        with open(agent_home + '/DelExtErr.lst', 'w') as extErrFileIn:
            for listline in DelExt_Out:
                extErrFileIn.write(listline)
        with open(agent_home + '/DelExtErr.lst', 'r') as extErrFile:
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
                with open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
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
        proc = subprocess.run([ggsci_bin], input='info rmttrail\n', text=True, capture_output=True)
        InfoRmt = proc.stdout
        DelRmt = ''
        informt_path = os.path.join(agent_home, 'informt.out')
        with open(informt_path, mode='w') as outfile2:
            outfile2.write(InfoRmt)
        with open(agent_home + '/informt.out', mode='r') as infile:
            RMT_Data = []
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip()
                    if ExtName.upper() == pmpName.upper():
                        proc = subprocess.run([ggsci_bin], input=input_cmd, text=True, capture_output=True)
                        DelRmt = proc.stdout
        if not DelRmt:
            DelRmt = 'No Remote trails attached to pump ' + pmpName
        with open(os.path.join(agent_home, 'DelRMTErr.lst'), 'w') as delrmtErrFileIn:
            delrmtErrFileIn.write(DelRmt)
        with open(os.path.join(agent_home, 'DelRMTErr.lst'), 'r') as delrmtErrFile:
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
        PARAM_DIRECTORY = os.path.join(gg_home, 'dirrpt')
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
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            if extops == 'extchk':
                ssh.stdin.write('info ' + extname + ' showch debug')
            elif extops == 'extstats':
                ssh.stdin.write('stats extract ' + extname + '\n')
            elif extops == 'extstartdef':
                ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'extstartatcsn':
                extatcsn = data['extatcsn']
                ssh.stdin.write('start ' + extname + ' atcsn ' + str(extatcsn))
            elif extops == 'extstartaftercsn':
                extaftercsn = data['extaftercsn']
                ssh.stdin.write('start ' + extname + ' aftercsn ' + str(extaftercsn))
            elif extops == 'extstop':
                ssh.stdin.write('stop extract ' + extname + '\n')
            elif extops == 'extforcestop':
                ssh.stdin.write('send extract ' + extname + ' forcestop' + '\n')
            elif extops == 'extkill':
                ssh.stdin.write('kill extract ' + extname + '\n')
            elif extops == 'extstatus':
                ssh.stdin.write('send extract ' + extname + ' status' + '\n')
            elif extops == 'extdel':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin SOURCEDB ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
                ssh.stdin.write('delete extract ' + extname + '\n')
            elif extops == 'pmpdel':
                ssh.stdin.write('delete extract ' + extname + '\n')
            elif extops == 'upgie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('info ' + extname)
                (InfoExt, stderr) = ssh.communicate()
                if 'Integrated' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Integrated Mode !! STOP !!')
                elif 'Oracle Redo Logs' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    (LoginErr, stderr) = ssh.communicate()
                    if 'ERROR' in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                        ssh.stdin.write('send extract ' + extname + ' tranlogoptions PREPAREFORUPGRADETOIE' + '\n')
                        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                        ssh.stdin.write('stop extract ' + extname + '\n')
                        time.sleep(60)
                        ssh.stdin.write('info extract ' + extname + '\n')
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write('register extract ' + extname + ' database' + '\n')
                        RegErr = ssh.stdout.readline()
                        if 'ERROR' in RegErr and 'already registered' not in RegErr:
                            ExtErrPrint.append(RegErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(RegErr)
                            ssh.stdin.write('start extract ' + extname + '\n')
                            time.sleep(60)
                            ssh.stdin.write('info extract ' + extname + ' upgrade' + '\n')
                            ssh.stdin.flush()
                        while True:
                            upg_Output = ssh.stdout.readline()
                            if 'ERROR' in upg_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + ' upgrade ' + '\n')
                                ssh.stdout.flush()
                            elif 'capture.' in upg_Output:
                                break
                        ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'dwnie':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('info ' + extname)
                (InfoExt, stderr) = ssh.communicate()
                if 'Oracle Redo Logs' in InfoExt:
                    ExtErrPrint.append('Extract is Already in Classic Mode !! STOP !!')
                elif 'Integrated' in InfoExt and 'RUNNING' in InfoExt:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    (LoginErr, stderr) = ssh.communicate()
                    if 'ERROR' in LoginErr:
                        ExtErrPrint.append(LoginErr)
                        ssh.kill()
                        ssh.stdin.close()
                    else:
                        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                        ssh.stdin.write('stop extract ' + extname + '\n')
                        time.sleep(60)
                        ssh.stdin.write('info extract ' + extname + '\n')
                        ssh.stdin.flush()
                        while True:
                            info_Output = ssh.stdout.readline()
                            if 'RUNNING' in info_Output:
                                time.sleep(60)
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'STOPPED' in info_Output:
                                break
                        ssh.stdin.write('info ' + extname + ' downgrade' + '\n')
                        InfoIEErr = ssh.stdout.readline()
                        if 'ready to be downgraded' not in InfoIEErr:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.kill()
                            ssh.stdin.close()
                        else:
                            ExtErrPrint.append(InfoIEErr)
                            ssh.stdin.write('alter extract ' + extname + ' downgrade integrated tranlog' + '\n')
                            ssh.stdin.write('info extract ' + extname + '\n')
                            ssh.stdin.flush()
                        while True:
                            dwn_Output = ssh.stdout.readline()
                            if 'ERROR' in dwn_Output:
                                ssh.stdin.write('info extract ' + extname + '\n')
                                ssh.stdout.flush()
                            elif 'Oracle Redo Logs' in dwn_Output:
                                break
                        ssh.stdin.write('unregister extract ' + extname + ' database' + '\n')
                        ssh.stdin.write('start extract ' + extname + '\n')
            elif extops == 'extetroll':
                ssh.stdin.write('alter extract ' + extname + ' etrollover' + '\n')
            elif extops == 'extbegin':
                beginmode = data['beginmode']
                if beginmode == 'Now':
                    ssh.stdin.write('alter extract ' + extname + ',begin now\n')
                elif beginmode == 'Time':
                    domain = data['domain']
                    alias = data['alias']
                    ctvalue = data['ctvalue']
                    ctvalue = ctvalue.replace('T', ' ')
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    ssh.stdin.write('alter extract ' + extname + ',begin ' + ctvalue + '\n')
                elif beginmode == 'SCN':
                    domain = data['domain']
                    alias = data['alias']
                    scnvalue = data['scnvalue']
                    ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                    ssh.stdin.write('alter extract ' + extname + ',scn ' + str(scnvalue) + '\n')
                elif beginmode == 'pmpextseqno':
                    seqnovalue = data['seqnovalue']
                    rbavalue = data['rbavalue']
                    ssh.stdin.write('alter extract ' + extname + ',extseqno ' + str(seqnovalue) + ',extrba ' + str(rbavalue) + '\n')
            elif extops == 'exttraildel':
                trailname = data['trailname']
                for name in trailname:
                    ssh.stdin.write('delete exttrail ' + name + ', Extract ' + extname + '\n')
            elif extops == 'exttrailadd':
                trailname = data['trailname']
                trailtype = data['trailtype']
                trailsize = data['trailsize']
                ssh.stdin.write('add ' + trailtype + ' ' + trailname + ', Extract ' + extname + ',megabytes ' + str(trailsize) + '\n')
            elif extops == 'cachemgr':
                ssh.stdin.write('send extract ' + extname + ' cachemgr cachestats' + '\n')
            elif extops == 'extunreg':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                ssh.stdin.write('unregister extract ' + extname + ' database' + '\n')
            elif extops == 'extedit':
                with open(os.path.join(gg_home, 'dirprm', extname + '.prm')) as extPrmFile:
                    prmfile = extPrmFile.read()
            (chkExt, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            if extops == 'extstats':
                with open(os.path.join(agent_home, 'extStats'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(agent_home, 'extStats')) as extErrFile:
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
                            if not line.strip().startswith('No'):
                                OpNameFinal = ''
                                OpName = line.strip().split()[0:-1]
                                if len(OpName) > 0:
                                    for Op in OpName:
                                        OpNameFinal = OpNameFinal + Op
                                    OpNameFinal = OpNameFinal.lstrip()
                                    Oper = line.split()[-1]
                                    ExtProcStats[TabName].update({OpNameFinal: Oper})
            else:
                with open(os.path.join(agent_home, 'ChkExt.lst'), 'w') as extChkFileIn:
                    extChkFileIn.write(chkExt)
                with open(os.path.join(agent_home, 'ChkExt.lst'), 'r') as extErrFile:
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
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            if repops == 'repchk':
                ssh.stdin.write('info ' + repname + ' showch debug')
            elif repops == 'repstats':
                ssh.stdin.write('stats replicat ' + repname + '\n')
            elif repops == 'repstartdef':
                ssh.stdin.write('start replicat ' + repname + '\n')
            elif repops == 'repskiptrans':
                ssh.stdin.write('start replicat ' + repname + ' SKIPTRANSACTION' + '\n')
            elif repops == 'repnofilterdup':
                ssh.stdin.write('start replicat ' + repname + ' NOFILTERDUPTRANSACTIONS' + '\n')
            elif repops == 'repatcsn':
                repatcsn = data['repatcsn']
                ssh.stdin.write('start replicat ' + repname + ' ATCSN ' + str(repatcsn) + '\n')
            elif repops == 'repaftercsn':
                repaftercsn = data['repaftercsn']
                ssh.stdin.write('start replicat ' + repname + ' AFTERCSN ' + str(repaftercsn) + '\n')
            elif repops == 'repstop':
                ssh.stdin.write('stop replicat ' + repname + '\n')
            elif repops == 'repforcestop':
                ssh.stdin.write('send replicat ' + repname + ' forcestop' + '\n')
            elif repops == 'repkill':
                ssh.stdin.write('kill replicat ' + repname + '\n')
            elif repops == 'repdel':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
                ssh.stdin.write('delete replicat ' + repname + '\n')
            elif repops == 'upgir':
                domain = data['domain']
                alias = data['alias']
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                ssh.stdin.write('alter replicat ' + repname + ',integrated' + '\n')
            elif repops == 'dwnir':
                domain = data['domain']
                alias = data['alias']
                chktbl = data['chktbl']
                ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
                ssh.stdin.write('alter replicat ' + repname + ' nonintegrated ,CHECKPOINTTABLE ' + chktbl + '\n')
            elif repops == 'repbegin':
                domain = data['domain']
                alias = data['alias']
                beginmode = data['beginmode']
                ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' domain ' + domain + '\n')
                if beginmode == 'Now':
                    ssh.stdin.write('alter replicat ' + repname + ',begin now\n')
                elif beginmode == 'Time':
                    ctvalue = data['ctvalue']
                    ssh.stdin.write('alter replicat ' + repname + ',begin ' + ctvalue + '\n')
                elif beginmode == 'LOC':
                    seqnovalue = data['seqnovalue']
                    rbavalue = data['rbavalue']
                    ssh.stdin.write('alter replicat ' + repname + ',extseqno ' + str(seqnovalue) + ',extrba ' + str(rbavalue) + '\n')
            elif repops == 'repedit':
                repPrm = os.path.join(gg_home, 'dirprm', repname + '.prm')
                with open(repPrm, 'r') as repPrmFile:
                    prmFile = repPrmFile.read()
            (chkRep, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
            with open(agent_home + '/ChkRep.lst', 'w') as repChkFileIn:
                repChkFileIn.write(chkRep)
            with open(agent_home + '/ChkRep.lst', 'r') as repErrFile:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        if mgrOps == 'mgrstart':
            ssh.stdin.write('start manager')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrstop':
            ssh.stdin.write('stop manager!')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrrefresh':
            ssh.stdin.write('refresh manager')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrkill':
            ssh.stdin.write('kill manager')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrchildstatus':
            ssh.stdin.write('send manager childstatus debug')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrportinfo':
            ssh.stdin.write('send manager GETPORTINFO detail')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        elif mgrOps == 'mgrpurgeold':
            ssh.stdin.write('send manager GETPURGEOLDEXTRACTS detail')
            (mgrOps, stderr) = ssh.communicate()
            ssh.kill()
            ssh.stdin.close()
        with open(agent_home + '/MgrOps.lst', 'w') as mgrFileIn:
            mgrFileIn.write(mgrOps)
        with open(agent_home + '/MgrOps.lst', 'r') as mgrFileOut:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('SEND EXTRACT ' + extname + ' SHOWTRANS TABULAR ' + '\n')
        (extShowTrans, stderr) = ssh.communicate()
        ssh.kill()
        ssh.stdin.close()
        with open(agent_home + '/ExtShowTrans.lst', 'w') as ExtShowTransFileIn:
            ExtShowTransFileIn.write(extShowTrans)
        with open(agent_home + '/ExtShowTrans.lst', 'r') as ExtShowTransFileOut:
            ExtShowTransPrint = []
            copy = False
            for line in ExtShowTransFileOut:
                line = line.strip()
                if len(line) > 0 and (not line.startswith('-')):
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
                        ExtShowTransPrint_df = pd.DataFrame(ExtShowTransPrint, columns=['XID', 'Items', 'Extract', 'Redo Thread', 'Start Time', 'SCN', 'Redo Seq', 'Redo RBA', 'Status'])
                        ExtShowTransPrint_df = ExtShowTransPrint_df.to_dict('records')
        return [ExtShowTransPrint_df]

class ggExtSkipTrans(Resource):

    def post(self):
        data = request.get_json(force=True)
        extname = data['extname']
        xid = data['xid']
        xid = xid.lstrip('["').rstrip('"]')
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('SEND EXTRACT ' + extname + ' SKIPTRANS ' + xid + ' FORCE' + '\n')
        (extSkipTrans, stderr) = ssh.communicate()
        ssh.kill()
        ssh.stdin.close()
        with open(agent_home + '/ExtSkipTrans.lst', 'w') as ExtSkipTransFileIn:
            ExtSkipTransFileIn.write(extSkipTrans)
        with open(agent_home + '/ExtSkipTrans.lst', 'r') as ExtSkipTransFileOut:
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
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
        AddRep_Out = []
        (LoginErr, stderr) = ssh.communicate()
        for chktab in chkpttbl:
            chkTabName = chktab
        if 'ERROR' in LoginErr:
            AddRep_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin sourcedb ' + alias + ' , useridalias ' + alias + ' , domain ' + domain + '\n')
            ssh.stdin.write('add replicat ' + repname + ' ' + repmode + ' exttrail ' + trail + ' , checkpointtable ' + chkTabName + '\n')
            (AddRepErr, stderr) = ssh.communicate()
            if 'ERROR' in AddRepErr:
                AddRep_Out.append(AddRepErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                repPrm = os.path.join(gg_home, 'dirprm', repname + '.prm')
                with open(repPrm, 'w') as repFile:
                    repFile.write(currentParamList)
                AddRep_Out.append(AddRepErr)
                if startRepChk is False:
                    ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
                    ssh.stdin.write('start replicat ' + repname)
                    (StartRepErr, stderr) = ssh.communicate()
                    AddRep_Out.append(StartRepErr)
        with open(agent_home + '/AddRepErr.lst', 'w') as repErrFileIn:
            for listline in AddRep_Out:
                repErrFileIn.write(listline)
        with open(agent_home + '/AddRepErr.lst', 'r') as repErrFile:
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
            schema_list = "SELECT DISTINCT ltrim(rtrim(user_name(uid))) AS username  FROM sysobjects  WHERE type = 'U'"
            schema_data_fetch = pd.read_sql_query(schema_list, con)
            schema_data_fetch = schema_data_fetch.to_dict('records')
            cursor = con.cursor()
            cursor.execute('SELECT db_name() AS dbname, @@version AS version  FROM sysobjects  WHERE id = 1')
            dbName = cursor.fetchone()
            if dbName:
                msg['DBNAME'] = dbName[0]
                msg['ProductName'] = dbName[1]
        except Exception as e:
            schema_data_fetch = str(e)
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
            capture_name = 'SELECT CLIENT_NAME FROM cdb_capture'
            capture_name_fetch = pd.read_sql_query(capture_name, con)
        else:
            capture_name = 'SELECT CLIENT_NAME FROM dba_capture'
            capture_name_fetch = pd.read_sql_query(capture_name, con)
        dict_det = "SELECT first_change# FIRST_CHANGE,FIRST_TIME\n                      FROM v$archived_log \n                      WHERE dictionary_begin = 'YES' AND \n                            standby_dest = 'NO' AND\n                            name IS NOT NULL AND \n                            status = 'A'"
        dict_det_fetch = pd.read_sql_query(dict_det, con)
        dict_det_fetch = dict_det_fetch.astype(str)
        return [capture_name_fetch.to_dict('records'), dict_det_fetch.to_dict('records')]

class tableListOnly(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        schemaList = data['schemaList']
        val = selectConn(dbname)
        con = val[0]
        table_fetch = ''
        tabSizeFrame = []
        try:
            cursor = con.cursor()
            i = 1
            bindNames = ','.join((':%d' % i for i in range(len(schemaList))))
            schemas = []
            for schema in schemaList:
                schemas.append(schema)
                cursor.execute("SELECT u.name  AS schema_name, so.name AS table_name FROM sysobjects AS so JOIN sysusers AS u ON so.uid = u.uid WHERE so.type = 'U' AND (so.sysstat2 & 1024) = 0   /* not remote */ AND (so.sysstat2 & 2048) = 0   /* not proxy */ AND u.name = ?       /* filter by schema name */ ORDER BY u.name, so.name", (schema,))
                table_fetch = cursor.fetchall()
                for row in table_fetch:
                    schema_name = row[0]
                    table_name = row[1]
                    full_name = f'{schema_name}.{table_name}'
                    cursor.execute(f"sp_spaceused '{full_name}'")
                    result = cursor.fetchall()[0]
                    columns = [desc[0] for desc in cursor.description]
                    space_info = dict(zip(columns, result))
                    space_info['owner'] = schema_name
                    tabSizeFrame.append(space_info)
        except Exception as e:
               logger.error(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tabSizeFrame, trailPath]

def anonymize_sql(sql: str):
    mappings = {}
    table_match = re.search('CREATE\\s+TABLE\\s+(\\w+)', sql, re.IGNORECASE)
    table_name = table_match.group(1) if table_match else 'UnknownTable'
    dummy_table_name = 'dummy_table_1'
    mappings['table_name'] = table_name
    mappings['dummy_table_name'] = dummy_table_name
    sql = re.sub(f'\\b{table_name}\\b', dummy_table_name, sql)
    start_idx = sql.find('(')
    if start_idx == -1:
        return (sql, mappings)
    bracket = 0
    end_idx = -1
    for i in range(start_idx, len(sql)):
        if sql[i] == '(':
            bracket += 1
        elif sql[i] == ')':
            bracket -= 1
            if bracket == 0:
                end_idx = i
                break
    if end_idx == -1:
        return (sql, mappings)
    column_block = sql[start_idx + 1:end_idx].strip()
    after_block = sql[end_idx + 1:].strip()

    def split_columns(s):
        parts = []
        bracket = 0
        current = []
        for char in s:
            if char == '(':
                bracket += 1
            elif char == ')':
                bracket -= 1
            elif char == ',' and bracket == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
            current.append(char)
        if current:
            parts.append(''.join(current).strip())
        return parts
    column_defs = split_columns(column_block)
    column_mapping = {}
    new_column_lines = []
    constraint_lines = []
    col_index = 1
    for line in column_defs:
        first_word = line.split()[0]
        if re.match('^(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT)', first_word, re.IGNORECASE):
            constraint_lines.append(line)
        else:
            col_name = first_word
            dummy_col = f'col_{col_index}'
            column_mapping[col_name] = dummy_col
            rest = line[len(col_name):].strip()
            new_column_lines.append(f'    {dummy_col} {rest}')
            col_index += 1
    mappings['column_mapping'] = column_mapping
    mappings['reverse_column_mapping'] = {v: k for (k, v) in column_mapping.items()}
    new_constraint_lines = []
    for line in constraint_lines:
        for (orig_col, dummy_col) in column_mapping.items():
            line = re.sub(f'\\b{orig_col}\\b', dummy_col, line)
        new_constraint_lines.append(f'    {line}')
    final_sql = f'CREATE TABLE {dummy_table_name} (\n' + ',\n'.join(new_column_lines + new_constraint_lines) + '\n)' + (f' {after_block}' if after_block else '') + ';'
    return (final_sql, mappings)

def deanonymize_sql(anonymized_sql: str, mappings: dict):
    sql = anonymized_sql
    for (dummy_col, orig_col) in mappings['reverse_column_mapping'].items():
        dummy_col = dummy_col.upper()
        sql = re.sub(f'\\b{dummy_col}\\b', orig_col, sql, re.IGNORECASE)
    sql = re.sub(f"\\b{mappings['dummy_table_name'].upper()}\\b", mappings['table_name'], sql + '\n', re.IGNORECASE)
    return sql

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
        tabSizeFrame = []
        autoQualifySplit = []
        table_fetch = ''
        try:
            cursor = con.cursor()
            i = 1
            bindNames = ','.join((':%d' % i for i in range(len(schemaList))))
            schemas = []
            if LoadName:
                os.umask(0)
                if not os.path.exists(os.path.join(agent_home, LoadName)):
                    os.makedirs(os.path.join(agent_home, LoadName), mode=511)
            for schema in schemaList:
                schemas.append(schema)
                cursor.execute("SELECT u.name  AS schema_name, so.name AS table_name FROM sysobjects AS so JOIN sysusers AS u ON so.uid = u.uid WHERE so.type = 'U' AND (so.sysstat2 & 1024) = 0   /* not remote */ AND (so.sysstat2 & 2048) = 0   /* not proxy */ AND u.name = ?       /* filter by schema name */ ORDER BY u.name, so.name", (schema,))
                table_fetch = cursor.fetchall()
                for row in table_fetch:
                    cursor.execute(f"sp_spaceused '{row[0] + '.' + row[1]}'")
                    result = cursor.fetchall()[0]
                    if int(float(result[2].split()[0])) > int(table_split_chunk_size) / 1024:
                        autoQualifySplit.append(row[0] + '.' + row[1])
                    spaceused_columns = [desc[0] for desc in cursor.description]
                    space_info = dict(zip(spaceused_columns, result))
                    space_info['name'] = row[0] + '.' + row[1]
                    tabSizeFrame.append(space_info)
                df = pd.DataFrame(tabSizeFrame, columns=spaceused_columns)
                expected_headers = ['table_name', 'count', 'tablesize', 'datasize', 'indexsize', 'unused']
                if df.shape[1] == len(expected_headers):
                    df.to_csv(os.path.join(agent_home, LoadName, LoadName + '_' + schema + '.csv'), index=False, header=expected_headers)
                else:
                    logger.error(f'Mismatch: Expected 5 columns, got {df.shape[1]}. Writing without headers.')
                    df.to_csv(os.path.join(agent_home, LoadName, LoadName + '_' + schema + '.csv'), index=False)
        except Exception as e:
            logger.info(str(e))
            tabSizeFrame.append(str(e))
        finally:
            if con:
                cursor.close()
                con.close()
        return [tabSizeFrame, gg_home, autoQualifySplit]

class suppLog(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        result = {}
        try:
            cursor = con.cursor()
            name = dbname.split('@')[0]
            cursor.execute('use {}'.format(name))
            cursor.execute('dbcc gettrunc')
            row = cursor.fetchone()
            if row:
                truncation_status = 'Secondary truncation point is set' if row[1] == 1 else 'Secondary truncation point is NOT set'
                result = {'name': row[5], 'Status': row[1], 'Truncation': truncation_status}
            else:
                result = {'name': 'N/A', 'Status': 'N/A', 'Truncation': 'N/A'}
        except Exception as e:
            result = str(e)
        finally:
            if con:
                cursor.close()
                con.close()
        return [result]

class suppLogSchema(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbname = data['dbname']
        val = selectConn(dbname)
        con = val[0]
        schema_data_fetch = ''
        try:
            schema_list = "SELECT DISTINCT ltrim(rtrim(user_name(uid))) AS username  FROM sysobjects  WHERE type = 'U'"
            schema_data_fetch = pd.read_sql_query(schema_list, con)
            schema_data_fetch = schema_data_fetch.to_dict('records')
        except Exception as e:
            schema_data_fetch = str(e)
        finally:
            if con:
                con.close()
        return [schema_data_fetch]

class readLog(Resource):

    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = []
        with open(os.path.join(agent_home, jobName, jobName + log)) as infile:
            for line in infile:
                retData.append(line)
        return [retData]

class writeLog(Resource):

    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = data['retData']
        with open(os.path.join(agent_home, jobName, jobName + log), 'w') as infile:
            for line in retData:
                infile.write(line)
        return ['Success']

class checkLog(Resource):

    def post(self):
        data = request.get_json(force=True)
        jobName = data['jobName']
        log = data['log']
        retData = ''
        if os.path.exists(os.path.join(agent_home, jobName, jobName + log)):
            retData = True
        else:
            retData = False
        return [retData]

class ggAddSupp(Resource):

    def post(self):
        data = request.get_json(force=True)
        domain = data['domain']
        alias = data['alias']
        tranlevel = data['tranlevel']
        buttonValue = data['buttonValue']
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write(f'dblogin SOURCEDB {alias},useridalias {alias},domain {domain}\n')
        AddSupp_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            AddSupp_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write(f'dblogin SOURCEDB {alias},useridalias {alias},domain {domain}\n')
            if buttonValue == 'add':
                tabNameList = data['tabNameList']
                opts = data['opts']
                with open(os.path.join(agent_home, 'addtrandata.oby'), 'w') as infile:
                    for tabname in tabNameList:
                        infile.write(f'add trandata {tabname} {opts}')
                        infile.write('\n')
                pathTran = os.path.join(agent_home, 'addtrandata.oby')
                ssh.stdin.write(f'obey {pathTran}\n')
                (AddSuppErr, stderr) = ssh.communicate()
                AddSupp_Out.append(AddSuppErr)
            elif buttonValue == 'info':
                tabNameList = data['tabNameList']
                with open(os.path.join(agent_home, 'infotrandata.oby'), 'w') as infile:
                    for tabname in tabNameList:
                        infile.write(f'info trandata {tabname}')
                        infile.write('\n')
                pathTran = os.path.join(agent_home, 'infotrandata.oby')
                ssh.stdin.write(f'obey {pathTran}\n')
                (AddSuppErr, stderr) = ssh.communicate()
                AddSupp_Out.append(AddSuppErr)
            elif buttonValue == 'del':
                tabNameList = data['tabNameList']
                opts = data['opts']
                with open(os.path.join(agent_home, 'deltrandata.oby'), 'w') as infile:
                    for tabname in tabNameList:
                        infile.write(f'delete trandata {tabname} {opts}')
                        infile.write('\n')
                ssh.stdin.write('obey ' + os.path.join(agent_home, 'deltrandata.oby') + '\n')
                (AddSuppErr, stderr) = ssh.communicate()
                AddSupp_Out.append(AddSuppErr)
        with open(os.path.join(agent_home, 'AddSuppErr.lst'), 'w') as suppErrFileIn:
            for listline in AddSupp_Out:
                suppErrFileIn.write(listline)
        with open(os.path.join(agent_home, 'AddSuppErr.lst')) as suppErrFile:
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
                    if 'Transaction logging' in line:
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
        cursor.execute('SELECT user FROM CONN WHERE dbname=:dbname', {'dbname': alias})
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
                    new_line = line.replace(line, 'GGSCHEMA ' + user + '\n')
                    infile.write(new_line)
                else:
                    infile.write(line)
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
        AddHB_Out = []
        (LoginErr, stderr) = ssh.communicate()
        if 'ERROR' in LoginErr:
            AddHB_Out.append(LoginErr)
            ssh.kill()
            ssh.stdin.close()
        else:
            ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
            ssh.stdin.write('dblogin useridalias ' + alias + ' domain ' + domain + '\n')
            if hbTblOps == 'add':
                frequency = data['HBTblFrequency']
                retention_time = data['HBTblRetention']
                purge_frequency = data['HBTblPurgeFrequency']
                ssh.stdin.write('add heartbeattable frequency ' + str(frequency) + ' retention_time ' + str(retention_time) + ' purge_frequency ' + str(purge_frequency) + '\n')
            elif hbTblOps == 'edit':
                frequency = data['HBTblFrequency']
                retention_time = data['HBTblRetention']
                purge_frequency = data['HBTblPurgeFrequency']
                ssh.stdin.write('alter heartbeattable frequency ' + str(frequency) + ', retention_time ' + str(retention_time) + ', purge_frequency ' + str(purge_frequency) + '\n')
            elif hbTblOps == 'del':
                ssh.stdin.write('delete heartbeattable' + '\n')
            (AddHBErr, stderr) = ssh.communicate()
            if 'ERROR' in AddHBErr:
                AddHB_Out.append(AddHBErr)
                ssh.kill()
                ssh.stdin.close()
            else:
                AddHB_Out.append(AddHBErr)
        with open(os.path.join(agent_home, 'AddHBErr.lst'), 'w') as HBErrFileIn:
            for listline in AddHB_Out:
                HBErrFileIn.write(listline)
        with open(os.path.join(agent_home, 'AddHBErr.lst'), 'r') as HBErrFile:
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
            if filename.endswith('.prm'):
                prmpath = os.path.join(gg_home, 'dirprm', filename)
                if os.path.isfile(prmpath):
                    prmfiles.append(filename)
        if not os.path.exists(globalsPath):
            with open(str(globalsPath), 'w') as globalsFile:
                wallet = 'GGSCHEMA TEST \nWALLETLOCATION ' + os.path.join(gg_home, 'dirwlt') + '\n' + 'ALLOWOUTPUTDIR ' + trailPath
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
            if filename.endswith('.rpt'):
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
            if filename.endswith('.dsc'):
                dscpath = os.path.join(gg_home, 'dirrpt', filename)
                if os.path.isfile(dscpath):
                    dscfiles.append(filename)
        dscnames = []
        for filename in os.listdir(PRM_DIRECTORY):
            if filename.endswith('.prm'):
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
            backupfile = dest_file + '.' + datetime.now().strftime('%Y-%m-%d_%H%M%S')
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
            backupfile = dest_file + '.' + datetime.now().strftime('%Y-%m-%d_%H%M%S')
            shutil.copy(dest_file, backupfile)
            with open(dest_file, 'w') as prmFile:
                viewprmfile = prmFile.write(prmContent)
        return ['Parameter File  Saved']

class get_Version(Resource):

    def get(self):
        getVer = subprocess.run([ggsci_bin, '-v'], capture_output=True, text=True).stdout
        with open(os.path.join(agent_home, 'getVersion'), 'w') as verFileIn:
            getVerfile = verFileIn.write(getVer)
        with open(os.path.join(agent_home, 'getVersion')) as verFileOut:
            for (i, line) in enumerate(verFileOut):
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
        processTime = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
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
                            memProcessDet['rssper'] = p.memory_percent(memtype='rss')
                            memProcessDet['vmsper'] = p.memory_percent(memtype='vms')
                            memProcessDet['ussper'] = p.memory_percent(memtype='uss')
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
                                cpuSys = round(cpu_percent * round(t.system_time / cpu_time))
                                cpuUser = round(cpu_percent * round(t.user_time / cpu_time))
                                cpuThreadDet.append({'group': process, 'pid': pid, 'thread': t[0], 'cpu': cpu, 'cpusys': cpuSys, 'cpuuser': cpuUser, 'inctime': processTime})
                            io_counters = p.io_counters()
                            if read_bytes > 0:
                                delta_read_bytes = io_counters[2] - read_bytes
                            else:
                                delta_read_bytes = 0
                            if write_bytes > 0:
                                delta_write_bytes = io_counters[3] - write_bytes
                            else:
                                delta_write_bytes = 0
                            if read_count > 0:
                                delta_read_count = io_counters[0] - read_count
                            else:
                                delta_read_count = 0
                            if write_count > 0:
                                delta_write_count = io_counters[1] - write_count
                            else:
                                delta_write_count = 0
                            disk_usage_process = io_counters[2] + io_counters[3]
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
        processTime = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
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
                            memDet.append({'id': i, 'group': process, 'rss': round(p.memory_full_info()[0] / (1024 * 1024)), 'uss': round(p.memory_full_info()[7] / (1024 * 1024)), 'mem': round(p.memory_percent(), 3), 'inctime': processTime})
                            total_process_mem = total_process_mem + p.memory_percent()
                            cpu_percent = p.cpu_percent(interval=0.2)
                            cpuDet.append({'id': i, 'group': process, 'cpu': cpu_percent, 'inctime': processTime})
                            io_counters = p.io_counters()
                            disk_bytes_process = io_counters[2] + io_counters[3]
                            disk_count_process = io_counters[0] + io_counters[1]
                            ioDet.append({'id': i, 'group': process, 'diskbytes': disk_bytes_process, 'diskcount': disk_count_process, 'inctime': processTime})
                            i = i + 1
                        except psutil.NoSuchProcess:
                            pass
        cpuUser = psutil.cpu_times_percent(interval=0.2)[0]
        cpuSystem = psutil.cpu_times_percent(interval=0.2)[2]
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
        memutil = {'total': total, 'available': available, 'used': used, 'free': free, 'percent': percent, 'swap_tot': swap_tot, 'swap_used': swap_used, 'swap_free': swap_free, 'swap_percent': swap_percent, 'cpuUser': cpuUser, 'cpuSystem': cpuSystem, 'loadavg': loadavg}
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
                passwd = cipher.encrypt(passwd)
                servicename = data['servicename']
                cursor.execute('insert into CONN values(:dbname,:user,:passwd,:servicename)', {'dbname': dbname, 'user': user, 'passwd': passwd, 'servicename': servicename})
                msg = 'Database Details Added'
                conn.commit()
            elif dbButton == 'editDB':
                dbname = data['dbname']
                user = data['username']
                passwd = data['passwd']
                passwd = cipher.encrypt(passwd)
                servicename = data['servicename']
                cursor.execute('insert OR replace into CONN values(:dbname,:user,:passwd,:servicename)', {'dbname': dbname, 'user': user, 'passwd': passwd, 'servicename': servicename})
                msg = 'Database Details Updated'
                conn.commit()
            elif dbButton == 'delDB':
                dbname = data['dbname']
                cursor.execute('delete from CONN where dbname=:dbname', {'dbname': dbname})
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
                    cursor.execute('select db_name() AS DatabaseName, @@servername AS ServerName, @@version AS VersionInfo')
                    result = cursor.fetchone()
                    if result:
                        msg['DBNAME'] = result[0]
                        msg['ProductName'] = result[1]
                        msg['ProductVersion'] = result[2]
                except Exception as e:
                    msg = str(e)
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
                    logger.error(str(e))
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
            cursor.execute('select user,servicename from CONN where dbname=:dbname', {'dbname': dbname})
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
        proc = subprocess.run([ggsci_bin], input='info replicat *\n', text=True, capture_output=True)
        InfoRep = proc.stdout
        infopr_path = os.path.join(agent_home, 'infopr.out')
        with open(infopr_path, mode='w') as outfile2:
            outfile2.write(InfoRep)
        with open(infopr_path, mode='r') as infile:
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
                with open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('useridalias', line, re.IGNORECASE):
                            alias = line.split()[1]
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {'dbname': alias})
        db_row = cursor.fetchone()
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            passwd = cipher.decrypt(passwd)
            servicename = db_row[2]
        con = cx_Oracle.connect(user, passwd, servicename)
        conn.close()
        db_det = "SELECT db.DBid,db.name DBNAME, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,\n                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  \n                           i.instance_number instance,db.database_role,db.current_scn\n                    from v$database db,v$instance i, v$version v\n                    where banner like 'Oracle%' "
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
        bindNames = [':' + str(i + 1) for i in range(len(pidlist))]
        pids = [pid['PROCESS'] for pid in pidlist]
        session_det = 'SELECT s.sid sid,s.serial# serial,p.spid spid,s.sql_id sql_id ,\n                                s.event event ,s.last_call_et call,s.process process \n                                from gv$session s , gv$process p  \n                                where s.paddr = p.addr and s.process in (%s)' % ','.join(bindNames)
        session_det_fetch = pd.read_sql_query(session_det, con, params=[*pids])
        session_det_fetch = pd.merge(session_det_fetch, df)
        session_det_fetch = session_det_fetch.to_dict('records')
        param = {'SESSION_ID': session_det_fetch[0]['SID'], 'SESSION_SERIAL': session_det_fetch[0]['SERIAL']}
        ash_det = "SELECT INST_ID,NVL(event,'ON CPU') event,COUNT(DISTINCT sample_time) AS TOTAL_COUNT\n                             FROM  gv$active_session_history\n                             WHERE sample_time > sysdate - 30/24/60 and SESSION_ID = :SESSION_ID  and SESSION_SERIAL#= :SESSION_SERIAL\n                             group by inst_id,event"
        ash_det_fetch = pd.read_sql_query(ash_det, con, params=[param['SESSION_ID'], param['SESSION_SERIAL']])
        ash_det_fetch = ash_det_fetch.astype(str)
        ash_det_fetch = ash_det_fetch.to_dict('records')
        sql_det = 'select SQL_FULLTEXT from gv$sql where sql_id=:sqlid'
        param = {'sqlid': session_det_fetch[0]['SQL_ID']}
        sql_det_fetch = pd.read_sql_query(sql_det, con, params=[param['sqlid']])
        sql_det_fetch = sql_det_fetch.astype(str)
        sql_det_fetch = sql_det_fetch.to_dict('records')
        safe_pids = min(pids)
        proc = subprocess.run(['pstack', safe_pids], text=True, capture_output=True)
        InfoPstack = proc.stdout
        with open(os.path.join(agent_home, 'crpstack.out'), 'w') as outfile2:
            outfile2.write(InfoPstack)
        with open(os.path.join(agent_home, 'crpstack.out')) as infile:
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
                with open(os.path.join(gg_home, 'dirprm', name), mode='r') as infile:
                    for line in infile:
                        if re.match('useridalias', line, re.IGNORECASE):
                            alias = line.split()[1]
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {'dbname': alias})
        db_row = cursor.fetchone()
        if db_row:
            user = db_row[0]
            passwd = db_row[1]
            servicename = db_row[2]
        con = cx_Oracle.connect(user, passwd, servicename)
        conn.close()
        db_det = "SELECT db.DBid,db.name DBNAME, db.platform_name  ,i.HOST_NAME HOST, i.VERSION,\n                           DECODE(regexp_substr(v.banner, '[^ ]+', 1, 4),'Edition','Standard',regexp_substr(v.banner, '[^ ]+', 1, 4)) DB_Edition,  \n                           i.instance_number instance,db.database_role,db.current_scn\n                    from v$database db,v$instance i, v$version v\n                    where banner like 'Oracle%' "
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
        bindNames = [':' + str(i + 1) for i in range(len(pidlist))]
        pids = [pid['PROCESS'] for pid in pidlist]
        session_det = 'SELECT s.sid sid,s.serial# serial,p.spid spid,s.sql_id sql_id ,s.event event ,s.last_call_et call,s.process process\n                    from gv$session s , gv$process p  \n                    where s.paddr = p.addr and \n                    s.process in (%s)' % ','.join(bindNames)
        session_det_fetch = pd.read_sql_query(session_det, con, params=[*pids])
        session_det_fetch = pd.merge(session_det_fetch, df)
        ggsci_input = f'send {repName},depinfo\n'
        proc = subprocess.run([ggsci_bin], input=ggsci_input, text=True, capture_output=True)
        InfoPRDepInfo = proc.stdout
        output_path = os.path.join(agent_home, 'prdepinfo.out')
        with open(output_path, mode='w') as outfile:
            outfile.write(InfoPRDepInfo)
        with open(output_path, mode='r') as infile:
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
        safe_pid = min(pids)
        proc = subprocess.run(['pstack', safe_pid], text=True, capture_output=True)
        InfoPstack = proc.stdout
        with open(os.path.join(agent_home, 'prpstack.out'), mode='w') as outfile2:
            outfile2.write(InfoPstack)
        with open(os.path.join(agent_home, 'prpstack.out'), mode='r') as infile:
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
        return [db_det_fetch.to_dict('records'), session_det_fetch.to_dict('records'), Scheduler_List, RunningTxn_List, NodeData, WaitGraph, Pstack]

class onepConn(Resource):

    def post(self):
        data = request.get_json(force=True)
        dep_type = data['dep_type']
        onepOps = data['onepOps']
        try:
            ErrPrint = []
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            oneplace_dep = config.get('AGENT_CONFIG', 'AGENT_DEPLOYMENT')
            if dep_type == 'ld':
                dep_url = 'http://' + agent_host + ':' + web_port
                if onepOps == 'add':
                    user = data['user']
                    passwd = data['passwd']
                    passwd = cipher.encrypt(passwd)
                    role = data['role']
                    dep_url = data['dep_url']
                    cursor.execute('insert into ONEPCONN values(:dep,:user,:passwd,:role,:dep_type,\n                          :dep_url)', {'dep': oneplace_dep, 'user': user, 'passwd': passwd, 'role': role, 'dep_type': dep_type, 'dep_url': dep_url})
                elif onepOps == 'edit':
                    user = data['user']
                    passwd = data['passwd']
                    passwd = cipher.encrypt(passwd)
                    cursor.execute('update ONEPCONN set passwd=:passwd where user=:user', {'user': user, 'passwd': passwd})
                elif onepOps == 'del':
                    user = data['user']
                    cursor.execute('delete from  ONEPCONN  where user=:user', {'user': user})
                conn.commit()
                ErrPrint.append('OneP User ' + user + ' Added')
            elif dep_type == 'rd':
                dep_url = data['dep_url']
                user = data['user']
                passwd = data['passwd']
                passwd = cipher.encrypt(passwd)
                dep_url = dep_url + '/oneplogin'
                payload = {'user': user, 'passwd': passwd, 'onepsuid': 'oneplaceusid1980'}
                headers = {'Content-Type': 'application/json'}
                try:
                    r = requests.post(dep_url, json=payload, headers=headers, verify=ssl_verify, timeout=sshTimeOut)
                    SignIn = r.json()[1]
                    oneplace_role = r.json()[2]
                    oneplace_dep = r.json()[4]
                    dep_url = r.json()[3]
                    dbtype = r.json()[5]
                    if SignIn == 'Y' and oneplace_role == 'admin':
                        cursor.execute('insert into ONEPCONN values(:dep,:user,:passwd,:role,:dep_type,\n                                    :dep_url,:dbtype)', {'dep': oneplace_dep, 'user': user, 'passwd': passwd, 'role': oneplace_role, 'dep_type': dep_type, 'dep_url': dep_url, 'dbtype': dbtype})
                        conn.commit()
                        ErrPrint.append('OneP User ' + user + ' Added')
                    else:
                        ErrPrint.append('Invalid Deployment Credentials')
                except requests.exceptions.ConnectionError:
                    ErrPrint.append('Invalid Deployment')
        except sqlite3.DatabaseError as e:
            ErrPrint.append('There is a problem with OneP Database ' + str(e))
        finally:
            if conn:
                conn.close()
        return [ErrPrint]

class onepDep(Resource):

    def get(self):
        ErrPrint = []
        try:
            conn = sqlite3.connect('conn.db')
            dep_det = "SELECT distinct dep,dep_url FROM ONEPCONN where role='admin'"
            dep_det_fetch = pd.read_sql_query(dep_det, conn)
        except sqlite3.DatabaseError as e:
            logger.info('There is a problem with Light Database ' + str(e))
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
            cursor.execute('SELECT distinct dep_url,dbtype FROM ONEPCONN WHERE dep=:dep', {'dep': dep})
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
        cursor.execute("SELECT user,passwd,role FROM ONEPCONN WHERE user=:user and passwd=:passwd\n                               and role='admin' and dep_type='ld'", {'user': user, 'passwd': passwd})
        user_row = cursor.fetchone()
        if user_row:
            val = infoall()
            for i in val[0]:
                if 'mgrport' in i.keys():
                    rmtPort = i['mgrport']
        else:
            rmtPort = 'Invalid Credentials'
            rmtHost = 'Invalid Credentials'
        return [rmtPort, agent_host]

class onepLogin(Resource):

    def post(self):
        data = request.get_json(force=True)
        user = data['user']
        userpasswd = data['passwd']
        onepsuid = data['onepsuid']
        ErrPrint = []
        SignIn = 'N'
        OnepDepName = ''
        OnepRole = ''
        OnepDepUrl = ''
        OnepType = ''
        try:
            conn = sqlite3.connect('conn.db')
            cursor = conn.cursor()
            cursor.execute("SELECT dep,user,passwd,role,dep_url,dbtype FROM ONEPCONN WHERE user = :user and dep_type='ld'", {'user': user})
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

class ggGetProcess(Resource):

    def get(self):
        ExtTrail_Data = []
        ssh = subprocess.Popen([ggsci_bin], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
        ssh.stdin.write('info exttrail' + '\n')
        (InfoExt, stderr) = ssh.communicate(timeout=sshTimeOut)
        with open(os.path.join(agent_home, 'infotrail.out'), mode='w') as outfile:
            outfile.write(InfoExt)
        with open(os.path.join(agent_home, 'infotrail.out'), mode='r') as infile:
            for line in infile:
                if 'Extract Trail' in line:
                    TrailName = line.split(':', 1)[-1].strip()
                elif 'Extract' in line:
                    ExtName = line.split(':', 1)[-1].strip()
                    ExtTrailSet = {'id': ExtName, 'category': TrailName}
                    ExtTrail_Data.append(ExtTrailSet)
        OPlaceDebug(['infotrail.out'])
        return [ExtTrail_Data]

class selectDBConn(Resource):

    def post(self):
        data = request.get_json(force=True)
        dbName = data['dbName']
        conn = sqlite3.connect('conn.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {'dbname': dbName})
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
    cursor.execute('SELECT user,passwd,servicename FROM CONN WHERE dbname=:dbname', {'dbname': dbname})
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
        connection_string = f'DSN={servicename};UID={user};PWD={passwd}'
        try:           
            con = pyodbc.connect(connection_string, autocommit=True)            
            
            db_det = 'SELECT @@version AS version'
            db_det_fetch = pd.read_sql_query(db_det, con)
            db_det = db_det_fetch.to_dict('records')
            db_main_ver = db_det[0]['version']            
        except cx_Oracle.DatabaseError as e:
            db_main_ver = str(e)
            logger.info(str(e))
    return [con, db_main_ver]

def table_itter_rows(dbName, jobName):
    extract = os.path.join(agent_base, 'extract')
    ssh = subprocess.Popen([extract, dbName, jobName], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=0)
    (ILProcStatRate, stderr) = ssh.communicate(timeout=sshTimeOut)

def infoall():
    processTime = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    with open(os.path.join(agent_home, 'infoall'), mode='r') as infile:
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
                    (extlagH, extlagM, extlagS) = line[2].split(':')
                    ExtLag = int(extlagH) * 3600 + int(extlagM) * 60 + int(extlagS)
                    (extchkH, extchkM, extchkS) = line[4].split(':')
                    ExtChkLag = int(extchkH) * 3600 + int(extchkM) * 60 + int(extchkS)
                elif 'VAM' in line:
                    GG_Data.append({'extname': ExtName, 'extstat': ExtStat, 'extlag': ExtLag, 'extchklag': ExtChkLag, 'extIncTime': processTime})
                elif 'File' in line:
                    GG_Data.append({'pmpname': ExtName, 'pmpstat': ExtStat, 'pmplag': ExtLag, 'pmpchklag': ExtChkLag, 'pmpIncTime': processTime})
    with open(os.path.join(agent_home, 'infoall'), mode='r') as infile:
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
                    (replagH, replagM, replagS) = line[2].split(':')
                    RepLag = int(replagH) * 3600 + int(replagM) * 60 + int(replagS)
                    (repchkH, repchkM, repchkS) = line[4].split(':')
                    RepChkLag = int(repchkH) * 3600 + int(replagM) * 60 + int(repchkS)
                elif 'File' in line:
                    GG_Data.append({'repname': RepName, 'repstat': RepStat, 'replag': RepLag, 'repchklag': RepChkLag, 'repIncTime': processTime})
    with open(os.path.join(agent_home, 'infoall'), mode='r') as infile:
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

def write_extract_log(msg):
    log_file = 'convert_output.txt'
    os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
    with open(log_file, 'a', encoding='utf-8', buffering=1) as f:
        f.write(msg)
        f.flush()

def extract_file(zf, info, extract_dir):
    zf.extract(info.filename, path=extract_dir)
    out_path = os.path.join(extract_dir, info.filename)
    perm = info.external_attr >> 16
    os.chmod(out_path, perm)

def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for (i, s) in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return '%sB' % n

def get_embedding(texts):
    if isinstance(texts, str):
        texts = [texts]
    if not texts or not all((isinstance(t, str) and t.strip() for t in texts)):
        raise ValueError('get_embedding() received invalid or empty input.')
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt').to(device)
    with torch.no_grad():
        model_output = reranker_model(**inputs)
        embeddings = model_output.last_hidden_state[:, 0]
        embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings

def rerank_results(query, docs, top_k=3):
    query_emb = get_embedding(f'query: {query}')
    doc_texts = [f'passage: {doc.page_content}' for doc in docs]
    #print(doc_texts)
    doc_embs = get_embedding(doc_texts)
    scores = torch.matmul(query_emb, doc_embs.T).squeeze(0)
    top_indices = torch.topk(scores, k=top_k).indices.tolist()
    reranked_docs = [docs[i] for i in top_indices]
    return reranked_docs

def extract_types_and_query_context(sql_query: str, db, top_k_per_type: int=3, use_reranker: bool=False, rerank_fn=None, verbose: bool=True) -> str:
    
    with open(os.path.join(agent_home,'RAG','rag_search_pattern')) as f:
         rag_search_pattern = f.read().strip()
    
    raw_types = re.findall(rag_search_pattern, sql_query, re.IGNORECASE)
    unique_types = sorted(set(raw_types))
    if verbose:
        write_extract_log(f'🔍 Extracted types: {unique_types}\n')
        
    all_docs = []
    for dtype in unique_types:
        results = db.similarity_search(dtype, k=int(top_k_per_type))
        if use_reranker and rerank_fn:
            results = rerank_fn(dtype, results, top_k=int(top_k_per_type))
            all_docs.extend(results)
        if verbose:
            write_extract_log(f'\n ✅ {dtype}: Retrieved {results} results.\n')
            
    context = '\n'.join([doc.page_content for doc in all_docs])
    write_extract_log('\n-----------------Context---------------\n')
    write_extract_log('\n' + context + '\n')
    
    return context

def normalize_input(query, context):
    query = query.upper()
    context = context.upper()
    context = '\n'.join([line for line in context.strip().splitlines()])
    return (query, context)

def get_sql_rag_chain(llm, retriever, strict_prompt_template, context):
    rag_chain = create_stuff_documents_chain(llm=llm, prompt=strict_prompt_template)

    def execute_rag(input_query):
        (norm_input, norm_context) = normalize_input(input_query, context)
        context_doc = [Document(page_content=norm_context)]
        result = rag_chain.invoke({'input': norm_input, 'context': context_doc}, config={'verbose': True})
        ddl = result['answer'] if isinstance(result, dict) else result
        return ddl
    return execute_rag

def load_prompt_template(file_path: str) -> str:
    """Loads the system prompt from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

class RagDocumentView(Resource):
    def get(self):
        try:
            file_path = os.path.join(agent_home, 'RAG', 'Latest_Claude_Sonnet_Mappings')

            if not os.path.exists(file_path):
                return {"error": "File not found"}, 404

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            return {"content": content}, 200

        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}, 500

class RagPatternView(Resource):
    def get(self):
        try:
            file_path = os.path.join(agent_home, 'RAG', 'rag_search_pattern')

            if not os.path.exists(file_path):
                return {"error": "File not found"}, 404

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            return {"content": content}, 200

        except Exception as e:
            return {"error": str(e)}, 500

class savePattern(Resource):
    def post(self):
        data = request.get_json(force=True)
        new_pattern = data['pattern']
        target_file = os.path.join(agent_home, 'RAG', 'rag_search_pattern')
        backup_dir = os.path.join(agent_home, 'RAG', 'PatternBackups')
        
        try:
            os.makedirs(backup_dir, exist_ok=True)       
            if os.path.exists(target_file):
                timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
                backup_file = os.path.join(backup_dir, f'rag_search_pattern_{timestamp}')
                shutil.copy2(target_file, backup_file) 
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_pattern.strip())
            return {"message": "Saved successfully"}, 200                
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}, 500

class getQueryContext(Resource):
    def post(self):
        data = request.get_json(force=True)
        query = data['query']

        run_sybase_to_oracle_conversion(query)
        
        return("Completed")

class getS3BucketLists(Resource):
    def get(self):
        bucket_list = getS3BucketList()

        return jsonify({"buckets": bucket_list})

class uploadS3Bucket(Resource):
    def post(self):
        data = request.get_json(force=True)
        bucket_name = data['bucket_name']
        file_name = data['file_name']
        s3_key = data['s3_key']
        s3_key = f"uploads/{s3_key}"
        
        result = upload_file_to_s3(file_name, bucket_name, s3_key)
        
        return jsonify({"msg": result})

class getQueryLog(Resource):
    def get(self):
        file_path = os.path.join(agent_home, 'RAG', 'save_db_query_log.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return '⚠️ File not found.'
        except Exception as e:
            logger.error(str(e))
            return f'⚠️ Error reading file: {str(e)}'


class saveChromaDB(Resource):
    def post(self):
        data = request.get_json(force=True)
        new_content = data['content']

        target_file = os.path.join(agent_home, 'RAG', 'Latest_Claude_Sonnet_Mappings')
        backup_dir = os.path.join(agent_home, 'RAG', 'Backups')
        chroma_dir = os.path.join(agent_home, 'RAG', 'chroma_claude_db')
        save_script = os.path.join(agent_home, 'RAG', 'saveClaudeFromat.py')
        log_file = os.path.join(agent_home, 'RAG', 'save_db_log.txt')

        with open(log_file, 'w', encoding='utf-8') as lf:
            lf.write("🔄 Log initialized...\n")

        try:
            os.makedirs(backup_dir, exist_ok=True)
            if os.path.exists(target_file):
                timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
                backup_file = os.path.join(backup_dir, f'Latest_Claude_Sonnet_Mappings_{timestamp}')
                shutil.copy2(target_file, backup_file)

            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content.strip())

            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir)

            saveClaudeFromat.main()            

            return {"message": "Saved successfully"}, 200

        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}, 500

class readSaveDBFile(Resource):
    def get(self):
        file_path = os.path.join(agent_home, 'RAG', 'save_db_log.txt')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return '⚠️ File not found.'
        except Exception as e:
            logger.error(str(e))
            return f'⚠️ Error reading file: {str(e)}'


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
api.add_resource(savePrm_files, '/saveprmfiles')
api.add_resource(savePrm, '/saveprm')
api.add_resource(get_Version, '/ggversion')
api.add_resource(ggAddReplicat, '/ggaddreplicat')
api.add_resource(writeTmpPrm, '/writetmpprm')
api.add_resource(ggViewMgrRpt, '/viewmgrrpt')
api.add_resource(ggRepOps, '/ggrepops')
api.add_resource(ggExtOps, '/ggextops')
api.add_resource(ggMgrOps, '/ggmgrops')
api.add_resource(ggInfoDiagram, '/gginfodiag')
api.add_resource(ggTgtDiag, '/ggtgtdiag')
api.add_resource(ggAddChkptTbl, '/ggaddchkpttbl')
api.add_resource(rhpUploadImage, '/rhpuploadimg')
api.add_resource(listSoftFiles, '/listsoftfiles')
api.add_resource(ViewRunInsFile, '/viewrunins')
api.add_resource(ggGetAllTrails, '/gggettrails')
api.add_resource(getTableName, '/gettablename')
api.add_resource(getKeyConstrants, '/getKeyConstrants')
api.add_resource(getKeyConstraintsLines, '/getKeyConstraintsLines')
api.add_resource(constraintDDLGenAi, '/constraintDDLGenAi')
api.add_resource(getGrantKeyConstraints, '/getGrantKeyConstraints')
api.add_resource(getGrantKeyConstraintsLines, '/getGrantKeyConstraintsLines')
api.add_resource(grantKeyDDLGenAi, '/grantKeyDDLGenAi')
api.add_resource(getIndexConstraints, '/getIndexConstraints')
api.add_resource(getIndexConstraintsLines, '/getIndexConstraintsLines')
api.add_resource(indexDDLGenAi, '/indexDDLGenAi')
api.add_resource(getSchemaName, '/getschemaname')
api.add_resource(getViewName, '/getviewname')
api.add_resource(viewDDLGenAi, '/viewDDLGenAi')
api.add_resource(procDDLGenAi, '/procDDLGenAi')
api.add_resource(readConvertFile, '/readConvertFile')
api.add_resource(trigDDLGenAi, '/trigDDLGenAi')
api.add_resource(getProcName, '/getprocname')
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
api.add_resource(ggILDataSet, '/ggildataset')
api.add_resource(AddAutoILProc, '/addautoilproc')
api.add_resource(ggExtProcStats, '/ggextprocstats')
api.add_resource(ggRepProcStats, '/ggrepprocstats')
api.add_resource(ggILTables, '/ggiltables')
api.add_resource(ggILAction, '/ggilaction')
api.add_resource(ggILJobAct, '/ggiljobact')
api.add_resource(selectDBDet, '/selectdbdet')
api.add_resource(ggGetRMTTrail, '/gggetrmttrail')
api.add_resource(ggProcessAction, '/ggprocessaction')
api.add_resource(selectDBConn, '/selectconn')
api.add_resource(readLog, '/readlog')
api.add_resource(writeLog, '/writelog')
api.add_resource(checkLog, '/checklog')
api.add_resource(savePrm_files_Temp, '/saveprmtmp')
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
api.add_resource(fetchAutomateProcExcel, '/fetchAutomateProcExcel')
api.add_resource(fetchAutomateViewExcel, '/fetchAutomateViewExcel')
api.add_resource(fetchAutomateTableExcel, '/fetchAutomateTableExcel')
api.add_resource(fetchAutomateRoleExcel, '/fetchAutomateRoleExcel')
api.add_resource(fetchAutomateConstraintsExcel, '/fetchAutomateConstraintsExcel')
api.add_resource(fetchAutomateGrantConstraintsExcel, '/fetchAutomateGrantConstraintsExcel')
api.add_resource(fetchAutomateIndexesExcel, '/fetchAutomateIndexesExcel')
api.add_resource(fetchAutomateTriggerExcel, '/fetchAutomateTriggerExcel')
api.add_resource(automateView, '/automateView')
api.add_resource(automateOracleView, '/automateOracleView')
api.add_resource(automateOracleProc, '/automateOracleProc')
api.add_resource(automateOracleTrig, '/automateOracleTrig')
api.add_resource(updateExcel, '/updateExcel')
api.add_resource(updateExcelTable, '/updateExcelTable')
api.add_resource(updateExcelRole, '/updateExcelRole')
api.add_resource(updateExcelConstraints, '/updateExcelConstraints')
api.add_resource(updateExcelGrantConstraints, '/updateExcelGrantConstraints')
api.add_resource(updateExcelIndexes, '/updateExcelIndexes')
api.add_resource(updateExcelView, '/updateExcelView')
api.add_resource(updateExcelTrigger, '/updateExcelTrigger')
api.add_resource(getZoneDetails, '/getZoneDetails')
api.add_resource(updateZoneDetails, '/updateZoneDetails')
api.add_resource(automateTrigger, '/automateTrigger')
api.add_resource(tableListOnly, '/tableListOnly')
api.add_resource(ggGetProcess, '/ggprocesslist')
api.add_resource(getDDLFromTable, '/getddlfromtable')
api.add_resource(getUsersAndRolesFromDB, '/getUsersAndRolesFromDB')
api.add_resource(tableDDLGenAi, '/tableDDLGenAi')
api.add_resource(automateTable, '/automateTable')
api.add_resource(automateRole, '/automateRole')
api.add_resource(automateConstraints, '/automateConstraints')
api.add_resource(automateGrantConstraints, '/automateGrantConstraints')
api.add_resource(automateIndexes, '/automateIndexes')
api.add_resource(getTypeName, '/gettypename')
api.add_resource(getTypeDetails, '/gettypedetails')
api.add_resource(RagDocumentView, '/RagDocumentView')
api.add_resource(RagPatternView, '/RagPatternView')
api.add_resource(savePattern, '/savePattern')
api.add_resource(saveChromaDB, '/saveChromaDB')
api.add_resource(readSaveDBFile, '/readSaveDBFile')
api.add_resource(getQueryContext, '/getQueryContext')
api.add_resource(getS3BucketLists, '/getS3BucketLists')
api.add_resource(uploadS3Bucket, '/uploadS3Bucket')
api.add_resource(getQueryLog, '/getQueryLog')

