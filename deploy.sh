heroku login
heroku container:login
heroku container:push web --app norkos-account-management
heroku container:release web --app norkos-account-management
heroku logs --app norkos-account-management