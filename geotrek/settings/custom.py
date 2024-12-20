# import os

#
# BASIC SETTINGS
# ..............
SRID = 2975  # LAMBERT EXTENDED FOR FRANCE, used for geometric columns.
# Must be a projection in meters Fixed at install, don't change it after
#
 DEFAULT_STRUCTURE_NAME = 'OTISUD' # -> Name for your default structure. Can be changed in geotrek admin interface
#
 SPATIAL_EXTENT = (-23344.18, 7256163.66, 631069.19, 7978390.98)
# spatial bbox in your own projection (example here with 2154)
# this spatial_extent will limit map exploration, and will cut your raster imports
#
# LANGUAGE_CODE = 'en' # for web interface. default to fr (French)

# MODELTRANSLATION_LANGUAGES = ('en', 'fr', 'it', 'es')
# Change with your own wanted translations
# ex: MODELTRANSLATION_LANGUAGES = ('en', 'fr', 'de', 'ne')

 ADMINS = (
     ('David', 'd.philippe@otisud.com'), # change with tuple ('your name', 'your@address.mail')
 )
# used to send error mails

# MANAGERS = (
#     ('manager1', 'manager1@geotrek.fr'), # change with tuple ('your name', 'your@address.mail')
# )

# or MANAGERS = ADMINS
# used to send report mail

# TIME_ZONE="Europe/Paris"
# set your timezone for date format. For France, uncomment line beside
# For other zones : find your timezone in https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

#
# MAIL SETTINGS
# ..........................
# DEFAULT_FROM_EMAIL =
# address will be set for sended emails (ex: noreply@yourdomain.net)
# SERVER_EMAIL = DEFAULT_FROM_EMAIL
# EMAIL_HOST =
# EMAIL_HOST_USER =
# EMAIL_HOST_PASSWORD =
# EMAIL_PORT =
# EMAIL_USE_TLS = False
# EMAIL_USE_SSL = False

#
# External authent if required
# ..........................

# AUTHENT_DATABASE = 'your_authent_dbname'
# AUTHENT_TABLENAME = 'your_authent_table_name'
# if AUTHENT_TABLENAME:
#     AUTHENTICATION_BACKENDS = ('geotrek.authent.backend.DatabaseBackend',)

# IF YOU USE SSL

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
