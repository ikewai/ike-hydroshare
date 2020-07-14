# Script to refresh the Gateway's HydroShare Authentication Token

# What this does:
# 1. Get a new auth token from HydroShare.
# 2. Grab the current HS token metadata object from the Gateway.
# 3. Modify the metadata object with the new values.
# 4. Update the metadata object in the Gateway.

# Libs for Setup
import os

# Libs for Step 1
import requests
import json
import ast
from hs_restclient     import HydroShare, HydroShareAuthOAuth2
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2   import TokenExpiredError

# Libs for Step 2
import urllib
import urllib.parse
import getpass
from   requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings() # pylint: disable=no-member

# Libs for Step 3
from datetime import datetime, timedelta, timezone

DeploymentMode  = os.environ.get('HS_DEPLOYMENT_MODE') # Change to Prod when ready, pull from environment

# Constants for Step 1. Get ID and Secret from https://www.hydroshare.org/o/applications/
HSClientID      = os.environ.get('HS_CLIENT_ID')
HSClientSecret  = os.environ.get('HS_CLIENT_SECRET')
HSClientUser    = os.environ.get('HS_CLIENT_USER')
HSClientPass    = os.environ.get('HS_CLIENT_PASS')
HSAccessURL     = 'https://www.hydroshare.org/o/token/'

# Constants for Step 2. Get Token from Subscriptions portion of API Store
IkeServer      = ('agaveauth' if DeploymentMode == 'Dev' else 'ikeauth')
print(IkeServer)
IkeMetaURL     = 'https://'+IkeServer+'.its.hawaii.edu/meta/v2/data/'
IkeToken       = os.environ.get('IKE_TOKEN')
IkeHSTokenUUID = ('4550274236533370390-242ac1110-0001-012' if DeploymentMode == 'Dev' else '295018900705120746-242ac1110-0001-012')


# 1. Get a new token from HydroShare.
def getHydroShareToken(HSAccessURL, HSClientUser, HSClientPass, HSClientID, HSClientSecret):
    # Returns a token in python dictionary form.
    data = {
        'grant_type'    : 'password'   ,
        'username'      : HSClientUser ,
        'password'      : HSClientPass ,
        'client_id'     : HSClientID   ,
        'client_secret' : HSClientSecret
    }
    InitialAuth = requests.post(HSAccessURL, data=data)
    AuthData    = InitialAuth.text
    AccessToken = ast.literal_eval(AuthData)
    return AccessToken

# 2. Grab the current HS token metadata object from the Gateway.
def getMetadata(IkeToken, IkeMetaURL, IkeHSTokenUUID):
    headers = {
        'authorization' : "Bearer " + IkeToken,
        'content-type'   : "application/json"  ,
    }
    res  = requests.get(
        IkeMetaURL+IkeHSTokenUUID,
        headers=headers,
        verify=False
    )
    resp = json.loads(res.content)
    if resp['status'] == 'success':
        return resp['result']
    else:
        return resp

# 3. Modify the metadata object in memory.
def modifyMetadata(IkeHSTokenMeta, NewHSToken):
    IkeHSTokenMeta['value']['access_token']    =  NewHSToken['access_token']
    IkeHSTokenMeta['value']['expiration_date'] =  (datetime.now(timezone.utc) + timedelta(seconds=NewHSToken['expires_in'])).isoformat(sep='T', timespec='seconds')
    return IkeHSTokenMeta

# 4. Update the metadata object in the Gateway.
def updateMetadata(IkeToken, IkeHSTokenUUID, IkeHSTokenMeta):
    headers = {
        'authorization' : "Bearer " + IkeToken,
        'content-type'  : "application/json"  ,
    }
    res = requests.post(
        IkeMetaURL+IkeHSTokenUUID,
        json    = IkeHSTokenMeta ,
        headers = headers        ,
        verify  = False
    )
    resp = json.loads(res.content)
    if resp['status'] == 'success':
        return resp['result']
    else:
        return resp

## Begin Procedure ##
# 1. Get a new token from HydroShare.
NewHSToken = getHydroShareToken(HSAccessURL, HSClientUser, HSClientPass, HSClientID, HSClientSecret)

# 2. Grab the current HS token metadata object from the Gateway.
IkeHSTokenMeta = getMetadata(IkeToken=IkeToken, IkeMetaURL=IkeMetaURL, IkeHSTokenUUID=IkeHSTokenUUID)
if DeploymentMode == 'Dev':
    print("Pre-Update:  token: " + IkeHSTokenMeta['value']['access_token'] + " | expiration: " + IkeHSTokenMeta['value']['expiration_date'])

# 3. Modify the metadata object in memory.
NewIkeHSTokenMeta = modifyMetadata(IkeHSTokenMeta=IkeHSTokenMeta, NewHSToken=NewHSToken)

# 4. Update the metadata object in the Gateway.
ResultOfMetaUpdate = updateMetadata(IkeToken=IkeToken, IkeHSTokenUUID=IkeHSTokenUUID, IkeHSTokenMeta=NewIkeHSTokenMeta)

# 5. (optional) Confirm that the object now matches the new token.
UpdatedHSTokenMeta = getMetadata(IkeToken=IkeToken, IkeMetaURL=IkeMetaURL, IkeHSTokenUUID=IkeHSTokenUUID)
if DeploymentMode == 'Dev':
    print("Post-Update: token: " + UpdatedHSTokenMeta['value']['access_token'] + " | expiration: " + UpdatedHSTokenMeta['value']['expiration_date'])
## End Procedure ##