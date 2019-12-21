# -*- coding: utf-8 -*-
import hashlib, hmac, json, os, sys, time, requests, math, base64, logging
from datetime import datetime
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

# 密钥参数，替换为用户的secret_id和secret_key
secret_id = "#"
secret_key = "#"

service = "tsf"
host = "tsf.tencentcloudapi.com"
endpoint = "https://" + host
# 地域
region = "ap-beijing"
version = "2018-03-26"
algorithm = "TC3-HMAC-SHA256"

def getHeader(params, action, http_request_method, host=host, version=version, region=region):
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    # ************* 步骤 1：拼接规范请求串 *************
    canonical_uri = "/"
    
    canonical_querystring = ""
    ct = "x-www-form-urlencoded"
    payload = ""
    if http_request_method == "POST":
        canonical_querystring = ""
        ct = "json"
        payload = json.dumps(params)
    canonical_headers = "content-type:application/%s\nhost:%s\n" % (ct, host)
    signed_headers = "content-type;host"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                         canonical_uri + "\n" +
                         canonical_querystring + "\n" +
                         canonical_headers + "\n" +
                         signed_headers + "\n" +
                         hashed_request_payload)
    print(canonical_request)

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                      str(timestamp) + "\n" +
                      credential_scope + "\n" +
                      hashed_canonical_request)
    print(string_to_sign)

    # ************* 步骤 3：计算签名 *************
    # 计算签名摘要函数
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    print(signature)

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + signature)
    print(authorization)

    # 公共参数添加到请求头部
    headers = {
        "Authorization": authorization,
        "Host": host,
        "Content-Type": "application/%s" % ct,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": version,
        "X-TC-Region": region,
    }    
    return headers
    

def get_file_type(path):
    type_dict = {
        ".tar.gz": "tar.gz",
        ".jar": "fatjar",
        ".war": "war",
        ".zip": "zip"
    }
    for suffix in type_dict.keys():
        if path.endswith(suffix):
            return type_dict[suffix]
    else:
        raise Exception("Unknown file type")
    
def getPkgInfo(application_id, pkg_version): 
    params = dict(ApplicationId=application_id, SearchWord=pkg_version)
    headers = getHeader(params, "DescribePkgs", "POST")
    r = requests.post(endpoint, headers=headers, data=json.dumps(params))
    print r.content
    return json.loads(r.content)['Response']['Result']

def getUploadInfo(application_id, pkg_name, pkg_version, pkg_type, pkgDesc="" ):
    params = dict(ApplicationId=application_id, PkgName=pkg_name, PkgVersion=pkg_version, PkgDesc=pkgDesc, PkgType=pkg_type)
    headers = getHeader(params, "GetUploadInfo", "POST")
    r = requests.post(endpoint, headers = headers, data=json.dumps(params))
    # print "-----------------"
    # print r.status_code
    # print r.content
    # print "-----------------"
    cosUploadInfo = json.loads(r.content)['Response']['Result']
    return cosUploadInfo
    
def uploadFile(path, uploadInfo, application_id, app_Id, pkg_version):
    credential = uploadInfo['Credentials']
    secret_id = credential['TmpSecretId']      
    secret_key = credential['TmpSecretKey']    
    token = credential['SessionToken']         
    scheme = 'https'           
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    # 2. 获取客户端对象
    client = CosS3Client(config)
 
    file_name = os.path.basename(path)
    key = app_Id+"/"+application_id+"/"+pkg_version+"/"+file_name 
    response = client.upload_file(
        Bucket=uploadInfo['Bucket'],
        LocalFilePath=path,
        Key= key,
        PartSize=1,
        MAXThread=10,
        EnableMD5=True
    )
    size = os.path.getsize(path)
    md5 = getMd5(path)
    result = 0
    if md5 == '':
        result = 1
    params = dict(ApplicationId=application_id, Md5=md5, PkgId=uploadInfo['PkgId'], Result=0, Size=size)
    headers = getHeader(params, "UpdateUploadInfo", "POST")
    r = requests.post(endpoint, headers = headers, data=json.dumps(params))
    print r.status_code
    print r.content

def getMd5(file_path):
    f = open(file_path,'rb')
    md5_obj = hashlib.md5()
    md5_obj.update(f.read())
    hash_code = md5_obj.hexdigest()
    f.close()
    md5 = str(hash_code).lower()
    return md5
                
def deployGroup(group_id, pkg_id, startup_params):
    params = dict(GroupId=group_id, PkgId=pkg_id, StartupParameters=startup_params)
    headers = getHeader(params, "DeployGroup", "POST")
    r = requests.post(endpoint, headers = headers, data=json.dumps(params))
    print r.status_code
    print r.content
        
if __name__ == "__main__":
    path = sys.argv[1]                      # 本地文件路径
    applicationId = sys.argv[2]             # 应用ID
    pkg_version = sys.argv[3]               # 程序包版本
    appId = sys.argv[4]                     # 用户APPID
    group_id = sys.argv[5]                  # 部署组ID
    startup_params = sys.argv[6]             # 启动参数
    pkg_name = os.path.basename(path)
    pkg_type = get_file_type(pkg_name)
    
    pkgInfo = getPkgInfo(applicationId, pkg_version)
    if pkgInfo['TotalCount'] > 0:
        print "[INFO] {} has uploaded version {}, no need upload".format(applicationId, pkg_version)
        pkgId = pkgInfo['Content'][0]['PkgId']
    else:
        print "[INFO] {} not uploaded version {}, upload now".format(applicationId, pkg_version)
        uploadInfo = getUploadInfo(applicationId, pkg_name, pkg_version, pkg_type)  
        uploadFile(path, uploadInfo, applicationId, appId, pkg_version) 
        pkgId = uploadInfo['PkgId']

    deployGroup(group_id, pkgId, startup_params)
