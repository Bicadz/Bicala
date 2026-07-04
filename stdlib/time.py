# ================================
# TIME - Time module for Bicala
# ================================
import time as _time_

# Core time functions
def sleep(seconds): 
    """Pause execution for given seconds."""
    return _time_.sleep(seconds)

def ctime(seconds=None):
    """Return the standard 24-character time string."""
    if seconds is None:
        return _time_.ctime()
    return _time_.ctime(seconds)

def perf_counter():
    """High-resolution performance counter for benchmarking."""
    return _time_.perf_counter()

def strftime(format, seconds=None):
    """Convert time to string according to format."""
    if seconds is None:
        return _time_.strftime(format)
    return _time_.strftime(format, _time_.localtime(seconds))

def strptime(string, format):
    """Parse string to time according to format."""
    return _time_.strptime(string, format)

# Local time unit getters
def local_year():
    """Get current local year."""
    return _time_.localtime().tm_year

def local_month():
    """Get current local month (1-12)."""
    return _time_.localtime().tm_mon

def local_day():
    """Get current local day of month (1-31)."""
    return _time_.localtime().tm_mday

def local_weekday():
    """Get current local weekday (0=Monday, 6=Sunday)."""
    return _time_.localtime().tm_wday

def local_hour():
    """Get current local hour (0-23)."""
    return _time_.localtime().tm_hour

def local_minute():
    """Get current local minute (0-59)."""
    return _time_.localtime().tm_min

def local_second():
    """Get current local second (0-59)."""
    return _time_.localtime().tm_sec

# GMT time unit getters
def gmt_year():
    """Get current GMT year."""
    return _time_.gmtime().tm_year

def gmt_month():
    """Get current GMT month (1-12)."""
    return _time_.gmtime().tm_mon

def gmt_day():
    """Get current GMT day of month (1-31)."""
    return _time_.gmtime().tm_mday

def gmt_weekday():
    """Get current GMT weekday (0=Monday, 6=Sunday)."""
    return _time_.gmtime().tm_wday

def gmt_hour():
    """Get current GMT hour (0-23)."""
    return _time_.gmtime().tm_hour

def gmt_minute():
    """Get current GMT minute (0-59)."""
    return _time_.gmtime().tm_min

def gmt_second():
    """Get current GMT second (0-59)."""
    return _time_.gmtime().tm_sec

# Additional useful time functions
def time():
    """Return current time in seconds since epoch."""
    return _time_.time()
