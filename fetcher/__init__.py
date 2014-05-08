import pycurl
import sys
import time

from cStringIO import StringIO


def fetch(requests, concurrent=50, timeout_ms=1000, follow_redirects=True):
  multi = pycurl.CurlMulti()

  # Sadly, we need to track of pending curls, or they'll get CG'd and
  # mysteriously disappear. Don't ask me!
  curls            = []
  num_handles       = 0
  unscheduled_reqs = True

  while num_handles or unscheduled_reqs or curls:
    # If the concurrency cap hasn't been reached yet, another request can be
    # pulled off and added to the multi.
    if unscheduled_reqs and num_handles < concurrent:
      try:
        url, payload = requests.next()
      except StopIteration:
        unscheduled_reqs = False
        continue

      body = StringIO()

      curl = pycurl.Curl()
      curl.setopt(pycurl.URL, url)
      curl.setopt(pycurl.WRITEFUNCTION, body.write)
      curl.setopt(pycurl.TIMEOUT_MS, timeout_ms)
      curl.setopt(pycurl.CONNECTTIMEOUT_MS, timeout_ms)
      curl.setopt(pycurl.USERAGENT, 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64;' +\
        ' rv:21.0) Gecko/20100101 Firefox/21.0')

      if follow_redirects:
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
      else:
        curl.setopt(pycurl.FOLLOWLOCATION, 0)

      curl.body    = body
      curl.payload = payload
      curls.append(curl)
      multi.add_handle(curl)

    # Perform any curl requests that need to happen.
    ret = pycurl.E_CALL_MULTI_PERFORM
    while ret == pycurl.E_CALL_MULTI_PERFORM:
      ret, num_handles = multi.perform()

    # Wait at maximum for two seconds for a file descriptor to become available.
    # Restart if not.
    ret = multi.select(2.0)
    if ret == -1:
      continue

    # Finally, deal with any complete or error'd curls that may have been
    # resolved in this loop.
    while True:
      num_q, ok_list, err_list = multi.info_read()
      for c in ok_list:
        yield True, (c.payload, c.body.getvalue())
        multi.remove_handle(c)
        curls.remove(c)

      for c, errno, errmsg in err_list:
        error = "%d: %s" % (errno, errmsg)
        yield False, (c.payload, error, c.getinfo(pycurl.EFFECTIVE_URL))
        multi.remove_handle(c)
        curls.remove(c)

      if not num_q:
        break

def main(count, url):
  print 'Getting %s from %s' % (count, url)

  requests = ((url, 'req-%s' % i) for i in range(count))
  start =  time.time()
  for ok, resp in fetch(requests, concurrent=100):
    print ok, resp
  delta = time.time() - start
  print '%.02f req/s' % (count / delta)

if __name__ == '__main__':
  count = int(sys.argv[1])
  url   = sys.argv[2]
  sys.exit(main(count, url))
