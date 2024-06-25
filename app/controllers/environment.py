from decouple import config

is_development  = config('IS_DEVELOPMENT')
development_url = config('DEVELOPMENT_URL_MEDIA')
production_url  = config('PRODUCTION_URL_MEDIA')

#Check the Environment is in Production state or Development state
if is_development == 'False':
    media_url = production_url
else:
    media_url = development_url