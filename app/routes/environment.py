from decouple import config

is_development  = config('IS_DEVELOPMENT')
development_url = config('DEVELOPMENT_URL_MEDIA')
production_url  = config('PRODUCTION_URL_MEDIA')

if is_development == 'True':
    media_url = development_url
else:
    media_url = production_url

