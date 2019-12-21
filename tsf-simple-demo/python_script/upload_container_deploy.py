# -*- coding: utf-8 -*-
# tencentcloud-sdk-python

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tsf.v20180326 import tsf_client, models

import sys
import json
import os
import time

# 密钥参数，替换为用户的secret_id和secret_key
secret_id = "#"
secret_key = "#"
# docker build 命令
docker_build_command = "#"
# docker push 命令
docker_push_command = "#"
# 地域
region = "ap-guangzhou"

endpoint = "tsf.tencentcloudapi.com"

client = None


def docker_build():
    os.system(docker_build_command)


def docker_push():
    os.system(docker_push_command)


def init_client():
    try:
        cred = credential.Credential(secret_id, secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = endpoint
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = tsf_client.TsfClient(cred, region, clientProfile)
        return client
    except TencentCloudSDKException as err:
        print(err)
        raise TencentCloudSDKException


def describe_container_group_detail(group_id):
    req = models.DescribeContainerGroupDetailRequest()
    params = '{"GroupId":"' + group_id + '"}'
    req.from_json_string(params)

    resp = client.DescribeContainerGroupDetail(req)
    print(resp.to_json_string())
    return resp


def deploy_container_group(container_group_detail_resp, tag_name):
    params = dict(GroupId=container_group_detail_resp.Result.GroupId,
                  Server=container_group_detail_resp.Result.Server,
                  Reponame=container_group_detail_resp.Result.Reponame,
                  TagName=tag_name,
                  InstanceNum=container_group_detail_resp.Result.InstanceNum,
                  CpuRequest=container_group_detail_resp.Result.CpuRequest,
                  MemRequest=container_group_detail_resp.Result.MemRequest)

    req = models.DeployContainerGroupRequest()
    req.from_json_string(json.dumps(params))
    resp = client.DeployContainerGroup(req)
    print(resp.to_json_string())


def get_tag_name():
    tag_name = ""
    try:
        docker_build_tag_name = docker_build_command[docker_build_command.
                                                     rfind(":") + 1:]
        docker_push_tag_name = docker_push_command[docker_push_command.
                                                   rfind(":") + 1:]
        if docker_build_tag_name == docker_push_tag_name:
            tag_name = docker_build_tag_name
        else:
            raise ValueError('Docker build tag name 和 push tag name 不一致')
    except Exception:
        raise ValueError('Docker tag name 异常')
    return tag_name


if __name__ == "__main__":

    # 部署组ID
    group_id = sys.argv[1]

    # 镜像版本名称,如v1
    tag_name = get_tag_name()

    # group_id = "group-zvw397wa"
    # tag_name = "docker-consumer"
    docker_build()
    docker_push()
    client = init_client()
    container_group_detail_resp = describe_container_group_detail(group_id)
    # TODO 刚push的镜像有一定延迟，需要加入等待镜像逻辑
    # 目前没有查询镜像版本接口，粗暴延迟
    time.sleep(10)
    deploy_container_group(container_group_detail_resp, tag_name)
