''' krpc_utils
'''
import krpc
from .vessel import Vessel

def connect(name='client'):
    return krpc.connect(name=name)
