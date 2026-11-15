"""Local inference permits loopback IPC only; no provider, telemetry or DNS egress.
The app has one inference worker. This scoped process guard preserves concurrent
loopback health/resource traffic and restores transport before a Hybrid request.
"""
import contextlib,socket,threading
LOCK=threading.RLock()
class OfflineViolation(RuntimeError):pass
@contextlib.contextmanager
def local_network_guard():
 with LOCK:
  connect=socket.socket.connect;getaddrinfo=socket.getaddrinfo;attempts=[]
  def allowed(host):return host in ('127.0.0.1','localhost','::1',None,'')
  def guarded_connect(sock,address):
   if isinstance(address,tuple) and not allowed(address[0]):attempts.append('socket');raise OfflineViolation('External connection blocked in Local mode')
   return connect(sock,address)
  def guarded_dns(host,*args,**kwargs):
   if not allowed(host):attempts.append('DNS');raise OfflineViolation('External DNS blocked in Local mode')
   return getaddrinfo(host,*args,**kwargs)
  socket.socket.connect=guarded_connect;socket.getaddrinfo=guarded_dns
  try:yield attempts
  finally:socket.socket.connect=connect;socket.getaddrinfo=getaddrinfo
