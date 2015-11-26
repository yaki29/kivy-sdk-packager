from os.path import join, isfile, dirname
from os import listdir, environ
from pydrive.auth import GoogleAuth
from apiclient import errors
from pydrive.drive import GoogleDrive

cred = 'my_cred'
settings = b'''
client_config_backend: settings
client_config:
  client_id: {}
  client_secret: {}
  auth_uri: https://accounts.google.com/o/oauth2/auth
  token_uri: https://accounts.google.com/o/oauth2/token
  redirect_uri: http://localhost:8080/

save_credentials: True
save_credentials_file: {}
save_credentials_backend: file
get_refresh_token: True
'''.format(environ['GDRIVE_CLIENT_ID'].encode('ascii'),
           environ['GDRIVE_CLIENT_SECRET'].encode('ascii'), cred)


def get_drive():
    with open('settings.yaml', 'wb') as fh:
        fh.write(settings)

    with open(cred, 'wb') as fh:
        fh.write(environ['AIRPLANE_CHARGE'].encode('ascii'))

    gauth = GoogleAuth()
    # gauth.LocalWebserverAuth()
    gauth.LoadCredentials()
    if gauth.access_token_expired:
        gauth.Refresh()

    drive = GoogleDrive(gauth)
    return drive


def get_filelist(folder_id):
    drive = get_drive()
    l = drive.ListFile(
        {'q': "'{}' in parents and trashed=false".format(folder_id)}).GetList()
    files = {item['title']: item['id'] for item in l
             if item['mimeType'] != 'application/vnd.google-apps.folder'}
    return drive, files


def files_exist(*names):
    drive, files = get_filelist(environ['GDRIVE_UPLOAD_ID'])
    return all([name in files for name in names])


def download_file(directory, filename):
    drive, files = get_filelist(environ['GDRIVE_UPLOAD_ID'])
    if filename not in files:
        raise Exception("{} doesn't exist".format(filename))

    f = drive.CreateFile({'id': files[filename]})
    f.GetContentFile(join(directory, filename))


def upload_directory(directory):
    drive, files = get_filelist(environ['GDRIVE_UPLOAD_ID'])

    for fname in listdir(directory):
        name = join(directory, fname)
        if not isfile(name):
            raise Exception('{} is not a file'.format(name))

        if fname in files:
            print('Skipping {}. Already exists on gdrive'.format(fname))
            continue

        f = drive.CreateFile({'parents': [{'id': environ['GDRIVE_UPLOAD_ID']}],
                              'title': fname})
        f.SetContentFile(name)
        f.Upload()
        print('Uploaded {}'.format(f['title']))

#     try:
#         gauth.service.files().delete(fileId='0B1_HB9J8mZepdHFWaDB5VjJFQWM').execute()
#     except errors.HttpError, error:
#         print 'An error occurred: %s' % error


if __name__ == '__main__':
    import sys
    cmd = sys.argv[1]
    if cmd == 'upload':
        upload_directory(sys.argv[2])
    elif cmd == 'exists':
        print(files_exist(sys.argv[2:]))
    elif cmd == 'download':
        download_file(sys.argv[2:4])
