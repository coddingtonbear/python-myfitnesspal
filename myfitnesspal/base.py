import six

class MFPBase(object):
    def __str__(self):
        #return self.__unicode__().encode('ascii', 'replace')
        # return unicode for both Python 2.7 and 3.4 PORTING_CHECK
        if six.PY2:
            return self.__unicode__().encode('utf8', 'replace')
        else:
            return self.__unicode__()

    def __repr__(self):
        return '<%s>' % (
            str(self)
        )
