## Models using

[Tutorial sources here](https://alembic.sqlalchemy.org/en/latest/tutorial.html#creating-an-environment)

Steps to use models in project:
1. Init alembic in the root of directory:
   ```bash
   alembic init alembic
   ```
2. Fill `sqlalchemy.url` in file *alembic/alembic.ini* as URL to connect to the database.  
Examples:  
`sqlite+aiosqlite://~/tmp/db.sqlite3`,  
`postgresql+asyncpg://nick:password123@localhost/database123`,  
`mysql+asyncmy://nick:password123@localhost/database123`.  
Though better to set it via environment variables.
3. Create python module with models. [See example](https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models)
4. For using alembic, need to set `target_metadata = Base.metadata` in the file *alembic/env.py*.    
   `Base` is imported from the newly created module from the last step.

#### Create migration
```bash
alembic revision --autogenerate -m "Name of migration"
```

#### Update database with last migration
```bash
alembic upgrade head
```
