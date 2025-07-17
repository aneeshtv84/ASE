import os
import shutil
import stat
import socket
import sqlite3
import base64
from termcolor import colored
import hashlib
import logging
from tqdm import tqdm
import time
import json
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
logging.basicConfig(
    filename="skyliftai_install.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

def print_banner():
    banner = r"""
                SkyliftAI Agent Installer 
    -----------------------------------------------------
	- Installs start/stop/status control cli
        - Creates an SQLITE database 'conn.db' and creates metadata tables needed for Agent
	- Installs Agent library
	- Generates a config file for interacting with Skylift AI API
	- Logs installation progress
    """
    print(colored(banner, "cyan"))

print_banner()

print("""

	  SkyliftAI Agent - Release 2025.07.01

     Copyright SkyliftAI and all its affiliates
                 
     Starting Install Phase of SkyliftAI Agent
""")

while True:
   onepdep = input('Enter the SkyliftAI Deployment Name - ex (SYBASE) :')
   if not onepdep.strip():
       False
   else:
       break

while True:
   BASE_DIR = input('Enter the path for SkyliftAI Base :')
   if not BASE_DIR.strip():
       False
   else:
       break
while True:
   HOME_DIR = input('Enter the path for SkyliftAI Home :')
   if not HOME_DIR.strip():
       False
   else:
       break
while True:
   GG_HOME = input('Enter the path for Oracle Goldengate Software Home  :')
   if not GG_HOME.strip():
       False
   else:
       break
while True:
   GG_TRAIL = input('Enter the path for Oracle Goldengate Trail Directory :')
   if not GG_TRAIL.strip():
       False
   else:
       break
while True:
   onephost = input('Enter the SkyliftAI HostName/IP/VIP :')
   if not onephost.strip():
       False
   else:
       break
while True:
   server_port = input('Enter the SkyliftAI WebServer Port :')
   if not server_port.strip():
       False
   else:
       break
while True:
   admin_user = input('Enter the SkyliftAI Admin User:')
   if not admin_user.strip():
       False
   else:
       break
while True:
   admin_passwd = input('Enter the SkyliftAI Admin Password:')
   if not admin_passwd.strip():
       False
   else:
       break
while True:
   sybroot = input('Enter the SYBROOT_HOME:')
   if not sybroot.strip():
       False
   else:
       break
while True:
   sybase  = input('Enter the SYBASE_HOME:')
   if not sybase.strip():
       False
   else:
       break
while True:
   sybase_ase  = input('Enter the SYBASE_ASE_HOME:')
   if not sybase_ase.strip():
       False
   else:
       break
while True:
   sybase_ocs  = input('Enter the SYBASE_OCS_HOME:')
   if not sybase_ocs.strip():
       False
   else:
       break
while True:
   sap_jre  = input('Enter the SAP_JRE8_HOME:')
   if not sap_jre.strip():
       False
   else:
       break

while True:
   llm_model_provider = input('Enter the LLM Model Provider (ex - anthropic/amazon/openAI :')
   if not llm_model_provider.strip():
       False
   else:
       break
while True:
   llm_model_id = input('Enter the LLM Model ID ( Amazon Resource Name - arn) :')
   if not llm_model_id.strip():
       False
   else:
       break
while True:
   aws_region = input('Enter the AWS Region  Name (ex - eu-west-1  :')
   if not aws_region.strip():
       False
   else:
       break

while True:
   aws_profile = input('Enter the AWS Profile Name :')
   if not aws_profile.strip():
       False
   else:
       break

embedding_model = 'intfloat/e5-large-v2'
db_search_args = '3'
llm_model_kwargs = { "temperature": 0, "max_tokens": 1024, "top_k": 250, "top_p": 1, "stop_sequences": ["\\nHuman"] }
llm_model_kwargs_str = json.dumps(llm_model_kwargs)
ssl_verify=False

CONFIG_DIR = os.path.join(HOME_DIR,'config')

dep_url = 'http://' + onephost + ':' + server_port

shutil.rmtree(HOME_DIR,ignore_errors=True)
if not os.path.exists(BASE_DIR) : os.makedirs(BASE_DIR)
if not os.path.exists(HOME_DIR) : os.makedirs(HOME_DIR)
if not os.path.exists(GG_HOME) : os.makedirs(GG_HOME)
if not os.path.exists(GG_TRAIL) : os.makedirs(GG_TRAIL)
if not os.path.exists(CONFIG_DIR) : os.makedirs(CONFIG_DIR)

with open(os.path.join(CONFIG_DIR,'skyliftai.cfg'),'w') as infile:
     infile.write('[AGENT_CONFIG]' + '\n' + 'AGENT_DEPLOYMENT_NAME=' + onepdep + '\n' +  'BASE_DIR='+ BASE_DIR + '\n' + 'HOME_DIR='+ HOME_DIR  + '\n' + 'GG_HOME='+ GG_HOME + '\n' +  'GG_TRAIL='+ GG_TRAIL + '\n' + 'AGENT_HOST=' + onephost + '\n' + 'WEB_SERVER_PORT=' + server_port + '\n' + 'AGENT_DEBUG=N' + '\n' + 'TABLE_SPLIT_CHUNK_SIZE=10737418240' + '\n' + 'SYBROOT_HOME=' + sybroot + '\n' + 'SYBASE_HOME=' + sybase + '\n' + 'SYBASE_ASE_HOME='+ sybase_ase + '\n' + 'SYBASE_OCS_HOME=' + sybase_ocs + '\n' + 'SAP_JRE8_HOME=' + sap_jre + '\n' + 'LLM_MODEL_ID=' + llm_model_id + '\n' + 'AWS_PROFILE_NAME=' + aws_profile + '\n' + 'AWS_REGION=' + aws_region + '\n' + 'EMBEDDING_MODEL='+embedding_model +'\n' + 'DB_SEARCH_ARGS='+db_search_args + '\n' + 'LLM_MODEL_PROVIDER=' + llm_model_provider + '\n' + 'LLM_MODEL_KWARGS=' + llm_model_kwargs_str + '\n' + 'SSL_VERIFY=' + str(ssl_verify) ) 

class AESCipher:
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()[:16]
        self.iv = b'OnePlaceMyPlaceV'  # 16 bytes for AES-CBC

    def encrypt(self, raw):
        raw_bytes = raw.encode('utf-8')

        # PKCS7 padding
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

        # Unpad
        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_plain) + unpadder.finalize()

        return data.decode('utf-8')


cipher = AESCipher('SkyliftMyPlaceJamboUrl111019808')

admin_passwd = cipher.encrypt(admin_passwd)


def copy_with_progress(src, dst,desc,buffer_size=16 * 1024 * 1024):  # 16MB chunks
    total_size = os.path.getsize(src)

    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc=desc
    ) as pbar:
        while True:
            buf = fsrc.read(buffer_size)
            if not buf:
                break
            fdst.write(buf)
            pbar.update(len(buf))

dest_file = os.path.join(HOME_DIR,'skyliftai-agent')
copy_with_progress('./app', dest_file,"Installing Skylift AI Agent")
dest_onep = os.path.join(HOME_DIR,'aictl')
copy_with_progress('./skyliftai', dest_onep,"Installing AI Agent Control")
os.chmod(dest_file,0o755)
conn = sqlite3.connect(os.path.join(HOME_DIR,'conn.db'))
cursor = conn.cursor()
cursor.execute('''CREATE TABLE CONN(dbname text NOT NULL PRIMARY KEY,user text,passwd text,servicename text)''')
cursor.execute('''CREATE TABLE ONEPCONN(dep text NOT NULL,user text NOT NULL,passwd text,role text,dep_type text, dep_url text,dbtype text,PRIMARY KEY(user,dep_url))''')
cursor.execute('''CREATE TABLE CHKPT(dbname text NOT NULL,tabname text NOT NULL , PRIMARY KEY(dbname,tabname))''')
cursor.execute('''CREATE TABLE ILEXT(jobname text NOT NULL,srcdep text NOT NULL,domain text,alias text,extname text NOT NULL ,status text,trail text,PRIMARY KEY(jobname,srcdep,extname))''')
cursor.execute('''CREATE TABLE ILREP(jobname text NOT NULL,tgtdep text NOT NULL,domain text,alias text,repname text NOT NULL ,status text,trail text,PRIMARY KEY(jobname,tgtdep,repname))''')
cursor.execute('insert into ONEPCONN values(:dep,:user,:passwd,:role,:dep_type,:dep_url,:dbtype )',{"dep" : onepdep, "user": admin_user,"passwd" : admin_passwd , "role": 'admin', "dep_type" : 'ld' , "dep_url" : dep_url, "dbtype" : 'sybase'})
conn.commit()
cursor.close()
conn.close()
logger.info('Setup Completed Successfully')
print('Setup Completed Successfully')
