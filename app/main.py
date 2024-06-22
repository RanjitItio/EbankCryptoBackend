"""
This module configures the BlackSheep application before it starts.
"""
from blacksheep import Application
from rodi import Container
from app.docs import configure_docs
from app.auth import configure_authentication
from app.errors import configure_error_handlers
from app.services import configure_services
from app.settings import load_settings, Settings
from app.auth import UserAuthHandler
from blacksheep.server.authorization import Policy
from guardpost.common import AuthenticatedRequirement
from app.auth import AdminsPolicy
from app.controllers.controllers import controller_router
from app.req_stream import configure_upload_file





def configure_application(
    services: Container,
    settings: Settings,
) -> Application:
    app = Application(
        services=services, show_error_details=settings.app.show_error_details
    )

    configure_error_handlers(app)
    configure_authentication(app, settings)
    configure_docs(app, settings)

    app.use_authentication().add(UserAuthHandler())

    app.use_authorization().add(Policy(('userauth'), AuthenticatedRequirement())).add(AdminsPolicy())

    app.serve_files('Static', root_path='media', cache_time=90000)


    app.controllers_router = controller_router

    
    
    # docs.bind_app(app)

    app.use_cors(
    allow_methods="*",
    allow_origins="*",
    allow_headers="*",
    allow_credentials=True,
    max_age=600,
    )
  

    return app


app = configure_application(*configure_services(load_settings()))






