import os

class User_Config:
    SESSION_TOKEN_DURATION: int = os.environ.get('SESSION_TOKEN_DURATION', 3600) # from 900 sec to 129600 sec (36 hours)
