#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()


import json
import os
import boto3
from botocore.exceptions import ClientError

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout


def Start_Instance(req):
    print ("Getting Request")
    result = req.get("result")
    parameters = result.get("parameters")
    instance_action = parameters.get("instance_action")

    instance_id = "i-0a656796258609de1"
    print ("Starting EC2 Management")
    result = manageEC2instance(instance_action,instance_id,"eu-west-1")
    print("EC2 Managed")
    print (result)
    print(json.dumps(result, indent=4))
    print("Formatting Results")
    res = makeWebhookResult(instance_action, result)
    print("Results Formatted")
    return res

def manageEC2instance(instance_action, instance_id, _region_name):

    ec2 = boto3.client('ec2', _region_name)
    print("boto3 client created for action=" + instance_action)

    if instance_action == 'ON':
        # Do a dryrun first to verify permissions
        try:
            ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
        except Exception as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        try:
            print("executing action")
            response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
            return(response)
        except ClientError as e:
            print(e)
    else:
        # Do a dryrun first to verify permissions
        try:
            print("executing action")
            ec2.stop_instances(InstanceIds=[instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances witout dryrun
        try:
            response = ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
            return (response)
        except ClientError as e:
            print(e)
    return


def makeWebhookResult(instance_action, result):

    root = 'StoppingInstances'
    if instance_action == 'ON':
        root = 'StartingInstances'

    jroot = result.get(root)
    if jroot is None:
        return {}

    InstanceId = jroot[0].get('InstanceId')
    if InstanceId is None:
        return {}

    PreviousState = jroot[0].get('PreviousState')
    if PreviousState is None:
        return {}

    CurrentState = jroot[0].get('CurrentState')
    if CurrentState is None:
        return {}

    print("Creating speech")

    speech = "The server was " + PreviousState.get('Name') + " and now is " + CurrentState.get('Name') + "."

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-ec2-webhook"
    }


