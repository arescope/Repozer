#!../bin/python

from indico.core import db
from MaKaC.conference import CategoryManager, ConferenceHolder

from repoze.catalog.catalog import FileStorageCatalogFactory
from repoze.catalog.catalog import ConnectionManager
 
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
 
import transaction
from persistent import Persistent
from BTrees.OOBTree import OOBTree


from MaKaC.plugins.base import PluginsHolder
from indico.ext.search.repozer.Utils import getRolesValues

import indico.ext.search.repozer.html2text as html2text

db.DBMgr.getInstance().startRequest()
plugin = PluginsHolder().getPluginType('search').getPlugin("repozer")
DBpath = plugin.getOptions()["DBpath"].getValue() 

_initialized = False
factory = None

def initialize_catalog():
    '''
    Create a repoze.catalog instance and specify
    indices of intereset
 
    NB: Use of global variable
    '''
    global _initialized
    global factory
    factory = FileStorageCatalogFactory(DBpath, 'indico_catalog')
    if not _initialized:
        # create a catalog
        manager = ConnectionManager()
        catalog = factory(manager)
        
        # set up indexes
        #### CHANGE HERE TO ADD OR REMOVE INDEXES!!!
        catalog['title'] = CatalogTextIndex('title')
        catalog['titleSorter'] = CatalogFieldIndex('_titleSorter')
        # Descriptions is converted to TEXT for indexing
        catalog['description'] = CatalogTextIndex('_descriptionText')
        catalog['startDate'] = CatalogFieldIndex('startDate')
        catalog['endDate'] = CatalogFieldIndex('endDate')
        catalog['keywords'] = CatalogKeywordIndex('_listKeywords')
        catalog['category'] = CatalogKeywordIndex('_catName')
        # I define rolesVals as Text because I would permit searched for part of names
        catalog['rolesVals'] = CatalogTextIndex('_rolesVals')

        # commit the indexes
        manager.commit()
        manager.close()
        _initialized = True



def buildCatalog(DBpath):

    initialize_catalog()
    manager = ConnectionManager()
    catalog = factory(manager)
    
    # START EXISTING CONTENT INDEXING
    ch = CategoryManager()
    totnum = len(ch.getList())
    curnum = 0
    curper = 0
    for cat in ch.getList():
        for conf in cat.getConferenceList():
            # Check if conference REALLY exist:
            ch = ConferenceHolder()
            #fetch the conference which type is to be updated
            c = None
            try:
                c = ch.getById(conf.id)
            except:
                print "Conference ",conf.id," not indexed"
                pass
            if (c != None):
                # Ictp conferences Id starts with an 'a' char: need to be removed
                intId = int(conf.getId().replace('a','9999'))
                conf._catName = [str(cat.name)]            
                if len(conf._keywords)>0: 
                    conf._listKeywords = conf._keywords.split('\n')
                #conf._catId = cat.id            
                conf._rolesVals = getRolesValues(conf) 
                conf._titleSorter = str(conf.title).lower().replace(" ", "") 
            
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                try:
                    s = h.handle(conf.getDescription().decode('utf8','ignore'))
                    s = s.encode('ascii','ignore')
                except:
                    s = conf.getDescription()
                conf._descriptionText = s
                catalog.index_doc(intId, conf)
        transaction.commit()
        curnum += 1
        per = int(float(curnum)/float(totnum)*100)
        if per != curper:
            curper = per
            print "%s%%" % per
            
    # Pack it when finished
    print "Packing...."
    factory.db.pack()
    factory.db.close()
    
    manager.commit()
    manager.close()
    print "Done."
    
    db.DBMgr.getInstance().endRequest()


if __name__ == '__main__':
     
    buildCatalog(DBpath)  