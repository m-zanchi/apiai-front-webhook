#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import time
import http.client
from xml.dom import minidom

import os


from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout


def Check_Site_Status(req):
    if req.get("result").get("action") != "Check_Site_Status":
        return {}
    conn = http.client.HTTPSConnection("dh2.aiam.accenture.com")
    yql_query = makeYqlQuery(req)
    print("Query:")
    print(yql_query)

    payload = urlencode({"search" : yql_query})
    print(payload)
    # userAndPass = b64encode(b"username:password").decode("ascii")

    headers = {
    'content-type': "application/x-www-form-urlencoded",
    'authorization': "Basic "+os.environ.get('splunk_auth')+"=="
    }
    conn.request("POST", "/rest-ealadev/services/search/jobs", payload, headers)
    res = conn.getresponse()
    data = res.read()

    sid = minidom.parseString(data).getElementsByTagName('sid')[0].childNodes[0].nodeValue
    
    print("Splunk Job Created SID:" + sid)
    t_end = time.time() + 60
    isdonestatus = '0'
    while (time.time() < t_end):
        print("Querying job status...")
        searchstatus = conn.request('GET',"/rest-ealadev/services/search/jobs/" + sid, headers=headers)
        res = conn.getresponse()
        data2 = res.read()
        props = minidom.parseString(data2).getElementsByTagName('s:key')
        for element in props:
            if element.getAttribute('name') == "isDone":
                isdonestatus = element.childNodes[0].nodeValue
                break
        if (isdonestatus == '1'):
            break
        time.sleep(2)
    if (isdonestatus == '0'):
        print ("Timeout")
        return {}
    print("Splunk Job Finished")
    conn.request("GET", "/rest-ealadev/services/search/jobs/"+sid+"/results?count=0&output_mode=json", headers=headers)
    res = conn.getresponse()
    data3 = res.read()

    webhookres = makeWebhookResult(data3.decode("utf-8"))	
    return webhookres


def makeYqlQuery(req):
#   result = req.get("result")
#    parameters = result.get("parameters")
    return 'sindex="site_monitor" | head 1 | eval last_check=round((now()-_time)/60,0)  | table status, last_check'


def makeWebhookResult(data3):
    print ("data3:" +  data3)
    data = json.loads(data3)
    speech = ""
    for i in data['results']:
         speech = speech + "The web site was " + i["status"] + " last time checked " + i["last_check"] + "minutes ago."
    
    print("Speech:")
    print(speech)
    return {
        "speech": speech,
        "displayText": speech,
        "source": "apiai-weather-webhook-sample"
    }


