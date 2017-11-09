from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select, and_

class PullDB:
    def __init__(self, name):
        self.name = name   
        engine = create_engine('sqlite:///%s' % self.name)

        with engine.connect() as connection:
            meta = MetaData(engine)
        
            self.projects = Table('Projects', meta,
                Column('Id', Integer, primary_key=True),
                Column('Owner', String),
                Column('Repo', String),                
                sqlite_autoincrement=True
            )
            
            self.pulls = Table('PullRequests', meta,
                Column('Id', Integer, primary_key=True),
                Column('Owner', String),
                Column('Repo', String),
                Column('Number', Integer),
                Column('Comments', Integer),
                Column('ReviewComments', Integer),
                Column('Commits', Integer),
                sqlite_autoincrement=True
            )

            self.commits = Table('Commits', meta,
                Column('PullRequest', Integer, ForeignKey('PullRequests.Id')),
                Column('Sha', String, primary_key=True)
            )

            self.comments = Table('Comments', meta,                
                Column('PullRequest', Integer, ForeignKey('PullRequests.Id')),                
                Column('Id', Integer, primary_key=True),
                Column('CreatedAt', String),
                Column('Text', String)
            )
            
            meta.create_all(engine)            
        self.connection = engine.connect() 

    def get_pull_request_id(self, owner, repo, number):
        selection = select([self.pulls]).where(and_(self.pulls.columns.Owner == owner, self.pulls.columns.Repo == repo, self.pulls.columns.Number == number))
        
        result = self.connection.execute(selection)                 
        return result.fetchone()['Id']

    def find_pull_request(self, owner, repo, number):
        selection = select([self.pulls]).where(and_(self.pulls.columns.Owner == owner, self.pulls.columns.Repo == repo, self.pulls.columns.Number == number))
        
        result = self.connection.execute(selection)         
        return result.first()

    def exists_commit(self, pull_id, sha):
        selection = select([self.commits]).where(and_(self.commits.columns.PullRequest == pull_id, self.commits.columns.Sha == sha))

        result = self.connection.execute(selection)
        return result.first() != None

    def exists_comment(self, pull_id, comment_id):
        selection = select([self.comments]).where(and_(self.comments.columns.PullRequest == pull_id, self.comments.columns.Id == comment_id))

        result = self.connection.execute(selection)
        return result.first() != None

    def exists_email_comment(self, date, text):
        selection = select([self.comments]).where(and_(self.comments.columns.CreatedAt == date, self.comments.columns.Text == text))

        result = self.connection.execute(selection)
        return result.first() != None                 
    
    def record_pull_request(self, owner, repo, number, number_comments, number_review_comments, number_commits):
        insertion = self.pulls.insert().values(Owner=owner, Repo=repo, Number=number, Comments=number_comments, ReviewComments=number_review_comments, Commits=number_commits)
        
        self.connection.execute(insertion)

    def update_pull_request(self, id, owner, repo, number, number_comments, number_review_comments, number_commits):
        insertion = self.pulls.update().where(self.pulls.columns.Id == id).values(Owner=owner, Repo=repo, Number=number, Comments=number_comments, ReviewComments=number_review_comments, Commits=number_commits)
        
        self.connection.execute(insertion)

    def record_commit(self, pull_request, sha):
        insertion = self.commits.insert().values(PullRequest=pull_request, Sha=sha)
        
        self.connection.execute(insertion)

    def record_comment(self, pull_request, id, created_at, text):
        insertion = self.comments.insert().values(PullRequest=pull_request, Id=id, CreatedAt=created_at, Text=text)
        
        self.connection.execute(insertion)

    def setup_project(self, owner, repo):
        project = self.connection.execute(select([self.projects]).where(self.projects.columns.Owner == owner and self.projects.columns.Repo == repo)).fetchone()
        
        if(project == None): 
            insertion = self.projects.insert().values(Owner=owner, Repo=repo)
            self.connection.execute(insertion)

    def delete_project(self, id):
        project = self.connection.execute(select([self.projects]).where(self.projects.columns.Id == id)).fetchone()
        if(project != None):            
            self.connection.execute(self.pulls.delete().where(self.pulls.columns.Owner == project.Owner and self.pulls.columns.Repo == project.Repo))
        deletion = self.projects.delete().where(self.projects.columns.Id == id)        
        
        return self.connection.execute(deletion).rowcount == 1

    def get_projects(self):
        selection = select([self.projects])

        result = self.connection.execute(selection)
        return result.fetchall()