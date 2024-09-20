from blacksheep.server.routing import RoutesRegistry
# from blacksheep.server.routing import Router



controller_router = RoutesRegistry()


get    = controller_router.get
add_get = controller_router.add_get
post   = controller_router.post
put    = controller_router.put
delete = controller_router.delete

