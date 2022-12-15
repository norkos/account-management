heroku login
heroku container:login

heroku container:push web --app norkos-nam-billing
heroku container:release web --app norkos-nam-billing
heroku logs --app norkos-nam-billing

heroku container:push web --app norkos-emea-billing
heroku container:release web --app norkos-emea-billing
heroku logs --app norkos-emea-billing

heroku container:push web --app norkos-apac-billing
heroku container:release web --app norkos-apac-billing
heroku logs --app norkos-apac-billing
