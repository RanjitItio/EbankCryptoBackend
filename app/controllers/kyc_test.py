from blacksheep import json, Request, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from sqlmodel import select
from Models.models import Kycdetails, Users




@get('/api/kyc/test/')
async def kyc_test(self, request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            stmt = select(
                Kycdetails.id,
                Kycdetails.gander,
                Kycdetails.state,
                Kycdetails.status,
                Kycdetails.marital_status,
                Kycdetails.country,
                Kycdetails.email,
                Kycdetails.nationality,
                Kycdetails.user_id,
                Kycdetails.firstname,
                Kycdetails.phoneno,
                Kycdetails.id_type,
                Kycdetails.id_number,
                Kycdetails.id_expiry_date,
                Kycdetails.address,
                Kycdetails.lastname,
                Kycdetails.landmark,
                Kycdetails.lastname,
                Kycdetails.city,
                Kycdetails.uploaddocument,
                Kycdetails.dateofbirth,
                Kycdetails.zipcode,

                Users.ipaddress.label('ip_address'),
                Users.lastlogin,
                Users.is_merchent.label('merchant'),
                Users.is_admin.label('admin'),
                Users.is_active.label('active'),
                Users.is_verified.label('verified'),
                Users.group,
            ).join(
                Users, Users.id == Kycdetails.user_id
            )
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)