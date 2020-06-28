import six


class MFPBase:
    def __str__(self):
        # return self.__unicode__().encode('ascii', 'replace')
        # return unicode for both Python 2.7 and 3.4 PORTING_CHECK
        return self.__unicode__()

    def __repr__(self):
        return "<%s>" % (str(self))
