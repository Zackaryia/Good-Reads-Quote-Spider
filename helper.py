def dumper(obj): # used because json can not seralize objects
    try:
        return obj.toJSON()
    except:
        return obj.__dict__
