from peewee import *
import datetime,configparser
confs=configparser.ConfigParser()
confs.read("configs.ini")
database = SqliteDatabase(confs.get("AppConfig","dbname"), pragmas={'journal_mode': 'wal'})
class BaseModel(Model):
    class Meta:
        database=database
class DataTable(BaseModel):
    Key=AutoField(primary_key=True)
    Val=TextField()
    TID=IntegerField()#TransactionID
    created_at=DateTimeField(default=datetime.datetime.now())
class tbl_TCPConnection(BaseModel):
        id=AutoField()
        source_ip=CharField()
        destination_ip=CharField()
        source_port=IntegerField()
        destination_port=IntegerField()
        action=CharField(30)#storeDB|storefile|send
        enctype=CharField(null=True)

def init():
    database.create_tables([DataTable,tbl_TCPConnection],safe=True)

init()