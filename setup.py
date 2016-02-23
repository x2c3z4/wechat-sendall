from distutils.core import setup
setup(
  name = 'wechat-sendall',
  packages = ['wechat-sendall'], # this must be the same as the name above
  version = '1.1',
  description = 'Send custom message to your friend on wechat',
  author = 'Alex',
  author_email = 'lifeng1519@gmail.com',
  url = 'https://github.com/vonnyfly/wechat-sendall', # use the URL to the github repo
  download_url = 'https://github.com/vonnyfly/wechat-sendall/tarball/1.1', # I'll explain this in a second
  keywords = ['wechat', 'send', 'robot'], # arbitrary keywords
  classifiers = [],
  install_requires=[
      'requests',
      'beautifulsoup4',
  ],
  include_package_data = True,
)