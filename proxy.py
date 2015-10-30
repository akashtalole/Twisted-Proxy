#!/usr/bin/python
import getopt
import string
import sys

from twisted.internet import protocol
from twisted.internet import reactor,ssl

class ConsoleWriter():

  def write(self, data, type):
    if (data):
      lines = data.split("\n")
      prefix = "<" if type == "request" else ">"
      for line in lines:
        sys.stdout.write("%s %s\n" % (prefix, line))
    else:
      sys.stdout.write("No response from server\n")


class DebugHttpClientProtocol(protocol.Protocol):

  def __init__(self, serverTransport):
    self.serverTransport = serverTransport

  def sendMessage(self, data):
    self.transport.write(data)
  
  def dataReceived(self, data):
    self.data = data
    ConsoleWriter().write(self.data, "response")
    self.serverTransport.write(self.data)
  
  def connectionLost(self, reason):
    self.serverTransport.loseConnection()
    self.transport.loseConnection()


class DebugHttpServerProtocol(protocol.Protocol):

  def dataReceived(self, data):
    self.data = data
    ConsoleWriter().write(self.data, "request")
    client = protocol.ClientCreator(reactor, DebugHttpClientProtocol, self.transport)
    if (str(self.factory.targetPort) == "443"):
      d = client.connectSSL(self.factory.targetHost, self.factory.targetPort,ssl.DefaultOpenSSLContextFactory('server.key', 'server.crt'))
      d.addCallback(self.forwardToClient, client)
    else:
      d = client.connectTCP(self.factory.targetHost, self.factory.targetPort)
      d.addCallback(self.forwardToClient, client)

  def forwardToClient(self, client, data):
    client.sendMessage(self.data)


class DebugHttpServerFactory(protocol.ServerFactory):

  protocol = DebugHttpServerProtocol

  def __init__(self, targetHost, targetPort):
    self.targetHost = targetHost
    self.targetPort = targetPort

def main():
  from twisted.python import log
  log.startLogging(sys.stdout)
  (opts, args) = getopt.getopt(sys.argv[1:], "s:t:h",
    ["source=", "target=", "help"])

  sourcePort, targetHost, targetPort = None, None, None
  for option, argval in opts:
    if (option in ("-h", "--help")):
      usage()
    if (option in ("-s", "--source")):
      sourcePort = int(argval)
    if (option in ("-t", "--target")):
      (targetHost, targetPort) = string.split(argval, ":")
  if (str(targetPort) == "80"):
    reactor.listenTCP(int(sourcePort),DebugHttpServerFactory(targetHost, int(targetPort)))
    reactor.run()
  else:
    reactor.listenSSL(sourcePort,DebugHttpServerFactory(targetHost, int(targetPort)),ssl.DefaultOpenSSLContextFactory('server.key', 'server.crt'))
    reactor.run()


if __name__ == "__main__":
  main()
