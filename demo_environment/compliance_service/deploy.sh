heroku login
heroku container:login
heroku container:push web --app norkos-compliance-service
heroku container:release web --app norkos-compliance-service
heroku logs --app norkos-compliance-service