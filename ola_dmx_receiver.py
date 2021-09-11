from ola.ClientWrapper import ClientWrapper
from functools import partial

def NewData(universe, data):
    print universe, data[0]

wrapper = ClientWrapper()
client = wrapper.Client()
for universe in [1,2]:
	client.RegisterUniverse(universe, client.REGISTER, partial(NewData, universe))
wrapper.Run()
