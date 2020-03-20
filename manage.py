from flask_script import Manager, Server 
from flask_migrate import Migrate, MigrateCommand 
from app import app, db 

migrate = Migrate(app, db) 
manager = Manager(app) 
server = Server(
    host="0.0.0.0", 
    port=3000, 
    use_debugger = True,
    use_reloader = True,
)
manager.add_command("runserver", server)
manager.add_command('db', MigrateCommand) 

if __name__ == '__main__': 
    manager.run()