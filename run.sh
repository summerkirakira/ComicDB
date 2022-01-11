export FLASK_APP=comicdb
export FLASK_ENV=production
waitress-serve --port=8080 --call 'comicdb:create_app'
