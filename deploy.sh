heroku login
heroku container:login
heroku container:push web --app secure-spire-80562
heroku container:release web --app secure-spire-80562
heroku open --app secure-spire-80562
heroku logs --app secure-spire-80562