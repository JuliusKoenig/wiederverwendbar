import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from starlette_admin.contrib.mongoengine.admin import Admin
from starlette_admin.contrib.mongoengine.view import ModelView

from wiederverwendbar.examples.mongoengine.automatic_reference import Test1, Test2
from wiederverwendbar.mongoengine import MongoengineDbSingleton

# connect to database
MongoengineDbSingleton(init=True)

# Create starlette app
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        ),
    ],
)

# Create admin
admin = Admin(title="Test Admin")



class Test1View(ModelView):
    def __init__(self):
        super().__init__(document=Test1, icon="fa fa-server", name="Test1", label="Test1")

class Test2View(ModelView):
    def __init__(self):
        super().__init__(document=Test2, icon="fa fa-server", name="Test2", label="Test2")


# Add views to admin
admin.add_view(Test1View())
admin.add_view(Test2View())

# Mount admin to app
admin.mount_to(app)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
