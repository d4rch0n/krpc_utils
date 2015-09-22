''' krpc_utils
'''
import krpc

def connect(name='client'):
    return krpc.connect(name=name)
