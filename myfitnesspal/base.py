class MFPBase(object):
    def __str__(self):
        return self.__unicode__().encode('ascii', 'replace')

    def __repr__(self):
        return '<%s>' % (
            str(self)
        )
