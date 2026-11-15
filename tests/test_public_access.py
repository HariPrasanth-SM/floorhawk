import unittest,hmac,hashlib,secrets
from unittest.mock import Mock
from deploy.modal.gateway import issue_visitor_cookie
class PublicAccessTests(unittest.TestCase):
 def test_unique_signed_secure_noncached_sessions(self):
  key=secrets.token_bytes(32);cookies=[]
  for _ in range(2):
   response=Mock();response.headers={};self.assertIs(issue_visitor_cookie(response,key),response);args=response.set_cookie.call_args;self.assertEqual(args.args[0],'floorhawk-session');self.assertTrue(args.kwargs['httponly']);self.assertTrue(args.kwargs['secure']);self.assertEqual(args.kwargs['samesite'],'strict');self.assertEqual(args.kwargs['max_age'],8*3600);self.assertEqual(response.headers['Cache-Control'],'private, no-store');self.assertEqual(response.headers['Vary'],'Cookie');token=args.args[1];sid,sig=token.split('.');self.assertEqual(len(sid),48);self.assertTrue(hmac.compare_digest(sig,hmac.new(key,sid.encode(),'sha256').hexdigest()));cookies.append(token)
  self.assertNotEqual(*cookies)
 def test_bootstrap_is_explicit_public_root_only(self):
  from pathlib import Path
  text=(Path(__file__).resolve().parents[1]/'deploy/modal/gateway.py').read_text();self.assertIn("os.environ.get('FLOORHAWK_EVENT_ROLE')=='public' and request.method=='GET'and path==''",text);self.assertIn('controls.own(sid,ident)',text)

 def test_cookie_signing_key_is_not_shadowed_in_proxy(self):
  import ast
  from pathlib import Path
  tree=ast.parse((Path(__file__).resolve().parents[1]/'deploy/modal/gateway.py').read_text())
  proxy=next(n for n in ast.walk(tree)if isinstance(n,ast.AsyncFunctionDef)and n.name=='proxy')
  self.assertFalse(any(isinstance(n,ast.Name)and n.id=='key'and isinstance(n.ctx,ast.Store)for n in ast.walk(proxy)))
