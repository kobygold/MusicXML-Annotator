import os
import pickle

def setConfigVar(name,data):
    # save variable to myPersistent config file

    initFile = 'myPersistent.dat'
    initFolder = myprefdir()
    initPath = initFolder + "\\" + initFile

    if os.path.isfile(initPath):
        with open(initPath, 'rb') as f:
            obj = pickle.load(f)
            obj[name] = data

        with open(initPath, 'wb') as f:
            pickle.dump(obj, f)

    else: # file does not exist, try to create it with the given data as field
        obj = dict()
        obj[name] = data
        with open(initPath, 'wb') as f:
            pickle.dump(obj, f)


def getConfigVar(name,default=None):
    # get variable from myPersistent config file

    initFile = 'myPersistent.dat'
    initFolder = myprefdir()
    initPath = initFolder + "\\" + initFile

    if os.path.isfile(initPath):
        data = default
        with open(initPath, 'rb') as f:
            obj = pickle.load(f)
            data = obj.get(name)
            if data==None:
                data = default
        return data
    else:
        print('cannot find myPersistent config file: ' + initPath + ' will try to create it now')
        if default!=None:  # write the default value to file, to create the file for the first time
            setConfigVar(name, default)
        return default




def myprefdir():
    myprefdir = os.environ.get('APPDATA')
    if myprefdir==None:
        myprefdir = os.environ.get('HOME') # support linux (needed?)
        if myprefdir==None:
            myprefdir = "c:\\tmp"
    return myprefdir
