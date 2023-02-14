import os

working_dir = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
db_dir = os.path.join(working_dir, 'data.db')
