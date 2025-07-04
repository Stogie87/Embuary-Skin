from helper import LazyLogger
from monitor import JellySkipMonitor

LOG = LazyLogger(__name__)

LOG.info("Loading service.py")

JellySkipMonitor().start()

