 #!/usr/bin/python
#coding:utf-8

try: import httplib
except ImportError:
    import http.client as httplib
import sys
import urllib
import urllib2
import time
import json
import itertools
import mimetypes
import base64
import hmac
import uuid
from hashlib import sha1




class AliyunMonitor:


    def __init__(self,url):
        self.access_id = 'access_id'
        self.access_secret = 'access_secret'
        self.url = url
    ##签名
    def sign(self,accessKeySecret, parameters):
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k,v) in sortedParameters:
            canonicalizedQueryString += '&' + self.percent_encode(k) + '=' + self.percent_encode(v)

        stringToSign = 'GET&%2F&' + self.percent_encode(canonicalizedQueryString[1:]) #使用get请求方法

        h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def percent_encode(self,encodeStr):
        encodeStr = str(encodeStr)
        res = urllib.quote(encodeStr.decode(sys.stdin.encoding).encode('utf8'), '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def make_url(self,params):
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        parameters = {
            'Format' : 'JSON',
            'Version' : '2014-08-15',
            'AccessKeyId' : self.access_id,
            'SignatureVersion' : '1.0',
            'SignatureMethod' : 'HMAC-SHA1',
            'SignatureNonce' : str(uuid.uuid1()),
            'TimeStamp' : timestamp,
        }
        for key in params.keys():
            parameters[key] = params[key]

        signature = self.sign(self.access_secret,parameters)
        parameters['Signature'] = signature
        url = self.url + "/?" + urllib.urlencode(parameters)
        return url

    def do_request(self,params):
        url = self.make_url(params)
        print(url)
        request = urllib2.Request(url)
        try:
            conn = urllib2.urlopen(request)
            response = conn.read()
        except urllib2.HTTPError, e:
            print(e.read().strip())
            raise SystemExit(e)
        try:
            obj = json.loads(response)
        except ValueError, e:
            raise SystemExit(e)
        print obj
