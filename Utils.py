# -*- coding: utf-8 -*-
##
##
## This file is added for Indexing Indico's contents with repoze.catalog
## Copyright (C) 2013 Ictp.
from lxml import html
from datetime import datetime
from pytz import timezone
import MaKaC.common.info as info

def get_type(object, default):
    return type(object).__name__  


def getRolesValues(obj):
    # convert roles to list of values only
    vals = []
    if hasattr(obj,'_roles'):
        sroles = str(obj._roles).replace('false','False').replace('true','True')
        if sroles != '[]':
            lroles = eval(sroles)
            vals = []
            for r in lroles:
                child = r['child']                
                for c in child:
                    if 'familyName' in c:
                        vals.append(c['familyName'])
                    if 'firstName' in c:
                        vals.append(c['firstName'])
            return ','.join(vals)
    return ''



def getTextFromHtml(txt):
    s = ''
    if txt: 
        try:
            sp = html.fromstring(txt).text_content()
            s = ''.join(sp.splitlines())
        except: 
            s = txt
    return s
    
    
    
def getFid(obj):    
    """
    fid = FullID = confId | SessionId | ContributionId | MaterialId
    """
    fid = "|||"
    cname = type(obj).__name__
    if hasattr(obj, '__type__'): cname = obj.__type__
    if cname == 'Conference':
        fid = str(obj.getId()+"|||")
    if cname == 'Contribution':
        conf = obj.getConference()
        fid = str(conf.getId()) + "|"
        if obj.getSession():
            fid += str(obj.getSession().getId())
        fid += "|"+str(obj.getId()) + "|" 
    if cname == 'Material':      
        conf = obj.getConference()        
        fid = str(conf.getId()) + "|"        
        if obj.getSession():
            fid += str(obj.getSession().getId())
        fid += "|"
        if obj.getContribution():
            fid += str(obj.getContribution().getId())
        fid += "|" + str(obj.getId()) 
    return fid


def getCatFid(obj):  
    catList = []
    catowner = obj.getOwner()
    catId = obj.getOwner().getId()
    catList.append(catId)
    catowner = catowner.getOwner()
    while catowner:
        catId += "|"+catowner.getId()
        if catowner.name != 'Home':
            catList.append(catId.decode('utf8'))
        catowner = catowner.getOwner()
    return catList

    

def getTextFromAvatar(alist):
    data = []
    for s in alist:
        t = type(s).__name__
        if t in ['ContributionParticipation','ConferenceChair']:            
            name = s.getFullNameNoTitle() + ' ' + s.getAffiliation()
        else:
            name = s.getValues()['familyName']
            if hasattr(s.getValues(), 'firstName'): name += ' ' + s.getValues()['firstName']
            if hasattr(s.getValues(), 'affiliation'): name += ' ' + s.getValues()['affiliation']
        data.append(name)
    if data: return str(' '.join(data))
    return '' 


def getTypeFromFid(fid):
    confId, sessionId, talkId, materialId = fid.split("|")
    if materialId: return 'Material'
    if talkId: return 'Contribution'
    if sessionId: return 'Session'
    if confId: return 'Conference' 