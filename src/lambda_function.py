import boto3
import logging
import sys

logger = logging.getLogger()
logger.setLevel( logging.INFO )

def setids(response,ids):

        for rev in response['Reservations']:
                for instance in rev['Instances']:
                        ids.append(instance['InstanceId'])
                

def lambda_handler(event, context):
        client = boto3.client('ec2', event['region'])

        # region内の全インスタンス取得する
        all_instanceids = []
        response = client.describe_instances()
        setids(response, all_instanceids)
        logger.debug( all_instanceids )
        
        # 停止させないタグが付与されているインスタンスを取得する
        nostop_instanceids = []
        response = client.describe_instances(
                Filters=[{'Name':'tag:autostop', 'Values': ['false']}]
        )
        setids(response, nostop_instanceids)
        logger.debug("nonstop")
        logger.debug(nostop_instanceids)

        # スポットインスタンスを取得する
        spot_instanceids = []
        response = client.describe_instances(
                Filters=[{'Name':'instance-lifecycle','Values':['spot']}]
        )
        setids(response, spot_instanceids)
        logger.debug(spot_instanceids)

        # 停止させてもいいインスタンスIDを取得する
        # 停止させてもいいインスタンス = 全インスタンス - タグがついている - スポットインスタンス
        targetids = set(all_instanceids) - \
            set(nostop_instanceids) - set(spot_instanceids)
        
        logger.info("停止させるインスタンスID")
        logger.info(targetids)
        # 停止させる
        client.stop_instances(InstanceIds=list(targetids))

        nonstop_spotinstanceids = []
        response = client.describe_instances(
            Filters=[
                        {'Name': 'instance-lifecycle', 'Values': ['spot']},
                        {'Name': 'tag:autostop', 'Values': ['false']}
                ]
        )
        setids(response, nonstop_spotinstanceids)
        targetids = set(spot_instanceids)-set(nonstop_spotinstanceids)
        logger.info("終了させるスポットインスタンス")
        logger.info(targetids)
        # 終了させる
        client.terminate_instances(InstanceIds=list(targetids))

        return("finished")
