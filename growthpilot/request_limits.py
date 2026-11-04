"""Bound authenticated data polling within this single-process service."""
import threading
import time
from collections import deque

class ReadLimits:
 def __init__(self, limit=120, window=60, clock=time.monotonic):
  self.limit=limit;self.window=window;self.clock=clock;self.lock=threading.Lock();self.events={}
 def allow(self, username):
  with self.lock:
   current=self.clock()
   # Drop inactive buckets, including disabled accounts.
   for key in list(self.events):
    if not self.events[key] or self.events[key][-1]<=current-self.window: del self.events[key]
   events=self.events.setdefault(username,deque())
   while events and events[0]<=current-self.window: events.popleft()
   if len(events)>=self.limit:return False
   events.append(current);return True
