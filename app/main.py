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
from blacksheep.server.env import is_development
from blacksheep.server.security.hsts import HSTSMiddleware
from blacksheep.server.compression import use_gzip_compression
from app.CryptoFiatController.authentication import (
    CryptoFiatUserRegisterController, CryptoFiatUserLoginController
    )
from app.CryptoFiatController.deposit import DepositController
from app.CryptoFiatController.SendMoney import TransferMoneyController
from app.CryptoFiatController.Transactions import UserFiatTransactionController, UserFiatRecentTransactionController
from app.CryptoFiatController.Withdrawal import UserFiatWithdrawalController
from app.CryptoFiatController.ExchangeMoney import ExchangeMoneyController
from app.CryptoFiatController.user_profile import CryprtoFIATUserProfileController, UploadCryptoFIATUserProfilePicture
from app.CryptoFiatAdminControllers.admin_users import CryptoUserKYCController
from app.CryptoFiatAdminControllers.admin_transaction_deposit import AllDepositController, AdminFiletrFIATDepositController
from app.CryptoFiatAdminControllers.admin_transaction_transfer import AllTransferTransactions
from app.CryptoFiatAdminControllers.admin_transactions import AdminFiatAllTransactionsController
from app.CryptoFiatAdminControllers.admin_transaction_withdrawals import AdminAllWithdrawalTransactionController, AdminFilterFiatWithdrawal, AdminExportFIATWithdrawal
from app.CryptoFiatAdminControllers.admin_transaction_exchange import AdminFiatExchangeMoneyController
from app.CryptoFiatAdminControllers.admin_user_transactions import AdminUserFiatTransactionController
from app.CryptoFiatAdminControllers.fees import AdminFeeController
from app.CryptoController.wallet_request import CryptoWalletController, UserCryptoWalletsController
from app.CryptoController.transactions import CryptoBuyController, FeeController, CryptoSellController,CryptoTransactionControlller
from app.CryptoAdminController.wallet_requests import AdminCryptoWalletController, ExportWalletController
from app.CryptoAdminController.transactions import CryptoTransactionController, CryptoSellController, CryptoBuyController, ExportCryptoTransactionDataController




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

    app.serve_files('Static', root_path='media', cache_time=90000, extensions={'.pdf', '.png', '.jpg', '.jpeg', '.svg', '.webp'})

    app.controllers_router = controller_router

    use_gzip_compression(app)

    if not is_development:
        app.middlewares.append(HSTSMiddleware())
    
    
    # docs.bind_app(app)
    app.use_cors(
    allow_methods="*",
    allow_origins="*",
    allow_headers="*",
    allow_credentials=True,
    max_age=900,
    )
  

    return app


app = configure_application(*configure_services(load_settings()))





