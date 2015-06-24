class MFPBase(object):
    def __str__(self):
        #return self.__unicode__().encode('ascii', 'replace')
        return self.__unicode__()

    def __repr__(self):
        return '<%s>' % (
            str(self)
        )
